from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_market_focus_brief as focus_builder
import build_live_notion_dashboard as dashboard


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

    def test_alias_round_trip_maps_to_media_focus_asset_id(self) -> None:
        raw_candidate = {
            "id": "local-fed-1",
            "item_id": "local-fed-1",
            "source": "Reuters",
            "source_role": "fact_anchor",
            "evidence_role": "fact",
            "title": "Fed inflation warning keeps rates in focus",
            "summary": "Local fact anchor for the rates lead.",
        }
        payload = focus_builder.sanitize_local_packet(
            {
                "date": "2026-05-03",
                "policy": {},
                "market_radar": {"candidates": [raw_candidate], "storylines": []},
                "visual_cards": [],
                "raw_sources": [],
                "charts": [],
                "available_assets": [],
            }
        )
        alias = payload["market_radar"]["candidates"][0]["id"]
        self.assertTrue(alias.startswith("ev_"))

        model_output = {
            "market_focus_summary": "Rates frame the morning.",
            "what_market_is_watching": [
                {
                    "rank": 1,
                    "focus": "Rates pressure",
                    "market_question": "Are rates capping risk appetite?",
                    "why_it_matters": "The local Reuters item anchors the lead.",
                    "price_confirmation": "Check US10Y and DXY.",
                    "broadcast_use": "lead",
                    "confidence": 0.8,
                    "suggested_story_title": "Rates still frame the morning",
                    "one_sentence_for_host": "Start with rates before chasing headlines.",
                    "source_ids": [alias],
                    "evidence_ids": [alias],
                    "missing_assets": [],
                }
            ],
            "false_leads": [],
            "missing_assets": [],
            "source_gaps": [],
            "suggested_broadcast_order": [
                {
                    "rank": 1,
                    "focus_rank": 1,
                    "suggested_story_title": "Rates still frame the morning",
                    "broadcast_use": "lead",
                    "one_sentence_for_host": "Start with rates before chasing headlines.",
                    "evidence_ids": [alias],
                }
            ],
        }

        normalized = focus_builder.normalize_brief(model_output, payload)
        self.assertEqual(["local-fed-1"], normalized["what_market_is_watching"][0]["evidence_ids"])
        self.assertEqual(["local-fed-1"], normalized["suggested_broadcast_order"][0]["evidence_ids"])

        asset_id = dashboard.media_asset_id("local-fed-1")
        media_lines: list[str] = []
        rendered = dashboard.render_market_focus_media(
            media_lines,
            normalized,
            {"local-fed-1": raw_candidate},
            {"local-fed-1": raw_candidate},
            [],
        )
        media_markdown = "\n".join(media_lines)
        self.assertEqual(1, rendered)
        self.assertIn(f"asset_id: `{asset_id}`", media_markdown)

        story_lines: list[str] = []
        dashboard.render_host_storyline(
            story_lines,
            1,
            {
                "rank": 1,
                "title": "Rates still frame the morning",
                "recommendation_stars": 3,
                "evidence_to_use": [{"item_id": "local-fed-1", "evidence_id": "local-fed-1"}],
            },
            {"local-fed-1": raw_candidate},
        )
        self.assertIn(f"`{asset_id}`", "\n".join(story_lines))


if __name__ == "__main__":
    unittest.main()
