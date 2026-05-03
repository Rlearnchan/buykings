from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_actual_broadcast_outline as actual_outline
import extract_ppt_outline as ppt_outline


class BroadcastSampleParserTest(unittest.TestCase):
    def test_ppt_title_ignores_buykings_boilerplate(self) -> None:
        title = ppt_outline.choose_title(
            [
                "Economy l Finance l Politics l World",
                "THE BUYKINGS TIMES",
                "Markets now",
                "4월 FOMC",
            ]
        )

        self.assertEqual("Markets now", title)

    def test_ppt_visual_role_classifies_core_market_assets(self) -> None:
        self.assertEqual("rates_chart", ppt_outline.classify_visual_role("10Y Treasury yield", []))
        self.assertEqual("sector_heatmap", ppt_outline.classify_visual_role("S&P500 heatmap", []))
        self.assertEqual("earnings_calendar", ppt_outline.classify_visual_role("earnings calendar", []))

    def test_rtf_unicode_and_timestamp_segments(self) -> None:
        text = actual_outline.rtf_to_text(b"{\\rtf1\\ansi\\ansicpg949 \\uc0\\u48148 \\u51060 \\u53433 \\par 0:48\\par FOMC earnings}")
        self.assertIn("바이킹", text)
        self.assertIn("0:48", text)

        segments = actual_outline.segment_transcript("0:48\n48 seconds\nFOMC earnings start\n1:46\nOil and rates")
        self.assertEqual(["0:48", "1:46"], [segment["timestamp"] for segment in segments])
        self.assertIn("FOMC earnings", segments[0]["text"])


if __name__ == "__main__":
    unittest.main()
