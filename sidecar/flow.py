"""CocoIndex incremental flow — Wiki SDK + @coco.fn integration.

Keeps a pgvector index in sync with the wiki corpus. When a wiki page
changes (added, edited, or deleted), only the affected chunks re-process.

Usage:
    pip install -r requirements-cocoindex.txt
    cocoindex update sidecar/flow.py

The zero-dependency path (build_manifest -> load_index -> query_index)
remains the primary demo. This file shows the full CocoIndex integration.
"""

from __future__ import annotations

import pathlib
import re
from datetime import UTC, datetime
from typing import AsyncIterator

import asyncpg
import cocoindex as coco
from cocoindex.connectors import localfs, postgres
from cocoindex.ops.text import RecursiveSplitter
from wiki.parser import split_frontmatter_body

from sidecar.provenance import DEFAULT_SOURCE_GRAPH, content_hash, make_chunk_id, wiki_lock_hash
from sidecar.retrieval import embed_text

DATABASE_URL = "postgresql://cocoindex:cocoindex@localhost:5432/wiki_cocoindex"
TABLE_NAME = "wiki_chunks"

PG_DB = coco.ContextKey[asyncpg.Pool]("wiki_pg")

WIKI_TABLE_SCHEMA = postgres.TableSchema(
    {
        "chunk_id": postgres.ColumnDef(type="text", nullable=False),
        "page_path": postgres.ColumnDef(type="text", nullable=False),
        "page_title": postgres.ColumnDef(type="text", nullable=False),
        "heading": postgres.ColumnDef(type="text", nullable=False),
        "fragment": postgres.ColumnDef(type="text", nullable=False),
        "text": postgres.ColumnDef(type="text", nullable=False),
        "source_graph": postgres.ColumnDef(type="text", nullable=False),
        "content_hash": postgres.ColumnDef(type="text", nullable=False),
        "source_mtime": postgres.ColumnDef(type="text", nullable=False),
        "derived_at": postgres.ColumnDef(type="text", nullable=False),
        "wiki_lock_hash": postgres.ColumnDef(type="text", nullable=False),
        "metadata": postgres.ColumnDef(type="jsonb", nullable=False),
        "embedding": postgres.ColumnDef(type="vector(16)", nullable=False),
    },
    primary_key=["chunk_id"],
)


@coco.lifespan
async def coco_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    async with await asyncpg.create_pool(DATABASE_URL) as pool:
        builder.provide(PG_DB, pool)
        yield


def _page_title(body: str, stem: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return stem.replace("_", " ")


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def _nearest_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


@coco.fn(memo=True)
async def process_file(
    file: localfs.File,
    table: postgres.TableTarget,
    wiki_root: pathlib.Path,
    source_graph: str,
) -> None:
    raw = await file.read_text()
    frontmatter, body = split_frontmatter_body(raw)
    page_path_str = str(file.file_path.path)
    stem = file.file_path.path.stem
    title = _page_title(body, stem)
    lock_hash = wiki_lock_hash(wiki_root)
    mtime = datetime.fromtimestamp(
        file.file_path.resolve().stat().st_mtime, tz=UTC
    ).isoformat()

    splitter = RecursiveSplitter()
    for chunk in splitter.split(body, language="markdown"):
        heading = _nearest_heading(chunk.text)
        fragment = _slugify(heading or title)
        table.declare_row(
            row={
                "chunk_id": make_chunk_id(page_path_str, heading, chunk.text),
                "page_path": page_path_str,
                "page_title": title,
                "heading": heading,
                "fragment": fragment,
                "text": chunk.text,
                "source_graph": source_graph,
                "content_hash": content_hash(chunk.text),
                "source_mtime": mtime,
                "derived_at": datetime.now(tz=UTC).isoformat(),
                "wiki_lock_hash": lock_hash,
                "metadata": frontmatter or {},
                "embedding": embed_text(chunk.text),
            }
        )


@coco.fn
async def app_main(sourcedir: pathlib.Path) -> None:
    target = await postgres.mount_table_target(
        PG_DB,
        TABLE_NAME,
        WIKI_TABLE_SCHEMA,
    )
    target.declare_vector_index(column="embedding", metric="cosine")
    files = localfs.walk_dir(sourcedir, recursive=True, live=True)
    await coco.mount_each(
        process_file,
        files.items(),
        target,
        sourcedir,
        DEFAULT_SOURCE_GRAPH,
    )


app = coco.App(
    coco.AppConfig(name="WikiCocoIndexSidecar"),
    app_main,
    sourcedir=pathlib.Path(__file__).resolve().parent.parent / "wiki",
)
