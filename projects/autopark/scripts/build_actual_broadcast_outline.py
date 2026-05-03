#!/usr/bin/env python3
"""Build a transcript topic outline from an RTF/TXT/MD broadcast transcript."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "runtime"

TOPIC_KEYWORDS = {
    "market_map": ["주요 지수", "s&p", "나스닥", "다우", "히트맵", "러셀", "시장 상황"],
    "rates_fed": ["금리", "10년물", "국채", "fomc", "fmc", "연준", "fed", "파월"],
    "oil_energy": ["유가", "wti", "브렌트", "원유", "호르무즈", "이란", "opec", "에너지"],
    "fx_crypto": ["달러", "원달러", "dxy", "비트코인", "bitcoin", "btc"],
    "earnings": ["실적", "eps", "매출", "가이던스", "알파벳", "구글", "퀄컴", "인텔", "amd", "애플", "마이크로소프트", "메타", "아마존"],
    "ai_infra": ["ai", "오픈ai", "openai", "데이터센터", "반도체", "엔비디아", "컴퓨트", "전력"],
    "side_dish": ["머스크", "알트만", "트럼프", "재판", "화성", "책", "굿즈"],
    "risk_positioning": ["차익", "수익", "조정", "리스크", "압박", "포지션", "과열"],
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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_transcript_path(target_date: str) -> Path | None:
    mmdd = datetime.fromisoformat(target_date).strftime("%m%d")
    for pattern in [f"*{mmdd}*.rtf", f"*{mmdd}*.txt", f"*{mmdd}*.md"]:
        matches = sorted(PROJECT_ROOT.glob(pattern))
        if matches:
            return matches[0]
    host = RUNTIME_DIR / "broadcast" / target_date / "host-segment.md"
    return host if host.exists() else None


def decode_text(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() == ".rtf":
        return rtf_to_text(data)
    for encoding in ["utf-8", "cp949"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def rtf_to_text(data: bytes) -> str:
    source = data.decode("cp949", errors="replace")

    def unicode_repl(match: re.Match[str]) -> str:
        value = int(match.group(1))
        if value < 0:
            value += 65536
        try:
            return chr(value)
        except ValueError:
            return ""

    text = re.sub(r"\\uc\d+ ?", "", source)
    text = re.sub(r"\\u(-?\d+) ?", unicode_repl, text)
    text = re.sub(r"\\par[d]?\b|\\line\b", "\n", text)
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = text.replace("\\{", "{").replace("\\}", "}").replace("\\\\", "\\")
    text = text.replace("\\", "\n")
    text = text.replace("{", " ").replace("}", " ")
    rows = []
    for line in text.splitlines():
        line = clean(line)
        if not line:
            continue
        lowered = line.lower()
        if lowered.endswith(";") or lowered.startswith("*") or "fonttbl" in lowered or "colortbl" in lowered:
            continue
        if re.fullmatch(r"[;* ]+", line):
            continue
        rows.append(line)
    return "\n".join(rows)


def timestamp_seconds(value: str) -> int:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def segment_transcript(text: str) -> list[dict]:
    segments: list[dict] = []
    current_time = ""
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_parts
        body = clean(" ".join(current_parts), 900)
        if current_time and body:
            segments.append(
                {
                    "timestamp": current_time,
                    "seconds": timestamp_seconds(current_time),
                    "text": body,
                    "topic_tags": topic_tags(body),
                }
            )
        current_parts = []

    for line in text.splitlines():
        line = clean(line)
        if not line:
            continue
        if re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", line):
            flush()
            current_time = line
            continue
        if re.fullmatch(r"\d+분(?: \d+초)?|\d+초", line):
            continue
        if line.startswith("챕터 "):
            flush()
            current_time = current_time or "0:00"
        current_parts.append(line)
    flush()
    return segments


def topic_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            tags.append(topic)
    return tags


def build_topics(segments: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for segment in segments:
        for tag in segment.get("topic_tags") or ["uncategorized"]:
            grouped[tag].append(segment)
    topics = []
    for tag, rows in grouped.items():
        if tag == "uncategorized" and len(rows) < 3:
            continue
        counter = Counter()
        for row in rows:
            lowered = row["text"].lower()
            for keyword in TOPIC_KEYWORDS.get(tag, []):
                if keyword.lower() in lowered:
                    counter[keyword] += 1
        topics.append(
            {
                "topic_id": tag,
                "label": tag.replace("_", " "),
                "first_timestamp": min(rows, key=lambda item: item.get("seconds", 0)).get("timestamp"),
                "mention_count": len(rows),
                "keywords": [item for item, _ in counter.most_common(8)],
                "representative_texts": [row["text"] for row in rows[:4]],
            }
        )
    return sorted(topics, key=lambda item: (-item["mention_count"], item["first_timestamp"] or ""))


def build_outline(path: Path, target_date: str) -> dict:
    text = decode_text(path)
    segments = segment_transcript(text)
    return {
        "ok": True,
        "target_date": target_date,
        "source_path": str(path),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "segment_count": len(segments),
        "topics": build_topics(segments),
        "segments": segments,
        "plain_text_excerpt": clean(text, 5000),
    }


def render_markdown(payload: dict) -> str:
    lines = [
        f"# Actual Broadcast Outline - {payload.get('target_date')}",
        "",
        f"- source: `{payload.get('source_path')}`",
        f"- segment_count: `{payload.get('segment_count')}`",
        "",
        "## Topics",
        "",
    ]
    for topic in payload.get("topics") or []:
        lines.extend(
            [
                f"### {topic.get('label')}",
                "",
                f"- first: `{topic.get('first_timestamp')}`",
                f"- mentions: `{topic.get('mention_count')}`",
                f"- keywords: {', '.join(topic.get('keywords') or []) or '-'}",
            ]
        )
        for text in (topic.get("representative_texts") or [])[:2]:
            lines.append(f"- {clean(text, 180)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    transcript = args.transcript or default_transcript_path(args.date)
    if not transcript or not transcript.exists():
        print_json({"ok": False, "error": "missing_transcript", "date": args.date})
        return 1
    output_dir = args.output_dir or (RUNTIME_DIR / "broadcast" / args.date)
    payload = build_outline(transcript, args.date)
    json_path = output_dir / "actual-broadcast-outline.json"
    md_path = output_dir / "actual-broadcast-outline.md"
    if not args.dry_run:
        write_json(json_path, payload)
        write_text(md_path, render_markdown(payload))
    print_json(
        {
            "ok": True,
            "date": args.date,
            "source": str(transcript),
            "segment_count": payload.get("segment_count"),
            "topic_count": len(payload.get("topics") or []),
            "json": str(json_path),
            "markdown": str(md_path),
            "dry_run": args.dry_run,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
