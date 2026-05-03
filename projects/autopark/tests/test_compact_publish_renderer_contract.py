from __future__ import annotations

import json
import re
import shutil
import sys
import unittest
import uuid
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_live_notion_dashboard as dashboard
import build_dashboard_microcopy as microcopy
import build_pipeline_sourcebook as sourcebook
import publish_recon_to_notion as publisher
import review_dashboard_quality as quality


DATE = "2026-05-03"


class CompactPublishRendererContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_root = PROJECT / ".test-runtime" / f"compact-publish-{uuid.uuid4().hex}"
        self.processed = self.runtime_root / "processed"
        self.exports = self.runtime_root / "exports"
        self.prompts = self.runtime_root / "prompts"
        (self.processed / DATE).mkdir(parents=True)
        self.exports.mkdir(parents=True)
        self.prompts.mkdir(parents=True)
        (self.exports / "economic-calendar-us.png").write_text("fake", encoding="utf-8")
        (self.exports / "economic-calendar-global.png").write_text("fake", encoding="utf-8")
        self._dashboard_paths = {
            "PROCESSED_DIR": dashboard.PROCESSED_DIR,
            "EXPORTS_DIR": dashboard.EXPORTS_DIR,
            "screenshots_for": dashboard.screenshots_for,
        }
        self._quality_paths = {
            "PROCESSED_DIR": quality.PROCESSED_DIR,
            "RUNTIME_PROMPT_DIR": quality.RUNTIME_PROMPT_DIR,
        }
        dashboard.PROCESSED_DIR = self.processed
        dashboard.EXPORTS_DIR = self.exports
        dashboard.screenshots_for = self._fake_screenshots_for
        quality.PROCESSED_DIR = self.processed
        quality.RUNTIME_PROMPT_DIR = self.prompts
        self._seed_0503_like_payloads()

    def tearDown(self) -> None:
        for name, value in self._dashboard_paths.items():
            setattr(dashboard, name, value)
        for name, value in self._quality_paths.items():
            setattr(quality, name, value)
        resolved = self.runtime_root.resolve()
        test_root = (PROJECT / ".test-runtime").resolve()
        if test_root in resolved.parents and resolved.exists():
            shutil.rmtree(resolved)

    def _write_json(self, name: str, payload: object) -> None:
        (self.processed / DATE / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fake_screenshots_for(self, target_date: str, *names: str) -> list[str]:
        mapping = {
            "finviz-index-futures-*.png": "index-futures.png",
            "finviz-sp500-heatmap*.png": "sp500-heatmap.png",
            "*russell*heatmap*.png": "russell-heatmap.png",
            "*fedwatch-conditional-probabilities-short-term*.png": "fedwatch-short.png",
            "*fedwatch-conditional-probabilities-long-term*.png": "fedwatch-long.png",
            "*fedwatch*short*.png": "fedwatch-short.png",
            "*fedwatch*long*.png": "fedwatch-long.png",
            "*fear*greed*.png": "fear-greed.png",
            "*earnings-calendar*.jpg": "earnings-calendar.jpg",
            "*earnings-calendar*.png": "earnings-calendar.png",
        }
        hits = []
        for name in names:
            if name in mapping:
                path = self.runtime_root / mapping[name]
                path.write_text("fake", encoding="utf-8")
                hits.append(str(path))
                if name == "finviz-index-futures-*.png":
                    path2 = self.runtime_root / "index-futures-2.png"
                    path2.write_text("fake", encoding="utf-8")
                    hits.append(str(path2))
        return hits

    def _seed_0503_like_payloads(self) -> None:
        self._write_json("live-experiment-pack.json", {"freeze_time": "2026-05-03T10:35:00+09:00"})
        self._write_json(
            "today-misc-batch-a-candidates.json",
            {
                "captured_at": "2026-05-03T09:10:00+09:00",
                "candidates": [
                    {
                        "id": "rates-1",
                        "title": "US Jobs Report to Show Resilience as Fed Officials Keep Inflation Warnings Alive",
                        "source": "Yahoo Finance",
                        "url": "https://example.com/rates-story",
                        "source_role": "speed_anchor",
                        "evidence_role": "news_context",
                        "summary": "Fed 인플레이션 발언과 금리 부담을 확인하는 기사.",
                    },
                    {
                        "id": "oil-1",
                        "title": "Oil Traders Watch Hormuz Tension While Brent Barely Moves",
                        "source": "Reuters",
                        "url": "https://example.com/oil-story",
                        "source_role": "context_anchor",
                        "evidence_role": "price_reaction",
                        "summary": "유가 지정학 헤드라인과 가격 반응을 분리해 보는 기사.",
                    },
                    {
                        "id": "ai-1",
                        "title": "Cloud Giants Increase Data Center Spending for AI Infrastructure Demand",
                        "source": "CNBC",
                        "url": "https://example.com/ai-story",
                        "source_role": "supporting_story",
                        "evidence_role": "company_context",
                        "summary": "AI 인프라 투자 기대를 확인하는 기사.",
                    },
                ],
            },
        )
        self._write_json("today-misc-batch-b-candidates.json", {"captured_at": "2026-05-03T09:25:00+09:00", "candidates": []})
        self._write_json("x-timeline-posts.json", {"captured_at": "2026-05-03T09:35:00+09:00", "posts": []})
        self._write_json("earnings-ticker-drilldown.json", {"items": []})
        self._write_json(
            "finviz-feature-stocks.json",
            {
                "items": [
                    {
                        "ticker": "MSFT",
                        "status": "ok",
                        "url": "https://finviz.com/quote.ashx?t=MSFT",
                        "screenshot_path": str(self.runtime_root / "msft.png"),
                    }
                ]
            },
        )
        self._write_json("economic-calendar.json", {"events": [{"event": "ISM 서비스업"}]})
        self._write_json(
            "market-radar.json",
            {
                "candidates": [
                    {
                        "id": "rates-1",
                        "title": "US Jobs Report to Show Resilience as Fed Officials Keep Inflation Warnings Alive",
                        "source": "Yahoo Finance",
                        "url": "https://example.com/rates-story",
                        "source_role": "speed_anchor",
                        "evidence_role": "news_context",
                    },
                    {
                        "id": "oil-1",
                        "title": "Oil Traders Watch Hormuz Tension While Brent Barely Moves",
                        "source": "Reuters",
                        "url": "https://example.com/oil-story",
                        "source_role": "context_anchor",
                        "evidence_role": "price_reaction",
                    },
                    {
                        "id": "ai-1",
                        "title": "Cloud Giants Increase Data Center Spending for AI Infrastructure Demand",
                        "source": "CNBC",
                        "url": "https://example.com/ai-story",
                        "source_role": "supporting_story",
                        "evidence_role": "company_context",
                    },
                ]
            },
        )
        self._write_json(
            "market-preflight-agenda.json",
            {
                "preflight_summary": "금리, 유가, AI 인프라를 먼저 확인한다.",
                "with_web": False,
                "agenda_items": [
                    {
                        "rank": 1,
                        "agenda_id": "rates-watch",
                        "market_question": "금리 부담이 위험자산을 누르는가",
                        "why_to_check": "방송 첫 프레임 후보.",
                        "collection_targets": [{"target_type": "chart", "query_or_asset": "us10y"}],
                    }
                ],
            },
        )
        self._write_json(
            "market-focus-brief.json",
            {
                "fallback": False,
                "with_web": False,
                "market_focus_summary": "금리와 유가, AI 인프라 기대를 가격 반응 중심으로 묶는다.",
                "what_market_is_watching": [
                    {
                        "rank": 1,
                        "broadcast_use": "lead",
                        "focus": "Fed 발언 이후 금리와 달러 부담을 재확인한다.",
                        "evidence_ids": ["rates-1"],
                        "one_sentence_for_host": "Fed 인플레이션 경계 발언으로 금리·달러 부담이 다시 부각됐다.",
                    },
                    {
                        "rank": 2,
                        "broadcast_use": "supporting_story",
                        "focus": "유가 헤드라인과 가격 반응을 분리한다.",
                        "evidence_ids": ["oil-1"],
                        "one_sentence_for_host": "유가 관련 지정학 헤드라인은 나왔지만 가격 반응은 제한적이었다.",
                    },
                    {
                        "rank": 3,
                        "broadcast_use": "supporting_story",
                        "focus": "AI 인프라 투자 기대를 기술주 보조 소재로 쓴다.",
                        "evidence_ids": ["ai-1"],
                        "one_sentence_for_host": "AI 인프라 수요 뉴스는 기술주 보조 소재로 활용 가능하다.",
                    },
                ],
                "suggested_broadcast_order": [],
                "source_gaps": [{"issue": "개별 기업 실적 반응은 추가 확인 필요", "search_hint": "FactSet earnings season"}],
            },
        )
        self._write_json(
            "editorial-brief.json",
            {
                "fallback": False,
                "daily_thesis": "가격 반응이 말해주는 것은 금리 부담과 유가 둔감함의 동시 존재다.",
                "market_map_summary": "지수는 버티지만 금리와 달러가 속도를 제한한다.",
                "storylines": [
                    {
                        "rank": 1,
                        "recommendation_stars": 3,
                        "title": "Fed 이후 금리 부담을 다시 본다",
                        "hook": "금리와 달러가 위험자산 반등의 속도를 다시 제한하는지 확인한다.",
                        "evidence_to_use": [{"item_id": "rates-1", "title": "US Jobs Report to Show Resilience as Fed Officials Keep Inflation Warnings Alive"}],
                        "ppt_asset_queue": [{"public_material_label": "10년물 금리 차트"}, {"public_material_label": "달러인덱스 차트"}],
                    },
                    {
                        "rank": 2,
                        "recommendation_stars": 2,
                        "title": "유가는 뉴스보다 가격 반응이 약하다",
                        "hook": "지정학 헤드라인과 실제 유가 반응이 같은 방향인지 분리해 본다.",
                        "evidence_to_use": [{"item_id": "oil-1", "title": "Oil Traders Watch Hormuz Tension While Brent Barely Moves"}],
                        "ppt_asset_queue": [{"public_material_label": "유가 실질가격 차트"}, {"public_material_label": "WTI·브렌트 가격 차트"}],
                    },
                    {
                        "rank": 3,
                        "recommendation_stars": 1,
                        "title": "AI 인프라 기대는 기술주 보조 소재다",
                        "hook": "AI 투자 기대가 실적과 주가 반응으로 이어지는지 확인한다.",
                        "evidence_to_use": [{"item_id": "ai-1", "title": "Cloud Giants Increase Data Center Spending for AI Infrastructure Demand"}],
                        "ppt_asset_queue": [{"public_material_label": "AI 인프라 투자 기사"}, {"public_material_label": "한국 반도체 연결 기사"}],
                    },
                    {
                        "rank": 4,
                        "recommendation_stars": 1,
                        "title": "상단에 나오면 안 되는 네 번째 스토리",
                        "hook": "이 후보는 자료 수집 또는 debug에만 남아야 한다.",
                        "ppt_asset_queue": [{"public_material_label": "FactSet 실적 시즌 요약"}],
                    },
                ],
            },
        )

    def test_render_dashboard_matches_compact_golden_structure(self) -> None:
        markdown = dashboard.render_dashboard(DATE)
        lines = markdown.splitlines()
        self.assertRegex(lines[0], r"^문서 생성: `\d{2}\.\d{2}\.\d{2} \d{2}:\d{2} \(KST\)`$")
        self.assertRegex(lines[1], r"^자료 수집: `[^`]+ \(KST\)`$")
        self.assertEqual("시장 차트: `26.05.03 미국장 종가 기준`", lines[2])

        top = [title for level, title in quality.heading_lines(markdown) if level == 1]
        self.assertEqual(["🎥 진행자용 요약", "🤖 자료 수집"], top)
        host = quality.compact_host_area(markdown)
        self.assertLessEqual(len([line for line in host.splitlines() if line.strip()]), 55)
        host_h2 = [title for level, title in quality.heading_lines(host) if level == 2]
        self.assertEqual(["주요 뉴스", "방송 순서", "스토리라인"], host_h2)
        self.assertEqual(3, quality.compact_bullet_count(quality.compact_section_body(host, "주요 뉴스")))
        self.assertEqual(5, quality.compact_bullet_count(quality.compact_section_body(host, "방송 순서")))

        story_blocks = quality.compact_story_blocks(host)
        self.assertEqual(3, len(story_blocks))
        for block in story_blocks:
            self.assertEqual(1, len(re.findall(r"^추천도:\s+`(?:★★★|★★☆|★☆☆)`$", block, flags=re.M)))
            quotes = re.findall(r"^>\s+(.+)$", block, flags=re.M)
            self.assertEqual(1, len(quotes))
            self.assertTrue(all(len(quote) <= 180 for quote in quotes))
            self.assertEqual(1, block.count("**왜 중요한가**"))
            why_body = block.split("**왜 중요한가**", 1)[1].split("**슬라이드 구성:**", 1)[0]
            why_bullets = re.findall(r"^-\s+(.+)$", why_body, flags=re.M)
            self.assertGreaterEqual(len(why_bullets), 2)
            self.assertLessEqual(len(why_bullets), 3)
            self.assertTrue(all(len(bullet) <= 90 for bullet in why_bullets))
            self.assertTrue(quality.compact_host_relevance_complete(why_bullets))
            self.assertEqual(1, len(re.findall(r"^\*\*슬라이드 구성:\*\*\s+`[①②③④⑤⑥⑦⑧⑨⑩]", block, flags=re.M)))

        for forbidden in quality.COMPACT_HOST_FORBIDDEN:
            self.assertNotIn(forbidden, host)
        self.assertNotIn("US Jobs Report to Show Resilience", host)
        self.assertNotIn("상단에 나오면 안 되는 네 번째", host)
        self.assertIn("Fed 인플레이션 발언 기사", host)
        news_bullets = re.findall(r"^-\s+(.+)$", quality.compact_section_body(host, "주요 뉴스"), flags=re.M)
        self.assertEqual(3, len(news_bullets))
        self.assertTrue(all(len(bullet) <= 80 for bullet in news_bullets))
        slide_lines = re.findall(r"^\*\*슬라이드 구성:\*\*\s+(.+)$", quality.compact_section_body(host, "스토리라인"), flags=re.M)
        self.assertTrue(any(re.search(r"`[①②③④⑤⑥⑦⑧⑨⑩] .+`", label) for label in slide_lines))
        bare_story_label_lines = [
            label.strip()
            for slide_line in slide_lines
            for _, label in re.findall(r"`([①②③④⑤⑥⑦⑧⑨⑩]|\(\d+\))\s+([^`]+)`", slide_line)
        ]
        self.assertLessEqual(bare_story_label_lines.count("WTI·브렌트 가격 차트"), 1)

        collection = quality.compact_collection_area(markdown)
        for forbidden in ["source_role", "evidence_role", "item_id", "evidence_id", "MF-", "원문 제목"]:
            self.assertNotIn(forbidden, markdown)
        self.assertEqual(["1. 시장은 지금", "2. 미디어 포커스", "3. 실적/특징주"], quality.compact_collection_sections(collection))
        labels = quality.compact_collection_labels(collection)
        self.assertLess(labels.index("주요 지수 흐름"), labels.index("10년물 국채금리"))
        self.assertNotIn("주요 지수 흐름 2", labels)
        self.assertLess(labels.index("S&P500 히트맵"), labels.index("WTI 가격 차트"))
        self.assertLess(labels.index("WTI 가격 차트"), labels.index("브렌트 가격 차트"))
        self.assertIn("원/달러 환율 차트", labels)
        self.assertIn("FedWatch", labels)
        self.assertIn("오늘의 경제지표", labels)
        self.assertNotIn("FedWatch 단기 금리 확률", labels)
        self.assertNotIn("FedWatch 장기 금리 확률", labels)
        self.assertEqual(labels.index("FedWatch") + 1, labels.index("오늘의 경제지표"))
        self.assertNotIn("10년물 금리 차트", labels)
        self.assertEqual(len(labels), len(set(labels)))
        bare_labels = [quality.strip_public_label_marker(label) for label in labels]
        for label in bare_story_label_lines:
            self.assertIn(label, bare_labels)
        market_body = quality.compact_collection_section_body(collection, "1. 시장은 지금")
        self.assertNotIn("요약:", market_body)
        self.assertNotIn("원문 제목:", market_body)
        market_blocks = {quality.card_title(block): block for block in quality.compact_card_blocks(market_body)}
        self.assertEqual(2, quality.image_count(market_blocks["주요 지수 흐름"]))
        self.assertEqual(2, quality.image_count(market_blocks["FedWatch"]))
        self.assertEqual(2, quality.image_count(market_blocks["오늘의 경제지표"]))
        media_body = quality.compact_collection_section_body(collection, "2. 미디어 포커스")
        media_blocks = quality.compact_card_blocks(media_body)
        self.assertNotIn("- 출처: Autopark", media_body)
        self.assertNotIn("- 출처: Market Focus", media_body)
        self.assertNotIn("- 출처: Pre-flight Agenda", media_body)
        self.assertNotIn("실적·경제일정 표", media_body)
        self.assertTrue(all(re.match(r"^### [①②③④⑤⑥⑦⑧⑨⑩]", block.splitlines()[0]) for block in media_blocks[:3]))
        for block in media_blocks:
            self.assertIn("- 출처:", block)
            self.assertIn("- 수집 시점:", block)
            self.assertIn("- 내용:", block)
            bullets = re.findall(r"^\s{2}-\s+(.+)$", block.split("- 내용:", 1)[1], flags=re.M)
            self.assertGreaterEqual(len(bullets), 1)
            self.assertLessEqual(len(bullets), 3)
            self.assertTrue(all(len(bullet) <= 90 for bullet in bullets))
        self.assertIn("https://example.com/rates-story", collection)
        feature_body = quality.compact_collection_section_body(collection, "3. 실적/특징주")
        feature_blocks = quality.compact_card_blocks(feature_body)
        self.assertEqual("실적 캘린더", quality.card_title(feature_blocks[0]))
        self.assertEqual(1, quality.image_count(feature_blocks[0]))
        self.assertIn("### 마이크로소프트 (MSFT)", feature_body)
        self.assertIsNone(re.search(r"^###\s+(?:\d+\.|[①②③④⑤⑥⑦⑧⑨⑩])\s+마이크로소프트", feature_body, flags=re.M))

        findings = quality.review_compact_publish_contract(markdown)
        self.assertEqual([], [finding.title for finding in findings])

    def test_publish_converter_uses_date_title_and_keeps_host_heading(self) -> None:
        markdown = dashboard.render_dashboard(DATE)
        path = self.runtime_root / "26.05.03.md"
        path.write_text(markdown, encoding="utf-8")

        title, blocks = publisher.markdown_to_blocks(markdown, markdown_path=path, upload_images=False)

        self.assertEqual("26.05.03", title)
        self.assertEqual("heading_1", blocks[3]["type"])
        self.assertEqual("🎥 진행자용 요약", blocks[3]["heading_1"]["rich_text"][0]["text"]["content"])

    def test_explicit_chart_id_labels_win_before_axis_fallback(self) -> None:
        self.assertEqual("원/달러 환율 차트", dashboard.public_material_label({"item_id": "usd-krw", "title": "Dollar index pressure"}))
        self.assertEqual("달러인덱스 차트", dashboard.public_material_label({"item_id": "dollar-index", "title": "10Y yield"}))
        self.assertEqual("10년물 국채금리", dashboard.public_material_label({"item_id": "us10y", "title": "USD/KRW"}))

    def test_quality_gate_fails_if_host_exposes_internal_material(self) -> None:
        markdown = dashboard.render_dashboard(DATE)
        broken = markdown.replace("## 주요 뉴스", "## 주요 뉴스\n- MF-77e1c32e https://example.com source_role=speed_anchor", 1)
        findings = quality.review_compact_publish_contract(broken)
        self.assertTrue(any(finding.title.startswith("COMPACT-005") for finding in findings))

    def test_quality_gate_fails_if_why_relevance_lacks_required_axes(self) -> None:
        markdown = dashboard.render_dashboard(DATE)
        broken = re.sub(
            r"(\*\*왜 중요한가\*\*\n)- .+\n- .+\n- .+",
            r"\1- 전날 시장 반응만 확인한다.\n- 가격 반응만 확인한다.",
            markdown,
            count=1,
        )
        findings = quality.review_compact_publish_contract(broken)
        self.assertTrue(any(finding.title.startswith("COMPACT-045") for finding in findings))

    def test_public_material_label_rejects_internal_or_raw_title_labels(self) -> None:
        label = dashboard.public_material_label(
            {
                "public_material_label": "MF-77e1c32e",
                "title": "Yahoo Finance US Jobs Report to Show Resilience as Fed Keeps Inflation Warnings Alive",
                "source_role": "speed_anchor",
                "evidence_role": "news_context",
                "url": "https://example.com/signed/s3/path",
            }
        )

        self.assertLessEqual(len(label), 28)
        self.assertNotIn("MF-", label)
        self.assertNotIn("http", label)
        self.assertNotIn("/", label)
        self.assertNotIn("Yahoo Finance", label)
        self.assertNotRegex(label, r"\b[A-Za-z][A-Za-z0-9&'’.-]*(?:\s+[A-Za-z][A-Za-z0-9&'’.-]*){4,}\b")

    def test_sourcebook_renderer_summary_parses_latest_collection_contract(self) -> None:
        markdown = "\n".join(
            [
                "# 🎥 진행자용 요약",
                "## 스토리라인",
                "- `① WTI·브렌트 가격 차트`",
                "# 🤖 자료 수집",
                "## 1. 시장은 지금",
                "### 주요 지수 흐름",
                "- 출처: [finviz](https://finviz.com/)",
                "![주요 지수 흐름](a.png)",
                "![주요 지수 흐름](b.png)",
                "### FedWatch",
                "- 출처: [CME](https://example.com/)",
                "![FedWatch 단기 금리 확률](short.png)",
                "![FedWatch 장기 금리 확률](long.png)",
                "### 오늘의 경제지표",
                "- 출처: [Trading Economics](https://example.com/calendar)",
                "![오늘의 미국 경제지표](us.png)",
                "![오늘의 글로벌 경제지표](global.png)",
                "## 2. 미디어 포커스",
                "### ① WTI·브렌트 가격 차트",
                "- 출처: [IsabelNet](https://example.com/oil)",
                "- 내용:",
                "  - 유가 가격 반응을 확인한다.",
            ]
        )

        story_labels, market_cards, media_cards, forbidden = sourcebook.renderer_summary(markdown)

        self.assertEqual(["① WTI·브렌트 가격 차트"], story_labels)
        self.assertEqual(3, len(market_cards))
        self.assertEqual("주요 지수 흐름", market_cards[0]["label"])
        self.assertEqual(2, market_cards[0]["image_count"])
        self.assertEqual("FedWatch", market_cards[1]["label"])
        self.assertEqual(2, market_cards[1]["image_count"])
        self.assertEqual("오늘의 경제지표", market_cards[2]["label"])
        self.assertEqual(2, market_cards[2]["image_count"])
        self.assertEqual(1, len(media_cards))
        self.assertTrue(media_cards[0]["has_content"])
        self.assertEqual(0, forbidden["source_role"])

    def test_sourcebook_hygiene_gate_flags_sensitive_markers(self) -> None:
        path = self.runtime_root / "bad-sourcebook.md"
        path.write_text("OPENAI_API_KEY=sk-test\nhttps://bucket.s3.amazonaws.com/x.png?X-Amz-Signature=abc\n", encoding="utf-8")

        findings = sourcebook.hygiene_findings(path)

        self.assertIn("OPENAI_API_KEY", findings)
        self.assertIn("X-Amz-Signature", findings)

    def test_microcopy_validation_falls_back_per_invalid_item(self) -> None:
        context = {
            "storylines": [
                {
                    "storyline_id": "storyline-1",
                    "axis": "rates",
                    "quote_seed": "금리와 달러 부담을 확인한다.",
                    "slide_line": "`① 10년물 국채금리` → `② 달러인덱스 차트`",
                }
            ],
            "media_focus_cards": [
                {"card_key": "card-1", "label": "10년물 국채금리", "summary": "금리 부담을 확인하는 차트."}
            ],
        }
        fallback = microcopy.deterministic_microcopy(context)
        candidate = {
            "storylines": [
                {
                    "storyline_id": "storyline-1",
                    "quote_lines": ["https://example.com source_role bad"],
                    "host_relevance_bullets": ["하나뿐인 bullet"],
                    "slide_line": "`① 다른 자료`",
                }
            ],
            "media_focus_cards": [{"card_key": "card-1", "content_bullets": ["금리 부담을 90자 이내로 확인한다."]}],
        }

        payload, fallback_count, invalid_count = microcopy.validate_microcopy(candidate, context, fallback)

        self.assertEqual(1, fallback_count)
        self.assertGreaterEqual(invalid_count, 1)
        self.assertEqual(fallback["storylines"][0]["quote_lines"], payload["storylines"][0]["quote_lines"])
        self.assertEqual(["금리 부담을 90자 이내로 확인한다."], payload["media_focus_cards"][0]["content_bullets"])


if __name__ == "__main__":
    unittest.main()
