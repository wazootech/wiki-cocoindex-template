"""Run the CocoIndex incremental flow."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    flow = str(Path(__file__).resolve().parent.parent / "sidecar" / "flow.py")
    subprocess.run(
        [sys.executable, "-m", "cocoindex", "update", flow],
        check=True,
    )


if __name__ == "__main__":
    main()
