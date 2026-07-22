from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - dependency is present in CI.
    yaml = None

from .provenance import ChunkRecord, DEFAULT_SOURCE_GRAPH, content_hash, make_chunk_id, wiki_lock_hash
from .retrieval import embed_text


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end() :]
    data = yaml.safe_load(raw) if yaml is not None else {}
    return (data or {}), body


def _page_title(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("_", " ")


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def _split_sections(body: str, page_title: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_heading = page_title
    current_lines: list[str] = []
    seen_top_heading = False

    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            heading = match.group(2).strip()
            if level == 1 and not seen_top_heading:
                seen_top_heading = True
                current_heading = heading
                current_lines = []
                continue
            if level >= 2:
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines).strip()))
                current_heading = heading
                current_lines = []
                continue
        if seen_top_heading or not current_lines:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    if not sections and body.strip():
        sections.append((page_title, body.strip()))
    return [(heading, text) for heading, text in sections if text]


def _links(body: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for target in WIKILINK_RE.findall(body):
        results.append((target, "wikilink"))
    for target in MARKDOWN_LINK_RE.findall(body):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        results.append((target, "markdown"))
    return results


def page_records(path: Path, wiki_root: Path, source_graph: str = DEFAULT_SOURCE_GRAPH, lock_hash: str = "none") -> tuple[dict[str, object], list[ChunkRecord], list[dict[str, str]]]:
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(raw)
    title = _page_title(path, body)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
    page_path = str(path.relative_to(wiki_root)).replace("\\", "/")
    chunks: list[ChunkRecord] = []

    for heading, text in _split_sections(body, title):
        fragment = _slugify(heading)
        record = ChunkRecord(
            chunk_id=make_chunk_id(page_path, heading, text),
            page_path=page_path,
            page_title=title,
            heading=heading,
            fragment=fragment,
            text=text,
            source_graph=source_graph,
            content_hash=content_hash(text),
            source_mtime=mtime,
            derived_at=datetime.now(tz=UTC).isoformat(),
            wiki_lock_hash=lock_hash,
            metadata={"frontmatter": frontmatter},
            embedding=embed_text(text),
        )
        chunks.append(record)

    link_rows = [
        {"source_path": page_path, "target": target, "kind": kind}
        for target, kind in _links(body)
    ]
    page_row = {
        "page_path": page_path,
        "page_title": title,
        "content_hash": content_hash(raw),
        "source_mtime": mtime,
        "source_graph": source_graph,
    }
    return page_row, chunks, link_rows


def build_manifest(wiki_root: Path, build_dir: Path, source_graph: str = DEFAULT_SOURCE_GRAPH) -> dict[str, int]:
    build_dir.mkdir(parents=True, exist_ok=True)
    lock_hash = wiki_lock_hash(wiki_root)
    pages: list[dict[str, object]] = []
    chunks: list[dict[str, object]] = []
    links: list[dict[str, str]] = []

    for path in sorted(wiki_root.glob("**/*.md")):
        page_row, page_chunks, page_links = page_records(path, wiki_root, source_graph, lock_hash)
        pages.append(page_row)
        chunks.extend(asdict(chunk) for chunk in page_chunks)
        links.extend(page_links)

    _write_jsonl(build_dir / "pages.jsonl", pages)
    _write_jsonl(build_dir / "chunks.jsonl", chunks)
    _write_jsonl(build_dir / "links.jsonl", links)
    _write_trig(build_dir / "graph.trig", pages, chunks, source_graph)
    return {"pages": len(pages), "chunks": len(chunks), "links": len(links)}


def load_chunks(build_dir: Path) -> list[dict[str, object]]:
    path = build_dir / "chunks.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True))
            handle.write("\n")


def _write_trig(path: Path, pages: list[dict[str, object]], chunks: list[dict[str, object]], source_graph: str) -> None:
    lines = [
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix schema: <https://schema.org/> .",
        "",
        f"<{source_graph}> {{",
        f'  <{source_graph}> dcterms:title "Wiki CocoIndex template" .',
        f'  <{source_graph}> schema:datasetSize "{len(pages)} pages" .',
        f'  <{source_graph}> schema:articleBody "{len(chunks)} chunks" .',
        "}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
