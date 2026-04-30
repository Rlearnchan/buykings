#!/usr/bin/env python3
"""Build clean reconstruction pages with a generated today-misc section."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def strip_storyline_wrapper(markdown: str) -> str:
    lines = markdown.splitlines()
    output = []
    skip_until_summary = True
    for line in lines:
        if skip_until_summary:
            if line.strip() == "## 주요 뉴스 요약":
                skip_until_summary = False
                output.append(line)
            continue
        output.append(line)
    return "\n".join(output).strip() + "\n"


def replace_today_misc(recon: str, replacement_body: str) -> str:
    pattern = re.compile(r"^## 2\. 오늘의 이모저모\n.*?(?=^## 3\. )", flags=re.MULTILINE | re.DOTALL)
    replacement = "## 2. 오늘의 이모저모\n\n" + replacement_body.strip() + "\n\n"
    replaced, count = pattern.subn(replacement, recon)
    if count != 1:
        raise SystemExit(f"Expected exactly one 오늘의 이모저모 section, replaced {count}")
    return replaced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recon", nargs="+", type=Path)
    parser.add_argument("--storyline", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "runtime" / "notion" / "clean")
    args = parser.parse_args()

    body = strip_storyline_wrapper(read(args.storyline.resolve()))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for recon_path in args.recon:
        resolved = recon_path.resolve()
        clean = replace_today_misc(read(resolved), body)
        output = args.output_dir / resolved.name
        output.write_text(clean, encoding="utf-8")
        outputs.append(str(output))
    print("\n".join(outputs))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
