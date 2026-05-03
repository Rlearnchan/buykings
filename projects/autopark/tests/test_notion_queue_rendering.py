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
        self.assertIn("차트는 반응 확인용", rendered)
        self.assertIn("| 슬라이드 | 제목 | 자료 | 상태 | 작업 |", rendered)
        self.assertIn("| 0 | 타이틀 |", rendered)
        self.assertIn("| 1 | 시장은 지금 |", rendered)

    def test_compact_host_view_keeps_0421_shape_without_internal_labels(self) -> None:
        brief = {
            "daily_thesis": "실적은 좋은데, 금리가 발목을 잡는다",
            "editorial_summary": "지수는 쉬고 금리와 달러는 부담이다. AI 인프라 수요는 살아 있다. 유가는 보조 리스크다.",
            "ppt_asset_queue": [
                {
                    "asset_id": "storyline-1:10y",
                    "storyline_id": "storyline-1",
                    "caption": "10Y yield chart",
                    "visual_asset_role": "rates_chart",
                    "use_as_slide": True,
                    "slide_priority": 1,
                    "why_this_visual": "금리 부담을 보여준다.",
                },
                {
                    "asset_id": "storyline-1:dxy",
                    "storyline_id": "storyline-1",
                    "caption": "DXY chart",
                    "visual_asset_role": "data_chart",
                    "use_as_slide": True,
                    "slide_priority": 2,
                    "why_this_visual": "달러 부담을 보여준다.",
                },
            ],
            "storylines": [
                {
                    "storyline_id": "storyline-1",
                    "rank": 1,
                    "title": "실적은 좋은데, 금리가 발목을 잡는다",
                    "hook": "시장은 오르고 싶지만 금리와 달러가 속도를 제한한다.",
                    "lead_candidate_reason": "첫 5분에 시장 지도와 바로 붙는다.",
                    "why_now": "Fed 발언 이후 금리 재해석이 필요하다.",
                    "signal_or_noise": "signal",
                    "evidence_to_use": [
                        {"item_id": "10y", "evidence_id": "ev-10y", "title": "10Y yield", "evidence_role": "data"},
                        {"item_id": "dxy", "evidence_id": "ev-dxy", "title": "DXY", "evidence_role": "data"},
                    ],
                    "ppt_asset_queue": [
                        {
                            "asset_id": "storyline-1:10y",
                            "storyline_id": "storyline-1",
                            "caption": "10Y yield chart",
                            "visual_asset_role": "rates_chart",
                            "use_as_slide": True,
                            "slide_priority": 1,
                            "why_this_visual": "금리 부담을 보여준다.",
                        }
                    ],
                }
            ],
        }
        lines: list[str] = []
        dashboard.render_compact_host_view(
            lines,
            brief,
            brief["storylines"],
            {},
            brief["daily_thesis"],
            "지수는 쉬고 금리·달러는 부담",
            [],
        )
        rendered = "\n".join(lines)

        self.assertLess(rendered.index("# 오늘 방송 순서"), rendered.index("# 첫 꼭지"))
        self.assertIn("## 오늘의 핵심 관점", rendered)
        self.assertIn("실적은 좋은데, 금리가 발목을 잡는다", rendered)
        self.assertNotIn("리드 후보를 확정합니다", rendered)
        for forbidden in ["source_role", "evidence_role", "drop_code", "supported_by_mixed_evidence"]:
            self.assertNotIn(forbidden, rendered)

    def test_display_title_rewrites_unsupported_openai_claim(self) -> None:
        story = {
            "title": "OpenAI(AI) 숫자가 다시 AI 인프라 기대를 받치는가",
            "evidence_to_use": [
                {"title": "Anthropic cloud demand", "evidence_role": "analysis"},
                {"title": "Microsoft Azure growth", "evidence_role": "data"},
            ],
        }

        self.assertEqual("AI 인프라 수요는 아직 살아 있다", dashboard.story_display_title(story))

    def test_story_public_text_rewrites_oil_and_ai_body_copy(self) -> None:
        oil_story = {
            "title": "이란 뉴스에 되살아난 유가 프리미엄",
            "hook": "이란 관련 헤드라인이 다시 유가 프리미엄을 부각시키고 있습니다.",
            "talk_track": "짧게: 유가에 대한 프리미엄이 부활하는 조짐입니다.",
        }
        ai_story = {
            "title": "OpenAI(AI) 숫자가 다시 AI 인프라 기대를 받치는가",
            "hook": "AI 관련 숫자·거래 소식이 인프라 수요 기대를 지탱하고 있나?",
            "evidence_to_use": [{"title": "Anthropic chip purchase talks", "evidence_role": "fact"}],
        }

        self.assertNotIn("프리미엄", dashboard.story_quote_text(oil_story))
        self.assertNotIn("숫자", dashboard.sanitize_story_public_text(ai_story, ai_story["hook"]))

    def test_sentiment_asset_defaults_to_talk_only_without_exception(self) -> None:
        brief = {
            "storylines": [
                {
                    "storyline_id": "storyline-1",
                    "ppt_asset_queue": [
                        {
                            "asset_id": "x-1",
                            "source_role": "sentiment_probe",
                            "visual_asset_role": "x_post_screenshot",
                            "use_as_slide": True,
                            "caption": "X 반응 캡처",
                            "why_this_visual": "분위기 참고",
                        }
                    ],
                }
            ]
        }

        lines: list[str] = []
        dashboard.render_ppt_asset_queue(lines, brief)
        rendered = "\n".join(lines)

        self.assertNotIn("X 반응 캡처", rendered)
        self.assertIn("X 반응 캡처", "\n".join(dashboard.evidence_title(item, {}) for item in dashboard.flatten_talk_only(brief)))

    def test_talk_only_queue_deduplicates_by_title_prefix(self) -> None:
        brief = {
            "talk_only_queue": [
                {"item_id": "short", "title": "Using AI makes you stupid. We kno…", "evidence_role": "sentiment", "reason": "짧은 제목"},
                {
                    "item_id": "long",
                    "title": "Using AI makes you stupid. We know that. But what if it makes companies stupid too?",
                    "evidence_role": "sentiment",
                    "reason": "긴 제목",
                },
            ]
        }

        rows = dashboard.flatten_talk_only(brief)

        self.assertEqual(1, len(rows))
        self.assertEqual("long", rows[0]["item_id"])


if __name__ == "__main__":
    unittest.main()
