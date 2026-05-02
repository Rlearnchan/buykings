from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_editorial_brief as brief_builder


class EditorialBriefContractTest(unittest.TestCase):
    def test_normalize_brief_adds_broadcast_editor_fields(self) -> None:
        fixture = PROJECT / "tests" / "fixtures" / "editorial-brief-broadcast.json"
        brief = json.loads(fixture.read_text(encoding="utf-8"))
        payload = {
            "candidates": [
                {
                    "id": "fact-1",
                    "item_id": "fact-1",
                    "title": "Reuters earnings wrap",
                    "source": "Reuters",
                    "source_role": "fact_anchor",
                    "evidence_role": "fact",
                    "ppt_asset_candidate": True,
                    "talk_vs_slide": "talk_or_slide",
                    "asset_type": "article_screenshot",
                },
                {
                    "id": "chart-1",
                    "item_id": "chart-1",
                    "title": "10Y chart",
                    "source": "Datawrapper",
                    "source_role": "data_anchor",
                    "evidence_role": "market_reaction",
                    "ppt_asset_candidate": True,
                    "talk_vs_slide": "slide",
                    "asset_type": "rates_chart",
                },
                {
                    "id": "x-1",
                    "item_id": "x-1",
                    "title": "X post",
                    "source": "X",
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                    "ppt_asset_candidate": False,
                    "talk_vs_slide": "talk_only",
                },
            ]
        }

        normalized = brief_builder.normalize_brief(brief, payload)

        self.assertEqual("normal", normalized["broadcast_mode"])
        self.assertTrue(normalized["one_line_market_frame"])
        self.assertEqual("storyline-1", normalized["storylines"][0]["storyline_id"])
        self.assertTrue(normalized["storylines"][0]["lead_candidate_reason"])
        self.assertEqual("fact-1", normalized["storylines"][0]["evidence_to_use"][0]["evidence_id"])
        self.assertEqual("article_screenshot", normalized["storylines"][0]["ppt_asset_queue"][0]["visual_asset_role"])
        self.assertEqual("x-1", normalized["talk_only_queue"][0]["item_id"])

    def test_editorial_schema_requires_new_broadcast_fields(self) -> None:
        required = set(brief_builder.EDITORIAL_SCHEMA["required"])
        self.assertLessEqual({"broadcast_mode", "market_map_summary", "ppt_asset_queue", "talk_only_queue", "drop_list"}, required)
        story_required = set(brief_builder.STORYLINE_SCHEMA["required"])
        self.assertLessEqual({"lead_candidate_reason", "signal_or_noise", "market_causality", "ppt_asset_queue", "closing_line"}, story_required)

    def test_compact_candidate_infers_missing_roles_for_legacy_radar(self) -> None:
        candidate = brief_builder.compact_candidate(
            {
                "id": "https://x.com/example/status/1",
                "title": "Market reaction screenshot",
                "source": "Example on X",
                "url": "https://x.com/example/status/1",
                "visual_local_path": "runtime/assets/x-post.png",
            }
        )

        self.assertEqual("sentiment_probe", candidate["source_role"])
        self.assertEqual("sentiment", candidate["evidence_role"])
        self.assertTrue(candidate["ppt_asset_candidate"])
        self.assertEqual("x_post_screenshot", candidate["asset_type"])

    def test_normalize_brief_repairs_sentiment_only_storyline(self) -> None:
        story = {
            "storyline_id": "story-1",
            "rank": 1,
            "title": "Oil shock",
            "recommendation_stars": 3,
            "rating_reason": "Lead",
            "lead_candidate_reason": "Market-moving",
            "hook": "Oil moved markets.",
            "why_now": "Brent moved before the open.",
            "core_argument": "Energy is the risk frame.",
            "signal_or_noise": "signal",
            "market_causality": "needs support",
            "expectation_gap": "check_if_relevant",
            "prepricing_risk": "possible",
            "first_5min_fit": "high",
            "korea_open_relevance": "medium",
            "talk_track": "Explain oil first.",
            "slide_order": [],
            "slide_plan": [],
            "ppt_asset_queue": [],
            "evidence_to_use": [
                {
                    "item_id": "x-oil",
                    "evidence_id": "x-oil",
                    "title": "X oil reaction",
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                    "reason": "Social reaction",
                }
            ],
            "evidence_to_drop": [],
            "drop_code": "",
            "counterpoint": "",
            "what_would_change_my_mind": "",
            "closing_line": "",
        }
        payload = {
            "candidates": [
                {
                    "id": "x-oil",
                    "item_id": "x-oil",
                    "title": "X oil reaction",
                    "source": "X",
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                    "theme_keys": ["energy_geopolitics"],
                },
                {
                    "id": "yahoo-oil",
                    "item_id": "yahoo-oil",
                    "title": "Oil market analysis",
                    "source": "Yahoo Finance",
                    "source_role": "analysis_anchor",
                    "evidence_role": "analysis",
                    "theme_keys": ["energy_geopolitics"],
                    "score": 12,
                },
            ]
        }

        normalized = brief_builder.normalize_brief({"storylines": [story, story, story]}, payload)
        roles = {item["evidence_role"] for item in normalized["storylines"][0]["evidence_to_use"]}

        self.assertIn("analysis", roles)
        self.assertIn("auto_added_fact_data_analysis_support", normalized["storylines"][0]["market_causality"])

    def test_normalize_brief_repairs_sentiment_only_storyline_with_text_theme(self) -> None:
        story = {
            "storyline_id": "story-positioning",
            "rank": 3,
            "title": "과열 신호인가? 포지셔닝과 밸류에이션 점검",
            "recommendation_stars": 2,
            "rating_reason": "Backup",
            "lead_candidate_reason": "Risk appetite check",
            "hook": "S&P 500이 신고가를 내면서 과열 여부를 점검한다.",
            "why_now": "best month and record high signals need valuation support.",
            "core_argument": "Positioning needs data support.",
            "signal_or_noise": "watch",
            "market_causality": "needs support",
            "expectation_gap": "not_primary",
            "prepricing_risk": "possible",
            "first_5min_fit": "medium",
            "korea_open_relevance": "medium",
            "talk_track": "Explain valuation after the rally.",
            "slide_order": [],
            "slide_plan": [],
            "ppt_asset_queue": [],
            "evidence_to_use": [
                {
                    "item_id": "x-record",
                    "evidence_id": "x-record",
                    "title": "The stock market just had its best month since November 2020.",
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                    "reason": "Social market reaction",
                }
            ],
            "evidence_to_drop": [],
            "drop_code": "",
            "counterpoint": "",
            "what_would_change_my_mind": "",
            "closing_line": "",
        }
        payload = {
            "candidates": [
                {
                    "id": "x-record",
                    "item_id": "x-record",
                    "title": "The stock market just had its best month since November 2020.",
                    "source": "X",
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                },
                {
                    "id": "isabelnet-valuation",
                    "item_id": "isabelnet-valuation",
                    "title": "S&P 500 Sector P/E Valuations Relative to History",
                    "source": "Blog - ISABELNET",
                    "source_role": "data_anchor",
                    "evidence_role": "data",
                    "score": 3,
                },
            ]
        }

        normalized = brief_builder.normalize_brief({"storylines": [story, story, story]}, payload)
        roles = {item["evidence_role"] for item in normalized["storylines"][0]["evidence_to_use"]}

        self.assertIn("data", roles)

    def test_select_editorial_candidates_keeps_support_evidence_beyond_top_scores(self) -> None:
        rows = [
            {
                "id": f"x-{index}",
                "title": f"X post {index}",
                "source": "X",
                "url": f"https://x.com/example/status/{index}",
                "score": 100 - index,
            }
            for index in range(5)
        ]
        rows.append(
            {
                "id": "support-1",
                "title": "Reuters support",
                "source": "Reuters",
                "url": "https://reuters.com/example",
                "score": 1,
            }
        )

        selected = brief_builder.select_editorial_candidates(rows, 3)

        self.assertIn("support-1", {item["id"] for item in selected})

    def test_select_editorial_candidates_keeps_storyline_refs_beyond_top_scores(self) -> None:
        rows = [
            {
                "id": f"x-{index}",
                "title": f"High score post {index}",
                "source": "X",
                "url": f"https://x.com/example/status/{index}",
                "score": 100 - index,
            }
            for index in range(8)
        ]
        rows.append(
            {
                "id": "biztoc-com-source-091",
                "title": "Standard Intelligence raises $75M valuation $500M #tech",
                "source": "BizToc",
                "url": "https://alltoc.com/tech/standard-intelligence-raises-75m-valuation-500m",
                "score": 0,
            }
        )
        storylines = [
            {
                "selected_item_ids": ["biztoc-com-source-091"],
                "material_refs": [{"id": "x-1"}],
            }
        ]

        required_ids = brief_builder.referenced_candidate_ids_from_storylines(storylines)
        selected = brief_builder.select_editorial_candidates(rows, 3, required_ids=required_ids)
        selected_ids = {item["id"] for item in selected}

        self.assertIn("biztoc-com-source-091", selected_ids)
        self.assertIn("x-1", selected_ids)

    def test_select_editorial_candidates_keeps_positioning_support_beyond_top_scores(self) -> None:
        rows = [
            {
                "id": f"x-{index}",
                "title": f"High score social post {index}",
                "source": "X",
                "url": f"https://x.com/example/status/{index}",
                "score": 100 - index,
            }
            for index in range(8)
        ]
        rows.append(
            {
                "id": "isabelnet-valuation",
                "title": "S&P 500 Sector P/E Valuations Relative to History",
                "source": "Blog - ISABELNET",
                "url": "https://www.isabelnet.com/sector-valuations",
                "score": 1,
            }
        )

        selected = brief_builder.select_editorial_candidates(rows, 3)

        self.assertIn("isabelnet-valuation", {item["id"] for item in selected})


if __name__ == "__main__":
    unittest.main()
