from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_market_preflight_agenda as preflight


class MarketPreflightAgendaContractTest(unittest.TestCase):
    def test_fixture_satisfies_preflight_contract(self) -> None:
        fixture = PROJECT / "tests" / "fixtures" / "market-preflight-agenda-0503.json"
        agenda = json.loads(fixture.read_text(encoding="utf-8"))

        errors = preflight.validate_agenda(agenda)

        self.assertEqual([], errors)
        self.assertIn("preflight_summary", agenda)
        self.assertGreaterEqual(len(agenda["agenda_items"]), 1)
        for item in agenda["agenda_items"]:
            self.assertFalse(item["public_safe"])
            self.assertTrue(item["must_verify_with_local_evidence"])
            self.assertGreaterEqual(len(item["collection_targets"]), 1)

    def test_normalize_forces_preflight_to_non_public(self) -> None:
        raw = {
            "date": "2026-05-03",
            "preflight_summary": "Check rates first.",
            "agenda_items": [
                {
                    "rank": 1,
                    "agenda_id": "Rates first",
                    "market_question": "Are rates the constraint?",
                    "why_to_check": "Rates can cap growth stocks.",
                    "expected_broadcast_use": "lead_candidate",
                    "collection_targets": [
                        {
                            "target_type": "chart",
                            "query_or_asset": "US10Y",
                            "preferred_sources": [],
                            "reason": "confirm market reaction",
                        }
                    ],
                    "must_verify_with_local_evidence": False,
                    "public_safe": True,
                }
            ],
            "collection_priorities": {
                "fixed_charts": ["US10Y"],
                "targeted_news_queries": ["Fed inflation Reuters"],
                "targeted_x_queries": ["US10Y DXY Nasdaq reaction"],
                "official_or_primary_sources": ["Fed"],
            },
            "do_not_use_publicly": [],
            "source_gaps_to_watch": [],
        }

        agenda = preflight.normalize_agenda(raw, "2026-05-03")

        self.assertFalse(agenda["agenda_items"][0]["public_safe"])
        self.assertTrue(agenda["agenda_items"][0]["must_verify_with_local_evidence"])
        self.assertEqual([], preflight.validate_agenda(agenda))

    def test_fallback_agenda_keeps_pipeline_contract(self) -> None:
        agenda = preflight.fallback_agenda("2026-05-03", "test", model="gpt-5.5", with_web=True)

        self.assertTrue(agenda["fallback"])
        self.assertEqual("preflight_openai_unavailable", agenda["fallback_code"])
        self.assertEqual("gpt-5.5", agenda["model"])
        self.assertTrue(agenda["with_web"])
        self.assertEqual([], preflight.validate_agenda(agenda))

    def test_model_and_web_defaults(self) -> None:
        env = {"AUTOPARK_PREFLIGHT_MODEL": "gpt-5.4", "AUTOPARK_OPENAI_MODEL": "gpt-4.1"}

        self.assertEqual("custom", preflight.resolve_model("custom", env))
        self.assertEqual("gpt-5.4", preflight.resolve_model(None, env))
        self.assertEqual("gpt-4.1", preflight.resolve_model(None, {"AUTOPARK_OPENAI_MODEL": "gpt-4.1"}))
        self.assertEqual(preflight.DEFAULT_MODEL, preflight.resolve_model(None, {}))


if __name__ == "__main__":
    unittest.main()
