from __future__ import annotations

from pathlib import Path

from sidecar.manifest import build_manifest, load_chunks


def test_manifest_builds_chunk_and_link_files(tmp_path: Path) -> None:
    wiki_root = tmp_path / "wiki"
    wiki_root.mkdir()
    (wiki_root / "A_Page.md").write_text(
        """---
type: schema:CreativeWork
---

# A Page

Intro text.

## Details

See [another page](Another_Page.md).
""",
        encoding="utf-8",
    )
    (wiki_root / "Another_Page.md").write_text(
        "# Another Page\n\nTarget text.\n",
        encoding="utf-8",
    )

    summary = build_manifest(wiki_root, tmp_path / ".build" / "wiki-manifest")

    assert summary == {"pages": 2, "chunks": 3, "links": 1}
    chunks = load_chunks(tmp_path / ".build" / "wiki-manifest")
    assert {row["page_path"] for row in chunks} == {"A_Page.md", "Another_Page.md"}
    assert any(row["heading"] == "Details" for row in chunks)
