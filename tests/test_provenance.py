from __future__ import annotations

from sidecar.provenance import content_hash, make_chunk_id
from sidecar.retrieval import embed_text


def test_chunk_ids_are_stable() -> None:
    left = make_chunk_id("wiki/Page.md", "Details", "Hello world")
    right = make_chunk_id("wiki/Page.md", "Details", "Hello world")
    assert left == right
    assert left.startswith("sha256:")


def test_hash_embeddings_have_fixed_length() -> None:
    vector = embed_text("fresh context for agents")
    assert len(vector) == 16
    assert content_hash("abc").startswith("sha256:")
