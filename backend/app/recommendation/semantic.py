from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once per process and reuse it for requests."""
    return SentenceTransformer(MODEL_NAME)


def cosine_similarity(first: Sequence[float], second: Sequence[float]) -> float:
    """Return cosine similarity, defensively returning zero for invalid vectors."""
    left = np.asarray(first, dtype=float)
    right = np.asarray(second, dtype=float)
    if left.size == 0 or right.size == 0 or left.shape != right.shape:
        return 0.0
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    if denominator == 0:
        return 0.0
    return float(np.dot(left, right) / denominator)


@lru_cache(maxsize=512)
def embed_text(text: str) -> list[float]:
    """Encode a small free-text value once and cache it for the process lifetime."""
    vector = get_embedding_model().encode(text, normalize_embeddings=False)
    return vector.astype(float).tolist()
