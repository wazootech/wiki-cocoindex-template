from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sidecar.db import connect
from sidecar.manifest import load_chunks
from sidecar.retrieval import embed_text, score_text


def _query_db(query: str, limit: int) -> list[dict[str, object]]:
    query_embedding = embed_text(query)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT page_path, page_title, heading, fragment, content_hash,
                       wiki_lock_hash, text, embedding <=> %s AS distance
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
            "wiki_lock_hash": row[5],
            "text": row[6],
            "score": round(1.0 - float(row[7]), 6),
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
                "wiki_lock_hash": chunk.get("wiki_lock_hash", "none"),
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
        print(f"  content={row['content_hash']} lock={row['wiki_lock_hash']}")
        print(f"  {json.dumps(row['text'][:240], ensure_ascii=True)}")


if __name__ == "__main__":
    main()
