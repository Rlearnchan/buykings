#!/usr/bin/env python3
"""Build the upstream Market Focus Brief for Autopark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from source_policy import infer_source_policy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHART_DIR = PROJECT_ROOT / "charts"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
RUNTIME_NOTION_DIR = RUNTIME_DIR / "notion"
EXPORTS_DIR = PROJECT_ROOT / "exports" / "current"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "market_focus_brief.md"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_API_TIMEOUT_SECONDS = 180

BROADCAST_USES = {"lead", "supporting_story", "talk_only", "drop"}
PUBLIC_USES = {"lead", "supporting_story", "talk_only"}
LOCAL_ALIAS_KEY = "_local_evidence_aliases"


class OpenAIAPIError(RuntimeError):
    def __init__(self, label: str, status: int | None, api_code: str, message: str, body: str = "") -> None:
        self.label = label
        self.status = status
        self.api_code = api_code
        self.message = message
        self.body = body
        super().__init__(f"{label}: status={status}; api_code={api_code}; message={message}")


FOCUS_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rank",
        "focus",
        "market_question",
        "why_it_matters",
        "price_confirmation",
        "broadcast_use",
        "confidence",
        "suggested_story_title",
        "one_sentence_for_host",
        "source_ids",
        "evidence_ids",
        "missing_assets",
    ],
    "properties": {
        "rank": {"type": "integer", "minimum": 1, "maximum": 12},
        "focus": {"type": "string"},
        "market_question": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "price_confirmation": {"type": "string"},
        "broadcast_use": {
            "type": "string",
            "enum": ["lead", "supporting_story", "talk_only", "drop"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "suggested_story_title": {"type": "string"},
        "one_sentence_for_host": {"type": "string"},
        "source_ids": {"type": "array", "items": {"type": "string"}},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "missing_assets": {"type": "array", "items": {"type": "string"}},
    },
}

FALSE_LEAD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["focus", "reason", "source_ids", "evidence_ids", "drop_code"],
    "properties": {
        "focus": {"type": "string"},
        "reason": {"type": "string"},
        "source_ids": {"type": "array", "items": {"type": "string"}},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "drop_code": {"type": "string"},
    },
}

SOURCE_GAP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["issue", "why_needed", "search_hint", "safe_for_public", "related_focus_rank"],
    "properties": {
        "issue": {"type": "string"},
        "why_needed": {"type": "string"},
        "search_hint": {"type": "string"},
        "safe_for_public": {"type": "boolean"},
        "related_focus_rank": {"type": "integer", "minimum": 0, "maximum": 12},
    },
}

ORDER_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rank",
        "focus_rank",
        "suggested_story_title",
        "broadcast_use",
        "one_sentence_for_host",
        "evidence_ids",
    ],
    "properties": {
        "rank": {"type": "integer", "minimum": 1, "maximum": 12},
        "focus_rank": {"type": "integer", "minimum": 1, "maximum": 12},
        "suggested_story_title": {"type": "string"},
        "broadcast_use": {
            "type": "string",
            "enum": ["lead", "supporting_story", "talk_only", "drop"],
        },
        "one_sentence_for_host": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
    },
}

MARKET_FOCUS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "market_focus_summary",
        "what_market_is_watching",
        "false_leads",
        "missing_assets",
        "source_gaps",
        "suggested_broadcast_order",
    ],
    "properties": {
        "market_focus_summary": {"type": "string"},
        "what_market_is_watching": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": FOCUS_ITEM_SCHEMA,
        },
        "false_leads": {"type": "array", "items": FALSE_LEAD_SCHEMA},
        "missing_assets": {"type": "array", "items": {"type": "string"}},
        "source_gaps": {"type": "array", "items": SOURCE_GAP_SCHEMA},
        "suggested_broadcast_order": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": ORDER_ITEM_SCHEMA,
        },
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


def load_optional_json(path: Path | None) -> dict:
    if not path or not path.exists():
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


def compact_text(value: object, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def estimate_prompt_tokens(prompt: str) -> int:
    return max(1, int((len(prompt or "") + 3) / 4))


def sanitized_text(value: object, limit: int = 420) -> str:
    text = compact_text(value, limit * 2)
    text = re.sub(r"https?\s*:\s*/\s*/\s*\S+", "[link]", text, flags=re.I)
    text = re.sub(r"\bwww\.\S+", "[link]", text, flags=re.I)
    text = re.sub(r"[A-Za-z]:\\[^\s]+", "[path]", text)
    text = re.sub(r"(?:runtime|exports)[\\/][^\s]+", "[path]", text, flags=re.I)
    return compact_text(text, limit)


def unique_strings(values: list[object] | tuple[object, ...] | set[object]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        text = compact_text(value, 240)
        if not text or text in seen:
            continue
        rows.append(text)
        seen.add(text)
    return rows


def evidence_alias(value: object) -> str:
    digest = hashlib.sha1(str(value or "").encode("utf-8")).hexdigest()[:10]
    return f"ev_{digest}"


def alias_for(value: object, aliases: dict[str, str]) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    alias = evidence_alias(text)
    aliases.setdefault(alias, text)
    return alias


def title_of(item: dict) -> str:
    return compact_text(
        item.get("title")
        or item.get("headline")
        or item.get("summary")
        or item.get("text")
        or item.get("id"),
        160,
    )


def source_of(item: dict) -> str:
    return compact_text(
        item.get("source")
        or item.get("source_name")
        or item.get("source_id")
        or item.get("publisher")
        or item.get("type")
        or "",
        90,
    )


def item_id_of(item: dict) -> str:
    return str(item.get("item_id") or item.get("id") or item.get("url") or item.get("title") or "")


def score_of(item: dict) -> float:
    try:
        return float(item.get("score") or item.get("final_score") or item.get("cluster_score") or 0)
    except (TypeError, ValueError):
        return 0.0


def microcopy_by_item_id(payload: dict) -> dict[str, dict]:
    return {
        str(item.get("item_id") or ""): item
        for item in payload.get("items") or []
        if isinstance(item, dict) and item.get("item_id")
    }


def attach_evidence_microcopy(rows: list[dict], microcopy: dict) -> list[dict]:
    lookup = microcopy_by_item_id(microcopy)
    enriched = []
    for row in rows:
        item = dict(row)
        copy = lookup.get(item_id_of(item))
        if copy:
            item["micro_title"] = compact_text(copy.get("title") or "", 28)
            item["micro_content"] = compact_text(
                copy.get("content") or " ".join((copy.get("summary_bullets") or [])[:1]),
                300,
            )
        enriched.append(item)
    return enriched


def compact_candidate(item: dict) -> dict:
    policy = infer_source_policy(item)
    return {
        "id": item_id_of(item),
        "item_id": item_id_of(item),
        "title": title_of(item),
        "source": source_of(item),
        "url": item.get("url") or "",
        "published_at": item.get("published_at") or item.get("captured_at") or "",
        "score": score_of(item),
        "source_role": item.get("source_role") or "",
        "evidence_role": item.get("evidence_role") or "",
        "source_tier": item.get("source_tier") or policy.get("tier") or "",
        "source_authority": item.get("source_authority") or policy.get("authority") or "",
        "source_use_role": item.get("source_use_role") or policy.get("use_role") or "",
        "source_llm_policy": item.get("source_llm_policy") or policy.get("llm_policy") or "",
        "source_lead_allowed": bool(item.get("source_lead_allowed") if "source_lead_allowed" in item else policy.get("lead_allowed")),
        "theme_keys": item.get("theme_keys") or item.get("market_hooks") or [],
        "market_reaction": compact_text(item.get("market_reaction") or "", 180),
        "signal_or_noise": compact_text(item.get("signal_or_noise") or "", 80),
        "expectation_gap": compact_text(item.get("expectation_gap") or "", 120),
        "prepricing_risk": compact_text(item.get("prepricing_risk") or "", 120),
        "korea_open_relevance": compact_text(item.get("korea_open_relevance") or "", 120),
        "radar_question": compact_text(item.get("radar_question") or "", 180),
        "summary": compact_text(item.get("summary") or item.get("description") or "", 320),
        "micro_title": compact_text(item.get("micro_title") or "", 28),
        "micro_content": compact_text(item.get("micro_content") or "", 300),
        "visual_local_path": item.get("visual_local_path") or "",
        "image_refs": [
            {
                "local_path": image.get("local_path") or "",
                "alt": compact_text(image.get("alt") or image.get("caption") or "", 120),
            }
            for image in (item.get("image_refs") or [])[:3]
            if isinstance(image, dict)
        ],
    }


def compact_storyline(story: dict) -> dict:
    return {
        "storyline_id": story.get("storyline_id") or "",
        "rank": story.get("rank") or 0,
        "title": compact_text(story.get("title"), 160),
        "one_liner": compact_text(story.get("one_liner") or story.get("hook") or "", 260),
        "why_selected": compact_text(story.get("why_selected") or story.get("lead_candidate_reason") or "", 300),
        "angle": compact_text(story.get("angle") or story.get("core_argument") or "", 300),
        "recommendation_stars": story.get("recommendation_stars") or 1,
        "theme_keys": story.get("theme_keys") or [],
        "selected_item_ids": unique_strings(story.get("selected_item_ids") or []),
        "material_refs": [
            {
                "id": ref.get("id") or ref.get("item_id") or "",
                "title": compact_text(ref.get("title"), 120),
                "source": compact_text(ref.get("source"), 90),
                "url": ref.get("url") or "",
            }
            for ref in (story.get("material_refs") or [])[:6]
            if isinstance(ref, dict)
        ],
    }


def referenced_ids_from_storylines(storylines: list[dict]) -> set[str]:
    ids: set[str] = set()
    for story in storylines:
        ids.update(str(item) for item in story.get("selected_item_ids") or [] if item)
        for ref in story.get("material_refs") or []:
            if ref.get("id"):
                ids.add(str(ref["id"]))
            if ref.get("item_id"):
                ids.add(str(ref["item_id"]))
    return ids


def select_focus_candidates(radar: dict, max_candidates: int) -> list[dict]:
    rows = [row for row in radar.get("candidates") or [] if item_id_of(row)]
    required_ids = referenced_ids_from_storylines(radar.get("storylines") or [])
    by_id = {item_id_of(row): row for row in rows}
    selected: list[dict] = []
    seen: set[str] = set()

    for item_id in required_ids:
        if item_id in by_id and item_id not in seen:
            selected.append(by_id[item_id])
            seen.add(item_id)

    for row in sorted(rows, key=lambda item: (score_of(item), bool(item.get("visual_local_path")), title_of(item)), reverse=True):
        item_id = item_id_of(row)
        if item_id in seen:
            continue
        selected.append(row)
        seen.add(item_id)
        if len(selected) >= max_candidates:
            break

    return selected


def sample_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        for key in ["candidates", "posts", "items", "articles", "events", "rows"]:
            rows = payload.get(key)
            if isinstance(rows, list):
                break
        else:
            rows = []
    else:
        rows = []
    samples = []
    for row in rows[:8]:
        if not isinstance(row, dict):
            continue
        samples.append(
            {
                "id": row.get("id") or row.get("url") or row.get("title") or row.get("headline") or "",
                "title": title_of(row),
                "source": source_of(row),
                "url": row.get("url") or row.get("source_url") or "",
                "published_at": row.get("published_at") or row.get("created_at") or "",
                "summary": compact_text(row.get("summary") or row.get("text") or "", 220),
            }
        )
    return samples


def raw_file_kind(path: Path) -> str:
    rel = path.as_posix().lower()
    name = path.name.lower()
    if name.startswith("x") or "/x-" in rel or "x-timeline" in rel:
        return "x_social_sentiment"
    if "today-misc" in rel or "news" in name or any(
        token in rel for token in ["cnbc", "reuters", "yahoo", "tradingview", "factset", "isabelnet", "biztoc"]
    ):
        return "news_or_analysis"
    if "market-data" in name or "fedwatch" in name or "fear-greed" in name or "finviz" in name:
        return "market_reaction_or_data"
    return "other"


def should_include_raw_file(path: Path) -> bool:
    kind = raw_file_kind(path)
    return kind in {"x_social_sentiment", "news_or_analysis", "market_reaction_or_data"}


def compact_raw_file(path: Path, raw_root: Path) -> dict:
    payload = load_optional_json(path)
    source = payload.get("source") if isinstance(payload, dict) else {}
    source = source if isinstance(source, dict) else {}
    items = sample_items(payload)
    source_id = (
        payload.get("source_id")
        if isinstance(payload, dict)
        else ""
    ) or source.get("id") or path.stem
    source_name = (
        payload.get("name")
        if isinstance(payload, dict)
        else ""
    ) or source.get("name") or source_id
    return {
        "source_id": compact_text(source_id, 120),
        "source_name": compact_text(source_name, 120),
        "kind": raw_file_kind(path),
        "relative_path": str(path.relative_to(raw_root.parent)),
        "url": (payload.get("url") if isinstance(payload, dict) else "") or source.get("url") or "",
        "captured_at": payload.get("captured_at") if isinstance(payload, dict) else "",
        "status": payload.get("status") if isinstance(payload, dict) else "",
        "item_count": len(items),
        "sample_items": items,
    }


def collect_raw_sources(target_date: str, max_files: int) -> list[dict]:
    raw_root = RAW_DIR / target_date
    if not raw_root.exists():
        return []
    files = [path for path in sorted(raw_root.rglob("*.json")) if should_include_raw_file(path)]
    compacted = [compact_raw_file(path, raw_root) for path in files[:max_files]]
    return compacted


def compact_chart(path: Path) -> dict:
    payload = load_optional_json(path)
    slug = payload.get("slug") or path.name.removesuffix("-datawrapper.json")
    return {
        "chart_id": slug,
        "title": compact_text(payload.get("title"), 160),
        "subtitle": compact_text(payload.get("subtitle"), 120),
        "source_name": compact_text(payload.get("source_name"), 80),
        "source_url": payload.get("source_url") or "",
        "export_png": str(EXPORTS_DIR / f"{slug}.png") if (EXPORTS_DIR / f"{slug}.png").exists() else "",
    }


def collect_charts() -> list[dict]:
    return [compact_chart(path) for path in sorted(CHART_DIR.glob("*-datawrapper.json"))]


def collect_screenshot_assets(target_date: str, limit: int) -> list[dict]:
    roots = [RUNTIME_DIR / "screenshots" / target_date, RUNTIME_DIR / "assets" / target_date, EXPORTS_DIR]
    rows = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "asset_id": path.stem,
                    "path": str(path),
                    "kind": "screenshot" if root != EXPORTS_DIR else "chart_export",
                    "name": path.name,
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def sanitize_candidate(item: dict, aliases: dict[str, str]) -> dict:
    raw_id = item.get("id") or item.get("item_id") or item.get("url") or title_of(item)
    item_alias = alias_for(raw_id, aliases)
    policy = infer_source_policy(item)
    return {
        "id": item_alias,
        "item_id": item_alias,
        "source_id": sanitized_text(source_of(item), 80),
        "source_role": sanitized_text(item.get("source_role") or "", 60),
        "evidence_role": sanitized_text(item.get("evidence_role") or "", 60),
        "source_tier": sanitized_text(item.get("source_tier") or policy.get("tier") or "", 40),
        "source_authority": sanitized_text(item.get("source_authority") or policy.get("authority") or "", 40),
        "source_use_role": sanitized_text(item.get("source_use_role") or policy.get("use_role") or "", 60),
        "source_llm_policy": sanitized_text(item.get("source_llm_policy") or policy.get("llm_policy") or "", 80),
        "source_lead_allowed": bool(item.get("source_lead_allowed") if "source_lead_allowed" in item else policy.get("lead_allowed")),
        "title": sanitized_text(title_of(item), 100),
        "compact_summary": sanitized_text(item.get("summary") or item.get("description") or "", 320),
        "theme_keys": item.get("theme_keys") or item.get("market_hooks") or [],
        "market_reaction": sanitized_text(item.get("market_reaction") or "", 180),
        "signal_or_noise": sanitized_text(item.get("signal_or_noise") or "", 80),
        "expectation_gap": sanitized_text(item.get("expectation_gap") or "", 120),
        "prepricing_risk": sanitized_text(item.get("prepricing_risk") or "", 120),
        "korea_open_relevance": sanitized_text(item.get("korea_open_relevance") or "", 120),
        "radar_question": sanitized_text(item.get("radar_question") or "", 180),
        "micro_title": sanitized_text(item.get("micro_title") or "", 28),
        "micro_content": sanitized_text(item.get("micro_content") or "", 300),
        "asset_status": "capture_candidate" if item.get("visual_local_path") or item.get("image_refs") else "no_capture",
    }


def sanitize_storyline(story: dict, aliases: dict[str, str]) -> dict:
    selected = [alias_for(item_id, aliases) for item_id in story.get("selected_item_ids") or []]
    refs = []
    for ref in (story.get("material_refs") or [])[:6]:
        if not isinstance(ref, dict):
            continue
        raw_id = ref.get("id") or ref.get("item_id") or ref.get("url") or ref.get("title")
        refs.append(
            {
                "id": alias_for(raw_id, aliases),
                "title": sanitized_text(ref.get("title"), 100),
                "source": sanitized_text(ref.get("source"), 80),
            }
        )
    return {
        "storyline_id": story.get("storyline_id") or "",
        "rank": story.get("rank") or 0,
        "title": sanitized_text(story.get("title"), 140),
        "one_liner": sanitized_text(story.get("one_liner") or story.get("hook") or "", 220),
        "why_selected": sanitized_text(story.get("why_selected") or story.get("lead_candidate_reason") or "", 260),
        "angle": sanitized_text(story.get("angle") or story.get("core_argument") or "", 260),
        "recommendation_stars": story.get("recommendation_stars") or 1,
        "theme_keys": story.get("theme_keys") or [],
        "selected_item_ids": [item for item in selected if item],
        "material_refs": refs,
    }


def sanitize_raw_source(source: dict, aliases: dict[str, str]) -> dict:
    sample_rows = []
    for item in source.get("sample_items") or []:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id") or item.get("url") or item.get("title")
        sample_rows.append(
            {
                "id": alias_for(raw_id, aliases),
                "title": sanitized_text(item.get("title") or item.get("headline") or "", 100),
                "summary": sanitized_text(item.get("summary") or item.get("description") or item.get("text") or "", 180),
            }
        )
    return {
        "source_id": sanitized_text(source.get("source_id"), 100),
        "source_name": sanitized_text(source.get("source_name"), 100),
        "kind": sanitized_text(source.get("kind"), 80),
        "status": sanitized_text(source.get("status"), 80),
        "item_count": source.get("item_count") or len(sample_rows),
        "sample_items": sample_rows[:8],
    }


def sanitize_chart(chart: dict) -> dict:
    return {
        "chart_id": compact_text(chart.get("chart_id"), 80),
        "title": compact_text(chart.get("title"), 140),
        "takeaway": compact_text(chart.get("takeaway"), 200),
        "latest_value": compact_text(chart.get("latest_value"), 80),
        "asset_status": "available",
    }


def sanitize_asset(asset: dict) -> dict:
    return {
        "asset_id": compact_text(asset.get("asset_id"), 100),
        "kind": compact_text(asset.get("kind"), 80),
        "asset_status": "available",
    }


def compact_preflight_agenda(agenda: dict) -> dict:
    if not agenda or not isinstance(agenda.get("agenda_items"), list):
        return {}
    return {
        "date": agenda.get("date") or agenda.get("target_date") or "",
        "fallback": bool(agenda.get("fallback")),
        "fallback_code": agenda.get("fallback_code") or "",
        "preflight_summary": compact_text(agenda.get("preflight_summary"), 100),
        "agenda_items": [
            {
                "rank": item.get("rank") or index,
                "agenda_id": compact_text(item.get("agenda_id"), 80),
                "market_question": compact_text(item.get("market_question"), 180),
                "why_to_check": compact_text(item.get("why_to_check"), 220),
                "expected_broadcast_use": compact_text(item.get("expected_broadcast_use"), 60),
                "collection_targets": [
                    {
                        "target_type": compact_text(target.get("target_type"), 60),
                        "query_or_asset": compact_text(target.get("query_or_asset"), 140),
                        "preferred_sources": unique_strings(target.get("preferred_sources") or [])[:6],
                        "reason": compact_text(target.get("reason"), 160),
                    }
                    for target in (item.get("collection_targets") or [])[:8]
                    if isinstance(target, dict)
                ],
                "must_verify_with_local_evidence": bool(item.get("must_verify_with_local_evidence")) is True,
                "public_safe": False,
            }
            for index, item in enumerate((agenda.get("agenda_items") or [])[:6], start=1)
            if isinstance(item, dict)
        ],
        "collection_priorities": agenda.get("collection_priorities") or {},
        "source_gaps_to_watch": unique_strings(agenda.get("source_gaps_to_watch") or [])[:8],
    }


def compact_headline_river(river: dict) -> dict:
    if not isinstance(river, dict) or not river:
        return {}
    return {
        "date": river.get("date") or "",
        "source": "headline_river",
        "item_count": river.get("item_count") or len(river.get("items") or []),
        "baseline_source_ids": unique_strings(river.get("baseline_source_ids") or [])[:8],
        "support_source_ids": unique_strings(river.get("support_source_ids") or [])[:8],
        "agenda_expansions": [
            {
                "agenda_id": compact_text(item.get("agenda_id"), 80),
                "rank": item.get("rank") or index,
                "tickers": unique_strings(item.get("tickers") or [])[:12],
            }
            for index, item in enumerate((river.get("agenda_expansions") or [])[:8], start=1)
            if isinstance(item, dict)
        ],
        "source_stats": [
            {
                "source_id": compact_text(stat.get("source_id"), 80),
                "source_label": compact_text(stat.get("source_label"), 80),
                "status": compact_text(stat.get("status"), 40),
                "source_role": compact_text(stat.get("source_role"), 60),
                "item_count": stat.get("item_count") or 0,
            }
            for stat in (river.get("source_stats") or [])[:16]
            if isinstance(stat, dict)
        ],
        "anomaly_summary": {
            "top_keywords": [
                {"keyword": compact_text(row.get("keyword"), 40), "count": row.get("count") or 0}
                for row in ((river.get("anomaly_summary") or {}).get("top_keywords") or [])[:12]
                if isinstance(row, dict)
            ],
            "top_hosts": [
                {"host": compact_text(row.get("host"), 80), "count": row.get("count") or 0}
                for row in ((river.get("anomaly_summary") or {}).get("top_hosts") or [])[:12]
                if isinstance(row, dict)
            ],
            "top_title_tokens": [
                {"token": compact_text(row.get("token"), 40), "count": row.get("count") or 0}
                for row in ((river.get("anomaly_summary") or {}).get("top_title_tokens") or [])[:16]
                if isinstance(row, dict)
            ],
        },
        "sample_items": [
            {
                "item_id": compact_text(item.get("item_id"), 80),
                "source_label": compact_text(item.get("source_label"), 80),
                "publisher": compact_text(item.get("publisher"), 80),
                "title": sanitized_text(item.get("title"), 140),
                "snippet": sanitized_text(item.get("snippet"), 220),
                "source_role": compact_text(item.get("source_role"), 60),
                "source_authority": compact_text(item.get("source_authority"), 40),
                "agenda_links": unique_strings(item.get("agenda_links") or [])[:6],
                "content_level": compact_text(item.get("content_level"), 40),
            }
            for item in (river.get("items") or [])[:40]
            if isinstance(item, dict)
        ],
    }


def compact_analysis_river(river: dict) -> dict:
    if not isinstance(river, dict) or not river:
        return {}
    return {
        "date": river.get("date") or "",
        "source": "analysis_river",
        "item_count": river.get("item_count") or len(river.get("items") or []),
        "analysis_source_ids": unique_strings(river.get("analysis_source_ids") or [])[:16],
        "role_counts": [
            {"role": compact_text(row.get("role"), 60), "count": row.get("count") or 0}
            for row in (river.get("role_counts") or [])[:12]
            if isinstance(row, dict)
        ],
        "source_stats": [
            {
                "source_id": compact_text(stat.get("source_id"), 80),
                "source_label": compact_text(stat.get("source_label"), 80),
                "status": compact_text(stat.get("status"), 40),
                "source_role": compact_text(stat.get("source_role"), 60),
                "item_count": stat.get("item_count") or 0,
            }
            for stat in (river.get("source_stats") or [])[:20]
            if isinstance(stat, dict)
        ],
        "sample_items": [
            {
                "item_id": compact_text(item.get("item_id"), 80),
                "source_label": compact_text(item.get("source_label"), 80),
                "title": sanitized_text(item.get("title"), 140),
                "summary": sanitized_text(item.get("summary"), 240),
                "source_role": compact_text(item.get("source_role"), 60),
                "source_authority": compact_text(item.get("source_authority"), 40),
                "content_level": compact_text(item.get("content_level"), 40),
                "detected_keywords": unique_strings(item.get("detected_keywords") or [])[:8],
            }
            for item in (river.get("items") or [])[:36]
            if isinstance(item, dict)
        ],
    }


def sanitize_local_packet(payload: dict) -> dict:
    aliases: dict[str, str] = {}
    radar = payload.get("market_radar") or {}
    sanitized = {
        "date": payload.get("date"),
        "packet_mode": "sanitized_local",
        "policy": {
            **(payload.get("policy") or {}),
            "sanitized_local_packet": True,
            "raw_urls_excluded": True,
            "screenshot_paths_excluded": True,
            "full_article_and_social_text_excluded": True,
            "preflight_is_hypothesis_only": True,
        },
        "market_preflight_agenda": compact_preflight_agenda(payload.get("market_preflight_agenda") or {}),
        "headline_river": compact_headline_river(payload.get("headline_river") or {}),
        "analysis_river": compact_analysis_river(payload.get("analysis_river") or {}),
        "market_radar": {
            "candidate_count": radar.get("candidate_count") or len(radar.get("candidates") or []),
            "storylines": [sanitize_storyline(story, aliases) for story in (radar.get("storylines") or [])[:8]],
            "candidates": [sanitize_candidate(item, aliases) for item in (radar.get("candidates") or [])],
        },
        "visual_cards": [
            {
                "id": sanitized_text(item.get("id") or item.get("title") or "", 80),
                "title": sanitized_text(item.get("title") or "", 100),
                "summary": sanitized_text(item.get("summary") or item.get("caption") or "", 180),
                "asset_status": "available" if item.get("path") else "metadata_only",
            }
            for item in payload.get("visual_cards") or []
            if isinstance(item, dict)
        ],
        "raw_sources": [sanitize_raw_source(source, aliases) for source in payload.get("raw_sources") or []],
        "charts": [sanitize_chart(chart) for chart in payload.get("charts") or []],
        "available_assets": [sanitize_asset(asset) for asset in payload.get("available_assets") or []],
        "input_limits": payload.get("input_limits") or {},
        LOCAL_ALIAS_KEY: aliases,
    }
    return sanitized


def prompt_payload(payload: dict) -> dict:
    if isinstance(payload, dict):
        return {key: prompt_payload(value) for key, value in payload.items() if not str(key).startswith("_")}
    if isinstance(payload, list):
        return [prompt_payload(item) for item in payload]
    return payload


def build_input_payload(target_date: str, max_candidates: int, max_raw_files: int, max_assets: int) -> dict:
    processed = PROCESSED_DIR / target_date
    radar = load_json(processed / "market-radar.json")
    evidence_microcopy = load_optional_json(processed / "evidence-microcopy.json")
    if evidence_microcopy:
        radar = {**radar, "candidates": attach_evidence_microcopy(radar.get("candidates") or [], evidence_microcopy)}
    visuals = load_json(processed / "visual-cards.json")
    candidates = select_focus_candidates(radar, max_candidates)
    raw_payload = {
        "date": target_date,
        "policy": {
            "role": "market_editor_not_news_summarizer",
            "primary_question": "What was the market actually watching around the prior US session?",
            "local_sources_first": True,
            "x_social_is_sentiment_only": True,
            "charts_are_reaction_not_causality": True,
            "missing_external_story_must_be_source_gap": True,
            "do_not_publish_story_without_local_item_id_or_evidence_id": True,
            "lead_rule": "best_market_explanation_first_5min_not_most_sensational",
        },
        "market_radar": {
            "candidate_count": radar.get("candidate_count") or len(radar.get("candidates") or []),
            "storylines": [compact_storyline(story) for story in (radar.get("storylines") or [])[:8]],
            "candidates": [compact_candidate(item) for item in candidates],
        },
        "visual_cards": [
            {
                "id": item.get("id") or item.get("title") or "",
                "title": title_of(item),
                "summary": compact_text(item.get("summary") or item.get("caption") or "", 220),
                "path": item.get("local_path") or item.get("visual_local_path") or "",
            }
            for item in (visuals.get("cards") or visuals.get("items") or [])[:24]
            if isinstance(item, dict)
        ],
        "raw_sources": collect_raw_sources(target_date, max_raw_files),
        "charts": collect_charts(),
        "available_assets": collect_screenshot_assets(target_date, max_assets),
        "market_preflight_agenda": load_optional_json(processed / "market-preflight-agenda.json"),
        "headline_river": load_optional_json(processed / "headline-river.json"),
        "analysis_river": load_optional_json(processed / "analysis-river.json"),
    }
    return sanitize_local_packet(raw_payload)


def synthetic_smoke_payload(target_date: str) -> dict:
    raw_payload = {
        "date": target_date,
        "policy": {
            "role": "market_editor_not_news_summarizer",
            "primary_question": "What was the market actually watching around the prior US session?",
            "local_sources_first": True,
            "x_social_is_sentiment_only": True,
            "charts_are_reaction_not_causality": True,
            "missing_external_story_must_be_source_gap": True,
            "do_not_publish_story_without_local_item_id_or_evidence_id": True,
            "lead_rule": "best_market_explanation_first_5min_not_most_sensational",
            "synthetic_smoke": True,
        },
        "market_radar": {
            "candidate_count": 3,
            "storylines": [
                {
                    "title": "Rates and dollar frame risk appetite",
                    "one_liner": "Synthetic market packet for API schema smoke.",
                    "why_selected": "Multiple synthetic local sources point to the same market question.",
                    "selected_item_ids": ["synthetic-fed-1", "synthetic-us10y-1"],
                    "material_refs": [],
                }
            ],
            "candidates": [
                {
                    "id": "synthetic-fed-1",
                    "item_id": "synthetic-fed-1",
                    "source": "Synthetic Wire",
                    "title": "Fed speaker keeps inflation risk in focus",
                    "summary": "Synthetic local fact item: inflation concern keeps rate sensitivity alive.",
                    "theme_keys": ["rates_macro"],
                    "source_role": "fact_anchor",
                    "evidence_role": "fact",
                },
                {
                    "id": "synthetic-us10y-1",
                    "item_id": "synthetic-us10y-1",
                    "source": "Synthetic Market Data",
                    "title": "US 10Y yield holds firm while growth stocks pause",
                    "summary": "Synthetic local market reaction item: yields and dollar constrain risk appetite.",
                    "theme_keys": ["rates_macro"],
                    "source_role": "market_reaction",
                    "evidence_role": "market_reaction",
                },
                {
                    "id": "synthetic-x-1",
                    "item_id": "synthetic-x-1",
                    "source": "Synthetic X",
                    "title": "Traders debate whether oil risk is real",
                    "summary": "Synthetic social sentiment item only; do not use as fact anchor.",
                    "theme_keys": ["oil_geopolitics"],
                    "source_role": "sentiment_probe",
                    "evidence_role": "sentiment",
                },
            ],
        },
        "visual_cards": [],
        "raw_sources": [
            {
                "source_id": "synthetic-news",
                "path": "synthetic/news.json",
                "kind": "news_or_analysis",
                "sample_items": [{"id": "synthetic-fed-1", "title": "Fed speaker keeps inflation risk in focus"}],
            },
            {
                "source_id": "synthetic-x",
                "path": "synthetic/x.json",
                "kind": "x_social_sentiment",
                "sample_items": [{"id": "synthetic-x-1", "title": "Traders debate whether oil risk is real"}],
            },
        ],
        "charts": [
            {
                "path": "synthetic/us10y-datawrapper.json",
                "chart_id": "us10y",
                "title": "US 10Y synthetic chart",
                "takeaway": "Rates remain the price confirmation to check.",
                "latest_value": "4.30%",
            }
        ],
        "available_assets": [],
        "input_limits": {"synthetic_smoke": True, "max_candidates": 3, "max_raw_files": 2, "max_assets": 0},
    }
    return sanitize_local_packet(raw_payload)


def known_evidence_ids(payload: dict) -> set[str]:
    ids: set[str] = {"market-radar"}
    ids.update(str(value) for value in (payload.get(LOCAL_ALIAS_KEY) or {}).values() if value)
    for item in payload.get("market_radar", {}).get("candidates") or []:
        for key in ["id", "item_id", "url"]:
            value = item.get(key)
            if value:
                ids.add(str(value))
    for story in payload.get("market_radar", {}).get("storylines") or []:
        ids.update(str(item) for item in story.get("selected_item_ids") or [] if item)
        for ref in story.get("material_refs") or []:
            if ref.get("id"):
                ids.add(str(ref["id"]))
    for source in payload.get("raw_sources") or []:
        if source.get("source_id"):
            ids.add(str(source["source_id"]))
        for item in source.get("sample_items") or []:
            for key in ["id", "url"]:
                value = item.get(key)
                if value:
                    ids.add(str(value))
    for chart in payload.get("charts") or []:
        if chart.get("chart_id"):
            ids.add(str(chart["chart_id"]))
    for asset in payload.get("available_assets") or []:
        for key in ["asset_id", "path"]:
            value = asset.get(key)
            if value:
                ids.add(str(value))
    return ids


def prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "You are a market editor. Return the required JSON only."


def build_prompt(payload: dict, with_web: bool = False) -> str:
    web_note = (
        "Web search is enabled. Use it only to flag source_gaps or verify that a local story is incomplete; "
        "do not turn a web-only discovery into a public story unless it is tied to local evidence_ids."
        if with_web
        else "Web search is disabled. Use only the local collected source packet."
    )
    return f"""{prompt_template()}

Runtime mode:
- {web_note}
- candidates[].micro_title is a short public title; candidates[].micro_content is one core summary in 1-3 sentences; do not let either change source order or promote unsupported stories.
- candidates[].source_tier/source_authority/source_use_role are trust hints only. Premium Reuters/Bloomberg/WSJ can anchor facts via sanitized summaries; market_data confirms reaction but not causality; social sources cannot be standalone fact evidence.
- market_preflight_agenda is today's hypothesis map. headline_river is the broad headline/anomaly layer. analysis_river is specialist commentary/chart/earnings context. Use them to spot missing angles, source gaps, and corroboration, but do not promote an issue unless candidates[] or charts provide local evidence.

Return JSON matching the provided schema. Do not wrap it in Markdown.

Input packet:
{json.dumps(prompt_payload(payload), ensure_ascii=False, indent=2)}
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


def extract_web_sources(raw: dict) -> list[dict]:
    sources: list[dict] = []
    for item in raw.get("output") or []:
        action = item.get("action") or {}
        for source in action.get("sources") or []:
            if isinstance(source, dict):
                sources.append(
                    {
                        "url": source.get("url") or "",
                        "title": compact_text(source.get("title") or "", 160),
                        "source": source.get("source") or "",
                    }
                )
    return sources


def classify_openai_error(status: int | None, api_code: str, message: str) -> str:
    text = f"{api_code} {message}".lower()
    if api_code in {"model_not_available", "model_not_found"}:
        return "model_not_available"
    if "model" in text and (
        "not available" in text
        or "does not exist" in text
        or "do not have access" in text
        or "not have access" in text
        or "not found" in text
    ):
        return "model_not_available"
    if status == 401:
        return "auth_failed"
    if status == 429:
        return "rate_limited"
    if status and status >= 500:
        return "openai_server_error"
    return "openai_api_error"


def openai_http_error(exc: urllib.error.HTTPError) -> OpenAIAPIError:
    body = exc.read().decode("utf-8", errors="replace")
    api_code = f"http_{exc.code}"
    message = exc.reason or body[:240]
    try:
        payload = json.loads(body)
        error = payload.get("error") if isinstance(payload, dict) else {}
        if isinstance(error, dict):
            api_code = str(error.get("code") or error.get("type") or api_code)
            message = str(error.get("message") or message)
    except json.JSONDecodeError:
        pass
    label = classify_openai_error(exc.code, api_code, message)
    return OpenAIAPIError(label, exc.code, api_code, compact_text(message, 500), compact_text(body, 1000))


def is_transient_exception(exc: BaseException) -> bool:
    return isinstance(exc, OpenAIAPIError) and exc.status in {502, 503, 504}


def call_openai(
    prompt: str,
    token: str,
    model: str,
    timeout: int,
    with_web: bool,
    reasoning_effort: str,
) -> tuple[dict, str | None, list[dict], dict]:
    payload: dict = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_market_focus_brief",
                "strict": True,
                "schema": MARKET_FOCUS_SCHEMA,
            }
        },
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    if with_web:
        payload["tools"] = [{"type": "web_search"}]
        payload["tool_choice"] = "auto"
        payload["include"] = ["web_search_call.action.sources"]
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    request_timeout = None if timeout <= 0 else timeout
    try:
        with urllib.request.urlopen(request, timeout=request_timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise openai_http_error(exc) from exc
    text = extract_output_text(raw)
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(text), raw.get("id"), extract_web_sources(raw), {
        "usage": raw.get("usage") or {},
        "output_chars": len(text),
    }


def call_openai_with_transient_retry(
    prompt: str,
    token: str,
    model: str,
    timeout: int,
    with_web: bool,
    reasoning_effort: str,
    *,
    retry_delay_seconds: float = 8.0,
) -> tuple[dict, str | None, list[dict], dict]:
    transient_errors: list[str] = []
    for attempt_index in range(2):
        try:
            brief, response_id, web_sources, stats = call_openai(prompt, token, model, timeout, with_web, reasoning_effort)
            stats["attempt_count"] = attempt_index + 1
            stats["transient_retry_count"] = attempt_index
            if transient_errors:
                stats["transient_errors"] = transient_errors
            return brief, response_id, web_sources, stats
        except Exception as exc:  # noqa: BLE001 - retry only known transient gateway errors.
            if attempt_index == 0 and is_transient_exception(exc):
                transient_errors.append(f"{type(exc).__name__}: {exc}")
                time.sleep(retry_delay_seconds)
                continue
            raise
    raise RuntimeError("unreachable_openai_retry_state")


def load_fixture_response(path: Path) -> tuple[dict, str | None, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("brief"), dict):
        return payload["brief"], payload.get("raw_response_id") or payload.get("id"), payload.get("web_sources") or []
    if isinstance(payload, dict) and (payload.get("output_text") or payload.get("output")):
        extracted = extract_output_text(payload)
        if not extracted:
            raise RuntimeError("fixture response did not contain output_text")
        return json.loads(extracted), payload.get("id"), extract_web_sources(payload)
    if isinstance(payload, dict):
        return payload, payload.get("id"), payload.get("web_sources") or []
    raise ValueError("fixture must be a JSON object")


def resolve_model(args_model: str | None, env: dict[str, str]) -> str:
    return args_model or env.get("AUTOPARK_MARKET_FOCUS_MODEL") or env.get("AUTOPARK_OPENAI_MODEL") or DEFAULT_MODEL


def write_raw_response(
    target_date: str,
    model: str,
    response_id: str | None,
    brief: dict,
    source: str,
    web_sources: list[dict],
    output_path: Path | None = None,
) -> Path:
    path = output_path or (RUNTIME_DIR / "openai-responses" / f"{target_date}-market-focus-raw.json")
    write_json(
        path,
        {
            "ok": True,
            "target_date": target_date,
            "received_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": model,
            "source": source,
            "raw_response_id": response_id,
            "web_sources": web_sources,
            "brief": brief,
        },
    )
    return path


def normalized_use(value: object) -> str:
    text = str(value or "").strip()
    return text if text in BROADCAST_USES else "drop"


def normalize_focus_item(item: dict, index: int, known_ids: set[str]) -> tuple[dict, list[dict]]:
    source_ids = unique_strings(item.get("source_ids") or item.get("sources") or [])
    evidence_ids = unique_strings(item.get("evidence_ids") or item.get("source_ids") or [])
    all_ids = unique_strings([*source_ids, *evidence_ids])
    broadcast_use = normalized_use(item.get("broadcast_use"))
    missing_assets = unique_strings(item.get("missing_assets") or [])
    gaps: list[dict] = []
    known_hits = [item_id for item_id in all_ids if item_id in known_ids]

    if broadcast_use in PUBLIC_USES and not all_ids:
        broadcast_use = "drop"
        missing_assets.append("local evidence_id or source_id required before public use")
        gaps.append(
            {
                "issue": compact_text(item.get("focus") or "evidence-less market focus", 140),
                "why_needed": "The model proposed a public story without a local item_id/evidence_id.",
                "search_hint": compact_text(item.get("market_question") or item.get("focus") or "", 180),
                "safe_for_public": False,
                "related_focus_rank": index,
            }
        )
    elif broadcast_use in PUBLIC_USES and all_ids and not known_hits:
        broadcast_use = "drop"
        missing_assets.append("referenced ids were not found in the local source packet")
        gaps.append(
            {
                "issue": compact_text(item.get("focus") or "unknown local evidence ids", 140),
                "why_needed": "The focus references ids that are not in the local packet; keep it out of the public dashboard until sourced.",
                "search_hint": ", ".join(all_ids[:3]),
                "safe_for_public": False,
                "related_focus_rank": index,
            }
        )

    try:
        confidence = float(item.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    focus = compact_text(item.get("focus") or item.get("suggested_story_title") or f"focus-{index}", 180)
    normalized = {
        "rank": int(item.get("rank") or index),
        "focus": focus,
        "market_question": compact_text(item.get("market_question") or focus, 260),
        "why_it_matters": compact_text(item.get("why_it_matters") or "", 420),
        "price_confirmation": compact_text(item.get("price_confirmation") or "", 260),
        "broadcast_use": broadcast_use,
        "confidence": max(0.0, min(1.0, confidence)),
        "suggested_story_title": compact_text(item.get("suggested_story_title") or focus, 140),
        "one_sentence_for_host": compact_text(item.get("one_sentence_for_host") or item.get("why_it_matters") or focus, 260),
        "source_ids": source_ids,
        "evidence_ids": evidence_ids,
        "missing_assets": unique_strings(missing_assets),
    }
    return normalized, gaps


def normalize_false_lead(item: dict) -> dict:
    return {
        "focus": compact_text(item.get("focus") or item.get("title") or "", 180),
        "reason": compact_text(item.get("reason") or "", 260),
        "source_ids": unique_strings(item.get("source_ids") or []),
        "evidence_ids": unique_strings(item.get("evidence_ids") or item.get("source_ids") or []),
        "drop_code": compact_text(item.get("drop_code") or "weak_or_unconfirmed", 80),
    }


def normalize_source_gap(item: dict) -> dict:
    try:
        related_rank = int(item.get("related_focus_rank") or 0)
    except (TypeError, ValueError):
        related_rank = 0
    return {
        "issue": compact_text(item.get("issue") or "", 180),
        "why_needed": compact_text(item.get("why_needed") or "", 260),
        "search_hint": compact_text(item.get("search_hint") or "", 220),
        "safe_for_public": bool(item.get("safe_for_public")) is True,
        "related_focus_rank": max(0, min(12, related_rank)),
    }


def make_order_from_focus(items: list[dict]) -> list[dict]:
    order = []
    for item in items:
        if item.get("broadcast_use") not in PUBLIC_USES:
            continue
        order.append(
            {
                "rank": len(order) + 1,
                "focus_rank": int(item.get("rank") or len(order) + 1),
                "suggested_story_title": item.get("suggested_story_title") or item.get("focus") or "",
                "broadcast_use": item.get("broadcast_use") or "supporting_story",
                "one_sentence_for_host": item.get("one_sentence_for_host") or "",
                "evidence_ids": unique_strings(item.get("evidence_ids") or item.get("source_ids") or []),
            }
        )
    return order[:8]


def normalize_order_item(item: dict, index: int, focus_by_rank: dict[int, dict]) -> dict | None:
    try:
        focus_rank = int(item.get("focus_rank") or item.get("rank") or index)
    except (TypeError, ValueError):
        focus_rank = index
    focus = focus_by_rank.get(focus_rank, {})
    if focus and focus.get("broadcast_use") not in PUBLIC_USES:
        return None
    broadcast_use = normalized_use(item.get("broadcast_use") or focus.get("broadcast_use"))
    if broadcast_use not in PUBLIC_USES:
        return None
    evidence_ids = unique_strings(item.get("evidence_ids") or focus.get("evidence_ids") or focus.get("source_ids") or [])
    if not evidence_ids:
        return None
    return {
        "rank": index,
        "focus_rank": focus_rank,
        "suggested_story_title": compact_text(
            item.get("suggested_story_title") or focus.get("suggested_story_title") or focus.get("focus") or "",
            140,
        ),
        "broadcast_use": broadcast_use,
        "one_sentence_for_host": compact_text(
            item.get("one_sentence_for_host") or focus.get("one_sentence_for_host") or "",
            240,
        ),
        "evidence_ids": evidence_ids,
    }


def resolve_evidence_alias(value: object, input_payload: dict) -> str:
    text = compact_text(value, 240)
    aliases = input_payload.get(LOCAL_ALIAS_KEY) or {}
    return aliases.get(text, text)


def resolve_focus_aliases(item: dict, input_payload: dict) -> dict:
    item["source_ids"] = unique_strings([resolve_evidence_alias(value, input_payload) for value in item.get("source_ids") or []])
    item["evidence_ids"] = unique_strings([resolve_evidence_alias(value, input_payload) for value in item.get("evidence_ids") or []])
    return item


def normalize_brief(brief: dict, input_payload: dict) -> dict:
    known_ids = known_evidence_ids(input_payload)
    focus_items = []
    generated_gaps = []
    for index, item in enumerate(brief.get("what_market_is_watching") or [], start=1):
        if not isinstance(item, dict):
            continue
        normalized, gaps = normalize_focus_item(item, index, known_ids)
        focus_items.append(normalized)
        generated_gaps.extend(gaps)
    focus_items = sorted(focus_items, key=lambda item: int(item.get("rank") or 999))
    for index, item in enumerate(focus_items, start=1):
        item["rank"] = index
        resolve_focus_aliases(item, input_payload)

    focus_by_rank = {int(item.get("rank") or index): item for index, item in enumerate(focus_items, start=1)}
    supplied_order = []
    for index, item in enumerate(brief.get("suggested_broadcast_order") or [], start=1):
        if isinstance(item, dict):
            normalized = normalize_order_item(item, index, focus_by_rank)
            if normalized:
                supplied_order.append(normalized)
    order = supplied_order or make_order_from_focus(focus_items)
    for index, item in enumerate(order, start=1):
        item["rank"] = index
        item["evidence_ids"] = unique_strings([resolve_evidence_alias(value, input_payload) for value in item.get("evidence_ids") or []])

    missing_assets = unique_strings(
        [
            *(brief.get("missing_assets") or []),
            *(asset for focus in focus_items for asset in focus.get("missing_assets") or []),
        ]
    )
    source_gaps = [normalize_source_gap(item) for item in brief.get("source_gaps") or [] if isinstance(item, dict)]
    source_gaps.extend(normalize_source_gap(item) for item in generated_gaps)
    false_leads = [normalize_false_lead(item) for item in brief.get("false_leads") or [] if isinstance(item, dict)]

    return {
        "market_focus_summary": compact_text(brief.get("market_focus_summary"), 80),
        "what_market_is_watching": focus_items,
        "false_leads": false_leads,
        "missing_assets": missing_assets,
        "source_gaps": source_gaps,
        "suggested_broadcast_order": order,
    }


def validate_brief(brief: dict) -> list[str]:
    errors = []
    if not compact_text(brief.get("market_focus_summary")):
        errors.append("missing market_focus_summary")
    focus_items = brief.get("what_market_is_watching")
    if not isinstance(focus_items, list) or not focus_items:
        errors.append("what_market_is_watching must contain at least one item")
        return errors
    for index, item in enumerate(focus_items, start=1):
        for key in [
            "rank",
            "focus",
            "market_question",
            "why_it_matters",
            "price_confirmation",
            "broadcast_use",
            "confidence",
            "suggested_story_title",
            "one_sentence_for_host",
            "missing_assets",
        ]:
            if key not in item:
                errors.append(f"focus {index} missing {key}")
        if item.get("broadcast_use") not in BROADCAST_USES:
            errors.append(f"focus {index} invalid broadcast_use")
        ids = [*(item.get("source_ids") or []), *(item.get("evidence_ids") or [])]
        if item.get("broadcast_use") in PUBLIC_USES and not ids:
            errors.append(f"focus {index} public item missing source_ids/evidence_ids")
    if not isinstance(brief.get("false_leads"), list):
        errors.append("false_leads must be a list")
    if not isinstance(brief.get("missing_assets"), list):
        errors.append("missing_assets must be a list")
    if not isinstance(brief.get("source_gaps"), list):
        errors.append("source_gaps must be a list")
    if not isinstance(brief.get("suggested_broadcast_order"), list) or not brief.get("suggested_broadcast_order"):
        errors.append("suggested_broadcast_order must contain at least one item")
    return errors


def item_lookup(payload: dict) -> dict[str, dict]:
    rows = {}
    for item in payload.get("market_radar", {}).get("candidates") or []:
        for key in ["id", "item_id", "url"]:
            value = item.get(key)
            if value:
                rows[str(value)] = item
    return rows


def chart_confirmation(payload: dict) -> str:
    charts = [chart for chart in payload.get("charts") or [] if chart.get("title")]
    titles = [chart["title"] for chart in charts[:5]]
    return "; ".join(titles) if titles else "Check index futures, rates, dollar, oil, and heatmap captures."


def fallback_brief(
    target_date: str,
    reason: str,
    input_payload: dict,
    raw_response_id: str | None = None,
    raw_response_path: str = "",
    model: str | None = None,
    with_web: bool = False,
    fallback_code: str = "openai_unavailable",
) -> dict:
    radar = input_payload.get("market_radar") or {}
    candidates = item_lookup(input_payload)
    focus_items = []
    false_leads = []
    for index, story in enumerate((radar.get("storylines") or [])[:5], start=1):
        ids = [item_id for item_id in story.get("selected_item_ids") or [] if item_id]
        known = [candidates[item_id] for item_id in ids if item_id in candidates]
        source_ids = ids[:4]
        themes = Counter(theme for item in known for theme in item.get("theme_keys") or [])
        focus = compact_text(story.get("title") or (known[0].get("title") if known else ""), 160)
        market_question = (
            compact_text(known[0].get("radar_question"), 220)
            if known and known[0].get("radar_question")
            else compact_text(story.get("one_liner") or focus, 220)
        )
        stars = int(story.get("recommendation_stars") or 1)
        use = "lead" if index == 1 and source_ids else ("supporting_story" if source_ids and stars >= 2 else "talk_only")
        if not source_ids:
            use = "drop"
        focus_items.append(
            {
                "rank": index,
                "focus": focus or f"Market focus {index}",
                "market_question": market_question,
                "why_it_matters": compact_text(story.get("why_selected") or story.get("angle") or "", 360),
                "price_confirmation": chart_confirmation(input_payload),
                "broadcast_use": use,
                "confidence": max(0.25, min(0.72, 0.3 + stars * 0.14 + len(themes) * 0.04)),
                "suggested_story_title": focus or f"Market focus {index}",
                "one_sentence_for_host": compact_text(story.get("one_liner") or story.get("angle") or focus, 240),
                "source_ids": source_ids,
                "evidence_ids": source_ids,
                "missing_assets": [] if source_ids else ["local evidence_id required"],
            }
        )
        for item in known:
            if str(item.get("evidence_role") or "").lower() == "sentiment" and len(known) == 1:
                false_leads.append(
                    {
                        "focus": item.get("title") or focus,
                        "reason": "Social-only item cannot establish the market cause by itself.",
                        "source_ids": [item.get("id") or ""],
                        "evidence_ids": [item.get("id") or ""],
                        "drop_code": "sentiment_only_not_fact",
                    }
                )

    if not focus_items:
        focus_items.append(
            {
                "rank": 1,
                "focus": "Market reaction check",
                "market_question": "What are index futures, rates, dollar, oil, and sector heatmaps confirming?",
                "why_it_matters": "No strong market-radar storyline was available, so the operator should lead with the market map.",
                "price_confirmation": chart_confirmation(input_payload),
                "broadcast_use": "talk_only",
                "confidence": 0.25,
                "suggested_story_title": "Market reaction check",
                "one_sentence_for_host": "Start with the market map and avoid causal claims until a local source confirms them.",
                "source_ids": ["market-radar"],
                "evidence_ids": ["market-radar"],
                "missing_assets": ["fact/data/analysis lead source"],
            }
        )

    brief = normalize_brief(
        {
            "market_focus_summary": compact_text(
                f"Fallback market-radar focus: {reason}. Use local evidence only.",
                80,
            ),
            "what_market_is_watching": focus_items,
            "false_leads": false_leads,
            "missing_assets": [],
            "source_gaps": [
                {
                    "issue": "OpenAI market focus call unavailable",
                    "why_needed": "A higher-quality editor pass was requested for lead selection.",
                    "search_hint": "rerun build_market_focus_brief.py after API availability returns",
                    "safe_for_public": False,
                    "related_focus_rank": 0,
                }
            ],
            "suggested_broadcast_order": make_order_from_focus(focus_items),
        },
        input_payload,
    )
    return {
        "ok": True,
        "fallback": True,
        "fallback_code": fallback_code,
        "fallback_reason": reason,
        "target_date": target_date,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "model": model,
        "with_web": bool(with_web),
        "raw_response_id": raw_response_id,
        "raw_response_path": raw_response_path,
        **brief,
    }


def markdown_link(label: str, url: str) -> str:
    return f"[{label}]({url})" if str(url).startswith("http") else label


def evidence_label(item_id: str, lookup: dict[str, dict]) -> str:
    row = lookup.get(item_id)
    if not row:
        return f"`{compact_text(item_id, 80)}`"
    title = compact_text(row.get("title") or item_id, 80)
    source = compact_text(row.get("source") or "", 40)
    label = f"{title} / {source}" if source else title
    return markdown_link(label, row.get("url") or "")


def render_markdown(brief: dict, input_payload: dict) -> str:
    lookup = item_lookup(input_payload)
    lines = [
        "# Market Focus Brief",
        "",
        f"- target_date: `{brief.get('target_date') or input_payload.get('date')}`",
        f"- generated_at: `{brief.get('created_at') or datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')}`",
        f"- model: `{brief.get('model') or 'none'}`",
        f"- with_web: `{bool(brief.get('with_web'))}`",
        f"- fallback: `{bool(brief.get('fallback'))}`",
    ]
    if brief.get("fallback"):
        lines.append(f"- fallback_code: `{brief.get('fallback_code') or 'unknown'}`")
        lines.append(f"- fallback_reason: {compact_text(brief.get('fallback_reason') or '', 240)}")
    lines.extend(
        [
            "",
            "## Market Focus Summary",
            "",
            brief.get("market_focus_summary") or "-",
            "",
            "## What Market Is Watching",
            "",
        ]
    )
    for item in brief.get("what_market_is_watching") or []:
        ids = unique_strings([*(item.get("evidence_ids") or []), *(item.get("source_ids") or [])])
        evidence = ", ".join(evidence_label(item_id, lookup) for item_id in ids[:5]) or "-"
        lines.extend(
            [
                f"### {item.get('rank')}. {item.get('suggested_story_title') or item.get('focus')}",
                "",
                f"- broadcast_use: `{item.get('broadcast_use')}` / confidence: `{item.get('confidence')}`",
                f"- focus: {item.get('focus')}",
                f"- market_question: {item.get('market_question')}",
                f"- why_it_matters: {item.get('why_it_matters')}",
                f"- price_confirmation: {item.get('price_confirmation')}",
                f"- host_line: {item.get('one_sentence_for_host')}",
                f"- evidence: {evidence}",
            ]
        )
        if item.get("missing_assets"):
            lines.append("- missing_assets: " + ", ".join(f"`{asset}`" for asset in item["missing_assets"]))
        lines.append("")

    lines.extend(["## Suggested Broadcast Order", ""])
    for item in brief.get("suggested_broadcast_order") or []:
        lines.append(
            f"{item.get('rank')}. `{item.get('broadcast_use')}` {item.get('suggested_story_title')} - {item.get('one_sentence_for_host')}"
        )
    if not brief.get("suggested_broadcast_order"):
        lines.append("- none")

    lines.extend(["", "## False Leads", ""])
    for item in brief.get("false_leads") or []:
        lines.append(f"- `{item.get('drop_code')}` {item.get('focus')}: {item.get('reason')}")
    if not brief.get("false_leads"):
        lines.append("- none")

    lines.extend(["", "## Missing Assets", ""])
    for item in brief.get("missing_assets") or []:
        lines.append(f"- {item}")
    if not brief.get("missing_assets"):
        lines.append("- none")

    lines.extend(["", "## Source Gaps", ""])
    for item in brief.get("source_gaps") or []:
        public = "public-ok" if item.get("safe_for_public") else "hold"
        lines.append(f"- `{public}` {item.get('issue')}: {item.get('why_needed')} / search: {item.get('search_hint')}")
    if not brief.get("source_gaps"):
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=None)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--with-web", action="store_true")
    parser.add_argument("--max-candidates", type=int, default=36)
    parser.add_argument("--max-raw-files", type=int, default=48)
    parser.add_argument("--max-assets", type=int, default=80)
    parser.add_argument("--timeout", type=int, default=DEFAULT_API_TIMEOUT_SECONDS)
    parser.add_argument("--no-api-timeout", action="store_true", help="Disable the urllib read timeout for one-off latency experiments.")
    parser.add_argument("--response-fixture", type=Path, help="Read a saved OpenAI response or brief JSON instead of calling the API.")
    parser.add_argument("--output", type=Path, help="Write JSON to a custom path instead of data/processed/<date>/market-focus-brief.json.")
    parser.add_argument("--markdown-output", type=Path, help="Write Markdown to a custom path instead of runtime/notion/<date>-market-focus.md.")
    parser.add_argument("--prompt-output", type=Path, help="Write the exact prompt payload to a JSON file without secrets.")
    parser.add_argument("--raw-response-output", type=Path, help="Write the raw response wrapper to a custom experiment path.")
    parser.add_argument("--synthetic-smoke", action="store_true", help="Use a tiny synthetic packet for API contract smoke without exporting local collected sources.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    model = resolve_model(args.model, env)
    reasoning_effort = args.reasoning_effort or env.get("AUTOPARK_MARKET_FOCUS_REASONING_EFFORT") or DEFAULT_REASONING_EFFORT
    fixture_meta = load_optional_json(args.response_fixture) if args.response_fixture else {}
    fixture_model = fixture_meta.get("model") if isinstance(fixture_meta, dict) else None
    input_payload = synthetic_smoke_payload(args.date) if args.synthetic_smoke else build_input_payload(args.date, args.max_candidates, args.max_raw_files, args.max_assets)
    output_path = args.output or (PROCESSED_DIR / args.date / "market-focus-brief.json")
    markdown_path = args.markdown_output or (RUNTIME_NOTION_DIR / f"{args.date}-market-focus.md")
    prompt = build_prompt(input_payload, with_web=args.with_web)
    api_timeout = 0 if args.no_api_timeout else args.timeout

    if args.prompt_output:
        write_json(
            args.prompt_output,
            {
                "ok": True,
                "target_date": args.date,
                "model": model,
                "with_web": args.with_web,
                "input_payload": prompt_payload(input_payload),
                "prompt": prompt,
            },
        )

    if args.dry_run:
        print_json(
            {
                "ok": True,
                "status": "dry-run",
                "target_date": args.date,
                "model": model,
                "with_web": args.with_web,
                "output": str(output_path),
                "markdown_output": str(markdown_path),
                "candidate_count": len(input_payload.get("market_radar", {}).get("candidates") or []),
                "raw_source_count": len(input_payload.get("raw_sources") or []),
                "asset_count": len(input_payload.get("available_assets") or []),
                "synthetic_smoke": bool(args.synthetic_smoke),
            }
        )
        return 0

    response_id = None
    raw_response_path = ""
    web_sources: list[dict] = []
    request_stats: dict = {
        "stage": "market_focus_brief",
        "model": model,
        "with_web": bool(args.with_web),
        "timeout_seconds": api_timeout,
        "candidate_count_sent": len(input_payload.get("market_radar", {}).get("candidates") or []),
        "raw_source_count": len(input_payload.get("raw_sources") or []),
        "asset_count": len(input_payload.get("available_assets") or []),
        "prompt_chars": len(prompt),
        "estimated_prompt_tokens": estimate_prompt_tokens(prompt),
    }
    monotonic = time.monotonic()
    try:
        if args.response_fixture:
            brief, response_id, web_sources = load_fixture_response(args.response_fixture)
            response_source = "fixture"
        else:
            token = env.get("OPENAI_API_KEY")
            if not token:
                raise RuntimeError("missing_openai_api_key")
            monotonic = time.monotonic()
            request_stats["request_started_at"] = now_iso()
            brief, response_id, web_sources, response_stats = call_openai_with_transient_retry(
                prompt,
                token,
                model,
                api_timeout,
                with_web=args.with_web,
                reasoning_effort=reasoning_effort,
            )
            request_stats.update(response_stats)
            request_stats["request_finished_at"] = now_iso()
            request_stats["elapsed_seconds"] = round(time.monotonic() - monotonic, 3)
            request_stats["raw_response_id"] = response_id
            response_source = "openai_responses_api_with_web" if args.with_web else "openai_responses_api"
        if args.response_fixture and args.response_fixture.resolve().parent == (RUNTIME_DIR / "openai-responses").resolve():
            raw_response_path = str(args.response_fixture.resolve())
        else:
            raw_response_path = str(write_raw_response(args.date, model, response_id, brief, response_source, web_sources, args.raw_response_output))
        brief = normalize_brief(brief, input_payload)
        errors = validate_brief(brief)
        if errors:
            raise ValueError("; ".join(errors))
        brief = {
            "ok": True,
            "fallback": False,
            "target_date": args.date,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": fixture_model or ("fixture" if args.response_fixture else model),
            "with_web": bool(args.with_web),
            "raw_response_id": response_id,
            "raw_response_path": raw_response_path,
            "web_sources": web_sources,
            "request_stats": request_stats,
            **brief,
        }
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        if request_stats.get("request_started_at") and not request_stats.get("elapsed_seconds"):
            request_stats["request_finished_at"] = now_iso()
            request_stats["elapsed_seconds"] = round(time.monotonic() - monotonic, 3)
        request_stats["error"] = f"{type(exc).__name__}: {exc}"
        fallback_code = exc.label if isinstance(exc, OpenAIAPIError) else "openai_unavailable"
        brief = fallback_brief(
            args.date,
            f"{type(exc).__name__}: {exc}",
            input_payload,
            raw_response_id=response_id,
            raw_response_path=raw_response_path,
            model=model,
            with_web=args.with_web,
            fallback_code=fallback_code,
        )
        brief["request_stats"] = request_stats

    write_json(output_path, brief)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(brief, input_payload), encoding="utf-8")
    print_json(
        {
            "ok": True,
            "fallback": bool(brief.get("fallback")),
            "output": str(output_path),
            "markdown_output": str(markdown_path),
            "model": brief.get("model"),
            "with_web": bool(brief.get("with_web")),
            "synthetic_smoke": bool(args.synthetic_smoke),
            "focus_count": len(brief.get("what_market_is_watching") or []),
            "source_gap_count": len(brief.get("source_gaps") or []),
            "fallback_code": brief.get("fallback_code"),
            "fallback_reason": brief.get("fallback_reason"),
            "request_stats": brief.get("request_stats"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
