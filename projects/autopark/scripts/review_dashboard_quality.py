#!/usr/bin/env python3
"""Review an Autopark Notion dashboard against 0421 format and PPT narrative rules."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
RUNTIME_REVIEW_DIR = PROJECT_ROOT / "runtime" / "reviews"


@dataclass
class Finding:
    category: str
    severity: str
    title: str
    detail: str
    recommendation: str


def display_date_title(target_date: str) -> str:
    return datetime.fromisoformat(target_date).strftime("%y.%m.%d")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def heading_lines(markdown: str) -> list[tuple[int, str]]:
    rows = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            rows.append((len(match.group(1)), match.group(2)))
    return rows


def has_heading(markdown: str, pattern: str) -> bool:
    return any(re.search(pattern, title, re.I) for _, title in heading_lines(markdown))


def section(markdown: str, title_pattern: str) -> str:
    lines = markdown.splitlines()
    start = None
    start_level = None
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match and re.search(title_pattern, match.group(2), re.I):
            start = index + 1
            start_level = len(match.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", lines[index])
        if match and len(match.group(1)) <= (start_level or 1):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def source_url_count(markdown: str) -> int:
    return len(re.findall(r"(?<!\]\()https?://\S+", markdown))


def image_count(markdown: str) -> int:
    return len(re.findall(r"!\[[^\]]*]\([^)]+\)", markdown))


def table_count(markdown: str) -> int:
    return len(re.findall(r"^\|.+\|\n\|[-:| ]+\|", markdown, flags=re.M))


def issue(findings: list[Finding], category: str, severity: str, title: str, detail: str, recommendation: str) -> None:
    findings.append(Finding(category, severity, title, detail, recommendation))


def load_json(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except json.JSONDecodeError as exc:
        return {}, f"json_parse_error: {exc}"


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def item_ids(payload: dict) -> set[str]:
    return {
        str(value)
        for item in payload.get("candidates") or []
        for value in [item.get("id"), item.get("item_id")]
        if value
    }


def candidate_map(payload: dict) -> dict[str, dict]:
    rows = {}
    for item in payload.get("candidates") or []:
        for key in [item.get("id"), item.get("item_id")]:
            if key:
                rows[str(key)] = item
    return rows


def evidence_roles(story: dict, candidates: dict[str, dict]) -> list[str]:
    roles = []
    for item in story.get("evidence_to_use") or []:
        row = candidates.get(str(item.get("item_id") or ""))
        roles.append(item.get("evidence_role") or (row or {}).get("evidence_role") or "")
    return [role for role in roles if role]


def needs_expectation_check(story: dict) -> bool:
    blob = normalize(" ".join(str(story.get(key) or "") for key in ["title", "hook", "why_now", "core_argument"])).lower()
    return bool(re.search(r"earnings|eps|revenue|guidance|forecast|fed|fomc|inflation|pce|jobs|실적|가이던스|예상|연준|금리|물가", blob))


PUBLIC_FORBIDDEN_LABELS = [
    "supported_by_mixed_evidence",
    "check_market_pricing",
    "visual_only_not_causality",
    "sentiment_only_not_fact",
    "fact_anchor",
    "analysis_anchor",
    "market_reaction",
    "source_role",
    "evidence_role",
    "drop_code",
    "item_id",
    "evidence_id",
    "visual_asset_role",
]


LEAD_REQUIREMENTS = [
    {
        "axis": "rates_macro",
        "label": "금리·달러",
        "axis_patterns": [r"\brate", r"\brates", r"\bfed\b", r"\bfomc\b", r"\bdxy\b", r"\bdollar", r"금리", r"달러", r"연준"],
        "required": {
            "10Y": [r"\b10y\b", r"10-year", r"10년", r"treasury", r"국채"],
            "DXY/달러": [r"\bdxy\b", r"dollar", r"달러", r"원달러"],
            "TLT": [r"\btlt\b"],
            "나스닥/성장주 반응": [r"nasdaq", r"qqq", r"growth", r"duration", r"나스닥", r"성장주"],
        },
        "minimum": 2,
    },
    {
        "axis": "oil",
        "label": "유가",
        "axis_patterns": [r"\boil\b", r"\bwti\b", r"brent", r"crude", r"opec", r"hormuz", r"유가", r"원유", r"호르무즈"],
        "required": {
            "WTI": [r"\bwti\b", r"crude", r"원유"],
            "Brent": [r"brent", r"브렌트"],
            "XLE/에너지주": [r"\bxle\b", r"energy", r"에너지", r"xom", r"cvx"],
            "OPEC/EIA/호르무즈": [r"opec", r"eia", r"hormuz", r"inventory", r"호르무즈", r"재고"],
        },
        "minimum": 2,
    },
    {
        "axis": "earnings",
        "label": "실적",
        "axis_patterns": [r"earnings", r"\beps\b", r"revenue", r"guidance", r"실적", r"가이던스", r"매출"],
        "required": {
            "EPS": [r"\beps\b", r"주당순이익"],
            "매출": [r"revenue", r"sales", r"매출"],
            "가이던스": [r"guidance", r"outlook", r"forecast", r"가이던스", r"전망"],
            "주가 반응": [r"after[- ]?hours", r"pre[- ]?market", r"reaction", r"shares", r"주가", r"시간외"],
        },
        "minimum": 2,
    },
    {
        "axis": "ai",
        "label": "AI",
        "axis_patterns": [r"\bai\b", r"artificial intelligence", r"capex", r"cloud", r"semiconductor", r"data center", r"인공지능", r"반도체", r"데이터센터"],
        "required": {
            "CapEx": [r"capex", r"capital expenditure", r"투자"],
            "클라우드/매출": [r"cloud", r"revenue", r"sales", r"클라우드", r"매출"],
            "반도체 반응": [r"semiconductor", r"nvidia", r"nvda", r"amd", r"반도체"],
            "데이터센터 수요": [r"data center", r"datacenter", r"데이터센터"],
        },
        "minimum": 2,
    },
]


def match_any(blob: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, blob, flags=re.I) for pattern in patterns)


def story_blob(story: dict) -> str:
    parts = [str(story.get(key) or "") for key in ["title", "hook", "lead_candidate_reason", "why_now", "core_argument", "talk_track"]]
    for item in story.get("evidence_to_use") or []:
        parts.extend(str(item.get(key) or "") for key in ["title", "source", "source_role", "evidence_role", "reason"])
    for asset in story.get("ppt_asset_queue") or []:
        parts.extend(str(asset.get(key) or "") for key in ["caption", "visual_asset_role", "why_this_visual", "risks_or_caveats"])
    return normalize(" ".join(parts)).lower()


def story_asset_blob(story: dict) -> str:
    parts = []
    for item in story.get("evidence_to_use") or []:
        parts.extend(str(item.get(key) or "") for key in ["title", "source", "source_role", "evidence_role", "reason"])
    for asset in story.get("ppt_asset_queue") or []:
        parts.extend(str(asset.get(key) or "") for key in ["caption", "visual_asset_role", "why_this_visual", "risks_or_caveats"])
    return normalize(" ".join(parts)).lower()


def confirmed_public_asset_blob(markdown: str) -> str:
    rows = [
        line
        for line in public_markdown(markdown).splitlines()
        if "확인 완료" in line or "후보 있음" in line or "초안 완료" in line
    ]
    return normalize(" ".join(rows)).lower()


def chart_title(chart_id: str) -> str:
    path = PROJECT_ROOT / "charts" / f"{chart_id}-datawrapper.json"
    payload, error = load_json(path)
    if error:
        return ""
    return normalize(payload.get("title"))


def chart_delta_is_negative(chart_id: str) -> bool:
    return bool(re.search(r"\((?:-|−)", chart_title(chart_id)))


def oil_price_reaction_weak() -> bool:
    titles = [chart_title("crude-oil-wti"), chart_title("crude-oil-brent")]
    if not any(titles):
        return False
    return any(chart_delta_is_negative(chart_id) for chart_id in ["crude-oil-wti", "crude-oil-brent"])


def openai_number_supported(story: dict) -> bool:
    blob = story_asset_blob(story)
    if "openai" not in blob.lower():
        return False
    chunks = re.split(r"[.;\n]|(?<=다\.)\s+", blob)
    return any(
        "openai" in chunk.lower()
        and re.search(r"\d|contract|revenue|sales|capex|매출|계약|수주|투자", chunk, flags=re.I)
        for chunk in chunks
    )


def lead_requirement_status(story: dict, extra_asset_blob: str = "") -> dict:
    blob = story_blob(story)
    asset_blob = normalize(f"{story_asset_blob(story)} {extra_asset_blob}").lower()
    for spec in LEAD_REQUIREMENTS:
        if not match_any(blob, spec["axis_patterns"]):
            continue
        present = [label for label, patterns in spec["required"].items() if match_any(asset_blob, patterns)]
        missing = [label for label in spec["required"] if label not in present]
        return {"axis": spec["axis"], "label": spec["label"], "present": present, "missing": missing, "minimum": spec["minimum"], "met": len(present) >= int(spec["minimum"])}
    return {"axis": "", "label": "", "present": [], "missing": [], "minimum": 0, "met": True}


def public_markdown(markdown: str) -> str:
    return re.split(r"^#\s+검증 로그/회고용\s*$", markdown, maxsplit=1, flags=re.M)[0]


def compact_top_markdown(markdown: str) -> str:
    host = section(markdown, r"진행자용 1페이지 요약")
    if host:
        return host
    return re.split(r"^#\s+(?:PPT 제작 큐|자료 수집 상세|📚\s*추천 스토리라인)\s*$", markdown, maxsplit=1, flags=re.M)[0]


def review_integrity(target_date: str, markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    processed = PROCESSED_DIR / target_date
    brief, brief_error = load_json(processed / "editorial-brief.json")
    radar, radar_error = load_json(processed / "market-radar.json")
    visuals, visual_error = load_json(processed / "visual-cards.json")

    for label, error in [("editorial-brief.json", brief_error), ("market-radar.json", radar_error), ("visual-cards.json", visual_error)]:
        if error.startswith("json_parse_error"):
            issue(findings, "integrity", "high", f"INT-000 JSON 파싱 실패: {label}", error, "JSON 산출물이 깨지면 publish 전에 pipeline을 중단하세요.")
    if not brief:
        issue(findings, "integrity", "high", "INT-000 editorial brief 없음", "editorial-brief.json을 읽을 수 없습니다.", "build_editorial_brief.py 결과를 확인하세요.")
        return findings

    stories = brief.get("storylines") or []
    candidates = candidate_map(radar)
    known_ids = item_ids(radar)
    if not known_ids and stories:
        issue(findings, "integrity", "high", "INT-000 후보 id 장부 없음", "market-radar 후보 item_id 장부가 없어 evidence 참조를 검증할 수 없습니다.", "build_market_radar.py 산출물을 확인하세요.")

    lead = next((story for story in stories if int(story.get("rank") or 0) == 1), stories[0] if stories else {})
    if not lead:
        issue(findings, "integrity", "high", "INT-001 lead storyline 없음", "첫 꼭지 후보가 감지되지 않았습니다.", "rank=1 storyline을 만들고 lead_candidate_reason을 채우세요.")
    elif not normalize(lead.get("lead_candidate_reason")):
        issue(findings, "integrity", "high", "INT-002 lead_candidate_reason 없음", "리드 후보에 왜 첫 꼭지인지 설명이 없습니다.", "lead_candidate_reason에 시장 설명력, 첫 5분 이해도, PPT 근거를 적으세요.")
    else:
        lead_status = lead_requirement_status(lead, confirmed_public_asset_blob(markdown))
        if lead_status["axis"] and not lead_status["met"]:
            issue(
                findings,
                "integrity",
                "high",
                "LEAD-ASSET-001 lead 필수 숫자/차트 부족",
                f"리드가 {lead_status['label']} 축인데 필수 숫자/차트가 부족합니다. 현재 확인: {', '.join(lead_status['present']) or '-'} / 부족: {', '.join(lead_status['missing'])}",
                "리드 확정 대신 lead_candidate_pending_numbers로 다루고, 10Y/DXY/TLT 같은 축별 필수 자료를 최소 2개 붙이세요.",
            )

    seen_titles: dict[str, int] = {}
    seen_axes: dict[str, int] = {}
    for index, story in enumerate(stories, start=1):
        title = normalize(story.get("title"))
        title_lower = title.lower()
        public = public_markdown(markdown)
        if "openai" in title_lower and not openai_number_supported(story) and "AI 인프라 수요는 아직 살아 있다" not in public:
            issue(
                findings,
                "integrity",
                "high",
                "LOGIC-001 제목과 근거 클러스터 충돌",
                f"{index}번 스토리라인 제목은 OpenAI 숫자를 암시하지만 OpenAI 전용 숫자/계약 근거가 부족합니다.",
                "display_title은 Anthropic/MS/클라우드/AI 인프라처럼 실제 근거 묶음에서 파생하세요.",
            )
        if any(token in title_lower for token in ["oil", "wti", "brent"]) or "유가" in title:
            if (
                oil_price_reaction_weak()
                and re.search(r"프리미엄|급등|되살아난|rally|surge|spike", title, re.I)
                and "가격 반응은 약하다" not in public
                and "가격 반응과 함께" not in public
            ):
                issue(
                    findings,
                    "integrity",
                    "high",
                    "LOGIC-001 제목과 시장 반응 충돌",
                    f"{index}번 유가 스토리라인 제목은 가격 프리미엄을 암시하지만 WTI/Brent 차트 반응은 약하거나 하락입니다.",
                    "public display_title을 '리스크는 있으나 가격 반응은 약하다'처럼 낮추고 원 제목은 audit에 남기세요.",
                )
        seen_titles[title.lower()] = seen_titles.get(title.lower(), 0) + 1
        axis = normalize(story.get("signal_or_noise") or story.get("core_argument"))[:40].lower()
        if axis:
            seen_axes[axis] = seen_axes.get(axis, 0) + 1
        if not normalize(story.get("signal_or_noise")):
            issue(findings, "integrity", "medium", "INT-003 signal_or_noise 없음", f"{index}번 스토리라인에 signal_or_noise가 없습니다.", "signal/watch/noise 중 하나로 판단을 남기세요.")

        use_items = story.get("evidence_to_use") or []
        drop_items = story.get("evidence_to_drop") or []
        roles = evidence_roles(story, candidates)
        for item in use_items:
            item_id = str(item.get("item_id") or "")
            row = candidates.get(item_id, {})
            source_role = item.get("source_role") or row.get("source_role") or ""
            evidence_role = item.get("evidence_role") or row.get("evidence_role") or ""
            source_blob = normalize(f"{row.get('source')} {row.get('url')} {row.get('type')}").lower()
            is_social = source_role == "sentiment_probe" or "x.com" in source_blob or "reddit" in source_blob or row.get("type") == "x_social"
            if is_social and evidence_role == "fact":
                issue(findings, "integrity", "high", "INT-004 X/Reddit 단독 fact 근거", f"{index}번 스토리라인의 `{item_id}`가 social 자료인데 fact evidence로 쓰였습니다.", "X/Reddit은 sentiment evidence로 낮추고 fact/data/analysis 근거를 추가하세요.")
            if not item_id or item_id not in known_ids or not item.get("evidence_id"):
                issue(findings, "integrity", "high", "INT-005 evidence id 참조 오류", f"{index}번 스토리라인 evidence가 item_id/evidence_id를 제대로 남기지 않았습니다: `{item_id}`", "evidence_to_use에는 당일 후보 item_id와 evidence_id를 모두 남기세요.")
        if roles and set(roles) <= {"sentiment"}:
            issue(findings, "integrity", "high", "INT-004 sentiment-only 스토리라인", f"{index}번 스토리라인이 sentiment evidence만 사용합니다.", "방송용 fact/data/analysis 근거를 하나 이상 붙이거나 drop하세요.")
        for item in drop_items:
            if not normalize(item.get("drop_code")):
                issue(findings, "integrity", "medium", "INT-006 drop_code 없음", f"{index}번 스토리라인의 버릴 자료에 drop_code가 없습니다.", "support_only, sentiment_only_not_fact, visual_only_not_causality 같은 drop_code를 남기세요.")

        assets = story.get("ppt_asset_queue") or []
        if not assets:
            issue(findings, "integrity", "medium", "INT-007 ppt_asset_queue 없음", f"{index}번 스토리라인에 PPT 자료 큐가 없습니다.", "장표 후보가 없으면 talk-only 이유라도 명확히 남기세요.")
        if assets and not any(asset.get("use_as_slide") for asset in assets) and not any(asset.get("use_as_talk_only") for asset in assets):
            issue(findings, "integrity", "medium", "INT-008 slide/talk 구분 없음", f"{index}번 스토리라인의 asset queue가 slide와 talk-only를 구분하지 않습니다.", "use_as_slide 또는 use_as_talk_only를 명확히 채우세요.")
        if roles and set(roles) <= {"visual", "market_reaction"} and "supported" in normalize(story.get("market_causality")).lower():
            issue(findings, "integrity", "high", "INT-009 차트만으로 원인 확정", f"{index}번 스토리라인이 visual/market_reaction만으로 causality를 확정합니다.", "히트맵/차트는 반응으로만 쓰고 fact/data/analysis 근거를 붙이세요.")
        if needs_expectation_check(story):
            if not normalize(story.get("expectation_gap")) or normalize(story.get("expectation_gap")) in {"not_primary", "check_if_relevant"}:
                issue(findings, "integrity", "medium", "INT-010 expectation_gap 부족", f"{index}번 스토리라인은 실적/매크로 기대 비교가 필요합니다.", "절대값보다 예상 대비 결과와 내재 기대를 기록하세요.")
            if not normalize(story.get("prepricing_risk")) or normalize(story.get("prepricing_risk")) in {"low", "check_if_relevant"}:
                issue(findings, "integrity", "medium", "INT-010 prepricing_risk 부족", f"{index}번 스토리라인은 선반영 여부 확인이 필요합니다.", "이미 가격에 반영됐는지와 확인할 차트를 남기세요.")
        if len(normalize(story.get("talk_track"))) > 900 or len(normalize(story.get("core_argument"))) > 650:
            issue(findings, "integrity", "low", "INT-013 너무 긴 요약문", f"{index}번 스토리라인 문장이 방송 큐로 바로 쓰기엔 깁니다.", "핵심 주장과 talk_track을 진행자가 읽을 수 있는 길이로 압축하세요.")
        if not normalize(story.get("storyline_id")) or any(not item.get("evidence_id") for item in use_items):
            issue(findings, "integrity", "medium", "INT-014 회고 식별자 부족", f"{index}번 스토리라인에 회고용 storyline_id/evidence_id가 부족합니다.", "방송 후 비교를 위해 식별자를 유지하세요.")

    duplicate_titles = [title for title, count in seen_titles.items() if title and count > 1]
    duplicate_axes = [axis for axis, count in seen_axes.items() if axis and count > 1]
    if duplicate_titles or duplicate_axes:
        issue(findings, "integrity", "medium", "INT-012 중복 스토리라인 가능성", "동일 제목 또는 같은 축의 스토리라인이 반복됩니다.", "같은 테마는 하나의 강한 꼭지로 합치고 다른 꼭지는 보조 자료로 내리세요.")

    if not normalize(brief.get("market_map_summary")):
        issue(findings, "integrity", "low", "INT-011 시장 지도 요약 없음", "오늘의 한 줄이 시장 지도와 충돌하는지 확인할 요약이 없습니다.", "market_map_summary에 지수/금리/유가/달러/비트코인 반응을 분리해 적으세요.")
    if not (brief.get("ppt_asset_queue") or any(story.get("ppt_asset_queue") for story in stories)):
        issue(findings, "integrity", "medium", "INT-007 전체 PPT 큐 없음", "대시보드 전체에 PPT asset queue가 없습니다.", "상단 PPT 제작 큐 섹션을 채우세요.")
    if "PPT 제작 큐" not in markdown or "말로만 처리할 자료" not in markdown:
        issue(findings, "integrity", "medium", "INT-008 대시보드 queue 섹션 없음", "Markdown에서 PPT 제작 큐와 talk-only 섹션을 찾지 못했습니다.", "Notion renderer에 두 큐 섹션을 유지하세요.")
    public = public_markdown(markdown)
    leaked = [label for label in PUBLIC_FORBIDDEN_LABELS if re.search(rf"\b{re.escape(label)}\b", public)]
    if leaked:
        issue(
            findings,
            "integrity",
            "high",
            "PUBLIC-001 내부 라벨 public 노출",
            "진행자용 public 영역에 내부 enum/ID 라벨이 노출됩니다: " + ", ".join(leaked[:8]),
            "source_role, evidence_role, drop_code, item_id/evidence_id는 하단 `검증 로그/회고용` 섹션으로만 보내고 public 영역은 한국어 표현으로 변환하세요.",
        )
    if re.search(r"\bUnknown Error\b", public, re.I) or "수집 현황 표" in public:
        issue(
            findings,
            "integrity",
            "high",
            "RENDER-001 public 렌더링 실패 문구 노출",
            "진행자용 public 영역에 수집 오류 원문 또는 내부 수집 현황 표가 노출됩니다.",
            "오류 원문과 소스 상태 표는 검증 로그로 내리고 public에는 방송 전 확인 문장만 남기세요.",
        )
    dangling_ellipsis = [
        line.strip()
        for line in public.splitlines()
        if line.strip().startswith(("- ", ">")) and line.strip().endswith("…")
    ]
    if dangling_ellipsis:
        issue(
            findings,
            "integrity",
            "medium",
            "RENDER-001 public 문장 말줄임표 종료",
            "public 문장이 완결되지 않고 말줄임표로 끝납니다: " + dangling_ellipsis[0],
            "진행자용 문장은 clean_complete 계열로 닫고, 기사 제목은 출처/시간/제목으로 분리해 노출하세요.",
        )
    if re.search(r"^\s*(?:리포트|요약하면|후속):", public, re.M):
        issue(
            findings,
            "integrity",
            "medium",
            "HOST-001 리서치 문체 public 노출",
            "짧은 말문 또는 public 본문에 리서치 문서식 접두어가 남아 있습니다.",
            "`리포트:`, `요약하면`, `후속:` 같은 표현은 진행자가 읽는 구어체 문장으로 바꾸세요.",
        )
    compact_top = compact_top_markdown(markdown)
    compact_lines = [line for line in compact_top.splitlines() if line.strip()]
    news_section = section(compact_top, r"주요 뉴스 요약")
    order_section = section(compact_top, r"오늘 방송 순서")
    news_count = len([line for line in news_section.splitlines() if line.strip().startswith("- ")])
    order_count = len(re.findall(r"^\d+\.\s+", order_section, flags=re.M))
    thesis_line = next((line for line in compact_top.splitlines() if line.strip().startswith("- ") and "핵심 관점" not in line), "")
    if len(compact_top) > 1900 or len(compact_lines) > 32 or news_count > 3 or order_count > 5 or len(normalize(thesis_line).lstrip("- ")) > 70:
        issue(
            findings,
            "integrity",
            "medium",
            "HOST-001 진행자용 상단 요약 과다",
            f"추천 스토리라인 전 상단 compact 영역이 너무 깁니다. 문자 {len(compact_top)}, 유효 라인 {len(compact_lines)}.",
            "상단은 오늘의 핵심 관점, 뉴스 3줄, 방송 순서 5줄, 첫 꼭지 체크만 남기고 상세 근거는 하단으로 내리세요.",
        )
    queue_section = section(public, r"PPT 제작 큐")
    if "| 슬라이드 | 제목 | 자료 | 상태 | 작업 |" not in queue_section:
        issue(
            findings,
            "integrity",
            "medium",
            "RENDER-001 PPT 제작 큐 표 누락",
            "PPT 제작 큐가 슬라이드 제작 표로 보이지 않습니다.",
            "`슬라이드 | 제목 | 자료 | 상태 | 작업` 표로 렌더링하세요.",
        )
    for label in ["0", "1", "4", "5", "6", "8"]:
        if label not in queue_section:
            issue(
                findings,
                "integrity",
                "medium",
                "RENDER-001 PPT 제작 순서 누락",
                f"public PPT 큐에서 `{label}` 순서를 찾지 못했습니다.",
                "PPT asset queue를 타이틀, 시장 지도, 10Y, 유가, 달러, 리드 순서가 보이는 표로 묶으세요.",
            )
            break
    if visual_error == "missing" or not visuals:
        issue(findings, "integrity", "low", "visual-cards 없음", "visual-cards.json을 읽지 못했습니다.", "시각 자료 큐 품질은 제한적으로만 검증됩니다.")
    return findings


def storyline_blocks(storyline_section: str) -> list[str]:
    matches = list(re.finditer(r"^#{2,3}\s+\d+\.\s+.+?\s*$", storyline_section, flags=re.M))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(storyline_section)
        blocks.append(storyline_section[match.start() : end].strip())
    return blocks


def review_format(markdown: str, target_date: str) -> list[Finding]:
    findings: list[Finding] = []
    public = public_markdown(markdown)
    expected_title = display_date_title(target_date)
    first_heading = next((title for level, title in heading_lines(markdown) if level == 1), "")

    if first_heading != expected_title:
        issue(
            findings,
            "format",
            "high",
            "날짜 제목 형식 불일치",
            f"첫 H1이 `{first_heading}`입니다. 0421 포맷은 날짜만 쓴 `{expected_title}`입니다.",
            f"첫 줄을 `# {expected_title}`로 맞추세요.",
        )

    for label, pattern in [
        ("문서 생성", r"(?:문서 생성|최종 수정 일시):\s*`?\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}"),
        ("자료 수집", r"(?:자료 수집|수집 구간):\s*`?\d{2}:\d{2}-\d{2}:\d{2}"),
    ]:
        if not re.search(pattern, markdown):
            issue(
                findings,
                "format",
                "medium",
                f"{label} 메타데이터 누락",
                f"`{label}`가 분 단위 KST 형식으로 보이지 않습니다.",
                f"상단에 `{label}: YY.MM.DD HH:MM (KST)` 또는 `수집 구간: HH:MM-HH:MM (KST)`를 넣으세요.",
            )

    required_sections = [
        ("진행자용 1페이지 요약", r"진행자용 1페이지 요약"),
        ("주요 뉴스 요약", r"주요 뉴스 요약"),
        ("PPT 제작 큐", r"PPT 제작 큐"),
        ("추천 스토리라인", r"추천 스토리라인"),
        ("자료 수집 상세", r"자료 수집 상세"),
        ("시장은 지금", r"시장은 지금"),
        ("보조 꼭지 후보", r"보조 꼭지 후보|오늘의 이모저모"),
        ("실적/특징주", r"실적/특징주"),
    ]
    for label, pattern in required_sections:
        if not has_heading(markdown, pattern):
            issue(
                findings,
                "format",
                "high",
                f"필수 섹션 누락: {label}",
                "0421/0422식 대시보드는 앞단 요약과 자료 수집 슬롯이 분리되어야 합니다.",
                f"`{label}` 섹션을 추가하고 관련 자료를 해당 위치로 옮기세요.",
            )

    storyline = section(markdown, r"추천 스토리라인")
    story_count = len(re.findall(r"^#{2,3}\s+\d+\.", storyline, flags=re.M))
    quote_count = len(re.findall(r"^>\s+", storyline, flags=re.M))
    if story_count < 3:
        issue(
            findings,
            "format",
            "high",
            "추천 스토리라인 3개 미만",
            f"현재 감지된 스토리라인은 {story_count}개입니다.",
            "방송 제작자가 고를 수 있도록 서로 다른 각도의 스토리라인 3개를 유지하세요.",
        )
    if quote_count < story_count:
        issue(
            findings,
            "format",
            "medium",
            "스토리라인 quote 부족",
            f"스토리라인 {story_count}개 중 quote는 {quote_count}개입니다.",
            "각 스토리라인 바로 아래에 한 줄 angle을 quote block으로 넣으세요.",
        )
    if "선정 이유" not in storyline and "왜 지금" not in storyline:
        issue(
            findings,
            "format",
            "medium",
            "스토리라인 선정 이유 누락",
            "`추천 스토리라인` 섹션 안에 선정 이유가 보이지 않습니다.",
            "각 스토리라인마다 `선정 이유`와 `슬라이드 구성` 또는 `구성 제안`을 넣으세요.",
        )
    if not re.search(r"슬라이드 구성|구성 제안|^###\s+구성", storyline, flags=re.M):
        issue(
            findings,
            "format",
            "medium",
            "슬라이드 구성 슬롯 누락",
            "스토리라인이 PPT 제작 순서로 바로 이어지기 어렵습니다.",
            "`슬라이드 구성` 또는 `구성 제안` 아래에 자료 순서를 적으세요.",
        )

    public_url_count = source_url_count(public)
    if public_url_count > 0:
        issue(
            findings,
            "format",
            "low",
            "노출 URL 존재",
            f"public 본문에 Markdown 링크가 아닌 원문 URL {public_url_count}개가 노출됩니다.",
            "`[KobeissiLetter](url)`처럼 짧은 출처명 링크로 바꾸세요.",
        )

    if re.search(r"볼 포인트|주요 내용|Finviz 출발점|Finviz 최근 뉴스", markdown):
        issue(
            findings,
            "format",
            "low",
            "래퍼성 불릿 라벨 존재",
            "0421 포맷은 하위 내용을 바로 1-depth 불릿으로 쓰는 쪽이 더 읽기 좋습니다.",
            "`볼 포인트`, `주요 내용`, `Finviz 최근 뉴스` 같은 라벨을 제거하고 내용을 바로 쓰세요.",
        )

    return findings


def review_content_legacy_broad(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    text = markdown.lower()
    market_section = section(markdown, r"시장은 지금").lower()
    misc_section = section(markdown, r"보조 꼭지 후보|오늘의 이모저모")
    feature_section = section(markdown, r"실적/특징주")
    storyline = section(markdown, r"추천 스토리라인")

    fixed_market_checks = [
        ("주요 지수 흐름", [r"주요 지수", r"s&p\s*500.*nasdaq|나스닥|다우"]),
        ("S&P500 히트맵", [r"s&p\s*500.*히트맵", r"heatmap"]),
        ("러셀 2000 히트맵", [r"러셀", r"russell"]),
        ("10년물 국채금리", [r"10년물", r"tnx", r"treasury"]),
        ("WTI", [r"wti"]),
        ("브렌트", [r"브렌트", r"brent"]),
        ("달러 인덱스/DXY", [r"dxy", r"달러 인덱스"]),
        ("원달러", [r"원/달러", r"원달러", r"usd/krw"]),
        ("비트코인", [r"비트코인", r"bitcoin"]),
        ("공포탐욕지수", [r"공포탐욕", r"fear.*greed"]),
        ("경제지표 캘린더", [r"경제 일정", r"경제지표", r"calendar"]),
    ]
    missing_market = []
    for label, patterns in fixed_market_checks:
        if not any(re.search(pattern, market_section) for pattern in patterns):
            missing_market.append(label)
    if missing_market:
        issue(
            findings,
            "content",
            "high" if len(missing_market) >= 4 else "medium",
            "고정 시장 루틴 누락",
            "누락 항목: " + ", ".join(missing_market),
            "PPT 앞단 루틴에 맞춰 지수/히트맵/금리/유가/달러/비트코인/공포탐욕/캘린더를 같은 순서로 배치하세요.",
        )

    if not any(re.search(pattern, (market_section + "\n" + feature_section).lower()) for pattern in [r"실적.*캘린더", r"earnings calendar"]):
        issue(
            findings,
            "content",
            "medium",
            "실적 캘린더 누락",
            "시장 루틴 또는 실적/특징주 섹션에서 이번 주 실적 캘린더를 찾지 못했습니다.",
            "Earnings Whispers 등 고정 소스 이미지를 실적/특징주 섹션 앞단에 배치하세요.",
        )

    if not re.search(r"오늘의 대립축|오늘의 메인|메인 thesis|오늘의 핵심 관점|첫 번째 메인|메인 후보", text):
        issue(
            findings,
            "content",
            "high",
            "오늘의 대립축/thesis 불명확",
            "PPT 표지는 의제 목록 이전에 오늘의 큰 해석 방향을 암시합니다.",
            "진행자용 1페이지 요약 첫머리에 오늘의 핵심 관점 한 문장을 명시하세요.",
        )

    storyline_titles = re.findall(r"^##\s+(.+?)\s*$", storyline, flags=re.M)
    if len(storyline_titles) >= 3:
        buckets = {
            "oil_energy": [r"유가", r"원유", r"wti", r"브렌트", r"opec", r"호르무즈", r"비료"],
            "ai": [r"\bai\b", r"openai", r"오픈ai", r"반도체", r"데이터센터", r"컴퓨팅"],
            "earnings": [r"실적", r"가이던스", r"어닝", r"eps", r"매출"],
            "market": [r"시장", r"지수", r"히트맵", r"위험선호", r"콜옵션"],
            "policy": [r"fed", r"연준", r"금리", r"달러", r"정책"],
        }
        counts = {
            bucket: sum(1 for title in storyline_titles if any(re.search(pattern, title, re.I) for pattern in patterns))
            for bucket, patterns in buckets.items()
        }
        dominant_count = max(counts.values() or [0])
        represented = sum(1 for count in counts.values() if count > 0)
        first_two_same = any(
            all(any(re.search(pattern, title, re.I) for pattern in patterns) for title in storyline_titles[:2])
            for patterns in buckets.values()
        )
        if (dominant_count >= 2 and represented <= 2) or first_two_same:
            issue(
                findings,
                "content",
                "medium",
                "스토리라인 꼭지 다양성 부족",
                "추천 스토리라인 1/2/3이 하나의 이슈를 나눠 전개하는 구조로 보입니다.",
                "각 스토리라인을 독립 방송 꼭지 후보로 분리하세요. 예: 실적/특징주, 시장 톤, 정책·지정학/단신을 서로 다른 슬롯으로 둡니다.",
            )

    if re.search(r"uae|opec|원유|유가|호르무즈|이란", text):
        energy_evidence = [
            ("OPEC/UAE 생산 또는 점유율", r"생산량|점유율|쿼터|quota|capacity"),
            ("호르무즈/수송 병목", r"호르무즈|strait|shipping|수송|봉쇄"),
            ("에너지 섹터/종목 차트", r"xle|oih|정유|에너지주|엑슨|셰브론|slb|hal|occidental"),
            ("원유 재고 이벤트", r"eia|원유재고|휘발유재고"),
        ]
        missing_evidence = [label for label, pattern in energy_evidence if not re.search(pattern, text)]
        if missing_evidence:
            issue(
                findings,
                "content",
                "medium",
                "에너지 메인 서사의 증거 장표 부족",
                "UAE/OPEC을 메인으로 잡았지만 뒷받침 장표가 부족합니다. 부족 항목: " + ", ".join(missing_evidence),
                "OPEC/UAE 생산·쿼터, 호르무즈 수송, 에너지 섹터/종목, EIA 이벤트를 자료 카드로 보강하세요.",
            )

    material_image_refs = len(re.findall(r"`[^`]+`", storyline))
    if image_count(storyline) < 2 and material_image_refs < 6:
        issue(
            findings,
            "content",
            "medium",
            "스토리라인 내 시각 자료 부족",
            f"추천 스토리라인 섹션의 이미지가 {image_count(storyline)}개입니다.",
            "상단에는 이미지를 직접 넣거나, 하단 자료 카드 제목을 code text로 충분히 참조해 PPT 장표 전환이 보이게 하세요.",
        )

    if len(re.findall(r"방송 멘트|짧은 말문|리서치 설명|텍스트-only|텍스트 정리|정리 슬라이드", markdown)) < 2:
        issue(
            findings,
            "content",
            "medium",
            "텍스트-only 슬라이드 초안 부족",
            "PPT 3개 분석상 복잡한 서사는 중간에 3-5문장 정리 슬라이드로 압축됩니다.",
            "`짧은 말문`, `리서치 설명` 또는 `정리 슬라이드 초안`을 스토리라인마다 추가하세요.",
        )

    if len(re.findall(r"다음 자료|다음날|이어집|연결|붙일", markdown)) < 4:
        issue(
            findings,
            "content",
            "medium",
            "자료 간 연결 지시 부족",
            "자료 카드가 개별 메모처럼 보일 수 있습니다.",
            "각 핵심 자료에 `이 자료가 여는 질문`과 `다음에 붙일 자료`를 추가하세요.",
        )

    if feature_section:
        ticker_like = len(re.findall(r"\(([A-Z]{1,5})\)|\b[A-Z]{2,5}\b", feature_section))
        if ticker_like < 4:
            issue(
                findings,
                "content",
                "medium",
                "특징주 후보가 적거나 티커 구조가 약함",
                f"실적/특징주 섹션에서 감지된 티커형 표기가 {ticker_like}개입니다.",
                "상위 테마 카드 1-2개 아래에 종목 4-6개를 붙이고, 종목별 전일 이슈와 일봉/5분봉을 연결하세요.",
            )
        if not re.search(r"테마|증명|섹터|상위", feature_section):
            issue(
                findings,
                "content",
                "medium",
                "특징주가 상위 테마 증명 구조로 묶이지 않음",
                "PPT 특징주는 단순 종목 뉴스가 아니라 당일 큰 테마를 증명하는 사례입니다.",
                "실적주, 테마 증명 종목, 고베타/비주류 움직임을 구분해 배치하세요.",
            )

    if table_count(markdown) == 0:
        issue(
            findings,
            "content",
            "low",
            "테이블 자료 없음",
            "경제 일정이나 수집 현황은 표로 볼 때 빠르게 스캔됩니다.",
            "경제 일정, 소스 커버리지, 후보 장부 요약 중 하나 이상은 표로 유지하세요.",
        )

    if not misc_section:
        issue(
            findings,
            "content",
            "high",
            "보조 꼭지 후보 자료 카드 부재",
            "스토리라인이 참조할 원자료 카드가 없으면 0421식 큐시트가 되기 어렵습니다.",
            "자료명을 짧게 재작성한 보조 꼭지 후보 카드들을 추가하세요.",
        )

    return findings


def review_editorial_storylines(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    storyline = section(markdown, r"추천 스토리라인")
    if not storyline:
        return findings

    blocks = storyline_blocks(storyline)
    titles = [
        normalize(match.group(1))
        for match in re.finditer(r"^#{2,3}\s+\d+\.\s+(.+?)\s*$", storyline, flags=re.M)
    ]
    lowered_titles = [title.lower() for title in titles]
    duplicates = sorted({title for title in lowered_titles if lowered_titles.count(title) > 1})
    if duplicates:
        issue(
            findings,
            "content",
            "medium",
            "스토리라인 제목 중복",
            f"중복 제목이 감지됐습니다: {', '.join(duplicates)}",
            "같은 이슈를 둘로 쪼개지 말고 하나의 더 강한 꼭지로 합치세요.",
        )

    if blocks and len(re.findall(r"추천도:\s*`?[★☆]{1,3}`?", storyline)) < len(blocks):
        issue(
            findings,
            "content",
            "medium",
            "추천도 누락",
            "일부 스토리라인에 별점 추천도가 보이지 않습니다.",
            "각 스토리라인 제목 아래에 `추천도: ★★★` 형식의 3점 척도를 넣으세요.",
        )

    uses_editorial_format = bool(re.search(r"^#{3,4}\s+(선정 이유|왜 지금|쓸 자료)", storyline, flags=re.M))
    required_slots = [
        ("hook", r"^>\s+"),
        ("why_now", r"^#{3,4}\s+(선정 이유|왜 지금)"),
        ("talk_track", r"^#{3,4}\s+(짧은 말문|방송 멘트 초안)"),
    ]
    if uses_editorial_format:
        for index, block in enumerate(blocks, start=1):
            for label, pattern in required_slots:
                if not re.search(pattern, block, flags=re.M):
                    issue(
                        findings,
                        "content",
                        "medium",
                        f"스토리라인 {index} {label} 누락",
                        f"{index}번 스토리라인에 `{label}` 역할의 문단이 보이지 않습니다.",
                        "상단 추천은 방송 글감이므로 훅, 왜 지금, 짧은 말문을 모두 유지하세요.",
                    )
            use_match = re.search(r"^#{3,4}\s+(?:쓸 자료|자료 배치)\s*(.*?)(?=^#{3,4}\s+|\Z)", block, flags=re.M | re.S)
            if not use_match or not re.search(r"`[^`]+`", use_match.group(1)):
                issue(
                    findings,
                    "content",
                    "medium",
                    f"스토리라인 {index} 근거 자료 누락",
                    f"{index}번 스토리라인에 `쓸 자료` 근거가 충분히 보이지 않습니다.",
                    "각 주장은 실제 수집 후보 제목을 code text로 연결하세요.",
                )

    evidence_usage: dict[str, set[int]] = {}
    if uses_editorial_format:
        for index, block in enumerate(blocks, start=1):
            use_match = re.search(r"^#{3,4}\s+(?:쓸 자료|자료 배치)\s*(.*?)(?=^#{3,4}\s+|\Z)", block, flags=re.M | re.S)
            if not use_match:
                continue
            for ref in re.findall(r"`([^`]+)`", use_match.group(1)):
                evidence_usage.setdefault(normalize(ref), set()).add(index)
    repeated = [ref for ref, indexes in evidence_usage.items() if len(indexes) >= 2]
    if repeated:
        issue(
            findings,
            "content",
            "low",
            "핵심 근거 반복 사용",
            f"여러 핵심 스토리라인에서 반복된 근거가 있습니다: {', '.join(repeated[:5])}",
            "반복 근거는 하나의 메인 꼭지에 모으고 나머지 꼭지는 다른 자료로 차별화하세요.",
        )

    internal_phrases = [
        "출처가 같은 방향의 신호",
        "점수와 구체성이",
        "기존 점수 기반",
        "클러스터",
        "selection_method",
        "source-count",
        "same-direction signals",
    ]
    leaked = [phrase for phrase in internal_phrases if phrase.lower() in markdown.lower()]
    if leaked:
        issue(
            findings,
            "content",
            "medium",
            "내부 로직 문장 노출",
            f"최종 본문에 내부 선별 로직 표현이 남아 있습니다: {', '.join(leaked)}",
            "사용자에게 보이는 문장은 방송 편집 판단으로 다시 쓰고, 점수/클러스터 설명은 숨기세요.",
        )
    return findings


def review_content(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    market_section = section(markdown, r"시장은 지금")
    misc_section = section(markdown, r"보조 꼭지 후보|오늘의 이모저모")
    feature_section = section(markdown, r"실적/특징주")

    if not market_section:
        issue(findings, "content", "high", "시장 섹션 없음", "`시장은 지금` 섹션을 찾지 못했습니다.", "시장 캡처와 차트를 `시장은 지금` 아래에 배치하세요.")
    if not misc_section:
        issue(findings, "content", "high", "보조 꼭지 후보 섹션 없음", "`보조 꼭지 후보` 섹션을 찾지 못했습니다.", "후보 자료 카드를 `보조 꼭지 후보` 아래에 배치하세요.")
    if not feature_section:
        issue(findings, "content", "medium", "실적/특징주 섹션 없음", "`실적/특징주` 섹션을 찾지 못했습니다.", "실적 캘린더와 특징주 자료를 별도 섹션으로 유지하세요.")

    for forbidden in ["이 자료가 여는 질문", "다음에 붙일 자료", "오늘의 핵심 키워드", "실적 캘린더 기반 후보", "Finviz 일봉/핫뉴스", "확률 1"]:
        if forbidden in markdown:
            issue(
                findings,
                "content",
                "medium",
                f"compact format 금지 문구 존재: {forbidden}",
                f"`{forbidden}` 문구는 현재 compact dashboard format에서 제거하기로 한 항목입니다.",
                "해당 문구를 제거하고 카드 본문은 한국어 요약 중심으로 유지하세요.",
            )

    if image_count(markdown) < 8:
        issue(
            findings,
            "content",
            "medium",
            "시각 자료 부족",
            f"이미지 수가 {image_count(markdown)}개입니다.",
            "시장 상태, X/뉴스 카드, 실적/특징주 이미지를 충분히 유지하세요.",
        )
    if table_count(markdown) == 0 and "FedWatch 금리 확률" not in markdown:
        issue(
            findings,
            "content",
            "low",
            "테이블 자료 없음",
            "경제 일정이나 FedWatch 확률처럼 빠르게 스캔할 표가 보이지 않습니다.",
            "경제 일정, FedWatch, 소스 커버리지 중 하나 이상을 표로 유지하세요.",
        )
    english_leak_pattern = (
        r"Bloomberg:|Tech stocks today|A draft White House|Big Tech earnings|"
        r"US stocks advanced|Australia and Japan markets|Standard Intelligence raises|"
        r"S&P is considering rule|Real capex \(inflation|33 minutes ago Reuters|"
        r"Huawei expects AI chip|GoDaddy forecasts quarterly"
    )
    if re.search(english_leak_pattern, markdown):
        issue(
            findings,
            "content",
            "medium",
            "영어 원문 제목 누수",
            "최종 페이지에 원문 영어 제목이 그대로 노출됩니다.",
            "한국어 키워드형 제목과 요약으로 변환하세요.",
        )
    findings.extend(review_editorial_storylines(markdown))
    return findings


def score(findings: list[Finding], category: str) -> int:
    penalty = {"high": 16, "medium": 8, "low": 3}
    total = sum(penalty[item.severity] for item in findings if item.category == category)
    return max(0, 100 - total)


def render_markdown(target_date: str, source_path: Path, findings: list[Finding]) -> str:
    format_score = score(findings, "format")
    content_score = score(findings, "content")
    integrity_score = score(findings, "integrity")
    gate = "pass" if format_score >= 80 and content_score >= 75 and not any(item.severity == "high" for item in findings) else "needs_revision"
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%y.%m.%d %H:%M")
    lines = [
        "# Dashboard Quality Review",
        "",
        f"- 대상일: `{target_date}`",
        f"- 리뷰 시각: `{now} (KST)`",
        f"- 대상 파일: `{source_path}`",
        f"- format score: `{format_score}`",
        f"- content score: `{content_score}`",
        f"- integrity score: `{integrity_score}`",
        f"- gate: `{gate}`",
        "",
        "## Summary",
        "",
    ]
    if findings:
        high = sum(1 for item in findings if item.severity == "high")
        medium = sum(1 for item in findings if item.severity == "medium")
        low = sum(1 for item in findings if item.severity == "low")
        lines.append(f"- findings: high {high}, medium {medium}, low {low}")
    else:
        lines.append("- findings: none")

    for category in ["format", "content", "integrity"]:
        lines.extend(["", f"## {category.title()} Findings", ""])
        rows = [item for item in findings if item.category == category]
        if not rows:
            lines.append("- 문제 없음")
            continue
        for index, item in enumerate(rows, start=1):
            lines.extend(
                [
                    f"### {index}. [{item.severity}] {item.title}",
                    "",
                    f"- 문제: {item.detail}",
                    f"- 수정: {item.recommendation}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def render_markdown_legacy_broad(target_date: str, source_path: Path, findings: list[Finding]) -> str:
    format_score = score(findings, "format")
    content_score = score(findings, "content")
    gate = "pass" if format_score >= 80 and content_score >= 75 and not any(item.severity == "high" for item in findings) else "needs_revision"
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%y.%m.%d %H:%M")
    lines = [
        "# Dashboard Quality Review",
        "",
        f"- 대상일: `{target_date}`",
        f"- 리뷰 시각: `{now} (KST)`",
        f"- 대상 파일: `{source_path}`",
        f"- format score: `{format_score}`",
        f"- content score: `{content_score}`",
        f"- gate: `{gate}`",
        "",
        "## Summary",
        "",
    ]
    if findings:
        high = sum(1 for item in findings if item.severity == "high")
        medium = sum(1 for item in findings if item.severity == "medium")
        low = sum(1 for item in findings if item.severity == "low")
        lines.append(f"- findings: high {high}, medium {medium}, low {low}")
    else:
        lines.append("- findings: none")

    for category in ["format", "content"]:
        lines.extend(["", f"## {category.title()} Findings", ""])
        rows = [item for item in findings if item.category == category]
        if not rows:
            lines.append("- 문제 없음")
            continue
        for index, item in enumerate(rows, start=1):
            lines.extend(
                [
                    f"### {index}. [{item.severity}] {item.title}",
                    "",
                    f"- 문제: {item.detail}",
                    f"- 수정: {item.recommendation}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=RUNTIME_REVIEW_DIR)
    parser.add_argument("--json", action="store_true", help="Print JSON summary to stdout.")
    args = parser.parse_args()

    input_path = args.input or (RUNTIME_NOTION_DIR / args.date / f"{display_date_title(args.date)}.md")
    markdown = input_path.read_text(encoding="utf-8")
    findings = review_format(markdown, args.date) + review_content(markdown) + review_integrity(args.date, markdown)
    format_score = score(findings, "format")
    content_score = score(findings, "content")
    integrity_score = score(findings, "integrity")
    gate = "pass" if format_score >= 80 and content_score >= 75 and not any(item.severity == "high" for item in findings) else "needs_revision"

    output_dir = args.output_dir / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "dashboard-quality.md"
    json_path = output_dir / "dashboard-quality.json"
    md_path.write_text(render_markdown(args.date, input_path, findings), encoding="utf-8")
    payload = {
        "ok": True,
        "date": args.date,
        "input": str(input_path),
        "format_score": format_score,
        "content_score": content_score,
        "integrity_score": integrity_score,
        "gate": gate,
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
        "markdown_output": str(md_path),
        "json_output": str(json_path),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print_json(payload if args.json else {k: payload[k] for k in ["ok", "format_score", "content_score", "integrity_score", "gate", "finding_count", "markdown_output", "json_output"]})
    return 1 if gate != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
