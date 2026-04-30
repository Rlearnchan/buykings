#!/usr/bin/env python3
"""Build a freeze-ready live experiment pack for pre-PPT Autopark trials."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cluster_today_misc import build_clusters
from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials, load_json


FIXED_CHART_HOOKS = {
    "bitcoin",
    "bond",
    "crude",
    "dollar",
    "fed",
    "fomc",
    "inflation",
    "jobs",
    "oil",
    "pce",
    "rate",
    "treasury",
    "yield",
}
TICKER_BRIDGE_HOOKS = {"ai", "buyback", "chip", "earnings", "guidance", "nvidia", "semiconductor", "tesla"}
BROADCAST_HOOKS = {
    "ai",
    "bitcoin",
    "earnings",
    "fed",
    "inflation",
    "iran",
    "market",
    "oil",
    "semiconductor",
    "tariff",
    "tesla",
    "trump",
}


def normalize(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def hooks(material: dict) -> set[str]:
    return {str(item).lower() for item in material.get("market_hooks") or []}


def title_blob(material: dict) -> str:
    return " ".join(
        normalize(str(material.get(key) or ""))
        for key in ["title", "summary", "source", "type", "url"]
    ).lower()


def clamp(value: int, low: int = 1, high: int = 5) -> int:
    return max(low, min(high, value))


def has_visual(material: dict) -> bool:
    return bool(material.get("visual_local_path") or material.get("image_refs"))


def score_bridge_to_fixed_charts(material: dict) -> int:
    text = title_blob(material)
    hit_count = len(hooks(material) & FIXED_CHART_HOOKS)
    hit_count += sum(1 for keyword in FIXED_CHART_HOOKS if keyword in text)
    return clamp(1 + hit_count)


def score_bridge_to_tickers(material: dict) -> int:
    text = title_blob(material)
    ticker_count = len(material.get("tickers") or [])
    hit_count = len(hooks(material) & TICKER_BRIDGE_HOOKS)
    hit_count += sum(1 for keyword in TICKER_BRIDGE_HOOKS if keyword in text)
    return clamp(1 + ticker_count + hit_count)


def score_block_expandability(material: dict) -> int:
    score = 1
    if has_visual(material):
        score += 1
    if material.get("type") in {"visual_card", "x_social"}:
        score += 1
    if score_bridge_to_fixed_charts(material) >= 3:
        score += 1
    if score_bridge_to_tickers(material) >= 3:
        score += 1
    return clamp(score)


def score_broadcast_hook(material: dict) -> int:
    text = title_blob(material)
    hit_count = len(hooks(material) & BROADCAST_HOOKS)
    hit_count += sum(1 for keyword in BROADCAST_HOOKS if keyword in text)
    if has_visual(material):
        hit_count += 1
    return clamp(1 + hit_count)


def score_explanation_cost(material: dict) -> int:
    text = title_blob(material)
    cost = 2
    if len(normalize(material.get("title"))) > 110:
        cost += 1
    if material.get("type") == "visual_card" and not normalize(material.get("summary")):
        cost += 1
    if not (hooks(material) or material.get("tickers")):
        cost += 1
    if any(term in text for term in ["derivative", "basis", "swap", "auction", "curve"]):
        cost += 1
    return clamp(cost)


def heuristic_total(row: dict) -> int:
    return (
        row["bridge_to_fixed_charts"]
        + row["bridge_to_tickers"]
        + row["block_expandability"]
        + row["broadcast_hook"]
        - row["explanation_cost"]
    )


def load_selection(path: Path) -> dict:
    payload = load_json(path)
    return payload.get("selection") or {}


def selected_lookup(selection: dict) -> dict[str, dict]:
    return {item.get("id"): item for item in selection.get("selected_items", []) if item.get("id")}


def storyline_lookup(selection: dict) -> dict[str, str]:
    lookup = {}
    for storyline in selection.get("storylines", []):
        title = normalize(storyline.get("title"))
        for item_id in storyline.get("selected_item_ids") or []:
            lookup[item_id] = title
    return lookup


def default_storyline_fit(material: dict, clusters: list[dict]) -> str:
    material_id = material.get("id")
    for cluster in clusters:
        if any(item.get("id") == material_id for item in cluster.get("representative_items") or []):
            return cluster.get("label") or cluster.get("cluster_id") or "unclustered"
    if hooks(material):
        return ", ".join(sorted(hooks(material))[:4])
    return "미분류 후보"


def build_ledger(materials: list[dict], clusters: list[dict], selection: dict) -> list[dict]:
    selected = selected_lookup(selection)
    selected_storylines = storyline_lookup(selection)
    rows = []
    for material in materials:
        material_id = material.get("id") or material.get("url") or material.get("title")
        row = {
            "id": material_id,
            "headline": material.get("title") or material.get("headline") or material_id,
            "source": material.get("source") or material.get("source_name") or material.get("source_id") or "",
            "url": material.get("url") or "",
            "type": material.get("type") or "candidate",
            "published_at": material.get("published_at") or "",
            "themes": sorted(hooks(material)),
            "tickers": material.get("tickers") or [],
            "storyline_fit": default_storyline_fit(material, clusters),
            "block_expandability": score_block_expandability(material),
            "bridge_to_fixed_charts": score_bridge_to_fixed_charts(material),
            "bridge_to_tickers": score_bridge_to_tickers(material),
            "broadcast_hook": score_broadcast_hook(material),
            "explanation_cost": score_explanation_cost(material),
            "visual_local_path": material.get("visual_local_path") or "",
            "summary": compact_text(material.get("summary"), 420),
        }
        row["heuristic_total"] = heuristic_total(row)
        if material_id in selected:
            selected_item = selected[material_id]
            row["selection_status"] = "selected"
            row["storyline_fit"] = selected_storylines.get(material_id) or selected_item.get("storyline_fit") or row["storyline_fit"]
            row["selection_reason"] = selected_item.get("selection_reason") or "모델 선별 항목"
            row["why_not_selected"] = ""
        elif row["heuristic_total"] >= 10 or row["block_expandability"] >= 4:
            row["selection_status"] = "reserve"
            row["selection_reason"] = "선별되지는 않았지만 고정 차트/티커/방송 훅 중 일부가 강해 예비 후보로 보관"
            row["why_not_selected"] = "상위 3개 스토리라인 안에 들어가지 못했거나 중복 가능성이 있음"
        else:
            row["selection_status"] = "rejected"
            row["selection_reason"] = ""
            row["why_not_selected"] = "설명 비용 대비 당일 메인 서사 연결성이 약하거나 단독 후보 성격이 강함"
        rows.append(row)
    return sorted(rows, key=lambda item: (item["selection_status"] != "selected", -item["heuristic_total"], item["headline"]))


def render_markdown(target_date: str, freeze_time: str, ledger: list[dict], selection: dict) -> str:
    selected_rows = [row for row in ledger if row["selection_status"] == "selected"]
    reserve_rows = [row for row in ledger if row["selection_status"] == "reserve"]
    rejected_rows = [row for row in ledger if row["selection_status"] == "rejected"]
    lines = [
        "# Autopark Live Experiment Pack",
        "",
        f"- 대상일: `{target_date}`",
        f"- freeze 시각: `{freeze_time}`",
        f"- 후보 수: `{len(ledger)}`",
        f"- selected/reserve/rejected: `{len(selected_rows)}/{len(reserve_rows)}/{len(rejected_rows)}`",
        "",
        "## 추천 스토리라인",
        "",
    ]
    for index, storyline in enumerate(selection.get("storylines") or [], start=1):
        lines.extend(
            [
                f"### {index}. {normalize(storyline.get('title'))}",
                "",
                f"> {normalize(storyline.get('one_liner'))}",
                "",
                f"- 선정 이유: {normalize(storyline.get('why_selected'))}",
                f"- 연결 자료: {', '.join(f'`{item_id}`' for item_id in storyline.get('selected_item_ids') or []) or '-'}",
                "",
            ]
        )
        for step in storyline.get("slide_flow") or []:
            lines.append(f"- {step}")
        lines.append("")
    if not selection.get("storylines"):
        lines.extend(["- 아직 storyline-selection-v4.json이 없어 후보 장부만 생성됨.", ""])

    lines.extend(["## 후보 장부", ""])
    for status, rows in [("selected", selected_rows), ("reserve", reserve_rows), ("rejected", rejected_rows[:20])]:
        lines.extend([f"### {status}", ""])
        if not rows:
            lines.extend(["- 없음", ""])
            continue
        for row in rows:
            title = row["headline"]
            source = row["source"] or row["type"]
            url = row["url"]
            source_text = f"[{source}]({url})" if url.startswith("http") else source
            lines.extend(
                [
                    f"#### {title}",
                    "",
                    f"- ID: `{row['id']}`",
                    f"- 출처: {source_text}",
                    f"- 상태: `{row['selection_status']}` / 점수: `{row['heuristic_total']}`",
                    f"- 연결성: 시장 `{row['bridge_to_fixed_charts']}`, 티커 `{row['bridge_to_tickers']}`, 블록 `{row['block_expandability']}`, 방송 훅 `{row['broadcast_hook']}`, 설명 비용 `{row['explanation_cost']}`",
                    f"- 스토리 적합: {row['storyline_fit']}",
                    f"- 선정/보류 이유: {row['selection_reason'] or row['why_not_selected']}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--limit-news", type=int, default=80)
    parser.add_argument("--limit-x", type=int, default=60)
    parser.add_argument("--limit-visuals", type=int, default=40)
    parser.add_argument("--selection", type=Path)
    args = parser.parse_args()

    materials = gather_materials(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    clusters = build_clusters(materials, representatives_per_cluster=8)
    selection_path = args.selection or (PROCESSED_DIR / args.date / "storyline-selection-v4.json")
    selection = load_selection(selection_path) if selection_path.exists() else {}
    freeze_time = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    ledger = build_ledger(materials, clusters, selection)

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "freeze_time": freeze_time,
        "material_count": len(materials),
        "selection_source": str(selection_path),
        "selection_available": bool(selection),
        "ledger": ledger,
    }
    (processed_dir / "live-experiment-pack.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (notion_dir / "live-experiment-pack.md").write_text(
        render_markdown(args.date, freeze_time, ledger, selection),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "target_date": args.date,
                "material_count": len(materials),
                "selection_available": bool(selection),
                "output": str(processed_dir / "live-experiment-pack.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
