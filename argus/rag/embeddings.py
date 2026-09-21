"""Embedding interfaces with a deterministic local implementation for tests."""

from collections.abc import Sequence
from hashlib import sha256
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    dimension: int

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...


class HashEmbedder:
    """Dependency-light, deterministic embedding baseline; replace in production."""

    def __init__(self, dimension: int = 256) -> None:
        self.dimension = dimension

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype="float32")
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                vectors[row, index] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)

