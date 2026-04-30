#!/usr/bin/env python3
"""Import Autopark today-misc source candidates from bookmarks and sources.xlsx."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOKMARKS = PROJECT_ROOT / "bookmarks_26. 4. 27..html"
DEFAULT_XLSX = PROJECT_ROOT / "sources.xlsx"
DEFAULT_OUTPUT = PROJECT_ROOT / "config" / "today_misc_sources.json"
NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FIXED_ID_BY_TITLE = {
    "주요 지수 흐름": "fixed-index-futures",
    "S&P500 히트맵": "fixed-sp500-heatmap",
    "10년물 국채금리": "fixed-us10y",
    "WTI": "fixed-wti",
    "브렌트": "fixed-brent",
    "달러 인덱스": "fixed-dollar-index",
    "원/달러": "fixed-usd-krw",
    "비트코인": "fixed-bitcoin",
    "실적발표 스케줄": "fixed-earnings-calendar",
    "공포탐욕지수": "fixed-fear-greed",
    "FED Watch": "fixed-fed-watch",
    "핀비즈-특징주": "fixed-finviz-feature-stocks",
}


@dataclass
class TodayMiscSource:
    id: str
    name: str
    url: str
    category: str
    cadence: str
    enabled: bool
    requires_login: bool
    auth_profile: str | None
    collection_method: str
    trust_level: str
    priority: int
    onboarding_batch: str
    broadcast_use: str
    source_origin: str
    selectors_or_notes: str
    user_notes: str
    onboarding_status: str


class BookmarkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attrs_dict = dict(attrs)
            self.href = attrs_dict.get("href")
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href:
            title = " ".join(" ".join(self.parts).split())
            self.links.append((title, self.href))
            self.href = None
            self.parts = []


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"^www\.", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "source"


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/") or url


def host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def classify(title: str, url: str, origin: str) -> dict:
    h = host(url)
    text = f"{title} {url}".lower()

    if origin == "sources_xlsx":
        return {
            "category": "fixed_reference",
            "cadence": "daily",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "already_modeled_elsewhere",
            "trust_level": "medium",
            "priority": 5,
            "onboarding_batch": "reference",
            "broadcast_use": "고정 시장/캡처 소스. 오늘의 이모저모 직접 대상은 아님",
        }

    if "x.com" in h or "twitter.com" in h or "threads.net" in h or "instagram.com" in h:
        return {
            "category": "x_social_signal",
            "cadence": "daily",
            "requires_login": True,
            "auth_profile": "x",
            "collection_method": "browser_profile_extract",
            "trust_level": "medium",
            "priority": 2,
            "onboarding_batch": "batch_b_special_social",
            "broadcast_use": "시장 참여자 반응, 차트/숫자 아이디어, 속보성 소재 탐색",
        }

    if any(domain in h for domain in ["reuters.com", "cnbc.com", "marketwatch.com", "finance.yahoo.com", "tradingview.com", "biztoc.com"]):
        return {
            "category": "fast_news",
            "cadence": "daily",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "html_or_rss_probe",
            "trust_level": "high" if "reuters.com" in h or "cnbc.com" in h else "medium",
            "priority": 1,
            "onboarding_batch": "batch_a_fast_news",
            "broadcast_use": "밤새 미국 증시 관련 headline 후보 수집",
        }

    if any(domain in h for domain in ["bloomberg.com", "wsj.com", "ft.com"]):
        return {
            "category": "fast_news_paywall",
            "cadence": "daily",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "headline_only_or_browser_profile",
            "trust_level": "high",
            "priority": 2,
            "onboarding_batch": "batch_a_fast_news_limited",
            "broadcast_use": "고신뢰 headline 확인, 원문은 접근 가능 범위에서만 요약",
        }

    if any(key in h for key in ["factset.com", "advisorperspectives.com", "isabelnet.com", "bilello.blog", "edwardjones.com", "hedgefundtips.com"]):
        return {
            "category": "research_chart_source",
            "cadence": "weekly_or_daily",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "html_article_probe",
            "trust_level": "medium",
            "priority": 2,
            "onboarding_batch": "batch_b_special_social",
            "broadcast_use": "방송에서 보여줄 수 있는 차트/맥락 자료 탐색",
        }

    if any(key in h for key in ["alphastreet.com", "earnings", "fxempire.com"]):
        return {
            "category": "earnings_company_event",
            "cadence": "daily_or_weekly",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "html_calendar_or_article_probe",
            "trust_level": "medium",
            "priority": 2,
            "onboarding_batch": "batch_c_earnings",
            "broadcast_use": "실적 이벤트와 회사별 스토리 후보 탐색",
        }

    if any(key in h for key in ["reddit.com", "dcinside.com", "fmkorea.com", "theqoo.net", "pann.nate.com", "flipboard.com"]):
        return {
            "category": "community_curiosity",
            "cadence": "ad_hoc",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "manual_or_browser_scan",
            "trust_level": "low",
            "priority": 4,
            "onboarding_batch": "later_community",
            "broadcast_use": "대중 관심사/아이디어 보조. 공식/뉴스 소스 확인 전 방송 근거로 쓰지 않음",
        }

    if any(key in h for key in ["finviz.com", "investing.com", "tipranks.com", "seekingalpha.com", "marketscreener.com", "etf.com", "sectorspdr.com", "financecharts.com"]):
        return {
            "category": "market_tool",
            "cadence": "daily_or_ad_hoc",
            "requires_login": False,
            "auth_profile": None,
            "collection_method": "browser_or_structured_extract",
            "trust_level": "medium",
            "priority": 3,
            "onboarding_batch": "later_market_tools",
            "broadcast_use": "시장/섹터/티커 보조 자료. 고정 차트와 중복되면 낮은 우선순위",
        }

    if "chatgpt" in text or "claude" in text or "gemini" in text or "translate" in text or "deepl" in text:
        return {
            "category": "workflow_tool",
            "cadence": "ad_hoc",
            "requires_login": True,
            "auth_profile": None,
            "collection_method": "manual_tool",
            "trust_level": "n/a",
            "priority": 5,
            "onboarding_batch": "workflow_tool",
            "broadcast_use": "수집 대상이 아니라 작업 보조 도구",
        }

    return {
        "category": "unclassified",
        "cadence": "needs_review",
        "requires_login": False,
        "auth_profile": None,
        "collection_method": "needs_user_review",
        "trust_level": "unknown",
        "priority": 5,
        "onboarding_batch": "needs_triage",
        "broadcast_use": "사용자 검토 필요",
    }


def source_id_for(title: str, url: str, origin: str, existing: set[str]) -> str:
    if origin == "sources_xlsx" and title in FIXED_ID_BY_TITLE:
        base = FIXED_ID_BY_TITLE[title]
        candidate = base
        index = 2
        while candidate in existing:
            candidate = f"{base}-{index}"
            index += 1
        existing.add(candidate)
        return candidate

    parsed_host = host(url)
    base = slugify(parsed_host.split(":")[0])
    path = slugify(urlparse(url).path.strip("/").split("/")[0]) if urlparse(url).path else ""
    if "x.com" in parsed_host or "twitter.com" in parsed_host:
        parts = [part for part in urlparse(url).path.split("/") if part]
        handle = parts[0] if parts else title
        base = f"x-{slugify(handle)}"
    elif origin == "sources_xlsx":
        base = f"fixed-{slugify(title)}"
    elif path:
        base = f"{base}-{path}"
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}-{index}"
        index += 1
    existing.add(candidate)
    return candidate


def read_bookmarks(path: Path) -> list[tuple[str, str]]:
    parser = BookmarkParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return [(title or host(url), url) for title, url in parser.links if url.startswith(("http://", "https://"))]


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings = []
    for item in root.findall("main:si", NS):
        parts = [node.text or "" for node in item.findall(".//main:t", NS)]
        strings.append("".join(parts))
    return strings


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    value = cell.find("main:v", NS)
    if value is None or value.text is None:
        inline = cell.find("main:is/main:t", NS)
        return inline.text if inline is not None and inline.text else ""
    if cell.get("t") == "s":
        return strings[int(value.text)]
    return value.text


def read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    rows: list[list[str]] = []
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheet_names = sorted(
            name for name in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", name)
        )
        if not sheet_names:
            return []
        root = ET.fromstring(zf.read(sheet_names[0]))
        for row in root.findall(".//main:sheetData/main:row", NS):
            values = [cell_value(cell, strings) for cell in row.findall("main:c", NS)]
            rows.append(values)
    if not rows:
        return []
    headers = [str(header).strip() for header in rows[0]]
    result = []
    for row in rows[1:]:
        item = {headers[index]: row[index] if index < len(row) else "" for index in range(len(headers))}
        if item.get("링크"):
            result.append(item)
    return result


def build_source(title: str, url: str, origin: str, note: str, existing_ids: set[str]) -> TodayMiscSource:
    classification = classify(title, url, origin)
    source_id = source_id_for(title, url, origin, existing_ids)
    return TodayMiscSource(
        id=source_id,
        name=html.unescape(title).strip() or host(url),
        url=url,
        category=classification["category"],
        cadence=classification["cadence"],
        enabled=False,
        requires_login=classification["requires_login"],
        auth_profile=classification["auth_profile"],
        collection_method=classification["collection_method"],
        trust_level=classification["trust_level"],
        priority=classification["priority"],
        onboarding_batch=classification["onboarding_batch"],
        broadcast_use=classification["broadcast_use"],
        source_origin=origin,
        selectors_or_notes=note,
        user_notes="",
        onboarding_status="needs_user_review",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bookmarks", type=Path, default=DEFAULT_BOOKMARKS)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    existing_ids: set[str] = set()
    seen_urls: set[str] = set()
    sources: list[TodayMiscSource] = []

    if args.bookmarks.exists():
        for title, url in read_bookmarks(args.bookmarks):
            canon = canonical_url(url)
            if canon in seen_urls:
                continue
            seen_urls.add(canon)
            sources.append(build_source(title, url, "bookmarks_html", "", existing_ids))

    if args.xlsx.exists():
        for row in read_xlsx_rows(args.xlsx):
            title = row.get("이름", "")
            url = row.get("링크", "")
            canon = canonical_url(url)
            if not url or canon in seen_urls:
                continue
            seen_urls.add(canon)
            note = " / ".join(part for part in [row.get("주기", ""), row.get("메모", "")] if part)
            sources.append(build_source(title, url, "sources_xlsx", note, existing_ids))

    payload = {
        "schema_version": 1,
        "description": "Candidate sources for Autopark section 2 오늘의 이모저모.",
        "generated_from": {
            "bookmarks": str(args.bookmarks),
            "sources_xlsx": str(args.xlsx),
        },
        "defaults": {
            "enabled": False,
            "timezone": "Asia/Seoul",
            "review_policy": "Enable only after user notes and one dry-run collection pass.",
        },
        "sources": [asdict(source) for source in sorted(sources, key=lambda item: (item.priority, item.category, item.id))],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for source in sources:
        counts[source.category] = counts.get(source.category, 0) + 1
    print(
        json.dumps(
            {"ok": True, "output": str(args.output), "source_count": len(sources), "category_counts": counts},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
