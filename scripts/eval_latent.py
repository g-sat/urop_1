"""Evaluate latent ambiguity. Entry point: python scripts/eval_latent.py

Calls ambiguity_layer.latent.decide.classify and reads CASES.
Writes results/latent_eval.json. No API. No existing script evaluates this split.

User instruction: "do this then i need you to evaluate this and check clearly with ecc after u impliment thjs"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ambiguity_layer.latent.cases import CASES
from ambiguity_layer.latent.decide import classify


def main() -> None:
    labels = ["decision", "latent", "none"]
    matrix = {gold: {pred: 0 for pred in labels} for gold in labels}
    rows = []
    correct = 0
    for case in CASES:
        result = classify(
            case["readings"],
            case["immediate_answers"],
            case["followup_answers"],
        )
        predicted = result["label"]
        gold = case["gold"]
        match = predicted == gold
        correct += int(match)
        matrix[gold][predicted] += 1
        rows.append(
            {
                "id": case["id"],
                "gold": gold,
                "predicted": predicted,
                "action": result["action"],
                "reason": result["reason"],
                "match": match,
            }
        )
    n = len(CASES)
    summary = {
        "n": n,
        "correct": correct,
        "accuracy": round(correct / n, 3),
        "matrix": matrix,
        "asked_on_latent": sum(
            1 for row in rows if row["gold"] == "latent" and row["action"] == "ask"
        ),
        "assumed_on_latent": sum(
            1
            for row in rows
            if row["gold"] == "latent" and row["action"] == "answer_with_assumption"
        ),
        "asked_on_decision": sum(
            1 for row in rows if row["gold"] == "decision" and row["action"] == "ask"
        ),
    }
    out = ROOT / "results" / "latent_eval.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "results": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {out}")
    if correct != n:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
