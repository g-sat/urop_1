"""Dataset analysis: clustering, confusion matrix, linguistic error analysis."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sklearn.cluster import KMeans
from sklearn.metrics import confusion_matrix

from ambiguity_layer import config
from ambiguity_layer.eval.embeddings import embed
from ambiguity_layer.nlp import analyze


def load_jsonl(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or config.DATASET_PATH
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def cluster_prompts(
    rows: list[dict[str, Any]] | None = None,
    n_clusters: int = 6,
) -> dict[str, Any]:
    rows = rows or load_jsonl()
    texts = [r["long_prompt"] for r in rows]
    vectors = embed(texts)
    k = min(n_clusters, len(rows))
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(vectors)

    clusters: dict[int, list[str]] = defaultdict(list)
    for row, lab in zip(rows, labels):
        clusters[int(lab)].append(row.get("id", ""))

    return {
        "n_clusters": k,
        "embedding_model": config.EMBEDDING_MODEL,
        "clusters": {str(k_): ids for k_, ids in sorted(clusters.items())},
        "inertia": float(km.inertia_),
    }


def type_confusion(
    y_true: list[str],
    y_pred: list[str],
    labels: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    labels = labels or config.AMBIGUITY_TYPES
    yt = [t if t in labels else "missing_entity" for t in y_true]
    yp = [p if p in labels else "missing_entity" for p in y_pred]
    cm = confusion_matrix(yt, yp, labels=list(labels))
    return {
        "labels": list(labels),
        "matrix": cm.tolist(),
        "counts_true": dict(Counter(yt)),
        "counts_pred": dict(Counter(yp)),
    }


def linguistic_error_analysis(benchmark_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {r.get("id"): r for r in load_jsonl()}
    buckets: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for row in benchmark_results:
        if row.get("error"):
            buckets["runtime_error"] += 1
            continue
        missed = (not row.get("detected")) or (not row.get("clarification_match"))
        if not missed:
            buckets["ok"] += 1
            continue

        sample = by_id.get(row.get("id"))
        if not sample:
            buckets["unknown_sample"] += 1
            continue

        nlp = analyze(sample["long_prompt"])
        kinds = [s.kind for s in nlp.proposed_spans]
        attr = kinds[0] if kinds else "no_nlp_span"
        buckets[attr] += 1
        if len(examples[attr]) < 5:
            examples[attr].append(row.get("id"))

    return {"miss_attribution_counts": dict(buckets), "examples": dict(examples)}


def run_full_analysis(results_path: Path, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or config.ANALYSIS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(Path(results_path).read_text(encoding="utf-8"))
    results = payload.get("results", payload)
    rows = load_jsonl()

    clustering = cluster_prompts(rows)

    y_true, y_pred = [], []
    for r in results:
        if r.get("error"):
            continue
        gold = r.get("gold_type") or r.get("goldType")
        pred = r.get("predicted_type") or r.get("predictedType")
        if gold and pred:
            y_true.append(str(gold))
            y_pred.append(str(pred))

    confusion = (
        type_confusion(y_true, y_pred) if y_true else {"labels": [], "matrix": []}
    )
    errors = linguistic_error_analysis(results)

    report = {
        "source_results": str(results_path),
        "clustering": clustering,
        "confusion_matrix": confusion,
        "linguistic_error_analysis": errors,
        "type_distribution_dataset": dict(
            Counter(r.get("ambiguity_type") for r in rows)
        ),
    }

    out_path = out_dir / "analysis_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = ["# Analysis Report", "", "## Type confusion matrix", ""]
    if confusion.get("labels"):
        labs = confusion["labels"]
        md.append("| gold \\ pred | " + " | ".join(labs) + " |")
        md.append("|---|" + "|".join(["---"] * len(labs)) + "|")
        for i, lab in enumerate(labs):
            md.append(
                f"| {lab} | "
                + " | ".join(str(x) for x in confusion["matrix"][i])
                + " |"
            )
    md.extend(["", "## Miss attribution (NLP phenomena)", ""])
    for k, v in errors.get("miss_attribution_counts", {}).items():
        md.append(f"- **{k}**: {v}")
    (out_dir / "analysis_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_path
