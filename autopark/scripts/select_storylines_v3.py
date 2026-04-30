#!/usr/bin/env python3
"""Draft storylines from clustered today-misc materials."""

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


DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


SELECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dashboard_summary_bullets": {"type": "array", "minItems": 4, "maxItems": 6, "items": {"type": "string"}},
        "selected_items": {
            "type": "array",
            "minItems": 6,
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "type": {"type": "string"},
                    "selection_reason": {"type": "string"},
                    "storyline_fit": {"type": "string"},
                    "verification_note": {"type": "string"},
                    "visual_local_path": {"type": "string"},
                },
                "required": [
                    "id",
                    "title",
                    "source",
                    "url",
                    "type",
                    "selection_reason",
                    "storyline_fit",
                    "verification_note",
                    "visual_local_path",
                ],
            },
        },
        "storylines": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "one_liner": {"type": "string"},
                    "why_selected": {"type": "string"},
                    "cluster_ids": {"type": "array", "items": {"type": "string"}},
                    "selected_item_ids": {"type": "array", "minItems": 2, "items": {"type": "string"}},
                    "slide_flow": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"type": "string"}},
                    "opening_script_draft": {"type": "string"},
                    "verification_notes": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "one_liner",
                    "why_selected",
                    "cluster_ids",
                    "selected_item_ids",
                    "slide_flow",
                    "opening_script_draft",
                    "verification_notes",
                ],
            },
        },
        "deferred_patterns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["dashboard_summary_bullets", "selected_items", "storylines", "deferred_patterns"],
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compact_cluster(cluster: dict, representatives: int) -> dict:
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
                "summary": compact_text(item.get("summary"), 420),
                "visual_local_path": item.get("visual_local_path") or "",
            }
            for item in (cluster.get("representative_items") or [])[:representatives]
        ],
    }


def build_prompt(clusters: list[dict], sample_outline: str, selected_count: int) -> str:
    return f"""You are designing a Korean morning-market-broadcast dashboard from clustered source materials.

Important context:
- This is a pre-PPT preparation dashboard. Do not write as if the PPT already exists.
- The previous item-by-item approach missed cross-source combinations. You now see clusters first.
- Return exactly 3 storylines, not 4 or 5. This dashboard has room for three recommended storylines.
- The 3 storylines are alternative broadcast segment ideas, not a three-act essay about one main issue.
- Each storyline must stand alone as "이 꼭지로 풀어갈 수 있습니다"; avoid #2/#3 depending on #1.
- Prefer slot diversity across earnings/tickers, market tone, macro/policy/geopolitics, and side-dish materials when the source set allows it.
- Select {selected_count} material cards total, but storylines should be based on clusters and cross-cluster connections.
- Every selected_item must be copied from a representative item ID shown below. Do not invent IDs or URLs.
- Every storyline.selected_item_ids must refer only to selected_items[].id.
- Use Korean for storylines, reasons, and dashboard summary.
- Prefer a broadcastable angle over mechanical summary: "why this matters this morning", "what chart/article can show it", and "what the host can say".
- Visual cards are useful, but do not overclaim exact values unless the source text says them. Put uncertainty in verification_notes.
- Match the 04.21 sample structure: 주요 뉴스 요약, 추천 스토리라인 3개, quote one-liner, 선정 이유, 슬라이드 구성.
- slide_flow must be Korean slide/segment descriptions, not raw IDs. Example: "시장 심리 회복 차트로 현재 리스크 선호를 먼저 보여준다".
- It is okay for one storyline to combine two clusters if that creates a better broadcast arc.
- Be careful with directionality. If a source says dollar is elevated against yen, do not summarize it as yen strength.

04.21 sample outline:
{sample_outline or "- not available -"}

Clustered materials:
{json.dumps(clusters, ensure_ascii=False, indent=2)}
"""


def call_openai(prompt: str, token: str, model: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_clustered_storyline_selection",
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
    parts = []
    for item in raw.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    text = "".join(parts).strip()
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return {"raw_response_id": raw.get("id"), "selection": json.loads(text)}


def repair_selection(selection: dict, materials: list[dict]) -> dict:
    material_lookup = {item.get("id"): item for item in materials}
    fixed_items = []
    seen = set()

    def material_to_selected(original: dict, reason: str) -> dict:
        title = original.get("title") or original.get("id") or ""
        summary = compact_text(original.get("summary"), 240)
        return {
            "id": original.get("id") or "",
            "title": title,
            "source": original.get("source") or "",
            "url": original.get("url") or "",
            "type": original.get("type") or "",
            "selection_reason": reason,
            "storyline_fit": summary or reason,
            "verification_note": "자동 보강: 스토리라인이 참조한 대표 재료이므로 원문/수치 확인 필요.",
            "visual_local_path": original.get("visual_local_path") or "",
        }

    for item in selection.get("selected_items", []):
        material_id = item.get("id")
        original = material_lookup.get(material_id)
        if not original or material_id in seen:
            continue
        seen.add(material_id)
        item["title"] = item.get("title") or original.get("title") or material_id
        item["source"] = original.get("source") or item.get("source") or ""
        item["url"] = original.get("url") or item.get("url") or ""
        item["type"] = original.get("type") or item.get("type") or ""
        item["visual_local_path"] = original.get("visual_local_path") or ""
        fixed_items.append(item)

    for storyline in selection.get("storylines", []):
        for material_id in storyline.get("selected_item_ids", []):
            if material_id in seen or material_id not in material_lookup or len(fixed_items) >= 8:
                continue
            original = material_lookup[material_id]
            fixed_items.append(material_to_selected(original, "자동 보강: 스토리라인 연결 자료로 참조됨."))
            seen.add(material_id)
    selection["selected_items"] = fixed_items

    selected_ids = {item.get("id") for item in fixed_items}
    for storyline in selection.get("storylines", []):
        ids = [item_id for item_id in storyline.get("selected_item_ids", []) if item_id in selected_ids]
        dropped = [item_id for item_id in storyline.get("selected_item_ids", []) if item_id not in selected_ids]
        storyline["selected_item_ids"] = ids
        if dropped:
            storyline.setdefault("verification_notes", []).append(
                f"자동 후처리: 선별 카드 밖 참조 제거 ({', '.join(dropped)})"
            )
    return selection


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url.startswith("http") else label


def clean_title(value: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", value or "").strip()


def render_markdown(target_date: str, selection: dict, clusters: list[dict]) -> str:
    selected = {item["id"]: item for item in selection.get("selected_items", [])}
    cluster_lookup = {cluster["cluster_id"]: cluster for cluster in clusters}
    lines = [
        "# 오늘의 이모저모 선별 및 스토리라인 v3",
        "",
        f"수집 기준일: `{target_date}`",
        "",
        "> 후보를 먼저 클러스터링하고, 모델은 묶음 간 연결과 방송용 각도 설계에 집중합니다.",
        "",
        "## 주요 뉴스 요약",
        "",
    ]
    for item in selection.get("dashboard_summary_bullets", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 추천 스토리라인", ""])
    for index, storyline in enumerate(selection.get("storylines", []), start=1):
        lines.extend(
            [
                f"### {index}. {clean_title(storyline.get('title', ''))}",
                "",
                f"> {storyline.get('one_liner', '')}",
                "",
                "#### 선정 이유",
                "",
                f"- {storyline.get('why_selected', '')}",
                "",
                "#### 참조 클러스터",
                "",
            ]
        )
        for cluster_id in storyline.get("cluster_ids", []):
            cluster = cluster_lookup.get(cluster_id)
            if cluster:
                lines.append(f"- `{cluster_id}` {cluster.get('label')} ({cluster.get('item_count')}개 후보)")
            else:
                lines.append(f"- `{cluster_id}`")
        lines.extend(["", "#### 슬라이드 구성", ""])
        for flow in storyline.get("slide_flow", []):
            lines.append(f"- {flow}")
        lines.extend(["", "#### 연결 자료", ""])
        for material_id in storyline.get("selected_item_ids", []):
            material = selected.get(material_id)
            if material:
                lines.append(f"- `{material_id}` {link(material.get('title', material_id), material.get('url', ''))}")
            else:
                lines.append(f"- `{material_id}`")
        lines.extend(["", "#### 30초 오프닝 가안", "", storyline.get("opening_script_draft", ""), "", "#### 확인 필요", ""])
        for note in storyline.get("verification_notes", []):
            lines.append(f"- {note}")
        lines.append("")

    lines.extend(["## 채택 재료 카드", ""])
    for item in selection.get("selected_items", []):
        lines.extend(
            [
                f"### {item.get('title')}",
                "",
                f"- ID: `{item.get('id')}`",
                f"- 유형: `{item.get('type')}`",
                f"- 출처: {link(item.get('source', '-'), item.get('url', ''))}",
                f"- 선정 이유: {item.get('selection_reason')}",
                f"- 스토리 연결: {item.get('storyline_fit')}",
                f"- 확인 필요: {item.get('verification_note')}",
            ]
        )
        if item.get("visual_local_path"):
            lines.extend(["", f"![{item.get('title')}]({item.get('visual_local_path')})"])
        lines.append("")

    lines.extend(["## 보류 패턴", ""])
    for item in selection.get("deferred_patterns", []):
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=os.environ.get("AUTOPARK_SELECTOR_MODEL", DEFAULT_MODEL))
    parser.add_argument("--clusters", type=Path)
    parser.add_argument("--sample-outline", type=Path)
    parser.add_argument("--selected-count", type=int, default=8)
    parser.add_argument("--representatives-per-cluster", type=int, default=8)
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
    compact_clusters = [
        compact_cluster(cluster, args.representatives_per_cluster)
        for cluster in cluster_payload.get("clusters", [])
    ]
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
        "cluster_count": len(compact_clusters),
        "clusters": compact_clusters,
        "materials": materials,
        **result,
    }
    (processed_dir / "storyline-selection-v3.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (notion_dir / "storyline-selection-v3.md").write_text(
        render_markdown(args.date, result["selection"], compact_clusters),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "status": result.get("status", "published"), "model": args.model}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
