#!/usr/bin/env python3
"""Cluster today-misc candidates before model-based storyline selection."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials


CLUSTER_RULES = [
    ("market_tone", ["futures", "nasdaq", "s&p", "sentiment", "market", "stock", "positioning", "dow"]),
    ("rates_fx_policy", ["rate", "inflation", "bank", "boj", "fed", "dollar", "yen", "currency", "treasury"]),
    ("energy_geopolitics", ["oil", "crude", "iran", "middle east", "war", "supply", "inventory", "china"]),
    ("ai_tech_rotation", ["ai", "openai", "semiconductor", "chip", "cloud", "software", "tech", "data center"]),
    ("earnings_company", ["earnings", "guidance", "gm", "tariff", "tesla", "boeing", "revenue", "profit"]),
    ("crypto_risk", ["bitcoin", "crypto", "coinbase", "risk asset"]),
]

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "from",
    "this",
    "into",
    "amid",
    "near",
    "after",
    "before",
    "market",
    "markets",
    "stock",
    "stocks",
    "today",
}


def normalize(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


def token_set(material: dict) -> set[str]:
    text = " ".join(
        str(material.get(key) or "")
        for key in ["title", "summary", "source", "url", "type"]
    )
    text += " " + " ".join(material.get("market_hooks") or [])
    text += " " + " ".join(material.get("tickers") or [])
    tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9&.-]{1,}", text.lower()))
    return {token for token in tokens if token not in STOPWORDS and len(token) > 2}


def classify(material: dict) -> str:
    text = normalize(
        " ".join(
            [
                str(material.get("title") or ""),
                str(material.get("summary") or ""),
                " ".join(material.get("market_hooks") or []),
                " ".join(material.get("tickers") or []),
            ]
        )
    )
    scores = {}
    for cluster_id, keywords in CLUSTER_RULES:
        scores[cluster_id] = sum(1 for keyword in keywords if keyword in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other_watchlist"


def representative_items(items: list[dict], limit: int) -> list[dict]:
    def score(item: dict) -> tuple[int, int, str]:
        has_visual = 1 if item.get("visual_local_path") else 0
        numeric_score = item.get("score")
        numeric = int(numeric_score) if isinstance(numeric_score, int | float) else 0
        return (has_visual, numeric, item.get("title") or "")

    return sorted(items, key=score, reverse=True)[:limit]


def build_clusters(materials: list[dict], representatives_per_cluster: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for material in materials:
        grouped[classify(material)].append(material)

    clusters = []
    for cluster_id, items in sorted(grouped.items()):
        hook_counter = Counter()
        ticker_counter = Counter()
        source_counter = Counter()
        token_counter = Counter()
        for item in items:
            hook_counter.update(item.get("market_hooks") or [])
            ticker_counter.update(item.get("tickers") or [])
            source_counter.update([item.get("source") or item.get("type") or "unknown"])
            token_counter.update(token_set(item))
        reps = representative_items(items, representatives_per_cluster)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "label": cluster_id.replace("_", " "),
                "item_count": len(items),
                "sources": [source for source, _ in source_counter.most_common(6)],
                "market_hooks": [hook for hook, _ in hook_counter.most_common(8)],
                "tickers": [ticker for ticker, _ in ticker_counter.most_common(8)],
                "keywords": [token for token, _ in token_counter.most_common(12)],
                "representative_items": [compact_material(item) for item in reps],
            }
        )
    return sorted(clusters, key=lambda row: row["item_count"], reverse=True)


def compact_material(material: dict) -> dict:
    return {
        "id": material.get("id"),
        "type": material.get("type"),
        "source": material.get("source"),
        "title": material.get("title"),
        "url": material.get("url"),
        "published_at": material.get("published_at"),
        "summary": compact_text(material.get("summary"), 500),
        "market_hooks": material.get("market_hooks") or [],
        "tickers": material.get("tickers") or [],
        "score": material.get("score"),
        "visual_local_path": material.get("visual_local_path") or "",
    }


def render_markdown(target_date: str, clusters: list[dict]) -> str:
    lines = ["# 오늘의 이모저모 후보 클러스터", "", f"수집 기준일: `{target_date}`", ""]
    for cluster in clusters:
        lines.extend(
            [
                f"## {cluster['label']}",
                "",
                f"- 후보 수: `{cluster['item_count']}`",
                f"- 주요 출처: {', '.join(cluster['sources']) or '-'}",
                f"- hooks: {', '.join(cluster['market_hooks']) or '-'}",
                f"- keywords: {', '.join(cluster['keywords']) or '-'}",
                "",
            ]
        )
        for item in cluster["representative_items"]:
            lines.extend(
                [
                    f"### {item.get('title') or item.get('id')}",
                    "",
                    f"- ID: `{item.get('id')}`",
                    f"- 유형: `{item.get('type')}`",
                    f"- 출처: {item.get('url') or item.get('source') or '-'}",
                    f"- 요약: {item.get('summary') or '-'}",
                    "",
                ]
            )
            if item.get("visual_local_path"):
                lines.extend([f"![{item.get('title')}]({item['visual_local_path']})", ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--limit-news", type=int, default=40)
    parser.add_argument("--limit-x", type=int, default=30)
    parser.add_argument("--limit-visuals", type=int, default=24)
    parser.add_argument("--representatives-per-cluster", type=int, default=8)
    args = parser.parse_args()

    materials = gather_materials(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    clusters = build_clusters(materials, args.representatives_per_cluster)
    payload = {
        "ok": True,
        "target_date": args.date,
        "material_count": len(materials),
        "cluster_count": len(clusters),
        "materials": materials,
        "clusters": clusters,
    }

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "today-misc-clusters.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (notion_dir / "today-misc-clusters.md").write_text(render_markdown(args.date, clusters), encoding="utf-8")
    print(json.dumps({"ok": True, "material_count": len(materials), "cluster_count": len(clusters)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
