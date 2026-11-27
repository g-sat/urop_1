"""Charts of the Cursor-model labels on the AmbigQA dev set.

Called by: python scripts/make_ambigqa_score_figures.py
No other script reads results/ambigqa_cursor/scores.json.
Reads counts.decision, counts.none, and counts.latent for each batch.
Writes PNG files into results/figures and paper/figures.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "results" / "ambigqa_cursor" / "scores.json"
OUTS = [ROOT / "results" / "figures", ROOT / "paper" / "figures"]

COLORS = {
    "decision": "#C05621",
    "none": "#2F855A",
    "latent": "#2B6CB0",
}


def save(fig: plt.Figure, name: str) -> None:
    for folder in OUTS:
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def load_rows() -> list[tuple[int, int, int, int]]:
    raw = json.loads(SCORES.read_text(encoding="utf-8"))
    rows = []
    for name, row in raw.items():
        batch = int(name.removeprefix("batch_").removesuffix(".jsonl"))
        counts = row["counts"]
        rows.append(
            (
                batch,
                int(counts.get("decision", 0)),
                int(counts.get("none", 0)),
                int(counts.get("latent", 0)),
            )
        )
    rows.sort()
    return rows


def style(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def totals_chart(rows: list[tuple[int, int, int, int]]) -> None:
    decision = sum(row[1] for row in rows)
    none = sum(row[2] for row in rows)
    latent = sum(row[3] for row in rows)
    labels = ["Decision", "None", "Latent"]
    values = [decision, none, latent]
    colors = [COLORS["decision"], COLORS["none"], COLORS["latent"]]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    bars = ax.bar(labels, values, color=colors)
    ax.set_ylabel("Questions")
    ax.set_title("AmbigQA dev labels (2,002 questions)")
    ax.set_ylim(0, max(values) * 1.12)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 18,
            f"{value}",
            ha="center",
            va="bottom",
        )
    style(ax)
    save(fig, "ambigqa_label_totals.png")


def by_batch_chart(rows: list[tuple[int, int, int, int]]) -> None:
    batches = [row[0] for row in rows]
    decision = [row[1] for row in rows]
    none = [row[2] for row in rows]
    latent = [row[3] for row in rows]
    fig, ax = plt.subplots(figsize=(11.2, 4.2))
    ax.bar(batches, decision, color=COLORS["decision"], label="Decision", width=0.85)
    ax.bar(batches, none, bottom=decision, color=COLORS["none"], label="None", width=0.85)
    bottom = [left + mid for left, mid in zip(decision, none)]
    ax.bar(batches, latent, bottom=bottom, color=COLORS["latent"], label="Latent", width=0.85)
    ax.set_xlabel("Batch")
    ax.set_ylabel("Questions")
    ax.set_title("Label mix by batch")
    ax.set_xlim(-0.6, 50.6)
    ax.set_xticks(range(0, 51, 5))
    ax.legend(
        frameon=False,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
    )
    style(ax)
    save(fig, "ambigqa_labels_by_batch.png")


def latent_chart(rows: list[tuple[int, int, int, int]]) -> None:
    hit = [(batch, latent) for batch, _decision, _none, latent in rows if latent > 0]
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    names = [str(batch) for batch, _latent in hit]
    values = [latent for _batch, latent in hit]
    bars = ax.bar(names, values, color=COLORS["latent"])
    ax.set_xlabel("Batch")
    ax.set_ylabel("Latent questions")
    ax.set_title("Batches that contain a latent label")
    ax.set_ylim(0, max(values) + 1)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.08,
            str(value),
            ha="center",
            va="bottom",
            fontsize=8,
        )
    style(ax)
    save(fig, "ambigqa_latent_by_batch.png")


def second_pass() -> dict[str, dict]:
    folder = ROOT / "results" / "ambigqa_second_pass"
    found: dict[str, dict] = {}
    if not folder.exists():
        return found
    for path in sorted(folder.glob("pass_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                found[str(item["id"])] = item
    return found


def confusion_chart() -> list[list[int]]:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "latent_decide",
        ROOT / "ambiguity_layer" / "latent" / "decide.py",
    )
    decide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decide)

    gold_labels = ["singleAnswer", "multipleQAs"]
    pred_labels = ["decision", "latent", "none"]
    index_g = {name: i for i, name in enumerate(gold_labels)}
    index_p = {name: i for i, name in enumerate(pred_labels)}
    matrix = [[0, 0, 0], [0, 0, 0]]
    batches = ROOT / "data" / "ambigqa_batches"
    labeled = ROOT / "results" / "ambigqa_cursor"
    revised = second_pass()
    missing = 0
    for src in sorted(batches.glob("batch_*.json")):
        gold = {
            str(row["id"]): row["ambigqa_type"]
            for row in json.loads(src.read_text(encoding="utf-8"))
        }
        out = labeled / (src.stem + ".jsonl")
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            item = revised.get(str(item["id"]), item)
            kind = gold.get(str(item["id"]))
            if kind not in index_g:
                missing += 1
                continue
            result = decide.classify(
                item["readings"],
                item["immediate_answers"],
                item["followup_answers"],
            )
            matrix[index_g[kind]][index_p[result["label"]]] += 1

    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(
        range(3),
        ["Decision", "Latent", "None"],
    )
    ax.set_yticks(
        range(2),
        ["Single answer", "Multiple QAs"],
    )
    ax.set_xlabel("This rule")
    ax.set_ylabel("AmbigQA annotation")
    ax.set_title("AmbigQA type against this rule")
    peak = max(max(row) for row in matrix)
    for i in range(2):
        row_total = sum(matrix[i]) or 1
        for j in range(3):
            count = matrix[i][j]
            share = 100.0 * count / row_total
            color = "white" if count > peak * 0.55 else "black"
            ax.text(
                j,
                i,
                f"{count}\n{share:.1f}%",
                ha="center",
                va="center",
                color=color,
            )
    fig.colorbar(im, ax=ax, fraction=0.046)
    save(fig, "ambigqa_confusion.png")
    print("missing", missing)
    print(json.dumps(matrix))
    return matrix


def _scores(gold: list[bool], pred: list[bool]) -> dict[str, float]:
    tp = sum(g and p for g, p in zip(gold, pred))
    fp = sum((not g) and p for g, p in zip(gold, pred))
    fn = sum(g and (not p) for g, p in zip(gold, pred))
    tn = sum((not g) and (not p) for g, p in zip(gold, pred))
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": round((tp + tn) / n, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def policy_comparison() -> None:
    """Ask-or-answer policies on the same 2,002 answer lists.

    Gold is AmbigQA multipleQAs. IntentSim, Rao and Daumé's stopping
    rule, and string semantic entropy all ask exactly when the immediate
    answers differ. That bit is this rule's decision label, so those
    three are one row, not three trained models.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "latent_decide",
        ROOT / "ambiguity_layer" / "latent" / "decide.py",
    )
    decide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decide)

    revised = second_pass()
    gold: list[bool] = []
    rule_ask: list[bool] = []
    rule_flag: list[bool] = []
    many_readings: list[bool] = []
    batches = ROOT / "data" / "ambigqa_batches"
    labeled = ROOT / "results" / "ambigqa_cursor"
    for src in sorted(batches.glob("batch_*.json")):
        kinds = {
            str(row["id"]): row["ambigqa_type"]
            for row in json.loads(src.read_text(encoding="utf-8"))
        }
        out = labeled / (src.stem + ".jsonl")
        for line in out.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            item = revised.get(str(item["id"]), item)
            kind = kinds[str(item["id"])]
            result = decide.classify(
                item["readings"],
                item["immediate_answers"],
                item["followup_answers"],
            )
            label = result["label"]
            gold.append(kind == "multipleQAs")
            rule_ask.append(label == "decision")
            rule_flag.append(label in {"decision", "latent"})
            many_readings.append(int(item["n"]) >= 2)
            immediate_split = not decide._all_same(item["immediate_answers"])
            if immediate_split != (label == "decision"):
                raise RuntimeError("decision label drifted from immediate answers")

    always_ask = [True] * len(gold)
    always_answer = [False] * len(gold)
    systems = [
        ("Ask if answers\ndiffer", rule_ask),
        ("Ask if decision\nor latent", rule_flag),
        ("Ask if 2+\nreadings", many_readings),
        ("Always ask", always_ask),
        ("Always answer", always_answer),
    ]
    table = {name.replace("\n", " "): _scores(gold, pred) for name, pred in systems}
    same = sum(a == b for a, b in zip(rule_ask, many_readings))
    table["note"] = {
        "n": len(gold),
        "gold_multiple": sum(gold),
        "rule_ask_equals_immediate_split": True,
        "agreement_with_two_or_more_readings": same,
        "named_systems_not_executed": [
            "IntentSim (no public code; needs 10 samples and an NLI model)",
            "Rao and Daumé neural ranker (StackExchange posts, not these questions)",
            "AmbigQA SpanSeqGen (Wikipedia index and BART checkpoint)",
        ],
    }
    out = ROOT / "results" / "ambigqa_cursor" / "baseline_compare.json"
    out.write_text(json.dumps(table, indent=2), encoding="utf-8")

    names = [name for name, _pred in systems]
    accuracy = [table[name.replace("\n", " ")]["accuracy"] for name in names]
    f1 = [table[name.replace("\n", " ")]["f1"] for name in names]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    xpos = list(range(len(names)))
    width = 0.38
    ax.bar([x - width / 2 for x in xpos], accuracy, width, color="#2F855A", label="Accuracy")
    ax.bar([x + width / 2 for x in xpos], f1, width, color="#C05621", label="F1 on multiple QAs")
    ax.set_xticks(xpos, names)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Ask-or-answer policies on 2,002 AmbigQA questions")
    ax.legend(frameon=False, loc="upper right")
    style(ax)
    save(fig, "ambigqa_policy_comparison.png")
    print(json.dumps(table, indent=2))


def main() -> None:
    rows = load_rows()
    totals_chart(rows)
    by_batch_chart(rows)
    latent_chart(rows)
    confusion_chart()
    policy_comparison()


if __name__ == "__main__":
    main()
