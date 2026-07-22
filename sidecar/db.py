"""Database connection helpers.

Tries Docker Postgres first, falls back to PGlite (zero-Docker local mode).
"""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres@localhost:5432/postgres"
)

_PGLITE_DATA_DIR = Path(tempfile.gettempdir()) / "wiki-cocoindex-pglite"


def _docker_available() -> bool:
    try:
        import psycopg

        with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _pglite_connect(schema_sql: str | None = None) -> object:
    from py_pglite import PGliteConfig, PGliteManager
    from pgvector.psycopg import register_vector
    import psycopg

    _PGLITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config = PGliteConfig(
        extensions=["pgvector"],
        data_dir=str(_PGLITE_DATA_DIR),
    )
    manager = PGliteManager(config=config)
    dsn = manager.get_dsn()
    conn = psycopg.connect(dsn, autocommit=True)
    register_vector(conn)
    if schema_sql:
        with conn.cursor() as cur:
            for statement in (s.strip() for s in schema_sql.split(";") if s.strip()):
                cur.execute(f"{statement};")
    return conn


@contextmanager
def connect(schema_sql: str | None = None) -> Iterator:
    """Yield a psycopg connection, preferring Docker Postgres, falling back to PGlite."""
    if _docker_available():
        import psycopg
        from pgvector.psycopg import register_vector

        conn = psycopg.connect(DATABASE_URL, connect_timeout=2)
        register_vector(conn)
        try:
            if schema_sql:
                with conn.cursor() as cur:
                    for statement in (s.strip() for s in schema_sql.split(";") if s.strip()):
                        cur.execute(f"{statement};")
            yield conn
        finally:
            conn.close()
    else:
        conn = _pglite_connect(schema_sql)
        try:
            yield conn
        finally:
            conn.close()
