"""Hybrid evaluation: SBERT (+ optional NLI). No lexical word-overlap judging."""

from __future__ import annotations

from typing import Any

from ambiguity_layer.eval.embeddings import best_clarification_similarity
from ambiguity_layer.eval.nli import clarification_nli


def score_clarification(
    questions: list[str],
    gold: str,
    *,
    use_nli: bool = True,
) -> dict[str, Any]:
    sbert = best_clarification_similarity(questions, gold)
    out: dict[str, Any] = {
        "sbert": sbert,
        "clarification_score": sbert["score"],
        "clarification_match": sbert["match"],
        "method": "sbert",
    }
    if use_nli:
        try:
            nli = clarification_nli(questions, gold)
            out["nli"] = nli
            # Combine: average scores; match if either says match and mean >= 0.5
            combined = 0.5 * (sbert["score"] + nli["score"])
            out["clarification_score"] = round(combined, 4)
            out["clarification_match"] = bool(
                (sbert["match"] or nli["match"]) and combined >= 0.45
            )
            out["method"] = "sbert+nli"
        except Exception as exc:  # noqa: BLE001
            out["nli_error"] = str(exc)
    return out


def score_clause_semantic(predicted: str, gold: str, prompt: str) -> dict[str, Any]:
    """Embedding similarity between clauses, lightly contextualized by prompt."""
    from ambiguity_layer.eval.embeddings import cosine, embed

    p = (predicted or "").strip()
    g = (gold or "").strip()
    if not p or not g:
        return {"clause_score": 0.0, "clause_hit": False, "method": "sbert"}

    # Encode clause alone and "clause in prompt" style strings
    texts = [p, g, f"{p} || {prompt[:300]}", f"{g} || {prompt[:300]}"]
    vecs = embed(texts)
    score = max(cosine(vecs[0], vecs[1]), cosine(vecs[2], vecs[3]))
    return {
        "clause_score": round(float(score), 4),
        "clause_hit": float(score) >= 0.45,
        "method": "sbert",
        "threshold": 0.45,
    }


def types_equal(predicted: str | None, gold: str | None) -> bool:
    return (predicted or "").strip().lower() == (gold or "").strip().lower()
