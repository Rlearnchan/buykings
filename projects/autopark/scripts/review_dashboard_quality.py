#!/usr/bin/env python3
"""Review an Autopark Notion dashboard against 0421 format and PPT narrative rules."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
RUNTIME_REVIEW_DIR = PROJECT_ROOT / "runtime" / "reviews"
RUNTIME_PROMPT_DIR = PROJECT_ROOT / "runtime" / "openai-prompts"


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


EVIDENCE_MICROCOPY_FORBIDDEN = [
    "source_role",
    "evidence_role",
    "item_id:",
    "evidence_id",
    "asset_id",
    "MF-",
    "http://",
    "https://",
]


def source_stat_count(stats: list[dict], source_id: str) -> int:
    for stat in stats:
        if isinstance(stat, dict) and stat.get("source_id") == source_id:
            try:
                return int(stat.get("item_count") or 0)
            except (TypeError, ValueError):
                return 0
    return 0


def review_headline_river_contract(target_date: str) -> list[Finding]:
    findings: list[Finding] = []
    path = PROCESSED_DIR / target_date / "headline-river.json"
    payload, error = load_json(path)
    if error:
        issue(
            findings,
            "content",
            "low",
            "Headline river artifact missing",
            f"`{path}` could not be loaded: {error}.",
            "Run collect_headline_river.py before market-radar so the broad headline baseline is visible.",
        )
        return findings
    items = payload.get("items") or []
    stats = [stat for stat in (payload.get("source_stats") or []) if isinstance(stat, dict)]
    if not items:
        issue(
            findings,
            "content",
            "low",
            "Headline river has no items",
            "headline-river.json exists but contains zero collected headlines.",
            "Keep deterministic downstream fallbacks, but inspect Finviz/Yahoo/BizToc collection health.",
        )
    required_sources = {
        "finviz-news": "Finviz headline baseline",
        "yahoo-finance-ticker-rss": "Yahoo base ticker RSS",
        "biztoc-feed": "BizToc RSS anomaly feed",
        "biztoc-home": "BizToc home anomaly scan",
    }
    for source_id, label in required_sources.items():
        if source_stat_count(stats, source_id) <= 0:
            issue(
                findings,
                "content",
                "low",
                f"{label} weak or missing",
                f"`{source_id}` produced no headline river items.",
                "Treat this as a source-layer warning, not a publish blocker; check source URL/parser drift if repeated.",
            )
    anomaly = payload.get("anomaly_summary") or {}
    if not (anomaly.get("top_keywords") or []):
        issue(
            findings,
            "content",
            "low",
            "BizToc anomaly keywords missing",
            "headline-river anomaly_summary.top_keywords is empty.",
            "Use BizToc as a noisy keyword detector; if empty repeatedly, inspect the feed/home parser.",
        )
    if not (payload.get("agenda_expansions") or []):
        issue(
            findings,
            "content",
            "low",
            "Preflight agenda expansion absent",
            "No agenda-linked Yahoo ticker expansion was generated.",
            "This is acceptable on quiet/fallback days, but review agenda-to-ticker mapping if it repeats.",
        )
    return findings


def review_analysis_river_contract(target_date: str) -> list[Finding]:
    findings: list[Finding] = []
    path = PROCESSED_DIR / target_date / "analysis-river.json"
    payload, error = load_json(path)
    if error:
        issue(
            findings,
            "content",
            "low",
            "Analysis river artifact missing",
            f"`{path}` could not be loaded: {error}.",
            "Run collect_analysis_river.py before market-radar so specialist analysis context is visible.",
        )
        return findings
    items = payload.get("items") or []
    if not items:
        issue(
            findings,
            "content",
            "low",
            "Analysis river has no items",
            "analysis-river.json exists but contains zero normalized specialist items.",
            "This is not a publish blocker, but repeated emptiness means X/FactSet/IsabelNet source health should be inspected.",
        )
    news_distribution = [
        item.get("source_id") or item.get("source_label")
        for item in items
        if isinstance(item, dict) and item.get("source_role") == "news_distribution"
    ]
    if news_distribution:
        issue(
            findings,
            "integrity",
            "medium",
            "News distribution leaked into analysis river",
            f"analysis-river contains news-distribution sources: {', '.join(str(item) for item in news_distribution[:6])}.",
            "Keep Reuters/Bloomberg/CNBC news distribution in the news/headline layer unless they provide a sanitized analysis candidate elsewhere.",
        )
    for index, item in enumerate(items[:80], start=1):
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get(key) or "") for key in ["title", "summary", "source_label"])
        lowered = text.lower()
        if any(token.lower() in lowered for token in EVIDENCE_MICROCOPY_FORBIDDEN):
            issue(
                findings,
                "integrity",
                "medium",
                "Forbidden token in analysis river",
                f"`{item.get('item_id') or index}` contains a public-forbidden token.",
                "Keep role/id/hash tokens internal and out of publish-facing candidate summaries.",
            )
        if len(normalize(str(item.get("summary") or ""))) > 900:
            issue(
                findings,
                "integrity",
                "medium",
                "Analysis river summary too long",
                f"`{item.get('item_id') or index}` has a long summary that may resemble raw body text.",
                "Store only sanitized excerpts/summaries; never raw article bodies or full X threads.",
            )
    return findings


def review_evidence_microcopy_contract(target_date: str) -> list[Finding]:
    findings: list[Finding] = []
    path = PROCESSED_DIR / target_date / "evidence-microcopy.json"
    payload, error = load_json(path)
    if error:
        if os.environ.get("AUTOPARK_EVIDENCE_MICROCOPY_ENABLED") == "1":
            issue(
                findings,
                "integrity",
                "high",
                "Evidence microcopy artifact missing",
                f"`{path}` could not be loaded: {error}",
                "Run build_evidence_microcopy.py after market-radar and before focus/editorial.",
            )
        return findings
    if payload.get("enabled") and not payload.get("items"):
        issue(
            findings,
            "integrity",
            "high",
            "Evidence microcopy has no items",
            "Evidence microcopy is enabled but generated zero item summaries.",
            "Generate deterministic fallback rows when the API path is unavailable.",
        )
    generated_fields = {str(field) for field in (payload.get("generated_fields") or [])}
    requires_public_title = "title" in generated_fields
    for index, item in enumerate(payload.get("items") or [], start=1):
        if not isinstance(item, dict):
            issue(findings, "integrity", "high", "Invalid evidence microcopy row", f"Row {index} is not an object.", "Keep items as JSON objects.")
            continue
        title = normalize(str(item.get("title") or ""))
        if requires_public_title and (not title or len(title) > 28):
            issue(
                findings,
                "integrity",
                "high",
                "Evidence microcopy title invalid",
                f"`{item.get('item_id') or index}` title is {len(title)} chars.",
                "Keep evidence microcopy titles around 20 characters and under 28 characters.",
            )
        content = normalize(str(item.get("content") or " ".join((item.get("summary_bullets") or [])[:1]) or ""))
        if not content:
            issue(
                findings,
                "integrity",
                "high",
                "Evidence microcopy content missing",
                f"`{item.get('item_id') or index}` has no one-line content.",
                "Each evidence microcopy item needs one content field with 1-3 complete sentences.",
            )
        sentence_count = len([part for part in re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+|(?<=요\.)\s+|\n+", content) if normalize(part)])
        if content and (sentence_count < 1 or sentence_count > 3):
            issue(
                findings,
                "integrity",
                "high",
                "Evidence microcopy sentence count invalid",
                f"`{item.get('item_id') or index}` content has {sentence_count} sentence-like parts.",
                "Keep evidence microcopy content to one core point in 1-3 complete sentences.",
            )
        for field, value in [("content", content)]:
            text = normalize(str(value or ""))
            if len(text) > 300:
                issue(
                    findings,
                    "integrity",
                    "high",
                    "Evidence microcopy line too long",
                    f"`{item.get('item_id') or index}` {field} is {len(text)} chars.",
                    "Keep generated evidence microcopy content within 300 characters.",
                )
            lowered = text.lower()
            if any(token.lower() in lowered for token in EVIDENCE_MICROCOPY_FORBIDDEN):
                issue(
                    findings,
                    "integrity",
                    "high",
                    "Evidence microcopy exposes forbidden token",
                    f"`{item.get('item_id') or index}` {field} contains a forbidden token or URL.",
                    "Validate and replace only the failing item with deterministic fallback.",
                )
            if re.search(r"<html\b|<!doctype html|<body\b|</body>|X-Amz-Signature|SessionToken", text, flags=re.I):
                issue(
                    findings,
                    "integrity",
                    "high",
                    "Evidence microcopy contains raw body material",
                    f"`{item.get('item_id') or index}` {field} looks like raw HTML or a signed response.",
                    "Never send or persist raw HTML, full article bodies, or signed URLs in microcopy.",
                )
    return findings


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


def public_before_media_focus(markdown: str) -> str:
    if is_compact_publish_markdown(markdown):
        return compact_host_area(markdown)
    public = public_markdown(markdown)
    return re.split(r"^##\s+\d+\.\s+미디어 포커스\s*$", public, maxsplit=1, flags=re.M)[0]


COMPACT_TOP_LEVEL_HEADINGS = ["🎥 진행자용 요약", "🤖 자료 수집"]
COMPACT_HOST_SUBHEADINGS = ["주요 뉴스", "방송 순서", "스토리라인"]
COMPACT_HOST_FORBIDDEN = [
    "MF-",
    "http://",
    "https://",
    "source_role",
    "evidence_role",
    "item_id",
    "evidence_id",
    "![",
    "<table",
    "PPT 제작 큐",
    "슬라이드 제작 순서",
    "말로만 처리할 자료",
    "자료 수집 상세",
    "경제 일정/실적 일정",
    "Audit",
    "Debug",
]
COMPACT_BANNED_SECTIONS = [
    "# PPT 제작 큐",
    "## 슬라이드 제작 순서",
    "## 말로만 처리할 자료",
    "# 자료 수집 상세",
    "## 경제 일정/실적 일정",
    "# Audit",
    "# Debug",
    "# 품질 리뷰",
    "# 회고",
    "## 자료 수집",
]
COMPACT_GLOBAL_FORBIDDEN = [
    "source_role",
    "evidence_role",
    "item_id",
    "evidence_id",
    "asset_id",
    "MF-",
    "PPT 제작 큐",
    "슬라이드 제작 순서",
    "말로만 처리할 자료",
    "자료 수집 상세",
    "리드 스토리 자료",
    "보조 스토리 자료",
    "확인 필요 자료",
    "원문 확인 필요 자료",
    "경제 일정/실적 일정",
    "# Audit",
    "# Debug",
]
COMPACT_MARKET_NOW_LABEL_ORDER = [
    "주요 지수 흐름",
    "S&P500 히트맵",
    "러셀 2000 히트맵",
    "10년물 국채금리",
    "WTI 가격 차트",
    "브렌트 가격 차트",
    "달러인덱스 차트",
    "원/달러 환율 차트",
    "비트코인 가격 차트",
    "CNN Fear & Greed",
    "FedWatch",
    "오늘의 경제지표",
]


def is_compact_publish_markdown(markdown: str) -> bool:
    top = [title for level, title in heading_lines(markdown) if level == 1]
    return any(title in top for title in COMPACT_TOP_LEVEL_HEADINGS)


def compact_host_area(markdown: str) -> str:
    match = re.search(r"^#\s+🎥 진행자용 요약\s*$", markdown, flags=re.M)
    if not match:
        return ""
    start = match.start()
    next_match = re.search(r"^#\s+🤖 자료 수집\s*$", markdown[match.end() :], flags=re.M)
    if not next_match:
        return markdown[start:]
    return markdown[start : match.end() + next_match.start()]


def compact_collection_area(markdown: str) -> str:
    parts = re.split(r"^#\s+🤖 자료 수집\s*$", markdown, maxsplit=1, flags=re.M)
    return parts[1] if len(parts) == 2 else ""


def compact_collection_sections(collection: str) -> list[str]:
    return [title for level, title in heading_lines(collection) if level == 2]


def compact_section_body(host: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", host, flags=re.M)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", host[start:], flags=re.M)
    end = start + next_match.start() if next_match else len(host)
    return host[start:end].strip()


def compact_bullet_count(body: str) -> int:
    return len(re.findall(r"^-\s+", body, flags=re.M))


def compact_story_blocks(host: str) -> list[str]:
    body = compact_section_body(host, "스토리라인")
    matches = list(re.finditer(r"^###\s+[123]\.\s+.+$", body, flags=re.M))
    blocks = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        blocks.append(body[start:end].strip())
    return blocks


def compact_collection_labels(collection: str) -> list[str]:
    return [title for level, title in heading_lines(collection) if level == 3]


def compact_collection_section_body(collection: str, heading: str) -> str:
    return compact_section_body(collection, heading)


def compact_card_blocks(section_body: str) -> list[str]:
    matches = list(re.finditer(r"^###\s+.+$", section_body, flags=re.M))
    blocks: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section_body)
        blocks.append(section_body[start:end].strip())
    return blocks


def card_title(block: str) -> str:
    first = block.splitlines()[0] if block.splitlines() else ""
    return re.sub(r"^###\s+", "", first).strip()


def strip_public_label_marker(label: str) -> str:
    text = normalize(label).strip("`")
    text = re.sub(r"^(?:[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|\(\d+\))\s+", "", text)
    return text.strip("` ")


def image_count(block: str) -> int:
    return len(re.findall(r"^!\[[^\]]*]\([^)]+\)$", block, flags=re.M))


def has_markdown_table(text: str) -> bool:
    return bool(re.search(r"^\|.+\|\s*$", text, flags=re.M))


def markdown_image_targets(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text or "")


def missing_image_marker(text: str) -> bool:
    return bool(re.search(r"^-\s+이미지 없음\s*$", text or "", flags=re.M))


def finviz_index_chart_image_ok(image_path: str) -> bool | None:
    if "finviz-index-futures" not in image_path:
        return None
    try:
        from PIL import Image
    except ImportError:
        return None
    path = Path(image_path)
    if not path.is_absolute():
        path = PROJECT_ROOT.parents[1] / path
    try:
        image = Image.open(path).convert("RGB")
    except OSError:
        return None
    width, height = image.size
    if width < 650 or height < 180:
        return False
    left = image.crop((0, 0, min(width, 390), min(height, 190)))
    title_band = left.crop((25, 18, min(left.width, 170), min(left.height, 58)))
    chart_body = left.crop((35, 45, min(left.width, 340), min(left.height, 175)))
    title_pixels = 0
    grid_pixels = 0
    market_pixels = 0
    title_data = title_band.load()
    for y in range(title_band.height):
        for x in range(title_band.width):
            red, green, blue = title_data[x, y]
            if max(red, green, blue) < 245 and max(red, green, blue) - min(red, green, blue) < 35:
                title_pixels += 1
    chart_data = chart_body.load()
    for y in range(chart_body.height):
        for x in range(chart_body.width):
            red, green, blue = chart_data[x, y]
            if 175 <= red <= 235 and 175 <= green <= 235 and 175 <= blue <= 235 and max(red, green, blue) - min(red, green, blue) < 28:
                grid_pixels += 1
            if (green > red + 35 and green > blue + 20) or (red > green + 35 and red > blue + 20):
                market_pixels += 1
    return title_pixels >= 80 and grid_pixels >= 250 and market_pixels >= 120


def compact_english_word_run_too_long(text: str) -> bool:
    return len(re.findall(r"\b[A-Za-z][A-Za-z0-9&'’.-]*\b", text or "")) >= 5


def compact_raw_source_like(text: str) -> bool:
    lowered = normalize(text).lower()
    enum_like = re.fullmatch(r"[a-z0-9_.:-]{3,40}", lowered.strip() or "") is not None
    return bool(
        enum_like
        or "_" in lowered
        or re.search(r"\b[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/|\b)", lowered)
        or re.search(r"@\w+|breaking:|trump on|says he will|등\s+\d+개\s+출처|source-count|same direction", lowered)
        or re.search(r"\b(?:low|medium|high|unknown|null|true|false|fallback|source_gap|false_lead|missing_assets)\b", lowered)
        or lowered.count("/") >= 2
    )


def compact_contains_any(text: str, words: list[str]) -> bool:
    lowered = normalize(text).lower()
    return any(word.lower() in lowered for word in words)


def compact_host_relevance_complete(lines: list[str]) -> bool:
    blob = " ".join(lines)
    requirements = [
        ["전날", "전일", "시장", "주목", "반영", "가격", "화제"],
        ["첫 5분", "첫 꼭지", "방송", "진행자", "보여주", "다룰"],
        ["한국", "개인투자자", "PPT", "환율", "업종", "성장주"],
    ]
    return all(compact_contains_any(blob, needles) for needles in requirements)


def compact_public_label_ok(label: str) -> bool:
    text = normalize(label)
    if not text or len(text) > 28:
        return False
    forbidden = [
        "MF-",
        "http",
        "/",
        "source_role",
        "evidence_role",
        "item_id",
        "evidence_id",
        "Reuters",
        "Bloomberg",
        "CNBC",
        "Yahoo Finance",
        "TradingView",
        "Kobeissi",
        "AdvisorPerspectives",
    ]
    if any(token.lower() in text.lower() for token in forbidden):
        return False
    return not compact_english_word_run_too_long(text)


def review_compact_publish_contract(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = markdown.splitlines()
    meta_patterns = [
        r"^문서 생성: `\d{2}\.\d{2}\.\d{2} \d{2}:\d{2} \(KST\)`$",
        r"^자료 수집: `[^`]+ \(KST\)`$",
        r"^시장 차트: `차트별 기준 시점 별도 표기`$",
    ]
    for index, pattern in enumerate(meta_patterns):
        if len(lines) <= index or not re.match(pattern, lines[index]):
            issue(findings, "format", "high", "COMPACT-001 메타 3줄 불일치", "문서 맨 위 메타 3줄이 고정 형식과 다릅니다.", "문서 생성/자료 수집/시장 차트 3줄만 먼저 렌더하세요.")
            break

    top = [title for level, title in heading_lines(markdown) if level == 1]
    if top != COMPACT_TOP_LEVEL_HEADINGS:
        issue(findings, "format", "high", "COMPACT-002 top-level heading 불일치", f"top-level heading: {top}", "허용 heading은 # 🎥 진행자용 요약, # 🤖 자료 수집 두 개뿐입니다.")
    global_hits = [token for token in COMPACT_GLOBAL_FORBIDDEN if token in markdown]
    if global_hits:
        issue(findings, "format", "high", "COMPACT-021 publish forbidden metadata", ", ".join(global_hits), "publish Markdown에는 role/id/debug/PPT 제작 큐 성격의 내부 토큰을 렌더하지 마세요.")

    host = compact_host_area(markdown)
    if not host:
        issue(findings, "format", "high", "COMPACT-003 진행자용 요약 없음", "host_area를 찾을 수 없습니다.", "고정 heading # 🎥 진행자용 요약을 사용하세요.")
        return findings

    host_h2 = [title for level, title in heading_lines(host) if level == 2]
    if host_h2 != COMPACT_HOST_SUBHEADINGS:
        issue(findings, "format", "high", "COMPACT-004 host 하위 heading 불일치", f"host h2: {host_h2}", "주요 뉴스/방송 순서/스토리라인 세 heading만 허용합니다.")
    forbidden_hits = [token for token in COMPACT_HOST_FORBIDDEN if token in host]
    if forbidden_hits:
        issue(findings, "format", "high", "COMPACT-005 host forbidden token", ", ".join(forbidden_hits), "host_area에는 내부 ID, URL, 이미지, audit/debug 성격 토큰을 넣지 마세요.")
    if has_markdown_table(host):
        issue(findings, "format", "high", "COMPACT-006 host table 금지", "host_area에 Markdown table이 있습니다.", "host_area는 bullet과 짧은 문장만 사용하세요.")
    if len([line for line in host.splitlines() if line.strip()]) > 55:
        issue(findings, "format", "high", "COMPACT-007 host line count 초과", "host_area가 55줄을 초과합니다.", "진행자용 요약은 55줄 이하로 유지하세요.")
    news_body = compact_section_body(host, "주요 뉴스")
    news_bullets = re.findall(r"^-\s+(.+)$", news_body, flags=re.M)
    if len(news_bullets) != 3:
        issue(findings, "format", "high", "COMPACT-008 주요 뉴스 bullet 수 불일치", "주요 뉴스는 정확히 3개 bullet이어야 합니다.", "주요 뉴스 bullet 3개만 렌더하세요.")
    else:
        invalid_news = [bullet for bullet in news_bullets if len(bullet) > 80 or compact_english_word_run_too_long(bullet)]
        if invalid_news:
            issue(findings, "format", "high", "COMPACT-016 주요 뉴스 public 문장 위반", "주요 뉴스 bullet이 80자를 넘거나 영어 원문형 제목처럼 보입니다.", "주요 뉴스는 80자 이하 한국어 방송 해석 문장으로만 렌더하세요.")
    if compact_bullet_count(compact_section_body(host, "방송 순서")) != 5:
        issue(findings, "format", "high", "COMPACT-009 방송 순서 bullet 수 불일치", "방송 순서는 정확히 5개 bullet이어야 합니다.", "시장/3개 스토리라인/실적 bullet만 렌더하세요.")

    story_blocks = compact_story_blocks(host)
    if len(story_blocks) != 3:
        issue(findings, "format", "high", "COMPACT-010 스토리라인 수 불일치", f"스토리라인 {len(story_blocks)}개가 렌더됐습니다.", "스토리라인은 정확히 3개만 렌더하세요.")
    for index, block in enumerate(story_blocks, start=1):
        if len(re.findall(r"^추천도:\s+`(?:★★★|★★☆|★☆☆)`$", block, flags=re.M)) != 1:
            issue(findings, "format", "high", "COMPACT-011 추천도 형식 불일치", f"{index}번 스토리라인 추천도 형식이 다릅니다.", "추천도는 ★★★/★★☆/★☆☆ 중 하나만 사용하세요.")
        quotes = [match.group(1).strip() for match in re.finditer(r"^>\s+(.+)$", block, flags=re.M)]
        if len(quotes) != 1:
            issue(findings, "format", "high", "COMPACT-012 quote 줄 수 위반", f"{index}번 스토리라인 quote 수: {len(quotes)}", "quote는 한 줄 인용문 하나만 렌더하세요.")
        quote_bad = [line for line in quotes if len(line) > 180 or compact_raw_source_like(line) or any(token in line for token in COMPACT_HOST_FORBIDDEN)]
        if quote_bad:
            issue(findings, "format", "high", "COMPACT-017 quote public 문장 위반", f"{index}번 quote가 180자를 넘거나 금지 토큰을 포함합니다.", "quote는 180자 이하 public 문장만 사용하세요.")
        if block.count("**왜 중요한가**") != 1:
            issue(findings, "format", "high", "COMPACT-040 왜 중요한가 누락", f"{index}번 스토리라인에 왜 중요한가 블록이 없습니다.", "각 스토리라인에 **왜 중요한가**와 2~3개 bullet을 렌더하세요.")
        why_body = block.split("**왜 중요한가**", 1)[1].split("**슬라이드 구성:**", 1)[0] if "**왜 중요한가**" in block else ""
        why_bullets = re.findall(r"^-\s+(.+)$", why_body, flags=re.M)
        if len(why_bullets) < 2 or len(why_bullets) > 3:
            issue(findings, "format", "high", "COMPACT-041 왜 중요한가 bullet 수 위반", f"{index}번 why bullet 수: {len(why_bullets)}", "왜 중요한가 bullet은 2~3개만 렌더하세요.")
        why_bad = [line for line in why_bullets if len(line) > 90 or compact_raw_source_like(line) or any(token in line for token in COMPACT_HOST_FORBIDDEN)]
        if why_bad:
            issue(findings, "format", "high", "COMPACT-042 왜 중요한가 public 문장 위반", f"{index}번 why bullet이 90자를 넘거나 금지 토큰을 포함합니다.", "왜 중요한가 bullet은 90자 이하 public 문장만 사용하세요.")
        if why_bullets and not compact_host_relevance_complete(why_bullets):
            issue(findings, "format", "high", "COMPACT-045 왜 중요한가 핵심 요소 누락", f"{index}번 why bullet: " + " / ".join(why_bullets[:3]), "왜 중요한가에는 전날 시장 이슈, 첫 5분 방송 이유, 한국장/개인투자자/PPT 연결점을 모두 담으세요.")
        slide_match = re.search(r"^\*\*슬라이드 구성:\*\*\s+(.+)$", block, flags=re.M)
        if not slide_match:
            issue(findings, "format", "high", "COMPACT-013 슬라이드 구성 한 줄 누락", f"{index}번 스토리라인에 한 줄 슬라이드 구성이 없습니다.", "`**슬라이드 구성:** `① 자료명` → `② 자료명`` 형식으로 렌더하세요.")
            material_labels = []
        else:
            slide_line = slide_match.group(1).strip()
            if any(token in slide_line for token in COMPACT_HOST_FORBIDDEN) or "\n" in slide_line:
                issue(findings, "format", "high", "COMPACT-043 슬라이드 구성 금지 토큰", f"{index}번 슬라이드 구성에 금지 토큰이 있습니다.", "슬라이드 구성에는 번호+자료명만 넣으세요.")
            refs = re.findall(r"`([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|\(\d+\))\s+([^`]+)`", slide_line)
            if not refs:
                issue(findings, "format", "high", "COMPACT-014 슬라이드 구성 원형 번호 누락", f"{index}번 슬라이드 구성: {slide_line}", "슬라이드 구성 자료명은 미디어 포커스의 원형 번호와 함께 렌더하세요.")
            material_labels = [label.strip() for _, label in refs]
            bad_labels = [label for label in material_labels if not compact_public_label_ok(label)]
            if bad_labels:
                issue(findings, "format", "high", "COMPACT-018 public material label 위반", f"{index}번 스토리라인 자료명 위반: " + ", ".join(bad_labels[:4]), "자료명은 28자 이하 한국어 명사구로 렌더하고 내부 ID/URL/source metadata를 넣지 마세요.")

    collection = compact_collection_area(markdown)
    if collection:
        sections = compact_collection_sections(collection)
        expected_sections = ["1. 시장은 지금", "2. 미디어 포커스", "3. 실적/특징주"]
        if sections != expected_sections:
            issue(findings, "format", "high", "COMPACT-022 자료 수집 section 불일치", f"자료 수집 sections: {sections}", "자료 수집 하위 heading은 ## 1. 시장은 지금, ## 2. 미디어 포커스, ## 3. 실적/특징주만 허용합니다.")
        labels = compact_collection_labels(collection)
        label_positions = {label: index for index, label in enumerate(labels)}
        for earlier, later in [
            ("주요 지수 흐름", "10년물 국채금리"),
            ("S&P500 히트맵", "WTI 가격 차트"),
            ("WTI 가격 차트", "브렌트 가격 차트"),
        ]:
            if earlier in label_positions and later in label_positions and label_positions[earlier] > label_positions[later]:
                issue(findings, "format", "high", "COMPACT-024 자료 수집 material order 불일치", f"{earlier}가 {later}보다 뒤에 있습니다.", "시장 지도 → 히트맵 → 금리 → 유가 → 달러/환율 → 위험자산 순서를 유지하세요.")
        if "원/달러 환율 차트" not in labels and ("usd-krw" in markdown or "원/달러" in markdown):
            issue(findings, "format", "high", "COMPACT-025 usd-krw label 불일치", "USD/KRW 자료가 원/달러 환율 차트 label로 렌더되지 않았습니다.", "usd-krw는 반드시 원/달러 환율 차트로 렌더하세요.")
        duplicate_cards = sorted(label for label in set(labels) if labels.count(label) > 1)
        if duplicate_cards:
            issue(findings, "format", "high", "COMPACT-026 중복 자료 카드", "동일 label 카드가 중복 렌더됐습니다: " + ", ".join(duplicate_cards[:6]), "같은 asset/url/image 자료는 한 번만 full card로 렌더하세요.")
        story_labels = []
        for block in story_blocks:
            slide_match = re.search(r"^\*\*슬라이드 구성:\*\*\s+(.+)$", block, flags=re.M)
            if slide_match:
                story_labels.extend(label.strip() for _, label in re.findall(r"`([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|\(\d+\))\s+([^`]+)`", slide_match.group(1)))
        bare_labels = {strip_public_label_marker(label) for label in labels}
        missing_story_labels = sorted(set(story_labels) - bare_labels)
        if missing_story_labels:
            issue(findings, "format", "high", "COMPACT-027 스토리 자료 label 미수집", "스토리라인 자료명이 자료 수집 카드에 없습니다: " + ", ".join(missing_story_labels[:6]), "슬라이드 구성에 노출한 public material label은 자료 수집에도 같은 label로 렌더하세요.")
        if re.search(r"^-\s+(?:source_role|evidence_role|item_id|evidence_id|원문 제목):", collection, flags=re.M):
            issue(findings, "format", "high", "COMPACT-028 자료 카드 필드 위반", "자료 수집 카드에 금지 필드가 렌더됐습니다.", "자료 카드에는 출처/수집 시점/요약/원문/이미지만 렌더하세요.")
        market_body = compact_collection_section_body(collection, "1. 시장은 지금")
        media_body = compact_collection_section_body(collection, "2. 미디어 포커스")
        feature_body = compact_collection_section_body(collection, "3. 실적/특징주")
        market_blocks = compact_card_blocks(market_body)
        market_titles = [card_title(block) for block in market_blocks]
        market_block_by_title = {card_title(block): block for block in market_blocks}
        if "1. 시장은 지금" not in sections:
            issue(findings, "format", "high", "COMPACT-029 시장은 지금 누락", "## 1. 시장은 지금 section이 없습니다.", "자료 수집 첫 section으로 시장은 지금을 렌더하세요.")
        missing_market_cards = [label for label in COMPACT_MARKET_NOW_LABEL_ORDER if label not in market_titles]
        if missing_market_cards:
            issue(findings, "format", "high", "COMPACT-044 시장 필수 카드 누락", ", ".join(missing_market_cards), "시장 지도 고정 카드 전체를 같은 순서로 렌더하세요.")
        index_block = market_block_by_title.get("주요 지수 흐름", "")
        index_image_count = image_count(index_block)
        index_blank = missing_image_marker(index_block)
        if market_titles.count("주요 지수 흐름") != 1 or (index_image_count < 2 and not index_blank):
            issue(findings, "format", "high", "COMPACT-030 주요 지수 흐름 2장 누락", f"시장 카드: {market_titles[:6]}", "Finviz index futures 캡처는 주요 지수 흐름 한 카드 안에 2장 렌더하세요.")
        index_quality = [
            finviz_index_chart_image_ok(target)
            for target in markdown_image_targets(index_block)
        ]
        bad_index_images = [result for result in index_quality if result is False]
        if bad_index_images:
            issue(findings, "format", "high", "COMPACT-050 주요 지수 흐름 이미지 품질 실패", "Finviz 주요 지수 이미지가 상단 DOW/NASDAQ/S&P500 차트 형태로 보이지 않습니다.", "Cloudflare 화면이나 테이블 영역 crop이 아닌 상단 지수 캔들차트 2장을 다시 캡처하세요.")
        fedwatch_block = market_block_by_title.get("FedWatch", "")
        fedwatch_blank = missing_image_marker(fedwatch_block)
        if market_titles.count("FedWatch") != 1 or (image_count(fedwatch_block) < 2 and not fedwatch_blank):
            issue(findings, "format", "high", "COMPACT-031 FedWatch 단기/장기 누락", f"시장 카드: {market_titles}", "FedWatch 수집 실패 시 과거 이미지를 쓰지 말고 이미지 없음으로 렌더하세요.")
        economy_block = market_block_by_title.get("오늘의 경제지표", "")
        if market_titles.count("오늘의 경제지표") != 1 or image_count(economy_block) < 1:
            issue(findings, "format", "high", "COMPACT-053 오늘의 경제지표 누락", f"시장 카드: {market_titles}", "FedWatch 바로 뒤에 오늘의 경제지표 표 이미지를 렌더하세요.")
        elif "FedWatch" in market_titles and "오늘의 경제지표" in market_titles:
            if market_titles.index("오늘의 경제지표") != market_titles.index("FedWatch") + 1 or market_titles.index("오늘의 경제지표") != len(market_titles) - 1:
                issue(findings, "format", "high", "COMPACT-054 FedWatch/경제지표 순서 위반", f"시장 카드: {market_titles}", "오늘의 경제지표는 FedWatch 바로 뒤, 시장 섹션 최하단에 렌더하세요.")
        if re.search(r"^-\s+(?:요약|원문 제목|기준 시점|내용):", market_body, flags=re.M):
            issue(findings, "format", "high", "COMPACT-032 시장 카드 설명 필드 위반", "시장 차트 카드에 요약/원문 제목/기준 시점/내용 필드가 있습니다.", "시장 차트에는 출처와 기준/캡처/확인 메타, 이미지만 렌더하세요.")
        if "원/달러 환율 차트" not in market_titles and "원/달러" in markdown:
            issue(findings, "format", "high", "COMPACT-033 원/달러 label 누락", "원/달러 자료가 시장 카드 label로 보이지 않습니다.", "usd-krw는 원/달러 환율 차트로 렌더하세요.")
        if "2. 미디어 포커스" not in sections:
            issue(findings, "format", "high", "COMPACT-034 미디어 포커스 누락", "## 2. 미디어 포커스 section이 없습니다.", "시장은 지금 다음에는 미디어 포커스 하나만 렌더하세요.")
        media_blocks = compact_card_blocks(media_body)
        for idx, block in enumerate(media_blocks, start=1):
            title = card_title(block)
            if not re.match(r"^(?:[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|\(\d+\))\s+", title):
                issue(findings, "format", "high", "COMPACT-035 미디어 포커스 순번 누락", f"자료명 `{title}`에 원형 숫자가 없습니다.", "미디어 포커스 자료명은 ①부터 순서대로 시작하세요.")
            if "- 출처:" not in block or not re.search(r"^-\s+(?:게시|확인):\s+`[^`]+`", block, flags=re.M):
                issue(findings, "format", "high", "COMPACT-036 미디어 카드 출처/시간 메타 누락", title, "각 미디어 포커스 카드에는 출처와 게시 또는 확인 시점을 렌더하세요.")
            if re.search(r"^-\s+출처:\s+(?:Autopark|Market Focus|Pre-flight Agenda)\s*$", block, flags=re.M):
                issue(findings, "format", "high", "COMPACT-052 미디어 카드 내부 단계 출처 노출", title, "미디어 포커스의 출처는 뉴스/자료 제공자/원자료 사이트명이어야 합니다.")
            if "**주요 내용**" not in block:
                issue(findings, "format", "high", "COMPACT-037 미디어 카드 주요 내용 누락", title, "각 미디어 포커스 카드에는 주요 내용 블록을 렌더하세요.")
            content_part = block.split("**주요 내용**", 1)[1] if "**주요 내용**" in block else ""
            bullets = re.findall(r"^-\s+(.+)$", content_part, flags=re.M)
            if len(bullets) < 1 or len(bullets) > 3:
                issue(findings, "format", "high", "COMPACT-038 미디어 주요 내용 bullet 수 위반", f"{title}: {len(bullets)}개", "주요 내용 bullet은 1~3개로 렌더하세요.")
            raw_like_bullets = [bullet for bullet in bullets if compact_raw_source_like(bullet)]
            if raw_like_bullets:
                issue(findings, "format", "low", "COMPACT-039 미디어 주요 내용 bullet 원문형 노출", f"{title}: " + ", ".join(raw_like_bullets[:2]), "당분간 원문형 문장 감지는 발행 blocker가 아니라 polish finding으로만 기록합니다.")
            long_bullets = [bullet for bullet in bullets if len(bullet) > 300 and not compact_raw_source_like(bullet)]
            if long_bullets:
                issue(findings, "format", "low", "COMPACT-039 미디어 주요 내용 bullet 길이 초과", f"{title}: " + ", ".join(long_bullets[:2]), "당분간 300자 초과는 발행 blocker가 아니라 polish finding으로만 기록합니다.")
        if "3. 실적/특징주" not in sections:
            issue(findings, "format", "high", "COMPACT-046 실적/특징주 누락", "## 3. 실적/특징주 section이 없습니다.", "특징주와 실적 캘린더는 미디어 포커스가 아니라 3번 섹션에 렌더하세요.")
        feature_blocks = compact_card_blocks(feature_body)
        feature_titles = [card_title(block) for block in feature_blocks]
        if feature_titles[:1] != ["실적 캘린더"]:
            issue(findings, "format", "high", "COMPACT-047 실적 캘린더 첫 카드 누락", f"실적/특징주 첫 카드: {feature_titles[:1]}", "실적/특징주 섹션의 첫 자료는 ### 실적 캘린더 이미지 카드여야 합니다.")
        if feature_blocks and image_count(feature_blocks[0]) < 1:
            issue(findings, "format", "high", "COMPACT-048 실적 캘린더 이미지 누락", "실적 캘린더 카드에 이미지가 없습니다.", "Earnings Whispers 실적 캘린더 캡처를 첫 카드 이미지로 렌더하세요.")
        numbered_feature_titles = [title for title in feature_titles[1:] if re.match(r"^(?:\\d+\\.|[①②③④⑤⑥⑦⑧⑨⑩])\\s+", title)]
        if numbered_feature_titles:
            issue(findings, "format", "high", "COMPACT-049 특징주 기업명 번호 노출", ", ".join(numbered_feature_titles[:4]), "실적/특징주 하위 기업명 앞에는 순번을 붙이지 마세요.")

    for banned in COMPACT_BANNED_SECTIONS:
        if banned in markdown:
            issue(findings, "format", "high", "COMPACT-015 금지 섹션 노출", banned, "publish Markdown에서는 금지 섹션을 생성하지 마세요.")
    return findings


def compact_top_markdown(markdown: str) -> str:
    host = section(markdown, r"진행자용 1페이지 요약")
    if host:
        return host
    return re.split(r"^#\s+(?:PPT 제작 큐|자료 수집 상세|📚\s*추천 스토리라인)\s*$", markdown, maxsplit=1, flags=re.M)[0]


PUBLIC_USES = {"lead", "supporting_story", "talk_only"}


def json_blob(payload: object) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(payload)


def local_evidence_blob(radar: dict) -> str:
    parts: list[str] = []
    for item in radar.get("candidates") or []:
        if not isinstance(item, dict):
            continue
        for key in ["id", "item_id", "source", "source_name", "title", "headline", "summary", "radar_question"]:
            value = item.get(key)
            if value:
                parts.append(str(value))
    for chart_id in ["us10y", "crude-oil-wti", "crude-oil-brent", "dollar-index", "usd-krw", "bitcoin"]:
        title = chart_title(chart_id)
        if title:
            parts.extend([chart_id, title])
    return normalize(" ".join(parts)).lower()


def target_tokens(value: str) -> list[str]:
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "market",
        "markets",
        "reaction",
        "news",
        "latest",
        "today",
        "check",
        "source",
    }
    tokens = re.findall(r"[A-Za-z0-9가-힣/.-]{3,}", value or "")
    rows: list[str] = []
    for token in tokens:
        lowered = token.lower().strip(".-/")
        if lowered and lowered not in stopwords and lowered not in rows:
            rows.append(lowered)
    return rows


def target_collected(target: dict, collected_blob: str) -> bool:
    query = normalize(target.get("query_or_asset") or "")
    if not query:
        return False
    lowered = query.lower()
    if lowered in collected_blob:
        return True
    tokens = target_tokens(query)
    if not tokens:
        return False
    needed = 1 if len(tokens) <= 2 else 2
    return sum(1 for token in tokens if token in collected_blob) >= needed


def query_too_broad(query: str) -> bool:
    text = normalize(query).lower()
    if not text:
        return True
    generic = {
        "stock market news",
        "market news",
        "latest market news",
        "us market news",
        "stocks today",
        "business news",
    }
    if text in generic:
        return True
    tokens = target_tokens(text)
    if len(tokens) <= 1:
        return True
    return len(tokens) <= 2 and not re.search(r"\b(fed|fomc|cpi|pce|jobs|dxy|us10y|wti|brent|ai|nvidia|oil|earnings|reuters|bloomberg|cnbc)\b", text, re.I)


def raw_packet_violations(input_payload: dict) -> list[str]:
    blob = json_blob(input_payload)
    checks = {
        "raw URL": r"https?://",
        "signed URL": r"(X-Amz-Signature|Signature=|Expires=|AWSAccessKeyId)",
        "local screenshot path": r"([A-Za-z]:\\|runtime[\\/](?:screenshots|assets)|exports[\\/]current|\.png\b|\.jpe?g\b|\.webp\b)",
        "article/social body key": r'"(?:body|html|full_text|raw_text|article_body)"\s*:',
    }
    return [label for label, pattern in checks.items() if re.search(pattern, blob, flags=re.I)]


def preflight_downgrade_blob(focus_brief: dict) -> str:
    parts: list[str] = []
    for section_name in ["source_gaps", "false_leads", "missing_assets"]:
        parts.append(json_blob(focus_brief.get(section_name) or []))
    for focus in focus_brief.get("what_market_is_watching") or []:
        if isinstance(focus, dict) and focus.get("broadcast_use") in {"drop", "talk_only"}:
            parts.append(json_blob(focus))
    return normalize(" ".join(parts)).lower()


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
    public = public_before_media_focus(markdown)
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
        ("미디어 포커스", r"미디어 포커스|보조 꼭지 후보|오늘의 이모저모"),
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
    compact_storyline_format = bool(
        re.search(r"^#{3,4}\s+슬라이드 구성", storyline, flags=re.M)
        and re.search(r"^#{3,4}\s+자료 태그", storyline, flags=re.M)
    )
    if story_count < 3:
        issue(
            findings,
            "format",
            "high",
            "추천 스토리라인 3개 미만",
            f"현재 감지된 스토리라인은 {story_count}개입니다.",
            "방송 제작자가 고를 수 있도록 서로 다른 각도의 스토리라인 3개를 유지하세요.",
        )
    if quote_count < story_count and not compact_storyline_format:
        issue(
            findings,
            "format",
            "medium",
            "스토리라인 quote 부족",
            f"스토리라인 {story_count}개 중 quote는 {quote_count}개입니다.",
            "각 스토리라인 바로 아래에 한 줄 angle을 quote block으로 넣으세요.",
        )
    if "선정 이유" not in storyline and "왜 지금" not in storyline and not compact_storyline_format:
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

    public_url_count = source_url_count(public_before_media_focus(markdown))
    if public_url_count > 0:
        issue(
            findings,
            "format",
            "low",
            "노출 URL 존재",
            f"public 본문에 Markdown 링크가 아닌 원문 URL {public_url_count}개가 노출됩니다.",
            "`[KobeissiLetter](url)`처럼 짧은 출처명 링크로 바꾸세요.",
        )

    if re.search(r"볼 포인트|Finviz 출발점|Finviz 최근 뉴스", markdown):
        issue(
            findings,
            "format",
            "low",
            "래퍼성 불릿 라벨 존재",
            "0421 포맷은 하위 내용을 바로 1-depth 불릿으로 쓰는 쪽이 더 읽기 좋습니다.",
            "`볼 포인트`, `Finviz 최근 뉴스` 같은 라벨을 제거하고 내용을 바로 쓰세요.",
        )

    return findings


def review_content_legacy_broad(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    text = markdown.lower()
    market_section = section(markdown, r"시장은 지금").lower()
    misc_section = section(markdown, r"미디어 포커스|보조 꼭지 후보|오늘의 이모저모")
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

    uses_editorial_format = bool(re.search(r"^#{3,4}\s+(선정 이유|왜 지금|쓸 자료|자료 배치|자료 태그|슬라이드 구성)", storyline, flags=re.M))
    compact_storyline_format = bool(
        re.search(r"^#{3,4}\s+슬라이드 구성", storyline, flags=re.M)
        and re.search(r"^#{3,4}\s+자료 태그", storyline, flags=re.M)
    )
    required_slots = [
        ("hook", r"^>\s+"),
        ("why_now", r"^#{3,4}\s+(선정 이유|왜 지금)"),
        ("talk_track", r"^#{3,4}\s+(짧은 말문|방송 멘트 초안)"),
    ]
    if uses_editorial_format and not compact_storyline_format:
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
            use_match = re.search(r"^#{3,4}\s+(?:쓸 자료|자료 배치|자료 태그)\s*(.*?)(?=^#{3,4}\s+|\Z)", block, flags=re.M | re.S)
            if not use_match or not re.search(r"`[^`]+`", use_match.group(1)):
                issue(
                    findings,
                    "content",
                    "medium",
                    f"스토리라인 {index} 근거 자료 누락",
                    f"{index}번 스토리라인에 `자료 태그`가 충분히 보이지 않습니다.",
                    "`2. 미디어 포커스`의 asset_id/title_tag를 code text로 연결하세요.",
                )

    evidence_usage: dict[str, set[int]] = {}
    if uses_editorial_format:
        for index, block in enumerate(blocks, start=1):
            use_match = re.search(r"^#{3,4}\s+(?:쓸 자료|자료 배치|자료 태그)\s*(.*?)(?=^#{3,4}\s+|\Z)", block, flags=re.M | re.S)
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


def review_market_focus_contract(target_date: str, markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    processed = PROCESSED_DIR / target_date
    focus_brief, focus_error = load_json(processed / "market-focus-brief.json")
    preflight_agenda, _ = load_json(processed / "market-preflight-agenda.json")
    radar, _ = load_json(processed / "market-radar.json")
    if focus_error == "missing" and "Market Focus Brief" not in markdown:
        return findings

    compact_publish = is_compact_publish_markdown(markdown)
    storyline = compact_host_area(markdown) if compact_publish else section(markdown, r"추천 스토리라인|異붿쿇 ?ㅽ넗由щ씪")
    media_focus = compact_collection_area(markdown) if compact_publish else section(markdown, r"미디어 포커스|誘몃뵒??포커스|蹂댁“ 瑗")
    public = compact_host_area(markdown) if compact_publish else public_markdown(markdown)
    public_before_media = public_before_media_focus(markdown)
    if preflight_agenda:
        raw_preflight_markers = [
            "Market Pre-flight Agenda",
            "Agenda Items",
            "collection_targets",
            "targeted_news_queries",
            "do_not_use_publicly",
            "source_gaps_to_watch",
        ]
        leaked = [marker for marker in raw_preflight_markers if marker in public_before_media]
        if leaked:
            issue(
                findings,
                "content",
                "medium",
                "PREFLIGHT-001 preflight 원문 public 노출",
                "상단 public 영역에 preflight 원문/필드가 노출됐습니다: " + ", ".join(leaked[:6]),
                "Pre-flight는 discovery layer이므로 상단에는 `Pre-flight Agenda: 정상/fallback` 상태 라벨만 남기고 원문은 audit/debug에 두세요.",
            )

    if storyline:
        direct_urls = re.findall(r"(?<!\]\()https?://\S+", storyline)
        images = re.findall(r"!\[[^\]]*]\([^)]+\)", storyline)
        long_material_lines = [
            line
            for line in storyline.splitlines()
            if len(normalize(line)) > 120 and re.search(r"https?://|Reuters|Bloomberg|CNBC|Yahoo|TradingView|Kobeissi|기사|원문|source_role|evidence_role", line, re.I)
        ]
        if direct_urls or images or len(long_material_lines) >= 2:
            issue(
                findings,
                "content",
                "medium",
                "STORY-001 스토리라인 자료 원문 과다 노출",
                f"스토리라인 섹션에 URL {len(direct_urls)}개, 이미지 {len(images)}개, 긴 자료 라인 {len(long_material_lines)}개가 노출됐습니다.",
                "스토리라인에는 방송 흐름과 `MF-... / title_tag`만 남기고 원문 제목, URL, 캡처 설명은 `2. 미디어 포커스`로 이동하세요.",
            )

        if not compact_publish:
            refs = set(re.findall(r"`(MF-[a-f0-9]{8}|MF-source-gap)`", storyline))
            media_ids = set(re.findall(r"`(MF-[a-f0-9]{8})`|^(?:#{2,4})\s+(MF-[a-f0-9]{8})", media_focus, flags=re.M))
            media_ids = {item for pair in media_ids for item in pair if item}
            missing = sorted(ref for ref in refs if ref not in media_ids)
            if not refs:
                issue(
                    findings,
                    "integrity",
                    "high",
                    "STORY-002 스토리라인 자료 태그 누락",
                    "스토리라인 섹션에서 `MF-...` 자료 태그를 찾지 못했습니다.",
                    "`2. 미디어 포커스`의 asset_id와 같은 `MF-...` 태그만 스토리라인에 참조하세요.",
                )
            elif missing:
                issue(
                    findings,
                    "integrity",
                    "high",
                    "STORY-002 미디어 포커스 asset_id 매칭 실패",
                    "스토리라인 자료 태그가 하단 미디어 포커스 asset_id와 맞지 않습니다: " + ", ".join(missing[:8]),
                    "스토리라인의 자료 태그는 반드시 `2. 미디어 포커스`에 존재하는 asset_id만 사용하세요.",
                )

    if not focus_brief:
        return findings

    summary = normalize(focus_brief.get("market_focus_summary") or "")
    if len(summary) > 80:
        issue(
            findings,
            "content",
            "medium",
            "FOCUS-001 market_focus_summary 길이 초과",
            f"market_focus_summary가 {len(summary)}자입니다.",
            "상단 노출용 summary는 80자 이하로 줄이고, 긴 판단 근거는 audit/debug에 두세요.",
        )

    focus_items = focus_brief.get("what_market_is_watching") or []
    lead = next((item for item in focus_items if item.get("broadcast_use") == "lead"), focus_items[0] if focus_items else {})
    if lead:
        lead_rank = int(lead.get("rank") or 1)
        lead_ids = [*(lead.get("evidence_ids") or []), *(lead.get("source_ids") or [])]
        has_gap = any(int(gap.get("related_focus_rank") or 0) == lead_rank for gap in focus_brief.get("source_gaps") or [])
        if not lead_ids and not has_gap:
            issue(
                findings,
                "integrity",
                "high",
                "FOCUS-002 lead focus 근거 누락",
                "lead focus에 evidence_id/source_id도 없고 연결된 source_gap도 없습니다.",
                "lead는 local evidence_id/source_id를 갖거나, public 승격 전 source_gap으로 보류되어야 합니다.",
            )

    local_ids = item_ids(radar)
    collected_blob = local_evidence_blob(radar)
    if preflight_agenda:
        for item in (preflight_agenda.get("agenda_items") or [])[:3]:
            if not isinstance(item, dict):
                continue
            fact_targets = [
                target
                for target in item.get("collection_targets") or []
                if isinstance(target, dict)
                and target.get("target_type") in {"chart", "news_search", "official_source", "market_reaction"}
            ]
            if fact_targets and not any(target_collected(target, collected_blob) for target in fact_targets):
                issue(
                    findings,
                    "integrity",
                    "medium",
                    "PREFLIGHT-003 상위 agenda fact/data 미수집",
                    f"rank {item.get('rank')} `{item.get('agenda_id')}`의 fact/data collection target이 local evidence에서 확인되지 않았습니다.",
                    "rank 1~3 preflight target의 차트, 뉴스, 공식 출처 중 최소 하나는 market-radar 또는 chart asset에 연결하세요.",
                )
        broad_queries = []
        priorities = preflight_agenda.get("collection_priorities") or {}
        for query in [*(priorities.get("targeted_news_queries") or []), *(priorities.get("targeted_x_queries") or [])]:
            if query_too_broad(str(query)):
                broad_queries.append(str(query))
        for item in preflight_agenda.get("agenda_items") or []:
            if not isinstance(item, dict):
                continue
            for target in item.get("collection_targets") or []:
                if isinstance(target, dict) and target.get("target_type") in {"news_search", "x_search", "official_source"}:
                    query = str(target.get("query_or_asset") or "")
                    if query_too_broad(query):
                        broad_queries.append(query)
        if broad_queries:
            issue(
                findings,
                "content",
                "medium",
                "PREFLIGHT-004 실행 불가능한 broad query",
                "Pre-flight suggested query가 너무 넓습니다: " + ", ".join(sorted(set(broad_queries))[:6]),
                "`stock market news` 같은 포괄 쿼리 대신 Fed/유가/기업명/출처/가격 반응을 포함한 실행 가능한 쿼리로 좁히세요.",
            )

        downgrade_blob = preflight_downgrade_blob(focus_brief)
        focus_public_blob = normalize(
            " ".join(
                json_blob(focus)
                for focus in focus_items
                if isinstance(focus, dict) and focus.get("broadcast_use") in PUBLIC_USES
            )
        ).lower()
        for item in (preflight_agenda.get("agenda_items") or [])[:3]:
            if not isinstance(item, dict) or item.get("expected_broadcast_use") not in {"lead_candidate", "supporting_candidate"}:
                continue
            same_rank_public = any(
                isinstance(focus, dict)
                and int(focus.get("rank") or 0) == int(item.get("rank") or 0)
                and focus.get("broadcast_use") in PUBLIC_USES
                for focus in focus_items
            )
            if same_rank_public:
                continue
            agenda_id = normalize(item.get("agenda_id") or "").lower()
            question_tokens = target_tokens(item.get("market_question") or "")
            overlaps_public = agenda_id and agenda_id in focus_public_blob
            overlaps_public = overlaps_public or sum(1 for token in question_tokens if token in focus_public_blob) >= 2
            mentions_downgrade = agenda_id and agenda_id in downgrade_blob
            mentions_downgrade = mentions_downgrade or sum(1 for token in question_tokens if token in downgrade_blob) >= 2
            targets = [target for target in item.get("collection_targets") or [] if isinstance(target, dict)]
            collected_as_evidence = any(target_collected(target, collected_blob) for target in targets)
            collected_as_evidence = collected_as_evidence or sum(1 for token in question_tokens if token in collected_blob) >= 2
            if collected_as_evidence:
                continue
            if not overlaps_public and not mentions_downgrade:
                issue(
                    findings,
                    "integrity",
                    "medium",
                    "FOCUS-003 preflight 충돌 downgrade reason 없음",
                    f"preflight rank {item.get('rank')} `{item.get('agenda_id')}`가 public focus로 확인되지 않았지만 source_gap/false_lead/drop 사유도 보이지 않습니다.",
                    "preflight 가설이 local evidence와 충돌하거나 수집 실패했다면 Market Focus의 source_gap, false_leads, missing_assets 중 하나에 downgrade reason을 남기세요.",
                )

    web_urls = {
        normalize(item.get("url"))
        for item in focus_brief.get("web_sources") or []
        if isinstance(item, dict) and item.get("url")
    }
    for focus in focus_items:
        if focus.get("broadcast_use") not in PUBLIC_USES:
            continue
        ids = [*(focus.get("evidence_ids") or []), *(focus.get("source_ids") or [])]
        local_hit = any(item_id in local_ids for item_id in ids)
        if preflight_agenda and not local_hit:
            issue(
                findings,
                "integrity",
                "high",
                "PREFLIGHT-002 local evidence 없는 preflight 승격",
                f"public broadcast_use={focus.get('broadcast_use')} focus가 local evidence_id/source_id 없이 승격됐습니다: {', '.join(ids[:5]) or 'no ids'}",
                "Pre-flight는 가설일 뿐이므로 local evidence에 연결되지 않으면 source_gap/drop으로 내려야 합니다.",
            )
        web_only = [item_id for item_id in ids if item_id in web_urls]
        no_local = ids and not any(item_id in local_ids for item_id in ids)
        has_related_gap = any(int(gap.get("related_focus_rank") or 0) == int(focus.get("rank") or 0) for gap in focus_brief.get("source_gaps") or [])
        if web_only or (focus_brief.get("with_web") and no_local and not has_related_gap):
            issue(
                findings,
                "integrity",
                "high",
                "WEB-001 web_search-only 근거 public 노출",
                f"public broadcast_use={focus.get('broadcast_use')} focus가 local evidence 없이 web_search 근거를 사용합니다: {', '.join((web_only or ids)[:5])}",
                "web_search로 발견한 내용은 기존 evidence_id가 없으면 source_gap으로 표시하고 public fact/lead로 노출하지 마세요.",
            )
        if preflight_agenda.get("with_web") and not local_hit:
            issue(
                findings,
                "integrity",
                "high",
                "WEB-002 preflight web_search-only public 노출",
                f"Pre-flight web_search가 켜진 상태에서 local evidence 없는 focus가 public 후보로 남았습니다: {focus.get('suggested_story_title') or focus.get('focus')}",
                "Pre-flight web_search 결과는 discovery hint이며, local evidence_id가 생기기 전에는 public fact가 아니라 source_gap이어야 합니다.",
            )

    if preflight_agenda.get("with_web"):
        web_titles = [
            normalize(item.get("title") or item.get("source") or "")
            for item in preflight_agenda.get("web_sources") or []
            if isinstance(item, dict)
        ]
        exposed = [title for title in web_titles if len(title) >= 24 and title in public]
        if exposed:
            issue(
                findings,
                "integrity",
                "high",
                "WEB-002 preflight web_search-only public 노출",
                "Pre-flight web source title이 public 영역에 직접 노출됐습니다: " + ", ".join(exposed[:3]),
                "Pre-flight web 발견은 evidence_id가 생길 때까지 source_gap/audit에만 둬야 합니다.",
            )

    prompt_payload, prompt_error = load_json(RUNTIME_PROMPT_DIR / f"{target_date}-market-focus-prompt.json")
    if not prompt_error:
        violations = raw_packet_violations(prompt_payload.get("input_payload") or {})
        if violations:
            issue(
                findings,
                "integrity",
                "high",
                "SANITIZE-001 Market Focus input raw field 포함",
                "Market Focus input packet에 sanitized policy 위반이 있습니다: " + ", ".join(violations),
                "OpenAI로 보낼 packet에는 raw URL, signed URL, local screenshot path, full article/X body를 제외하세요.",
            )
    return findings


def review_content(markdown: str) -> list[Finding]:
    findings: list[Finding] = []
    market_section = section(markdown, r"시장은 지금")
    misc_section = section(markdown, r"미디어 포커스|보조 꼭지 후보|오늘의 이모저모")
    feature_section = section(markdown, r"실적/특징주")

    if not market_section:
        issue(findings, "content", "high", "시장 섹션 없음", "`시장은 지금` 섹션을 찾지 못했습니다.", "시장 캡처와 차트를 `시장은 지금` 아래에 배치하세요.")
    if not misc_section:
        issue(findings, "content", "high", "미디어 포커스 섹션 없음", "`미디어 포커스` 섹션을 찾지 못했습니다.", "기사, X, 캡처와 source/evidence role을 `2. 미디어 포커스` 아래에 모으세요.")
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
    if is_compact_publish_markdown(markdown):
        findings = (
            review_compact_publish_contract(markdown)
            + review_headline_river_contract(args.date)
            + review_analysis_river_contract(args.date)
            + review_market_focus_contract(args.date, markdown)
            + review_evidence_microcopy_contract(args.date)
        )
    else:
        findings = (
            review_format(markdown, args.date)
            + review_content(markdown)
            + review_integrity(args.date, markdown)
            + review_headline_river_contract(args.date)
            + review_analysis_river_contract(args.date)
            + review_market_focus_contract(args.date, markdown)
            + review_evidence_microcopy_contract(args.date)
        )
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
