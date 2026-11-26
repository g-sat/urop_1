"""Compare EcoGate with a generate-anyway baseline.

Entry point: python scripts/run_ecogate.py
Calls ambiguity_layer.optimize.controller and ambiguity_layer.nlp.analyze.
Reads ambiguity_benchmark.jsonl. Writes results/ecogate.json.
No other script reports tokens and joules saved by skipping decode.

User verbatim request: build power and token optimisation from future-work
gaps in top-venue papers, combined with the ambiguity interception layer.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ambiguity_layer import config
from ambiguity_layer.nlp import analyze
from ambiguity_layer.optimize.controller import baseline_answer_anyway_tokens, eco_process
from ambiguity_layer.optimize.energy import EnergyLedger
from ambiguity_layer.optimize.policy import decide


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def joules(prompt_tokens: int, completion_tokens: int, nlp_seconds: float = 0.0) -> float:
    return EnergyLedger(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        nlp_seconds=nlp_seconds,
    ).joules()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", "-n", type=int, default=None)
    parser.add_argument("--dataset", type=Path, default=config.DATASET_PATH)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", type=Path, default=config.RESULTS_DIR / "ecogate.json")
    args = parser.parse_args()

    samples = load_jsonl(args.dataset)
    if args.limit:
        samples = samples[: args.limit]

    rows = []
    for i, sample in enumerate(samples):
        prompt = sample["long_prompt"]
        label = sample.get("id", f"row_{i}")
        print(f"[{i + 1}/{len(samples)}] {label} ... ", end="", flush=True)
        if args.live:
            result = eco_process(prompt, generate_final=False)
            energy = result["energy"]
            predicted = (result.get("diagnosis") or {}).get("ambiguityType")
        else:
            t0 = time.perf_counter()
            nlp = analyze(prompt)
            nlp_s = time.perf_counter() - t0
            action = decide(nlp)
            top = nlp.proposed_spans[0] if nlp.proposed_spans else None
            # Uncertain band still pays one diagnostic call. That cost is
            # estimated here so the offline report does not pretend it is free.
            # The answer is still not decoded.
            prompt_body = max(1, len(prompt) // 4)
            if action == "llm_diagnose":
                p_tok, c_tok, calls = 900 + prompt_body, 80, 1
            elif action == "answer":
                p_tok, c_tok, calls = 120 + prompt_body, 180, 1
            else:
                p_tok, c_tok, calls = 0, 0, 0
            energy = {
                "action": action,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": p_tok + c_tok,
                "llm_calls": calls,
                "nlp_seconds": round(nlp_s, 4),
                "joules": round(joules(p_tok, c_tok, nlp_s), 4),
            }
            predicted = top.suggested_type if top and action != "answer" else None

        base = baseline_answer_anyway_tokens(prompt)
        base_j = joules(base["prompt_tokens"], base["completion_tokens"])
        saved_tokens = base["prompt_tokens"] + base["completion_tokens"] - energy["total_tokens"]
        saved_j = base_j - energy["joules"]
        print(
            f"{energy['action']} tokens={energy['total_tokens']} "
            f"saved_tok={saved_tokens} saved_J={saved_j:.1f}"
        )
        rows.append(
            {
                "id": label,
                "gold_type": sample.get("ambiguity_type"),
                "predicted_type": predicted,
                "eco": energy,
                "baseline_tokens": base["prompt_tokens"] + base["completion_tokens"],
                "baseline_joules": round(base_j, 4),
                "tokens_saved": saved_tokens,
                "joules_saved": round(saved_j, 4),
            }
        )

    base_tok = sum(r["baseline_tokens"] for r in rows)
    eco_tok = sum(r["eco"]["total_tokens"] for r in rows)
    summary = {
        "samples": len(rows),
        "live_llm": args.live,
        "actions": {
            name: sum(1 for r in rows if r["eco"]["action"] == name)
            for name in ("nlp_clarify", "llm_diagnose", "answer")
        },
        "eco_tokens": eco_tok,
        "baseline_tokens": base_tok,
        "tokens_saved": sum(r["tokens_saved"] for r in rows),
        "token_reduction": round(1 - eco_tok / max(1, base_tok), 3),
        "eco_joules": round(sum(r["eco"]["joules"] for r in rows), 3),
        "baseline_joules": round(sum(r["baseline_joules"] for r in rows), 3),
        "joules_saved": round(sum(r["joules_saved"] for r in rows), 3),
        "energy_model": {
            "input_J_per_token": config.INPUT_JOULES_PER_TOKEN,
            "output_J_per_token": config.OUTPUT_JOULES_PER_TOKEN,
            "cpu_watts": config.CPU_WATTS,
            "note": "Relative comparison model, not a wall-meter reading.",
        },
    }
    print("\n=== EcoGate Summary ===")
    print(json.dumps(summary, indent=2))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"summary": summary, "results": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
