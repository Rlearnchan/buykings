#!/usr/bin/env python3
"""Inspect a Notion page's block outline for Autopark format comparison."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from publish_recon_to_notion import DEFAULT_CONFIG, DEFAULT_ENV, get_block_children, load_config, load_env


def plain_text(block: dict) -> str:
    block_type = block.get("type")
    if not block_type:
        return ""
    payload = block.get(block_type, {})
    if block_type == "child_page":
        return payload.get("title", "")
    if block_type == "image":
        return " ".join(part.get("plain_text", "") for part in payload.get("caption", []))
    return " ".join(part.get("plain_text", "") for part in payload.get("rich_text", []))


def walk(block_id: str, token: str, depth: int = 0, max_depth: int = 2) -> list[dict]:
    rows: list[dict] = []
    for child in get_block_children(block_id, token):
        text = plain_text(child)
        rows.append(
            {
                "id": child.get("id"),
                "type": child.get("type"),
                "depth": depth,
                "text": text[:240],
                "has_children": child.get("has_children", False),
            }
        )
        if child.get("has_children") and depth < max_depth:
            rows.extend(walk(child["id"], token, depth + 1, max_depth))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-id", help="Notion page id. Defaults to config integrations.notion.example_page_id")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    env = {**os.environ, **load_env(args.env.resolve())}
    token = env.get("NOTION_API_KEY")
    if not token:
        raise SystemExit("Missing NOTION_API_KEY in environment or .env")

    config = load_config(args.config.resolve())
    notion_config = config.get("integrations", {}).get("notion", {})
    page_id = args.page_id or notion_config.get("example_page_id")
    if not page_id:
        raise SystemExit("Missing --page-id and integrations.notion.example_page_id")

    rows = walk(page_id, token, max_depth=args.max_depth)
    payload = {"ok": True, "page_id": page_id, "block_count": len(rows), "blocks": rows}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
