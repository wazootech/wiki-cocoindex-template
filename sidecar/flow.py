"""CocoIndex starter flow.

This file shows the intended incremental sidecar. The runnable local demo lives in
scripts/load_index.py so the template works without the CocoIndex package installed.
"""

from __future__ import annotations

import pathlib

import cocoindex as coco
from cocoindex.connectors import localfs, postgres
from cocoindex.ops.text import RecursiveSplitter
from pgvector.psycopg import register_vector

from sidecar.retrieval import embed_text


DATABASE_URL = "postgresql://cocoindex:cocoindex@localhost:5432/wiki_cocoindex"
TABLE_NAME = "wiki_chunks"


class WikiChunk:
    def __init__(
        self,
        chunk_id: str,
        page_path: str,
        page_title: str,
        heading: str,
        fragment: str,
        text: str,
        source_graph: str,
        content_hash: str,
        source_mtime: str,
        metadata: dict,
        embedding: list[float],
    ) -> None:
        self.chunk_id = chunk_id
        self.page_path = page_path
        self.page_title = page_title
        self.heading = heading
        self.fragment = fragment
        self.text = text
        self.source_graph = source_graph
        self.content_hash = content_hash
        self.source_mtime = source_mtime
        self.metadata = metadata
        self.embedding = embedding


@coco.fn
async def process_file(file, table) -> None:
    text = await file.read_text()
    splitter = RecursiveSplitter()
    for chunk in splitter.split(text):
        table.declare_row(
            row=WikiChunk(
                chunk_id=f"sha256:{chunk.start.line}-{chunk.end.line}",
                page_path=str(file.file_path.path),
                page_title=file.file_path.path.stem.replace("_", " "),
                heading="",
                fragment="",
                text=chunk.text,
                source_graph="https://wazootech.github.io/wiki-cocoindex-template/wiki/",
                content_hash=f"sha256:{len(chunk.text)}",
                source_mtime="",
                metadata={},
                embedding=embed_text(chunk.text),
            )
        )


@coco.fn
async def app_main(sourcedir: pathlib.Path) -> None:
    target_table = await postgres.mount_table_target(
        "wiki_cocoindex",
        table_name=TABLE_NAME,
        table_schema=await postgres.TableSchema.from_class(
            WikiChunk,
            primary_key=["chunk_id"],
        ),
    )
    target_table.declare_vector_index(column="embedding")
    files = localfs.walk_dir(sourcedir, recursive=True, live=True)
    await coco.mount_each(process_file, files.items(), target_table)


app = coco.App(
    coco.AppConfig(name="WikiCocoIndexTemplate"),
    app_main,
    sourcedir=pathlib.Path(__file__).parent.parent / "wiki",
)
