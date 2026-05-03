from __future__ import annotations

import json
import sys
import unittest
from unittest import mock
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import review_dashboard_quality as quality


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class DashboardQualityIntegrityTest(unittest.TestCase):
    date = "2026-05-02"

    def fixture_loader(self, radar: dict, brief: dict, visuals: dict):
        def load_json(path: Path):
            if path.name == "market-radar.json":
                return radar, ""
            if path.name == "editorial-brief.json":
                return brief, ""
            if path.name == "visual-cards.json":
                return visuals, ""
            return {}, "missing"

        return load_json

    def test_integrity_gate_flags_social_fact_and_missing_drop_code(self) -> None:
        radar = {
            "candidates": [
                {"id": "x-1", "item_id": "x-1", "title": "X rumor", "source": "X", "url": "https://x.com/post", "type": "x_social", "source_role": "sentiment_probe", "evidence_role": "sentiment"},
                {"id": "fact-1", "item_id": "fact-1", "title": "Reuters fact", "source": "Reuters", "source_role": "fact_anchor", "evidence_role": "fact"},
            ]
        }
        base_story = {
            "storyline_id": "storyline-1",
            "rank": 1,
            "title": "Lead",
            "recommendation_stars": 3,
            "lead_candidate_reason": "시장 설명력과 PPT 후보가 있다.",
            "signal_or_noise": "signal",
            "market_causality": "supported_by_mixed_evidence",
            "expectation_gap": "not_primary",
            "prepricing_risk": "low",
            "first_5min_fit": "high",
            "korea_open_relevance": "medium",
            "hook": "hook",
            "why_now": "why",
            "core_argument": "argument",
            "talk_track": "talk",
            "ppt_asset_queue": [{"asset_id": "a1", "use_as_slide": True, "use_as_talk_only": False}],
            "evidence_to_use": [{"item_id": "x-1", "evidence_id": "x-1", "title": "X rumor", "source_role": "sentiment_probe", "evidence_role": "fact", "reason": "bad fact"}],
            "evidence_to_drop": [{"item_id": "fact-1", "evidence_id": "fact-1", "title": "Reuters fact", "reason": "missing drop code"}],
        }
        brief = {
            "daily_thesis": "오늘의 한 줄",
            "market_map_summary": "시장 지도",
            "ppt_asset_queue": [],
            "storylines": [
                base_story,
                {**base_story, "storyline_id": "storyline-2", "rank": 2, "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "title": "Reuters fact", "source_role": "fact_anchor", "evidence_role": "fact", "reason": "ok"}]},
                {**base_story, "storyline_id": "storyline-3", "rank": 3, "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "title": "Reuters fact", "source_role": "fact_anchor", "evidence_role": "fact", "reason": "ok"}]},
            ],
        }

        with mock.patch.object(quality, "load_json", side_effect=self.fixture_loader(radar, brief, {"cards": []})):
            findings = quality.review_integrity(self.date, "# PPT 제작 큐\n| 슬라이드 | 제목 | 자료 | 상태 | 작업 |\n|---:|---|---|---|---|\n| 0 | 타이틀 | Lead | 초안 완료 | 표지 |\n\n## 말로만 처리할 자료\n")
        titles = {item.title for item in findings}

        self.assertIn("INT-004 X/Reddit 단독 fact 근거", titles)
        self.assertIn("INT-006 drop_code 없음", titles)

    def test_integrity_gate_accepts_required_queue_sections(self) -> None:
        radar = {"candidates": [{"id": "fact-1", "item_id": "fact-1", "source_role": "fact_anchor", "evidence_role": "fact"}]}
        story = {
            "storyline_id": "storyline-1",
            "rank": 1,
            "title": "Lead",
            "lead_candidate_reason": "첫 꼭지 이유",
            "signal_or_noise": "signal",
            "market_causality": "supported_by_mixed_evidence",
            "expectation_gap": "explicit",
            "prepricing_risk": "checked",
            "first_5min_fit": "high",
            "core_argument": "short",
            "talk_track": "short",
            "ppt_asset_queue": [{"asset_id": "a1", "use_as_slide": True, "use_as_talk_only": False}],
            "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "source_role": "fact_anchor", "evidence_role": "fact"}],
            "evidence_to_drop": [{"item_id": "fact-1", "evidence_id": "fact-1", "drop_code": "support_only"}],
        }
        brief = {
            "daily_thesis": "x",
            "market_map_summary": "m",
            "ppt_asset_queue": [{"asset_id": "a1"}],
            "storylines": [{**story, "rank": index, "storyline_id": f"storyline-{index}"} for index in range(1, 4)],
        }

        with mock.patch.object(quality, "load_json", side_effect=self.fixture_loader(radar, brief, {"cards": []})):
            findings = quality.review_integrity(self.date, "# PPT 제작 큐\n| 슬라이드 | 제목 | 자료 | 상태 | 작업 |\n|---:|---|---|---|---|\n| 0 | 타이틀 | Lead | 초안 완료 | 표지 |\n| 1 | 시장은 지금 | 주요 지수 | 확인 완료 | 지도 |\n| 4 | 10년물 금리 | 10Y | 확인 완료 | 확인 |\n| 5 | 유가 | WTI | 확인 완료 | 확인 |\n| 6 | 달러/원달러 | DXY | 확인 완료 | 확인 |\n| 8 | 리드 | Fact | 후보 있음 | 확인 |\n\n## 말로만 처리할 자료\n")

        blocked = [item for item in findings if item.title in {"INT-001 lead storyline 없음", "INT-005 evidence id 참조 오류"}]
        self.assertEqual([], blocked)

    def test_integrity_gate_blocks_internal_labels_in_public_view_only(self) -> None:
        radar = {"candidates": [{"id": "fact-1", "item_id": "fact-1", "source_role": "fact_anchor", "evidence_role": "fact"}]}
        story = {
            "storyline_id": "storyline-1",
            "rank": 1,
            "title": "Lead",
            "lead_candidate_reason": "첫 꼭지 이유",
            "signal_or_noise": "signal",
            "ppt_asset_queue": [{"asset_id": "a1", "use_as_slide": True}],
            "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "evidence_role": "fact"}],
        }
        brief = {"daily_thesis": "x", "market_map_summary": "m", "ppt_asset_queue": [{"asset_id": "a1"}], "storylines": [story]}
        markdown = "\n".join(
            [
                "# PPT 제작 큐",
                "| 슬라이드 | 제목 | 자료 | 상태 | 작업 |",
                "|---:|---|---|---|---|",
                "| 0 | 타이틀 | Lead | 초안 완료 | 표지 |",
                "| 1 | 시장은 지금 | 주요 지수 | 확인 완료 | 지도 |",
                "| 4 | 10년물 금리 | 10Y | 확인 완료 | 확인 |",
                "| 5 | 유가 | WTI | 확인 완료 | 확인 |",
                "| 6 | 달러/원달러 | DXY | 확인 완료 | 확인 |",
                "| 8 | 리드 | Fact | 후보 있음 | 확인 |",
                "supported_by_mixed_evidence",
                "## 말로만 처리할 자료",
                "# 검증 로그/회고용",
                "drop_code=`support_only`",
            ]
        )

        with mock.patch.object(quality, "load_json", side_effect=self.fixture_loader(radar, brief, {"cards": []})):
            findings = quality.review_integrity(self.date, markdown)

        self.assertIn("PUBLIC-001 내부 라벨 public 노출", {item.title for item in findings})

    def test_integrity_gate_requires_lead_numbers_for_rates_axis(self) -> None:
        radar = {"candidates": [{"id": "fact-1", "item_id": "fact-1", "source_role": "fact_anchor", "evidence_role": "fact"}]}
        story = {
            "storyline_id": "storyline-1",
            "rank": 1,
            "title": "Fed rates and dollar lead",
            "lead_candidate_reason": "금리와 달러가 오늘 시장을 설명한다.",
            "signal_or_noise": "signal",
            "ppt_asset_queue": [{"asset_id": "a1", "caption": "10Y yield", "use_as_slide": True}],
            "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "title": "Fed comments", "evidence_role": "fact"}],
        }
        brief = {"daily_thesis": "x", "market_map_summary": "m", "ppt_asset_queue": [{"asset_id": "a1"}], "storylines": [story]}
        markdown = "# PPT 제작 큐\n| 슬라이드 | 제목 | 자료 | 상태 | 작업 |\n|---:|---|---|---|---|\n| 0 | 타이틀 | Lead | 초안 완료 | 표지 |\n| 1 | 시장은 지금 | 주요 지수 | 확인 완료 | 지도 |\n| 8 | 리드 | 10Y yield | 후보 있음 | 확인 |\n\n## 말로만 처리할 자료\n"

        with mock.patch.object(quality, "load_json", side_effect=self.fixture_loader(radar, brief, {"cards": []})):
            findings = quality.review_integrity(self.date, markdown)

        self.assertIn("LEAD-ASSET-001 lead 필수 숫자/차트 부족", {item.title for item in findings})

    def test_integrity_gate_blocks_unknown_error_in_public(self) -> None:
        radar = {"candidates": [{"id": "fact-1", "item_id": "fact-1", "source_role": "fact_anchor", "evidence_role": "fact"}]}
        story = {
            "storyline_id": "storyline-1",
            "rank": 1,
            "title": "Lead",
            "lead_candidate_reason": "첫 꼭지 이유",
            "signal_or_noise": "signal",
            "ppt_asset_queue": [{"asset_id": "a1", "use_as_slide": True}],
            "evidence_to_use": [{"item_id": "fact-1", "evidence_id": "fact-1", "evidence_role": "fact"}],
        }
        brief = {"daily_thesis": "x", "market_map_summary": "m", "ppt_asset_queue": [{"asset_id": "a1"}], "storylines": [story]}
        markdown = "# PPT 제작 큐\n| 슬라이드 | 제목 | 자료 | 상태 | 작업 |\n|---:|---|---|---|---|\n| 0 | 타이틀 | Unknown Error | 초안 완료 | 표지 |\n\n## 말로만 처리할 자료\n"

        with mock.patch.object(quality, "load_json", side_effect=self.fixture_loader(radar, brief, {"cards": []})):
            findings = quality.review_integrity(self.date, markdown)

        self.assertIn("RENDER-001 public 렌더링 실패 문구 노출", {item.title for item in findings})


if __name__ == "__main__":
    unittest.main()
