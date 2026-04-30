#!/usr/bin/env python3
"""Build a small ledger for short side-dish/refresh materials from collected items."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials


SIDE_DISH_KEYWORDS = {
    "tech_ceo": ["musk", "altman", "openai", "xai", "sam altman", "elon"],
    "political_theater": ["trump", "white house", "state visit", "king charles", "charles", "royal", "buckingham"],
    "market_anecdote": ["paul tudor jones", "dotcom", "bubble", "1929", "1987", "2000", "stock market cap to gdp"],
    "geopolitical_quote": ["iran", "hormuz", "opec", "uae", "tariff", "sanction"],
}

HARD_NEWS_TYPES = {"news"}


def clean(value: str | None, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def material_blob(material: dict) -> str:
    return " ".join(str(material.get(key) or "") for key in ["title", "headline", "summary", "source", "raw_text", "text"]).lower()


def score_material(material: dict) -> tuple[int, list[str], str]:
    blob = material_blob(material)
    tags = []
    score = 0
    for tag, keywords in SIDE_DISH_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword in blob]
        if hits:
            tags.append(tag)
            score += min(6, len(hits) * 2)
    source = (material.get("source") or material.get("source_name") or "").lower()
    item_type = (material.get("type") or "").lower()
    if item_type == "x" or "x.com" in (material.get("url") or ""):
        score += 3
    if item_type in HARD_NEWS_TYPES:
        score -= 1
    if material.get("visual_local_path") or material.get("image_count"):
        score += 2
    if any(name in source for name in ["kobeissi", "investinq", "stockmarket.news", "unusual", "deitaone", "zerohedge"]):
        score += 2
    reason = ", ".join(tags) if tags else "단신성 키워드 약함"
    return score, tags, reason


def load_extra_x_posts(date: str) -> list[dict]:
    processed = PROCESSED_DIR / date
    extras = []
    for path in processed.glob("*x*posts*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for post in payload.get("posts", []):
            extras.append(
                {
                    "id": post.get("url") or post.get("text", "")[:60],
                    "headline": post.get("text") or post.get("raw_text") or "",
                    "source": post.get("source_name") or post.get("source_id") or "X",
                    "url": post.get("url") or "",
                    "type": "x",
                    "published_at": post.get("created_at") or "",
                    "summary": post.get("text") or "",
                    "image_count": post.get("image_count") or len(post.get("images") or []),
                }
            )
    return extras


def build_rows(date: str, limit_news: int, limit_x: int, limit_visuals: int) -> list[dict]:
    materials = gather_materials(date, limit_news, limit_x, limit_visuals)
    materials.extend(load_extra_x_posts(date))
    rows = []
    seen = set()
    for material in materials:
        key = material.get("url") or material.get("id") or material.get("headline") or material.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        score, tags, reason = score_material(material)
        if not tags or score < 4:
            continue
        rows.append(
            {
                "id": material.get("id") or key,
                "headline": material.get("headline") or material.get("title") or material.get("summary") or "",
                "source": material.get("source") or material.get("source_name") or material.get("type") or "",
                "url": material.get("url") or "",
                "type": material.get("type") or "",
                "published_at": material.get("published_at") or "",
                "score": score,
                "tags": tags,
                "reason": reason,
                "summary": material.get("summary") or "",
                "visual_local_path": material.get("visual_local_path") or "",
            }
        )
    rows.sort(key=lambda row: (-row["score"], row["headline"]))
    return rows


def render_markdown(date: str, rows: list[dict]) -> str:
    lines = [
        "# Side-dish Candidates",
        "",
        f"- 대상일: `{date}`",
        f"- 생성 시각: `{datetime.now().strftime('%y.%m.%d %H:%M')}`",
        f"- 후보 수: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("- 후보 없음")
        return "\n".join(lines).rstrip() + "\n"

    for row in rows[:12]:
        label = row["source"] or row["type"] or "source"
        source = f"[{label}]({row['url']})" if str(row.get("url", "")).startswith("http") else label
        lines.extend(
            [
                f"## {clean(row['headline'], 80)}",
                "",
                f"- 출처: {source}",
                f"- 점수: `{row['score']}` / 태그: {', '.join(row['tags']) or '-'}",
                f"- 쓰임새: 메인 thesis가 아니라 오프닝/전환/마무리 환기 소재로 분리",
                f"- 메모: {row['reason']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--limit-news", type=int, default=100)
    parser.add_argument("--limit-x", type=int, default=80)
    parser.add_argument("--limit-visuals", type=int, default=40)
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
        "candidates": rows,
    }
    json_path = processed_dir / "side-dish-candidates.json"
    md_path = notion_dir / "side-dish-candidates.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(args.date, rows), encoding="utf-8")
    print(json.dumps({"ok": True, "candidate_count": len(rows), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
