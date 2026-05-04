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

        self.assertEqual("fallback_headline", roles["finviz-news"].role)
        self.assertEqual("agenda_deepening", roles["yahoo-finance-ticker-rss"].role)
        self.assertEqual("anomaly_detector", roles["biztoc-api"].role)
        self.assertEqual("anomaly_detector", roles["biztoc-feed"].role)
        self.assertEqual("anomaly_detector", roles["biztoc-home"].role)
        self.assertEqual("support_context", roles["cnbc-world"].role)
        self.assertEqual("support_context", roles["tradingview-news"].role)
        self.assertEqual("news_distribution", roles["x-reuters"].role)
        self.assertEqual("news_distribution", roles["x-marketwatch"].role)

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

        self.assertEqual(headline_river.BASELINE_SOURCE_IDS, ["yahoo-finance-ticker-rss"])
        self.assertIn("finviz-news", headline_river.FALLBACK_SOURCE_IDS)
        self.assertIn("x-reuters", headline_river.HEADLINE_X_SOURCE_IDS)
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

    def test_html_parser_filters_low_signal_navigation_links(self) -> None:
        source = headline_river.SourceSpec(
            source_id="biztoc-home",
            label="BizToc Home",
            url="https://biztoc.com/",
            collection_method="html",
            role="anomaly_detector",
            authority="medium_low",
            collection_ease="medium",
            always_collect=True,
        )
        page = """
        <html><body>
          <a href="/settings">Dark mode settings</a>
          <a href="/upgrade">Customize news grid</a>
          <a href="/story/markets-ai">AI capex worries return as traders watch big tech earnings</a>
        </body></html>
        """

        items = headline_river.parse_html_items(source, page, "2026-05-04T05:30:00+09:00")

        self.assertEqual(1, len(items))
        self.assertEqual("AI capex worries return as traders watch big tech earnings", items[0].title)

    def test_html_parser_filters_quote_and_section_links(self) -> None:
        biztoc = headline_river.SourceSpec(
            source_id="biztoc-home",
            label="BizToc Home",
            url="https://biztoc.com/",
            collection_method="html",
            role="anomaly_detector",
            authority="medium_low",
            collection_ease="medium",
            always_collect=True,
        )
        cnbc = headline_river.SourceSpec(
            source_id="cnbc-world",
            label="CNBC World",
            url="https://www.cnbc.com/world/",
            collection_method="html",
            role="support_context",
            authority="medium",
            collection_ease="medium",
            always_collect=False,
        )

        biztoc_items = headline_river.parse_html_items(
            biztoc,
            '<a href="https://finance.yahoo.com/quote/ES=F/">S&P FUTURES 7,270 0.16% •</a><a href="/story/oil">Oil risk returns as traders watch Hormuz shipping</a>',
            "2026-05-04T05:30:00+09:00",
        )
        cnbc_items = headline_river.parse_html_items(
            cnbc,
            '<a href="/cryptocurrency/">Cryptocurrency</a><a href="/2026/05/04/global-markets-open.html">Global stocks rise as tech rally broadens</a>',
            "2026-05-04T05:30:00+09:00",
        )

        self.assertEqual(["Oil risk returns as traders watch Hormuz shipping"], [item.title for item in biztoc_items])
        self.assertEqual(["Global stocks rise as tech rally broadens"], [item.title for item in cnbc_items])

    def test_balanced_limit_keeps_late_sources_represented(self) -> None:
        source = headline_river.SourceSpec(
            source_id="base",
            label="Base",
            url="https://example.com/",
            collection_method="html",
            role="baseline_headline",
            authority="medium",
            collection_ease="high",
            always_collect=True,
        )
        rows = []
        for source_id in ["a", "b", "c"]:
            spec = headline_river.SourceSpec(**{**source.__dict__, "source_id": source_id})
            for index in range(4):
                rows.append(headline_river.make_item(spec, index + 1, f"{source_id} market headline {index}", f"https://example.com/{source_id}/{index}", "2026-05-04T05:30:00+09:00"))

        limited = headline_river.balanced_limit(rows, 5)

        self.assertEqual(["a", "b", "c", "a", "b"], [item.source_id for item in limited])

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

            def fake_rapidapi(url: str, timeout: int = 30) -> dict:
                return {
                    "items": [
                        {
                            "title": "BizToc API sees market risk headlines cluster around oil",
                            "url": "https://biztoc.com/x/oil-risk",
                            "summary": "Oil and Fed headlines are clustering.",
                        }
                    ]
                }

            headline_river.fetch_text = fake_fetch
            original_rapidapi = headline_river.fetch_rapidapi_json
            headline_river.fetch_rapidapi_json = fake_rapidapi
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
                headline_river.fetch_rapidapi_json = original_rapidapi

            self.assertTrue(payload["ok"])
            self.assertGreaterEqual(payload["item_count"], 3)
            self.assertEqual(headline_river.BASELINE_SOURCE_IDS, payload["baseline_source_ids"])
            self.assertEqual(headline_river.FALLBACK_SOURCE_IDS, payload["fallback_source_ids"])
            self.assertEqual(1, len(payload["agenda_expansions"]))
            self.assertTrue(any(item["source_role"] == "agenda_deepening" for item in payload["items"]))
            self.assertTrue(any(item["source_id"] == "biztoc-api" for item in payload["items"]))
            self.assertIn("anomaly_summary", payload)
        finally:
            if tmp_root.exists():
                shutil.rmtree(tmp_root)


if __name__ == "__main__":
    unittest.main()
