from __future__ import annotations

import shutil
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sidecar.manifest import build_manifest, load_chunks


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        demo_root = Path(tmp) / "demo"
        shutil.copytree(root / "wiki", demo_root / "wiki")

        first = build_manifest(demo_root / "wiki", demo_root / ".build" / "wiki-manifest")
        before = {row["chunk_id"]: row for row in load_chunks(demo_root / ".build" / "wiki-manifest")}

        target = demo_root / "wiki" / "CocoIndex_Sidecar.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "\nThis line proves incremental refresh.\n",
            encoding="utf-8",
        )

        second = build_manifest(demo_root / "wiki", demo_root / ".build" / "wiki-manifest")
        after = {row["chunk_id"]: row for row in load_chunks(demo_root / ".build" / "wiki-manifest")}

        changed = sorted(set(before) ^ set(after))
        print(f"before: {first}")
        print(f"after: {second}")
        print(f"changed chunk ids: {changed}")


if __name__ == "__main__":
    main()
