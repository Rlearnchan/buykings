from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_editorial_brief as brief_builder


class RetrospectiveLearningTest(unittest.TestCase):
    def test_summarize_retrospective_payload_scores_labels(self) -> None:
        config = brief_builder.load_retrospective_learning_config(Path("__missing__.json"))
        comparison = {
            "storyline_results": [
                {
                    "storyline_id": "story-1",
                    "title": "Rates lead",
                    "labels": ["used_as_lead", "used_as_slide", "strong_broadcast_fit"],
                    "slide_matches": [{"title": "10Y Treasury yield"}],
                }
            ],
            "asset_results": [
                {
                    "item_id": "x-1",
                    "storyline_id": "story-2",
                    "title": "X-only reaction",
                    "label": "false_positive_sentiment_only",
                }
            ],
        }
        review = {
            "review": {
                "summary_for_next_brief": "Prefer fact/data plus a clear visual.",
                "missed_broadcast_topics": [
                    {"topic": "oil", "suggested_source_or_query": "WTI and OPEC morning scan"}
                ],
            }
        }

        summary = brief_builder.summarize_retrospective_payload("2026-04-29", review, comparison, "", config)

        self.assertGreater(summary["positive_score"], 0)
        self.assertGreater(summary["caution_score"], 0)
        self.assertEqual(1, summary["label_counts"]["used_as_lead"])
        self.assertEqual(1, summary["label_counts"]["false_positive_sentiment_only"])
        self.assertTrue(any("social-only" in action or "Never promote" in action for action in summary["actions"]))
        self.assertEqual("oil", summary["missed_topics"][0]["topic"])

    def test_normalize_brief_appends_learning_watchpoints(self) -> None:
        brief = {
            "broadcast_mode": "normal",
            "daily_thesis": "Rates lead the open.",
            "editorial_summary": "Use rates as the lead.",
            "storylines": [
                {
                    "storyline_id": "story-1",
                    "rank": 1,
                    "title": "Rates lead",
                    "recommendation_stars": 3,
                    "rating_reason": "Best lead",
                    "lead_candidate_reason": "Market explanation and visual fit.",
                    "hook": "Rates explain the open.",
                    "why_now": "The move is visible before Korea open.",
                    "core_argument": "Rates changed the risk frame.",
                    "signal_or_noise": "signal",
                    "market_causality": "fact/data supported",
                    "expectation_gap": "check_if_relevant",
                    "prepricing_risk": "low",
                    "first_5min_fit": "high",
                    "korea_open_relevance": "medium",
                    "talk_track": "Explain rates first.",
                    "slide_order": ["10Y chart"],
                    "slide_plan": ["10Y chart"],
                    "ppt_asset_queue": [],
                    "evidence_to_use": [
                        {
                            "item_id": "rate-1",
                            "evidence_id": "rate-1",
                            "title": "10Y chart",
                            "source_role": "data_anchor",
                            "evidence_role": "data",
                            "reason": "Rates moved.",
                        }
                    ],
                    "evidence_to_drop": [],
                    "drop_code": "",
                    "counterpoint": "Could be temporary.",
                    "what_would_change_my_mind": "No follow-through.",
                    "closing_line": "Watch rates first.",
                },
                {
                    "storyline_id": "story-2",
                    "rank": 2,
                    "title": "Earnings backup",
                    "recommendation_stars": 2,
                    "rating_reason": "Backup",
                    "lead_candidate_reason": "Useful later.",
                    "hook": "Earnings matter.",
                    "why_now": "Earnings are due.",
                    "core_argument": "Expectations matter.",
                    "signal_or_noise": "watch",
                    "market_causality": "needs check",
                    "expectation_gap": "required",
                    "prepricing_risk": "possible",
                    "first_5min_fit": "medium",
                    "korea_open_relevance": "medium",
                    "talk_track": "Mention briefly.",
                    "slide_order": [],
                    "slide_plan": [],
                    "ppt_asset_queue": [],
                    "evidence_to_use": [
                        {
                            "item_id": "earn-1",
                            "evidence_id": "earn-1",
                            "title": "Earnings calendar",
                            "source_role": "data_anchor",
                            "evidence_role": "data",
                            "reason": "Upcoming earnings.",
                        }
                    ],
                    "evidence_to_drop": [],
                    "drop_code": "",
                    "counterpoint": "",
                    "what_would_change_my_mind": "",
                    "closing_line": "",
                },
                {
                    "storyline_id": "story-3",
                    "rank": 3,
                    "title": "Sentiment backup",
                    "recommendation_stars": 1,
                    "rating_reason": "Backup",
                    "lead_candidate_reason": "Color only.",
                    "hook": "Sentiment is noisy.",
                    "why_now": "People are discussing it.",
                    "core_argument": "Color only.",
                    "signal_or_noise": "noise",
                    "market_causality": "not causal",
                    "expectation_gap": "not_primary",
                    "prepricing_risk": "low",
                    "first_5min_fit": "low",
                    "korea_open_relevance": "low",
                    "talk_track": "Skip if time is short.",
                    "slide_order": [],
                    "slide_plan": [],
                    "ppt_asset_queue": [],
                    "evidence_to_use": [
                        {
                            "item_id": "x-1",
                            "evidence_id": "x-1",
                            "title": "X reaction",
                            "source_role": "sentiment_probe",
                            "evidence_role": "sentiment",
                            "reason": "Color.",
                        }
                    ],
                    "evidence_to_drop": [],
                    "drop_code": "",
                    "counterpoint": "",
                    "what_would_change_my_mind": "",
                    "closing_line": "",
                },
            ],
        }
        payload = {
            "candidates": [
                {"id": "rate-1", "item_id": "rate-1", "title": "10Y chart", "talk_vs_slide": "slide", "ppt_asset_candidate": True},
                {"id": "earn-1", "item_id": "earn-1", "title": "Earnings calendar"},
                {"id": "x-1", "item_id": "x-1", "title": "X reaction", "talk_vs_slide": "talk_only"},
            ],
            "retrospective_learning": {
                "aggregate_actions": ["Never promote social-only material as fact."]
            },
        }

        normalized = brief_builder.normalize_brief(brief, payload)

        self.assertTrue(any("retrospective_learning" in item for item in normalized["retrospective_watchpoints"]))


if __name__ == "__main__":
    unittest.main()
