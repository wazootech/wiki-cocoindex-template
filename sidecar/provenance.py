from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


EMBEDDING_DIMENSIONS = 16
DEFAULT_SOURCE_GRAPH = "https://wazootech.github.io/wiki-cocoindex-template/wiki/"


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    page_path: str
    page_title: str
    heading: str
    fragment: str
    text: str
    source_graph: str
    content_hash: str
    source_mtime: str
    derived_at: str
    wiki_lock_hash: str
    metadata: dict[str, object]
    embedding: list[float]


def stable_hash(*parts: str) -> str:
    digest = sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def make_chunk_id(page_path: str, heading: str, text: str) -> str:
    return f"sha256:{stable_hash(page_path, heading, text)[:32]}"


def content_hash(text: str) -> str:
    return f"sha256:{stable_hash(text)[:32]}"


def file_mtime_iso(path: Path) -> str:
    return f"{path.stat().st_mtime_ns}"


def wiki_lock_hash(wiki_root: Path) -> str:
    lock_path = wiki_root.parent / "wiki.lock"
    if not lock_path.exists():
        return "none"
    return f"sha256:{stable_hash(lock_path.read_text(encoding='utf-8'))[:32]}"


def as_jsonable(record: ChunkRecord) -> dict[str, object]:
    return asdict(record)
