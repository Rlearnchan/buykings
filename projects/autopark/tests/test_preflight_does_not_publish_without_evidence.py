from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_market_focus_brief as focus_builder


class PreflightPromotionGuardTest(unittest.TestCase):
    def test_preflight_only_story_is_demoted_to_source_gap(self) -> None:
        input_payload = focus_builder.sanitize_local_packet(
            {
                "date": "2026-05-03",
                "policy": {},
                "market_preflight_agenda": {
                    "date": "2026-05-03",
                    "preflight_summary": "Rates first.",
                    "agenda_items": [
                        {
                            "rank": 1,
                            "agenda_id": "agenda_rates_dollar",
                            "market_question": "Can earnings beat rates and dollar pressure?",
                            "why_to_check": "It may frame the morning.",
                            "expected_broadcast_use": "lead_candidate",
                            "collection_targets": [
                                {
                                    "target_type": "news_search",
                                    "query_or_asset": "Fed inflation Reuters market reaction",
                                    "preferred_sources": ["Reuters"],
                                    "reason": "fact anchor",
                                }
                            ],
                            "must_verify_with_local_evidence": True,
                            "public_safe": False,
                        }
                    ],
                    "collection_priorities": {},
                    "source_gaps_to_watch": [],
                },
                "market_radar": {
                    "candidates": [{"id": "known-local-1", "item_id": "known-local-1", "title": "Known local fact"}],
                    "storylines": [],
                },
                "visual_cards": [],
                "raw_sources": [],
                "charts": [],
                "available_assets": [],
            }
        )
        model_output = {
            "market_focus_summary": "Rates may be the agenda.",
            "what_market_is_watching": [
                {
                    "rank": 1,
                    "focus": "Rates and dollar pressure",
                    "market_question": "Can earnings beat rates and dollar pressure?",
                    "why_it_matters": "Pre-flight flagged it, but local evidence is missing.",
                    "price_confirmation": "No local confirmation.",
                    "broadcast_use": "lead",
                    "confidence": 0.8,
                    "suggested_story_title": "Rates and dollar lead",
                    "one_sentence_for_host": "Hold this until local evidence exists.",
                    "source_ids": ["agenda_rates_dollar"],
                    "evidence_ids": [],
                    "missing_assets": [],
                }
            ],
            "false_leads": [],
            "missing_assets": [],
            "source_gaps": [],
            "suggested_broadcast_order": [],
        }

        normalized = focus_builder.normalize_brief(model_output, input_payload)

        self.assertEqual("drop", normalized["what_market_is_watching"][0]["broadcast_use"])
        self.assertEqual([], normalized["suggested_broadcast_order"])
        self.assertFalse(normalized["source_gaps"][0]["safe_for_public"])
        self.assertIn("agenda_rates_dollar", normalized["source_gaps"][0]["search_hint"])


if __name__ == "__main__":
    unittest.main()
