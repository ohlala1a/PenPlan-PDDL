"""Simple hashing-based embedding utilities used for retrieval scoring.

These utilities avoid external dependencies while providing deterministic
vector representations and cosine similarity computations."""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, List


class HashingVectorizer:
    """Produces fixed-size vectors using a hashing trick."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def encode(self, text: str) -> List[float]:
        tokens = list(_tokenize(text))
        if not tokens:
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions
        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimensions
            magnitude = (int(digest[8:16], 16) % 1000) / 1000.0 + 0.1
            vector[index] += magnitude

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0.0:
            return vector
        return [component / norm for component in vector]


def cosine_similarity(lhs: Iterable[float], rhs: Iterable[float]) -> float:
    lhs_list = list(lhs)
    rhs_list = list(rhs)
    if len(lhs_list) != len(rhs_list):
        raise ValueError("Vectors must share the same dimensionality")
    numerator = sum(x * y for x, y in zip(lhs_list, rhs_list))
    lhs_norm = math.sqrt(sum(x * x for x in lhs_list))
    rhs_norm = math.sqrt(sum(y * y for y in rhs_list))
    if lhs_norm == 0.0 or rhs_norm == 0.0:
        return 0.0
    return numerator / (lhs_norm * rhs_norm)


def _tokenize(text: str) -> Iterable[str]:
    cleaned = (
        text.lower()
        .replace("-", " ")
        .replace("/", " ")
        .replace("_", " ")
        .replace(",", " ")
        .replace(".", " ")
    )
    for token in cleaned.split():
        stripped = token.strip()
        if stripped:
            yield stripped
