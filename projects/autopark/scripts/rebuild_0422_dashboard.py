#!/usr/bin/env python3
"""Rebuild the 26.04.22 reverse-engineered dashboard artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
DEFAULT_DATE = "2026-04-28"
DEFAULT_PAGE_DATE = "26.04.22"
DEFAULT_RECON = PROJECT_ROOT / "recon" / "26.04.22.md"
DEFAULT_OUTPUT = PROJECT_ROOT / "runtime" / "notion" / DEFAULT_DATE / "0421-format-v4" / "26.04.22.md"


def run(command: list[str], dry_run: bool) -> None:
    print("$ " + " ".join(command))
    if dry_run:
        return
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def existing_selection(date: str, preferred_version: str) -> Path:
    preferred = PROJECT_ROOT / "data" / "processed" / date / f"storyline-selection-{preferred_version}.json"
    fallback = PROJECT_ROOT / "data" / "processed" / date / "storyline-selection-v3.json"
    if preferred.exists():
        try:
            payload = json.loads(preferred.read_text(encoding="utf-8"))
            selection = payload.get("selection") or {}
            if selection.get("selected_items") and selection.get("storylines"):
                return preferred
        except json.JSONDecodeError:
            pass
    return fallback


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--page-date", default=DEFAULT_PAGE_DATE)
    parser.add_argument("--recon", type=Path, default=DEFAULT_RECON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--selection-version", default="v4")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    processed = PROJECT_ROOT / "data" / "processed" / args.date
    finviz = processed / "finviz-feature-stocks.json"
    x_enrichment = processed / "earnings-whispers-posts.json"
    selection = existing_selection(args.date, args.selection_version)
    feature_cards = PROJECT_ROOT / "runtime" / "notion" / args.date / "feature-stock-cards.md"

    missing = [path for path in [args.recon, finviz, selection] if not path.exists()]
    if missing:
        print(
            json.dumps(
                {"ok": False, "missing": [str(path.relative_to(REPO_ROOT)) for path in missing]},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    feature_command = [
            str(PYTHON),
            "projects/autopark/scripts/build_feature_stock_cards.py",
            "--page-date",
            args.page_date,
            "--date",
            args.date,
            "--finviz-enrichment",
            str(finviz.relative_to(REPO_ROOT)),
    ]
    if x_enrichment.exists():
        feature_command.extend(["--x-enrichment", str(x_enrichment.relative_to(REPO_ROOT))])
    run(feature_command, args.dry_run)
    run(
        [
            str(PYTHON),
            "projects/autopark/scripts/build_recon_0421_format.py",
            str(args.recon.relative_to(REPO_ROOT)),
            "--selection",
            str(selection.relative_to(REPO_ROOT)),
            "--finviz-enrichment",
            str(finviz.relative_to(REPO_ROOT)),
            "--feature-stocks",
            str(feature_cards.relative_to(REPO_ROOT)),
            "--output",
            str(args.output.relative_to(REPO_ROOT)),
        ],
        args.dry_run,
    )
    if args.publish:
        run(
            [
                str(PYTHON),
                "projects/autopark/scripts/publish_recon_to_notion.py",
                "--replace-existing",
                str(args.output.relative_to(REPO_ROOT)),
            ],
            args.dry_run,
        )

    print(
        json.dumps(
            {
                "ok": True,
                "date": args.date,
                "page_date": args.page_date,
                "selection": str(selection.relative_to(REPO_ROOT)),
                "output": str(args.output.relative_to(REPO_ROOT)),
                "publish": args.publish,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
