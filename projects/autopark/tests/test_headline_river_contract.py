from __future__ import annotations

import argparse
import json
import shutil
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import collect_headline_river as headline_river


class HeadlineRiverContractTest(unittest.TestCase):
    def test_source_roles_v2_contains_required_news_roles(self) -> None:
        roles = headline_river.parse_source_roles(PROJECT / "config" / "source_roles_v2.yml")

        self.assertEqual("baseline_headline", roles["finviz-news"].role)
        self.assertEqual("agenda_deepening", roles["yahoo-finance-ticker-rss"].role)
        self.assertEqual("anomaly_detector", roles["biztoc-feed"].role)
        self.assertEqual("anomaly_detector", roles["biztoc-home"].role)
        self.assertEqual("support_context", roles["cnbc-world"].role)
        self.assertEqual("support_context", roles["tradingview-news"].role)

    def test_agenda_expansion_adds_tickers_without_replacing_baseline(self) -> None:
        preflight = {
            "agenda_items": [
                {
                    "rank": 1,
                    "agenda_id": "agenda_rates_dollar",
                    "market_question": "Are rates and dollar pressuring valuation?",
                    "why_to_check": "US10Y and DXY can affect Korea open.",
                },
                {
                    "rank": 2,
                    "agenda_id": "agenda_oil_risk",
                    "market_question": "Is oil moving on Hormuz risk?",
                    "why_to_check": "WTI and Brent affect inflation expectations.",
                },
            ]
        }

        expansions = headline_river.agenda_expansions(preflight)

        self.assertEqual(headline_river.BASELINE_SOURCE_IDS, ["finviz-news", "yahoo-finance-ticker-rss", "biztoc-feed", "biztoc-home"])
        self.assertEqual(2, len(expansions))
        self.assertIn("^TNX", expansions[0]["tickers"])
        self.assertIn("DX-Y.NYB", expansions[0]["tickers"])
        self.assertIn("CL=F", expansions[1]["tickers"])
        self.assertIn("BZ=F", expansions[1]["tickers"])

    def test_rss_parser_keeps_summary_and_agenda_link(self) -> None:
        source = headline_river.SourceSpec(
            source_id="yahoo-agenda-agenda_oil_risk",
            label="Yahoo Agenda RSS: agenda_oil_risk",
            url="https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL%3DF",
            collection_method="rss",
            role="agenda_deepening",
            authority="medium",
            collection_ease="high",
            always_collect=False,
        )
        feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss><channel><item>
          <title>Oil steadies as Hormuz risk stays in focus</title>
          <link>https://finance.yahoo.com/news/oil-steadies-123.html</link>
          <pubDate>Mon, 04 May 2026 04:01:14 +0000</pubDate>
          <description><![CDATA[Crude traders are watching shipping risk.]]></description>
          <source url="https://example.com/">Example Wire</source>
        </item></channel></rss>"""

        items = headline_river.parse_rss_items(source, feed, "2026-05-04T05:30:00+09:00", ["agenda_oil_risk"])

        self.assertEqual(1, len(items))
        self.assertEqual("headline+summary", items[0].content_level)
        self.assertEqual(["agenda_oil_risk"], items[0].agenda_links)
        self.assertEqual("agenda_deepening", items[0].source_role)
        self.assertIn("oil", items[0].detected_keywords)

    def test_build_headline_river_dry_with_stubbed_fetch(self) -> None:
        tmp_root = PROJECT / ".tmp-tests" / "headline-river"
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        try:
            processed = tmp_root / "processed"
            (processed / "2026-05-04").mkdir(parents=True)
            (processed / "2026-05-04" / "market-preflight-agenda.json").write_text(
                json.dumps(
                    {
                        "agenda_items": [
                            {
                                "agenda_id": "agenda_ai_capex",
                                "market_question": "Is AI capex weighing on big tech?",
                                "why_to_check": "AI capex links to semiconductors.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            original_processed = headline_river.PROCESSED_DIR
            original_fetch = headline_river.fetch_text
            headline_river.PROCESSED_DIR = processed

            def fake_fetch(url: str, timeout: int = 30) -> str:
                if "biztoc.com/feed" in url:
                    return """<rss><channel><item><title>Fed and oil headlines repeat across market feeds</title><link>https://biztoc.com/x/fed-oil</link><description>Markets are watching Fed and oil.</description></item></channel></rss>"""
                if "rss" in url or "feeds.finance.yahoo.com" in url or "biztoc.com/feed" in url:
                    return """<rss><channel><item><title>AI chip earnings lift market focus</title><link>https://finance.yahoo.com/news/ai-chip.html</link><description>Semiconductor names are in focus.</description></item></channel></rss>"""
                return """<html><body><a href="https://example.com/news/market">Market breadth improves after tech rally</a></body></html>"""

            headline_river.fetch_text = fake_fetch
            try:
                payload = headline_river.build_headline_river(
                    argparse.Namespace(
                        date="2026-05-04",
                        source_roles=PROJECT / "config" / "source_roles_v2.yml",
                        limit_per_source=10,
                        overall_limit=50,
                        timeout=1,
                        include_support=False,
                        skip_agenda_expansion=False,
                    )
                )
            finally:
                headline_river.PROCESSED_DIR = original_processed
                headline_river.fetch_text = original_fetch

            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["item_count"], 3)
            self.assertEqual(headline_river.BASELINE_SOURCE_IDS, payload["baseline_source_ids"])
            self.assertEqual(1, len(payload["agenda_expansions"]))
            self.assertTrue(any(item["source_role"] == "agenda_deepening" for item in payload["items"]))
            self.assertIn("anomaly_summary", payload)
        finally:
            if tmp_root.exists():
                shutil.rmtree(tmp_root)


if __name__ == "__main__":
    unittest.main()
