#!/usr/bin/env python3
"""Compare Autopark recommendations with actual PPT slides and transcript topics."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

STOPWORDS = {
    "오늘",
    "시장",
    "자료",
    "확인",
    "그리고",
    "하지만",
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
}


def clean(value: object, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_notion_path(target_date: str) -> Path:
    title = datetime.fromisoformat(target_date).strftime("%y.%m.%d")
    return RUNTIME_DIR / "notion" / target_date / f"{title}.md"


def token_set(text: str) -> set[str]:
    raw = re.findall(r"[A-Za-z0-9$]{2,}|[가-힣]{2,}", clean(text).lower())
    return {token for token in raw if token not in STOPWORDS and not token.isdigit()}


def overlap_score(left: str, right: str) -> float:
    a = token_set(left)
    b = token_set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / max(4, min(len(a), len(b)))


def best_matches(query: str, rows: list[dict], text_keys: list[str], limit: int = 3) -> list[dict]:
    matches = []
    for row in rows:
        haystack = " ".join(str(row.get(key) or "") for key in text_keys)
        score = overlap_score(query, haystack)
        if score <= 0:
            continue
        matches.append({"score": round(score, 3), **row})
    return sorted(matches, key=lambda item: (-item["score"], item.get("slide_number") or item.get("seconds") or 0))[:limit]


def storyline_text(story: dict) -> str:
    parts = [
        story.get("title"),
        story.get("hook"),
        story.get("why_now"),
        story.get("core_argument"),
        story.get("talk_track"),
        " ".join(item.get("title") or "" for item in story.get("evidence_to_use") or []),
        " ".join(item.get("caption") or "" for item in story.get("ppt_asset_queue") or []),
    ]
    return clean(" ".join(str(part or "") for part in parts))


def evidence_rows(story: dict) -> list[dict]:
    rows = []
    for evidence in story.get("evidence_to_use") or []:
        rows.append(
            {
                "item_id": evidence.get("item_id") or evidence.get("evidence_id") or "",
                "evidence_id": evidence.get("evidence_id") or evidence.get("item_id") or "",
                "storyline_id": story.get("storyline_id") or "",
                "title": evidence.get("title") or "",
                "source_role": evidence.get("source_role") or "",
                "evidence_role": evidence.get("evidence_role") or "",
                "kind": "evidence",
            }
        )
    for asset in story.get("ppt_asset_queue") or []:
        rows.append(
            {
                "item_id": asset.get("asset_id") or "",
                "evidence_id": asset.get("asset_id") or "",
                "storyline_id": story.get("storyline_id") or "",
                "title": asset.get("caption") or "",
                "source_role": asset.get("source_role") or "",
                "evidence_role": asset.get("visual_asset_role") or "visual",
                "kind": "ppt_asset",
            }
        )
    return rows


def classify_story_usage(story: dict, slide_matches: list[dict], segment_matches: list[dict]) -> list[str]:
    labels = []
    first_slide = min((int(item.get("slide_number") or 999) for item in slide_matches), default=999)
    first_segment = min((int(item.get("seconds") or 999999) for item in segment_matches), default=999999)
    if first_slide <= 8 or first_segment <= 360:
        labels.append("used_as_lead" if int(story.get("rank") or 0) == 1 else "used_later")
    elif slide_matches or segment_matches:
        labels.append("used_later")
    if slide_matches:
        labels.append("used_as_slide")
    if segment_matches and not slide_matches:
        labels.append("used_as_talk_only")
    if segment_matches and not slide_matches:
        labels.append("mentioned_only")
    if not labels:
        if not story.get("ppt_asset_queue"):
            labels.append("not_used_low_visual_value")
        elif story.get("signal_or_noise") == "noise":
            labels.append("not_used_weak_market_reaction")
        else:
            labels.append("not_used_already_known")
    if slide_matches or segment_matches:
        labels.append("strong_broadcast_fit" if (slide_matches and segment_matches) else "weak_broadcast_fit")
    return list(dict.fromkeys(labels))


def compare(target_date: str, brief: dict, ppt_outline: dict, broadcast_outline: dict, dashboard_markdown: str) -> dict:
    slides = ppt_outline.get("slides") or []
    segments = broadcast_outline.get("segments") or []
    topics = broadcast_outline.get("topics") or []
    story_results = []
    asset_results = []

    for index, story in enumerate(brief.get("storylines") or [], start=1):
        story = {**story, "rank": story.get("rank") or index}
        text = storyline_text(story)
        slide_matches = [item for item in best_matches(text, slides, ["title", "text"], 5) if item["score"] >= 0.15]
        segment_matches = [item for item in best_matches(text, segments, ["text"], 5) if item["score"] >= 0.12]
        labels = classify_story_usage(story, slide_matches, segment_matches)
        story_results.append(
            {
                "storyline_id": story.get("storyline_id") or f"storyline-{index}",
                "title": story.get("title") or "",
                "rank": story.get("rank") or index,
                "labels": labels,
                "slide_matches": [
                    {
                        "slide_number": item.get("slide_number"),
                        "title": item.get("title"),
                        "score": item.get("score"),
                        "visual_asset_role": item.get("visual_asset_role"),
                    }
                    for item in slide_matches
                ],
                "transcript_matches": [
                    {
                        "timestamp": item.get("timestamp"),
                        "score": item.get("score"),
                        "text": clean(item.get("text"), 180),
                    }
                    for item in segment_matches
                ],
            }
        )
        for evidence in evidence_rows(story):
            evidence_query = clean(f"{evidence.get('title')} {story.get('title')}")
            evidence_slide_matches = [item for item in best_matches(evidence_query, slides, ["title", "text"], 3) if item["score"] >= 0.16]
            evidence_segment_matches = [item for item in best_matches(evidence_query, segments, ["text"], 3) if item["score"] >= 0.13]
            if evidence_slide_matches:
                label = "used_as_slide"
            elif evidence_segment_matches:
                label = "used_as_talk_only" if evidence.get("evidence_role") != "sentiment" else "mentioned_only"
            elif evidence.get("evidence_role") == "sentiment":
                label = "false_positive_sentiment_only"
            elif evidence.get("evidence_role") in {"visual", "market_reaction"}:
                label = "false_positive_visual_only"
            else:
                label = "not_used_already_known"
            asset_results.append(
                {
                    "item_id": evidence.get("item_id") or "",
                    "evidence_id": evidence.get("evidence_id") or "",
                    "storyline_id": evidence.get("storyline_id") or "",
                    "title": evidence.get("title") or "",
                    "label": label,
                    "slide_matches": [
                        {"slide_number": item.get("slide_number"), "title": item.get("title"), "score": item.get("score")}
                        for item in evidence_slide_matches
                    ],
                    "transcript_matches": [
                        {"timestamp": item.get("timestamp"), "score": item.get("score"), "text": clean(item.get("text"), 140)}
                        for item in evidence_segment_matches
                    ],
                }
            )

    dashboard_text = clean(" ".join([dashboard_markdown, json.dumps(brief, ensure_ascii=False)]))
    missed_slides = []
    for slide in slides:
        if int(slide.get("slide_number") or 0) <= 2:
            continue
        score = overlap_score(slide.get("title") or "", dashboard_text)
        if score < 0.08 and slide.get("visual_asset_role") not in {"index_chart", "sector_heatmap", "rates_chart", "oil_chart", "fx_chart", "crypto_chart"}:
            missed_slides.append(
                {
                    "slide_number": slide.get("slide_number"),
                    "title": slide.get("title"),
                    "visual_asset_role": slide.get("visual_asset_role"),
                    "label": "missed_source_gap",
                    "reason": "PPT slide title has weak overlap with dashboard/editorial brief.",
                }
            )
    topic_counter = Counter(tag for segment in segments for tag in segment.get("topic_tags") or [])
    return {
        "ok": True,
        "target_date": target_date,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "storyline_count": len(brief.get("storylines") or []),
            "slide_count": len(slides),
            "transcript_segment_count": len(segments),
            "topic_count": len(topics),
        },
        "storyline_results": story_results,
        "asset_results": asset_results,
        "missed_slides": missed_slides[:20],
        "topic_summary": [{"topic": topic, "mentions": count} for topic, count in topic_counter.most_common()],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        f"# Dashboard to Broadcast Asset Comparison - {payload.get('target_date')}",
        "",
        "## Storylines",
        "",
    ]
    for item in payload.get("storyline_results") or []:
        lines.extend(
            [
                f"### {item.get('rank')}. {item.get('title')}",
                "",
                f"- labels: {', '.join(item.get('labels') or [])}",
            ]
        )
        if item.get("slide_matches"):
            best = item["slide_matches"][0]
            lines.append(f"- best slide: `{best.get('slide_number')}` {best.get('title')} ({best.get('score')})")
        if item.get("transcript_matches"):
            best = item["transcript_matches"][0]
            lines.append(f"- best transcript: `{best.get('timestamp')}` {best.get('text')} ({best.get('score')})")
        lines.append("")
    lines.extend(["## Asset Labels", ""])
    for item in (payload.get("asset_results") or [])[:40]:
        lines.append(f"- `{item.get('label')}` `{item.get('item_id')}` {clean(item.get('title'), 90)}")
    lines.extend(["", "## Missed Slides", ""])
    for item in payload.get("missed_slides") or []:
        lines.append(f"- slide `{item.get('slide_number')}` `{item.get('visual_asset_role')}` {item.get('title')}")
    if not payload.get("missed_slides"):
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--dashboard", type=Path)
    parser.add_argument("--ppt-outline", type=Path)
    parser.add_argument("--broadcast-outline", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brief_path = args.brief or (PROCESSED_DIR / args.date / "editorial-brief.json")
    dashboard_path = args.dashboard or default_notion_path(args.date)
    ppt_path = args.ppt_outline or (RUNTIME_DIR / "broadcast" / args.date / "ppt-outline.json")
    broadcast_path = args.broadcast_outline or (RUNTIME_DIR / "broadcast" / args.date / "actual-broadcast-outline.json")
    brief = load_json(brief_path)
    ppt_outline = load_json(ppt_path)
    broadcast_outline = load_json(broadcast_path)
    dashboard = dashboard_path.read_text(encoding="utf-8", errors="replace") if dashboard_path.exists() else ""
    missing = [
        label
        for label, payload in [
            ("editorial_brief", brief),
            ("ppt_outline", ppt_outline),
            ("broadcast_outline", broadcast_outline),
        ]
        if not payload
    ]
    if missing:
        print_json({"ok": False, "error": "missing_inputs", "missing": missing, "date": args.date})
        return 1
    payload = compare(args.date, brief, ppt_outline, broadcast_outline, dashboard)
    output_dir = args.output_dir or (RUNTIME_DIR / "broadcast" / args.date)
    json_path = output_dir / "broadcast-asset-comparison.json"
    md_path = output_dir / "broadcast-asset-comparison.md"
    if not args.dry_run:
        write_json(json_path, payload)
        write_text(md_path, render_markdown(payload))
    print_json(
        {
            "ok": True,
            "date": args.date,
            "storyline_count": len(payload.get("storyline_results") or []),
            "asset_count": len(payload.get("asset_results") or []),
            "missed_slide_count": len(payload.get("missed_slides") or []),
            "json": str(json_path),
            "markdown": str(md_path),
            "dry_run": args.dry_run,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
