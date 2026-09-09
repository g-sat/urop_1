"""Sentence embedding utilities (SBERT)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ambiguity_layer import config


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL)


def embed(texts: list[str]) -> np.ndarray:
    model = get_embedder()
    return np.asarray(model.encode(texts, normalize_embeddings=True))


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def best_clarification_similarity(questions: list[str], gold: str) -> dict:
    """Max cosine similarity between any predicted question and gold clarification."""
    qs = [q.strip() for q in questions if q and str(q).strip()]
    gold = (gold or "").strip()
    if not qs or not gold:
        return {"score": 0.0, "match": False, "best_question": None, "method": "sbert"}

    vectors = embed(qs + [gold])
    q_vecs, g_vec = vectors[:-1], vectors[-1]
    scores = [cosine(v, g_vec) for v in q_vecs]
    best_i = int(np.argmax(scores))
    score = float(scores[best_i])
    return {
        "score": round(score, 4),
        "match": score >= 0.55,
        "best_question": qs[best_i],
        "method": "sbert",
        "threshold": 0.55,
    }
