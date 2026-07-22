from __future__ import annotations

from sidecar.retrieval import score_text


def test_score_text_prefers_related_content() -> None:
    related = score_text("incremental context", "incremental derived context")
    unrelated = score_text("incremental context", "A recipe for pasta")
    assert related > unrelated
