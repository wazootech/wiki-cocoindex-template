from __future__ import annotations

import math
import re
from collections.abc import Iterable
from hashlib import sha256

from .provenance import EMBEDDING_DIMENSIONS


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    tokens = tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:2], "big") % dimensions
        weight = (int.from_bytes(digest[2:6], "big") / 2**32) * 2.0 - 1.0
        vector[slot] += weight

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    return sum(l * r for l, r in zip(left_values, right_values))


def score_text(query: str, text: str) -> float:
    return cosine_similarity(embed_text(query), embed_text(text))


def best_heading(page_title: str, heading: str) -> str:
    return heading or page_title
