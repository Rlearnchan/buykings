from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT.parents[1]


class HybridPipelineOrderTest(unittest.TestCase):
    def run_dry(self, *args: str) -> dict:
        script = PROJECT / "scripts" / "run_live_dashboard_all_in_one.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--date",
                "2026-05-03",
                "--operation-mode",
                "daily_broadcast",
                "--skip-chrome-launch",
                "--skip-publish",
                "--dry-run",
                *args,
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(result.stdout)

    def test_preflight_runs_before_collection_and_focus(self) -> None:
        payload = self.run_dry()
        planned = payload["planned"]

        self.assertLess(planned.index("build market preflight agenda"), planned.index("collect news batch a/b"))
        self.assertLess(planned.index("collect news batch a/b"), planned.index("collect headline river"))
        self.assertLess(planned.index("collect headline river"), planned.index("build market radar"))
        self.assertLess(planned.index("collect headline river"), planned.index("collect analysis river"))
        self.assertLess(planned.index("collect analysis river"), planned.index("build market radar"))
        self.assertLess(planned.index("build market radar"), planned.index("build evidence microcopy"))
        self.assertLess(planned.index("build market radar"), planned.index("build market focus brief"))
        self.assertLess(planned.index("build market focus brief"), planned.index("build editorial brief"))
        self.assertTrue(payload["editorial"]["preflight_enabled"])
        self.assertEqual("build market preflight agenda", payload["editorial"]["preflight_step"])
        x_command = next(
            command
            for command in payload["browser_commands"]
            if any(str(part).endswith("collect_x_timeline.mjs") for part in command) and "x-timeline" in command
        )
        self.assertIn("--search-fallback", x_command)

    def test_skip_preflight_flag_removes_only_preflight_stage(self) -> None:
        payload = self.run_dry("--skip-preflight-agenda")

        self.assertNotIn("build market preflight agenda", payload["planned"])
        self.assertIn("collect headline river", payload["planned"])
        self.assertIn("collect analysis river", payload["planned"])
        self.assertIn("build market focus brief", payload["planned"])
        self.assertFalse(payload["editorial"]["preflight_enabled"])


if __name__ == "__main__":
    unittest.main()
