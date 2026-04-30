#!/usr/bin/env python3
"""Append a Datawrapper chart trial block to an existing Notion page."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from publish_recon_to_notion import (
    DEFAULT_CONFIG,
    DEFAULT_ENV,
    append_children,
    block,
    get_block_children,
    load_config,
    load_env,
    notion_request,
    rich_text,
    upload_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = PROJECT_ROOT / "exports" / "current" / "us10y.png"


def image_block(image_path: Path, token: str, caption: str, dry_run: bool) -> dict:
    if dry_run:
        return block("paragraph", f"[image: {caption}] {image_path}")
    file_upload_id = upload_file(image_path, token)
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
            "caption": rich_text(caption),
        },
    }


def iter_blocks(root_id: str, token: str) -> list[dict]:
    found = []
    pending = [root_id]
    while pending:
        block_id = pending.pop(0)
        for child in get_block_children(block_id, token):
            found.append(child)
            if child.get("has_children"):
                pending.append(child["id"])
    return found


def replace_matching_image(page_id: str, image_path: Path, token: str, caption: str, match_text: str, dry_run: bool) -> dict:
    matches = []
    for child in iter_blocks(page_id, token):
        if child.get("type") != "image":
            continue
        caption_text = "".join(
            part.get("plain_text", "")
            for part in child.get("image", {}).get("caption", [])
        )
        if match_text in caption_text:
            matches.append({"block_id": child["id"], "caption": caption_text})

    result = {"matched": matches, "updated": []}
    if dry_run:
        return result

    for match in matches:
        file_upload_id = upload_file(image_path, token)
        notion_request(
            "PATCH",
            f"/blocks/{match['block_id']}",
            token,
            {
                "image": {
                    "file_upload": {"id": file_upload_id},
                    "caption": rich_text(caption),
                }
            },
        )
        result["updated"].append(match["block_id"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-id", required=True, help="Existing Notion page id")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--replace-caption-contains", help="Replace existing image blocks whose caption contains this text")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**os.environ, **load_env(args.env.resolve())}
    token = env.get("NOTION_API_KEY")
    if not token:
        raise SystemExit("Missing NOTION_API_KEY in environment or .env")

    config = load_config(args.config.resolve())
    image_path = args.image.resolve()
    if not image_path.exists():
        raise SystemExit(f"Missing image: {image_path}")

    notion_config = config.get("integrations", {}).get("notion", {})
    page_id = args.page_id
    caption = "미국 10년물 국채금리 Datawrapper PoC. Source: FRED, Federal Reserve Bank of St. Louis."
    if args.replace_caption_contains:
        replace_result = replace_matching_image(
            page_id,
            image_path,
            token,
            caption,
            args.replace_caption_contains,
            args.dry_run,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "page_id": page_id,
                    "image": str(image_path),
                    "status": "dry-run" if args.dry_run else "replaced",
                    "replace": replace_result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    children = [
        block("heading_2", "Datawrapper 전환 테스트"),
        block(
            "paragraph",
            "고정 차트는 사이트 캡처 대신 API/구조화 데이터로 수집해 Datawrapper에서 제작하는 방향으로 전환한다. "
            "아래 이미지는 Notion 업로드 및 렌더링 확인용 PoC이며, 날짜별 본문 차트로 확정된 산출물은 아니다.",
        ),
        image_block(
            image_path,
            token,
            caption,
            args.dry_run,
        ),
        block(
            "paragraph",
            "운영 방침: Datawrapper PNG는 Notion/방송 준비용, 원본 사이트 스크린샷은 내부 증빙용으로 분리한다.",
        ),
    ]

    result = {
        "ok": True,
        "page_id": page_id,
        "image": str(image_path),
        "dashboard_parent_page_id": notion_config.get("dashboard_parent_page_id"),
        "block_count": len(children),
        "status": "dry-run" if args.dry_run else "appended",
    }
    if not args.dry_run:
        append_children(page_id, children, token)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
