#!/usr/bin/env python3
"""Build compact Korean bullets for Finviz feature-stock cards."""

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

import build_dashboard_microcopy as dashboard_microcopy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"
CONTRACT = "feature_stock_microcopy_v1"
FORBIDDEN_TOKENS = ["source_role", "evidence_role", "item_id", "evidence_id", "asset_id", "MF-", "http://", "https://"]


SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["ticker", "content_bullets"],
                "properties": {
                    "ticker": {"type": "string"},
                    "content_bullets": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string"}},
                },
            },
        }
    },
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip(" ,.;:") + "…"
    return text


def strip_forbidden(text: str) -> str:
    for token in FORBIDDEN_TOKENS:
        text = re.sub(re.escape(token), "", text, flags=re.I)
    text = re.sub(r"\bhttps?://\S+", "", text)
    return clean(text)


def usable_seed(row: dict) -> str:
    parts = [*(row.get("quote_summary") or [])]
    parts.extend(news.get("headline") or "" for news in row.get("news") or [])
    return clean(" ".join(part for part in parts if part), 900)


def deterministic_bullets(row: dict) -> list[str]:
    return []


def build_context(rows: list[dict]) -> dict[str, Any]:
    return {
        "task": "feature_stock_microcopy",
        "items": [
            {
                "ticker": row.get("ticker") or "",
                "finviz_title": row.get("title") or "",
                "finviz_quote_summary": (row.get("quote_summary") or [])[:3],
                "finviz_news": [
                    {"time": news.get("time") or "", "headline": news.get("headline") or ""}
                    for news in (row.get("news") or [])[:5]
                ],
            }
            for row in rows
        ],
    }


def build_prompt(context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You write compact Korean microcopy for an Autopark Notion section called 실적/특징주.",
            "Input items are Finviz ticker pages: quote-page extracted issue lines and recent Finviz headlines.",
            "For each ticker, write 1-3 Korean bullets that say only why this stock is hot today based on Finviz input.",
            "Do not add PPT advice, cautions, generic investment advice, or causes not supported by the input.",
            "Keep key market terms such as non-GAAP EPS, revenue, guidance, AI demand, premarket in English when useful.",
            "If the input is thin, write one bullet. If there is no meaningful Finviz issue line, omit that ticker from items.",
            "Never output URLs or internal IDs. Return strict JSON only.",
            json.dumps(context, ensure_ascii=False),
        ]
    )


def extract_output_text(raw: dict) -> str:
    if isinstance(raw.get("output_text"), str):
        return raw["output_text"]
    for item in raw.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]
    return ""


def call_openai(context: dict[str, Any], *, token: str, model: str, timeout: int) -> tuple[dict, str | None]:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": build_prompt(context)}]}],
        "text": {"format": {"type": "json_schema", "name": "autopark_feature_stock_microcopy", "strict": True, "schema": SCHEMA}},
    }
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    output_text = extract_output_text(raw)
    if not output_text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(output_text), raw.get("id")


def validate_item(ticker: str, bullets: list[Any], fallback: list[str]) -> tuple[list[str], bool]:
    rows: list[str] = []
    invalid = False
    for bullet in bullets[:3]:
        text = strip_forbidden(str(bullet or ""))
        if not text or any(token.lower() in text.lower() for token in FORBIDDEN_TOKENS):
            invalid = True
            continue
        if text not in rows:
            rows.append(text)
    if rows:
        return rows[:3], invalid
    return fallback, True


def build_microcopy(rows: list[dict], env: dict[str, str], timeout: int) -> dict:
    model = env.get("AUTOPARK_FEATURE_STOCK_MICROCOPY_MODEL") or env.get("AUTOPARK_MICROCOPY_MODEL") or DEFAULT_MODEL
    enabled = env.get("AUTOPARK_FEATURE_STOCK_MICROCOPY_ENABLED", env.get("AUTOPARK_MICROCOPY_ENABLED", "0")) == "1"
    fallback_items = {row.get("ticker"): deterministic_bullets(row) for row in rows}
    fallback_payload = {
        "ok": True,
        "contract": CONTRACT,
        "enabled": enabled,
        "source": "deterministic",
        "model": model,
        "item_count": len(rows),
        "fallback_count": sum(1 for value in fallback_items.values() if value),
        "items": [{"ticker": ticker, "content_bullets": bullets} for ticker, bullets in fallback_items.items() if ticker and bullets],
    }
    if not enabled:
        return fallback_payload
    token = env.get("OPENAI_API_KEY")
    if not token:
        return {**fallback_payload, "source": "deterministic_missing_openai_api_key"}
    started = time.monotonic()
    try:
        parsed, response_id = call_openai(build_context(rows), token=token, model=model, timeout=timeout)
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return {**fallback_payload, "source": "deterministic_openai_failed", "fallback_reason": f"{type(exc).__name__}: {clean(exc, 240)}"}
    by_ticker = {clean(item.get("ticker")).upper(): item for item in parsed.get("items") or [] if item.get("ticker")}
    items = []
    fallback_count = 0
    invalid_count = 0
    for row in rows:
        ticker = clean(row.get("ticker")).upper()
        if not ticker:
            continue
        bullets, invalid = validate_item(ticker, by_ticker.get(ticker, {}).get("content_bullets") or [], fallback_items.get(ticker) or [])
        if invalid:
            invalid_count += 1
        if not by_ticker.get(ticker):
            fallback_count += 1
        if bullets:
            items.append({"ticker": ticker, "content_bullets": bullets})
    return {
        "ok": True,
        "contract": CONTRACT,
        "enabled": True,
        "source": "openai_responses_api",
        "model": model,
        "request_count": 1,
        "item_count": len(rows),
        "fallback_count": fallback_count,
        "invalid_output_count": invalid_count,
        "raw_response_ids": [response_id] if response_id else [],
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=REPO_ROOT / ".env")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    payload = load_json(args.input or (PROCESSED_DIR / args.date / "finviz-feature-stocks.json"))
    rows = [row for row in payload.get("items") or [] if row.get("status") == "ok"][: args.limit]
    env = {**dashboard_microcopy.load_env(args.env), **os.environ}
    result = build_microcopy(rows, env, args.timeout)
    result["target_date"] = args.date
    result["generated_at"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    output = args.output or (PROCESSED_DIR / args.date / "feature-stock-microcopy.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "source": result.get("source"), "items": len(result.get("items") or [])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
