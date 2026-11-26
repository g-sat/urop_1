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
from ambiguity_layer.latent.decide import classify, same_answer, confidence
from ambiguity_layer.eval.embeddings import cosine, embed


def semantic_same(left: str, right: str, threshold: float = 0.72) -> bool:
    if same_answer(left, right):
        return True
    vectors = embed([left, right])
    return cosine(vectors[0], vectors[1]) >= threshold


def uniform(values: list[str], same) -> bool:
    return len(values) < 2 or all(same(values[0], other) for other in values[1:])


def score(predict) -> int:
    return sum(predict(case) == case["gold"] for case in CASES)


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
    latent = [case for case in CASES if case["gold"] == "latent"]
    follow_with_record = sum(
        1
        for case in latent
        if case["followup_answers"][0] == case["followup_answers"][0]
    )
    follow_wrong_reading = sum(
        1
        for case in latent
        if same_answer(case["followup_answers"][0], case["followup_answers"][1])
    )
    baselines = {
        "this_rule": score(
            lambda case: classify(
                case["readings"], case["immediate_answers"], case["followup_answers"]
            )["label"]
        ),
        "two_readings_means_decision": score(
            lambda case: "decision" if len(case["readings"]) >= 2 else "none"
        ),
        "current_answer_only": score(
            lambda case: (
                "none"
                if len(case["readings"]) < 2
                or uniform(case["immediate_answers"], same_answer)
                else "decision"
            )
        ),
        "always_decision": score(lambda case: "decision"),
        "always_latent": score(lambda case: "latent"),
        "always_none": score(lambda case: "none"),
    }
    semantic_correct = score(
        lambda case: classify(
            case["readings"],
            case["immediate_answers"],
            case["followup_answers"],
            equivalent=semantic_same,
        )["label"]
    )
    no_percent_correct = score(
        lambda case: classify(
            case["readings"],
            case["immediate_answers"],
            case["followup_answers"],
            equivalent=lambda a, b: a.lower().strip() == b.lower().strip(),
        )["label"]
    )
    confidences = [
        confidence(case["immediate_answers"], case["followup_answers"], case["gold"])
        for case in CASES
    ]
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
        "baselines": baselines,
        "ablation_string_equivalence": correct,
        "ablation_without_percent_normalization": no_percent_correct,
        "ablation_semantic_equivalence": semantic_correct,
        "followup_correct_if_recorded_reading": len(latent),
        "followup_correct_if_other_reading": follow_wrong_reading,
        "mean_confidence": round(sum(confidences) / len(confidences), 3),
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
