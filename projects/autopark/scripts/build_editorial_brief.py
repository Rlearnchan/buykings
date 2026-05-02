#!/usr/bin/env python3
"""Build an LLM-authored editorial brief for the Autopark dashboard."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"
RETROSPECTIVE_LEARNING_CONFIG = CONFIG_DIR / "retrospective_learning.json"

TEXT_THEME_HINTS = {
    "ai_infra": (
        "ai",
        "artificial intelligence",
        "cloud",
        "capex",
        "data center",
        "semiconductor",
        "chip",
        "nvidia",
        "huawei",
        "컴퓨트",
        "반도체",
        "데이터센터",
    ),
    "earnings_signal": (
        "earnings",
        "eps",
        "revenue",
        "guidance",
        "forecast",
        "quarter",
        "실적",
        "가이던스",
        "매출",
    ),
    "energy_geopolitics": (
        "oil",
        "brent",
        "wti",
        "iran",
        "hormuz",
        "opec",
        "energy",
        "crude",
        "유가",
        "원유",
        "호르무즈",
        "이란",
        "에너지",
    ),
    "rates_macro": (
        "fed",
        "fomc",
        "inflation",
        "pce",
        "treasury",
        "yield",
        "rate",
        "recession",
        "금리",
        "연준",
        "인플레",
        "침체",
    ),
    "market_positioning": (
        "position",
        "positioning",
        "valuation",
        "p/e",
        "concentration",
        "leverage",
        "risk appetite",
        "record high",
        "all-time high",
        "best month",
        "mania",
        "manias",
        "bull",
        "bear",
        "market cap",
        "s&p 500",
        "포지셔닝",
        "밸류",
        "과열",
        "레버리지",
        "집중",
        "사상 최고",
        "최고치",
        "강세장",
    ),
}

try:
    from editorial_policy import infer_asset_type, infer_evidence_role, infer_source_role, infer_talk_vs_slide
except ImportError:  # pragma: no cover - keeps direct execution resilient if helper is unavailable.
    infer_asset_type = None
    infer_evidence_role = None
    infer_source_role = None
    infer_talk_vs_slide = None


EVIDENCE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id", "evidence_id", "title", "source_role", "evidence_role", "reason"],
    "properties": {
        "item_id": {"type": "string"},
        "evidence_id": {"type": "string"},
        "title": {"type": "string"},
        "source_role": {"type": "string"},
        "evidence_role": {"type": "string"},
        "reason": {"type": "string"},
    },
}

DROP_EVIDENCE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id", "evidence_id", "title", "source_role", "evidence_role", "drop_code", "reason"],
    "properties": {
        "item_id": {"type": "string"},
        "evidence_id": {"type": "string"},
        "title": {"type": "string"},
        "source_role": {"type": "string"},
        "evidence_role": {"type": "string"},
        "drop_code": {"type": "string"},
        "reason": {"type": "string"},
    },
}

PPT_ASSET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "asset_id",
        "source",
        "source_role",
        "visual_asset_role",
        "storyline_id",
        "slide_priority",
        "use_as_slide",
        "use_as_talk_only",
        "caption",
        "why_this_visual",
        "risks_or_caveats",
    ],
    "properties": {
        "asset_id": {"type": "string"},
        "source": {"type": "string"},
        "source_role": {"type": "string"},
        "visual_asset_role": {"type": "string"},
        "storyline_id": {"type": "string"},
        "slide_priority": {"type": "integer", "minimum": 1, "maximum": 20},
        "use_as_slide": {"type": "boolean"},
        "use_as_talk_only": {"type": "boolean"},
        "caption": {"type": "string"},
        "why_this_visual": {"type": "string"},
        "risks_or_caveats": {"type": "string"},
    },
}

STORYLINE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "storyline_id",
        "rank",
        "title",
        "recommendation_stars",
        "rating_reason",
        "lead_candidate_reason",
        "hook",
        "why_now",
        "core_argument",
        "signal_or_noise",
        "market_causality",
        "expectation_gap",
        "prepricing_risk",
        "first_5min_fit",
        "korea_open_relevance",
        "talk_track",
        "slide_order",
        "slide_plan",
        "ppt_asset_queue",
        "evidence_to_use",
        "evidence_to_drop",
        "drop_code",
        "counterpoint",
        "what_would_change_my_mind",
        "closing_line",
    ],
    "properties": {
        "storyline_id": {"type": "string"},
        "rank": {"type": "integer", "minimum": 1, "maximum": 5},
        "title": {"type": "string"},
        "recommendation_stars": {"type": "integer", "minimum": 1, "maximum": 3},
        "rating_reason": {"type": "string"},
        "lead_candidate_reason": {"type": "string"},
        "hook": {"type": "string"},
        "why_now": {"type": "string"},
        "core_argument": {"type": "string"},
        "signal_or_noise": {"type": "string"},
        "market_causality": {"type": "string"},
        "expectation_gap": {"type": "string"},
        "prepricing_risk": {"type": "string"},
        "first_5min_fit": {"type": "string"},
        "korea_open_relevance": {"type": "string"},
        "talk_track": {"type": "string"},
        "slide_order": {"type": "array", "items": {"type": "string"}},
        "slide_plan": {"type": "array", "items": {"type": "string"}},
        "ppt_asset_queue": {"type": "array", "items": PPT_ASSET_SCHEMA},
        "evidence_to_use": {"type": "array", "items": EVIDENCE_SCHEMA},
        "evidence_to_drop": {"type": "array", "items": DROP_EVIDENCE_SCHEMA},
        "drop_code": {"type": "string"},
        "counterpoint": {"type": "string"},
        "what_would_change_my_mind": {"type": "string"},
        "closing_line": {"type": "string"},
    },
}

EDITORIAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "broadcast_mode",
        "daily_thesis",
        "one_line_market_frame",
        "market_map_summary",
        "editorial_summary",
        "ppt_asset_queue",
        "talk_only_queue",
        "drop_list",
        "retrospective_watchpoints",
        "storylines",
    ],
    "properties": {
        "broadcast_mode": {"type": "string"},
        "daily_thesis": {"type": "string"},
        "one_line_market_frame": {"type": "string"},
        "market_map_summary": {"type": "string"},
        "editorial_summary": {"type": "string"},
        "ppt_asset_queue": {"type": "array", "items": PPT_ASSET_SCHEMA},
        "talk_only_queue": {"type": "array", "items": EVIDENCE_SCHEMA},
        "drop_list": {"type": "array", "items": DROP_EVIDENCE_SCHEMA},
        "retrospective_watchpoints": {"type": "array", "items": {"type": "string"}},
        "storylines": {"type": "array", "minItems": 3, "maxItems": 5, "items": STORYLINE_SCHEMA},
    },
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_json(payload: dict, ensure_ascii: bool = False) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=ensure_ascii, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def write_raw_editorial_response(target_date: str, model: str, response_id: str | None, brief: dict, source: str) -> Path:
    path = RUNTIME_DIR / "openai-responses" / f"{target_date}-editorial-raw.json"
    write_json(
        path,
        {
            "ok": True,
            "target_date": target_date,
            "received_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": model,
            "source": source,
            "raw_response_id": response_id,
            "brief": brief,
        },
    )
    return path


def compact_text(value: object, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def title_of(item: dict) -> str:
    return compact_text(item.get("title") or item.get("headline") or item.get("summary") or item.get("id"), 120)


def source_of(item: dict) -> str:
    return compact_text(item.get("source") or item.get("type") or item.get("publisher") or "", 80)


def resolved_source_role(item: dict) -> str:
    if item.get("source_role"):
        return str(item.get("source_role"))
    if infer_source_role:
        return infer_source_role(item)
    blob = f"{item.get('source') or ''} {item.get('url') or ''}".lower()
    if "x.com" in blob or "twitter.com" in blob or "reddit" in blob:
        return "sentiment_probe"
    if any(token in blob for token in ["finviz", "heatmap", "chart", "datawrapper"]):
        return "market_reaction"
    if "reuters" in blob:
        return "fact_anchor"
    if any(token in blob for token in ["bloomberg", "wsj", "financial times"]):
        return "analysis_anchor"
    return "weak_or_unverified"


def resolved_evidence_role(item: dict, source_role: str | None = None) -> str:
    if item.get("evidence_role"):
        return str(item.get("evidence_role"))
    role = source_role or resolved_source_role(item)
    if infer_evidence_role:
        return infer_evidence_role(role, item)
    if role == "sentiment_probe":
        return "sentiment"
    if role in {"market_reaction", "visual_anchor"}:
        return "visual" if item.get("visual_local_path") else "market_reaction"
    if role in {"fact_anchor", "company_primary", "official_policy"}:
        return "fact"
    if role == "data_anchor":
        return "data"
    if role == "analysis_anchor":
        return "analysis"
    return "context"


def resolved_asset_type(item: dict) -> str:
    if item.get("asset_type"):
        return str(item.get("asset_type"))
    if infer_asset_type:
        return infer_asset_type(item)
    return "article_screenshot"


def resolved_talk_vs_slide(item: dict, asset_type: str, evidence_role: str) -> str:
    if item.get("talk_vs_slide"):
        return str(item.get("talk_vs_slide"))
    if infer_talk_vs_slide:
        return infer_talk_vs_slide(item, asset_type, evidence_role)
    if item.get("visual_local_path") or item.get("image_refs"):
        return "slide"
    if evidence_role == "sentiment":
        return "talk_only"
    return "talk_or_slide"


def is_visual_candidate(item: dict) -> bool:
    asset_type = resolved_asset_type(item)
    evidence_role = resolved_evidence_role(item)
    talk_vs_slide = resolved_talk_vs_slide(item, asset_type, evidence_role)
    return bool(item.get("ppt_asset_candidate") or item.get("visual_local_path") or item.get("image_refs") or talk_vs_slide in {"slide", "talk_or_slide"})


def candidate_rank(item: dict) -> tuple[float, int, int, str]:
    score = float(item.get("score") or item.get("final_score") or 0)
    visual = 1 if item.get("visual_local_path") or item.get("image_refs") else 0
    source_count = len(set(item.get("sources") or [item.get("source") or ""]))
    return (score, visual, source_count, title_of(item))


def inferred_theme_keys_from_text(*values: object) -> set[str]:
    text = " ".join(str(value or "") for value in values).lower()
    return {
        theme
        for theme, hints in TEXT_THEME_HINTS.items()
        if any(hint in text for hint in hints)
    }


def referenced_candidate_ids_from_storylines(storylines: list[dict]) -> set[str]:
    ids: set[str] = set()
    for story in storylines:
        for item_id in story.get("selected_item_ids") or []:
            if item_id:
                ids.add(str(item_id))
        for ref in story.get("material_refs") or []:
            item_id = ref.get("id") or ref.get("item_id")
            if item_id:
                ids.add(str(item_id))
    return ids


def editorial_support_candidates(rows: list[dict], limit: int = 10) -> list[dict]:
    positioning = []
    scored = []
    support_themes = {"market_positioning", "rates_macro", "earnings_signal", "energy_geopolitics", "ai_infra"}
    for item in rows:
        themes = theme_keys_of(item)
        if not themes & support_themes:
            continue
        source_role = resolved_source_role(item)
        evidence_role = resolved_evidence_role(item, source_role)
        if evidence_role not in {"fact", "data", "analysis", "market_reaction", "visual"}:
            continue
        if "market_positioning" in themes:
            positioning.append((candidate_rank(item), item))
        scored.append((len(themes & support_themes), candidate_rank(item), item))
    merged = []
    seen = set()
    for _, item in sorted(positioning, key=lambda row: row[0], reverse=True)[:6]:
        item_id = str(item.get("id") or item.get("item_id") or "")
        if item_id and item_id not in seen:
            merged.append(item)
            seen.add(item_id)
    for _, _, item in sorted(scored, key=lambda row: (row[0], row[1]), reverse=True):
        item_id = str(item.get("id") or item.get("item_id") or "")
        if item_id and item_id not in seen:
            merged.append(item)
            seen.add(item_id)
        if len(merged) >= limit:
            break
    return merged


def select_editorial_candidates(rows: list[dict], max_candidates: int, required_ids: set[str] | None = None) -> list[dict]:
    ranked = sorted(rows, key=candidate_rank, reverse=True)
    selected = ranked[:max_candidates]
    required_ids = required_ids or set()
    required = [
        item
        for item in rows
        if str(item.get("id") or item.get("item_id") or "") in required_ids
    ]
    support_roles = {"fact", "data", "analysis"}
    support = [
        item
        for item in ranked
        if resolved_evidence_role(item, resolved_source_role(item)) in support_roles
    ][:8]
    market_reaction = [
        item
        for item in ranked
        if resolved_evidence_role(item, resolved_source_role(item)) in {"visual", "market_reaction"}
    ][:4]
    editorial_support = editorial_support_candidates(rows)
    merged = []
    seen = set()
    for item in [*selected, *required, *support, *market_reaction, *editorial_support]:
        item_id = str(item.get("id") or item.get("item_id") or item.get("url") or item.get("title") or "")
        if not item_id or item_id in seen:
            continue
        merged.append(item)
        seen.add(item_id)
    return merged


def theme_keys_of(item: dict) -> set[str]:
    explicit = {str(theme) for theme in (item.get("theme_keys") or item.get("market_hooks") or []) if theme}
    inferred = inferred_theme_keys_from_text(
        item.get("title"),
        item.get("headline"),
        item.get("summary"),
        item.get("text"),
        item.get("source"),
        item.get("url"),
    )
    return explicit | inferred


def support_candidates_for_story(story: dict, selected_items: list[dict], candidates: list[dict], limit: int = 2) -> list[dict]:
    story_themes = set()
    for item in selected_items:
        story_themes |= theme_keys_of(item)
    if not story_themes:
        for ref in story.get("material_refs") or []:
            story_themes |= theme_keys_of(ref)
    story_themes |= inferred_theme_keys_from_text(
        story.get("title"),
        story.get("hook"),
        story.get("why_now"),
        story.get("core_argument"),
        story.get("talk_track"),
        story.get("signal_or_noise"),
    )
    primary_themes = {"market_positioning"} if "market_positioning" in story_themes else set(story_themes)
    selected_ids = {str(item.get("id") or item.get("item_id") or "") for item in selected_items}
    rows = []
    for item in candidates:
        item_id = str(item.get("id") or item.get("item_id") or "")
        if not item_id or item_id in selected_ids:
            continue
        source_role = resolved_source_role(item)
        evidence_role = resolved_evidence_role(item, source_role)
        if evidence_role in {"sentiment", "context", "visual", "market_reaction"}:
            continue
        item_themes = theme_keys_of(item)
        overlap = len(story_themes & item_themes) if story_themes else 0
        if overlap <= 0:
            continue
        primary_overlap = len(primary_themes & item_themes) if primary_themes else overlap
        rows.append((primary_overlap, overlap, candidate_rank(item), item))
    return [item for _, _, _, item in sorted(rows, key=lambda row: (row[0], row[1], row[2]), reverse=True)[:limit]]


def compact_candidate(item: dict) -> dict:
    source_role = resolved_source_role(item)
    evidence_role = resolved_evidence_role(item, source_role)
    asset_type = resolved_asset_type(item)
    talk_vs_slide = resolved_talk_vs_slide(item, asset_type, evidence_role)
    return {
        "id": str(item.get("id") or ""),
        "item_id": str(item.get("item_id") or item.get("id") or ""),
        "title": title_of(item),
        "source": source_of(item),
        "source_role": source_role,
        "evidence_role": evidence_role,
        "url": item.get("url") or "",
        "published_at": item.get("published_at") or item.get("captured_at") or "",
        "score": item.get("score") or item.get("final_score") or 0,
        "theme_keys": item.get("theme_keys") or item.get("market_hooks") or [],
        "topic_cluster": item.get("topic_cluster") or "",
        "asset_type": asset_type,
        "market_reaction": item.get("market_reaction") or "",
        "signal_or_noise": item.get("signal_or_noise") or "",
        "signal_axes": item.get("signal_axes") or [],
        "expectation_gap": item.get("expectation_gap") or "",
        "prepricing_risk": item.get("prepricing_risk") or "",
        "korea_open_relevance": item.get("korea_open_relevance") or "",
        "first_5min_fit": item.get("first_5min_fit") or "",
        "ppt_asset_candidate": is_visual_candidate(item),
        "drop_risk": item.get("drop_risk") or "",
        "talk_vs_slide": talk_vs_slide,
        "summary": compact_text(item.get("summary") or item.get("text") or item.get("selection_reason"), 520),
        "visual_local_path": item.get("visual_local_path") or "",
    }


def compact_finviz_item(item: dict) -> dict:
    return {
        "ticker": item.get("ticker") or "",
        "title": title_of(item),
        "screenshot_path": item.get("screenshot_path") or "",
        "quote_summary": [compact_text(row, 160) for row in (item.get("quote_summary") or [])[:3]],
        "news": [
            {
                "time": compact_text(row.get("time"), 30),
                "headline": compact_text(row.get("headline"), 160),
                "url": row.get("url") or "",
            }
            for row in (item.get("news") or [])[:4]
        ],
    }


def load_recent_briefs(target_date: str, days: int = 7) -> list[dict]:
    current = parse_date(target_date)
    briefs = []
    for offset in range(1, days + 1):
        day = (current - timedelta(days=offset)).isoformat()
        brief = load_json(PROCESSED_DIR / day / "editorial-brief.json")
        if brief:
            briefs.append(
                {
                    "date": day,
                    "daily_thesis": brief.get("daily_thesis") or "",
                    "titles": [story.get("title") for story in brief.get("storylines", []) if story.get("title")],
                }
            )
    return briefs


def load_recent_broadcast_feedback(target_date: str, days: int = 7) -> list[dict]:
    current = parse_date(target_date)
    rows = []
    for offset in range(1, days + 1):
        day = (current - timedelta(days=offset)).isoformat()
        folder = RUNTIME_DIR / "broadcast" / day
        if not folder.exists():
            continue
        snippets = []
        paths = [path for path in sorted(folder.glob("*")) if path.suffix.lower() in {".md", ".txt"}]
        preferred = [path for path in paths if any(token in path.name.lower() for token in ["retrospective", "feedback", "review"])]
        for path in preferred:
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = compact_text(path.read_text(encoding="utf-8", errors="replace"), 900)
            if text:
                snippets.append({"file": path.name, "text": text})
        if snippets:
            rows.append({"date": day, "files": snippets[:4]})
    return rows


def read_optional_text(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return ""
    try:
        return compact_text(path.read_text(encoding="utf-8", errors="replace"), limit)
    except OSError:
        return ""


def load_retrospective_learning_config(path: Path = RETROSPECTIVE_LEARNING_CONFIG) -> dict:
    defaults = {
        "version": 1,
        "lookback_days": 7,
        "max_days": 4,
        "max_examples_per_day": 6,
        "label_weights": {
            "used_as_lead": 4,
            "used_later": 1,
            "mentioned_only": 1,
            "used_as_slide": 3,
            "used_as_talk_only": 1,
            "strong_broadcast_fit": 3,
            "weak_broadcast_fit": 1,
            "not_used_too_complex": -3,
            "not_used_low_visual_value": -2,
            "not_used_already_known": -1,
            "not_used_weak_market_reaction": -2,
            "missed_source_gap": -3,
            "missed_weighting_error": -4,
            "false_positive_sentiment_only": -4,
            "false_positive_visual_only": -4,
        },
        "label_actions": {
            "used_as_lead": "Boost first-five-minute market explainers with slide-ready evidence.",
            "used_as_slide": "Prefer concrete PPT assets when editorial strength is similar.",
            "false_positive_sentiment_only": "Never promote social-only material as fact.",
            "false_positive_visual_only": "Do not infer causality from charts without fact/data/analysis support.",
            "missed_source_gap": "Add source watchpoints for topics the dashboard missed.",
            "missed_weighting_error": "Require stronger fact/data anchors before promoting similar signals.",
            "not_used_too_complex": "Demote stories that need too much setup.",
            "not_used_low_visual_value": "Keep low-visual-value material as talk-only.",
        },
        "hard_rules": [
            "Retrospective feedback is preference and format guidance, not a source for new market facts.",
            "Current-day evidence still decides the story.",
        ],
    }
    config = load_optional_json(path)
    if not config:
        return defaults
    merged = {**defaults, **config}
    merged["label_weights"] = {**defaults["label_weights"], **(config.get("label_weights") or {})}
    merged["label_actions"] = {**defaults["label_actions"], **(config.get("label_actions") or {})}
    return merged


def label_values(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value:
        return [value]
    return []


def score_labels(labels: list[str], weights: dict[str, int | float]) -> int:
    return int(sum(float(weights.get(label, 0)) for label in labels))


def summarize_retrospective_payload(day: str, review_payload: dict, comparison_payload: dict, feedback_text: str, config: dict) -> dict:
    review = review_payload.get("review") if isinstance(review_payload.get("review"), dict) else review_payload
    weights = config.get("label_weights") or {}
    label_counter: Counter[str] = Counter()
    examples: list[dict] = []

    for item in (comparison_payload.get("storyline_results") or [])[:8]:
        labels = label_values(item.get("labels"))
        if not labels:
            continue
        label_counter.update(labels)
        best_slide = (item.get("slide_matches") or [{}])[0]
        examples.append(
            {
                "type": "storyline",
                "storyline_id": item.get("storyline_id") or "",
                "title": compact_text(item.get("title"), 120),
                "labels": labels,
                "score": score_labels(labels, weights),
                "best_slide": compact_text(best_slide.get("title"), 100),
            }
        )

    for item in (comparison_payload.get("asset_results") or [])[:20]:
        labels = label_values(item.get("label"))
        if not labels:
            continue
        label_counter.update(labels)
        if score_labels(labels, weights) == 0:
            continue
        examples.append(
            {
                "type": "asset",
                "item_id": item.get("item_id") or item.get("evidence_id") or "",
                "storyline_id": item.get("storyline_id") or "",
                "title": compact_text(item.get("title"), 120),
                "labels": labels,
                "score": score_labels(labels, weights),
            }
        )

    for item in (review.get("asset_usage_labels") or [])[:20]:
        labels = label_values(item.get("label"))
        if not labels:
            continue
        label_counter.update(labels)
        examples.append(
            {
                "type": "review_label",
                "item_id": item.get("item_id") or "",
                "storyline_id": item.get("storyline_id") or "",
                "labels": labels,
                "score": score_labels(labels, weights),
                "comment": compact_text(item.get("comment") or item.get("evidence"), 140),
            }
        )

    missed_topics = [
        {
            "topic": compact_text(item.get("topic"), 100),
            "suggested_source_or_query": compact_text(item.get("suggested_source_or_query"), 140),
        }
        for item in (review.get("missed_broadcast_topics") or [])[:6]
    ]
    label_actions = config.get("label_actions") or {}
    action_labels = [label for label, _ in label_counter.most_common() if label in label_actions]
    positive_score = sum(max(0, score_labels([label], weights)) * count for label, count in label_counter.items())
    caution_score = sum(abs(min(0, score_labels([label], weights))) * count for label, count in label_counter.items())
    summary = {
        "date": day,
        "label_counts": dict(label_counter.most_common()),
        "positive_score": int(positive_score),
        "caution_score": int(caution_score),
        "actions": [label_actions[label] for label in action_labels[:8]],
        "examples": sorted(examples, key=lambda item: abs(int(item.get("score") or 0)), reverse=True)[: int(config.get("max_examples_per_day") or 6)],
        "missed_topics": missed_topics,
        "summary_for_next_brief": compact_text(review.get("summary_for_next_brief") or feedback_text, 500),
        "prompt_updates": [compact_text(item, 180) for item in (review.get("prompt_updates") or [])[:6]],
    }
    has_signal = bool(label_counter or missed_topics or summary["summary_for_next_brief"] or summary["prompt_updates"])
    return summary if has_signal else {}


def load_retrospective_learning(target_date: str) -> dict:
    config = load_retrospective_learning_config()
    current = parse_date(target_date)
    lookback_days = int(config.get("lookback_days") or 7)
    max_days = int(config.get("max_days") or 4)
    rows = []
    aggregate: Counter[str] = Counter()
    for offset in range(1, lookback_days + 1):
        day = (current - timedelta(days=offset)).isoformat()
        review_payload = load_optional_json(RUNTIME_DIR / "reviews" / day / "broadcast-retrospective.json")
        comparison_payload = load_optional_json(RUNTIME_DIR / "broadcast" / day / "broadcast-asset-comparison.json")
        feedback_text = read_optional_text(RUNTIME_DIR / "broadcast" / day / "retrospective-feedback.md")
        summary = summarize_retrospective_payload(day, review_payload, comparison_payload, feedback_text, config)
        if not summary:
            continue
        rows.append(summary)
        aggregate.update(summary.get("label_counts") or {})
        if len(rows) >= max_days:
            break
    actions = []
    label_actions = config.get("label_actions") or {}
    for label, _ in aggregate.most_common():
        action = label_actions.get(label)
        if action and action not in actions:
            actions.append(action)
    return {
        "available": bool(rows),
        "config_version": config.get("version"),
        "lookback_days": lookback_days,
        "hard_rules": config.get("hard_rules") or [],
        "aggregate_label_counts": dict(aggregate.most_common()),
        "aggregate_actions": actions[:10],
        "days": rows,
    }


def build_input_payload(target_date: str, max_candidates: int) -> dict:
    processed = PROCESSED_DIR / target_date
    radar = load_json(processed / "market-radar.json")
    radar_storylines = radar.get("storylines") or []
    required_ids = referenced_candidate_ids_from_storylines(radar_storylines)
    candidates = select_editorial_candidates(radar.get("candidates") or [], max_candidates, required_ids=required_ids)
    finviz = load_json(processed / "finviz-feature-stocks.json")
    visuals = load_json(processed / "visual-cards.json")
    return {
        "date": target_date,
        "policy": {
            "selection_style": "strong_selective",
            "minimum_storylines": 3,
            "maximum_storylines": 5,
            "do_not_pad_to_five": True,
            "editorial_role": "morning_broadcast_editor",
            "lead_storyline_rule": "best_market_explanation_first_5min_clear_ppt_supported",
            "evidence_roles": ["fact", "data", "analysis", "sentiment", "visual", "market_reaction"],
            "sentiment_sources_are_not_fact": True,
            "market_reaction_is_not_causality": True,
            "operation_mode": os.environ.get("AUTOPARK_OPERATION_MODE") or "daily_broadcast",
            "expected_broadcast": os.environ.get("AUTOPARK_EXPECTED_BROADCAST", "1") != "0",
            "operation_note": os.environ.get("AUTOPARK_OPERATION_NOTE") or "",
        },
        "market_radar_storylines": radar_storylines,
        "candidates": [compact_candidate(item) for item in candidates if item.get("id")],
        "finviz_feature_stocks": [compact_finviz_item(item) for item in (finviz.get("items") or [])[:10]],
        "visual_cards": [
            {
                "id": item.get("id") or item.get("title") or "",
                "title": title_of(item),
                "summary": compact_text(item.get("summary") or item.get("caption") or "", 220),
                "path": item.get("local_path") or item.get("visual_local_path") or "",
            }
            for item in (visuals.get("cards") or visuals.get("items") or [])[:16]
        ],
        "recent_briefs": load_recent_briefs(target_date),
        "recent_broadcast_feedback": load_recent_broadcast_feedback(target_date),
        "retrospective_learning": load_retrospective_learning(target_date),
    }


def build_prompt(payload: dict) -> str:
    return f"""You are the editorial lead for a Korean morning markets broadcast.

You are not a news summarizer. You are the morning broadcast editor who prepares:
1) the lead storyline decision,
2) the PPT asset queue,
3) the talk-only queue,
4) the drop list,
5) identifiers needed for post-broadcast retrospective learning.

Rules:
- Use only the provided candidates and evidence IDs.
- Do not invent facts, prices, dates, or claims outside the evidence.
- Select 3 to 5 storylines. Do not pad to 5 if only 3 are strong.
- Merge overlapping stories instead of splitting the same theme twice.
- Each storyline must be a usable broadcast segment with a hook, why-now, argument, evidence, talk track, and counterpoint.
- Today's lead is not the most sensational headline. It is the story that best explains today's market move, can be understood in the first 5 minutes, and can be supported by PPT material.
- Separate fact, data, analysis, sentiment, visual, and market_reaction evidence. Use source_role and evidence_role exactly for that editorial distinction.
- X, Reddit, and community posts cannot be fact evidence by themselves. They can only be sentiment evidence or light-segment color.
- Heatmaps, index charts, company charts, and Finviz captures show market reaction; they do not prove causality unless paired with fact/data/analysis evidence.
- For earnings and macro data, judge expectation_gap: actual result versus expected result and market-implied expectation.
- If a story may already be priced in, mark prepricing_risk clearly.
- Always show both evidence_to_use and evidence_to_drop. Dropped items need a drop_code.
- Separate slide material from talk-only material. A slide asset must appear in ppt_asset_queue; a spoken-only item must not masquerade as a slide.
- Every storyline judgment must leave item_id/evidence_id references so a retrospective can compare the dashboard with the transcript and PPT outline.
- Prefer Korean that sounds like a human market editor, not a scoring system.
- Do not mention internal scoring, clustering, source-count logic, or "same-direction signals".
- Put weak-but-related material into evidence_to_drop with a reason.
- Every evidence_to_use item_id must come from candidates[].id.
- Rating uses 1 to 3 stars: 3 = lead segment, 2 = useful segment, 1 = backup only.
- If retrospective_learning is available, apply its label-weight guidance to today's editorial judgment:
  - used_as_lead, used_as_slide, and strong_broadcast_fit are positive broadcast-fit signals for similar evidence patterns.
  - false_positive_sentiment_only means social/community-only items must be demoted and never treated as fact.
  - false_positive_visual_only means charts/heatmaps need fact/data/analysis support before causal claims.
  - not_used_too_complex means the first-five-minute explanation must be simpler.
  - not_used_low_visual_value means the material belongs in talk_only_queue unless a clearer visual exists today.
  - missed_source_gap and missed_weighting_error should become retrospective_watchpoints and source/query cautions.
- If recent_broadcast_feedback is present, infer what the human actually used and adjust today's selection style accordingly.
- Treat broadcast feedback as preference/format guidance, not as a source for new market facts.
- Never cite retrospective_learning as evidence_to_use for today's market story. It only changes ranking, format, and watchpoints.
- If policy.operation_mode is no_broadcast, write an internal preparation brief for the next broadcast rather than pretending there is a live show today.
- If policy.operation_mode is monday_catchup, separate weekend accumulation from Monday-open items and prefer facts that still matter at Monday 07:20 KST.
- For Monday catch-up, avoid treating every weekend headline equally; keep only items that can become a broadcast lead, market context, or useful backup.

Output requirements:
- broadcast_mode should be one of normal, earnings_heavy, fed_day, macro_shock, guest_early, no_guest_long_host, holiday_korea_market_open unless the evidence strongly implies another short code.
- market_map_summary is the market-map reading, not the causal explanation.
- The first storyline by rank should be the lead candidate. It must include lead_candidate_reason.
- For each ppt_asset_queue item, fill all fields even if risks_or_caveats is "none".
- For evidence_to_use/evidence_to_drop, evidence_id may equal item_id when the candidate has no separate evidence_id.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def extract_output_text(raw: dict) -> str:
    if raw.get("output_text"):
        return str(raw["output_text"]).strip()
    return "".join(
        content.get("text", "")
        for item in raw.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    ).strip()


def call_openai(prompt: str, token: str, model: str, timeout: int) -> tuple[dict, str | None]:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_editorial_brief",
                "strict": True,
                "schema": EDITORIAL_SCHEMA,
            }
        },
    }
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    text = extract_output_text(raw)
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(text), raw.get("id")


def load_fixture_response(path: Path) -> tuple[dict, str | None]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if isinstance(payload, dict) and isinstance(payload.get("brief"), dict):
        return payload["brief"], payload.get("raw_response_id") or payload.get("id")
    if isinstance(payload, dict) and (payload.get("output_text") or payload.get("output")):
        extracted = extract_output_text(payload)
        if not extracted:
            raise RuntimeError("fixture response did not contain output_text")
        return json.loads(extracted), payload.get("id")
    if isinstance(payload, dict):
        return payload, payload.get("id")
    raise ValueError("fixture must be a JSON object")


def star_label(stars: int) -> str:
    return {3: "강추", 2: "추천", 1: "보조"}.get(stars, "보조")


def known_candidates(input_payload: dict) -> dict[str, dict]:
    rows = {}
    for item in input_payload.get("candidates") or []:
        for key in [item.get("id"), item.get("item_id")]:
            if key:
                rows[str(key)] = item
    return rows


def normalize_evidence(item: dict, candidates: dict[str, dict], drop: bool = False) -> dict:
    item_id = str(item.get("item_id") or item.get("evidence_id") or "")
    candidate = candidates.get(item_id, {})
    title = item.get("title") or candidate.get("title") or item_id
    source_role = item.get("source_role") or candidate.get("source_role") or "weak_or_unverified"
    evidence_role = item.get("evidence_role") or candidate.get("evidence_role") or "context"
    normalized = {
        "item_id": item_id,
        "evidence_id": str(item.get("evidence_id") or item_id),
        "title": compact_text(title, 140),
        "source_role": source_role,
        "evidence_role": evidence_role,
        "reason": compact_text(item.get("reason") or candidate.get("summary") or "", 240),
    }
    if drop:
        normalized["drop_code"] = item.get("drop_code") or candidate.get("drop_risk") or "support_only"
    return normalized


def normalize_asset(item: dict, storyline_id: str, priority: int = 1) -> dict:
    return {
        "asset_id": str(item.get("asset_id") or f"{storyline_id}:asset-{priority}"),
        "source": str(item.get("source") or ""),
        "source_role": str(item.get("source_role") or "weak_or_unverified"),
        "visual_asset_role": str(item.get("visual_asset_role") or item.get("asset_type") or "article_screenshot"),
        "storyline_id": str(item.get("storyline_id") or storyline_id),
        "slide_priority": int(item.get("slide_priority") or priority),
        "use_as_slide": bool(item.get("use_as_slide", True)),
        "use_as_talk_only": bool(item.get("use_as_talk_only", False)),
        "caption": compact_text(item.get("caption") or item.get("title") or "", 160),
        "why_this_visual": compact_text(item.get("why_this_visual") or item.get("reason") or "", 240),
        "risks_or_caveats": compact_text(item.get("risks_or_caveats") or item.get("drop_risk") or "none", 200),
    }


def asset_from_candidate(candidate: dict, storyline_id: str, priority: int) -> dict:
    source_role = resolved_source_role(candidate)
    evidence_role = resolved_evidence_role(candidate, source_role)
    asset_type = resolved_asset_type(candidate)
    talk_vs_slide = resolved_talk_vs_slide(candidate, asset_type, evidence_role)
    return normalize_asset(
        {
            "asset_id": f"{storyline_id}:{candidate.get('id') or candidate.get('item_id')}",
            "source": candidate.get("source") or "",
            "source_role": source_role,
            "visual_asset_role": asset_type,
            "storyline_id": storyline_id,
            "slide_priority": priority,
            "use_as_slide": talk_vs_slide != "talk_only",
            "use_as_talk_only": talk_vs_slide == "talk_only",
            "caption": candidate.get("title") or "",
            "why_this_visual": candidate.get("summary") or "",
            "risks_or_caveats": candidate.get("drop_risk") or ("sentiment_only_not_fact" if evidence_role == "sentiment" else "none"),
        },
        storyline_id,
        priority,
    )


def normalize_storyline(story: dict, index: int, candidates: dict[str, dict]) -> dict:
    storyline_id = str(story.get("storyline_id") or f"storyline-{index}")
    use_items = [normalize_evidence(item, candidates) for item in (story.get("evidence_to_use") or [])]
    drop_items = [normalize_evidence(item, candidates, drop=True) for item in (story.get("evidence_to_drop") or [])]
    slide_plan = [compact_text(item, 180) for item in (story.get("slide_plan") or story.get("slide_order") or []) if compact_text(item)]
    slide_order = [compact_text(item, 180) for item in (story.get("slide_order") or story.get("slide_plan") or []) if compact_text(item)]
    assets = [normalize_asset(item, storyline_id, pos) for pos, item in enumerate(story.get("ppt_asset_queue") or [], start=1)]
    if not assets:
        for pos, evidence in enumerate(use_items, start=1):
            candidate = candidates.get(evidence.get("item_id"), {})
            if candidate.get("ppt_asset_candidate") or candidate.get("visual_local_path"):
                assets.append(asset_from_candidate(candidate, storyline_id, pos))
    return {
        "storyline_id": storyline_id,
        "rank": int(story.get("rank") or index),
        "title": compact_text(story.get("title"), 100),
        "recommendation_stars": max(1, min(3, int(story.get("recommendation_stars") or 1))),
        "rating_reason": compact_text(story.get("rating_reason") or star_label(int(story.get("recommendation_stars") or 1)), 160),
        "lead_candidate_reason": compact_text(story.get("lead_candidate_reason") or story.get("rating_reason") or story.get("why_now"), 260),
        "hook": compact_text(story.get("hook"), 240),
        "why_now": compact_text(story.get("why_now"), 360),
        "core_argument": compact_text(story.get("core_argument"), 360),
        "signal_or_noise": compact_text(story.get("signal_or_noise") or "watch", 80),
        "market_causality": compact_text(story.get("market_causality") or "needs_explicit_fact_data_analysis_pairing", 180),
        "expectation_gap": compact_text(story.get("expectation_gap") or "check_if_relevant", 160),
        "prepricing_risk": compact_text(story.get("prepricing_risk") or "check_if_relevant", 160),
        "first_5min_fit": compact_text(story.get("first_5min_fit") or "medium", 120),
        "korea_open_relevance": compact_text(story.get("korea_open_relevance") or "medium", 120),
        "talk_track": compact_text(story.get("talk_track"), 520),
        "slide_order": slide_order,
        "slide_plan": slide_plan,
        "ppt_asset_queue": assets,
        "evidence_to_use": use_items,
        "evidence_to_drop": drop_items,
        "drop_code": compact_text(story.get("drop_code") or ",".join(sorted({item.get("drop_code", "") for item in drop_items if item.get("drop_code")})), 120),
        "counterpoint": compact_text(story.get("counterpoint"), 300),
        "what_would_change_my_mind": compact_text(story.get("what_would_change_my_mind") or "추가 fact/data evidence가 반대 방향으로 확인되면 조정합니다.", 260),
        "closing_line": compact_text(story.get("closing_line") or story.get("hook"), 220),
    }


def repair_storyline_evidence_support(stories: list[dict], candidates: dict[str, dict]) -> list[dict]:
    support_roles = {"fact", "data", "analysis"}
    for story in stories:
        evidence = story.get("evidence_to_use") or []
        initial_count = len(evidence)
        roles = {item.get("evidence_role") for item in evidence}
        if roles & support_roles:
            continue
        selected_items = [
            candidates[item.get("item_id")]
            for item in evidence
            if item.get("item_id") in candidates
        ]
        support_items = support_candidates_for_story(story, selected_items, list(candidates.values()), limit=2)
        existing_ids = {item.get("item_id") for item in evidence}
        for item in support_items:
            item_id = str(item.get("item_id") or item.get("id") or "")
            if not item_id or item_id in existing_ids:
                continue
            source_role = resolved_source_role(item)
            evidence_role = resolved_evidence_role(item, source_role)
            if evidence_role not in support_roles:
                continue
            evidence.append(
                {
                    "item_id": item_id,
                    "evidence_id": item_id,
                    "title": compact_text(item.get("title"), 140),
                    "source_role": source_role,
                    "evidence_role": evidence_role,
                    "reason": "자동 보강: sentiment 단독 스토리라인이 되지 않도록 같은 테마의 fact/data/analysis 후보를 추가했습니다.",
                }
            )
            existing_ids.add(item_id)
        if len(evidence) != initial_count:
            story["evidence_to_use"] = evidence
            story["market_causality"] = compact_text(
                f"{story.get('market_causality') or ''} / auto_added_fact_data_analysis_support",
                180,
            )
            watch = "자동 보강 근거가 실제 방송 전 causal anchor로 충분한지 확인"
            if watch not in story.get("slide_plan", []):
                story["slide_plan"] = [*(story.get("slide_plan") or []), watch]
    return stories


def normalize_brief(brief: dict, input_payload: dict) -> dict:
    candidates = known_candidates(input_payload)
    stories = [normalize_storyline(story, index, candidates) for index, story in enumerate(brief.get("storylines") or [], start=1)]
    stories = repair_storyline_evidence_support(stories, candidates)
    ppt_assets = [asset for story in stories for asset in story.get("ppt_asset_queue", [])]
    talk_items = [
        evidence
        for story in stories
        for evidence in story.get("evidence_to_use", [])
        if candidates.get(evidence.get("item_id"), {}).get("talk_vs_slide") == "talk_only"
    ]
    drop_items = [item for story in stories for item in story.get("evidence_to_drop", [])]
    watchpoints = [compact_text(item, 180) for item in (brief.get("retrospective_watchpoints") or [])]
    learning = input_payload.get("retrospective_learning") or {}
    for action in learning.get("aggregate_actions") or []:
        point = compact_text(f"retrospective_learning: {action}", 180)
        if point and point not in watchpoints:
            watchpoints.append(point)
    return {
        "broadcast_mode": brief.get("broadcast_mode") or "normal",
        "daily_thesis": compact_text(brief.get("daily_thesis"), 180),
        "one_line_market_frame": compact_text(brief.get("one_line_market_frame") or brief.get("daily_thesis"), 180),
        "market_map_summary": compact_text(brief.get("market_map_summary") or "시장 지도는 별도 차트와 히트맵으로 확인합니다.", 260),
        "editorial_summary": compact_text(brief.get("editorial_summary"), 900),
        "ppt_asset_queue": [normalize_asset(item, item.get("storyline_id") or "brief", pos) for pos, item in enumerate(brief.get("ppt_asset_queue") or ppt_assets, start=1)],
        "talk_only_queue": [normalize_evidence(item, candidates) for item in (brief.get("talk_only_queue") or talk_items)],
        "drop_list": [normalize_evidence(item, candidates, drop=True) for item in (brief.get("drop_list") or drop_items)],
        "retrospective_watchpoints": watchpoints[:12],
        "storylines": stories,
    }


def fallback_brief(target_date: str, reason: str, raw_response_id: str | None = None, raw_response_path: str = "") -> dict:
    radar = load_json(PROCESSED_DIR / target_date / "market-radar.json")
    candidates = {item.get("id"): item for item in radar.get("candidates") or []}
    storylines = []
    for index, story in enumerate((radar.get("storylines") or [])[:3], start=1):
        storyline_id = story.get("storyline_id") or f"fallback-{index}"
        evidence = []
        selected_items = []
        for item_id in story.get("selected_item_ids") or []:
            item = candidates.get(item_id)
            if not item:
                continue
            selected_items.append(item)
            source_role = resolved_source_role(item)
            evidence_role = resolved_evidence_role(item, source_role)
            evidence.append(
                {
                    "item_id": item_id,
                    "evidence_id": item_id,
                    "title": title_of(item),
                    "source_role": source_role,
                    "evidence_role": evidence_role,
                    "reason": "기존 점수 기반 후보에서 선택된 자료입니다.",
                }
            )
        if not any(item.get("evidence_role") in {"fact", "data", "analysis"} for item in evidence):
            for item in support_candidates_for_story(story, selected_items, list(candidates.values()), limit=2):
                item_id = str(item.get("id") or item.get("item_id") or "")
                if not item_id:
                    continue
                selected_items.append(item)
                source_role = resolved_source_role(item)
                evidence_role = resolved_evidence_role(item, source_role)
                evidence.append(
                    {
                        "item_id": item_id,
                        "evidence_id": item_id,
                        "title": title_of(item),
                        "source_role": source_role,
                        "evidence_role": evidence_role,
                        "reason": "fallback 보강: X/커뮤니티 단독 근거가 되지 않도록 같은 테마의 fact/data/analysis 후보를 붙였습니다.",
                    }
                )
        stars = int(story.get("recommendation_stars") or 2)
        ppt_assets = story.get("ppt_asset_queue") or [
            asset_from_candidate(item, storyline_id, priority)
            for priority, item in enumerate([row for row in selected_items if is_visual_candidate(row)][:4], start=1)
        ]
        drop_items = story.get("evidence_to_drop") or []
        storylines.append(
            {
                "storyline_id": storyline_id,
                "rank": index,
                "title": compact_text(story.get("title"), 80),
                "recommendation_stars": max(1, min(3, stars)),
                "rating_reason": story.get("recommendation_label") or star_label(stars),
                "lead_candidate_reason": compact_text(story.get("lead_candidate_reason") or story.get("why_selected") or "", 220),
                "hook": compact_text(story.get("one_liner") or story.get("title"), 180),
                "why_now": compact_text(story.get("why_selected") or "오늘 수집 자료에서 상대적으로 강하게 잡힌 방송 후보입니다.", 220),
                "core_argument": compact_text(story.get("angle") or story.get("one_liner") or "", 220),
                "signal_or_noise": story.get("signal_or_noise") or "watch",
                "market_causality": story.get("market_causality") or "fallback_needs_manual_pairing_check",
                "expectation_gap": story.get("expectation_gap") or "check_if_relevant",
                "prepricing_risk": story.get("prepricing_risk") or "check_if_relevant",
                "first_5min_fit": story.get("first_5min_fit") or "medium",
                "korea_open_relevance": story.get("korea_open_relevance") or "medium",
                "evidence_to_use": evidence[:4],
                "evidence_to_drop": drop_items,
                "drop_code": story.get("drop_code") or "",
                "slide_order": [title for title in (story.get("slide_order") or []) if title][:3]
                or [item["title"] for item in evidence[:3]],
                "slide_plan": story.get("slide_plan") or [item["title"] for item in evidence[:3]],
                "ppt_asset_queue": ppt_assets,
                "talk_track": compact_text(story.get("talk_track") or story.get("one_liner") or story.get("angle"), 260),
                "counterpoint": "API 편집 단계가 실패해 기존 규칙 기반 후보를 사용했습니다. 방송 전 사람이 강약을 확인해야 합니다.",
                "what_would_change_my_mind": "fact/data/analysis 근거가 반대로 확인되면 리드 판단을 낮춥니다.",
                "closing_line": compact_text(story.get("one_liner") or story.get("title"), 180),
            }
        )
    ppt_assets = [asset for story in storylines for asset in story.get("ppt_asset_queue", [])]
    drop_items = [item for story in storylines for item in story.get("evidence_to_drop", [])]
    return {
        "ok": True,
        "fallback": True,
        "fallback_reason": reason,
        "target_date": target_date,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "model": None,
        "raw_response_id": raw_response_id,
        "raw_response_path": raw_response_path,
        "broadcast_mode": "normal",
        "daily_thesis": compact_text((storylines[0]["hook"] if storylines else "") or "오늘 시장의 핵심 질문을 선별합니다.", 140),
        "one_line_market_frame": compact_text((storylines[0]["hook"] if storylines else "") or "오늘 시장의 핵심 질문을 선별합니다.", 140),
        "market_map_summary": "fallback 결과입니다. 시장 지도는 지수/히트맵/금리/유가/달러/비트코인 차트에서 수동 확인하세요.",
        "editorial_summary": "OpenAI 편집장 단계가 실패해 기존 market-radar 스토리라인을 사용했습니다.",
        "ppt_asset_queue": ppt_assets,
        "talk_only_queue": [],
        "drop_list": drop_items,
        "retrospective_watchpoints": ["fallback_used", "manual_editorial_review_required"],
        "storylines": storylines,
    }


def validate_brief(brief: dict, input_payload: dict) -> list[str]:
    errors = []
    if not brief.get("daily_thesis"):
        errors.append("missing daily_thesis")
    if not brief.get("editorial_summary"):
        errors.append("missing editorial_summary")
    stories = brief.get("storylines")
    if not isinstance(stories, list) or len(stories) < 3:
        errors.append("storylines must contain at least 3 items")
        return errors
    known_ids = {
        str(value)
        for item in input_payload.get("candidates") or []
        for value in [item.get("id"), item.get("item_id")]
        if value
    }
    titles = []
    for index, story in enumerate(stories, start=1):
        title = compact_text(story.get("title"))
        if not title:
            errors.append(f"storyline {index} missing title")
        titles.append(title)
        stars = story.get("recommendation_stars")
        if not isinstance(stars, int) or stars < 1 or stars > 3:
            errors.append(f"storyline {index} invalid recommendation_stars")
        for key in ["hook", "why_now", "talk_track"]:
            if not compact_text(story.get(key)):
                errors.append(f"storyline {index} missing {key}")
        for key in ["storyline_id", "lead_candidate_reason", "signal_or_noise", "market_causality", "first_5min_fit"]:
            if not compact_text(story.get(key)):
                errors.append(f"storyline {index} missing {key}")
        evidence = story.get("evidence_to_use")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"storyline {index} missing evidence_to_use")
        for item in evidence or []:
            if item.get("item_id") not in known_ids:
                errors.append(f"storyline {index} unknown evidence item_id: {item.get('item_id')}")
            if not item.get("evidence_id"):
                errors.append(f"storyline {index} evidence missing evidence_id")
    duplicates = {title for title in titles if titles.count(title) > 1 and title}
    if duplicates:
        errors.append(f"duplicate storyline titles: {', '.join(sorted(duplicates))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-candidates", type=int, default=28)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--response-fixture", type=Path, help="Read a saved OpenAI response or brief JSON instead of calling the API.")
    parser.add_argument("--output", type=Path, help="Write the generated brief to a custom path instead of data/processed/<date>/editorial-brief.json.")
    parser.add_argument("--prompt-output", type=Path, help="Write the exact local prompt payload to a JSON file without printing secrets.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    model = args.model or env.get("AUTOPARK_EDITORIAL_MODEL") or env.get("AUTOPARK_OPENAI_MODEL") or DEFAULT_MODEL
    fixture_meta = load_optional_json(args.response_fixture) if args.response_fixture else {}
    fixture_model = fixture_meta.get("model") if isinstance(fixture_meta, dict) else None
    input_payload = build_input_payload(args.date, args.max_candidates)
    output_path = args.output or (PROCESSED_DIR / args.date / "editorial-brief.json")
    if args.prompt_output:
        write_json(
            args.prompt_output,
            {
                "ok": True,
                "target_date": args.date,
                "model": model,
                "input_payload": input_payload,
                "prompt": build_prompt(input_payload),
            },
        )

    if args.dry_run:
        preview = {
            "ok": True,
            "status": "dry-run",
            "target_date": args.date,
            "model": model,
            "output": str(output_path),
            "candidate_count": len(input_payload.get("candidates") or []),
            "prompt_payload": input_payload,
        }
        print_json(preview)
        return 0

    response_id = None
    raw_response_path = ""
    try:
        if args.response_fixture:
            brief, response_id = load_fixture_response(args.response_fixture)
            response_source = "fixture"
        else:
            token = env.get("OPENAI_API_KEY")
            if not token:
                raise RuntimeError("missing_openai_api_key")
            brief, response_id = call_openai(build_prompt(input_payload), token, model, args.timeout)
            response_source = "openai_responses_api"
        if args.response_fixture and args.response_fixture.resolve().parent == (RUNTIME_DIR / "openai-responses").resolve():
            raw_response_path = str(args.response_fixture.resolve())
        else:
            raw_response_path = str(write_raw_editorial_response(args.date, model, response_id, brief, response_source))
        brief = normalize_brief(brief, input_payload)
        errors = validate_brief(brief, input_payload)
        if errors:
            raise ValueError("; ".join(errors))
        brief = {
            "ok": True,
            "fallback": False,
            "target_date": args.date,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": fixture_model or ("fixture" if args.response_fixture else model),
            "raw_response_id": response_id,
            "raw_response_path": raw_response_path,
            **brief,
            "retrospective_learning_applied": {
                "available": bool((input_payload.get("retrospective_learning") or {}).get("available")),
                "aggregate_label_counts": (input_payload.get("retrospective_learning") or {}).get("aggregate_label_counts") or {},
                "aggregate_actions": (input_payload.get("retrospective_learning") or {}).get("aggregate_actions") or [],
            },
        }
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        brief = fallback_brief(args.date, f"{type(exc).__name__}: {exc}", raw_response_id=response_id, raw_response_path=raw_response_path)

    write_json(output_path, brief)
    print_json(
        {
            "ok": True,
            "fallback": bool(brief.get("fallback")),
            "output": str(output_path),
            "model": brief.get("model"),
            "raw_response_path": brief.get("raw_response_path"),
            "storyline_count": len(brief.get("storylines") or []),
            "fallback_reason": brief.get("fallback_reason"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
