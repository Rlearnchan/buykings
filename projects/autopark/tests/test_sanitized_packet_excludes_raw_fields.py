from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_market_focus_brief as focus_builder


class SanitizedPacketTest(unittest.TestCase):
    def test_sanitized_packet_excludes_urls_paths_and_full_bodies(self) -> None:
        raw = {
            "date": "2026-05-03",
            "policy": {},
            "market_radar": {
                "candidates": [
                    {
                        "id": "https://example.com/full/article?token=secret",
                        "item_id": "raw-1",
                        "url": "https://example.com/full/article?token=secret",
                        "source": "Reuters",
                        "source_role": "fact_anchor",
                        "evidence_role": "fact",
                        "title": "Fed official says inflation data was bad news for cuts",
                        "summary": "Compact local summary only.",
                        "body": "FULL ARTICLE BODY " * 100,
                        "visual_local_path": r"C:\\Users\\User1\\screenshots\\fed.png",
                    }
                ],
                "storylines": [{"selected_item_ids": ["raw-1"], "title": "Rates"}],
            },
            "visual_cards": [{"id": "card-1", "title": "Card", "summary": "Summary", "path": r"C:\\tmp\\card.png"}],
            "raw_sources": [
                {
                    "source_id": "news",
                    "source_name": "News",
                    "kind": "json",
                    "sample_items": [
                        {
                            "id": "https://example.com/source",
                            "title": "Source item",
                            "url": "https://example.com/source",
                            "html": "<html>secret</html>",
                            "summary": "Compact sample summary.",
                        }
                    ],
                }
            ],
            "charts": [{"chart_id": "us10y", "title": "US10Y", "takeaway": "Higher"}],
            "available_assets": [{"asset_id": "fed.png", "path": r"C:\\tmp\\fed.png", "kind": "screenshot"}],
        }

        sanitized = focus_builder.prompt_payload(focus_builder.sanitize_local_packet(raw))
        blob = json.dumps(sanitized, ensure_ascii=False)

        self.assertIn("packet_mode", sanitized)
        self.assertNotIn("https://example.com", blob)
        self.assertNotIn("C:\\", blob)
        self.assertNotIn("FULL ARTICLE BODY", blob)
        self.assertNotIn("<html>", blob)
        self.assertNotIn(focus_builder.LOCAL_ALIAS_KEY, sanitized)
        self.assertTrue(any(row["id"].startswith("ev_") for row in sanitized["market_radar"]["candidates"]))


if __name__ == "__main__":
    unittest.main()
