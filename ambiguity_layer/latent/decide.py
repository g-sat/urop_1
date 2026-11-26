"""Latent versus decision ambiguity.

Called by tests/test_latent.py and scripts/eval_latent.py.
No existing file separates an answer that changes now from an answer that
is the same now but splits on a follow-up. The cycled benchmark types are not used.

User instruction: "do this then i need you to evaluate this and check clearly with ecc after u impliment thjs"
"""

from __future__ import annotations

import re

DECISION = "decision"
LATENT = "latent"
NONE = "none"


def _normalize(text: str) -> str:
    value = (text or "").lower().strip()
    value = value.replace("%", " percent ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def same_answer(left: str, right: str) -> bool:
    return _normalize(left) == _normalize(right)


def _all_same(values: list[str]) -> bool:
    if len(values) < 2:
        return True
    first = values[0]
    return all(same_answer(first, other) for other in values[1:])


def classify(
    readings: list[str],
    immediate_answers: list[str],
    followup_answers: list[str],
    equivalent=None,
) -> dict[str, str]:
    """Classify from the answers under each reading.

    decision: ask now, because the readings change the immediate answer.
    latent: do not ask on this turn. The immediate answer matches, and the
    follow-up does not. Answer under a recorded assumption.
    none: one reading, or neither answer changes.
    """
    if len(readings) < 2:
        return {"label": NONE, "action": "answer", "reason": "one reading"}
    if len(immediate_answers) != len(readings) or len(followup_answers) != len(readings):
        raise ValueError("readings, immediate answers, and follow-up answers must align")

    same = equivalent or same_answer

    def uniform(values: list[str]) -> bool:
        if len(values) < 2:
            return True
        return all(same(values[0], other) for other in values[1:])

    if not uniform(immediate_answers):
        return {
            "label": DECISION,
            "action": "ask",
            "reason": "immediate answers differ",
        }
    if not uniform(followup_answers):
        return {
            "label": LATENT,
            "action": "answer_with_assumption",
            "reason": "immediate answers match and the follow-up splits",
        }
    return {
        "label": NONE,
        "action": "answer",
        "reason": "readings change neither the answer nor the follow-up",
    }


def confidence(immediate_answers: list[str], followup_answers: list[str], label: str) -> float:
    """Margin of the label. 1 is a clean split or a clean match. Not a probability."""
    from ambiguity_layer.eval.embeddings import cosine, embed

    def mean_sim(values: list[str]) -> float:
        if len(values) < 2:
            return 1.0
        vectors = embed(values)
        sims = [cosine(vectors[0], vectors[i]) for i in range(1, len(vectors))]
        return float(sum(sims) / len(sims))

    immediate = mean_sim(immediate_answers)
    follow = mean_sim(followup_answers)
    if label == DECISION:
        return round(max(0.0, min(1.0, 1.0 - immediate)), 3)
    if label == LATENT:
        return round(max(0.0, min(1.0, immediate * (1.0 - follow))), 3)
    return round(max(0.0, min(1.0, min(immediate, follow))), 3)
