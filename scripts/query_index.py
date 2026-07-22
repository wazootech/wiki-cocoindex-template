from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.errors import DuplicateObject, UniqueViolation
from pgvector.psycopg import register_vector

from sidecar.manifest import load_chunks
from sidecar.retrieval import embed_text, score_text


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


def _query_db(query: str, limit: int) -> list[dict[str, object]]:
    query_embedding = embed_text(query)
    ensure_vector_extension()
    with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT page_path, page_title, heading, fragment, content_hash,
                       text, embedding <=> %s AS distance
                FROM wiki_chunks
                ORDER BY distance ASC
                LIMIT %s
                """,
                (query_embedding, limit),
            )
            rows = cur.fetchall()
    return [
        {
            "page_path": row[0],
            "page_title": row[1],
            "heading": row[2],
            "fragment": row[3],
            "content_hash": row[4],
            "text": row[5],
            "score": round(1.0 - float(row[6]), 6),
        }
        for row in rows
    ]


def _query_manifest(query: str, limit: int) -> list[dict[str, object]]:
    root = Path(__file__).resolve().parents[1]
    chunks = load_chunks(root / ".build" / "wiki-manifest")
    ranked = sorted(
        (
            {
                "page_path": chunk["page_path"],
                "page_title": chunk["page_title"],
                "heading": chunk["heading"],
                "fragment": chunk["fragment"],
                "content_hash": chunk["content_hash"],
                "text": chunk["text"],
                "score": round(score_text(query, str(chunk["text"])), 6),
            }
            for chunk in chunks
        ),
        key=lambda row: row["score"],
        reverse=True,
    )
    return ranked[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        rows = _query_db(args.query, args.limit)
    except Exception:
        rows = _query_manifest(args.query, args.limit)

    for row in rows:
        print(f"[{row['score']:.3f}] {row['page_title']} > {row['heading']}")
        print(f"  {row['page_path']}#{row['fragment']}")
        print(f"  {row['content_hash']}")
        print(f"  {json.dumps(row['text'][:240], ensure_ascii=True)}")


if __name__ == "__main__":
    main()
