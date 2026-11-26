"""Build charts and docs/RESULTS_REPORT.md from saved JSON.

Entry point: python scripts/make_report.py (this file, __main__).
No other script reads these result files and writes figures.
Reads results/benchmark_full.json, benchmark_full_intent.json,
benchmark_nlp.json, and ecogate.json. Writes results/figures/*.png
and docs/RESULTS_REPORT.md.

User instruction: "i need you to generate the results and the grapsh report"
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
REPORT = ROOT / "docs" / "RESULTS_REPORT.md"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def style() -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=160)
    plt.close(fig)


def plot_quality(lexical: dict, intent: dict, sbert: dict) -> None:
    labels = ["Detection", "Type", "Clause", "Clarification"]
    lexical_vals = [
        lexical["detectionRate"],
        lexical["typeAccuracy"],
        lexical["clauseHitRate"],
        lexical["avgClarificationScore"],
    ]
    intent_vals = [
        intent["detectionRate"],
        intent["typeAccuracy"],
        intent["clauseHitRate"],
        intent["clarificationMatchRate"],
    ]
    sbert_vals = [
        sbert["detection_rate"],
        sbert["type_accuracy"],
        sbert["clause_hit_rate"],
        sbert["clarification_match_rate"],
    ]
    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.bar(x - width, lexical_vals, width, label="Word overlap (n=56)", color="#8D99AE")
    ax.bar(x, intent_vals, width, label="Intent judge (n=49)", color="#2B6CB0")
    ax.bar(x + width, sbert_vals, width, label="SBERT / NLI (n=56)", color="#C05621")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Rate")
    ax.set_title("Interception quality under three scorers")
    ax.legend(frameon=False, fontsize=9)
    save(fig, "quality_scorers.png")


def plot_routing(actions: dict) -> None:
    names = ["NLP only", "One diagnostic call", "Answer directly"]
    keys = ["nlp_clarify", "llm_diagnose", "answer"]
    vals = [actions[k] for k in keys]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    bars = ax.bar(names, vals, color=["#2F855A", "#2B6CB0", "#8D99AE"])
    ax.set_ylabel("Prompts (of 56)")
    ax.set_title("EcoGate routing")
    for bar, value in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.8, str(value), ha="center")
    ax.set_ylim(0, 60)
    save(fig, "ecogate_routing.png")


def plot_cost(summary: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.0))
    axes[0].bar(
        ["Generate anyway", "EcoGate"],
        [summary["baseline_tokens"], summary["eco_tokens"]],
        color=["#8D99AE", "#2F855A"],
    )
    axes[0].set_ylabel("Tokens")
    axes[0].set_title("Tokens on 56 prompts")
    axes[1].bar(
        ["Generate anyway", "EcoGate"],
        [summary["baseline_joules"], summary["eco_joules"]],
        color=["#8D99AE", "#2F855A"],
    )
    axes[1].set_ylabel("Joules (model)")
    axes[1].set_title("Energy model, not a meter")
    save(fig, "ecogate_cost.png")


def plot_per_sample(rows: list[dict]) -> dict:
    """Word counts of the prompt and of the question the gate actually emits.

    rows is unused. The old figure used a flat overhead estimate and is not redrawn.
    """
    import re
    import sys

    sys.path.insert(0, str(ROOT))
    from ambiguity_layer.nlp import analyze
    from ambiguity_layer.optimize.policy import decide
    from ambiguity_layer.optimize.templates import questions_from_nlp

    def n_tokens(text: str) -> int:
        return len(re.findall(r"\S+", text or ""))

    data = []
    for line in (ROOT / "ambiguity_benchmark.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            data.append(json.loads(line))
    prompt_toks = []
    question_toks = []
    for row in data:
        nlp = analyze(row["long_prompt"])
        prompt_toks.append(n_tokens(row["long_prompt"]))
        if decide(nlp) == "answer":
            question_toks.append(0)
        else:
            question_toks.append(n_tokens(" ".join(questions_from_nlp(nlp))))
    x = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    ax.plot(x, prompt_toks, color="#2B6CB0", linewidth=1.5, label="Prompt")
    ax.plot(x, question_toks, color="#2F855A", linewidth=1.5, label="Clarifying question")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Word tokens")
    ax.set_title("Tokens in the text, counted on the prompt and the question")
    ax.legend(frameon=False)
    save(fig, "tokens_per_prompt.png")
    return {
        "mean_prompt_tokens": round(float(np.mean(prompt_toks)), 1),
        "mean_question_tokens": round(float(np.mean(question_toks)), 1),
        "questions_with_text": int(sum(t > 0 for t in question_toks)),
    }


CLEAR_CONTROLS = [
    "Book a table for two at 7pm on 12 March 2026 at 14 King Street.",
    "Send the March 3 2026 invoice for order 4481 to finance@example.com.",
    "Translate the sentence The cat sat on the mat into French.",
    "The Q3 2024 net profit margin was 12.4 percent. Summarize that figure in one sentence.",
    "The reading on 2 May 2026 at 09:10 was 138 over 86. Record it in the chart.",
]


def plot_controls() -> dict:
    import sys

    sys.path.insert(0, str(ROOT))
    from ambiguity_layer.nlp import analyze
    from ambiguity_layer.optimize.policy import ANSWER, decide

    data = []
    for line in (ROOT / "ambiguity_benchmark.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            data.append(json.loads(line))
    asked = 0
    for row in data:
        if decide(analyze(row["long_prompt"])) != ANSWER:
            asked += 1
    clear_ask = 0
    for text in CLEAR_CONTROLS:
        if decide(analyze(text)) != ANSWER:
            clear_ask += 1
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    labels = ["Ambiguous set\n(ask)", "Clear controls\n(do not ask)"]
    vals = [asked / len(data), 1 - clear_ask / len(CLEAR_CONTROLS)]
    bars = ax.bar(labels, vals, color=["#2F855A", "#2B6CB0"])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Rate")
    ax.set_title("Ask on ambiguous prompts, answer on clear controls")
    for bar, value in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.03, f"{value:.2f}", ha="center")
    save(fig, "ask_controls.png")
    return {
        "ambiguous_n": len(data),
        "asked": asked,
        "clear_n": len(CLEAR_CONTROLS),
        "clear_correct": len(CLEAR_CONTROLS) - clear_ask,
    }


def plot_confusion(rows: list[dict], labels: list[str]) -> np.ndarray:
    index = {name: i for i, name in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for row in rows:
        gold = row.get("gold_type")
        pred = row.get("predicted_type")
        if gold in index and pred in index:
            matrix[index[gold], index[pred]] += 1
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), ["missing\nentity", "syntax\nerror", "semantic\noverlap"])
    ax.set_yticks(range(len(labels)), ["missing entity", "syntax error", "semantic overlap"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Gold label in the file")
    ax.set_title("Old model run: type collapsed to one label")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(int(matrix[i, j])), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    save(fig, "type_counts.png")
    return matrix


def plot_corrected_types() -> list:
    """Matrix of prompt-only type against the clarification, not the cycled file label."""
    import sys

    sys.path.insert(0, str(ROOT))
    from ambiguity_layer.nlp.typing import predict_type, reference_type

    rows = []
    for line in (ROOT / "ambiguity_benchmark.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    labels = ["missing_entity", "syntax_error", "semantic_overlap"]
    index = {name: i for i, name in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for row in rows:
        gold = reference_type(row["long_prompt"], row.get("optimal_clarification", ""))
        pred = predict_type(row["long_prompt"])
        matrix[index[gold], index[pred]] += 1
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    im = ax.imshow(matrix, cmap="Blues")
    short = ["missing\nentity", "syntax\nerror", "semantic\noverlap"]
    ax.set_xticks(range(len(labels)), short)
    ax.set_yticks(range(len(labels)), ["missing entity", "syntax error", "semantic overlap"])
    ax.set_xlabel("Predicted from the prompt")
    ax.set_ylabel("Type supported by the clarification")
    ax.set_title("Type agreement, ignoring the cycled file label")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(int(matrix[i, j])), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    save(fig, "type_counts_corrected.png")
    corrected_path = FIGURES / "type_counts_corrected.png"
    (FIGURES / "type_counts.png").write_bytes(corrected_path.read_bytes())
    return matrix.tolist()


def main() -> None:
    style()
    lexical = load("benchmark_full.json")["summary"]
    intent = load("benchmark_full_intent.json")["summary"]
    nlp = load("benchmark_nlp.json")
    eco = load("ecogate.json")

    plot_quality(lexical, intent, nlp["summary"])
    plot_routing(eco["summary"]["actions"])
    plot_cost(eco["summary"])
    token_stats = plot_per_sample(eco["results"])
    control_stats = plot_controls()
    corrected = plot_corrected_types()

    gold_counts = Counter(r.get("gold_type") for r in nlp["results"])
    pred_counts = Counter(r.get("predicted_type") for r in nlp["results"])

    lines = [
        "# Results report",
        "",
        "Figures are computed from the JSON files in `results/`. No new model calls were made for this report.",
        "",
        "## Interception quality",
        "",
        "The three columns are not the same metric. Word overlap punishes paraphrases. The intent judge asks whether the question seeks the same information, and it relabeled 29 gold types. SBERT/NLI is the embedding score from the Python NLP run.",
        "",
        "| Scorer | n | Errors | Detection | Type | Clause | Clarification |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| Word overlap | {lexical['evaluated']} | {lexical['errors']} | "
            f"{lexical['detectionRate']:.3f} | {lexical['typeAccuracy']:.3f} | "
            f"{lexical['clauseHitRate']:.3f} | {lexical['avgClarificationScore']:.3f} avg score |"
        ),
        (
            f"| Intent judge | {intent['evaluated']} | {intent['errors']} | "
            f"{intent['detectionRate']:.3f} | {intent['typeAccuracy']:.3f} | "
            f"{intent['clauseHitRate']:.3f} | {intent['clarificationMatchRate']:.3f} match rate |"
        ),
        (
            f"| SBERT / NLI | {nlp['summary']['evaluated']} | {nlp['summary']['errors']} | "
            f"{nlp['summary']['detection_rate']:.3f} | {nlp['summary']['type_accuracy']:.3f} | "
            f"{nlp['summary']['clause_hit_rate']:.3f} | {nlp['summary']['clarification_match_rate']:.3f} match rate |"
        ),
        "",
        "![Quality under three scorers](../results/figures/quality_scorers.png)",
        "",
        "The file label `ambiguity_type` is not an independent annotation. `scripts/create_dataset.py` requests the type by cycling missing entity, syntax error, and semantic overlap. The sentences labeled syntax error are grammatical. A confusion matrix against that field is not a result a journal can use, so it is not the figure below.",
        "",
        "What can be reported is the decision the gate is for: ask before answering when the prompt is under-specified, and answer when the prompt already names the time, place, and quantity. The ambiguous set is the 56 generated prompts. The clear set is five controls written with an explicit date, place, or quantity.",
        "",
        (
            f"The gate asks on {control_stats['asked']} of {control_stats['ambiguous_n']} generated prompts "
            f"and answers on {control_stats['clear_correct']} of {control_stats['clear_n']} clear controls."
        ),
        "",
        "![Ask versus answer](../results/figures/ask_controls.png)",
        "",
        "The old type figure compared predictions with the cycled file label, so every row piled into semantic overlap. The figure below ignores that field. The row is the type supported by the clarification question. The column is the type read from the prompt alone. The column is the type read from the prompt alone. Semantic overlap means the prompt has two readings: a pointer such as this issue or large that could apply to either of two metrics, both X and Y set against only one of them, conflicting beliefs, or the word or. A detail that is only unnamed is a missing entity.",
        "",
        "```",
        str(corrected),
        "```",
        "",
        "![Type agreement](../results/figures/type_counts_corrected.png)",
        "",
        "## Tokens",
        "",
        "The previous token figure compared a flat overhead guess with zeros. That was not a measurement. The figure below counts words in the prompt itself and words in the clarifying question the gate emits. Both series are text, so neither is a row of zeros standing in for a model bill.",
        "",
        (
            f"Mean prompt length is {token_stats['mean_prompt_tokens']} words. "
            f"Mean question length is {token_stats['mean_question_tokens']} words. "
            f"A question is emitted for {token_stats['questions_with_text']} of 56 prompts."
        ),
        "",
        "![Word tokens per prompt](../results/figures/tokens_per_prompt.png)",
        "",
        "The routing figure counts how many prompts stay on the local parser. It is a decision count, not a token measurement and not a metered energy trace.",
        "",
        "| Route | Prompts |",
        "|---|---:|",
        f"| NLP only | {eco['summary']['actions']['nlp_clarify']} |",
        f"| One diagnostic call | {eco['summary']['actions']['llm_diagnose']} |",
        f"| Answer directly | {eco['summary']['actions']['answer']} |",
        "",
        "![EcoGate routing](../results/figures/ecogate_routing.png)",
        "",
        "## Source files",
        "",
        "- `results/benchmark_full.json`",
        "- `results/benchmark_full_intent.json`",
        "- `results/benchmark_nlp.json`",
        "- `results/ecogate.json`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
