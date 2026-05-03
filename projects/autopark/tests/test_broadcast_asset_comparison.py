from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import compare_dashboard_to_broadcast_assets as asset_compare


class BroadcastAssetComparisonTest(unittest.TestCase):
    def test_storyline_and_ppt_asset_receive_usage_labels(self) -> None:
        brief = {
            "storylines": [
                {
                    "storyline_id": "story-001",
                    "rank": 1,
                    "title": "FOMC rates repricing",
                    "hook": "Markets moved on Treasury yield and FOMC expectations.",
                    "evidence_to_use": [
                        {
                            "item_id": "rate-001",
                            "evidence_id": "rate-001",
                            "title": "10Y Treasury yield",
                            "evidence_role": "data",
                        }
                    ],
                    "ppt_asset_queue": [
                        {
                            "asset_id": "asset-001",
                            "caption": "10Y Treasury yield chart",
                            "visual_asset_role": "rates_chart",
                        }
                    ],
                }
            ]
        }
        ppt_outline = {
            "slides": [
                {
                    "slide_number": 4,
                    "title": "10Y Treasury yield",
                    "text": "FOMC rates repricing chart",
                    "visual_asset_role": "rates_chart",
                }
            ]
        }
        broadcast_outline = {
            "segments": [
                {
                    "timestamp": "0:50",
                    "seconds": 50,
                    "text": "FOMC rates repricing and Treasury yield were the lead topic.",
                    "topic_tags": ["rates_fed"],
                }
            ],
            "topics": [],
        }

        result = asset_compare.compare("2026-04-29", brief, ppt_outline, broadcast_outline, "FOMC rates")

        story = result["storyline_results"][0]
        self.assertIn("used_as_lead", story["labels"])
        self.assertIn("used_as_slide", story["labels"])
        self.assertEqual("used_as_slide", result["asset_results"][0]["label"])


if __name__ == "__main__":
    unittest.main()
