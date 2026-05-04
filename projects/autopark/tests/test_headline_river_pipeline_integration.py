from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_editorial_brief as editorial
import build_market_focus_brief as market_focus
import build_market_radar as market_radar


class HeadlineRiverPipelineIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = PROJECT / ".tmp-tests" / "headline-river-integration"
        if self.tmp_root.exists():
            shutil.rmtree(self.tmp_root)
        self.processed = self.tmp_root / "processed"
        self.runtime = self.tmp_root / "runtime"
        self.raw = self.tmp_root / "raw"
        self.day_dir = self.processed / "2026-05-04"
        self.day_dir.mkdir(parents=True)
        self.runtime.mkdir(parents=True)
        self.raw.mkdir(parents=True)
        self.write_base_files()

    def tearDown(self) -> None:
        if self.tmp_root.exists():
            shutil.rmtree(self.tmp_root)

    def write_base_files(self) -> None:
        headline_river = {
            "ok": True,
            "date": "2026-05-04",
            "item_count": 2,
            "baseline_source_ids": ["finviz-news", "yahoo-finance-ticker-rss", "biztoc-feed", "biztoc-home"],
            "support_source_ids": ["cnbc-world"],
            "agenda_expansions": [{"agenda_id": "agenda_oil_risk", "rank": 1, "tickers": ["CL=F", "BZ=F"]}],
            "source_stats": [{"source_id": "finviz-news", "source_label": "Finviz News", "status": "ok", "source_role": "baseline_headline", "item_count": 1}],
            "anomaly_summary": {
                "top_keywords": [{"keyword": "oil", "count": 2}],
                "top_hosts": [{"host": "finance.yahoo.com", "count": 1}],
                "top_title_tokens": [{"token": "oil", "count": 2}],
            },
            "items": [
                {
                    "item_id": "finviz-news-001",
                    "source_id": "finviz-news",
                    "source_label": "Finviz News",
                    "publisher": "Reuters",
                    "title": "Oil rises as traders watch supply risk",
                    "url": "https://example.com/oil",
                    "published_at": "2026-05-04T01:00:00+00:00",
                    "snippet": "Crude traders kept supply risk in focus.",
                    "source_role": "baseline_headline",
                    "source_authority": "medium",
                    "content_level": "headline+summary",
                    "agenda_links": ["agenda_oil_risk"],
                    "detected_keywords": ["oil", "wti"],
                },
                {
                    "item_id": "biztoc-feed-001",
                    "source_id": "biztoc-feed",
                    "source_label": "BizToc RSS",
                    "publisher": "",
                    "title": "Fed and oil dominate market feeds",
                    "url": "https://example.com/fed-oil",
                    "published_at": "2026-05-04T01:10:00+00:00",
                    "snippet": "Market feeds repeated Fed and oil headlines.",
                    "source_role": "anomaly_detector",
                    "source_authority": "medium",
                    "content_level": "headline+summary",
                    "agenda_links": [],
                    "detected_keywords": ["fed", "oil"],
                },
            ],
        }
        preflight = {
            "preflight_summary": "Oil and Fed path are the morning hypotheses.",
            "agenda_items": [
                {
                    "rank": 1,
                    "agenda_id": "agenda_oil_risk",
                    "market_question": "Is oil moving inflation expectations?",
                    "why_to_check": "Oil can affect rates and Korea-open sectors.",
                    "expected_broadcast_use": "lead_check",
                    "must_verify_with_local_evidence": True,
                }
            ],
        }
        radar = {
            "ok": True,
            "candidate_count": 1,
            "storylines": [
                {
                    "storyline_id": "story_oil",
                    "rank": 1,
                    "title": "Oil risk returns",
                    "one_liner": "Oil is the market question.",
                    "selected_item_ids": ["finviz-news-001"],
                    "material_refs": [{"id": "finviz-news-001", "title": "Oil rises as traders watch supply risk", "source": "Reuters"}],
                    "recommendation_stars": 3,
                }
            ],
            "candidates": [
                {
                    "id": "finviz-news-001",
                    "title": "Oil rises as traders watch supply risk",
                    "source": "Reuters",
                    "url": "https://example.com/oil",
                    "summary": "Crude traders kept supply risk in focus.",
                    "theme_keys": ["energy_geopolitics"],
                    "source_role": "baseline_headline",
                    "evidence_role": "fact",
                    "score": 14,
                    "agenda_links": ["agenda_oil_risk"],
                }
            ],
        }
        analysis_river = {
            "ok": True,
            "date": "2026-05-04",
            "source": "analysis_river",
            "item_count": 1,
            "analysis_source_ids": ["x-kobeissiletter"],
            "role_counts": [{"role": "market_attention", "count": 1}],
            "source_stats": [{"source_id": "x-kobeissiletter", "source_label": "Kobeissi Letter", "status": "ok", "source_role": "market_attention", "item_count": 1}],
            "items": [
                {
                    "item_id": "x-kobeissiletter-001",
                    "source_id": "x-kobeissiletter",
                    "source_label": "Kobeissi Letter",
                    "title": "Fed and oil risk draw market attention",
                    "url": "https://example.com/kobeissi",
                    "summary": "Markets are watching Fed expectations and oil together.",
                    "source_role": "market_attention",
                    "source_authority": "medium",
                    "content_level": "text",
                    "detected_keywords": ["fed", "oil"],
                }
            ],
        }
        (self.day_dir / "headline-river.json").write_text(json.dumps(headline_river), encoding="utf-8")
        (self.day_dir / "analysis-river.json").write_text(json.dumps(analysis_river), encoding="utf-8")
        (self.day_dir / "market-preflight-agenda.json").write_text(json.dumps(preflight), encoding="utf-8")
        (self.day_dir / "market-radar.json").write_text(json.dumps(radar), encoding="utf-8")
        (self.day_dir / "visual-cards.json").write_text(json.dumps({"cards": []}), encoding="utf-8")
        (self.day_dir / "market-focus-brief.json").write_text(
            json.dumps(
                {
                    "market_focus_summary": "Oil is the lead check.",
                    "what_market_is_watching": [],
                    "false_leads": [],
                    "missing_assets": [],
                    "source_gaps": [],
                    "suggested_broadcast_order": [],
                }
            ),
            encoding="utf-8",
        )

    def test_market_radar_ingests_headline_river_items(self) -> None:
        original_processed = market_radar.PROCESSED_DIR
        original_gather = market_radar.gather_materials
        original_extra_x = market_radar.load_extra_x_posts
        market_radar.PROCESSED_DIR = self.processed
        market_radar.gather_materials = lambda *args, **kwargs: []
        market_radar.load_extra_x_posts = lambda *args, **kwargs: []
        try:
            rows = market_radar.build_rows("2026-05-04", 10, 10, 10)
        finally:
            market_radar.PROCESSED_DIR = original_processed
            market_radar.gather_materials = original_gather
            market_radar.load_extra_x_posts = original_extra_x

        self.assertTrue(any(row["id"] == "finviz-news-001" for row in rows))
        self.assertTrue(any(row["id"] == "x-kobeissiletter-001" for row in rows))
        oil_row = next(row for row in rows if row["id"] == "finviz-news-001")
        self.assertEqual("headline_river", oil_row["type"])
        self.assertEqual(["agenda_oil_risk"], oil_row["agenda_links"])
        analysis_row = next(row for row in rows if row["id"] == "x-kobeissiletter-001")
        self.assertEqual("analysis_river", analysis_row["type"])
        self.assertGreater(oil_row["content_level_bonus"], 0)

    def test_market_radar_scores_deeper_content_above_headline_only(self) -> None:
        headline_river = json.loads((self.day_dir / "headline-river.json").read_text(encoding="utf-8"))
        headline_river["items"] = [
            {
                "item_id": "headline-only",
                "source_id": "finviz-news",
                "source_label": "Finviz News",
                "publisher": "",
                "title": "Oil risk keeps inflation and Fed path in focus",
                "url": "https://example.com/oil-headline",
                "published_at": "2026-05-04T01:00:00+00:00",
                "snippet": "",
                "source_role": "baseline_headline",
                "source_authority": "medium",
                "content_level": "headline",
                "agenda_links": [],
                "detected_keywords": ["oil", "fed"],
            },
            {
                "item_id": "headline-summary",
                "source_id": "finviz-news",
                "source_label": "Finviz News",
                "publisher": "",
                "title": "Oil risk keeps inflation and Fed path in focus",
                "url": "https://example.com/oil-summary",
                "published_at": "2026-05-04T01:00:00+00:00",
                "snippet": "Crude traders tied the move to inflation expectations.",
                "source_role": "baseline_headline",
                "source_authority": "medium",
                "content_level": "headline+summary",
                "agenda_links": [],
                "detected_keywords": ["oil", "fed"],
            },
        ]
        (self.day_dir / "headline-river.json").write_text(json.dumps(headline_river), encoding="utf-8")
        original_processed = market_radar.PROCESSED_DIR
        original_gather = market_radar.gather_materials
        original_extra_x = market_radar.load_extra_x_posts
        market_radar.PROCESSED_DIR = self.processed
        market_radar.gather_materials = lambda *args, **kwargs: []
        market_radar.load_extra_x_posts = lambda *args, **kwargs: []
        try:
            rows = market_radar.build_rows("2026-05-04", 10, 10, 10)
        finally:
            market_radar.PROCESSED_DIR = original_processed
            market_radar.gather_materials = original_gather
            market_radar.load_extra_x_posts = original_extra_x

        summary_row = next(row for row in rows if row["id"] == "headline-summary")
        headline_row = next(row for row in rows if row["id"] == "headline-only")
        self.assertGreater(summary_row["score"], headline_row["score"])

    def test_market_focus_payload_includes_preflight_and_headline_river(self) -> None:
        original_processed = market_focus.PROCESSED_DIR
        original_raw = market_focus.RAW_DIR
        market_focus.PROCESSED_DIR = self.processed
        market_focus.RAW_DIR = self.raw
        try:
            payload = market_focus.build_input_payload("2026-05-04", max_candidates=10, max_raw_files=0, max_assets=0)
        finally:
            market_focus.PROCESSED_DIR = original_processed
            market_focus.RAW_DIR = original_raw

        self.assertEqual("Oil and Fed path are the morning hypotheses.", payload["market_preflight_agenda"]["preflight_summary"])
        self.assertEqual(2, payload["headline_river"]["item_count"])
        self.assertEqual(1, payload["analysis_river"]["item_count"])
        self.assertEqual("agenda_oil_risk", payload["headline_river"]["agenda_expansions"][0]["agenda_id"])
        self.assertEqual("Finviz News", payload["headline_river"]["sample_items"][0]["source_label"])
        self.assertEqual("Kobeissi Letter", payload["analysis_river"]["sample_items"][0]["source_label"])

    def test_editorial_payload_includes_preflight_and_headline_river_context(self) -> None:
        original_processed = editorial.PROCESSED_DIR
        original_runtime = editorial.RUNTIME_DIR
        editorial.PROCESSED_DIR = self.processed
        editorial.RUNTIME_DIR = self.runtime
        try:
            payload = editorial.build_input_payload("2026-05-04", max_candidates=10)
        finally:
            editorial.PROCESSED_DIR = original_processed
            editorial.RUNTIME_DIR = original_runtime

        self.assertEqual("Oil and Fed path are the morning hypotheses.", payload["market_preflight_agenda"]["preflight_summary"])
        self.assertEqual(2, payload["headline_river"]["item_count"])
        self.assertEqual(1, payload["analysis_river"]["item_count"])
        self.assertEqual("oil", payload["headline_river"]["anomaly_summary"]["top_keywords"][0]["keyword"])
        self.assertEqual("market_attention", payload["analysis_river"]["role_counts"][0]["role"])


if __name__ == "__main__":
    unittest.main()
