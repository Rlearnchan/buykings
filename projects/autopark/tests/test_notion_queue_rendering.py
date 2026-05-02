from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_live_notion_dashboard as dashboard


class NotionQueueRenderingTest(unittest.TestCase):
    def test_queue_renderers_show_slide_talk_and_drop(self) -> None:
        brief = {
            "ppt_asset_queue": [
                {
                    "asset_id": "storyline-1:chart-1",
                    "source": "Datawrapper",
                    "source_role": "data_anchor",
                    "visual_asset_role": "rates_chart",
                    "storyline_id": "storyline-1",
                    "slide_priority": 1,
                    "use_as_slide": True,
                    "use_as_talk_only": False,
                    "caption": "10년물 금리",
                    "why_this_visual": "금리 부담을 보여준다.",
                    "risks_or_caveats": "원인 확정 근거는 아님",
                }
            ],
            "talk_only_queue": [{"item_id": "x-1", "title": "X 반응", "evidence_role": "sentiment", "reason": "분위기 확인"}],
            "drop_list": [{"item_id": "v-1", "title": "히트맵", "drop_code": "visual_only_not_causality", "reason": "원인 근거 아님"}],
        }
        lines: list[str] = []
        dashboard.render_ppt_asset_queue(lines, brief)
        dashboard.render_talk_only_queue(lines, brief, {})
        dashboard.render_drop_queue(lines, brief, {})
        rendered = "\n".join(lines)

        self.assertIn("10년물 금리", rendered)
        self.assertIn("X 반응", rendered)
        self.assertIn("visual_only_not_causality", rendered)


if __name__ == "__main__":
    unittest.main()
