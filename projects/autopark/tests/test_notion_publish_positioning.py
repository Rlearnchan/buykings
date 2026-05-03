from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import publish_recon_to_notion as publish


class NotionPublishPositioningTest(unittest.TestCase):
    def test_resolve_insert_position_finds_heading(self) -> None:
        original = publish.get_block_children
        try:
            publish.get_block_children = lambda _page, _token: [
                {
                    "id": "quote-1",
                    "type": "quote",
                    "quote": {"rich_text": [{"plain_text": "intro"}]},
                },
                {
                    "id": "heading-today",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"plain_text": "오늘의 자료"}]},
                },
            ]

            position = publish.resolve_insert_position("parent", "token", "오늘의 자료")
        finally:
            publish.get_block_children = original

        self.assertEqual(
            {"type": "after_block", "after_block": {"id": "heading-today"}},
            position,
        )

    def test_resolve_insert_position_fails_when_heading_missing(self) -> None:
        original = publish.get_block_children
        try:
            publish.get_block_children = lambda _page, _token: []
            with self.assertRaises(SystemExit):
                publish.resolve_insert_position("parent", "token", "오늘의 자료")
        finally:
            publish.get_block_children = original

    def test_append_page_link_uses_position_payload(self) -> None:
        calls: list[tuple[str, str, dict | None]] = []
        original = publish.notion_request
        try:
            def fake_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
                calls.append((method, path, payload))
                return {"results": [{"id": "new-link", "type": "link_to_page", "link_to_page": {"page_id": "page-1"}}]}

            publish.notion_request = fake_request
            link = publish.append_page_link_at_position(
                "parent",
                "page-1",
                "token",
                {"type": "after_block", "after_block": {"id": "heading-today"}},
            )
        finally:
            publish.notion_request = original

        self.assertEqual("new-link", link["id"])
        self.assertEqual("PATCH", calls[0][0])
        self.assertEqual("/blocks/parent/children", calls[0][1])
        self.assertEqual({"type": "after_block", "after_block": {"id": "heading-today"}}, calls[0][2]["position"])
        self.assertEqual("link_to_page", calls[0][2]["children"][0]["type"])
        self.assertEqual("page-1", calls[0][2]["children"][0]["link_to_page"]["page_id"])


if __name__ == "__main__":
    unittest.main()
