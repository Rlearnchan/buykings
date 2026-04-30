#!/usr/bin/env python3
"""Extract ticker candidates from the fixed Earnings Whispers calendar capture."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"

TICKER_RE = re.compile(r"\$([A-Z][A-Z0-9.]{0,5})\b")

MEGACAP = {"MSFT", "AMZN", "AAPL", "META", "GOOGL", "GOOG", "NVDA", "TSLA"}
AI_INFRA = {"TER", "STX", "WDC", "NXPI", "QCOM", "RMBS", "APH", "CLS", "BE", "GLW"}
PLATFORM = {"HOOD", "SOFI", "RDDT", "SPOT", "V", "MA"}
CONSUMER = {"SBUX", "CMG", "KO", "CL", "F", "CAT", "UPS"}
ENERGY = {"COP", "CVX", "VLO", "ENPH"}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def extract_tickers(text: str) -> list[str]:
    seen = set()
    tickers = []
    for match in TICKER_RE.finditer(text or ""):
        ticker = match.group(1).upper().replace(".", "-")
        if ticker in seen:
            continue
        seen.add(ticker)
        tickers.append(ticker)
    return tickers


def tags_for_ticker(ticker: str) -> list[str]:
    tags = []
    if ticker in MEGACAP:
        tags.append("megacap")
    if ticker in AI_INFRA:
        tags.append("ai_infra")
    if ticker in PLATFORM:
        tags.append("platform")
    if ticker in CONSUMER:
        tags.append("consumer")
    if ticker in ENERGY:
        tags.append("energy")
    return tags


def parse_posts(payload: dict) -> list[dict]:
    rows = []
    seen = set()
    for post in payload.get("posts", []):
        text_blob = "\n".join(
            str(post.get(key) or "")
            for key in ["text", "raw_text"]
        )
        for image in post.get("image_refs", []) or []:
            text_blob += "\n" + str(image.get("alt") or "")
        for ticker in extract_tickers(text_blob):
            if ticker in seen:
                continue
            seen.add(ticker)
            rows.append(
                {
                    "rank": len(rows) + 1,
                    "ticker": ticker,
                    "tags": tags_for_ticker(ticker),
                    "source": post.get("source_name") or post.get("source_id") or "Earnings Whispers",
                    "source_url": post.get("url") or post.get("status_url") or "",
                    "created_at": post.get("created_at") or post.get("created_at_inferred") or "",
                    "captured_at": post.get("captured_at") or "",
                    "image_refs": [
                        image.get("local_path")
                        for image in post.get("image_refs", [])
                        if image.get("download_status") == "ok" and image.get("local_path")
                    ],
                }
            )
    return rows


def render_markdown(target_date: str, rows: list[dict]) -> str:
    lines = [
        "# Earnings Calendar Ticker Pool",
        "",
        f"- 대상일: `{target_date}`",
        f"- 추출 티커: `{len(rows)}`",
        "",
        "## 우선 태그별 후보",
        "",
    ]
    for label, tag in [
        ("AI/인프라", "ai_infra"),
        ("플랫폼/핀테크", "platform"),
        ("메가캡", "megacap"),
        ("소비/산업", "consumer"),
        ("에너지", "energy"),
    ]:
        tickers = [row["ticker"] for row in rows if tag in row["tags"]]
        lines.append(f"- {label}: {', '.join(f'`{ticker}`' for ticker in tickers) or '-'}")

    lines.extend(["", "## 전체 티커", ""])
    lines.append("| 순서 | 티커 | 태그 | 출처 |")
    lines.append("|---:|---|---|---|")
    for row in rows:
        tags = ", ".join(row["tags"]) or "-"
        source = f"[{row['source']}]({row['source_url']})" if row["source_url"].startswith("http") else row["source"]
        lines.append(f"| {row['rank']} | `{row['ticker']}` | {tags} | {source} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()

    input_path = args.input or (PROCESSED_DIR / args.date / "earnings-calendar-x-posts.json")
    payload = load_json(input_path.resolve())
    rows = parse_posts(payload)

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "ok": True,
        "target_date": args.date,
        "source_file": str(input_path),
        "ticker_count": len(rows),
        "tickers": rows,
    }
    json_path = processed_dir / "earnings-calendar-tickers.json"
    md_path = notion_dir / "earnings-calendar-tickers.md"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(args.date, rows), encoding="utf-8")
    print(json.dumps({"ok": True, "ticker_count": len(rows), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
