#!/usr/bin/env python3
"""Collect lightweight headline candidates for Autopark's 오늘의 이모저모."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "today_misc_sources.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
ASSETS_DIR = PROJECT_ROOT / "runtime" / "assets"
DEFAULT_SOURCE_IDS = [
    "reuters-com-source",
    "cnbc-com-world",
    "tradingview-com-news",
    "finance-yahoo-com-source",
]
DEFAULT_BATCH_B_IDS = [
    "isabelnet-com-blog",
    "insight-factset-com-source",
    "advisorperspectives-com-topic",
    "x-kobeissiletter",
    "x-investinq",
    "x-lizannsonders",
    "x-bespokeinvest",
    "x-nicktimiraos",
]
SOURCE_FEEDS = {
    "insight-factset-com-source": "https://insight.factset.com/rss.xml",
}

MARKET_KEYWORDS = {
    "ai",
    "bank",
    "bitcoin",
    "bond",
    "buyback",
    "chip",
    "crypto",
    "dollar",
    "earnings",
    "economy",
    "fed",
    "federal reserve",
    "fomc",
    "futures",
    "guidance",
    "inflation",
    "jobs",
    "market",
    "nasdaq",
    "nvidia",
    "oil",
    "pce",
    "rate",
    "recession",
    "s&p",
    "stock",
    "tariff",
    "tesla",
    "treasury",
    "trump",
    "yield",
}
TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
EXCLUDED_URL_PARTS = (
    "/personal-finance/",
    "/credit-cards/",
    "/mortgages/",
    "/loans/",
    "/banking/",
    "/video/",
)
ISABELNET_NAV_PATHS = {
    "/",
    "/about",
    "/basic-membership",
    "/blog",
    "/contact",
    "/faq",
    "/forecasting-models",
    "/legal-notice",
    "/membership-access",
    "/premium-membership",
    "/privacy-policy",
    "/pro-membership",
    "/stock-market-bull-and-bear-indicator",
    "/stock-market-equity-risk-premium",
    "/stock-market-forecasting-models",
    "/stock-market-forecasting-models-vs-us-stock-market",
    "/stock-market-long-term-forecast",
    "/stock-market-short-term-forecast",
    "/stock-market-valuation",
    "/subscribe",
    "/terms-of-use",
}
YAHOO_NEWS_PATH_PARTS = (
    "/economy/",
    "/markets/",
    "/news/",
    "/sectors/",
)


@dataclass
class Candidate:
    id: str
    headline: str
    source_id: str
    source_name: str
    url: str
    published_at: str | None
    captured_at: str
    summary: str
    why_it_matters: str
    market_hooks: list[str]
    tickers: list[str]
    evidence: list[dict]
    image_refs: list[dict]
    novelty: int
    market_relevance: int
    broadcast_fit: int
    confidence: int
    needs_user_note: bool
    score: int


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
        if tag.lower() == "a" and self.href:
            text = clean_text(" ".join(self.parts))
            if text:
                self.items.append({"title": text, "url": self.href})
            self.href = None
            self.parts = []


def parse_rss_items(feed_text: str) -> list[dict]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(feed_text)
    items = []
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title") or "")
        link = clean_text(item.findtext("link") or "")
        pub_date = clean_text(item.findtext("pubDate") or "")
        if not title or not link:
            continue
        published_at = None
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date).date().isoformat()
            except (TypeError, ValueError, IndexError):
                published_at = None
        items.append({"title": title, "url": link, "published_at": published_at})
    return items


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = [(key, value) for key, value in query if not key.lower().startswith("utm_")]
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", urllib.parse.urlencode(query), "")
    )


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 Autopark/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")
    except (TimeoutError, urllib.error.URLError):
        completed = subprocess.run(
            ["curl", "-fsSL", "--max-time", "20", url],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"curl exited {completed.returncode}")
        return completed.stdout


def extension_for_image(url: str, content_type: str | None) -> str:
    lowered_type = (content_type or "").lower()
    if "png" in lowered_type:
        return ".png"
    if "webp" in lowered_type:
        return ".webp"
    if "gif" in lowered_type:
        return ".gif"
    if "jpeg" in lowered_type or "jpg" in lowered_type:
        return ".jpg"
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-") or "asset"


def download_image(url: str, output_path: Path) -> str | None:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 Autopark/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        content_type = response.headers.get("content-type")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.read())
        return content_type


def download_candidate_images(candidates: list[Candidate], assets_dir: Path) -> None:
    for candidate in candidates:
        refs = []
        for index, image in enumerate(candidate.image_refs):
            image_url = image.get("url") or image.get("src")
            if not image_url:
                refs.append(image)
                continue
            stem = safe_filename(f"{candidate.source_id}-{candidate.id}-{index + 1}")
            provisional = assets_dir / f"{stem}.img"
            try:
                content_type = download_image(image_url, provisional)
                extension = extension_for_image(image_url, content_type)
                final_path = provisional.with_suffix(extension)
                if final_path != provisional:
                    provisional.replace(final_path)
                refs.append(
                    {
                        **image,
                        "download_status": "ok",
                        "local_path": str(final_path.relative_to(PROJECT_ROOT.parent)),
                        "content_type": content_type,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - image failures should not drop the candidate.
                refs.append({**image, "download_status": "error", "error": str(exc)})
        candidate.image_refs = refs


def extract_anchors(source: dict, page: str) -> list[dict]:
    parser = AnchorParser(source["url"])
    parser.feed(page)
    items = []
    seen = set()
    source_host = urllib.parse.urlparse(source["url"]).netloc.lower().removeprefix("www.")
    for item in parser.items:
        title = clean_text(item["title"])
        if len(title) < 18 or len(title) > 180:
            continue
        url = canonical_url(item["url"])
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if any(part in parsed.path.lower() for part in EXCLUDED_URL_PARTS):
            continue
        item_host = parsed.netloc.lower().removeprefix("www.")
        if source_host and item_host and not item_host.endswith(source_host.split(":")[0]):
            continue
        if title.lower() in {"subscribe", "sign in", "watchlist", "markets", "news"}:
            continue
        key = (title.lower(), url)
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": title, "url": url, "published_at": None})
    return items


def extract_image_urls(base_url: str, page: str) -> list[dict]:
    images = []
    seen = set()
    for match in re.finditer(r"<img\b[^>]*>", page, flags=re.IGNORECASE):
        tag = match.group(0)
        src_match = re.search(r'\b(?:src|data-src|data-lazy-src)=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
        if not src_match:
            continue
        src = html.unescape(src_match.group(1))
        if not src or src.startswith("data:"):
            continue
        url = urllib.parse.urljoin(base_url, src)
        lowered = url.lower()
        if any(token in lowered for token in ["logo", "avatar", "profile", "blank", "spinner", "gravatar"]):
            continue
        alt_match = re.search(r'\balt=["\']([^"\']*)["\']', tag, flags=re.IGNORECASE)
        alt = clean_text(alt_match.group(1)) if alt_match else ""
        key = (url, alt)
        if key in seen:
            continue
        seen.add(key)
        images.append({"url": url, "alt": alt})
    return images


def normalized_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", html.unescape(value).lower()).strip()


def matching_image_for_title(title: str, images: list[dict]) -> dict | None:
    title_label = normalized_label(title)
    if not title_label:
        return None
    for image in images:
        alt_label = normalized_label(image.get("alt", ""))
        if not alt_label:
            continue
        if alt_label in title_label or title_label in alt_label:
            return image
    title_words = {word for word in title_label.split() if len(word) >= 4}
    best = None
    best_score = 0
    for image in images:
        alt_words = {word for word in normalized_label(image.get("alt", "")).split() if len(word) >= 4}
        score = len(title_words & alt_words)
        if score > best_score:
            best = image
            best_score = score
    return best if best_score >= 3 else None


def parse_month_date(month: str, day: str, year: str) -> str | None:
    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    month_number = months.get(month[:3].lower())
    if not month_number:
        return None
    try:
        return date(int(year), month_number, int(day)).isoformat()
    except ValueError:
        return None


def extract_isabelnet_items(source: dict, page: str) -> list[dict]:
    items = []
    for item in extract_anchors(source, page):
        parsed = urllib.parse.urlparse(item["url"])
        path = parsed.path.rstrip("/") or "/"
        if parsed.query:
            continue
        if path in ISABELNET_NAV_PATHS:
            continue
        if path.startswith("/blog/page/"):
            continue
        title = item["title"]
        if title.lower() in {"recent posts", "daily blog posts", "retrieve your password"}:
            continue
        items.append(item)

    published_at = None
    match = re.search(r"\b([A-Z]{3})\s+(\d{1,2})\s+(20\d{2})\b", page, flags=re.IGNORECASE)
    if match:
        published_at = parse_month_date(match.group(1), match.group(2), match.group(3))
    if not published_at:
        match = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", page)
        if match:
            try:
                published_at = date(int(match.group(3)), int(match.group(1)), int(match.group(2))).isoformat()
            except ValueError:
                published_at = None

    if published_at:
        for item in items:
            item["published_at"] = published_at
    images = extract_image_urls(source["url"], page)
    for item in items:
        image = matching_image_for_title(item["title"], images)
        if image:
            item["image_refs"] = [image]
    return items


def extract_yahoo_items(source: dict, page: str, target_date: date) -> list[dict]:
    items = []
    for item in extract_anchors(source, page):
        parsed = urllib.parse.urlparse(item["url"])
        path = parsed.path
        if parsed.netloc.lower().removeprefix("www.") != "finance.yahoo.com":
            continue
        if path.startswith("/quote/") or path.startswith("/research-hub/") or path.startswith("/videos/"):
            continue
        if not any(part in path for part in YAHOO_NEWS_PATH_PARTS):
            continue
        title = item["title"]
        if title.lower().startswith("skip to "):
            continue
        # Yahoo's homepage renders source/time as sibling text ("Reuters · 1h ago").
        # The static anchors retain the article links, so homepage news links are treated as same-day candidates.
        item["published_at"] = target_date.isoformat()
        items.append(item)
    return items


def extract_items(source: dict, page: str, target_date: date) -> list[dict]:
    if source["id"] in SOURCE_FEEDS:
        return parse_rss_items(page)
    if source["id"] == "isabelnet-com-blog":
        return extract_isabelnet_items(source, page)
    if source["id"] == "finance-yahoo-com-source":
        return extract_yahoo_items(source, page, target_date)
    return extract_anchors(source, page)


def hooks_for_title(title: str) -> list[str]:
    lowered = title.lower()
    hooks = []
    for keyword in sorted(MARKET_KEYWORDS):
        if " " in keyword:
            matched = keyword in lowered
        else:
            matched = re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", lowered) is not None
        if matched:
            hooks.append(keyword)
    return hooks[:8]


def tickers_for_title(title: str) -> list[str]:
    stop = {"AI", "CEO", "CFO", "ETF", "Fed", "GDP", "IPO", "LLC", "NYSE", "SEC", "USA"}
    tickers = []
    for match in TICKER_RE.findall(title):
        if match in stop:
            continue
        tickers.append(match)
    return sorted(set(tickers))[:8]


def score_item(title: str, source: dict) -> tuple[int, list[str]]:
    hooks = hooks_for_title(title)
    score = len(hooks) * 2
    lowered = title.lower()
    if any(term in lowered for term in ["stock", "market", "fed", "earnings", "tariff", "ai"]):
        score += 3
    if source.get("trust_level") == "high":
        score += 2
    if source.get("category") == "fast_news":
        score += 1
    return score, hooks


def infer_item_date(item: dict, target_date: date) -> date | None:
    if item.get("published_at"):
        try:
            return date.fromisoformat(item["published_at"][:10])
        except ValueError:
            pass
    url = item.get("url", "")
    title = item.get("title", "")
    match = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", url)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    lowered = title.lower()
    if "yesterday" in lowered:
        return target_date - timedelta(days=1)
    match = re.search(r"\b(\d+)\s+hours?\s+ago\b", lowered)
    if match:
        return target_date
    match = re.search(r"\b(\d+)\s+days?\s+ago\b", lowered)
    if match:
        return target_date - timedelta(days=int(match.group(1)))
    return None


def is_recent_enough(item_date: date | None, target_date: date, lookback_hours: int) -> bool:
    if item_date is None:
        return True
    if item_date > target_date:
        return False
    earliest = target_date - timedelta(days=max(1, (lookback_hours + 23) // 24))
    return item_date >= earliest


def build_candidates(
    source: dict,
    items: list[dict],
    captured_at: str,
    target_date: date,
    limit: int,
    lookback_hours: int,
    require_recent_signal: bool,
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for index, item in enumerate(items):
        item_date = infer_item_date(item, target_date)
        if not is_recent_enough(item_date, target_date, lookback_hours):
            continue
        if require_recent_signal and item_date is None:
            continue
        score, hooks = score_item(item["title"], source)
        if score < 2:
            continue
        tickers = tickers_for_title(item["title"])
        candidate_id = f"{source['id']}-{index + 1:03d}"
        candidates.append(
            Candidate(
                id=candidate_id,
                headline=item["title"],
                source_id=source["id"],
                source_name=source["name"],
                url=item["url"],
                published_at=item_date.isoformat() if item_date else item.get("published_at"),
                captured_at=captured_at,
                summary=item["title"],
                why_it_matters="시장 관련 키워드가 감지된 headline 후보. 사용자 노하우/교차 확인 후 방송 소재로 승격한다.",
                market_hooks=hooks,
                tickers=tickers,
                evidence=[{"kind": "headline", "text": item["title"], "source_url": item["url"]}],
                image_refs=item.get("image_refs", []),
                novelty=1,
                market_relevance=min(5, max(1, score // 2)),
                broadcast_fit=2 if hooks else 1,
                confidence=3 if source.get("trust_level") == "high" else 2,
                needs_user_note=True,
                score=score,
            )
        )
    candidates.sort(key=lambda item: (-item.score, item.source_name, item.headline))
    return candidates[:limit]


def load_sources(config_path: Path, source_ids: list[str] | None, batch: str | None) -> list[dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = config.get("sources", [])
    if source_ids:
        wanted = set(source_ids)
        return [source for source in sources if source["id"] in wanted]
    if batch:
        return [source for source in sources if source.get("onboarding_batch") == batch]
    wanted = set(DEFAULT_SOURCE_IDS)
    return [source for source in sources if source["id"] in wanted]


def default_batch_b_sources(config_path: Path) -> list[dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    wanted = set(DEFAULT_BATCH_B_IDS)
    return [source for source in config.get("sources", []) if source["id"] in wanted]


def render_review(candidates: list[Candidate], target_date: str) -> str:
    lines = [
        f"# 오늘의 이모저모 후보 {target_date}",
        "",
        "자동 수집 1차 후보입니다. 각 항목은 사용자 노하우와 교차 확인 전까지 확정 소재가 아닙니다.",
        "",
    ]
    if not candidates:
        lines.append("- 후보 없음")
        return "\n".join(lines) + "\n"

    for index, candidate in enumerate(candidates, start=1):
        hook_text = ", ".join(candidate.market_hooks) if candidate.market_hooks else "미분류"
        ticker_text = ", ".join(candidate.tickers) if candidate.tickers else "-"
        lines.extend(
            [
                f"## 후보 {index}. {candidate.headline}",
                "",
                f"- 출처: [{candidate.source_name}]({candidate.url})",
                f"- 감지 키워드: {hook_text}",
                f"- 관련 티커 후보: {ticker_text}",
                f"- 이미지 후보: {len(candidate.image_refs)}",
                f"- 점수: {candidate.score}",
                "- 메모: 시장 관련 키워드가 감지된 headline 후보. 사용자가 방송 적합성/맥락을 확인해야 한다.",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--source", action="append", dest="source_ids", help="Source id to collect; can repeat")
    parser.add_argument("--batch", help="Collect all sources in an onboarding batch")
    parser.add_argument("--batch-b-default", action="store_true", help="Collect the curated Batch B starter set")
    parser.add_argument("--limit-per-source", type=int, default=8)
    parser.add_argument("--overall-limit", type=int, default=30)
    parser.add_argument("--run-name", default="today-misc", help="Output namespace for raw/processed/review files")
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--no-download-images", action="store_true", help="Do not download image_refs to runtime/assets")
    parser.add_argument(
        "--require-recent-signal",
        action="store_true",
        help="Drop items whose date cannot be inferred from URL/title text.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = default_batch_b_sources(args.config) if args.batch_b_default else load_sources(args.config, args.source_ids, args.batch)
    target_date = date.fromisoformat(args.date)
    captured_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    safe_run_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", args.run_name).strip("-") or "today-misc"
    raw_dir = RAW_DIR / args.date / safe_run_name
    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    assets_dir = ASSETS_DIR / args.date / safe_run_name
    all_candidates: list[Candidate] = []
    source_results = []

    for source in sources:
        started = time.time()
        try:
            fetch_url = SOURCE_FEEDS.get(source["id"], source["url"])
            page = fetch_text(fetch_url)
            items = extract_items(source, page, target_date)
            candidates = build_candidates(
                source,
                items,
                captured_at,
                target_date,
                args.limit_per_source,
                args.lookback_hours,
                args.require_recent_signal,
            )
            if not args.no_download_images and not args.dry_run:
                download_candidate_images(candidates, assets_dir)
            source_results.append(
                {
                    "source_id": source["id"],
                    "name": source["name"],
                    "url": source["url"],
                    "status": "ok",
                    "raw_link_count": len(items),
                    "candidate_count": len(candidates),
                    "elapsed_seconds": round(time.time() - started, 2),
                }
            )
            all_candidates.extend(candidates)
            if not args.dry_run:
                raw_dir.mkdir(parents=True, exist_ok=True)
                (raw_dir / f"{source['id']}.json").write_text(
                    json.dumps(
                        {
                            "source": source,
                            "fetch_url": fetch_url,
                            "captured_at": captured_at,
                            "raw_link_count": len(items),
                            "items": items[:100],
                            "candidates": [asdict(candidate) for candidate in candidates],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
        except Exception as exc:  # noqa: BLE001 - source failures should not stop the batch.
            source_results.append(
                {
                    "source_id": source["id"],
                    "name": source["name"],
                    "url": source["url"],
                    "status": "error",
                    "error": str(exc),
                    "elapsed_seconds": round(time.time() - started, 2),
                }
            )

    deduped: dict[str, Candidate] = {}
    for candidate in all_candidates:
        key = canonical_url(candidate.url)
        if key not in deduped or candidate.score > deduped[key].score:
            deduped[key] = candidate
    ranked = sorted(deduped.values(), key=lambda item: (-item.score, item.source_name, item.headline))[
        : args.overall_limit
    ]

    payload = {
        "ok": True,
        "target_date": args.date,
        "run_name": safe_run_name,
        "captured_at": captured_at,
        "source_results": source_results,
        "lookback_hours": args.lookback_hours,
        "require_recent_signal": args.require_recent_signal,
        "assets_path": str(assets_dir.relative_to(PROJECT_ROOT.parent)) if not args.no_download_images else None,
        "candidates": [asdict(candidate) for candidate in ranked],
    }
    if not args.dry_run:
        processed_dir.mkdir(parents=True, exist_ok=True)
        notion_dir.mkdir(parents=True, exist_ok=True)
        candidates_name = "today-misc-candidates.json" if safe_run_name == "today-misc" else f"{safe_run_name}-candidates.json"
        review_name = "today-misc-review.md" if safe_run_name == "today-misc" else f"{safe_run_name}-review.md"
        (processed_dir / candidates_name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (notion_dir / review_name).write_text(
            render_review(ranked, args.date),
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
