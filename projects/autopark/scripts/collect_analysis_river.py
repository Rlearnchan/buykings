#!/usr/bin/env python3
"""Collect/normalize Autopark analysis-layer sources into a single river."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_ROLES_PATH = PROJECT_ROOT / "config" / "source_roles_v2.yml"
ANALYSIS_ROLES = {
    "market_attention",
    "chart_context",
    "earnings_reaction",
    "earnings_context",
    "macro_chart_context",
}
ANALYSIS_SOURCE_IDS = {
    "x-kobeissiletter",
    "x-wallstengine",
    "x-lizannsonders",
    "x-charliebilello",
    "x-nicktimiraos",
    "x-zerohedge",
    "x-theeconomist",
    "isabelnet",
    "factset-insight",
}
MARKET_KEYWORDS = {
    "ai",
    "bitcoin",
    "breadth",
    "capex",
    "cloud",
    "dollar",
    "earnings",
    "fed",
    "guidance",
    "inflation",
    "jobs",
    "margin",
    "nasdaq",
    "nvidia",
    "oil",
    "pce",
    "rate",
    "s&p",
    "semiconductor",
    "treasury",
    "wti",
    "yield",
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
    notes: str = ""


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
        href = dict(attrs).get("href")
        if href:
            self.href = urllib.parse.urljoin(self.base_url, href)
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self.href:
            return
        title = clean(" ".join(self.parts), 180)
        if title:
            self.items.append({"title": title, "url": self.href})
        self.href = None
        self.parts = []


def clean(value: object, limit: int | None = None) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def clean_public_text(value: object, limit: int | None = None) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"https?\s*:\s*/\s*/\s*\S+", " ", text, flags=re.I)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text, flags=re.I)
    text = re.sub(r"\b(?:tinyurl|bit\.ly|t\.co|x)\.com/\S+", " ", text, flags=re.I)
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—·ˇ")
    if limit and len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "on"}


def parse_source_roles(path: Path = DEFAULT_ROLES_PATH) -> dict[str, SourceSpec]:
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
            specs[current_id][key] = parse_bool(value) if value.lower() in {"true", "false"} else value
    return {
        source_id: SourceSpec(
            source_id=source_id,
            label=str(row.get("label") or source_id),
            url=str(row.get("url") or ""),
            collection_method=str(row.get("collection_method") or ""),
            role=str(row.get("role") or ""),
            authority=str(row.get("authority") or "medium"),
            collection_ease=str(row.get("collection_ease") or "medium"),
            notes=str(row.get("notes") or ""),
        )
        for source_id, row in specs.items()
    }


def source_role_specs(path: Path) -> dict[str, SourceSpec]:
    return {
        key: spec
        for key, spec in parse_source_roles(path).items()
        if key in ANALYSIS_SOURCE_IDS and spec.role in ANALYSIS_ROLES
    }


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def stable_id(*parts: object) -> str:
    blob = " ".join(clean(part) for part in parts if clean(part))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


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
            "User-Agent": "Mozilla/5.0 AutoparkAnalysisRiver/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def detected_keywords(title: str, summary: str) -> list[str]:
    blob = f"{title} {summary}".lower()
    return sorted(keyword for keyword in MARKET_KEYWORDS if keyword in blob)[:12]


def make_item(
    *,
    spec: SourceSpec,
    title: str,
    url: str,
    summary: str,
    captured_at: str,
    published_at: str = "",
    content_level: str = "headline",
    image_refs: list[dict] | None = None,
) -> dict:
    title = clean_public_text(title, 180)
    summary = clean_public_text(summary or title, 420)
    item_id = f"{spec.source_id}-{stable_id(url, title, summary)}"
    return {
        "item_id": item_id,
        "source_id": spec.source_id,
        "source_label": spec.label,
        "title": title,
        "url": clean(url),
        "host": host_of(url),
        "published_at": clean(published_at, 80),
        "summary": summary,
        "collection_method": spec.collection_method,
        "content_level": content_level,
        "captured_at": captured_at,
        "source_role": spec.role,
        "source_authority": spec.authority,
        "broadcast_use": spec.notes,
        "detected_keywords": detected_keywords(title, summary),
        "image_refs": image_refs or [],
    }


def parse_rss_items(spec: SourceSpec, feed_text: str, captured_at: str, limit: int) -> list[dict]:
    root = ET.fromstring(feed_text)
    rows: list[dict] = []
    for node in root.findall(".//item"):
        title = clean(node.findtext("title"), 180)
        url = clean(node.findtext("link"))
        if not title or not url:
            continue
        description = clean_public_text(re.sub(r"<[^>]+>", " ", node.findtext("description") or ""), 300)
        published_at = clean(node.findtext("pubDate"), 80)
        if published_at:
            try:
                published_at = parsedate_to_datetime(published_at).isoformat()
            except (TypeError, ValueError, IndexError):
                pass
        rows.append(
            make_item(
                spec=spec,
                title=title,
                url=url,
                summary=description,
                captured_at=captured_at,
                published_at=published_at,
                content_level="headline+summary",
            )
        )
        if len(rows) >= limit:
            break
    return rows


def parse_html_items(spec: SourceSpec, page_text: str, captured_at: str, limit: int) -> list[dict]:
    parser = AnchorParser(spec.url)
    parser.feed(page_text)
    rows: list[dict] = []
    seen: set[str] = set()
    for anchor in parser.items:
        title = clean_public_text(anchor.get("title"), 180)
        url = clean(anchor.get("url"))
        if len(title) < 24 or url in seen:
            continue
        if host_of(url) and host_of(spec.url) and host_of(spec.url) not in host_of(url):
            continue
        rows.append(
            make_item(
                spec=spec,
                title=title,
                url=url,
                summary=title,
                captured_at=captured_at,
                content_level="headline",
            )
        )
        seen.add(url)
        if len(rows) >= limit:
            break
    return rows


def collect_web_spec(spec: SourceSpec, captured_at: str, timeout: int, limit: int) -> tuple[list[dict], dict]:
    stat = {
        "source_id": spec.source_id,
        "source_label": spec.label,
        "source_role": spec.role,
        "status": "skipped",
        "item_count": 0,
    }
    if not spec.url:
        return [], stat
    try:
        body = fetch_text(spec.url, timeout=timeout)
        if spec.collection_method == "rss" or spec.url.endswith(".xml") or "rss" in spec.url:
            rows = parse_rss_items(spec, body, captured_at, limit)
        else:
            rows = parse_html_items(spec, body, captured_at, limit)
        stat.update({"status": "ok", "item_count": len(rows)})
        return rows, stat
    except Exception as exc:  # noqa: BLE001 - collection failures must be recorded, not fatal
        stat.update({"status": "error", "error": clean(str(exc), 180)})
        return [], stat


def source_lookup_from_posts(payload: dict) -> dict[str, dict]:
    rows = {}
    for item in payload.get("source_summary") or []:
        if isinstance(item, dict) and item.get("source_id"):
            rows[item["source_id"]] = item
    return rows


def collect_existing_x_posts(processed: Path, specs: dict[str, SourceSpec], captured_at: str, limit_per_source: int) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    stats: list[dict] = []
    by_source: Counter[str] = Counter()
    seen: set[str] = set()
    for path in sorted(processed.glob("*posts.json")):
        payload = read_json(path)
        source_summary = source_lookup_from_posts(payload)
        for post in payload.get("posts") or []:
            if not isinstance(post, dict):
                continue
            source_id = post.get("source_id") or ""
            spec = specs.get(source_id)
            if not spec or by_source[source_id] >= limit_per_source:
                continue
            text = clean_public_text(post.get("text"), 420)
            title = clean_public_text(text.split("\n", 1)[0], 180)
            url = clean(post.get("url"))
            key = url or f"{source_id}:{title}"
            if not title or key in seen:
                continue
            rows.append(
                make_item(
                    spec=spec,
                    title=title,
                    url=url,
                    summary=text,
                    captured_at=post.get("captured_at") or captured_at,
                    published_at=post.get("created_at") or post.get("created_at_inferred") or "",
                    content_level="text+image" if post.get("image_refs") else "text",
                    image_refs=post.get("image_refs") or [],
                )
            )
            by_source[source_id] += 1
            seen.add(key)
    for source_id, spec in specs.items():
        if spec.collection_method != "x_profile_or_search":
            continue
        summary = source_lookup_from_posts(read_json(processed / "x-timeline-posts.json")).get(source_id, {})
        stats.append(
            {
                "source_id": source_id,
                "source_label": spec.label,
                "source_role": spec.role,
                "status": summary.get("status") or ("ok" if by_source[source_id] else "missing"),
                "item_count": by_source[source_id],
            }
        )
    return rows, stats


def collect_existing_candidates(processed: Path, specs: dict[str, SourceSpec], captured_at: str, limit_per_source: int) -> list[dict]:
    rows: list[dict] = []
    by_source: Counter[str] = Counter()
    seen: set[str] = set()
    for filename in ["today-misc-batch-a-candidates.json", "today-misc-batch-b-candidates.json"]:
        payload = read_json(processed / filename)
        for candidate in payload.get("candidates") or []:
            source_id = candidate.get("source_id") or ""
            spec = specs.get(source_id)
            if not spec or by_source[source_id] >= limit_per_source:
                continue
            title = clean_public_text(candidate.get("headline") or candidate.get("title"), 180)
            url = clean(candidate.get("url"))
            key = url or f"{source_id}:{title}"
            if not title or key in seen:
                continue
            rows.append(
                make_item(
                    spec=spec,
                    title=title,
                    url=url,
                    summary=candidate.get("summary") or candidate.get("why_it_matters") or title,
                    captured_at=candidate.get("captured_at") or captured_at,
                    published_at=candidate.get("published_at") or "",
                    content_level="headline+summary",
                    image_refs=candidate.get("image_refs") or [],
                )
            )
            by_source[source_id] += 1
            seen.add(key)
    return rows


def dedupe_items(items: list[dict], limit: int) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for item in items:
        key = clean(item.get("url")).lower() or f"{item.get('source_id')}::{clean(item.get('title')).lower()}"
        if not key or key in seen:
            continue
        rows.append(item)
        seen.add(key)
        if len(rows) >= limit:
            break
    return rows


def build_analysis_river(args: argparse.Namespace) -> dict:
    processed = PROCESSED_DIR / args.date
    captured_at = now_kst()
    specs = source_role_specs(args.source_roles)
    items: list[dict] = []
    source_stats: list[dict] = []

    x_items, x_stats = collect_existing_x_posts(processed, specs, captured_at, args.limit_per_source)
    items.extend(x_items)
    source_stats.extend(x_stats)
    items.extend(collect_existing_candidates(processed, specs, captured_at, args.limit_per_source))

    if not args.skip_fetch:
        for spec in specs.values():
            if spec.collection_method == "x_profile_or_search":
                continue
            rows, stat = collect_web_spec(spec, captured_at, args.timeout, args.limit_per_source)
            items.extend(rows)
            source_stats.append(stat)

    items = dedupe_items(items, args.overall_limit)
    role_counts = Counter(item.get("source_role") or "" for item in items)
    content_counts = Counter(item.get("content_level") or "" for item in items)
    payload = {
        "ok": True,
        "date": args.date,
        "captured_at": captured_at,
        "source": "analysis_river",
        "source_count": len(specs),
        "item_count": len(items),
        "analysis_source_ids": sorted(specs),
        "role_counts": [{"role": key, "count": value} for key, value in sorted(role_counts.items())],
        "content_level_counts": [{"content_level": key, "count": value} for key, value in sorted(content_counts.items())],
        "source_stats": source_stats,
        "items": items,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now().date().isoformat())
    parser.add_argument("--source-roles", type=Path, default=DEFAULT_ROLES_PATH)
    parser.add_argument("--limit-per-source", type=int, default=20)
    parser.add_argument("--overall-limit", type=int, default=160)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--skip-fetch", action="store_true", help="Only normalize already collected local posts/candidates.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = build_analysis_river(args)
    if not args.dry_run:
        write_json(PROCESSED_DIR / args.date / "analysis-river.json", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
