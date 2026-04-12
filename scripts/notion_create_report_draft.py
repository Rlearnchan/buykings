#!/usr/bin/env python3
"""Create a Notion report draft page from a JSON spec."""

from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
import pathlib
import uuid
import urllib.error
import urllib.request


API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"


def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


class NotionClient:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(self, method: str, path: str, payload: dict) -> dict:
        url = f"{API_BASE}{path}"
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Notion API error ({exc.code}) on {method} {path}:\n{details}") from exc

    def request_no_body(self, method: str, path: str) -> dict:
        url = f"{API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Notion API error ({exc.code}) on {method} {path}:\n{details}") from exc

    def request_bytes(
        self,
        method: str,
        url: str,
        *,
        data: bytes,
        content_type: str,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Notion API error ({exc.code}) on {method} {url}:\n{details}") from exc

    def create_page(self, parent_page_id: str, title: str, children: list[dict]) -> dict:
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            },
            "children": children,
        }
        return self.request("POST", "/pages", payload)

    def list_block_children(self, block_id: str) -> list[dict]:
        results: list[dict] = []
        cursor = None
        while True:
            path = f"/blocks/{block_id}/children"
            if cursor:
                path = f"{path}?start_cursor={cursor}"
            response = self.request_no_body("GET", path)
            results.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        return results

    def trash_page(self, page_id: str) -> dict:
        return self.request("PATCH", f"/pages/{page_id}", {"in_trash": True})

    def create_file_upload(self, filename: str, content_type: str) -> dict:
        payload = {
            "mode": "single_part",
            "filename": filename,
            "content_type": content_type,
        }
        return self.request("POST", "/file_uploads", payload)

    def send_file_upload(self, upload_url: str, path: pathlib.Path, content_type: str) -> dict:
        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        body = build_multipart_body(boundary, path, content_type)
        return self.request_bytes(
            "POST",
            upload_url,
            data=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )


def rich_text(text: str, *, link: str | None = None) -> list[dict]:
    node = {"type": "text", "text": {"content": text}}
    if link:
        node["text"]["link"] = {"url": link}
    return [node]


def paragraph(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(text)}}


def heading(level: int, text: str) -> dict:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": rich_text(text)}}


def bulleted_list_item(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text(text)},
    }


def quote(text: str) -> dict:
    return {"object": "block", "type": "quote", "quote": {"rich_text": rich_text(text)}}


def divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def bookmark(url: str, caption: str | None = None) -> dict:
    block = {"object": "block", "type": "bookmark", "bookmark": {"url": url}}
    if caption:
        block["bookmark"]["caption"] = rich_text(caption)
    return block


def image(url: str, caption: str | None = None) -> dict:
    block = {"object": "block", "type": "image", "image": {"type": "external", "external": {"url": url}}}
    if caption:
        block["image"]["caption"] = rich_text(caption)
    return block


def uploaded_image(file_upload_id: str, caption: str | None = None) -> dict:
    block = {
        "object": "block",
        "type": "image",
        "image": {"type": "file_upload", "file_upload": {"id": file_upload_id}},
    }
    if caption:
        block["image"]["caption"] = rich_text(caption)
    return block


def build_multipart_body(boundary: str, path: pathlib.Path, content_type: str) -> bytes:
    buffer = io.BytesIO()
    boundary_line = f"--{boundary}\r\n".encode("utf-8")
    disposition = (
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode("utf-8")
    )
    content_type_line = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
    buffer.write(boundary_line)
    buffer.write(disposition)
    buffer.write(content_type_line)
    buffer.write(path.read_bytes())
    buffer.write(b"\r\n")
    buffer.write(f"--{boundary}--\r\n".encode("utf-8"))
    return buffer.getvalue()


def upload_section_images(client: NotionClient, spec: dict) -> dict[str, str]:
    uploaded: dict[str, str] = {}
    for section in spec["sections"]:
        image_path = section.get("image_path")
        if not image_path:
            continue
        path = pathlib.Path(image_path).resolve()
        if not path.exists():
            raise SystemExit(f"Section image not found: {path}")
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        upload = client.create_file_upload(path.name, content_type)
        client.send_file_upload(upload["upload_url"], path, content_type)
        uploaded[section["title"]] = upload["id"]
    return uploaded


def trash_previous_drafts(client: NotionClient, parent_page_id: str, title: str) -> list[str]:
    trashed: list[str] = []
    for block in client.list_block_children(parent_page_id):
        if block.get("type") != "child_page":
            continue
        if block.get("child_page", {}).get("title") != title:
            continue
        page_id = block["id"]
        client.trash_page(page_id)
        trashed.append(page_id)
    return trashed


def build_children(spec: dict, uploaded_images: dict[str, str]) -> list[dict]:
    blocks: list[dict] = []

    blocks.append(paragraph(spec["summary"]))
    if spec.get("topline_bullets"):
        for item in spec["topline_bullets"]:
            blocks.append(bulleted_list_item(item))

    for section in spec["sections"]:
        blocks.append(divider())
        blocks.append(heading(2, section["title"]))
        if section.get("subtitle"):
            blocks.append(quote(section["subtitle"]))
        if uploaded_images.get(section["title"]):
            blocks.append(uploaded_image(uploaded_images[section["title"]], section.get("image_caption")))
        elif section.get("image_url"):
            blocks.append(image(section["image_url"], section.get("image_caption")))
        elif section.get("publish_url"):
            blocks.append(bookmark(section["publish_url"], "Published chart"))
        blocks.append(paragraph(section["takeaway"]))
        if section.get("source"):
            blocks.append(paragraph(f"Source: {section['source']}"))
        if section.get("note"):
            blocks.append(paragraph(f"Note: {section['note']}"))

    if spec.get("footer_note"):
        blocks.append(divider())
        blocks.append(paragraph(spec["footer_note"]))

    return blocks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Path to report draft JSON spec")
    parser.add_argument(
        "--parent-page-id",
        help="Override NOTION_PARENT_PAGE_ID for this run",
    )
    args = parser.parse_args()

    spec_path = pathlib.Path(args.spec).resolve()
    spec = load_json(spec_path)
    parent_page_id = args.parent_page_id or read_env("NOTION_PARENT_PAGE_ID")
    token = read_env("NOTION_API_KEY")

    client = NotionClient(token)
    trashed_pages = trash_previous_drafts(client, parent_page_id, spec["title"])
    uploaded_images = upload_section_images(client, spec)
    page = client.create_page(parent_page_id, spec["title"], build_children(spec, uploaded_images))
    result = {
        "ok": True,
        "title": spec["title"],
        "page_id": page["id"],
        "url": page["url"],
        "parent_page_id": parent_page_id,
        "trashed_pages": trashed_pages,
        "uploaded_images": uploaded_images,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
