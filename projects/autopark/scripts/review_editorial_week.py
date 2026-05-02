#!/usr/bin/env python3
"""Review one week of Autopark editorial briefs and source usefulness."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DEFAULT_WEEKLY_DIR = RUNTIME_DIR / "weekly"

THEME_PATTERNS = {
    "AI/반도체": [r"\bai\b", r"인공지능", r"반도체", r"칩", r"데이터센터", r"capex", r"클라우드", r"nvidia", r"openai"],
    "유가/에너지": [r"유가", r"원유", r"wti", r"브렌트", r"opec", r"에너지", r"정유"],
    "실적/특징주": [r"실적", r"어닝", r"eps", r"매출", r"가이던스", r"특징주"],
    "금리/Fed": [r"fed", r"fomc", r"금리", r"인하", r"파월", r"fedwatch", r"채권"],
    "달러/환율": [r"달러", r"환율", r"원화", r"엔화", r"dxy", r"usd"],
    "정책/관세": [r"관세", r"백악관", r"트럼프", r"정책", r"규제", r"중국"],
    "크립토": [r"비트코인", r"bitcoin", r"crypto", r"암호화폐"],
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def week_days(end_date: str, days: int) -> list[str]:
    end = parse_day(end_date)
    return [(end - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]


def compact(value: object, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def table_cell(value: object) -> str:
    return compact(value, 500).replace("|", "\\|").replace("\n", "<br>")


def source_of(item: dict) -> str:
    return compact(item.get("source") or item.get("type") or item.get("publisher") or "unknown", 80)


def title_of(item: dict) -> str:
    return compact(item.get("title") or item.get("headline") or item.get("summary") or item.get("id"), 140)


def evidence_ids(brief: dict) -> set[str]:
    ids = set()
    for story in brief.get("storylines") or []:
        for evidence in story.get("evidence_to_use") or []:
            if evidence.get("item_id"):
                ids.add(str(evidence["item_id"]))
    return ids


def broadcast_feedback_for(day: str) -> list[dict]:
    folder = RUNTIME_DIR / "broadcast" / day
    if not folder.exists():
        return []
    rows = []
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        text = compact(path.read_text(encoding="utf-8", errors="replace"), 600)
        if text:
            rows.append({"file": path.name, "text": text})
    return rows


def theme_hits(text: str) -> list[str]:
    hits = []
    for theme, patterns in THEME_PATTERNS.items():
        if any(re.search(pattern, text, flags=re.I) for pattern in patterns):
            hits.append(theme)
    return hits or ["기타"]


def collect_week(end_date: str, days: int) -> list[dict]:
    rows = []
    for day in week_days(end_date, days):
        processed = PROCESSED_DIR / day
        brief = load_json(processed / "editorial-brief.json")
        radar = load_json(processed / "market-radar.json")
        quality = load_json(RUNTIME_DIR / "reviews" / day / "dashboard-quality.json")
        rows.append(
            {
                "date": day,
                "brief": brief,
                "radar": radar,
                "quality": quality,
                "broadcast_feedback": broadcast_feedback_for(day),
            }
        )
    return rows


def render_source_value_report(rows: list[dict]) -> str:
    collected = Counter()
    used = Counter()
    useful_titles: dict[str, list[str]] = defaultdict(list)
    dropped_sources = Counter()

    for row in rows:
        candidates = row["radar"].get("candidates") or []
        candidate_by_id = {str(item.get("id")): item for item in candidates if item.get("id")}
        for item in candidates:
            collected[source_of(item)] += 1
        for item_id in evidence_ids(row["brief"]):
            item = candidate_by_id.get(item_id)
            if not item:
                continue
            source = source_of(item)
            used[source] += 1
            if len(useful_titles[source]) < 4:
                useful_titles[source].append(title_of(item))
        for story in row["brief"].get("storylines") or []:
            for evidence in story.get("evidence_to_drop") or []:
                item = candidate_by_id.get(str(evidence.get("item_id")))
                if item:
                    dropped_sources[source_of(item)] += 1

    lines = [
        "# Source Value Report",
        "",
        "최근 브리프에서 수집 소스가 실제 추천 스토리라인 근거로 얼마나 쓰였는지 본 리포트입니다.",
        "",
        "| 소스 | 수집 수 | 채택 수 | 채택률 | 버림 표시 | 판단 | 대표 채택 자료 |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    all_sources = sorted(set(collected) | set(used), key=lambda source: (used[source], collected[source]), reverse=True)
    for source in all_sources:
        total = collected[source]
        picked = used[source]
        rate = picked / total if total else 0
        if picked >= 4 and rate >= 0.18:
            verdict = "높음"
        elif picked >= 2:
            verdict = "보통"
        elif total >= 8 and picked == 0:
            verdict = "낮음"
        else:
            verdict = "관찰"
        examples = "<br>".join(table_cell(title) for title in useful_titles[source]) if useful_titles[source] else "-"
        lines.append(f"| {table_cell(source)} | {total} | {picked} | {rate:.0%} | {dropped_sources[source]} | {verdict} | {examples} |")
    if len(lines) == 6:
        lines.append("| - | 0 | 0 | 0% | 0 | 데이터 없음 | - |")
    return "\n".join(lines)


def render_storyline_repeat_report(rows: list[dict]) -> str:
    theme_counts = Counter()
    title_rows = []
    for row in rows:
        for story in row["brief"].get("storylines") or []:
            title = compact(story.get("title"), 120)
            text = " ".join([title, compact(story.get("hook"), 180), compact(story.get("core_argument"), 180)])
            hits = theme_hits(text)
            for theme in hits:
                theme_counts[theme] += 1
            title_rows.append((row["date"], title, ", ".join(hits), int(story.get("recommendation_stars") or 0)))

    lines = [
        "# Storyline Repeat Report",
        "",
        "같은 프레임이 얼마나 반복되는지 보는 리포트입니다. 반복 자체가 나쁜 것은 아니지만, 매일 같은 제목과 논리로 보이면 프롬프트나 소스 가중치를 조정해야 합니다.",
        "",
        "## Theme Counts",
        "",
        "| 테마 | 횟수 | 코멘트 |",
        "|---|---:|---|",
    ]
    for theme, count in theme_counts.most_common():
        comment = "반복 주의" if count >= 4 else "정상 범위"
        lines.append(f"| {table_cell(theme)} | {count} | {comment} |")
    if not theme_counts:
        lines.append("| - | 0 | 데이터 없음 |")

    lines.extend(["", "## Daily Titles", "", "| 날짜 | 추천도 | 테마 | 제목 |", "|---|---:|---|---|"])
    for day, title, themes, stars in title_rows:
        lines.append(f"| {day} | {stars} | {table_cell(themes)} | {table_cell(title or '-')} |")
    if not title_rows:
        lines.append("| - | 0 | - | 데이터 없음 |")
    return "\n".join(lines)


def render_prompt_improvement_notes(rows: list[dict]) -> str:
    theme_counts = Counter()
    low_quality_days = []
    feedback_lines = []
    missing_evidence = 0
    total_stories = 0

    for row in rows:
        quality = row["quality"] or {}
        if quality.get("gate") == "needs_revision":
            low_quality_days.append(row["date"])
        for story in row["brief"].get("storylines") or []:
            total_stories += 1
            text = " ".join([compact(story.get("title")), compact(story.get("hook")), compact(story.get("core_argument"))])
            for theme in theme_hits(text):
                theme_counts[theme] += 1
            if not story.get("evidence_to_use"):
                missing_evidence += 1
        for feedback in row["broadcast_feedback"]:
            feedback_lines.append(f"- {row['date']} `{feedback['file']}`: {feedback['text']}")

    repeated = [theme for theme, count in theme_counts.items() if count >= 4]
    lines = [
        "# Prompt Improvement Notes",
        "",
        "## 다음 주 프롬프트 조정 제안",
        "",
    ]
    if repeated:
        lines.append(f"- 반복 테마가 강합니다: {', '.join(repeated)}. 같은 테마라도 `가격 반응`, `실적 검증`, `정책 리스크`, `반론` 중 다른 축으로 재구성하게 프롬프트를 조정하세요.")
    else:
        lines.append("- 테마 반복은 과도하지 않습니다. 현재처럼 3~5개 강선별 정책을 유지해도 됩니다.")
    if missing_evidence:
        lines.append(f"- 근거 없는 주장 {missing_evidence}/{total_stories or 1}개가 감지됐습니다. `evidence_to_use`가 없으면 스토리라인을 버리도록 더 강하게 지시하세요.")
    if low_quality_days:
        lines.append(f"- 품질 게이트 미통과 날짜가 있습니다: {', '.join(low_quality_days)}. 해당 날짜의 리뷰 JSON과 노션 본문을 프롬프트 회고 자료로 넣으세요.")
    if feedback_lines:
        lines.extend(["", "## 사후 방송 자료에서 읽은 피드백", ""])
        lines.extend(feedback_lines[:20])
        lines.extend(
            [
                "",
                "## 운영 메모",
                "",
                "- 사후 PPT/스크립트는 새로운 시장 사실로 쓰지 말고, 실제로 채택된 표현과 버려진 자료 유형을 학습하는 피드백으로만 사용하세요.",
                "- 다음 편집 브리프에는 최근 7일 방송 자료의 공통 선호를 반영하되, 하루 이슈 판단은 당일 수집 후보 안에서만 하도록 유지하세요.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## 사후 방송 자료",
                "",
                "- 아직 `runtime/broadcast/{date}/` 아래에 `.md` 또는 `.txt` 피드백 파일이 없습니다. 실제 PPT 노트나 스크립트를 넣으면 다음 리뷰부터 반영됩니다.",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end-date", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_WEEKLY_DIR)
    args = parser.parse_args()

    end = parse_day(args.end_date)
    iso = end.isocalendar()
    output_dir = args.output_dir / f"{iso.year}-W{iso.week:02d}"
    rows = collect_week(args.end_date, max(1, args.days))

    source_path = output_dir / "source-value-report.md"
    repeat_path = output_dir / "storyline-repeat-report.md"
    prompt_path = output_dir / "prompt-improvement-notes.md"
    write_text(source_path, render_source_value_report(rows))
    write_text(repeat_path, render_storyline_repeat_report(rows))
    write_text(prompt_path, render_prompt_improvement_notes(rows))

    print(
        json.dumps(
            {
                "ok": True,
                "end_date": args.end_date,
                "days": args.days,
                "output_dir": str(output_dir),
                "reports": [str(source_path), str(repeat_path), str(prompt_path)],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
