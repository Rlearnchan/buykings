#!/usr/bin/env python3
"""Build short evidence-level microcopy for Autopark market-radar candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
REPO_ROOT = PROJECT_DIR.parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_ENV = REPO_ROOT / ".env"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_GROUP_SIZE = 30
DEFAULT_FALLBACK = "deterministic"
MAX_TITLE_CHARS = 24
MAX_CONTENT_CHARS = 300
FORBIDDEN_TOKENS = [
    "source_role",
    "evidence_role",
    "item_id",
    "evidence_id",
    "asset_id",
    "MF-",
    "http://",
    "https://",
]
GENERATED_FIELDS = ["title", "content"]


EVIDENCE_MICROCOPY_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["item_id", "source_label", "title", "content"],
                "properties": {
                    "item_id": {"type": "string"},
                    "source_label": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
        }
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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def clean(value: object, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"https?://\S+", "", text, flags=re.I)
    text = re.sub(r"\bwww\.\S+", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip(" ,.;:-") + "…"
    return text


def strip_forbidden(text: str) -> str:
    result = text
    for token in FORBIDDEN_TOKENS:
        result = re.sub(re.escape(token), "", result, flags=re.I)
    result = re.sub(r"https?://\S+|www\.\S+", "", result, flags=re.I)
    result = re.sub(r"\b[A-Za-z]:\\\S+|/Users/\S+|/home/\S+", "", result)
    result = re.sub(r"<[^>]+>", " ", result)
    return clean(result)


def forbidden_hit(text: str) -> bool:
    lowered = (text or "").lower()
    return any(token.lower() in lowered for token in FORBIDDEN_TOKENS)


def raw_body_like(text: str) -> bool:
    lowered = (text or "").lower()
    return bool(
        "<html" in lowered
        or "<body" in lowered
        or "</p>" in lowered
        or "x-amz-signature" in lowered
        or "sessiontoken" in lowered
        or len(text) > 600
    )


def sanitize_line(value: object, limit: int = MAX_CONTENT_CHARS) -> str:
    text = strip_forbidden(str(value or ""))
    if not text or forbidden_hit(text) or raw_body_like(text):
        return ""
    if len(text) <= limit:
        return text
    clipped = text[:limit].rstrip()
    for mark in ["다.", "요.", ".", "?", "!"]:
        end = clipped.rfind(mark)
        if end >= 30:
            return clipped[: end + len(mark)].strip()
    return clipped[: limit - 1].rstrip(" ,.;:-") + "…"


def item_id_of(item: dict) -> str:
    return str(item.get("item_id") or item.get("id") or item.get("url") or item.get("title") or "").strip()


def source_label_of(item: dict) -> str:
    return clean(item.get("source") or item.get("source_name") or item.get("source_id") or item.get("type") or "Autopark", 80)


def title_of(item: dict) -> str:
    return clean(item.get("title") or item.get("headline") or item.get("summary") or item_id_of(item), 160)


def summary_of(item: dict) -> str:
    return clean(item.get("summary") or item.get("description") or item.get("selection_reason") or item.get("text") or title_of(item), 420)


def theme_keys_of(item: dict) -> list[str]:
    values = item.get("theme_keys") or item.get("market_hooks") or []
    return [clean(value, 40) for value in values if clean(value, 40)][:6]


def compact_item_for_prompt(item: dict) -> dict:
    return {
        "item_id": item_id_of(item),
        "source_label": source_label_of(item),
        "title": title_of(item),
        "summary": summary_of(item),
        "published_at": clean(item.get("published_at") or item.get("captured_at") or "", 40),
        "theme_keys": theme_keys_of(item),
        "radar_question": clean(item.get("radar_question") or "", 160),
        "market_reaction": clean(item.get("market_reaction") or "", 160),
        "korea_open_relevance": clean(item.get("korea_open_relevance") or "", 140),
        "asset_status": "visual_available" if item.get("visual_local_path") or item.get("image_refs") else "metadata_only",
    }


def radar_candidates(radar: dict, limit: int) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for item in radar.get("candidates") or []:
        if not isinstance(item, dict):
            continue
        item_id = item_id_of(item)
        if not item_id or item_id in seen:
            continue
        rows.append(item)
        seen.add(item_id)
        if len(rows) >= limit:
            break
    return rows


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def fallback_content(item: dict) -> str:
    title = title_of(item)
    summary = summary_of(item)
    if summary and summary != title:
        return sanitize_line(summary, MAX_CONTENT_CHARS) or sanitize_line(title, MAX_CONTENT_CHARS)
    return sanitize_line(title, MAX_CONTENT_CHARS) or "자료의 핵심 내용을 정리했습니다."


def deterministic_item(item: dict, reason: str = "deterministic") -> dict:
    return {
        "item_id": item_id_of(item),
        "source_label": sanitize_line(source_label_of(item), 80) or "Autopark",
        "title": sanitize_line(title_of(item), MAX_TITLE_CHARS) or item_id_of(item),
        "content": fallback_content(item),
        "fallback": True,
        "fallback_reason": reason,
    }


def validate_item(output: dict, source_item: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    expected_id = item_id_of(source_item)
    item_id = str(output.get("item_id") or "").strip()
    if item_id != expected_id:
        errors.append("item_id_mismatch")
    source_label = sanitize_line(output.get("source_label") or source_label_of(source_item), 80)
    title = sanitize_line(output.get("title") or title_of(source_item), MAX_TITLE_CHARS)
    content = sanitize_line(
        output.get("content")
        or " ".join(str(value) for value in (output.get("summary_bullets") or [])[:1]),
        MAX_CONTENT_CHARS,
    )
    if not content:
        errors.append("missing_content")
    text_blob = " ".join([source_label, title, content])
    if forbidden_hit(text_blob):
        errors.append("forbidden_token")
    if raw_body_like(text_blob):
        errors.append("raw_body_like")
    return (
        {
            "item_id": expected_id,
            "source_label": source_label or source_label_of(source_item),
            "title": title or title_of(source_item),
            "content": content,
        },
        errors,
    )


def build_prompt(target_date: str, items: list[dict]) -> str:
    packet = {
        "date": target_date,
        "policy": {
            "purpose": "evidence_microcopy_for_korean_morning_market_broadcast",
            "do_not_rank_or_select_items": True,
            "do_not_change_item_id_or_order": True,
            "do_not_invent_prices_dates_or_causality": True,
            "raw_body_and_urls_excluded": True,
        },
        "items": [compact_item_for_prompt(item) for item in items],
    }
    return f"""You write evidence-level Korean microcopy for Autopark.

Task:
- For each item, write a short public title around 20 Korean characters, hard max 24 characters.
- For each item, write exactly one content paragraph, 120-300 characters when source detail allows.
- The content should say what the news/material says, with enough context for a host to understand it quickly.
- Korean should be the base language, but English market terms or quoted phrases are allowed when useful.
- Do not add unsupported interpretation, PPT usage, cautions, or phrases like "자료입니다".

Strict rules:
- Do not change item_id, item order, ranking, selection, storyline, or material labels.
- Do not invent facts, prices, dates, market reactions, or causal links not supported by the item.
- Preserve uncertainty in the source when it is a claim, opinion, or social post.
- Do not output URLs, raw HTML, full article text, credentials, signed URLs, or internal role/hash tokens.
- Return JSON matching the schema only.

Input packet:
{json.dumps(packet, ensure_ascii=False, indent=2)}
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
                "name": "autopark_evidence_microcopy",
                "strict": True,
                "schema": EVIDENCE_MICROCOPY_RESPONSE_SCHEMA,
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


def group_size_from(value: object) -> int:
    try:
        size = int(value or DEFAULT_GROUP_SIZE)
    except (TypeError, ValueError):
        return DEFAULT_GROUP_SIZE
    return max(20, min(40, size))


def build_microcopy(target_date: str, env: dict[str, str], *, limit: int, group_size: int, timeout: int) -> dict:
    radar = load_json(PROCESSED_DIR / target_date / "market-radar.json")
    items = radar_candidates(radar, limit)
    enabled = env.get("AUTOPARK_EVIDENCE_MICROCOPY_ENABLED") == "1"
    model = env.get("AUTOPARK_EVIDENCE_MICROCOPY_MODEL") or DEFAULT_MODEL
    fallback_mode = env.get("AUTOPARK_EVIDENCE_MICROCOPY_FALLBACK") or DEFAULT_FALLBACK
    token = env.get("OPENAI_API_KEY") or ""
    started = time.monotonic()
    result_items: list[dict] = []
    fallback_count = 0
    invalid_output_count = 0
    request_count = 0
    response_ids: list[str] = []
    source = "deterministic_disabled"
    error = ""

    if enabled and token:
        source = "openai_responses_api"
        by_id = {item_id_of(item): item for item in items}
        for group in chunked(items, group_size):
            fallback_by_id = {item_id_of(item): deterministic_item(item, "openai_item_fallback") for item in group}
            try:
                request_count += 1
                response, response_id = call_openai(build_prompt(target_date, group), token, model, timeout)
                if response_id:
                    response_ids.append(response_id)
                outputs = {
                    str(item.get("item_id") or "").strip(): item
                    for item in response.get("items") or []
                    if isinstance(item, dict)
                }
                for source_item in group:
                    item_id = item_id_of(source_item)
                    validated, errors = validate_item(outputs.get(item_id) or {}, source_item)
                    if errors:
                        invalid_output_count += 1
                        fallback_count += 1
                        result_items.append(fallback_by_id[item_id])
                    else:
                        result_items.append(validated)
            except Exception as exc:  # noqa: BLE001 - the required path is deterministic fallback.
                error = f"{type(exc).__name__}: {exc}"
                if fallback_mode != "deterministic":
                    raise
                fallback_count += len(group)
                result_items.extend(fallback_by_id.values())
    else:
        source = "deterministic_missing_api_key" if enabled else "deterministic_disabled"
        if enabled and not token:
            error = "missing_openai_api_key"
        result_items = [deterministic_item(item, source) for item in items]
        fallback_count = len(result_items)

    elapsed = round(time.monotonic() - started, 3)
    estimated_tokens = sum(max(1, len(json.dumps(compact_item_for_prompt(item), ensure_ascii=False)) // 4) for item in items)
    return {
        "ok": True,
        "contract": "evidence_microcopy_v1",
        "date": target_date,
        "enabled": enabled,
        "source": source,
        "model": model,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "request_count": request_count,
        "group_size": group_size,
        "item_count": len(result_items),
        "candidate_count": len(radar.get("candidates") or []),
        "fallback_count": fallback_count,
        "invalid_output_count": invalid_output_count,
        "estimated_tokens": estimated_tokens,
        "generated_fields": GENERATED_FIELDS,
        "response_ids": response_ids,
        "error": error,
        "items": result_items,
        "source_item_ids": [item_id for item_id in by_id] if enabled and token else [item_id_of(item) for item in items],
        "elapsed_seconds": elapsed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--group-size", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    env = {**load_env(args.env.resolve()), **os.environ}
    group_size = group_size_from(args.group_size or env.get("AUTOPARK_EVIDENCE_MICROCOPY_GROUP_SIZE"))
    payload = build_microcopy(args.date, env, limit=args.limit, group_size=group_size, timeout=args.timeout)
    output = args.output or (PROCESSED_DIR / args.date / "evidence-microcopy.json")
    if not args.dry_run:
        write_json(output, payload)
    print_json(
        {
            "ok": payload["ok"],
            "date": payload["date"],
            "enabled": payload["enabled"],
            "source": payload["source"],
            "model": payload["model"],
            "output": str(output),
            "request_count": payload["request_count"],
            "item_count": payload["item_count"],
            "fallback_count": payload["fallback_count"],
            "invalid_output_count": payload["invalid_output_count"],
            "elapsed_seconds": payload["elapsed_seconds"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
