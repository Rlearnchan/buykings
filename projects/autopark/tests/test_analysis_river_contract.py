from __future__ import annotations

import argparse
import json
import shutil
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import collect_analysis_river as analysis_river


class AnalysisRiverContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = PROJECT / ".tmp-tests" / "analysis-river"
        if self.tmp_root.exists():
            shutil.rmtree(self.tmp_root)
        self.processed = self.tmp_root / "processed"
        self.day_dir = self.processed / "2026-05-04"
        self.day_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.tmp_root.exists():
            shutil.rmtree(self.tmp_root)

    def test_source_registry_keeps_analysis_sources_separate_from_news_distribution(self) -> None:
        specs = analysis_river.source_role_specs(PROJECT / "config" / "source_roles_v2.yml")

        self.assertIn("x-kobeissiletter", specs)
        self.assertIn("x-wallstengine", specs)
        self.assertIn("isabelnet", specs)
        self.assertIn("factset-insight", specs)
        self.assertNotIn("x-reuters", specs)
        self.assertNotIn("x-bloomberg", specs)

    def test_build_analysis_river_normalizes_existing_x_posts_without_fetch(self) -> None:
        (self.day_dir / "x-timeline-posts.json").write_text(
            json.dumps(
                {
                    "source_summary": [{"source_id": "x-kobeissiletter", "status": "ok", "post_count": 1}],
                    "posts": [
                        {
                            "source_id": "x-kobeissiletter",
                            "text": "Markets are watching Fed rate expectations and oil together. https:// tinyurl.com/example",
                            "url": "https://x.com/KobeissiLetter/status/1",
                            "created_at": "2026-05-04T01:00:00Z",
                            "image_refs": [{"local_path": "projects/autopark/runtime/assets/chart.png"}],
                        },
                        {
                            "source_id": "x-reuters",
                            "text": "Newswire headline should stay in news distribution, not analysis river.",
                            "url": "https://x.com/Reuters/status/2",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        original_processed = analysis_river.PROCESSED_DIR
        analysis_river.PROCESSED_DIR = self.processed
        try:
            payload = analysis_river.build_analysis_river(
                argparse.Namespace(
                    date="2026-05-04",
                    source_roles=PROJECT / "config" / "source_roles_v2.yml",
                    limit_per_source=10,
                    overall_limit=50,
                    timeout=1,
                    skip_fetch=True,
                )
            )
        finally:
            analysis_river.PROCESSED_DIR = original_processed

        self.assertTrue(payload["ok"])
        self.assertEqual(1, payload["item_count"])
        self.assertEqual("x-kobeissiletter", payload["items"][0]["source_id"])
        self.assertEqual("market_attention", payload["items"][0]["source_role"])
        self.assertEqual("text+image", payload["items"][0]["content_level"])
        self.assertNotIn("tinyurl.com", payload["items"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
