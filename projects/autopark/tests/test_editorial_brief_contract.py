from __future__ import annotations

from contextlib import contextmanager
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_editorial_brief as brief_builder


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@contextmanager
def local_temp_root():
    root = PROJECT / f".tmp-editorial-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def candidate(item_id: str, **extra: object) -> dict:
    row = {
        "id": item_id,
        "item_id": item_id,
        "title": f"Local evidence {item_id}",
        "source": "Reuters",
        "source_role": "fact_anchor",
        "evidence_role": "fact",
        "summary": f"Compact summary for {item_id}.",
        "theme_keys": ["rates_macro"],
        "score": 10,
    }
    row.update(extra)
    return row


def model_brief() -> dict:
    stories = []
    for index, item_id in enumerate(["c1", "c2", "c3"], start=1):
        stories.append(
            {
                "storyline_id": f"story-{index}",
                "rank": index,
                "title": f"Editorial story {index}",
                "recommendation_stars": 3 if index == 1 else 2,
                "rating_reason": "usable",
                "lead_candidate_reason": "Local evidence supports this segment.",
                "hook": f"Hook {index}",
                "why_now": "The local packet has a timely fact anchor.",
                "core_argument": "Use local evidence, not web-only claims.",
                "signal_or_noise": "signal",
                "market_causality": "fact/data/analysis support present",
                "expectation_gap": "check_if_relevant",
                "prepricing_risk": "check_if_relevant",
                "first_5min_fit": "high",
                "korea_open_relevance": "medium",
                "evidence_to_use": [
                    {
                        "item_id": item_id,
                        "evidence_id": item_id,
                        "title": f"Local evidence {item_id}",
                        "source_role": "fact_anchor",
                        "evidence_role": "fact",
                        "reason": "Local packet fact anchor.",
                    }
                ],
                "evidence_to_drop": [],
                "drop_code": "",
                "slide_order": [f"Slide {index}"],
                "slide_plan": [f"Slide {index}"],
                "ppt_asset_queue": [],
                "talk_track": f"Talk track {index}.",
                "counterpoint": "If the local evidence weakens, downgrade.",
                "what_would_change_my_mind": "Contrary local data.",
                "closing_line": f"Closing {index}.",
            }
        )
    return {
        "broadcast_mode": "normal",
        "daily_thesis": "Use local evidence to choose the lead.",
        "one_line_market_frame": "Rates and local evidence frame the morning.",
        "market_map_summary": "Market map is mixed.",
        "editorial_summary": "Three local-evidence segments are usable.",
        "ppt_asset_queue": [],
        "talk_only_queue": [],
        "drop_list": [],
        "retrospective_watchpoints": [],
        "storylines": stories,
    }


def seed_editorial_inputs(root: Path, target_date: str = "2026-05-03", extra_candidate: dict | None = None) -> tuple[Path, Path]:
    processed = root / "data" / "processed"
    runtime = root / "runtime"
    day = processed / target_date
    rows = [candidate("c1"), candidate("c2"), candidate("c3")]
    if extra_candidate:
        rows.append(extra_candidate)
    write_json(
        day / "market-radar.json",
        {
            "candidates": rows,
            "storylines": [
                {"storyline_id": f"fallback-{idx}", "title": f"Fallback {idx}", "selected_item_ids": [item_id], "recommendation_stars": 2}
                for idx, item_id in enumerate(["c1", "c2", "c3"], start=1)
            ],
        },
    )
    write_json(
        day / "market-focus-brief.json",
        {
            "market_focus_summary": "Local focus available.",
            "what_market_is_watching": [{"rank": 1, "focus": "Rates", "broadcast_use": "lead", "evidence_ids": ["c1"], "source_ids": ["c1"]}],
            "source_gaps": [{"issue": "gap", "safe_for_public": False}],
            "suggested_broadcast_order": [{"rank": 1, "focus_rank": 1, "suggested_story_title": "Rates", "broadcast_use": "lead", "evidence_ids": ["c1"]}],
        },
    )
    write_json(day / "finviz-feature-stocks.json", {"items": []})
    write_json(day / "visual-cards.json", {"cards": []})
    return processed, runtime


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

    def test_editorial_timeout_fallback_records_debug_stats(self) -> None:
        with local_temp_root() as root:
            processed, runtime = seed_editorial_inputs(root)
            env_path = root / ".env"
            env_path.write_text("OPENAI_API_KEY=dummy\n", encoding="utf-8")
            output = root / "editorial-brief.json"
            argv = [
                "build_editorial_brief.py",
                "--date",
                "2026-05-03",
                "--env",
                str(env_path),
                "--output",
                str(output),
                "--api-timeout-seconds",
                "1",
            ]
            with (
                mock.patch.object(brief_builder, "PROCESSED_DIR", processed),
                mock.patch.object(brief_builder, "RUNTIME_DIR", runtime),
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(brief_builder, "call_openai", side_effect=TimeoutError("read timed out")),
            ):
                self.assertEqual(0, brief_builder.main())

            brief = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(brief["fallback"])
            self.assertEqual("editorial_api_timeout", brief["fallback_code"])
            self.assertIn("first_attempt", brief["debug_stats"])
            self.assertIn("retry_attempt", brief["debug_stats"])
            self.assertEqual("editorial_timeout_retry_compact", brief["debug_stats"]["retry_attempt"]["retry_code"])
            self.assertTrue(brief["storylines"])

    def test_editorial_timeout_compact_retry_can_succeed(self) -> None:
        with local_temp_root() as root:
            processed, runtime = seed_editorial_inputs(root)
            env_path = root / ".env"
            env_path.write_text("OPENAI_API_KEY=dummy\n", encoding="utf-8")
            output = root / "editorial-brief.json"
            argv = [
                "build_editorial_brief.py",
                "--date",
                "2026-05-03",
                "--env",
                str(env_path),
                "--output",
                str(output),
                "--api-timeout-seconds",
                "1",
            ]
            with (
                mock.patch.object(brief_builder, "PROCESSED_DIR", processed),
                mock.patch.object(brief_builder, "RUNTIME_DIR", runtime),
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(brief_builder, "call_openai", side_effect=[TimeoutError("read timed out"), (model_brief(), "resp_retry", {"id": "resp_retry"})]),
            ):
                self.assertEqual(0, brief_builder.main())

            brief = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(brief["fallback"])
            self.assertEqual("resp_retry", brief["raw_response_id"])
            self.assertEqual("editorial_timeout_retry_compact", brief["debug_stats"]["retry_attempt"]["retry_code"])
            self.assertLessEqual(
                brief["debug_stats"]["retry_attempt"]["candidate_count_sent"],
                brief["debug_stats"]["first_attempt"]["candidate_count_sent"],
            )

    def test_compact_retry_prompt_excludes_raw_fields_but_keeps_evidence_roles(self) -> None:
        raw_candidate = candidate(
            "c-raw",
            title="Local raw candidate",
            source="X",
            source_role="sentiment_probe",
            evidence_role="sentiment",
            url="https://example.com/article?X-Amz-Signature=secret",
            visual_local_path=r"C:\Users\User1\screenshots\raw.png",
            summary="Compact summary with https://example.com/path and C:\\temp\\raw.png",
            body="FULL ARTICLE BODY SHOULD NOT APPEAR",
            html="<html>SHOULD NOT APPEAR</html>",
            text="FULL X TEXT SHOULD NOT APPEAR",
        )
        with local_temp_root() as root:
            processed, runtime = seed_editorial_inputs(root, extra_candidate=raw_candidate)
            day = processed / "2026-05-03"
            write_json(
                day / "finviz-feature-stocks.json",
                {
                    "items": [
                        {
                            "ticker": "RAW",
                            "title": "Raw ticker",
                            "screenshot_path": r"C:\Users\User1\finviz\raw.png",
                            "news": [{"time": "now", "headline": "Headline", "url": "https://example.com/news"}],
                        }
                    ]
                },
            )
            write_json(
                day / "visual-cards.json",
                {"cards": [{"id": "card-raw", "title": "Card", "summary": "See https://example.com/card", "local_path": r"C:\tmp\card.png"}]},
            )
            with mock.patch.object(brief_builder, "PROCESSED_DIR", processed), mock.patch.object(brief_builder, "RUNTIME_DIR", runtime):
                payload = brief_builder.build_input_payload("2026-05-03", 28, compact_retry=True)
                prompt = brief_builder.build_prompt(payload)

        self.assertNotIn("https://", prompt)
        self.assertNotIn("C:\\", prompt)
        self.assertNotIn("X-Amz", prompt)
        self.assertNotIn("FULL ARTICLE BODY SHOULD NOT APPEAR", prompt)
        self.assertNotIn("<html>", prompt)
        self.assertNotIn("FULL X TEXT SHOULD NOT APPEAR", prompt)
        self.assertIn("c-raw", prompt)
        self.assertIn("source_role", prompt)
        self.assertIn("evidence_role", prompt)
        self.assertIn("asset_status", prompt)


if __name__ == "__main__":
    unittest.main()
