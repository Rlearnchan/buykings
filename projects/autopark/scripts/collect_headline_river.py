#!/usr/bin/env python3
"""Collect the broad headline river for Autopark post-MVP source upgrades."""

from __future__ import annotations

import argparse
import os
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
DEFAULT_ROLES_PATH = PROJECT_ROOT / "config" / "source_roles_v2.yml"

BASELINE_SOURCE_IDS = ["yahoo-finance-ticker-rss"]
HEADLINE_X_SOURCE_IDS = ["x-reuters", "x-bloomberg", "x-cnbc", "x-wsj", "x-ft", "x-marketwatch"]
FALLBACK_SOURCE_IDS = ["biztoc-api", "biztoc-feed", "biztoc-home", "finviz-news"]
SUPPORT_SOURCE_IDS = []
MARKET_KEYWORDS = {
    "ai",
    "amazon",
    "apple",
    "bitcoin",
    "bond",
    "brent",
    "capex",
    "chip",
    "cloud",
    "crypto",
    "dollar",
    "dow",
    "earnings",
    "fed",
    "fomc",
    "guidance",
    "hormuz",
    "inflation",
    "jobs",
    "market",
    "microsoft",
    "nasdaq",
    "nvidia",
    "oil",
    "pce",
    "rate",
    "russell",
    "semiconductor",
    "s&p",
    "tariff",
    "treasury",
    "trump",
    "wti",
    "yield",
}

AGENDA_TICKER_MAP = {
    "rates_dollar": ["^TNX", "DX-Y.NYB", "TLT", "IEF", "KRE", "XLF"],
    "rate": ["^TNX", "DX-Y.NYB", "TLT", "IEF", "KRE", "XLF"],
    "dollar": ["DX-Y.NYB", "KRW=X", "UUP", "^TNX"],
    "oil": ["CL=F", "BZ=F", "XLE", "CVX", "XOM", "OIH"],
    "energy": ["CL=F", "BZ=F", "XLE", "CVX", "XOM", "OIH"],
    "ai": ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "AVGO", "AMD", "SMCI", "VRT", "CEG"],
    "capex": ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "AVGO", "AMD", "SMCI", "VRT", "CEG"],
    "breadth": ["^GSPC", "^IXIC", "^DJI", "^RUT", "RSP", "IWM", "QQQ", "SPY"],
    "equity": ["^GSPC", "^IXIC", "^DJI", "^RUT", "RSP", "IWM", "QQQ", "SPY"],
    "earnings": ["AMD", "PLTR", "SMCI", "ARM", "DIS", "UBER", "SHOP", "AMZN", "MSFT"],
    "guidance": ["AMD", "PLTR", "SMCI", "ARM", "DIS", "UBER", "SHOP", "AMZN", "MSFT"],
    "korea": ["EWY", "TSM", "ASML", "SOXX", "SMH", "KRW=X"],
    "transmission": ["EWY", "TSM", "ASML", "SOXX", "SMH", "KRW=X"],
    "crypto": ["BTC-USD", "ETH-USD", "COIN", "MSTR", "IBIT"],
    "bitcoin": ["BTC-USD", "ETH-USD", "COIN", "MSTR", "IBIT"],
}


@dataclass
class SourceSpec:
    source_id: str
    label: str
    url: str
    collection_method: str
    role: str
    authority: str
    collection_ease: str
    always_collect: bool
    notes: str = ""


@dataclass
class HeadlineItem:
    item_id: str
    source_id: str
    source_label: str
    publisher: str
    title: str
    url: str
    host: str
    published_at: str
    snippet: str
    collection_method: str
    content_level: str
    captured_at: str
    source_role: str
    source_authority: str
    agenda_links: list[str]
    detected_keywords: list[str]


class AnchorParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.items: list[dict] = []
        self.href: str | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.href = urllib.parse.urljoin(self.base_url, href)
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self.href:
            return
        title = clean_text(" ".join(self.parts))
        if title:
            self.items.append({"title": title, "url": self.href})
        self.href = None
        self.parts = []


def clean_text(value: object, limit: int | None = None) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def host_of(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def fetch_text(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 AutoparkHeadlineRiver/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_rapidapi_json(url: str, timeout: int = 30) -> object:
    api_key = os.environ.get("BIZTOC_RAPIDAPI_KEY") or os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        raise RuntimeError("missing BIZTOC_RAPIDAPI_KEY or RAPIDAPI_KEY")
    parsed = urllib.parse.urlparse(url)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": parsed.netloc or "biztoc.p.rapidapi.com",
            "User-Agent": "Mozilla/5.0 AutoparkHeadlineRiver/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "on"}


def parse_source_roles(path: Path = DEFAULT_ROLES_PATH) -> dict[str, SourceSpec]:
    """Parse the limited source registry shape without adding a YAML dependency."""
    specs: dict[str, dict] = {}
    current_id: str | None = None
    in_sources = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        if raw_line.startswith("sources:"):
            in_sources = True
            current_id = None
            continue
        if not in_sources:
            continue
        if re.match(r"^[a-zA-Z_].*:", raw_line):
            break
        match = re.match(r"^  ([a-zA-Z0-9_-]+):\s*$", raw_line)
        if match:
            current_id = match.group(1)
            specs[current_id] = {}
            continue
        match = re.match(r"^    ([a-zA-Z0-9_-]+):\s*(.*)$", raw_line)
        if match and current_id:
            key, value = match.group(1), match.group(2).strip()
            value = value.strip('"').strip("'")
            if value.lower() in {"true", "false"}:
                specs[current_id][key] = parse_bool(value)
            else:
                specs[current_id][key] = value
    return {
        source_id: SourceSpec(
            source_id=source_id,
            label=str(row.get("label") or source_id),
            url=str(row.get("url") or ""),
            collection_method=str(row.get("collection_method") or "html"),
            role=str(row.get("role") or "support_context"),
            authority=str(row.get("authority") or "medium"),
            collection_ease=str(row.get("collection_ease") or "medium"),
            always_collect=bool(row.get("always_collect")),
            notes=str(row.get("notes") or ""),
        )
        for source_id, row in specs.items()
        if row.get("url")
    }


def parse_rss_items(source: SourceSpec, feed_text: str, captured_at: str, agenda_links: list[str]) -> list[HeadlineItem]:
    root = ET.fromstring(feed_text)
    items: list[HeadlineItem] = []
    for index, item in enumerate(root.findall(".//item"), start=1):
        title = clean_text(item.findtext("title"), 180)
        url = clean_text(item.findtext("link"))
        if not title or not url:
            continue
        description = clean_text(re.sub(r"<[^>]+>", " ", item.findtext("description") or ""), 300)
        pub_date = clean_text(item.findtext("pubDate"), 80)
        published_at = pub_date
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date).isoformat()
            except (TypeError, ValueError, IndexError):
                published_at = pub_date
        source_node = item.find("source")
        publisher = clean_text(source_node.text if source_node is not None else "", 80)
        items.append(
            make_item(
                source,
                index,
                title,
                url,
                captured_at,
                publisher=publisher,
                published_at=published_at,
                snippet=description,
                agenda_links=agenda_links,
            )
        )
    return items


def iter_biztoc_api_rows(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ["items", "articles", "data", "news", "results"]:
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def parse_rapidapi_items(source: SourceSpec, payload: object, captured_at: str, limit: int) -> list[HeadlineItem]:
    items: list[HeadlineItem] = []
    for index, row in enumerate(iter_biztoc_api_rows(payload), start=1):
        title = clean_text(row.get("title") or row.get("headline") or row.get("name"), 180)
        url = clean_text(row.get("url") or row.get("link") or row.get("source_url"))
        if not title or not url:
            continue
        snippet = clean_text(row.get("summary") or row.get("description") or row.get("snippet") or "", 300)
        published_at = clean_text(row.get("published_at") or row.get("published") or row.get("date") or row.get("time"), 80)
        publisher = clean_text(row.get("source") or row.get("publisher") or row.get("domain") or "", 80)
        items.append(
            make_item(
                source,
                index,
                title,
                url,
                captured_at,
                publisher=publisher,
                published_at=published_at,
                snippet=snippet,
            )
        )
        if len(items) >= limit:
            break
    return items


def source_specific_keep(source_id: str, title: str, url: str) -> bool:
    lowered = title.lower()
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    host = host_of(url)
    low_signal_phrases = {
        "about us",
        "advertise",
        "dark mode",
        "customize news grid",
        "editor's picks",
        "editors' picks",
        "newsletter",
        "news flow",
        "podcast",
        "portfolio",
        "prediction markets",
        "privacy policy",
        "pro watchlist",
        "skip navigation",
        "sign in",
        "subscribe",
        "terms of service",
        "watch live",
    }
    nav_titles = {
        "home",
        "screener",
        "charts",
        "maps",
        "groups",
        "portfolio",
        "insider",
        "futures",
        "forex",
        "crypto",
        "calendar",
        "pricing",
        "theme",
        "help",
        "login",
        "register",
        "market news",
        "market pulse",
        "stocks news",
        "etf news",
        "crypto news",
        "financial news",
        "trending tickers",
        "subscribe",
        "sign in",
        "watchlist",
        "markets",
        "news",
        "calendars",
        "europe markets",
        "latest news",
        "news flow",
        "settings",
    }
    if lowered.startswith("skip to ") or lowered in nav_titles:
        return False
    if any(phrase in lowered for phrase in low_signal_phrases):
        return False
    if len(title) < 14 or len(title) > 220:
        return False
    if source_id == "finviz-news":
        if host_of(url) == "finviz.com" and not path.startswith("/news/"):
            return False
        if re.search(r"/(quote|screener|login|register|elite|calendar|map|groups|portfolio|futures|forex|crypto)", url):
            return False
    if source_id.startswith("biztoc"):
        if re.search(r"/(account|login|upgrade|about|privacy|settings|newsletter)", url):
            return False
        if host == "finance.yahoo.com" and path.startswith("/quote/"):
            return False
        if any(phrase in lowered for phrase in {"customize", "settings", "upgrade", "dark mode"}):
            return False
    if source_id == "cnbc-world":
        if "cnbc.com" not in host:
            return False
        if not path.endswith(".html"):
            return False
    if source_id == "tradingview-news" and any(phrase in lowered for phrase in {"economic calendar", "markets", "news flow"}):
        return False
    return True


def parse_html_items(source: SourceSpec, page_text: str, captured_at: str) -> list[HeadlineItem]:
    parser = AnchorParser(source.url)
    parser.feed(page_text)
    items: list[HeadlineItem] = []
    seen: set[tuple[str, str]] = set()
    for raw in parser.items:
        title = clean_text(raw.get("title"), 180)
        url = clean_text(raw.get("url"))
        key = (title.lower(), url)
        if key in seen or not source_specific_keep(source.source_id, title, url):
            continue
        seen.add(key)
        items.append(make_item(source, len(items) + 1, title, url, captured_at))
    return items


def make_item(
    source: SourceSpec,
    index: int,
    title: str,
    url: str,
    captured_at: str,
    publisher: str = "",
    published_at: str = "",
    snippet: str = "",
    agenda_links: list[str] | None = None,
) -> HeadlineItem:
    blob = f"{title} {snippet}".lower()
    keywords = sorted(keyword for keyword in MARKET_KEYWORDS if keyword in blob)[:12]
    return HeadlineItem(
        item_id=f"{source.source_id}-{index:03d}",
        source_id=source.source_id,
        source_label=source.label,
        publisher=publisher,
        title=clean_text(title, 180),
        url=url,
        host=host_of(url),
        published_at=published_at,
        snippet=clean_text(snippet, 300),
        collection_method=source.collection_method,
        content_level="headline+summary" if snippet else "headline",
        captured_at=captured_at,
        source_role=source.role,
        source_authority=source.authority,
        agenda_links=agenda_links or [],
        detected_keywords=keywords,
    )


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def ticker_key_for_agenda(item: dict) -> list[str]:
    text = " ".join(
        str(item.get(key) or "")
        for key in ["agenda_id", "market_question", "why_to_check", "expected_broadcast_use"]
    ).lower()
    tickers: list[str] = []
    for key, values in AGENDA_TICKER_MAP.items():
        if key in text:
            for ticker in values:
                if ticker not in tickers:
                    tickers.append(ticker)
    return tickers


def agenda_expansions(preflight: dict, max_agendas: int = 6) -> list[dict]:
    expansions = []
    for item in (preflight.get("agenda_items") or [])[:max_agendas]:
        tickers = ticker_key_for_agenda(item)
        if not tickers:
            continue
        expansions.append(
            {
                "agenda_id": item.get("agenda_id") or f"agenda_{len(expansions) + 1}",
                "rank": item.get("rank") or len(expansions) + 1,
                "tickers": tickers[:12],
                "url": yahoo_rss_url(tickers[:12]),
            }
        )
    return expansions


def yahoo_rss_url(tickers: list[str]) -> str:
    encoded = urllib.parse.quote(",".join(tickers), safe="")
    return f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={encoded}"


def collect_source(source: SourceSpec, captured_at: str, limit: int, timeout: int, agenda_links: list[str] | None = None) -> tuple[list[HeadlineItem], dict]:
    started = datetime.now()
    try:
        if source.collection_method == "rapidapi_json":
            payload = fetch_rapidapi_json(source.url, timeout)
            items = parse_rapidapi_items(source, payload, captured_at, limit)
        else:
            text = fetch_text(source.url, timeout)
            if source.collection_method == "rss":
                items = parse_rss_items(source, text, captured_at, agenda_links or [])
            else:
                items = parse_html_items(source, text, captured_at)
        items = items[:limit]
        return items, {
            "source_id": source.source_id,
            "source_label": source.label,
            "status": "ok",
            "item_count": len(items),
            "source_role": source.role,
            "authority": source.authority,
            "collection_method": source.collection_method,
            "elapsed_seconds": elapsed_seconds(started),
        }
    except RuntimeError as exc:
        status = "missing_key" if "BIZTOC_RAPIDAPI_KEY" in str(exc) or "RAPIDAPI_KEY" in str(exc) else "error"
        return [], {
            "source_id": source.source_id,
            "source_label": source.label,
            "status": status,
            "error": str(exc),
            "item_count": 0,
            "source_role": source.role,
            "authority": source.authority,
            "collection_method": source.collection_method,
            "elapsed_seconds": elapsed_seconds(started),
        }
    except Exception as exc:  # noqa: BLE001 - source failures should not stop the river.
        return [], {
            "source_id": source.source_id,
            "source_label": source.label,
            "status": "error",
            "error": str(exc),
            "item_count": 0,
            "source_role": source.role,
            "authority": source.authority,
            "collection_method": source.collection_method,
            "elapsed_seconds": elapsed_seconds(started),
        }


def collect_existing_x_posts(
    processed: Path,
    roles: dict[str, SourceSpec],
    captured_at: str,
    limit_per_source: int,
    wanted_source_ids: list[str],
) -> tuple[list[HeadlineItem], list[dict]]:
    rows: list[HeadlineItem] = []
    stats: list[dict] = []
    by_source: Counter[str] = Counter()
    seen: set[str] = set()
    wanted = set(wanted_source_ids)
    for path in sorted(processed.glob("*posts.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for post in payload.get("posts") or []:
            if not isinstance(post, dict):
                continue
            source_id = post.get("source_id") or ""
            if source_id not in wanted or by_source[source_id] >= limit_per_source:
                continue
            source = roles.get(source_id)
            if not source:
                continue
            text = clean_text(post.get("text"), 300)
            title = clean_text(text.split("\n", 1)[0], 180)
            url = clean_text(post.get("url"))
            key = url or f"{source_id}:{title.lower()}"
            if not title or key in seen:
                continue
            rows.append(
                make_item(
                    source,
                    by_source[source_id] + 1,
                    title,
                    url,
                    post.get("captured_at") or captured_at,
                    published_at=post.get("created_at") or post.get("created_at_inferred") or "",
                    snippet=text,
                )
            )
            by_source[source_id] += 1
            seen.add(key)
    for source_id in wanted_source_ids:
        source = roles.get(source_id)
        if not source:
            stats.append({"source_id": source_id, "status": "missing_config", "item_count": 0})
            continue
        stats.append(
            {
                "source_id": source_id,
                "source_label": source.label,
                "status": "ok" if by_source[source_id] else "missing",
                "item_count": by_source[source_id],
                "source_role": source.role,
                "authority": source.authority,
                "collection_method": source.collection_method,
                "elapsed_seconds": 0.0,
            }
        )
    return rows, stats


def elapsed_seconds(started: datetime) -> float:
    return round((datetime.now() - started).total_seconds(), 2)


def dedupe_items(items: list[HeadlineItem]) -> list[HeadlineItem]:
    deduped: list[HeadlineItem] = []
    seen: set[str] = set()
    for item in items:
        key = canonical_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def balanced_limit(items: list[HeadlineItem], limit: int) -> list[HeadlineItem]:
    if limit <= 0 or len(items) <= limit:
        return items[:limit]
    sources: list[str] = []
    buckets: dict[str, list[HeadlineItem]] = {}
    for item in items:
        source_id = item.source_id
        if source_id not in buckets:
            sources.append(source_id)
            buckets[source_id] = []
        buckets[source_id].append(item)
    rows: list[HeadlineItem] = []
    while len(rows) < limit:
        added = False
        for source_id in sources:
            bucket = buckets[source_id]
            if not bucket:
                continue
            rows.append(bucket.pop(0))
            added = True
            if len(rows) >= limit:
                break
        if not added:
            break
    return rows


def canonical_key(item: HeadlineItem) -> str:
    parsed = urllib.parse.urlparse(item.url)
    path = parsed.path.rstrip("/")
    return f"{item.title.lower()} {parsed.netloc.lower()}{path}"


def anomaly_summary(items: list[HeadlineItem], source_ids: set[str]) -> dict:
    rows = [item for item in items if item.source_id in source_ids]
    keyword_counts = Counter(keyword for item in rows for keyword in item.detected_keywords)
    host_counts = Counter(item.host for item in rows if item.host)
    title_tokens = Counter()
    for item in rows:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9&.-]{2,}", item.title):
            lowered = token.lower().strip(".")
            if lowered in {"the", "and", "for", "with", "from", "this", "that", "says", "news"}:
                continue
            title_tokens[lowered] += 1
    return {
        "source_ids": sorted(source_ids),
        "item_count": len(rows),
        "top_keywords": [{"keyword": key, "count": count} for key, count in keyword_counts.most_common(20)],
        "top_hosts": [{"host": key, "count": count} for key, count in host_counts.most_common(20)],
        "top_title_tokens": [{"token": key, "count": count} for key, count in title_tokens.most_common(30)],
    }


def render_review(payload: dict) -> str:
    lines = [
        "# Headline River",
        "",
        f"- date: `{payload['date']}`",
        f"- generated_at: `{payload['generated_at']}`",
        f"- item_count: `{payload['item_count']}`",
        "",
        "## Source Stats",
        "",
        "| source | status | role | count | note |",
        "|---|---:|---|---:|---|",
    ]
    for stat in payload.get("source_stats") or []:
        note = stat.get("error") or ""
        lines.append(f"| {stat.get('source_label')} | {stat.get('status')} | {stat.get('source_role')} | {stat.get('item_count')} | {note} |")
    lines.extend(["", "## BizToc Anomaly Summary", ""])
    anomaly = payload.get("anomaly_summary") or {}
    lines.append("- top_keywords: " + ", ".join(f"{row['keyword']}({row['count']})" for row in (anomaly.get("top_keywords") or [])[:12]))
    lines.append("- top_hosts: " + ", ".join(f"{row['host']}({row['count']})" for row in (anomaly.get("top_hosts") or [])[:12]))
    lines.extend(["", "## Sample Items", ""])
    for item in (payload.get("items") or [])[:30]:
        source = item.get("source_label")
        title = item.get("title")
        url = item.get("url")
        lines.append(f"- [{source}] [{title}]({url})")
    return "\n".join(lines) + "\n"


def build_headline_river(args: argparse.Namespace) -> dict:
    roles = parse_source_roles(args.source_roles)
    preflight = load_json(PROCESSED_DIR / args.date / "market-preflight-agenda.json")
    processed = PROCESSED_DIR / args.date
    captured_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    wanted = list(BASELINE_SOURCE_IDS)
    if args.include_support:
        wanted.extend(SUPPORT_SOURCE_IDS)
    all_items: list[HeadlineItem] = []
    source_stats: list[dict] = []

    for source_id in wanted:
        source = roles.get(source_id)
        if not source:
            source_stats.append({"source_id": source_id, "status": "missing_config", "item_count": 0})
            continue
        items, stat = collect_source(source, captured_at, args.limit_per_source, args.timeout)
        all_items.extend(items)
        source_stats.append(stat)

    expansions = agenda_expansions(preflight)
    if not args.skip_agenda_expansion:
        base = roles.get("yahoo-finance-ticker-rss")
        for expansion in expansions:
            if not base:
                continue
            expanded = SourceSpec(
                source_id=f"yahoo-agenda-{expansion['agenda_id']}",
                label=f"Yahoo Agenda RSS: {expansion['agenda_id']}",
                url=expansion["url"],
                collection_method="rss",
                role="agenda_deepening",
                authority=base.authority,
                collection_ease=base.collection_ease,
                always_collect=False,
                notes="Pre-flight agenda-linked Yahoo ticker RSS expansion.",
            )
            items, stat = collect_source(
                expanded,
                captured_at,
                args.limit_per_source,
                args.timeout,
                agenda_links=[str(expansion["agenda_id"])],
            )
            all_items.extend(items)
            source_stats.append({**stat, "agenda_id": expansion["agenda_id"], "tickers": expansion["tickers"]})

    x_items, x_stats = collect_existing_x_posts(processed, roles, captured_at, args.limit_per_source, HEADLINE_X_SOURCE_IDS)
    all_items.extend(x_items)
    source_stats.extend(x_stats)

    for source_id in FALLBACK_SOURCE_IDS:
        source = roles.get(source_id)
        if not source:
            source_stats.append({"source_id": source_id, "status": "missing_config", "item_count": 0})
            continue
        items, stat = collect_source(source, captured_at, args.limit_per_source, args.timeout)
        all_items.extend(items)
        source_stats.append(stat)

    items = balanced_limit(dedupe_items(all_items), args.overall_limit)
    payload = {
        "ok": True,
        "date": args.date,
        "generated_at": captured_at,
        "source_roles_path": str(args.source_roles),
        "item_count": len(items),
        "baseline_source_ids": BASELINE_SOURCE_IDS,
        "headline_x_source_ids": HEADLINE_X_SOURCE_IDS,
        "fallback_source_ids": FALLBACK_SOURCE_IDS,
        "support_source_ids": SUPPORT_SOURCE_IDS if args.include_support else [],
        "agenda_expansions": expansions,
        "source_stats": source_stats,
        "anomaly_summary": anomaly_summary(items, {"biztoc-api", "biztoc-feed", "biztoc-home"}),
        "items": [asdict(item) for item in items],
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--source-roles", type=Path, default=DEFAULT_ROLES_PATH)
    parser.add_argument("--limit-per-source", type=int, default=80)
    parser.add_argument("--overall-limit", type=int, default=300)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--include-support", action="store_true", help="Collect CNBC and TradingView support sources.")
    parser.add_argument("--skip-agenda-expansion", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_headline_river(args)
    if not args.dry_run:
        output = args.output or (PROCESSED_DIR / args.date / "headline-river.json")
        markdown = args.markdown_output or (RUNTIME_NOTION_DIR / args.date / "headline-river.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        markdown.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown.write_text(render_review(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "date": args.date,
                "item_count": payload["item_count"],
                "source_count": len(payload["source_stats"]),
                "agenda_expansion_count": len(payload["agenda_expansions"]),
                "output": str(args.output or (PROCESSED_DIR / args.date / "headline-river.json")),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
