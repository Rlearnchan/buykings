#!/usr/bin/env python3
"""Select public media-focus cards before rendering the compact dashboard.

This step keeps the renderer deterministic: it decides *which* external
materials should appear in media focus, while the dashboard renderer only
numbers and displays the selected cards.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import build_live_notion_dashboard as dashboard


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MAX_CARDS = 30
STORYLINE_TARGET = 15
SUPPLEMENTAL_TARGET = 15

STOPWORDS = {
    "about",
    "after",
    "amid",
    "and",
    "are",
    "as",
    "at",
    "before",
    "brief",
    "by",
    "for",
    "from",
    "how",
    "inc",
    "into",
    "its",
    "market",
    "markets",
    "may",
    "more",
    "new",
    "news",
    "over",
    "says",
    "stock",
    "stocks",
    "than",
    "that",
    "the",
    "this",
    "to",
    "today",
    "under",
    "update",
    "us",
    "with",
}

COMMON_MARKET_TERMS = {
    "ai",
    "bond",
    "bonds",
    "brent",
    "dollar",
    "earnings",
    "eps",
    "fed",
    "inflation",
    "jobs",
    "oil",
    "rate",
    "rates",
    "revenue",
    "treasury",
    "wti",
}

DOMAIN_LABELS = {
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "cnbc.com": "CNBC",
    "wsj.com": "WSJ",
    "ft.com": "Financial Times",
    "marketwatch.com": "MarketWatch",
    "barrons.com": "Barron's",
    "benzinga.com": "Benzinga",
    "finance.yahoo.com": "Yahoo Finance",
    "tradingview.com": "TradingView",
    "biztoc.com": "BizToc",
    "alltoc.com": "BizToc",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: object, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip(" ,.;:") + "…"
    return text


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def host_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host.removeprefix("www.")


def source_from_url(url: str) -> str:
    host = host_of(url)
    for domain, label in DOMAIN_LABELS.items():
        if host == domain or host.endswith("." + domain):
            return label
    if host:
        return host.split(".")[0].title()
    return ""


def source_display(row: dict) -> tuple[str, str]:
    raw_source = dashboard.source_label(row.get("source") or row.get("source_name") or row.get("type"), row.get("url") or "")
    url_source = source_from_url(clean(row.get("url")))
    lowered = raw_source.lower()
    if url_source and ("biztoc" in lowered or raw_source in {"Headline River", "Analysis River"}):
        via = raw_source if raw_source and raw_source != url_source else ""
        return url_source, via
    return raw_source or url_source or "source", ""


def all_candidate_rows(target_date: str, evidence_microcopy: dict) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    processed = PROCESSED_DIR / target_date
    radar = load_json(processed / "market-radar.json")
    batch_a = load_json(processed / "today-misc-batch-a-candidates.json")
    batch_b = load_json(processed / "today-misc-batch-b-candidates.json")
    x_timeline = load_json(processed / "x-timeline-posts.json")
    radar_rows = dashboard.attach_evidence_microcopy(radar.get("candidates") or [], evidence_microcopy)
    extra_rows = dashboard.attach_evidence_microcopy(
        dashboard.rows_with_payload_time(batch_a.get("candidates") or [], batch_a)
        + dashboard.rows_with_payload_time(batch_b.get("candidates") or [], batch_b)
        + dashboard.rows_with_payload_time(x_timeline.get("posts") or [], x_timeline),
        evidence_microcopy,
    )
    rows_by_key: dict[str, dict] = {}
    for row in [*extra_rows, *radar_rows]:
        key = clean(row.get("id") or row.get("item_id") or row.get("evidence_id") or row.get("url") or row.get("title"), 300)
        if key and key not in rows_by_key:
            rows_by_key[key] = row
    radar_by_id = {row.get("id"): row for row in radar_rows if row.get("id")}
    candidate_by_id = {row.get("id"): row for row in extra_rows if row.get("id")}
    return list(rows_by_key.values()), radar_by_id, candidate_by_id


def token_candidates(text: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9&.'-]{2,}|[가-힣]{2,}", text or ""):
        normalized = token.strip(" .'\"").lower()
        if len(normalized) < 3 or normalized in STOPWORDS:
            continue
        tokens.append(normalized)
    return tokens


def clean(value: object, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: max(0, limit - 3)].rstrip(" ,.;:") + "..."
    return text


def token_candidates(text: str) -> list[str]:
    tokens = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9&.'-]{2,}|[가-힣]{2,}", text or ""):
        normalized = token.strip(" .'\"").lower()
        if len(normalized) < 3 or normalized in STOPWORDS:
            continue
        tokens.append(normalized)
    return tokens


def anomaly_scan(rows: list[dict], limit: int = 30) -> list[dict]:
    term_counts: Counter[str] = Counter()
    title_counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)
    samples: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        title = clean(row.get("title") or row.get("headline") or row.get("summary"), 180)
        if not title:
            continue
        row_source, _ = source_display(row)
        seen_in_title = set()
        for token in token_candidates(title):
            term_counts[token] += 1
            seen_in_title.add(token)
            sources[token].add(row_source)
            if len(samples[token]) < 3:
                samples[token].append(title)
        for token in seen_in_title:
            title_counts[token] += 1
    results = []
    for term, count in term_counts.items():
        if count < 2 and len(sources[term]) < 2:
            continue
        if term in COMMON_MARKET_TERMS and count < 4:
            continue
        results.append(
            {
                "term": term,
                "count": count,
                "title_count": title_counts[term],
                "source_count": len(sources[term]),
                "sample_titles": samples[term],
                "is_new_or_unusual": term not in COMMON_MARKET_TERMS,
            }
        )
    return sorted(results, key=lambda item: (-item["source_count"], -item["title_count"], -item["count"], item["term"]))[:limit]


def row_key(row: dict) -> str:
    url = clean(row.get("url"), 300).lower()
    if url:
        return "url:" + url
    item_id = clean(row.get("id") or row.get("item_id") or row.get("evidence_id"), 200).lower()
    if item_id:
        return "id:" + item_id
    title = re.sub(r"\W+", " ", clean(row.get("title") or row.get("headline")).lower()).strip()
    return "title:" + title[:80]


def candidate_quality_ok(row: dict) -> bool:
    if dashboard.is_earnings_calendar_material(row):
        return False
    source, _ = source_display(row)
    if source in dashboard.INTERNAL_MEDIA_SOURCES:
        return False
    if not clean(row.get("title") or row.get("headline") or row.get("summary")):
        return False
    if not (clean(row.get("url")) or dashboard.material_visual_path(row)):
        return False
    if dashboard.english_dump_like(clean(row.get("summary") or "")) and not dashboard.material_visual_path(row):
        return False
    return True


def analysis_river_bonus(row: dict) -> float:
    row_type = clean(row.get("type")).lower()
    source_id = clean(row.get("source_id")).lower()
    source, _ = source_display(row)
    source_l = source.lower()
    if row_type == "analysis_river":
        return 8
    if any(token in source_l for token in ["kobeissi", "wall st engine", "isabel", "factset", "bilello", "sonders", "timiraos"]):
        return 8
    if source_id in {"factset-insight", "isabelnet"}:
        return 8
    if row_type == "headline_river":
        return -2
    return 0


def content_depth_bonus(row: dict) -> float:
    level = clean(row.get("content_level")).lower()
    bonus = 0.0
    if level in {"summary", "article_summary", "full_text", "article"}:
        bonus += 3
    if clean(row.get("micro_content")):
        bonus += 2
    if dashboard.material_visual_path(row):
        bonus += 2
    return bonus


def anomaly_bonus(row: dict, terms: list[dict]) -> float:
    blob = dashboard.row_blob(row).lower()
    score = 0.0
    for index, item in enumerate(terms[:15]):
        term = item["term"]
        if term in blob:
            score += max(0.5, 4.0 - index * 0.2)
    return min(score, 8.0)


def topic_axis(row: dict) -> str:
    return dashboard.topic_axis_from_blob(dashboard.row_blob(row))


def supplement_score(row: dict, terms: list[dict]) -> float:
    base = float(row.get("score") or row.get("final_score") or 0)
    return base + analysis_river_bonus(row) + content_depth_bonus(row) + anomaly_bonus(row, terms)


def make_card(row: dict, *, bucket: str, rank: int, slide_rank: int, reason: str, score: float) -> dict:
    source, collected_via = source_display(row)
    label = dashboard.supplemental_public_material_label(row)
    return {
        **row,
        "section": "media_focus",
        "selection_bucket": bucket,
        "selection_reason": reason,
        "selection_score": round(score, 2),
        "story_rank": rank,
        "slide_rank": slide_rank,
        "label": label,
        "public_title": label,
        "kind": "article" if row.get("url") else "material",
        "source": source,
        "collected_via": collected_via,
        "url": row.get("url") or "",
        "summary": dashboard.summarize_material_text(row) or row.get("summary") or row.get("title") or label,
        "image": dashboard.material_visual_path(row),
        "topic_axis": topic_axis(row),
    }


def storyline_reference_ids(story: dict) -> list[str]:
    ids: list[str] = []
    for item in story.get("evidence_to_use") or []:
        if not isinstance(item, dict):
            continue
        item_id = clean(item.get("item_id") or item.get("evidence_id"), 240)
        if item_id and item_id not in ids:
            ids.append(item_id)
    for item_id in story.get("slide_order") or []:
        item_id = clean(item_id, 240)
        if item_id and item_id not in ids:
            ids.append(item_id)
    return ids


def storyline_blob(story: dict) -> str:
    fields = [
        story.get("title"),
        story.get("hook"),
        story.get("lead_candidate_reason"),
        story.get("why_now"),
        story.get("core_argument"),
        story.get("market_causality"),
        story.get("first_5min_fit"),
        story.get("korea_open_relevance"),
        " ".join(str(item) for item in story.get("slide_plan") or []),
    ]
    return " ".join(clean(field) for field in fields if field)


def storyline_relation_score(story_terms: set[str], row: dict) -> float:
    if not story_terms:
        return 0.0
    row_terms = set(token_candidates(dashboard.row_blob(row)))
    overlap = story_terms & row_terms
    if not overlap:
        return 0.0
    return len(overlap) * 3.0 + min(6.0, float(row.get("score") or row.get("final_score") or 0) * 0.1)


def storyline_cards(storylines: list[dict], radar_by_id: dict, candidate_by_id: dict, max_cards: int) -> list[dict]:
    cards = []
    seen = set()
    for story_index, story in enumerate(storylines[:5], start=1):
        label_order: dict[str, int] = {}
        for slide_index, label in enumerate(dashboard.public_material_labels_for_story(story, radar_by_id)[:5], start=1):
            label_order.setdefault(label, slide_index)
        for item_id in storyline_reference_ids(story):
            row = dashboard.market_focus_material_row(item_id, radar_by_id, candidate_by_id)
            if not row:
                continue
            merged = {**row, "item_id": item_id, "evidence_id": item_id}
            if not candidate_quality_ok(merged):
                continue
            label = dashboard.supplemental_public_material_label(merged)
            if not dashboard.valid_public_material_label(label):
                continue
            key = row_key(merged)
            if key in seen:
                continue
            seen.add(key)
            cards.append(
                make_card(
                    {**merged, "label": label},
                    bucket="storyline",
                    rank=story_index,
                    slide_rank=label_order.get(label, len(cards) + 1),
                    reason="referenced_by_editorial_storyline",
                    score=float(merged.get("score") or merged.get("final_score") or 0),
                )
            )
            if len(cards) >= max_cards:
                return cards
        story_terms = set(token_candidates(storyline_blob(story)))
        related_rows = []
        for row in [*radar_by_id.values(), *candidate_by_id.values()]:
            score = storyline_relation_score(story_terms, row)
            if score > 0:
                related_rows.append((score, row))
        for relation_score, row in sorted(related_rows, key=lambda item: -item[0]):
            if not candidate_quality_ok(row):
                continue
            label = dashboard.supplemental_public_material_label(row)
            if not dashboard.valid_public_material_label(label):
                continue
            key = row_key(row)
            if key in seen:
                continue
            seen.add(key)
            cards.append(
                make_card(
                    {**row, "label": label},
                    bucket="storyline",
                    rank=story_index,
                    slide_rank=len(cards) + 1,
                    reason="related_to_editorial_storyline",
                    score=float(row.get("score") or row.get("final_score") or 0) + relation_score,
                )
            )
            if len(cards) >= max_cards:
                return cards
    return cards


def cap_for_source(source: str) -> int:
    lowered = (source or "").lower()
    if any(token in lowered for token in ["biztoc", "finviz"]):
        return 2
    if any(token in lowered for token in ["yahoo", "reuters", "marketwatch", "cnbc", "wsj"]):
        return 3
    return 4


def supplemental_cards(rows: list[dict], used_keys: set[str], used_labels: set[str], terms: list[dict], limit: int) -> list[dict]:
    scored = []
    for row in rows:
        if not candidate_quality_ok(row):
            continue
        key = row_key(row)
        if key in used_keys:
            continue
        label = dashboard.supplemental_public_material_label(row)
        if not dashboard.valid_public_material_label(label):
            continue
        score = supplement_score(row, terms)
        scored.append((score, analysis_river_bonus(row), content_depth_bonus(row), label, row))

    selected = []
    topic_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    seen = set(used_keys)
    for score, analysis_bonus, _, label, row in sorted(scored, key=lambda item: (-item[0], -item[1], item[3])):
        key = row_key(row)
        if key in seen:
            continue
        label = dashboard.unique_public_label(label, used_labels)
        if not label:
            continue
        source, _ = source_display(row)
        axis = topic_axis(row)
        if topic_counts[axis] >= 4:
            continue
        if source_counts[source] >= cap_for_source(source):
            continue
        seen.add(key)
        used_labels.add(label)
        topic_counts[axis] += 1
        source_counts[source] += 1
        selected.append(
            make_card(
                {**row, "label": label},
                bucket="supplemental",
                rank=80,
                slide_rank=len(selected) + 1,
                reason="open_pool_analysis_diversity" if analysis_bonus > 0 else "open_pool_quality_or_anomaly",
                score=score,
            )
        )
        if len(selected) >= limit:
            return selected

    for score, _, _, label, row in sorted(scored, key=lambda item: (-item[0], item[3])):
        key = row_key(row)
        if key in seen:
            continue
        label = dashboard.unique_public_label(label, used_labels)
        if not label:
            continue
        seen.add(key)
        used_labels.add(label)
        selected.append(
            make_card(
                {**row, "label": label},
                bucket="supplemental",
                rank=90,
                slide_rank=len(selected) + 1,
                reason="open_pool_fill_after_caps",
                score=score,
            )
        )
        if len(selected) >= limit:
            return selected
    return selected


def numbered_cards(cards: list[dict], max_cards: int) -> list[dict]:
    rows = []
    seen_keys = set()
    used_labels = set()
    for card in cards:
        key = row_key(card)
        if key in seen_keys:
            continue
        label = dashboard.unique_public_label(clean(card.get("label")), used_labels)
        if not label:
            continue
        seen_keys.add(key)
        used_labels.add(label)
        index = len(rows) + 1
        rows.append(
            {
                **card,
                "label": label,
                "card_key": dashboard.compact_card_key({**card, "label": label}, index),
                "media_number": f"({index})",
                "media_number_index": index,
            }
        )
        if len(rows) >= max_cards:
            break
    return rows


def build_selection(target_date: str, max_cards: int = MAX_CARDS, storyline_target: int = STORYLINE_TARGET) -> dict:
    processed = PROCESSED_DIR / target_date
    evidence_microcopy = load_json(processed / "evidence-microcopy.json")
    market_focus = load_json(processed / "market-focus-brief.json")
    editorial = load_json(processed / "editorial-brief.json")
    market_radar = load_json(processed / "market-radar.json")
    rows, radar_by_id, candidate_by_id = all_candidate_rows(target_date, evidence_microcopy)
    use_editorial = dashboard.valid_editorial_brief(editorial)
    storylines = dashboard.compact_storylines_for_publish(editorial.get("storylines") if use_editorial else market_radar.get("storylines") or [])
    terms = anomaly_scan(rows)
    story_cards = storyline_cards(storylines, radar_by_id, candidate_by_id, min(storyline_target, max_cards))
    used_keys = {row_key(card) for card in story_cards}
    used_labels = {clean(card.get("label")) for card in story_cards if clean(card.get("label"))}
    supplements = supplemental_cards(rows, used_keys, used_labels, terms, max(0, max_cards - len(story_cards)))
    cards = numbered_cards([*story_cards, *supplements], max_cards)
    return {
        "ok": True,
        "date": target_date,
        "generated_at": now_kst(),
        "contract": "media_focus_selection_v1",
        "max_cards": max_cards,
        "storyline_target": storyline_target,
        "storyline_count": sum(1 for card in cards if card.get("selection_bucket") == "storyline"),
        "supplemental_count": sum(1 for card in cards if card.get("selection_bucket") == "supplemental"),
        "candidate_count": len(rows),
        "anomaly_terms": terms,
        "selection_policy": {
            "theme_keys_usage": "tag_and_diversity_only_not_gate",
            "supplemental_terms_usage": "not_used_as_gate",
            "supplemental_pool": "all_quality_candidates",
            "supplemental_preference": "analysis_river_content_depth_source_diversity_anomaly",
        },
        "cards": cards,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--max-cards", type=int, default=MAX_CARDS)
    parser.add_argument("--storyline-target", type=int, default=STORYLINE_TARGET)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = build_selection(args.date, args.max_cards, args.storyline_target)
    output = args.output or (PROCESSED_DIR / args.date / "media-focus-selection.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(output),
                "card_count": len(payload.get("cards") or []),
                "storyline_count": payload.get("storyline_count"),
                "supplemental_count": payload.get("supplemental_count"),
                "anomaly_term_count": len(payload.get("anomaly_terms") or []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
