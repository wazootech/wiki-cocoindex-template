from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sidecar.manifest import build_manifest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = build_manifest(root / "wiki", root / ".build" / "wiki-manifest")
    print(
        f"wrote {summary['pages']} pages, {summary['chunks']} chunks, "
        f"{summary['links']} links"
    )


if __name__ == "__main__":
    main()
