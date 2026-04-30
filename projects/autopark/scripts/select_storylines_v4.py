#!/usr/bin/env python3
"""Select broadcast storylines from pre-ranked cluster representatives."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from caption_visual_assets import PROJECT_ROOT, REPO_ROOT, load_env
from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials, sample_outline_text
from select_storylines_v3 import (
    DEFAULT_ENV,
    DEFAULT_MODEL,
    OPENAI_API,
    SELECTION_SCHEMA,
    load_json,
    repair_selection,
    render_markdown,
)


SOURCE_WEIGHTS = {
    "visual_card": 5,
    "x_social": 4,
    "news": 3,
}

KEY_HOOKS = {
    "s&p",
    "nasdaq",
    "oil",
    "dollar",
    "yen",
    "rate",
    "inflation",
    "ai",
    "semiconductor",
    "earnings",
    "guidance",
    "bitcoin",
}


def material_priority(material: dict) -> tuple[int, int, int, str]:
    visual = 1 if material.get("visual_local_path") else 0
    type_weight = SOURCE_WEIGHTS.get(material.get("type"), 1)
    hooks = {str(hook).lower() for hook in material.get("market_hooks") or []}
    hook_score = len(hooks & KEY_HOOKS)
    return (visual, type_weight, hook_score, material.get("title") or "")


def shortlist_clusters(clusters: list[dict], per_cluster: int, max_total: int) -> list[dict]:
    rows = []
    total = 0
    for cluster in sorted(clusters, key=lambda item: item.get("item_count", 0), reverse=True):
        reps = cluster.get("representative_items") or []
        ranked = sorted(reps, key=material_priority, reverse=True)[:per_cluster]
        if not ranked:
            continue
        if total >= max_total:
            break
        ranked = ranked[: max(0, max_total - total)]
        total += len(ranked)
        rows.append({**cluster, "representative_items": ranked})
    return rows


def compact_cluster(cluster: dict) -> dict:
    return {
        "cluster_id": cluster.get("cluster_id"),
        "label": cluster.get("label"),
        "item_count": cluster.get("item_count"),
        "sources": cluster.get("sources") or [],
        "market_hooks": cluster.get("market_hooks") or [],
        "keywords": cluster.get("keywords") or [],
        "representative_items": [
            {
                "id": item.get("id"),
                "type": item.get("type"),
                "source": item.get("source"),
                "title": item.get("title"),
                "url": item.get("url"),
                "published_at": item.get("published_at"),
                "summary": compact_text(item.get("summary"), 320),
                "visual_local_path": item.get("visual_local_path") or "",
            }
            for item in cluster.get("representative_items", [])
        ],
    }


def build_prompt(clusters: list[dict], sample_outline: str, selected_count: int) -> str:
    return f"""You are selecting material for a Korean morning-market-broadcast dashboard.

Task:
- Return exactly 3 storylines.
- Select {selected_count} material cards total.
- This is a pre-PPT preparation dashboard. Do not write as if slides already exist.
- Use short, broadcastable Korean. Avoid long source-title style phrasing.
- The 3 storylines must be independent broadcast segment candidates, not a three-act expansion of one issue.
- Each storyline should be detachable: the host can pick only #1, only #2, or only #3 and still have a complete segment.
- Prefer diversity across slots: e.g. one earnings/ticker idea, one market/positioning idea, one policy/geopolitics/side-dish idea when materials support it.
- Do not let one macro theme consume all 3 slots unless every other cluster is clearly weak.
- Every selected_item must be copied from a representative item ID shown below.
- Every storyline.selected_item_ids must refer only to selected_items[].id.
- Choose materials that can be combined into a clear morning narrative, not just individually important links.
- Prefer visual cards and X posts when the visual explains the story, but include news when it anchors the claim.
- If a chart is hard to interpret, write a conservative verification_note.
- Avoid duplicates. If two materials say the same thing, keep the one with the better visual or cleaner source.

Sample 04.21 outline:
{sample_outline or "- not available -"}

Shortlisted cluster representatives:
{json.dumps(clusters, ensure_ascii=False, indent=2)}
"""


def call_openai(prompt: str, token: str, model: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_storyline_selection_v4",
                "strict": True,
                "schema": SELECTION_SCHEMA,
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
    text = "".join(
        content.get("text", "")
        for item in raw.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    ).strip()
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return {"raw_response_id": raw.get("id"), "selection": json.loads(text)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=os.environ.get("AUTOPARK_SELECTOR_MODEL", DEFAULT_MODEL))
    parser.add_argument("--clusters", type=Path)
    parser.add_argument("--sample-outline", type=Path)
    parser.add_argument("--selected-count", type=int, default=8)
    parser.add_argument("--per-cluster", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=22)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    token = env.get("OPENAI_API_KEY")
    if not token and not args.dry_run:
        raise SystemExit("Missing OPENAI_API_KEY in environment or .env")

    cluster_path = args.clusters or (PROCESSED_DIR / args.date / "today-misc-clusters.json")
    cluster_payload = load_json(cluster_path.resolve())
    materials = cluster_payload.get("materials") or gather_materials(args.date, 40, 30, 24)
    shortlisted = shortlist_clusters(cluster_payload.get("clusters", []), args.per_cluster, args.max_candidates)
    compact_clusters = [compact_cluster(cluster) for cluster in shortlisted]

    if args.dry_run:
        result = {
            "status": "dry-run",
            "selection": {
                "dashboard_summary_bullets": [],
                "selected_items": [],
                "storylines": [],
                "deferred_patterns": [],
            },
        }
    else:
        result = call_openai(
            build_prompt(compact_clusters, sample_outline_text(args.sample_outline), args.selected_count),
            token,
            args.model,
            args.timeout,
        )
        result["selection"] = repair_selection(result["selection"], materials)

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "model": args.model,
        "material_count": len(materials),
        "shortlisted_count": sum(len(cluster.get("representative_items") or []) for cluster in compact_clusters),
        "cluster_count": len(compact_clusters),
        "clusters": compact_clusters,
        "materials": materials,
        **result,
    }
    (processed_dir / "storyline-selection-v4.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (notion_dir / "storyline-selection-v4.md").write_text(
        render_markdown(args.date, result["selection"], compact_clusters),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "status": result.get("status", "published"),
                "model": args.model,
                "shortlisted_count": payload["shortlisted_count"],
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
