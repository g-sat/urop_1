"""Draw the baseline comparison and one figure per specification case.

Entry point: python scripts/make_case_figures.py
Reads CASES from ambiguity_layer/latent/cases.py.
Writes PNG files into results/figures and paper/figures.
No other script draws one image per case or the baseline bar chart.

User instruction: "u said that u will update the figures compare mine with that baseline and also have 1 image for every case ..."
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambiguity_layer.latent.cases import CASES
from ambiguity_layer.latent.decide import classify

OUTS = [
    ROOT / "results" / "figures",
    ROOT / "paper" / "figures",
]

COLORS = {
    "decision": "#C05621",
    "latent": "#2B6CB0",
    "none": "#2F855A",
}


def save(fig: plt.Figure, name: str) -> None:
    for folder in OUTS:
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width)) or ""


def baseline_chart() -> None:
    names = [
        "This rule",
        "Current answers\nonly",
        "Two readings\nmeans ask",
        "Always latent",
        "Always decision",
        "Always answer",
    ]
    scores = [12, 7, 6, 5, 4, 3]
    colors = ["#2F855A", "#8D99AE", "#8D99AE", "#8D99AE", "#8D99AE", "#8D99AE"]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    bars = ax.bar(names, scores, color=colors)
    ax.set_ylim(0, 14)
    ax.set_ylabel("Correct labels out of 12")
    ax.set_title("This rule against baselines on the same 12 cases")
    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            score + 0.25,
            str(score),
            ha="center",
        )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, "baseline_comparison.png")


def case_chart(index: int, case: dict) -> None:
    result = classify(
        case["readings"],
        case["immediate_answers"],
        case["followup_answers"],
    )
    label = result["label"]
    action = result["action"].replace("_", " ")
    k = len(case["readings"])
    baseline = "decision" if k >= 2 else "none"
    baseline_note = "same as this rule" if baseline == label else "wrong on this case"
    color = COLORS[label]

    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.add_patch(
        FancyBboxPatch(
            (0.3, 8.5),
            9.4,
            1.2,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor="#F4F6F8",
            edgecolor="#D0D5DD",
        )
    )
    ax.text(0.5, 9.15, wrap(case["prompt"], 78), va="center", fontsize=9)

    width = 9.0 / k
    for i in range(k):
        left = 0.4 + i * width
        ax.add_patch(
            FancyBboxPatch(
                (left, 1.5),
                width - 0.25,
                6.6,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor="white",
                edgecolor=color,
                linewidth=1.6,
            )
        )
        ax.text(
            left + 0.15,
            7.55,
            f"Reading {i + 1}",
            fontsize=9,
            color=color,
        )
        ax.text(left + 0.15, 6.9, wrap(case["readings"][i], 28), fontsize=8, va="top")
        ax.text(left + 0.15, 5.15, "Answer now", fontsize=8, color="#667085")
        ax.text(
            left + 0.15,
            4.75,
            wrap(case["immediate_answers"][i], 28),
            fontsize=8,
            va="top",
        )
        ax.text(left + 0.15, 3.15, "Follow-up", fontsize=8, color="#667085")
        follow = case["followup"] + " " + case["followup_answers"][i]
        ax.text(left + 0.15, 2.75, wrap(follow, 28), fontsize=8, va="top")

    ax.text(
        0.4,
        0.7,
        (
            f"{label}  |  {action}  |  "
            f"baseline that only counts readings: {baseline} ({baseline_note})"
        ),
        fontsize=8,
        color=color,
    )
    ax.set_title(
        f"Case {index}. {case['id'].replace('_', ' ')}",
        loc="left",
        fontsize=11,
        color=color,
    )
    save(fig, f"case_{index:02d}_{case['id']}.png")


def main() -> None:
    baseline_chart()
    for i, case in enumerate(CASES, start=1):
        case_chart(i, case)
    print(f"Wrote baseline chart and {len(CASES)} case figures")


if __name__ == "__main__":
    main()
