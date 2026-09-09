"""
Run the Active Ambiguity Interception benchmark (Python + NLP eval).

Usage:
  python scripts/run_benchmark.py --limit 10
  python scripts/run_benchmark.py --out results/benchmark_nlp.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ambiguity_layer import config
from ambiguity_layer.eval import score_clarification, score_clause_semantic, types_equal
from ambiguity_layer.pipeline import process_query


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def evaluate_sample(sample: dict, use_nli: bool) -> dict:
    started = time.time()
    result = process_query(sample["long_prompt"], generate_final=False)
    diagnosis = result.get("diagnosis") or {}
    detected = result.get("status") == "needs_clarification" and diagnosis.get(
        "isAmbiguous"
    )

    gold_type = sample.get("ambiguity_type")
    predicted = diagnosis.get("ambiguityType")
    type_match = bool(detected and types_equal(predicted, gold_type))

    clause = score_clause_semantic(
        diagnosis.get("problematicClause") or "",
        sample.get("ground_truth_clause") or "",
        sample["long_prompt"],
    )
    if not detected:
        clause = {"clause_score": 0.0, "clause_hit": False, "method": "sbert"}

    clar = (
        score_clarification(
            result.get("clarifying_questions") or [],
            sample.get("optimal_clarification") or "",
            use_nli=use_nli,
        )
        if detected
        else {
            "clarification_score": 0.0,
            "clarification_match": False,
            "method": "none",
        }
    )

    nlp = diagnosis.get("nlp") or {}
    return {
        "id": sample.get("id"),
        "gold_type": gold_type,
        "predicted_type": predicted,
        "detected": bool(detected),
        "type_match": type_match,
        "clause_hit": bool(clause.get("clause_hit")),
        "clause_score": clause.get("clause_score", 0.0),
        "clarification_match": bool(clar.get("clarification_match")),
        "clarification_score": clar.get("clarification_score", 0.0),
        "clarification_method": clar.get("method"),
        "clarifying_questions": result.get("clarifying_questions") or [],
        "problematic_clause": diagnosis.get("problematicClause") or "",
        "nlp_span_used": diagnosis.get("nlpSpanUsed"),
        "nlp_span_kind": diagnosis.get("nlpSpanKind"),
        "nlp_top_kinds": [s.get("kind") for s in (nlp.get("proposed_spans") or [])[:3]],
        "status": result.get("status"),
        "elapsed_sec": round(time.time() - started, 3),
        "error": None,
    }


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r.get("error")]
    n = len(ok) or 1
    return {
        "total": len(rows),
        "evaluated": len(ok),
        "errors": len(rows) - len(ok),
        "detection_rate": round(sum(r["detected"] for r in ok) / n, 3),
        "type_accuracy": round(sum(r["type_match"] for r in ok) / n, 3),
        "clause_hit_rate": round(sum(r["clause_hit"] for r in ok) / n, 3),
        "clarification_match_rate": round(
            sum(r["clarification_match"] for r in ok) / n, 3
        ),
        "avg_clause_score": round(sum(r["clause_score"] for r in ok) / n, 3),
        "avg_clarification_score": round(
            sum(r["clarification_score"] for r in ok) / n, 3
        ),
        "nlp_span_usage_rate": round(
            sum(1 for r in ok if r.get("nlp_span_used")) / n, 3
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="NLP+LLM ambiguity benchmark")
    parser.add_argument("--limit", "-n", type=int, default=None)
    parser.add_argument("--dataset", type=Path, default=config.DATASET_PATH)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--no-nli", action="store_true", help="SBERT only for clar")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between samples (raise if you hit 429s)",
    )
    args = parser.parse_args()

    samples = load_jsonl(args.dataset)
    if args.limit:
        samples = samples[: args.limit]

    print(f"Dataset: {args.dataset}")
    print(f"Samples: {len(samples)}")
    print("Eval: SBERT clause + SBERT" + ("" if args.no_nli else "+NLI") + " clarification\n")

    rows = []
    for i, sample in enumerate(samples):
        label = sample.get("id", f"row_{i}")
        print(f"[{i + 1}/{len(samples)}] {label} ... ", end="", flush=True)
        try:
            row = evaluate_sample(sample, use_nli=not args.no_nli)
            rows.append(row)
            print(
                f"{'AMB' if row['detected'] else 'CLEAR'} "
                f"type={'OK' if row['type_match'] else 'MISS'} "
                f"clause={'OK' if row['clause_hit'] else 'MISS'} "
                f"clar={'OK' if row['clarification_match'] else 'MISS'}"
                f"({row['clarification_score']})"
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "id": label,
                    "error": str(exc),
                    "detected": False,
                    "type_match": False,
                    "clause_hit": False,
                    "clarification_match": False,
                    "clause_score": 0.0,
                    "clarification_score": 0.0,
                }
            )
            print(f"ERROR: {exc}")
        if args.delay and i < len(samples) - 1:
            time.sleep(args.delay)

    summary = summarize(rows)
    print("\n=== Benchmark Summary ===")
    print(json.dumps(summary, indent=2))

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = args.out or (
        config.RESULTS_DIR
        / f"benchmark_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"summary": summary, "results": rows}, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
