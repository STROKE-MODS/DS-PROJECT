from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class InternshipEmbeddingIndex:
    ids: tuple[int, ...]
    normalized_description_matrix: np.ndarray

    def similarities(self, interest_embedding: Sequence[float]) -> np.ndarray:
        vector = np.asarray(interest_embedding, dtype=float)
        norm = np.linalg.norm(vector)
        if norm == 0:
            return np.zeros(len(self.ids), dtype=float)
        return self.normalized_description_matrix @ (vector / norm)

    def similarity(self, internship_id: int, interest_embedding: Sequence[float]) -> float:
        try:
            row = self.ids.index(internship_id)
        except ValueError:
            return 0.0
        return float(self.similarities(interest_embedding)[row])


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once per process and reuse it for requests."""
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=512)
def embed_text(text: str) -> list[float]:
    """Encode a small free-text value once and cache it for the process lifetime."""
    vector = get_embedding_model().encode(text, normalize_embeddings=False)
    return vector.astype(float).tolist()


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


_INDEX: InternshipEmbeddingIndex | None = None


def prepare_internship_embedding_index(internships) -> InternshipEmbeddingIndex:
    """Build the 500-row normalized matrix once and reuse it until IDs change."""
    global _INDEX
    ids = tuple(item.id for item in internships)
    if _INDEX is not None and _INDEX.ids == ids:
        return _INDEX
    vectors = [item.description_embedding for item in internships]
    matrix = np.asarray(vectors, dtype=float)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms != 0)
    _INDEX = InternshipEmbeddingIndex(ids=ids, normalized_description_matrix=normalized)
    return _INDEX
