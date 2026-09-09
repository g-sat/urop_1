"""Optional NLI / cross-encoder entailment for clarification equivalence."""

from __future__ import annotations

from functools import lru_cache

from ambiguity_layer import config


@lru_cache(maxsize=1)
def _cross_encoder():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(config.NLI_MODEL)


def clarification_nli(questions: list[str], gold: str) -> dict:
    """
    Score whether predicted questions ask for the same info as gold.

    Uses an NLI cross-encoder on paired texts. For models that output
    [contradiction, entailment, neutral] or a single relevance score,
    we normalize to a [0,1] equivalence score.
    """
    qs = [q.strip() for q in questions if q and str(q).strip()]
    gold = (gold or "").strip()
    if not qs or not gold:
        return {"score": 0.0, "match": False, "best_question": None, "method": "nli"}

    model = _cross_encoder()
    pairs = [(gold, q) for q in qs] + [(q, gold) for q in qs]
    raw = model.predict(pairs)

    scores: list[float] = []
    # raw may be (n, 3) or (n,)
    import numpy as np

    arr = np.asarray(raw)
    n = len(qs)
    for i in range(n):
        # average both directions
        s1 = _score_one(arr[i])
        s2 = _score_one(arr[i + n])
        scores.append(0.5 * (s1 + s2))

    best_i = int(np.argmax(scores))
    score = float(scores[best_i])
    return {
        "score": round(score, 4),
        "match": score >= 0.5,
        "best_question": qs[best_i],
        "method": "nli",
        "threshold": 0.5,
    }


def _score_one(row) -> float:
    import numpy as np

    row = np.asarray(row)
    if row.ndim == 0:
        # single logit/score — map via sigmoid-ish clip
        return float(1 / (1 + np.exp(-float(row))))
    if row.shape[-1] == 3:
        # contradiction, entailment, neutral (common order varies).
        # Take max(entailment-like) approx: index 1 often entailment for MNLI-style.
        # Also consider (entailment - contradiction).
        contra, ent, neu = float(row[0]), float(row[1]), float(row[2])
        # softmax
        ex = np.exp(row - np.max(row))
        prob = ex / ex.sum()
        return float(prob[1])  # entailment probability
    return float(np.max(row))
