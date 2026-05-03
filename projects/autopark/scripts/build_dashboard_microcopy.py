#!/usr/bin/env python3
"""Build short public-facing microcopy for the compact Autopark dashboard.

The renderer owns document structure, ordering, labels, and ranks. This helper
only supplies short copy fields that fit into the fixed publish template.
"""

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
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
RUNTIME_DIR = PROJECT_DIR / "runtime"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_FALLBACK = "deterministic"
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
GENERATED_FIELDS = ["quote_lines", "host_relevance_bullets", "content_bullets"]
MAX_CARDS_PER_REQUEST = 40


MICROCOPY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["storylines", "media_focus_cards"],
    "properties": {
        "storylines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["storyline_id", "quote_lines", "host_relevance_bullets", "slide_line"],
                "properties": {
                    "storyline_id": {"type": "string"},
                    "quote_lines": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string"}},
                    "host_relevance_bullets": {"type": "array", "minItems": 2, "maxItems": 3, "items": {"type": "string"}},
                    "slide_line": {"type": "string"},
                },
            },
        },
        "media_focus_cards": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["card_key", "content_bullets"],
                "properties": {
                    "card_key": {"type": "string"},
                    "content_bullets": {"type": "array", "minItems": 1, "maxItems": 1, "items": {"type": "string"}},
                },
            },
        },
    },
}


def clean(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip(" ,.;:") + "…"
    return text


def strip_markdown(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"!\[[^\]]*]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return clean(text)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def forbidden_hit(text: str) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in FORBIDDEN_TOKENS)


def english_word_run_too_long(text: str) -> bool:
    return len(re.findall(r"\b[A-Za-z][A-Za-z0-9&'’.-]*\b", text or "")) >= 5


def raw_source_like(text: str) -> bool:
    lowered = (text or "").lower()
    enum_like = re.fullmatch(r"[a-z0-9_.:-]{3,40}", lowered.strip() or "") is not None
    return bool(
        english_word_run_too_long(text)
        or enum_like
        or "_" in lowered
        or re.search(r"\b[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/|\b)", lowered)
        or re.search(r"@\w+|breaking:|trump on|says he will|등\s+\d+개\s+출처|same direction|source-count", lowered)
        or re.search(r"\b(?:low|medium|high|unknown|null|true|false|fallback|source_gap|false_lead|missing_assets)\b", lowered)
        or lowered.count("/") >= 2
    )


def content_raw_source_like(text: str) -> bool:
    lowered = (text or "").lower()
    enum_like = re.fullmatch(r"[a-z0-9_.:-]{3,40}", lowered.strip() or "") is not None
    return bool(
        enum_like
        or "_" in lowered
        or re.search(r"\b[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/|\b)", lowered)
        or re.search(r"@\w+|source-count|source_gap|false_lead|missing_assets", lowered)
        or lowered.count("/") >= 2
    )


def sanitize_line(value: Any, limit: int = 90) -> str:
    text = strip_markdown(value)
    for token in FORBIDDEN_TOKENS:
        text = re.sub(re.escape(token), "", text, flags=re.I)
    text = re.sub(r"\b[A-Za-z]:\\\S+|/Users/\S+|/home/\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -:/")
    if not text or raw_source_like(text):
        return ""
    if len(text) <= limit:
        return text
    clipped = text[:limit].rstrip()
    end = max(clipped.rfind(mark) for mark in [".", "?", "!", "다.", "요.", "함.", "음."])
    if end >= max(32, limit // 2):
        return clipped[: end + 1].rstrip()
    return clipped[: limit - 1].rstrip(" ,.;:") + "…"


def sanitize_content_line(value: Any, limit: int = 300) -> str:
    text = strip_markdown(value)
    for token in FORBIDDEN_TOKENS:
        text = re.sub(re.escape(token), "", text, flags=re.I)
    text = re.sub(r"\b[A-Za-z]:\\\S+|/Users/\S+|/home/\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -:/")
    if not text or content_raw_source_like(text):
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,.;:") + "…"


def sentence_parts(value: Any) -> list[str]:
    raw = strip_markdown(value)
    if not raw:
        return []
    parts = [clean(part) for part in re.split(r"(?<=[.!?。])\s+|\n+|[;；]\s*", raw) if clean(part)]
    return parts or [raw]


def pick_lines(seeds: list[Any], *, limit: int, minimum: int, maximum: int, fallbacks: list[str]) -> list[str]:
    rows: list[str] = []
    for seed in [*seeds, *fallbacks]:
        for part in sentence_parts(seed):
            line = sanitize_line(part, limit)
            if line and not forbidden_hit(line) and not raw_source_like(line) and line not in rows:
                rows.append(line)
            if len(rows) >= maximum:
                return rows
    return rows[:maximum] if len(rows) >= minimum else fallbacks[:minimum]


def candidate_lines(seeds: list[Any], *, limit: int, maximum: int = 8) -> list[str]:
    rows: list[str] = []
    for seed in seeds:
        for part in sentence_parts(seed):
            line = sanitize_line(part, limit)
            if line and not forbidden_hit(line) and not raw_source_like(line) and line not in rows:
                rows.append(line)
            if len(rows) >= maximum:
                return rows
    return rows


def contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word.lower() in lowered for word in words)


def host_relevance_lines(candidates: list[str], fallbacks: list[str]) -> list[str]:
    requirements = [
        (["전날", "전일", "시장", "주목", "반영", "가격", "화제"], fallbacks[0]),
        (["첫 5분", "첫 꼭지", "방송", "진행자", "보여주", "다룰"], fallbacks[1]),
        (["한국", "개인투자자", "PPT", "환율", "업종"], fallbacks[2]),
    ]
    rows: list[str] = []
    used: set[str] = set()
    for needles, fallback in requirements:
        picked = next((line for line in candidates if line not in used and contains_any(line, needles)), "")
        line = picked or fallback
        if line not in rows:
            rows.append(line)
            used.add(line)
    for line in fallbacks:
        if len(rows) >= 3:
            break
        if line not in rows:
            rows.append(line)
    return rows[:3]


def host_relevance_complete(lines: list[str]) -> bool:
    blob = " ".join(lines)
    requirements = [
        ["전날", "전일", "시장", "주목", "반영", "가격", "화제"],
        ["첫 5분", "첫 꼭지", "방송", "진행자", "보여주", "다룰"],
        ["한국", "개인투자자", "PPT", "환율", "업종", "성장주"],
    ]
    return all(contains_any(blob, needles) for needles in requirements)


def axis_fallbacks(axis: str) -> dict[str, list[str]]:
    rows = {
        "rates": {
            "quote": [
                "금리와 달러가 위험자산 반등의 속도를 다시 제한하는지 확인한다.",
                "지수보다 채권·환율 반응을 먼저 봐야 하는 아침이다.",
            ],
            "why": [
                "전날 시장은 Fed 발언 이후 금리와 달러 부담을 다시 가격에 반영했다.",
                "첫 5분에는 지수보다 10년물·달러 흐름을 먼저 보여주는 편이 빠르다.",
                "한국장에서는 환율과 성장주 밸류에이션 부담으로 바로 연결된다.",
            ],
        },
        "oil": {
            "quote": [
                "유가 뉴스는 컸지만 WTI·브렌트 가격 반응은 따로 봐야 한다.",
                "헤드라인보다 실제 가격과 에너지주 반응이 오늘의 출발점이다.",
            ],
            "why": [
                "전날 시장은 지정학 헤드라인을 유가와 에너지주가 얼마나 반영했는지 봤다.",
                "첫 5분에는 뉴스 강도와 가격 반응의 차이를 보여주면 이해가 빠르다.",
                "한국장에서는 정유·화학·항공과 물가 부담 장표로 곧장 이어진다.",
            ],
        },
        "ai": {
            "quote": [
                "AI 인프라 기대가 실적과 주가 반응으로 이어지는지 확인한다.",
                "기술주 보조 소재로 쓰되 가격 반응이 붙는지만 본다.",
            ],
            "why": [
                "전날 시장은 AI 투자 뉴스가 기술주 반등의 보조 동력이 되는지 주목했다.",
                "첫 5분에는 실적 기대와 실제 주가 반응을 짧게 분리해 보여줄 수 있다.",
                "한국장에서는 반도체·전력·장비주 PPT 연결점이 생긴다.",
            ],
        },
        "earnings": {
            "quote": [
                "실적 호재가 지수 전체보다 어느 섹터에 붙는지 확인한다.",
                "가이던스와 가격 반응이 같은 방향인지 먼저 본다.",
            ],
            "why": [
                "전날 시장은 실적 숫자보다 가이던스와 주가 반응의 조합을 봤다.",
                "첫 5분에는 승자와 낙오 종목을 나누면 장세 성격이 빨리 잡힌다.",
                "한국장에서는 관련 업종과 특징주 후보를 PPT로 묶기 쉽다.",
            ],
        },
    }
    return rows.get(
        axis,
        {
            "quote": ["가격 반응과 로컬 근거가 같은 방향인지 확인한다."],
            "why": [
                "전날 시장에서 주목받은 재료가 실제 가격 반응으로 이어졌는지 확인한다.",
                "첫 5분에는 핵심 변수와 반응을 나누면 방송 흐름이 빨리 잡힌다.",
                "한국장과 개인투자자 관점에서는 업종·환율·PPT 자료 연결이 중요하다.",
            ],
        },
    )


def deterministic_storyline(story: dict[str, Any]) -> dict[str, Any]:
    axis = clean(story.get("axis") or "market")
    fallbacks = axis_fallbacks(axis)
    quote_lines = pick_lines(
        [
            story.get("quote_seed"),
            story.get("one_sentence_for_host"),
            story.get("price_confirmation"),
            story.get("why_now"),
        ],
        limit=90,
        minimum=1,
        maximum=3,
        fallbacks=fallbacks["quote"],
    )
    why_candidates = candidate_lines(
        [
            story.get("why_it_matters"),
            story.get("market_attention"),
            story.get("lead_candidate_reason"),
            story.get("first_5min_fit"),
            story.get("korea_open_relevance"),
            story.get("market_causality"),
            story.get("price_confirmation"),
        ],
        limit=90,
    )
    why_lines = host_relevance_lines(why_candidates, fallbacks["why"])
    return {
        "storyline_id": clean(story.get("storyline_id")),
        "quote_lines": quote_lines[:3],
        "host_relevance_bullets": why_lines[:3],
        "slide_line": clean(story.get("slide_line")),
    }


def card_axis(card: dict[str, Any]) -> str:
    blob = " ".join(
        clean(card.get(key))
        for key in ["axis", "label", "title", "headline", "summary", "content", "source", "source_label", "url"]
    ).lower()
    if any(token in blob for token in ["oil", "wti", "brent", "energy", "xle", "cvx", "xom", "유가", "브렌트", "에너지"]):
        return "oil"
    if any(token in blob for token in ["fed", "rate", "inflation", "treasury", "dollar", "금리", "달러", "인플레이션"]):
        return "rates"
    if any(token in blob for token in ["ai", "cloud", "semiconductor", "googl", "msft", "meta", "반도체", "기술주"]):
        return "ai"
    if any(token in blob for token in ["earnings", "eps", "실적", "가이던스"]):
        return "earnings"
    return "market"


def card_fallbacks(card: dict[str, Any]) -> list[str]:
    label = sanitize_line(card.get("label") or card.get("title"), 50)
    axis = card_axis(card)
    rows = {
        "rates": [
            "연준·금리 경로가 지수 반등을 어디까지 제한하는지 보는 자료다.",
            "채권·환율 반응을 한국장 성장주 부담과 연결해 볼 수 있다.",
        ],
        "oil": [
            "유가 헤드라인이 실제 가격과 에너지주 반응으로 이어지는지 보는 자료다.",
            "정유·화학·항공 등 한국장 민감 업종의 PPT 연결점이 된다.",
        ],
        "ai": [
            "기술주 반응을 AI·실적 기대와 분리해 확인하는 보조 자료다.",
            "반도체·전력·플랫폼주 연결 장표로 붙일 수 있다.",
        ],
        "earnings": [
            "실적 숫자와 주가 반응이 같은 방향인지 확인하는 자료다.",
            "한국장 관련 업종과 특징주 후보를 고르는 보조 근거다.",
        ],
        "market": [
            "전날 시장 반응을 방송 흐름과 PPT 순서에 연결하는 자료다.",
            "개인투자자가 볼 가격·업종 포인트를 짧게 확인할 수 있다.",
        ],
    }.get(axis, [])
    if label:
        rows.insert(0, f"{label}의 시장 반응과 방송 연결 포인트를 확인한다.")
    return rows or ["자료의 가격 반응과 방송 연결 포인트를 확인한다."]


def deterministic_card(card: dict[str, Any]) -> dict[str, Any]:
    seeds = [
        card.get("micro_content"),
        card.get("summary"),
        card.get("content"),
        card.get("source_gap"),
        card.get("headline"),
        card.get("title"),
        card.get("label"),
    ]
    fallbacks = card_fallbacks(card)
    bullets: list[str] = []
    for seed in [*seeds, *fallbacks]:
        line = sanitize_content_line(seed, 300)
        if line:
            bullets.append(line)
            break
    if not bullets:
        bullets = [fallbacks[0]]
    return {"card_key": clean(card.get("card_key")), "content_bullets": bullets[:1]}


def deterministic_microcopy(context: dict[str, Any], *, model: str | None = None, reason: str = "deterministic") -> dict[str, Any]:
    storylines = [deterministic_storyline(story) for story in context.get("storylines") or [] if isinstance(story, dict)]
    cards = [deterministic_card(card) for card in context.get("media_focus_cards") or [] if isinstance(card, dict)]
    return {
        "ok": True,
        "source": reason,
        "microcopy_enabled": False,
        "model": model or "",
        "request_count": 0,
        "card_count": len(cards),
        "fallback_count": len(storylines) + len(cards),
        "invalid_output_count": 0,
        "estimated_tokens": estimate_tokens(json.dumps(context, ensure_ascii=False)),
        "generated_fields": GENERATED_FIELDS,
        "storylines": storylines,
        "media_focus_cards": cards,
    }


def expected_storyline_by_id(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(story.get("storyline_id")): story for story in context.get("storylines") or [] if isinstance(story, dict)}


def expected_card_by_key(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(card.get("card_key")): card for card in context.get("media_focus_cards") or [] if isinstance(card, dict)}


def valid_lines(value: Any, *, minimum: int, maximum: int, limit: int) -> list[str] | None:
    if not isinstance(value, list) or len(value) < minimum or len(value) > maximum:
        return None
    rows = [sanitize_line(item, limit) for item in value]
    if any(not row or forbidden_hit(row) or raw_source_like(row) or len(row) > limit for row in rows):
        return None
    return rows


def validate_storyline(item: dict[str, Any], expected: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    story_id = clean(item.get("storyline_id"))
    if story_id not in expected:
        return None
    quote_lines = valid_lines(item.get("quote_lines"), minimum=1, maximum=3, limit=90)
    why_lines = valid_lines(item.get("host_relevance_bullets"), minimum=2, maximum=3, limit=90)
    slide_line = clean(item.get("slide_line"))
    if quote_lines is None or why_lines is None:
        return None
    if not host_relevance_complete(why_lines):
        return None
    if slide_line != clean(expected[story_id].get("slide_line")) or forbidden_hit(slide_line):
        return None
    return {
        "storyline_id": story_id,
        "quote_lines": quote_lines,
        "host_relevance_bullets": why_lines,
        "slide_line": slide_line,
    }


def validate_card(item: dict[str, Any], expected: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    card_key = clean(item.get("card_key"))
    if card_key not in expected:
        return None
    raw_bullets = item.get("content_bullets")
    if not isinstance(raw_bullets, list) or len(raw_bullets) != 1:
        return None
    bullets = [sanitize_content_line(raw_bullets[0], 300)]
    if not bullets[0] or forbidden_hit(bullets[0]) or len(bullets[0]) > 300:
        return None
    return {"card_key": card_key, "content_bullets": bullets}


def validate_microcopy(candidate: dict[str, Any], context: dict[str, Any], fallback: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    expected_stories = expected_storyline_by_id(context)
    expected_cards = expected_card_by_key(context)
    fallback_stories = {item["storyline_id"]: item for item in fallback.get("storylines") or []}
    fallback_cards = {item["card_key"]: item for item in fallback.get("media_focus_cards") or []}
    story_rows = {}
    card_rows = {}
    invalid = 0

    for item in candidate.get("storylines") or []:
        if not isinstance(item, dict):
            invalid += 1
            continue
        valid = validate_storyline(item, expected_stories)
        if valid:
            story_rows[valid["storyline_id"]] = valid
        else:
            invalid += 1

    for item in candidate.get("media_focus_cards") or []:
        if not isinstance(item, dict):
            invalid += 1
            continue
        valid = validate_card(item, expected_cards)
        if valid:
            card_rows[valid["card_key"]] = valid
        else:
            invalid += 1

    stories = []
    cards = []
    fallback_count = 0
    for story_id in expected_stories:
        if story_id in story_rows:
            stories.append(story_rows[story_id])
        else:
            stories.append(fallback_stories[story_id])
            fallback_count += 1
    for card_key in expected_cards:
        if card_key in card_rows:
            cards.append(card_rows[card_key])
        else:
            cards.append(fallback_cards[card_key])
            fallback_count += 1
    merged = {**fallback, "storylines": stories, "media_focus_cards": cards}
    return merged, fallback_count, invalid


def extract_output_text(raw: dict[str, Any]) -> str:
    if isinstance(raw.get("output_text"), str):
        return raw["output_text"]
    parts: list[str] = []
    for item in raw.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                parts.append(str(content.get("text") or ""))
    return "\n".join(part for part in parts if part)


def build_prompt(context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You write compact Korean public-facing microcopy for a morning market dashboard.",
            "Do not change structure, order, labels, ranks, card_key, or slide_line.",
            "Only rewrite quote_lines, host_relevance_bullets, and content_bullets.",
            "Constraints:",
            "- Korean, concise, presenter-friendly.",
            "- quote_lines: 1-3 lines, each <=90 Korean characters.",
            "- host_relevance_bullets: 2-3 bullets, each <=90 Korean characters.",
            "- content_bullets: exactly 1 bullet, 120-300 characters when source detail allows.",
            "- For media focus content, state what the material says with useful context; Korean base is preferred, but English market terms or short quoted phrases are allowed.",
            "- Never include URLs, source_role, evidence_role, item_id, evidence_id, asset_id, or MF hashes.",
            "- Storyline relevance must explain yesterday's market attention, why it fits the first 5 minutes, and the Korea/PPT/personal-investor connection.",
            "Return strict JSON only.",
            json.dumps(context, ensure_ascii=False),
        ]
    )


def call_openai(context: dict[str, Any], *, token: str, model: str, timeout: int) -> tuple[dict[str, Any], str | None]:
    prompt = build_prompt(context)
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_dashboard_microcopy",
                "strict": True,
                "schema": MICROCOPY_SCHEMA,
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
    output_text = extract_output_text(raw)
    if not output_text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(output_text), raw.get("id")


def context_chunks(context: dict[str, Any], max_cards: int = MAX_CARDS_PER_REQUEST) -> list[dict[str, Any]]:
    cards = [card for card in context.get("media_focus_cards") or [] if isinstance(card, dict)]
    stories = [story for story in context.get("storylines") or [] if isinstance(story, dict)]
    if not cards:
        return [{**context, "storylines": stories, "media_focus_cards": []}]
    chunks = []
    for index in range(0, len(cards), max_cards):
        chunks.append(
            {
                **context,
                "storylines": stories if index == 0 else [],
                "media_focus_cards": cards[index : index + max_cards],
            }
        )
    return chunks


def build_microcopy(context: dict[str, Any], *, env: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    env = env or os.environ
    model = env.get("AUTOPARK_MICROCOPY_MODEL") or DEFAULT_MODEL
    fallback_mode = env.get("AUTOPARK_MICROCOPY_FALLBACK") or DEFAULT_FALLBACK
    fallback = deterministic_microcopy(context, model=model, reason=fallback_mode)
    enabled = env.get("AUTOPARK_MICROCOPY_ENABLED") == "1"
    if not enabled:
        return fallback
    token = env.get("OPENAI_API_KEY")
    if not token:
        return {**fallback, "microcopy_enabled": True, "source": "deterministic_missing_openai_api_key", "model": model}

    request_count = 0
    invalid_total = 0
    response_ids: list[str] = []
    candidate = {"storylines": [], "media_focus_cards": []}
    started = time.monotonic()
    try:
        for chunk in context_chunks(context):
            request_count += 1
            parsed, response_id = call_openai(chunk, token=token, model=model, timeout=timeout)
            if response_id:
                response_ids.append(response_id)
            candidate["storylines"].extend(parsed.get("storylines") or [])
            candidate["media_focus_cards"].extend(parsed.get("media_focus_cards") or [])
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return {
            **fallback,
            "microcopy_enabled": True,
            "source": "deterministic_openai_failed",
            "model": model,
            "request_count": request_count,
            "fallback_reason": f"{type(exc).__name__}: {clean(exc, 240)}",
        }

    merged, fallback_count, invalid_total = validate_microcopy(candidate, context, fallback)
    elapsed = round(time.monotonic() - started, 3)
    return {
        **merged,
        "microcopy_enabled": True,
        "source": "openai_responses_api",
        "model": model,
        "request_count": request_count,
        "card_count": len(context.get("media_focus_cards") or []),
        "fallback_count": fallback_count,
        "invalid_output_count": invalid_total,
        "estimated_tokens": estimate_tokens(build_prompt(context)),
        "generated_fields": GENERATED_FIELDS,
        "raw_response_ids": response_ids,
        "elapsed_seconds": elapsed,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--input", type=Path, help="Renderer-built microcopy context JSON.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    if not args.input:
        raise SystemExit("--input is required; renderer owns context/order construction.")
    context = json.loads(args.input.read_text(encoding="utf-8"))
    payload = build_microcopy(context, timeout=args.timeout)
    payload["generated_at"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    output = args.output or (PROCESSED_DIR / args.date / "dashboard-microcopy.json")
    write_json(output, payload)
    print(json.dumps({"ok": True, "output": str(output), "source": payload.get("source")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
