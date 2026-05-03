from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_market_focus_brief as focus_builder


class MarketFocusBriefContractTest(unittest.TestCase):
    def test_fixture_satisfies_market_focus_contract(self) -> None:
        fixture = PROJECT / "tests" / "fixtures" / "market-focus-brief-0503.json"
        brief = json.loads(fixture.read_text(encoding="utf-8"))

        errors = focus_builder.validate_brief(brief)

        self.assertEqual([], errors)
        required = {
            "market_focus_summary",
            "what_market_is_watching",
            "false_leads",
            "missing_assets",
            "source_gaps",
            "suggested_broadcast_order",
        }
        self.assertLessEqual(required, set(brief))
        for item in brief["what_market_is_watching"]:
            ids = [*(item.get("source_ids") or []), *(item.get("evidence_ids") or [])]
            if item["broadcast_use"] != "drop":
                self.assertTrue(ids)

    def test_schema_requires_requested_focus_fields(self) -> None:
        top_required = set(focus_builder.MARKET_FOCUS_SCHEMA["required"])
        self.assertLessEqual(
            {
                "market_focus_summary",
                "what_market_is_watching",
                "false_leads",
                "missing_assets",
                "source_gaps",
                "suggested_broadcast_order",
            },
            top_required,
        )
        item_required = set(focus_builder.FOCUS_ITEM_SCHEMA["required"])
        self.assertLessEqual(
            {
                "rank",
                "focus",
                "market_question",
                "why_it_matters",
                "price_confirmation",
                "broadcast_use",
                "confidence",
                "suggested_story_title",
                "one_sentence_for_host",
                "source_ids",
                "evidence_ids",
                "missing_assets",
            },
            item_required,
        )

    def test_normalize_demotes_public_story_without_local_evidence(self) -> None:
        payload = {
            "market_radar": {
                "candidates": [
                    {
                        "id": "known-1",
                        "item_id": "known-1",
                        "title": "Known local story",
                    }
                ],
                "storylines": [],
            },
            "raw_sources": [],
            "charts": [],
            "available_assets": [],
        }
        raw = {
            "market_focus_summary": "A web-only issue looks interesting.",
            "what_market_is_watching": [
                {
                    "rank": 1,
                    "focus": "Unsourced surprise story",
                    "market_question": "Is this really moving markets?",
                    "why_it_matters": "It could matter if locally sourced.",
                    "price_confirmation": "No local chart confirmation.",
                    "broadcast_use": "lead",
                    "confidence": 0.9,
                    "suggested_story_title": "Unsourced lead",
                    "one_sentence_for_host": "Do not say this publicly yet.",
                    "source_ids": [],
                    "evidence_ids": [],
                    "missing_assets": [],
                }
            ],
            "false_leads": [],
            "missing_assets": [],
            "source_gaps": [],
            "suggested_broadcast_order": [],
        }

        normalized = focus_builder.normalize_brief(raw, payload)

        self.assertEqual("drop", normalized["what_market_is_watching"][0]["broadcast_use"])
        self.assertIn("local evidence_id", normalized["what_market_is_watching"][0]["missing_assets"][0])
        self.assertFalse(normalized["source_gaps"][0]["safe_for_public"])
        self.assertEqual([], normalized["suggested_broadcast_order"])

    def test_fallback_brief_keeps_pipeline_contract(self) -> None:
        payload = {
            "market_radar": {
                "storylines": [
                    {
                        "title": "Rates frame",
                        "one_liner": "Rates and dollar are the market frame.",
                        "why_selected": "Multiple local sources point to the same market question.",
                        "selected_item_ids": ["known-1"],
                        "recommendation_stars": 3,
                    }
                ],
                "candidates": [
                    {
                        "id": "known-1",
                        "item_id": "known-1",
                        "title": "Fed inflation warning",
                        "source": "Reuters",
                        "radar_question": "Are rates repricing risk assets?",
                        "theme_keys": ["rates_macro"],
                    }
                ],
            },
            "raw_sources": [],
            "charts": [{"chart_id": "us10y", "title": "US 10Y: 4.38%"}],
            "available_assets": [],
        }

        brief = focus_builder.fallback_brief("2026-05-03", "test", payload)

        self.assertEqual([], focus_builder.validate_brief(brief))
        self.assertTrue(brief["fallback"])
        self.assertEqual("openai_unavailable", brief["fallback_code"])
        self.assertEqual("lead", brief["what_market_is_watching"][0]["broadcast_use"])
        self.assertEqual("known-1", brief["suggested_broadcast_order"][0]["evidence_ids"][0])

    def test_market_focus_model_override_priority(self) -> None:
        env = {
            "AUTOPARK_MARKET_FOCUS_MODEL": "gpt-5.4",
            "AUTOPARK_OPENAI_MODEL": "gpt-4.1",
        }

        self.assertEqual("custom-model", focus_builder.resolve_model("custom-model", env))
        self.assertEqual("gpt-5.4", focus_builder.resolve_model(None, env))
        self.assertEqual("gpt-4.1", focus_builder.resolve_model(None, {"AUTOPARK_OPENAI_MODEL": "gpt-4.1"}))
        self.assertEqual(focus_builder.DEFAULT_MODEL, focus_builder.resolve_model(None, {}))

    def test_model_availability_errors_are_classified_for_fallback(self) -> None:
        self.assertEqual(
            "model_not_available",
            focus_builder.classify_openai_error(400, "model_not_found", "The model does not exist."),
        )
        self.assertEqual(
            "model_not_available",
            focus_builder.classify_openai_error(403, "invalid_request_error", "You do not have access to model gpt-5.5."),
        )

    def test_synthetic_smoke_payload_has_local_ids_without_real_sources(self) -> None:
        payload = focus_builder.synthetic_smoke_payload("2026-05-03")
        ids = focus_builder.known_evidence_ids(payload)
        aliases = payload[focus_builder.LOCAL_ALIAS_KEY]

        self.assertTrue(any(value == "synthetic-fed-1" for value in aliases.values()))
        self.assertTrue(any(value == "synthetic-us10y-1" for value in aliases.values()))
        self.assertTrue(any(item.startswith("ev_") for item in ids))
        self.assertNotIn(focus_builder.LOCAL_ALIAS_KEY, focus_builder.prompt_payload(payload))
        self.assertTrue(payload["input_limits"]["synthetic_smoke"])


if __name__ == "__main__":
    unittest.main()
