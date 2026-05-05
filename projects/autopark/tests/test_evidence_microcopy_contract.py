from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_editorial_brief as editorial
import build_evidence_microcopy as evidence_microcopy
import build_market_focus_brief as market_focus
import review_dashboard_quality as quality


DATE = "2026-05-03"


class EvidenceMicrocopyContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_root = PROJECT / ".test-runtime" / f"evidence-microcopy-{uuid.uuid4().hex}"
        self.processed = self.runtime_root / "processed"
        (self.processed / DATE).mkdir(parents=True)
        self._paths = {
            "evidence": evidence_microcopy.PROCESSED_DIR,
            "market_focus": market_focus.PROCESSED_DIR,
            "editorial": editorial.PROCESSED_DIR,
            "quality": quality.PROCESSED_DIR,
        }
        evidence_microcopy.PROCESSED_DIR = self.processed
        market_focus.PROCESSED_DIR = self.processed
        editorial.PROCESSED_DIR = self.processed
        quality.PROCESSED_DIR = self.processed
        self._write_json(
            "market-radar.json",
            {
                "candidate_count": 2,
                "storylines": [{"selected_item_ids": ["oil-1"], "title": "Oil pressure", "rank": 1}],
                "candidates": [
                    {
                        "id": "oil-1",
                        "title": "Oil traders watch Brent and Hormuz tension",
                        "source": "Reuters",
                        "summary": "Brent and WTI are being watched against geopolitical tension.",
                        "theme_keys": ["energy_geopolitics"],
                    },
                    {
                        "id": "rates-1",
                        "title": "Fed officials keep inflation warnings alive",
                        "source": "Yahoo Finance",
                        "summary": "Treasury yields and inflation expectations remain a market constraint.",
                        "theme_keys": ["rates_macro"],
                    },
                ],
            },
        )
        self._write_json("visual-cards.json", {"cards": []})
        self._write_json("market-preflight-agenda.json", {})
        self._write_json("market-focus-brief.json", {"what_market_is_watching": []})
        self._write_json("finviz-feature-stocks.json", {"items": []})

    def tearDown(self) -> None:
        evidence_microcopy.PROCESSED_DIR = self._paths["evidence"]
        market_focus.PROCESSED_DIR = self._paths["market_focus"]
        editorial.PROCESSED_DIR = self._paths["editorial"]
        quality.PROCESSED_DIR = self._paths["quality"]
        if self.runtime_root.exists():
            shutil.rmtree(self.runtime_root)

    def _write_json(self, name: str, payload: object) -> None:
        (self.processed / DATE / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_group_size_allows_small_experiment_groups_and_caps_at_40(self) -> None:
        self.assertEqual(3, evidence_microcopy.group_size_from(3))
        self.assertEqual(30, evidence_microcopy.group_size_from(None))
        self.assertEqual(40, evidence_microcopy.group_size_from(99))

    def test_missing_api_key_generates_deterministic_artifact(self) -> None:
        payload = evidence_microcopy.build_microcopy(
            DATE,
            {"AUTOPARK_EVIDENCE_MICROCOPY_ENABLED": "1", "AUTOPARK_EVIDENCE_MICROCOPY_MODEL": "gpt-5-mini"},
            limit=10,
            group_size=20,
            timeout=1,
        )
        self.assertEqual("deterministic_missing_api_key", payload["source"])
        self.assertEqual(2, payload["item_count"])
        self.assertEqual(2, payload["fallback_count"])
        self.assertTrue(all(item["title"] for item in payload["items"]))
        self.assertTrue(all(len(item["title"]) <= 28 for item in payload["items"]))
        self.assertTrue(all(item["content"] for item in payload["items"]))
        self.assertTrue(all(len(item["content"]) <= 300 for item in payload["items"]))

    def test_headline_river_items_are_included_without_replacing_radar(self) -> None:
        self._write_json(
            "headline-river.json",
            {
                "ok": True,
                "items": [
                    {
                        "item_id": "headline-1",
                        "source_label": "Finviz News",
                        "publisher": "MarketWatch",
                        "title": "Stocks rise as oil headlines remain in focus",
                        "snippet": "Market headlines kept oil and rates in view.",
                        "url": "https://example.com/headline-1",
                        "source_role": "baseline_headline",
                        "agenda_links": ["agenda_oil_risk"],
                        "content_level": "headline+summary",
                    }
                ],
            },
        )

        payload = evidence_microcopy.build_microcopy(
            DATE,
            {"AUTOPARK_EVIDENCE_MICROCOPY_ENABLED": "0"},
            limit=10,
            group_size=20,
            timeout=1,
        )

        self.assertEqual(3, payload["item_count"])
        self.assertEqual(2, payload["candidate_count"])
        self.assertEqual(1, payload["headline_item_count"])
        self.assertEqual(0, payload["analysis_item_count"])
        self.assertIn("headline-1", {item["item_id"] for item in payload["items"]})

    def test_analysis_river_items_are_included_as_microcopy_sources(self) -> None:
        self._write_json(
            "analysis-river.json",
            {
                "ok": True,
                "items": [
                    {
                        "item_id": "analysis-1",
                        "source_label": "Kobeissi Letter",
                        "title": "Fed and oil dominate market attention",
                        "summary": "Markets are watching Fed expectations and oil risk together.",
                        "url": "https://example.com/analysis-1",
                        "source_role": "market_attention",
                        "content_level": "text",
                    }
                ],
            },
        )

        payload = evidence_microcopy.build_microcopy(
            DATE,
            {"AUTOPARK_EVIDENCE_MICROCOPY_ENABLED": "0"},
            limit=10,
            group_size=20,
            timeout=1,
        )

        self.assertEqual(3, payload["item_count"])
        self.assertEqual(1, payload["analysis_item_count"])
        self.assertIn("analysis-1", {item["item_id"] for item in payload["items"]})

    def test_invalid_output_falls_back_for_that_item_only(self) -> None:
        source_item = {"id": "oil-1", "title": "Oil", "source": "Reuters", "summary": "Oil summary"}
        valid, errors = evidence_microcopy.validate_item(
            {
                "item_id": "wrong-id",
                "source_label": "Reuters",
                "title": "Oil",
                "content": "",
            },
            source_item,
        )
        self.assertIn("item_id_mismatch", errors)
        self.assertIn("missing_content", errors)
        self.assertEqual("oil-1", valid["item_id"])

    def test_content_must_be_one_to_three_sentences(self) -> None:
        source_item = {"id": "oil-1", "title": "Oil", "source": "Reuters", "summary": "Oil summary"}
        _, errors = evidence_microcopy.validate_item(
            {
                "item_id": "oil-1",
                "source_label": "Reuters",
                "title": "Oil",
                "content": "첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. 넷째 문장입니다.",
            },
            source_item,
        )
        self.assertIn("content_sentence_count", errors)

    def test_deterministic_content_collapses_numbered_lists_to_contract(self) -> None:
        item = {
            "id": "calendar-1",
            "title": "Key Events This Week",
            "source": "Kobeissi Letter",
            "summary": "1. JOLTS data Tuesday. 2. ISM data Tuesday. 3. ADP data Wednesday. 4. Jobs report Friday. 5. Fed speakers this week.",
        }

        content = evidence_microcopy.fallback_content(item)

        self.assertLessEqual(len(evidence_microcopy.content_sentences(content)), 3)
        self.assertNotIn("4.", content)

    def test_url_item_ids_validate_without_cleaning_away_key(self) -> None:
        source_item = {
            "id": "https://x.com/example/status/1",
            "title": "Synthetic social post",
            "source": "X",
            "summary": "A short social item.",
        }
        valid, errors = evidence_microcopy.validate_item(
            {
                "item_id": "https://x.com/example/status/1",
                "source_label": "X",
                "title": "Synthetic social post",
                "content": "소셜 게시물의 핵심을 짧게 확인했습니다.",
            },
            source_item,
        )
        self.assertEqual([], errors)
        self.assertEqual("https://x.com/example/status/1", valid["item_id"])

    def test_focus_and_editorial_payloads_include_microcopy_fields(self) -> None:
        self._write_json(
            "evidence-microcopy.json",
            {
                "ok": True,
                "enabled": False,
                "items": [
                    {
                        "item_id": "oil-1",
                        "source_label": "Reuters",
                        "title": "Oil",
                        "content": "유가 리스크와 가격 반응을 함께 확인했습니다.",
                    }
                ],
            },
        )
        focus_payload = market_focus.build_input_payload(DATE, 5, 0, 0)
        focus_candidate = focus_payload["market_radar"]["candidates"][0]
        self.assertEqual("유가 리스크와 가격 반응을 함께 확인했습니다.", focus_candidate["micro_content"])
        editorial_payload = editorial.build_input_payload(DATE, 5)
        editorial_candidate = next(item for item in editorial_payload["candidates"] if item["id"] == "oil-1")
        self.assertEqual("유가 리스크와 가격 반응을 함께 확인했습니다.", editorial_candidate["summary"])
        self.assertNotIn("micro_content", editorial_candidate)

    def test_quality_gate_reviews_evidence_microcopy_artifact(self) -> None:
        self._write_json(
            "evidence-microcopy.json",
            {
                "ok": True,
                "enabled": True,
                "generated_fields": ["title", "content"],
                "items": [
                    {
                        "item_id": "oil-1",
                        "source_label": "Reuters",
                        "title": "Oil",
                        "content": "x" * 301,
                    }
                ],
            },
        )
        findings = quality.review_evidence_microcopy_contract(DATE)
        self.assertTrue(any("too long" in item.title.lower() for item in findings))

    def test_quality_gate_warns_on_weak_headline_river_without_blocker_severity(self) -> None:
        self._write_json(
            "headline-river.json",
            {
                "ok": True,
                "items": [],
                "source_stats": [
                    {"source_id": "finviz-news", "item_count": 0},
                    {"source_id": "yahoo-finance-ticker-rss", "item_count": 0},
                    {"source_id": "biztoc-feed", "item_count": 0},
                    {"source_id": "biztoc-home", "item_count": 0},
                ],
                "agenda_expansions": [],
                "anomaly_summary": {"top_keywords": []},
            },
        )

        findings = quality.review_headline_river_contract(DATE)

        self.assertTrue(findings)
        self.assertTrue(all(item.severity == "low" for item in findings))
        self.assertTrue(any("Headline river has no items" == item.title for item in findings))

    def test_quality_gate_warns_on_empty_analysis_river_without_blocker_severity(self) -> None:
        self._write_json(
            "analysis-river.json",
            {
                "ok": True,
                "items": [],
                "source_stats": [],
            },
        )

        findings = quality.review_analysis_river_contract(DATE)

        self.assertTrue(findings)
        self.assertTrue(all(item.severity == "low" for item in findings))
        self.assertTrue(any("Analysis river has no items" == item.title for item in findings))


if __name__ == "__main__":
    unittest.main()
