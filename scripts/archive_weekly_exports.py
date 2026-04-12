#!/usr/bin/env python3
"""Archive current weekly PNG exports into a dated snapshot folder."""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEEKLY_DIR = ROOT / "exports" / "wepoll-panic" / "weekly"
FILES = ["timeseries.png", "bubble.png"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="snapshot_date", default=str(date.today()), help="Snapshot date in YYYY-MM-DD")
    args = parser.parse_args()

    target_dir = WEEKLY_DIR / args.snapshot_date
    target_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for name in FILES:
        src = WEEKLY_DIR / name
        if not src.exists():
            raise SystemExit(f"Missing weekly export: {src}")
        dst = target_dir / name
        shutil.copy2(src, dst)
        copied.append(str(dst))

    print("\n".join(copied))


if __name__ == "__main__":
    main()
