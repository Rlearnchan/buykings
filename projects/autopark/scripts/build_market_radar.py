#!/usr/bin/env python3
"""Build a market-radar ledger focused on what the market is watching now."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from editorial_policy import enrich_candidate_row, enrich_storyline
from source_policy import infer_source_policy, policy_score_bonus
from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials, load_json, x_items

PROJECT_ROOT = PROCESSED_DIR.parents[1]
REPO_ROOT = PROCESSED_DIR.parents[3]
MONTH_LOOKUP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

CORE_SOURCE_WEIGHTS = {
    "kobeissi": 9,
    "wall st engine": 9,
    "wallstengine": 9,
    "isabelnet": 9,
    "stockmarket.news": 7,
    "investinq": 7,
    "bespoke": 7,
    "charlie bilello": 7,
    "liz ann": 6,
    "kevin gordon": 6,
    "reuters": 6,
    "bloomberg": 6,
    "cnbc": 6,
    "financial times": 6,
    "factset": 5,
    "tradingview": 5,
    "yahoo": 5,
}

THEMES = {
    "ai_infra": ["ai", "openai", "anthropic", "google", "data center", "compute", "chip", "semiconductor", "data storage", "storage demand", "power demand"],
    "market_positioning": ["call option", "retail", "hedge fund", "positioning", "bubble", "valuation", "market cap to gdp", "stock market cap to gdp", "risk appetite"],
    "rates_macro": ["fed", "fomc", "rate", "yield", "treasury", "inflation", "pce", "jobs", "dollar", "dxy"],
    "energy_geopolitics": ["oil", "wti", "brent", "iran", "hormuz", "opec", "uae", "gasoline", "fertilizer"],
    "earnings_signal": ["earnings", "guidance", "forecast", "outlook", "revenue", "eps", "margin", "free cash flow", "fcf"],
    "side_dish": ["musk", "altman", "trump", "charles", "white house", "state visit", "trial", "lawsuit"],
}

THEME_LABELS = {
    "ai_infra": "AI/인프라",
    "market_positioning": "시장 포지셔닝/밸류에이션",
    "rates_macro": "금리/매크로",
    "energy_geopolitics": "에너지/지정학",
    "earnings_signal": "실적 신호",
    "side_dish": "단신/환기",
}


def clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def material_blob(material: dict) -> str:
    return " ".join(
        clean(str(material.get(key) or ""))
        for key in ["id", "title", "headline", "summary", "source", "url", "type", "image_alt"]
    ).lower()


def contains(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower())
    if re.search(r"\W", keyword):
        return keyword.lower() in text
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def source_weight(material: dict) -> int:
    source = clean(material.get("source") or material.get("source_name") or material.get("source_id") or "").lower()
    url = clean(material.get("url") or "").lower()
    blob = f"{source} {url}"
    base = max([weight for key, weight in CORE_SOURCE_WEIGHTS.items() if key in blob] or [3])
    return base + policy_score_bonus(material)


def source_blob(material: dict) -> str:
    return f"{material.get('source') or material.get('source_name') or material.get('source_id') or ''} {material.get('url') or ''}".lower()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(value[:10])
    except ValueError:
        return None


def infer_material_date(material: dict, target_day: datetime) -> datetime | None:
    if parsed := parse_dt(material.get("published_at") or material.get("created_at")):
        return parsed
    text = clean(
        " ".join(
            str(material.get(key) or "")
            for key in ["title", "headline", "summary"]
        )
    )
    lowered = text.lower()
    if "today" in lowered:
        return target_day
    if "yesterday" in lowered:
        return target_day - timedelta(days=1)
    if match := re.search(r"\b(\d{1,2})\s+hours?\s+ago\b", lowered):
        return target_day - timedelta(hours=int(match.group(1)))
    if match := re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})\b", lowered):
        month = MONTH_LOOKUP[match.group(1)]
        day = int(match.group(2))
        inferred = datetime(target_day.year, month, day)
        if inferred.date() > target_day.date():
            inferred = datetime(target_day.year - 1, month, day)
        return inferred
    return None


def recency_adjustment(material: dict, target_day: datetime) -> tuple[int, int | None, str]:
    published = infer_material_date(material, target_day)
    if not published:
        return 0, None, "unknown"
    age_days = max(0, (target_day.date() - published.date()).days)
    if age_days <= 1:
        return 0, age_days, "fresh"
    if age_days <= 3:
        return 1, age_days, "recent"
    if age_days <= 7:
        return 3, age_days, "old"
    return 6, age_days, "stale"


def detect_themes(material: dict) -> dict[str, list[str]]:
    blob = material_blob(material)
    hits = {}
    for theme, keywords in THEMES.items():
        matched = [keyword for keyword in keywords if contains(blob, keyword)]
        if matched:
            hits[theme] = matched[:5]
    return hits


def visual_path(material: dict) -> str:
    path = material.get("visual_local_path") or ""
    if path:
        return path
    refs = material.get("image_refs") or []
    if refs and isinstance(refs[0], dict):
        return refs[0].get("local_path") or ""
    return ""


def load_extra_x_posts(date: str, limit: int) -> list[dict]:
    processed = PROCESSED_DIR / date
    rows = []
    seen = set()
    for path in sorted(processed.glob("*posts.json")):
        payload = load_json(path)
        for row in x_items(payload, limit):
            key = row.get("url") or row.get("title")
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def load_headline_river_items(date: str, limit: int = 300) -> list[dict]:
    payload = load_json(PROCESSED_DIR / date / "headline-river.json")
    rows = []
    for item in (payload.get("items") or [])[:limit]:
        if not isinstance(item, dict):
            continue
        title = clean(item.get("title") or item.get("headline") or "", 180)
        if not title:
            continue
        rows.append(
            {
                "id": item.get("item_id") or item.get("url") or title,
                "item_id": item.get("item_id") or item.get("url") or title,
                "title": title,
                "headline": title,
                "summary": clean(item.get("snippet") or title, 420),
                "source": item.get("publisher") or item.get("source_label") or item.get("source_id") or "Headline River",
                "source_name": item.get("source_label") or item.get("source_id") or "",
                "source_id": item.get("source_id") or "",
                "url": item.get("url") or "",
                "type": "headline_river",
                "published_at": item.get("published_at") or item.get("captured_at") or "",
                "captured_at": item.get("captured_at") or "",
                "source_role": item.get("source_role") or "",
                "source_authority": item.get("source_authority") or "",
                "source_use_role": item.get("source_role") or "",
                "collection_method": item.get("collection_method") or "",
                "content_level": item.get("content_level") or "headline",
                "agenda_links": item.get("agenda_links") or [],
                "detected_keywords": item.get("detected_keywords") or [],
            }
        )
    return rows


def load_analysis_river_items(date: str, limit: int = 160) -> list[dict]:
    payload = load_json(PROCESSED_DIR / date / "analysis-river.json")
    rows = []
    for item in (payload.get("items") or [])[:limit]:
        if not isinstance(item, dict):
            continue
        title = clean(item.get("title") or item.get("headline") or "", 180)
        if not title:
            continue
        rows.append(
            {
                "id": item.get("item_id") or item.get("url") or title,
                "item_id": item.get("item_id") or item.get("url") or title,
                "title": title,
                "headline": title,
                "summary": clean(item.get("summary") or title, 420),
                "source": item.get("source_label") or item.get("source_id") or "Analysis River",
                "source_name": item.get("source_label") or item.get("source_id") or "",
                "source_id": item.get("source_id") or "",
                "url": item.get("url") or "",
                "type": "analysis_river",
                "published_at": item.get("published_at") or item.get("captured_at") or "",
                "captured_at": item.get("captured_at") or "",
                "source_role": item.get("source_role") or "",
                "source_authority": item.get("source_authority") or "",
                "source_use_role": item.get("source_role") or "",
                "collection_method": item.get("collection_method") or "",
                "content_level": item.get("content_level") or "",
                "detected_keywords": item.get("detected_keywords") or [],
                "image_refs": item.get("image_refs") or [],
            }
        )
    return rows


def build_rows(date: str, limit_news: int, limit_x: int, limit_visuals: int) -> list[dict]:
    target_day = datetime.fromisoformat(date)
    materials = gather_materials(date, limit_news, limit_x, limit_visuals)
    materials.extend(load_extra_x_posts(date, limit_x))
    materials.extend(load_headline_river_items(date))
    materials.extend(load_analysis_river_items(date))
    rows = []
    seen = set()
    for material in materials:
        key = material.get("url") or material.get("id") or material.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        themes = detect_themes(material)
        weight = source_weight(material)
        recency_penalty, recency_days, recency_bucket = recency_adjustment(material, target_day)
        if "tradingview" in source_blob(material) and recency_days is not None and recency_days > 3:
            continue
        visual_bonus = 2 if visual_path(material) else 0
        theme_bonus = min(10, sum(len(values) for values in themes.values()))
        x_bonus = 2 if material.get("type") in {"x_social", "visual_card"} else 0
        headline_bonus = 2 if material.get("type") == "headline_river" else 0
        analysis_bonus = 3 if material.get("type") == "analysis_river" else 0
        agenda_bonus = min(4, len(material.get("agenda_links") or []) * 2)
        keyword_bonus = min(3, len(material.get("detected_keywords") or []) // 2)
        bridge_bonus = 2 if len(themes) >= 2 else 0
        side_penalty = 3 if set(themes) == {"side_dish"} else 0
        score = weight + visual_bonus + theme_bonus + x_bonus + headline_bonus + analysis_bonus + agenda_bonus + keyword_bonus + bridge_bonus - side_penalty - recency_penalty
        if score < 7 and recency_bucket in {"old", "stale"}:
            continue
        if score < 7 and not themes:
            continue
        title = material.get("title") or material.get("headline") or material.get("summary") or key
        row = {
            "id": material.get("id") or key,
            "title": clean(title, 140),
            "source": material.get("source") or material.get("source_name") or material.get("source_id") or material.get("type") or "",
            "url": material.get("url") or "",
            "type": material.get("type") or "candidate",
            "published_at": material.get("published_at") or "",
            "summary": clean(material.get("summary") or title, 420),
            "score": score,
            "source_weight": weight,
            "source_policy": infer_source_policy(material),
            "recency_days": recency_days,
            "recency_bucket": recency_bucket,
            "recency_penalty": recency_penalty,
            "themes": [
                {"theme": theme, "label": THEME_LABELS.get(theme, theme), "hits": hits}
                for theme, hits in sorted(themes.items())
            ],
            "theme_keys": sorted(themes),
            "visual_local_path": visual_path(material),
            "tickers": material.get("tickers") or [],
            "agenda_links": material.get("agenda_links") or [],
            "detected_keywords": material.get("detected_keywords") or [],
            "content_level": material.get("content_level") or "",
            "radar_question": radar_question(themes),
            "suggested_slot": suggested_slot(themes),
        }
        row.update(enrich_candidate_row(material, row, themes))
        rows.append(row)
    return sorted(rows, key=lambda row: (-row["score"], row["title"]))


def static_chart_rows(date: str) -> list[dict]:
    specs = [
        {
            "id": "fallback-us10y",
            "title": "US 10Y yield chart sets the rates frame for Monday prep",
            "summary": "Use the 10-year Treasury chart as the first check on whether risk assets are trading against rates or with rates.",
            "source": "Yahoo Finance",
            "url": "https://finance.yahoo.com/quote/%5ETNX",
            "visual": "us10y.png",
            "themes": {"rates_macro": ["treasury", "yield", "rate"]},
            "score": 18,
        },
        {
            "id": "fallback-oil",
            "title": "WTI and Brent charts show whether energy risk is moving markets",
            "summary": "Use crude oil charts to separate a broad risk move from a specific inflation or geopolitical impulse.",
            "source": "Yahoo Finance",
            "url": "https://finance.yahoo.com/quote/CL%3DF",
            "visual": "crude-oil-wti.png",
            "themes": {"energy_geopolitics": ["oil", "wti", "brent"]},
            "score": 17,
        },
        {
            "id": "fallback-dollar",
            "title": "DXY and USD/KRW charts anchor the dollar and Korea-open angle",
            "summary": "Use dollar-index and won-dollar moves to judge whether the US setup carries into the Korea open.",
            "source": "Yahoo Finance",
            "url": "https://finance.yahoo.com/quote/DX-Y.NYB",
            "visual": "dollar-index.png",
            "themes": {"rates_macro": ["dollar", "dxy"], "market_positioning": ["risk appetite"]},
            "score": 16,
        },
        {
            "id": "fallback-bitcoin",
            "title": "Bitcoin chart checks whether speculative risk appetite is confirming equities",
            "summary": "Use Bitcoin as a fast risk-appetite cross-check before treating equity strength as durable.",
            "source": "CoinGecko",
            "url": "https://www.coingecko.com/en/coins/bitcoin",
            "visual": "bitcoin.png",
            "themes": {"market_positioning": ["risk appetite"]},
            "score": 14,
        },
        {
            "id": "fallback-economic-calendar",
            "title": "Economic calendar defines the macro event risk for Monday",
            "summary": "Use the calendar image to mark the events that could change rates, dollar, and index futures during the session.",
            "source": "Trading Economics",
            "url": "https://www.tradingeconomics.com/calendar",
            "visual": "economic-calendar-us.png",
            "themes": {"rates_macro": ["fed", "inflation", "jobs"]},
            "score": 15,
        },
        {
            "id": "fallback-earnings",
            "title": "Feature earnings tickers test whether AI and consumer themes still have support",
            "summary": "Use GOOGL, MSFT, META, AMZN, V, PI, UBER, and EXPE as Monday prep names for theme validation.",
            "source": "Autopark earnings drilldown",
            "url": "",
            "visual": "",
            "themes": {"earnings_signal": ["earnings", "guidance"], "ai_infra": ["ai", "cloud"]},
            "score": 15,
            "tickers": ["GOOGL", "MSFT", "META", "AMZN", "V", "PI", "UBER", "EXPE"],
        },
    ]
    rows = []
    current_dir = PROJECT_ROOT / "exports" / "current"
    for spec in specs:
        visual_path = current_dir / spec["visual"] if spec.get("visual") else None
        material = {
            "id": spec["id"],
            "title": spec["title"],
            "summary": spec["summary"],
            "source": spec["source"],
            "url": spec["url"],
            "type": "fallback_static_chart",
            "published_at": date,
            "visual_local_path": str(visual_path) if visual_path and visual_path.exists() else "",
            "tickers": spec.get("tickers") or [],
        }
        themes = spec["themes"]
        row = {
            "id": spec["id"],
            "title": spec["title"],
            "source": spec["source"],
            "url": spec["url"],
            "type": "fallback_static_chart",
            "published_at": date,
            "summary": spec["summary"],
            "score": spec["score"],
            "source_weight": 5,
            "recency_days": 0,
            "recency_bucket": "fallback",
            "recency_penalty": 0,
            "themes": [
                {"theme": theme, "label": THEME_LABELS.get(theme, theme), "hits": hits}
                for theme, hits in sorted(themes.items())
            ],
            "theme_keys": sorted(themes),
            "visual_local_path": material["visual_local_path"],
            "tickers": material["tickers"],
            "radar_question": radar_question(themes),
            "suggested_slot": suggested_slot(themes),
        }
        row.update(enrich_candidate_row(material, row, themes))
        rows.append(row)
    return rows


def radar_question(themes: dict[str, list[str]]) -> str:
    keys = set(themes)
    if keys == {"side_dish"}:
        return "오프닝/전환/마무리에 쓸 만한 화제성 소재인가?"
    if "ai_infra" in keys and "market_positioning" in keys:
        return "AI 기대와 높아진 밸류에이션을 시장이 계속 정당화할 수 있나?"
    if "ai_infra" in keys and "earnings_signal" in keys:
        return "AI 인프라 수요가 실제 숫자와 가이던스로 확인되는가?"
    if "energy_geopolitics" in keys and "rates_macro" in keys:
        return "유가/지정학이 금리와 할인율을 다시 흔드는가?"
    if "energy_geopolitics" in keys:
        return "유가와 지정학 리스크가 시장의 위험선호를 어디까지 누르는가?"
    if "market_positioning" in keys:
        return "시장은 과열을 보는가, 아니면 쉬어가는 위험선호를 보는가?"
    if "rates_macro" in keys:
        return "금리와 달러가 오늘 시장의 방향을 제한하는가?"
    return "오늘 시장이 이 소재를 왜 보고 있는가?"


def suggested_slot(themes: dict[str, list[str]]) -> str:
    keys = set(themes)
    if "side_dish" in keys and len(keys) == 1:
        return "단신/환기"
    if "earnings_signal" in keys and ("ai_infra" in keys or "market_positioning" in keys):
        return "시장 레이더 -> 필요시 특징주"
    if "ai_infra" in keys or "market_positioning" in keys or "rates_macro" in keys:
        return "추천 스토리라인 후보"
    if "energy_geopolitics" in keys:
        return "시장 배경/리스크"
    return "오늘의 이모저모"


def row_ref(row: dict) -> str:
    return f"`{clean(row.get('title'), 64)}`"


def source_key(row: dict) -> str:
    source = clean(row.get("source") or "").lower()
    url = clean(row.get("url") or "").lower()
    if "kobeissi" in source or "kobeissi" in url:
        return "kobeissi"
    if "bloomberg" in source or "bloomberg" in url:
        return "bloomberg"
    if "isabelnet" in source or "isabelnet" in url:
        return "isabelnet"
    if "cnbc" in source or "cnbc" in url:
        return "cnbc"
    if "yahoo" in source or "yahoo" in url:
        return "yahoo"
    if "investinq" in source or "investinq" in url or "stockmarket.news" in source:
        return "stockmarket.news"
    return source or url[:48] or row.get("id", "")


def top_rows_for(rows: list[dict], required: set[str], excluded_ids: set[str], limit: int = 3) -> list[dict]:
    picked = []
    used_sources = set()
    for row in rows:
        if row.get("id") in excluded_ids:
            continue
        keys = set(row.get("theme_keys") or [])
        if not (keys & required):
            continue
        key = source_key(row)
        if key in used_sources:
            continue
        picked.append(row)
        used_sources.add(key)
        if len(picked) >= limit:
            return picked
    for row in rows:
        if row.get("id") in excluded_ids or row in picked:
            continue
        keys = set(row.get("theme_keys") or [])
        if not (keys & required):
            continue
        picked.append(row)
        if len(picked) >= limit:
            return picked
    return picked


def make_storyline(title: str, one_liner: str, rows: list[dict], why: str, angle: str) -> dict:
    return {
        "title": title,
        "one_liner": one_liner,
        "why_selected": why,
        "angle": angle,
        "selected_item_ids": [row["id"] for row in rows],
        "reference_titles": [clean(row.get("title"), 76) for row in rows],
        "material_refs": [
            {
                "id": row["id"],
                "title": clean(row.get("title"), 76),
                "source": row.get("source") or "",
                "url": row.get("url") or "",
                "slot": row.get("suggested_slot") or "",
            }
            for row in rows
        ],
    }


def build_storylines(rows: list[dict]) -> list[dict]:
    storylines = []
    used: set[str] = set()

    energy_rows = top_rows_for(rows, {"energy_geopolitics"}, used, 3)
    if energy_rows:
        used.update(row["id"] for row in energy_rows)
        storylines.append(
            make_storyline(
                "유가 쇼크를 시장은 어디까지 무시할 수 있나",
                "유가와 지정학 리스크가 커졌는데도 주식이 버티는 이유를 AI 기대와 위험선호로 점검하는 꼭지.",
                energy_rows,
                "Kobeissi/Bloomberg/Yahoo/CNBC 계열 후보가 같은 에너지·지정학 축을 반복해서 가리킨다.",
                "먼저 유가/호르무즈/UAE-OPEC 재료를 짚고, 이어서 주식시장이 왜 바로 꺾이지 않는지 위험선호와 AI 기대를 붙인다.",
            )
        )

    positioning_rows = top_rows_for(rows, {"market_positioning"}, used, 3)
    if positioning_rows:
        used.update(row["id"] for row in positioning_rows)
        storylines.append(
            make_storyline(
                "과열인가, 강세장의 연료인가",
                "개인 콜옵션, 밸류에이션, 포지셔닝 자료를 묶어 시장의 위험선호가 어느 정도까지 올라왔는지 보는 꼭지.",
                positioning_rows,
                "시장 방향보다 포지션의 공격성이 소재가 되는 자료들이 따로 잡힌다.",
                "포지셔닝 차트나 market cap/GDP 코멘트를 앞에 두고, 이것이 단기 과열인지 추세 확인인지 질문으로 남긴다.",
            )
        )

    ai_pool = [row for row in rows if "ai_infra" in set(row.get("theme_keys") or []) and "energy_geopolitics" not in set(row.get("theme_keys") or [])]
    ai_rows = top_rows_for(ai_pool or rows, {"ai_infra"}, used, 3)
    if ai_rows:
        used.update(row["id"] for row in ai_rows)
        storylines.append(
            make_storyline(
                "AI 기대는 아직 시장의 방패인가",
                "OpenAI, AI 포트폴리오, 반도체·스토리지 강세를 통해 시장이 지정학 리스크보다 AI 성장성을 더 크게 보는지 확인하는 꼭지.",
                ai_rows,
                "04.29 실제 방송의 핵심 질문이 AI 기대를 실적과 생산성으로 정당화할 수 있느냐였고, radar에도 관련 후보가 남아 있다.",
                "AI 관련 주가/기업 뉴스/인프라 수요 자료를 묶되, 단순 호재가 아니라 높은 기대를 정당화하는 증거인지 본다.",
            )
        )

    earnings_rows = top_rows_for(rows, {"earnings_signal"}, used, 3)
    if len(storylines) < 3 and earnings_rows:
        used.update(row["id"] for row in earnings_rows)
        storylines.append(
            make_storyline(
                "실적은 테마를 증명하는가",
                "개별 종목 실적을 단순 등락이 아니라 AI·소비·플랫폼 테마의 증거로 쓰는 꼭지.",
                earnings_rows,
                "실적 후보는 많지만 방송에서는 큰 테마를 증명하는 사례로 골라야 한다.",
                "실적주를 먼저 나열하지 말고, 시장이 검증하려는 테마를 먼저 말한 뒤 종목을 사례로 붙인다.",
            )
        )

    side_rows = top_rows_for(rows, {"side_dish"}, used, 2)
    if len(storylines) < 3 and side_rows:
        storylines.append(
            make_storyline(
                "오프닝에 쓸 수 있는 환기 소재",
                "메인 thesis는 아니지만 시청자 관심을 열어주는 인물·정책·기업 단신을 짧게 쓰는 꼭지.",
                side_rows,
                "방송 앞뒤에는 무거운 시장 논리만큼 분위기를 여는 소재도 필요하다.",
                "한 장 이상 끌지 말고, 관련 시장 질문으로 빠르게 넘긴다.",
            )
        )

    return storylines[:3]


def render_markdown(date: str, rows: list[dict]) -> str:
    theme_counter = Counter(theme for row in rows for theme in row.get("theme_keys", []))
    storylines = build_storylines(rows)
    lines = [
        "# Market Radar",
        "",
        f"- 대상일: `{date}`",
        f"- 생성 시각: `{datetime.now().strftime('%y.%m.%d %H:%M')}`",
        f"- 후보 수: `{len(rows)}`",
        "",
        "## Theme Pulse",
        "",
    ]
    for theme, count in theme_counter.most_common():
        lines.append(f"- {THEME_LABELS.get(theme, theme)}: `{count}`")

    lines.extend(["", "## Radar Storylines", ""])
    for index, storyline in enumerate(storylines, start=1):
        lines.extend(
            [
                f"### {index}. {storyline['title']}",
                "",
                f"> {storyline['one_liner']}",
                "",
                f"- 선정 이유: {storyline['why_selected']}",
                f"- 구성 각도: {storyline['angle']}",
                f"- 참고 자료: {', '.join(f'`{title}`' for title in storyline['reference_titles'])}",
                "",
            ]
        )

    lines.extend(["", "## Top Radar Items", ""])
    for index, row in enumerate(rows[:20], start=1):
        source = f"[{row['source']}]({row['url']})" if str(row.get("url", "")).startswith("http") else row["source"]
        theme_text = ", ".join(item["label"] for item in row.get("themes", [])) or "-"
        lines.extend(
            [
                f"### {index}. {row['title']}",
                "",
                f"- 점수: `{row['score']}` / 출처가중치: `{row['source_weight']}` / 슬롯: `{row['suggested_slot']}`",
                f"- 출처: {source}",
                f"- 테마: {theme_text}",
                f"- 레이더 질문: {row['radar_question']}",
                f"- 요약: {row['summary']}",
            ]
        )
        if row.get("visual_local_path"):
            path = Path(row["visual_local_path"])
            if not path.is_absolute():
                path = REPO_ROOT / row["visual_local_path"]
            lines.extend(["", f"![{row['title']}]({path})"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


THEME_LABELS.update(
    {
        "ai_infra": "AI/인프라",
        "market_positioning": "시장 포지셔닝/밸류에이션",
        "rates_macro": "금리/매크로",
        "energy_geopolitics": "에너지/지정학",
        "earnings_signal": "실적 신호",
        "side_dish": "단신/화제",
    }
)


def radar_question(themes: dict[str, list[str]]) -> str:
    keys = set(themes)
    if keys == {"side_dish"}:
        return "오프닝이나 마무리에 붙일 만한 화제인가?"
    if "ai_infra" in keys and "market_positioning" in keys:
        return "AI 기대와 높아진 밸류에이션을 시장이 계속 정당화할 수 있나?"
    if "ai_infra" in keys and "earnings_signal" in keys:
        return "AI 인프라 수요가 실제 숫자와 가이던스로 확인되는가?"
    if "energy_geopolitics" in keys and "rates_macro" in keys:
        return "유가와 지정학 리스크가 금리와 인플레이션 압력을 다시 키우는가?"
    if "energy_geopolitics" in keys:
        return "유가와 지정학 리스크가 시장의 위험선호를 어디까지 누르는가?"
    if "market_positioning" in keys:
        return "지금의 강세는 추세인가, 과열 신호인가?"
    if "rates_macro" in keys:
        return "금리와 달러가 오늘 시장 방향을 얼마나 제한하는가?"
    return "오늘 시장이 어떤 소재를 보고 있는가?"


def suggested_slot(themes: dict[str, list[str]]) -> str:
    keys = set(themes)
    if "side_dish" in keys and len(keys) == 1:
        return "단신/화제"
    if "earnings_signal" in keys and ("ai_infra" in keys or "market_positioning" in keys):
        return "시장 레이어 -> 특징주"
    if "ai_infra" in keys or "market_positioning" in keys or "rates_macro" in keys:
        return "추천 스토리라인 후보"
    if "energy_geopolitics" in keys:
        return "시장 배경/리스크"
    return "오늘의 이모저모"


def build_storylines(rows: list[dict]) -> list[dict]:
    storylines = []
    used: set[str] = set()

    energy_rows = top_rows_for(rows, {"energy_geopolitics"}, used, 3)
    if energy_rows:
        used.update(row["id"] for row in energy_rows)
        storylines.append(
            make_storyline(
                "유가 리스크를 시장은 어디까지 무시할 수 있나",
                "유가와 지정학 리스크가 커지는 와중에도 주식시장이 버티는 이유를 AI 기대와 위험선호로 읽는 축입니다.",
                energy_rows,
                "Kobeissi, Bloomberg, Yahoo, CNBC 계열 후보가 같은 에너지·지정학 축을 반복해서 가리킵니다.",
                "먼저 유가·호르무즈·OPEC 재료를 짚고, 이어서 주식시장이 바로 꺾이지 않는 이유를 위험선호와 AI 기대에서 찾습니다.",
            )
        )

    positioning_rows = top_rows_for(rows, {"market_positioning"}, used, 3)
    if positioning_rows:
        used.update(row["id"] for row in positioning_rows)
        storylines.append(
            make_storyline(
                "강세장의 연료인가, 과열의 신호인가",
                "개인 콜옵션, 레버리지 ETF, 밸류에이션 자료를 묶어 위험선호가 얼마나 강한지 보는 축입니다.",
                positioning_rows,
                "시장 방향보다 투자자의 공격성이 소재가 되는 자료들이 같이 잡혔습니다.",
                "포지셔닝 차트와 밸류에이션 경고를 앞에 놓고, 강세의 연료인지 과열 신호인지 묻는 흐름으로 정리합니다.",
            )
        )

    ai_pool = [row for row in rows if "ai_infra" in set(row.get("theme_keys") or []) and "energy_geopolitics" not in set(row.get("theme_keys") or [])]
    ai_rows = top_rows_for(ai_pool or rows, {"ai_infra"}, used, 3)
    if ai_rows:
        used.update(row["id"] for row in ai_rows)
        storylines.append(
            make_storyline(
                "AI 기대는 아직 시장의 방패인가",
                "AI 인프라, 빅테크 실적, 반도체 스토리지가 지정학 리스크보다 크게 가격에 반영되는지 보는 축입니다.",
                ai_rows,
                "AI 기대를 실적과 생산성, 인프라 수요로 정당화할 수 있는지 관련 후보가 모였습니다.",
                "AI 관련 주가와 기업 뉴스, 인프라 수요 자료를 묶되 단순 호재가 아니라 숫자로 확인되는지 봅니다.",
            )
        )

    earnings_rows = top_rows_for(rows, {"earnings_signal"}, used, 3)
    if len(storylines) < 3 and earnings_rows:
        used.update(row["id"] for row in earnings_rows)
        storylines.append(
            make_storyline(
                "실적은 테마를 증명하는가",
                "개별 종목 실적을 단순 등락보다 AI·소비·클라우드 테마를 검증하는 증거로 보는 축입니다.",
                earnings_rows,
                "실적 후보가 많지만 방송에서는 테마를 증명하는 자료로 골라야 합니다.",
                "실적주를 나열하지 말고 시장이 검증하는 테마를 먼저 말한 뒤 종목을 붙입니다.",
            )
        )

    side_rows = top_rows_for(rows, {"side_dish"}, used, 2)
    if len(storylines) < 3 and side_rows:
        storylines.append(
            make_storyline(
                "오프닝에 붙일 수 있는 단신",
                "메인 thesis는 아니지만 시청자 관심을 이어주는 인물·정책·기업 단신을 짧게 붙이는 축입니다.",
                side_rows,
                "무거운 시장 논리만큼 분위기를 여는 소재가 필요합니다.",
                "길게 설명하지 말고 관련 시장 질문으로 빠르게 연결합니다.",
            )
        )

    return storylines[:3]


def render_markdown(date: str, rows: list[dict]) -> str:
    theme_counter = Counter(theme for row in rows for theme in row.get("theme_keys", []))
    storylines = build_storylines(rows, date)
    lines = [
        "# Market Radar",
        "",
        f"- 대상일: `{date}`",
        f"- 생성 시각: `{datetime.now().strftime('%y.%m.%d %H:%M')}`",
        f"- 후보 수: `{len(rows)}`",
        "",
        "## Theme Pulse",
        "",
    ]
    for theme, count in theme_counter.most_common():
        lines.append(f"- {THEME_LABELS.get(theme, theme)}: `{count}`")

    lines.extend(["", "## Radar Storylines", ""])
    for index, storyline in enumerate(storylines, start=1):
        recommendation = storyline.get("recommendation") or ""
        label = storyline.get("recommendation_label") or ""
        lines.extend(
            [
                f"### {index}. {storyline['title']}",
                "",
                f"- 추천도: `{recommendation}` {label}".rstrip(),
                "",
                f"> {storyline['one_liner']}",
                "",
                f"- 선정 이유: {storyline['why_selected']}",
                f"- 구성 각도: {storyline['angle']}",
                f"- 참고 자료: {', '.join(f'`{title}`' for title in storyline['reference_titles'])}",
                "",
            ]
        )

    lines.extend(["", "## Top Radar Items", ""])
    for index, row in enumerate(rows[:20], start=1):
        source = f"[{row['source']}]({row['url']})" if str(row.get("url", "")).startswith("http") else row["source"]
        theme_text = ", ".join(item["label"] for item in row.get("themes", [])) or "-"
        lines.extend(
            [
                f"### {index}. {row['title']}",
                "",
                f"- 점수: `{row['score']}` / 출처 가중치: `{row['source_weight']}` / 슬롯: `{row['suggested_slot']}`",
                f"- 출처: {source}",
                f"- 테마: {theme_text}",
                f"- 레이더 질문: {row['radar_question']}",
                f"- 요약: {row['summary']}",
            ]
        )
        if row.get("visual_local_path"):
            path = Path(row["visual_local_path"])
            if not path.is_absolute():
                path = REPO_ROOT / row["visual_local_path"]
            lines.extend(["", f"![{row['title']}]({path})"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def primary_theme(row: dict) -> str:
    keys = row.get("theme_keys") or []
    return keys[0] if keys else "general"


def row_text(row: dict) -> str:
    return clean(" ".join(str(row.get(key) or "") for key in ["title", "summary", "source", "url"])).lower()


def theme_label(theme: str) -> str:
    return THEME_LABELS.get(theme, theme)


def previous_storyline_theme_sets(date: str | None) -> set[tuple[str, ...]]:
    if not date:
        return set()
    current = PROCESSED_DIR / date
    previous_dirs = sorted(
        [path for path in PROCESSED_DIR.iterdir() if path.is_dir() and path.name < current.name],
        key=lambda path: path.name,
        reverse=True,
    )
    if not previous_dirs:
        return set()
    payload = load_json(previous_dirs[0] / "market-radar.json")
    candidates = {row.get("id"): row for row in payload.get("candidates", [])}
    theme_sets: set[tuple[str, ...]] = set()
    for storyline in payload.get("storylines", []):
        keys: set[str] = set()
        for item_id in storyline.get("selected_item_ids", []):
            keys.update(candidates.get(item_id, {}).get("theme_keys") or [])
        if keys:
            theme_sets.add(tuple(sorted(keys)))
    return theme_sets


def storyline_clusters(rows: list[dict], date: str | None) -> list[dict]:
    groups: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in rows:
        row_keys = row.get("theme_keys") or [primary_theme(row)]
        keys = tuple(sorted(row_keys))
        groups[keys].append(row)
        if len(row_keys) != 1:
            continue
        for key in row_keys:
            groups[(key,)].append(row)

    previous_sets = previous_storyline_theme_sets(date)
    clusters = []
    for keys, group_rows in groups.items():
        if keys == ("general",):
            continue
        deduped = []
        seen_ids = set()
        seen_titles = set()
        for row in sorted(group_rows, key=lambda item: (-item.get("score", 0), item.get("title", ""))):
            title_key = clean(row.get("title"), 90).lower()
            if row.get("id") in seen_ids or title_key in seen_titles:
                continue
            seen_ids.add(row.get("id"))
            seen_titles.add(title_key)
            deduped.append(row)
        if not deduped:
            continue
        top = deduped[:4]
        sources = {source_key(row) for row in top}
        score = sum(row.get("score", 0) for row in top[:3])
        score += min(4, len(sources))
        score += 2 if len(keys) >= 2 else 0
        if len(sources) == 1:
            score -= 5
        if tuple(sorted(keys)) in previous_sets:
            score -= 6
        if keys == ("side_dish",):
            score -= 4
        clusters.append({"keys": keys, "rows": top, "score": score, "source_count": len(sources)})
    return sorted(clusters, key=lambda cluster: (-cluster["score"], cluster["keys"]))


def dynamic_title(rows: list[dict], keys: tuple[str, ...]) -> str:
    blob = " ".join(row_text(row) for row in rows[:3])
    tickers = []
    for row in rows:
        for ticker in row.get("tickers") or []:
            if ticker not in tickers:
                tickers.append(ticker)

    if "earnings_signal" in keys and tickers:
        return f"{', '.join(tickers[:3])} 실적이 오늘 테마를 증명하는가"
    if keys == ("earnings_signal",):
        if "red or blue" in blob or "politics" in blob:
            return "시장은 결국 실적과 혁신만 보나"
        return "실적 모멘텀은 랠리의 두 번째 엔진인가"
    if keys == ("energy_geopolitics",):
        if "exports" in blob or "exxon" in blob or "opec" in blob:
            return "유가 리스크, 에너지주에는 기회인가"
        return "유가 재료가 다시 증시 리스크가 되는가"
    if "openai" in blob:
        return "OpenAI 숫자가 다시 AI 인프라 기대를 받치는가"
    if "mark cuban" in blob or "data center" in blob or "compute" in blob:
        return "AI 인프라 투자, 누가 비용을 감당하나"
    if "nvidia" in blob or "semiconductor" in blob or "chip" in blob:
        return "반도체 기대는 아직 가격의 방패인가"
    if "risk appetite" in blob or "risky asset" in blob:
        return "위험자산 자금 유입, 강세의 연료인가"
    if "valuation" in blob or "market cap to gdp" in blob:
        return "밸류에이션 경고를 시장은 왜 넘기는가"
    if "iran" in blob or "hormuz" in blob:
        return "이란 뉴스에 되살아난 유가 프리미엄"
    if "oil" in blob or "wti" in blob or "brent" in blob:
        return "이란 뉴스에 되살아난 유가 프리미엄"
    if "fedwatch" in blob or "fomc" in blob or "rate cut" in blob:
        return "Fed 확률표가 말하는 다음 가격 변수"
    if "earnings_signal" in keys:
        return "실적 숫자가 기대를 다시 검증하는가"
    if "market_positioning" in keys:
        return "포지셔닝 자료가 말하는 시장의 온도"
    if "ai_infra" in keys:
        return "AI 기대가 오늘도 가격을 지탱하는가"
    if "energy_geopolitics" in keys:
        return "에너지 리스크가 다시 전면에 서는가"
    if "rates_macro" in keys:
        return "금리와 달러가 오늘의 숨은 제약인가"
    return clean(rows[0].get("title"), 42)


def dynamic_one_liner(rows: list[dict], keys: tuple[str, ...]) -> str:
    refs = [clean(row.get("title"), 44) for row in rows[:3]]
    labels = ", ".join(theme_label(key) for key in keys)
    return f"{labels} 재료를 {len(rows)}개 묶어, 오늘 시장이 실제로 반응한 축인지 확인하는 꼭지입니다. 핵심 근거는 {', '.join(refs)}입니다."


def dynamic_why(rows: list[dict], keys: tuple[str, ...], repeated: bool) -> str:
    sources = []
    for row in rows:
        label = source_key(row)
        if label and label not in sources:
            sources.append(label)
    if len(sources) == 1:
        base = f"{sources[0]} 한 출처 안에서 같은 방향의 신호가 여러 개 반복됐습니다."
    else:
        base = f"{', '.join(sources[:4])} 등 {len(sources)}개 출처가 같은 방향의 신호를 냈습니다."
    novelty = "전일에도 비슷한 테마가 있어 감점했지만, 오늘 새 근거가 충분해 후보로 유지했습니다." if repeated else "전일 고정 프레임보다 오늘 수집물의 점수와 구체성이 더 강하게 잡힌 묶음입니다."
    return f"{base} {novelty}"


def dynamic_angle(rows: list[dict], keys: tuple[str, ...]) -> str:
    if "earnings_signal" in keys:
        return "종목별 등락을 나열하지 말고, 실적이 어떤 테마를 증명하거나 깨는지부터 묻습니다."
    if "market_positioning" in keys:
        return "가격이 오른 이유보다 자금 흐름과 포지셔닝이 얼마나 과열됐는지를 먼저 보여줍니다."
    if "ai_infra" in keys:
        return "AI 기대를 막연한 성장 서사가 아니라 매출, capex, 반도체 수요, 비용 부담으로 쪼개 봅니다."
    if "energy_geopolitics" in keys:
        return "지정학 뉴스 자체보다 유가, 에너지주, 인플레이션 기대가 같이 움직이는지 확인합니다."
    if "rates_macro" in keys:
        return "Fed 확률, 달러, 장기금리를 한 묶음으로 보고 주식 리스크 프리미엄을 점검합니다."
    return "오프닝 단신으로 쓸지, 메인 스토리의 보조 근거로 쓸지부터 정하고 짧게 연결합니다."


def recommendation_stars(cluster_score: int | float, picked: list[dict], keys: tuple[str, ...], repeated: bool) -> int:
    sources = {source_key(row) for row in picked}
    score = float(cluster_score)
    if len(sources) >= 3:
        score += 3
    if len(keys) >= 2:
        score += 2
    if repeated:
        score -= 4
    if len(sources) == 1:
        score -= 4
    if score >= 43:
        return 3
    if score >= 34:
        return 2
    return 1


def recommendation_label(stars: int) -> str:
    if stars >= 3:
        return "강추"
    if stars == 2:
        return "추천"
    return "검토"


def build_storylines(rows: list[dict], date: str | None = None) -> list[dict]:
    previous_sets = previous_storyline_theme_sets(date)
    clusters = storyline_clusters(rows, date)
    storylines = []
    used_ids: set[str] = set()
    used_primary: set[str] = set()

    for cluster in clusters:
        keys = tuple(cluster["keys"])
        primary = keys[0] if keys else "general"
        if primary in used_primary and len(storylines) < 2:
            continue
        picked = [row for row in cluster["rows"] if row.get("id") not in used_ids][:3]
        if not picked:
            continue
        repeated = tuple(sorted(keys)) in previous_sets
        storyline = make_storyline(
            dynamic_title(picked, keys),
            dynamic_one_liner(picked, keys),
            picked,
            dynamic_why(picked, keys, repeated),
            dynamic_angle(picked, keys),
        )
        storyline = enrich_storyline(storyline, picked, len(storylines) + 1)
        storyline["theme_keys"] = list(keys)
        storyline["selection_method"] = "dynamic_cluster"
        storyline["cluster_score"] = cluster["score"]
        storyline["novelty_note"] = "penalized_for_previous_day_theme" if repeated else "fresh_or_stronger_than_previous_day"
        stars = recommendation_stars(cluster["score"], picked, keys, repeated)
        storyline["recommendation_stars"] = stars
        storyline["recommendation"] = "★" * stars + "☆" * (3 - stars)
        storyline["recommendation_label"] = recommendation_label(stars)
        storylines.append(storyline)
        used_ids.update(row["id"] for row in picked)
        used_primary.add(primary)
        if len(storylines) >= 5:
            break

    if len(storylines) < 5:
        for row in rows:
            if row.get("id") in used_ids:
                continue
            keys = tuple(row.get("theme_keys") or [primary_theme(row)])
            storyline = make_storyline(
                dynamic_title([row], keys),
                dynamic_one_liner([row], keys),
                [row],
                "상위 클러스터가 부족해 단일 고득점 후보를 예비 스토리로 올렸습니다.",
                dynamic_angle([row], keys),
            )
            storyline = enrich_storyline(storyline, [row], len(storylines) + 1)
            storyline["theme_keys"] = list(keys)
            storyline["selection_method"] = "single_high_score_fallback"
            storyline["cluster_score"] = row.get("score", 0)
            storyline["novelty_note"] = "fallback"
            stars = recommendation_stars(row.get("score", 0), [row], keys, False)
            storyline["recommendation_stars"] = stars
            storyline["recommendation"] = "★" * stars + "☆" * (3 - stars)
            storyline["recommendation_label"] = recommendation_label(stars)
            storylines.append(storyline)
            used_ids.add(row["id"])
            if len(storylines) >= 5:
                break

    return storylines[:5]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--limit-news", type=int, default=120)
    parser.add_argument("--limit-x", type=int, default=120)
    parser.add_argument("--limit-visuals", type=int, default=60)
    args = parser.parse_args()

    rows = build_rows(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    if len(rows) < 3:
        seen_ids = {row.get("id") for row in rows}
        rows.extend(row for row in static_chart_rows(args.date) if row.get("id") not in seen_ids)
        rows = sorted(rows, key=lambda row: (-row["score"], row["title"]))
    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_count": len(rows),
        "storylines": build_storylines(rows, args.date),
        "candidates": rows,
    }
    json_path = processed_dir / "market-radar.json"
    md_path = notion_dir / "market-radar.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(args.date, rows), encoding="utf-8")
    print(json.dumps({"ok": True, "candidate_count": len(rows), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
