#!/usr/bin/env python3
"""Build a market-radar ledger focused on what the market is watching now."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials, load_json, x_items

REPO_ROOT = PROCESSED_DIR.parents[2]

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
    return max([weight for key, weight in CORE_SOURCE_WEIGHTS.items() if key in blob] or [3])


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


def build_rows(date: str, limit_news: int, limit_x: int, limit_visuals: int) -> list[dict]:
    materials = gather_materials(date, limit_news, limit_x, limit_visuals)
    materials.extend(load_extra_x_posts(date, limit_x))
    rows = []
    seen = set()
    for material in materials:
        key = material.get("url") or material.get("id") or material.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        themes = detect_themes(material)
        weight = source_weight(material)
        visual_bonus = 2 if visual_path(material) else 0
        theme_bonus = min(10, sum(len(values) for values in themes.values()))
        x_bonus = 2 if material.get("type") in {"x_social", "visual_card"} else 0
        bridge_bonus = 2 if len(themes) >= 2 else 0
        side_penalty = 3 if set(themes) == {"side_dish"} else 0
        score = weight + visual_bonus + theme_bonus + x_bonus + bridge_bonus - side_penalty
        if score < 7 and not themes:
            continue
        title = material.get("title") or material.get("headline") or material.get("summary") or key
        rows.append(
            {
                "id": material.get("id") or key,
                "title": clean(title, 140),
                "source": material.get("source") or material.get("source_name") or material.get("source_id") or material.get("type") or "",
                "url": material.get("url") or "",
                "type": material.get("type") or "candidate",
                "published_at": material.get("published_at") or "",
                "summary": clean(material.get("summary") or title, 420),
                "score": score,
                "source_weight": weight,
                "themes": [
                    {"theme": theme, "label": THEME_LABELS.get(theme, theme), "hits": hits}
                    for theme, hits in sorted(themes.items())
                ],
                "theme_keys": sorted(themes),
                "visual_local_path": visual_path(material),
                "tickers": material.get("tickers") or [],
                "radar_question": radar_question(themes),
                "suggested_slot": suggested_slot(themes),
            }
        )
    return sorted(rows, key=lambda row: (-row["score"], row["title"]))


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--limit-news", type=int, default=120)
    parser.add_argument("--limit-x", type=int, default=120)
    parser.add_argument("--limit-visuals", type=int, default=60)
    args = parser.parse_args()

    rows = build_rows(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "candidate_count": len(rows),
        "storylines": build_storylines(rows),
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
