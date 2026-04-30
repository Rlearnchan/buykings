#!/usr/bin/env python3
"""Append Markdown blocks to one or more existing Notion pages."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from publish_recon_to_notion import (
    DEFAULT_ENV,
    MAX_CHILDREN_PER_REQUEST,
    append_children,
    block,
    chunks,
    load_env,
    markdown_to_blocks,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Markdown file to append")
    parser.add_argument("--page-id", action="append", required=True, help="Target Notion page id; repeatable")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--prepend-heading", help="Optional heading_2 inserted before Markdown blocks")
    parser.add_argument("--upload-images", action="store_true", help="Upload local Markdown images to Notion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**os.environ, **load_env(args.env.resolve())}
    token = env.get("NOTION_API_KEY")
    if not token:
        raise SystemExit("Missing NOTION_API_KEY in environment or .env")

    markdown_path = args.markdown.resolve()
    if not markdown_path.exists():
        raise SystemExit(f"Missing markdown file: {markdown_path}")

    _, blocks = markdown_to_blocks(
        markdown_path.read_text(encoding="utf-8"),
        markdown_path=markdown_path,
        token=token,
        upload_images=args.upload_images and not args.dry_run,
    )
    if args.prepend_heading:
        blocks = [block("heading_2", args.prepend_heading), *blocks]

    block_chunks = chunks(blocks, MAX_CHILDREN_PER_REQUEST)
    results = []
    for page_id in args.page_id:
        if not args.dry_run:
            for chunk in block_chunks:
                append_children(page_id, chunk, token)
        results.append(
            {
                "page_id": page_id,
                "source": str(markdown_path),
                "block_count": len(blocks),
                "chunk_count": len(block_chunks),
                "status": "dry-run" if args.dry_run else "appended",
            }
        )

    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
