#!/usr/bin/env python3
"""Build lightweight visual cards from collected image sources without vision calls."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from caption_visual_assets import PROJECT_ROOT, REPO_ROOT, load_env


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
DEFAULT_ENV = REPO_ROOT / ".env"
BOILERPLATE_PHRASES = [
    "advanced stock market forecast for professionals and individuals",
    "advanced stock market forecast for professional and individual",
]
VISUAL_REASONING_SOURCES = {
    "isabelnet",
}
VISUAL_REASONING_KEYWORDS = {
    "allocation",
    "breadth",
    "capex",
    "channel",
    "chart",
    "consumer",
    "credit",
    "earnings",
    "estimate",
    "fed",
    "flow",
    "fund",
    "inflation",
    "margin",
    "positioning",
    "rate",
    "recession",
    "revision",
    "sentiment",
    "spread",
    "survey",
    "yield",
    "가이던스",
    "금리",
    "마진",
    "밸류에이션",
    "서베이",
    "센티먼트",
    "스프레드",
    "실적",
    "인플레",
    "지표",
    "차트",
    "포지셔닝",
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


class PageTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta_description = ""
        self.in_paragraph = False
        self.current_parts: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        lowered = tag.lower()
        if lowered == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                content = clean_text(attrs_dict.get("content", ""))
                if content and not self.meta_description:
                    self.meta_description = content
        elif lowered == "p":
            self.in_paragraph = True
            self.current_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_paragraph:
            self.current_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "p" or not self.in_paragraph:
            return
        text = clean_text(" ".join(self.current_parts))
        if len(text) >= 40:
            self.paragraphs.append(text)
        self.current_parts = []
        self.in_paragraph = False


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_page(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 Autopark/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def page_summary(url: str, cache_dir: Path, use_cache: bool) -> dict:
    cache_path = cache_dir / (re.sub(r"[^a-zA-Z0-9_-]+", "-", url).strip("-")[:120] + ".html")
    html_text = ""
    status = "ok"
    error = None
    if use_cache and cache_path.exists():
        html_text = cache_path.read_text(encoding="utf-8", errors="replace")
        status = "cached"
    else:
        try:
            html_text = fetch_page(url)
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(html_text, encoding="utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            status = "error"
            error = str(exc)

    parser = PageTextParser()
    if html_text:
        parser.feed(html_text)
    meaningful_paragraphs = [
        paragraph
        for paragraph in parser.paragraphs
        if paragraph.lower() not in BOILERPLATE_PHRASES
    ]
    meta = "" if parser.meta_description.lower() in BOILERPLATE_PHRASES else parser.meta_description
    description = meta or (meaningful_paragraphs[0] if meaningful_paragraphs else "")
    return {
        "status": status,
        "error": error,
        "description": description,
        "paragraphs": meaningful_paragraphs[:3],
        "cache_path": str(cache_path.relative_to(REPO_ROOT)) if cache_path.exists() else None,
    }


def vision_lookup(target_date: str) -> dict[str, dict]:
    payload = load_json(PROCESSED_DIR / target_date / "image-intel.json")
    lookup = {}
    for result in payload.get("results", []):
        asset = result.get("asset") or {}
        headline = asset.get("headline")
        source_url = asset.get("source_url")
        caption = result.get("caption") or {}
        key_parts = [asset.get("asset_id"), headline, source_url]
        for key in key_parts:
            if key:
                lookup[str(key)] = {
                    "status": result.get("status"),
                    "main_claim_ko": caption.get("main_claim_ko"),
                    "broadcast_hook_ko": caption.get("broadcast_hook_ko"),
                    "caveats": caption.get("caveats") or [],
                }
    return lookup


def visual_reasoning_signal(candidate: dict, image: dict, description: str, vision: dict) -> tuple[bool, list[str]]:
    reasons = []
    source_name = (candidate.get("source_name") or candidate.get("source_id") or "").lower()
    combined = " ".join(
        str(value or "")
        for value in [
            candidate.get("headline"),
            candidate.get("summary"),
            description,
            image.get("alt"),
            image.get("url") or image.get("src"),
        ]
    ).lower()
    if any(source in source_name for source in VISUAL_REASONING_SOURCES):
        reasons.append("special_visual_source")
    if any(keyword in combined for keyword in VISUAL_REASONING_KEYWORDS):
        reasons.append("chart_or_market_keyword")
    if image.get("local_path") and len(clean_text(description)) < 80:
        reasons.append("weak_surrounding_text")
    if vision:
        reasons.append("vision_caption_available")
    return bool(reasons), reasons


def build_cards(target_date: str, fetch_descriptions: bool, use_cache: bool) -> tuple[list[dict], dict]:
    processed = PROCESSED_DIR / target_date
    batch_b = load_json(processed / "today-misc-batch-b-candidates.json")
    lookup = vision_lookup(target_date)
    cache_dir = PROJECT_ROOT / "data" / "raw" / target_date / "visual-card-pages"
    cards = []
    stats = {"candidate_count": 0, "image_count": 0, "fetched_pages": 0, "fetch_errors": 0}

    for candidate in batch_b.get("candidates", []):
        image_refs = candidate.get("image_refs") or []
        if not image_refs:
            continue
        stats["candidate_count"] += 1
        stats["image_count"] += len(image_refs)
        page_info = {"status": "skipped", "description": "", "paragraphs": []}
        if fetch_descriptions and candidate.get("url"):
            page_info = page_summary(candidate["url"], cache_dir, use_cache)
            if page_info["status"] == "error":
                stats["fetch_errors"] += 1
            else:
                stats["fetched_pages"] += 1

        vision = lookup.get(candidate.get("id") or "") or lookup.get(candidate.get("headline") or "") or lookup.get(candidate.get("url") or "") or {}
        description = page_info.get("description") or candidate.get("summary") or ""
        for index, image in enumerate(image_refs, start=1):
            needs_reasoning, reasoning_reasons = visual_reasoning_signal(candidate, image, description, vision)
            cards.append(
                {
                    "id": f"{candidate.get('id')}-visual-{index}",
                    "candidate_id": candidate.get("id"),
                    "source_id": candidate.get("source_id"),
                    "source_name": candidate.get("source_name"),
                    "title": candidate.get("headline"),
                    "url": candidate.get("url"),
                    "published_at": candidate.get("published_at"),
                    "description": description,
                    "description_source": "page" if page_info.get("description") else "candidate_summary",
                    "page_paragraphs": page_info.get("paragraphs") or [],
                    "image_alt": image.get("alt") or "",
                    "image_url": image.get("url") or image.get("src") or "",
                    "local_path": image.get("local_path"),
                    "market_hooks": candidate.get("market_hooks") or [],
                    "tickers": candidate.get("tickers") or [],
                    "scores": {
                        "novelty": candidate.get("novelty"),
                        "market_relevance": candidate.get("market_relevance"),
                        "broadcast_fit": candidate.get("broadcast_fit"),
                        "confidence": candidate.get("confidence"),
                        "score": candidate.get("score"),
                    },
                    "vision_optional": {
                        "available": bool(vision),
                        "status": vision.get("status"),
                        "main_claim_ko": vision.get("main_claim_ko"),
                        "broadcast_hook_ko": vision.get("broadcast_hook_ko"),
                    },
                    "needs_visual_reasoning": needs_reasoning,
                    "visual_reasoning_reasons": reasoning_reasons,
                    "manual_review_required": True,
                }
            )
    return cards, stats


def render_review(cards: list[dict], target_date: str) -> str:
    lines = [
        f"# 이미지 카드 후보 {target_date}",
        "",
        "사이트 원문/alt/주변 설명을 우선 사용한 경량 카드입니다. OpenAI vision은 난해한 이미지에만 선택적으로 씁니다.",
        "",
    ]
    for card in cards:
        lines.extend(
            [
                f"## {card['title']}",
                "",
                f"- 출처: [{card['source_name']}]({card['url']})",
                f"- 설명 출처: `{card['description_source']}`",
                f"- 설명: {card['description'] or '-'}",
                f"- 이미지 alt: {card['image_alt'] or '-'}",
                f"- 로컬 이미지: `{card['local_path']}`",
                f"- vision 후보: {card['needs_visual_reasoning']} ({', '.join(card.get('visual_reasoning_reasons') or []) or '-'})",
                f"- vision 사용 가능: {card['vision_optional']['available']}",
                "",
            ]
        )
        if card.get("local_path"):
            lines.append(f"![{card['title']}]({card['local_path']})")
            lines.append("")
    if not cards:
        lines.append("- 후보 없음")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--fetch-descriptions", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    # Keep .env loading here so future source-specific tokens can be used without changing the CLI.
    _ = {**load_env(args.env.resolve()), **os.environ}
    cards, stats = build_cards(args.date, args.fetch_descriptions, not args.no_cache)

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)

    payload = {"ok": True, "target_date": args.date, "stats": stats, "cards": cards}
    (processed_dir / "visual-cards.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (notion_dir / "visual-cards-review.md").write_text(render_review(cards, args.date), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
