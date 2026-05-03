#!/usr/bin/env python3
"""Publish Autopark reconstruction Markdown pages to Notion."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "autopark.json"
DEFAULT_ENV = REPO_ROOT / ".env"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
MAX_CHILDREN_PER_REQUEST = 100
MAX_RICH_TEXT = 1900


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def notion_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{NOTION_API}{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Notion API error {exc.code} on {method} {path}: {details}") from exc


def notion_multipart_upload(upload_url: str, token: str, path: Path, content_type: str) -> dict:
    boundary = "autopark-notion-boundary"
    file_bytes = path.read_bytes()
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    request = Request(
        upload_url,
        data=header + file_bytes + footer,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Notion upload error {exc.code} for {path}: {details}") from exc


def upload_file(path: Path, token: str) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    created = notion_request(
        "POST",
        "/file_uploads",
        token,
        {
            "mode": "single_part",
            "filename": path.name,
            "content_type": content_type,
        },
    )
    uploaded = notion_multipart_upload(created["upload_url"], token, path, content_type)
    return uploaded["id"]


def resolve_markdown_asset(markdown_path: Path, asset: str) -> Path:
    raw = Path(asset)
    if raw.is_absolute():
        return raw
    for base in (markdown_path.parent, REPO_ROOT, PROJECT_ROOT):
        candidate = (base / raw).resolve()
        if candidate.exists():
            return candidate
    return (markdown_path.parent / raw).resolve()


def get_block_children(block_id: str, token: str) -> list[dict]:
    children: list[dict] = []
    cursor = None
    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        payload = notion_request("GET", path, token)
        children.extend(payload.get("results", []))
        if not payload.get("has_more"):
            return children
        cursor = payload.get("next_cursor")


def archive_page(page_id: str, token: str) -> dict:
    return notion_request("PATCH", f"/pages/{page_id}", token, {"in_trash": True})


def archive_existing_child_pages(parent_page_id: str, title: str, token: str, dry_run: bool) -> list[dict]:
    matches = []
    for child in get_block_children(parent_page_id, token):
        if child.get("type") != "child_page":
            continue
        child_title = child.get("child_page", {}).get("title")
        if child_title == title:
            matches.append({"page_id": child["id"], "title": child_title})

    if dry_run:
        return [{"status": "would-archive", **match} for match in matches]

    archived = []
    for match in matches:
        archive_page(match["page_id"], token)
        archived.append({"status": "archived", **match})
    return archived


def text_fragments(text: str, *, link: str | None = None, code: bool = False, bold: bool = False) -> list[dict]:
    annotations = {}
    if code:
        annotations["code"] = True
    if bold:
        annotations["bold"] = True
    fragments = []
    for chunk in [text[i : i + MAX_RICH_TEXT] for i in range(0, len(text), MAX_RICH_TEXT)] or [""]:
        fragment = {"type": "text", "text": {"content": chunk}}
        if link:
            fragment["text"]["link"] = {"url": link}
        if annotations:
            fragment["annotations"] = annotations
        fragments.append(fragment)
    return fragments


def rich_text(text: str) -> list[dict]:
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    fragments: list[dict] = []
    cursor = 0
    inline = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)")
    for match in inline.finditer(text):
        if match.start() > cursor:
            fragments.extend(text_fragments(text[cursor : match.start()]))
        if match.group(1) is not None:
            fragments.extend(text_fragments(match.group(1), code=True))
        elif match.group(2) is not None:
            fragments.extend(text_fragments(match.group(2), bold=True))
        else:
            fragments.extend(text_fragments(match.group(3), link=match.group(4)))
        cursor = match.end()
    if cursor < len(text):
        fragments.extend(text_fragments(text[cursor:]))
    return fragments


def block(block_type: str, text: str) -> dict:
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": rich_text(text)},
    }


def paragraph_blocks(text: str) -> list[dict]:
    if len(text) <= MAX_RICH_TEXT:
        return [block("paragraph", text)]
    return [block("paragraph", text[i : i + MAX_RICH_TEXT]) for i in range(0, len(text), MAX_RICH_TEXT)]


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def table_block(header: list[str], rows: list[list[str]]) -> dict:
    width = len(header)

    def normalize(row: list[str]) -> list[str]:
        padded = [*row[:width], *([""] * max(0, width - len(row)))]
        return padded[:width]

    children = []
    for row in [header, *rows]:
        children.append(
            {
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": [rich_text(cell) for cell in normalize(row)],
                },
            }
        )
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def compact_publish_title(markdown_path: Path | None) -> str:
    if markdown_path is None:
        return ""
    if re.match(r"^\d{2}\.\d{2}\.\d{2}\.md$", markdown_path.name):
        return markdown_path.stem
    return ""


def markdown_to_blocks(markdown: str, markdown_path: Path | None = None, token: str | None = None, upload_images: bool = False) -> tuple[str, list[dict]]:
    title = compact_publish_title(markdown_path) or "Untitled"
    consume_first_h1_as_title = title == "Untitled"
    blocks: list[dict] = []
    list_stack: list[tuple[int, dict]] = []
    in_code = False
    code_lines: list[str] = []
    lines = markdown.splitlines()
    index = 0

    def reset_list_stack() -> None:
        list_stack.clear()

    def append_list_item(indent: int, item: dict) -> None:
        while list_stack and list_stack[-1][0] >= indent:
            list_stack.pop()
        if list_stack:
            parent = list_stack[-1][1]
            parent_type = parent["type"]
            parent[parent_type].setdefault("children", []).append(item)
        else:
            blocks.append(item)
        list_stack.append((indent, item))

    while index < len(lines):
        raw_line = lines[index]
        index += 1
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            reset_list_stack()
            if in_code:
                code_text = "\n".join(code_lines)
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": rich_text(code_text),
                            "language": "plain text",
                        },
                    }
                )
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            reset_list_stack()
            continue

        if (
            "|" in stripped
            and stripped.startswith("|")
            and index < len(lines)
            and is_table_separator(lines[index].strip())
        ):
            reset_list_stack()
            header = split_table_row(stripped)
            index += 1
            rows = []
            while index < len(lines):
                row_line = lines[index].strip()
                if not row_line or not row_line.startswith("|") or "|" not in row_line:
                    break
                rows.append(split_table_row(row_line))
                index += 1
            if header and rows:
                blocks.append(table_block(header, rows))
                continue
            blocks.extend(paragraph_blocks(stripped))
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            reset_list_stack()
            caption = image.group(1).strip()
            target = image.group(2).strip()
            if upload_images:
                if markdown_path is None or token is None:
                    raise SystemExit("Internal error: image upload requires markdown_path and token")
                image_path = resolve_markdown_asset(markdown_path, target)
                if not image_path.exists():
                    raise SystemExit(f"Missing image for Notion upload: {image_path}")
                file_upload_id = upload_file(image_path, token)
                blocks.append(
                    {
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "file_upload",
                            "file_upload": {"id": file_upload_id},
                            "caption": rich_text(caption) if caption else [],
                        },
                    }
                )
            else:
                blocks.append(block("paragraph", f"[image: {caption or target}] {target}"))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            reset_list_stack()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1 and consume_first_h1_as_title:
                title = text
                consume_first_h1_as_title = False
                continue
            if level >= 4:
                blocks.append(block("paragraph", f"**{text}**"))
                continue
            block_type = "heading_1" if level == 1 else "heading_2" if level == 2 else "heading_3"
            blocks.append(block(block_type, text))
            continue

        if stripped.startswith("> "):
            reset_list_stack()
            blocks.append(block("quote", stripped[2:].strip()))
            continue

        bullet = re.match(r"^([ \t]*)-\s+(.+)$", line)
        if bullet:
            indent = len(bullet.group(1).expandtabs(4))
            append_list_item(indent, block("bulleted_list_item", bullet.group(2).strip()))
            continue

        numbered = re.match(r"^([ \t]*)\d+\.\s+(.+)$", line)
        if numbered:
            indent = len(numbered.group(1).expandtabs(4))
            append_list_item(indent, block("numbered_list_item", numbered.group(2).strip()))
            continue

        reset_list_stack()
        blocks.extend(paragraph_blocks(stripped))

    if in_code and code_lines:
        blocks.append(
            {
                "object": "block",
                "type": "code",
                "code": {"rich_text": rich_text("\n".join(code_lines)), "language": "plain text"},
            }
        )
    return title, blocks


def create_page(parent_page_id: str, title: str, initial_children: list[dict], token: str) -> dict:
    return notion_request(
        "POST",
        "/pages",
        token,
        {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "properties": {"title": {"title": rich_text(title)}},
            "children": initial_children,
        },
    )


def append_children(block_id: str, children: list[dict], token: str) -> None:
    notion_request("PATCH", f"/blocks/{block_id}/children", token, {"children": children})


def chunks(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def publish_file(
    path: Path,
    parent_page_id: str,
    token: str,
    dry_run: bool,
    replace_existing: bool,
) -> dict:
    title, blocks = markdown_to_blocks(
        path.read_text(encoding="utf-8"),
        markdown_path=path,
        token=token,
        upload_images=not dry_run,
    )
    block_chunks = chunks(blocks, MAX_CHILDREN_PER_REQUEST)
    result = {
        "source": str(path),
        "title": title,
        "block_count": len(blocks),
        "chunk_count": len(block_chunks),
    }

    if replace_existing:
        result["replace_existing"] = archive_existing_child_pages(
            parent_page_id=parent_page_id,
            title=title,
            token=token,
            dry_run=dry_run,
        )

    if dry_run:
        result["status"] = "dry-run"
        return result

    initial = block_chunks[0] if block_chunks else []
    page = create_page(parent_page_id, title, initial, token)
    for extra in block_chunks[1:]:
        append_children(page["id"], extra, token)
    result.update({"status": "published", "page_id": page["id"], "url": page.get("url")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", nargs="+", type=Path, help="Markdown files to publish")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--parent-page-id", help="Override the Notion parent page id")
    parser.add_argument("--replace-existing", action="store_true", help="Archive child pages with the same title before publishing")
    parser.add_argument("--archive-existing-only", action="store_true", help="Archive matching child pages and do not create a new page")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**os.environ, **load_env(args.env.resolve())}
    token = env.get("NOTION_API_KEY")
    if not token:
        raise SystemExit("Missing NOTION_API_KEY in environment or .env")

    config = load_config(args.config.resolve())
    notion_config = config.get("integrations", {}).get("notion", {})
    parent_page_id = args.parent_page_id or notion_config.get("dashboard_parent_page_id")
    if not parent_page_id:
        raise SystemExit("Missing dashboard_parent_page_id in config or --parent-page-id")

    results = []
    for path in args.markdown:
        resolved = path.resolve()
        title, blocks = markdown_to_blocks(
            resolved.read_text(encoding="utf-8"),
            markdown_path=resolved,
            token=token,
            upload_images=False,
        )
        if args.archive_existing_only:
            results.append(
                {
                    "source": str(resolved),
                    "title": title,
                    "block_count": len(blocks),
                    "replace_existing": archive_existing_child_pages(
                        parent_page_id=parent_page_id,
                        title=title,
                        token=token,
                        dry_run=args.dry_run,
                    ),
                    "status": "dry-run" if args.dry_run else "archived-existing-only",
                }
            )
            continue

        results.append(
            publish_file(
                resolved,
                parent_page_id=parent_page_id,
                token=token,
                dry_run=args.dry_run,
                replace_existing=args.replace_existing,
            )
        )
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
