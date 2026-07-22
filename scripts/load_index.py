from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.errors import DuplicateObject, UniqueViolation
from pgvector.psycopg import register_vector

from sidecar.manifest import load_chunks


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres@localhost:5432/postgres"
)


def ensure_vector_extension() -> None:
    with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        except (DuplicateObject, UniqueViolation):
            conn.rollback()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    chunks = load_chunks(root / ".build" / "wiki-manifest")
    try:
        ensure_vector_extension()
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                schema_sql = (root / "sidecar" / "schema.sql").read_text(encoding="utf-8")
                for statement in (part.strip() for part in schema_sql.split(";") if part.strip()):
                    cur.execute(f"{statement};")
                cur.execute("SELECT chunk_id FROM wiki_chunks")
                existing = {row[0] for row in cur.fetchall()}
                active = {chunk["chunk_id"] for chunk in chunks}
                stale = existing - active
                if stale:
                    cur.execute("DELETE FROM wiki_chunks WHERE chunk_id = ANY(%s)", (sorted(stale),))
                for chunk in chunks:
                    cur.execute(
                        """
                        INSERT INTO wiki_chunks (
                            chunk_id, page_path, page_title, heading, fragment, text,
                            source_graph, content_hash, source_mtime, indexed_at, metadata, embedding
                        ) VALUES (
                            %(chunk_id)s, %(page_path)s, %(page_title)s, %(heading)s, %(fragment)s,
                            %(text)s, %(source_graph)s, %(content_hash)s, %(source_mtime)s,
                            now(), %(metadata)s::jsonb, %(embedding)s
                        )
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            page_path = EXCLUDED.page_path,
                            page_title = EXCLUDED.page_title,
                            heading = EXCLUDED.heading,
                            fragment = EXCLUDED.fragment,
                            text = EXCLUDED.text,
                            source_graph = EXCLUDED.source_graph,
                            content_hash = EXCLUDED.content_hash,
                            source_mtime = EXCLUDED.source_mtime,
                            indexed_at = now(),
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                        """,
                        {
                            **chunk,
                            "metadata": json.dumps(chunk["metadata"], ensure_ascii=True),
                        },
                    )
            conn.commit()
        print(f"loaded {len(chunks)} chunks")
    except Exception as exc:
        print(f"database unavailable, skipped load: {exc.__class__.__name__}: {exc}")


if __name__ == "__main__":
    main()
