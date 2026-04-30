#!/usr/bin/env python3
"""Prepare a Finviz capture plan from the earnings ticker drilldown ledger."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
NODE_SCRIPT = PROJECT_ROOT / "scripts" / "capture_finviz_feature_stocks.mjs"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_csv(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip().upper() for part in value.split(",") if part.strip()}


def select_rows(payload: dict, args: argparse.Namespace) -> list[dict]:
    statuses = {status.strip() for status in args.statuses.split(",") if status.strip()}
    include = parse_csv(args.include)
    exclude = parse_csv(args.exclude)
    rows = []
    seen = set()
    for row in payload.get("tickers", []):
        ticker = str(row.get("ticker") or "").upper()
        if not ticker or ticker in seen or ticker in exclude:
            continue
        if ticker not in include:
            if row.get("status") not in statuses:
                continue
            if int(row.get("score") or 0) < args.min_score:
                continue
        rows.append(row)
        seen.add(ticker)
        if len(rows) >= args.limit and not include - seen:
            break

    for ticker in sorted(include - seen):
        rows.append(
            {
                "ticker": ticker,
                "status": "manual",
                "score": 0,
                "reason": "수동 포함",
                "tags": [],
            }
        )
    return rows[: args.limit]


def render_markdown(date: str, rows: list[dict], command: list[str]) -> str:
    tickers = [row["ticker"] for row in rows]
    lines = [
        "# Finviz Drilldown Capture Plan",
        "",
        f"- 대상일: `{date}`",
        f"- 생성 시각: `{datetime.now().strftime('%y.%m.%d %H:%M')}`",
        f"- 캡처 후보: {', '.join(f'`{ticker}`' for ticker in tickers) or '-'}",
        "",
        "## 실행 명령",
        "",
        "```bash",
        " ".join(command),
        "```",
        "",
        "## 후보 근거",
        "",
    ]
    if not rows:
        lines.append("- 없음")
    for row in rows:
        tags = ", ".join(row.get("tags") or []) or "-"
        lines.extend(
            [
                f"### {row['ticker']}",
                "",
                f"- 상태: `{row.get('status') or '-'}` / 점수: `{row.get('score') or 0}` / 태그: {tags}",
                f"- 이유: {row.get('reason') or '-'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--statuses", default="drilldown")
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--limit", type=int, default=14)
    parser.add_argument("--include", help="Comma-separated tickers to force include.")
    parser.add_argument("--exclude", help="Comma-separated tickers to omit.")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--browser-channel", default="")
    parser.add_argument("--timeout-ms", type=int, default=45000)
    parser.add_argument("--execute", action="store_true", help="Run the Finviz capture after writing the plan.")
    args = parser.parse_args()

    input_path = args.input or (PROCESSED_DIR / args.date / "earnings-ticker-drilldown.json")
    payload = load_json(input_path)
    rows = select_rows(payload, args)
    tickers = [row["ticker"] for row in rows]

    command = [
        "node",
        str(NODE_SCRIPT.relative_to(REPO_ROOT)),
        "--date",
        args.date,
        "--tickers",
        ",".join(tickers),
        "--timeout-ms",
        str(args.timeout_ms),
    ]
    if args.headed:
        command.append("--headed")
    if args.browser_channel:
        command.extend(["--browser-channel", args.browser_channel])

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "ok": True,
        "target_date": args.date,
        "source_file": str(input_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ticker_count": len(tickers),
        "tickers": tickers,
        "rows": rows,
        "command": command,
    }
    json_path = processed_dir / "finviz-drilldown-capture-plan.json"
    md_path = notion_dir / "finviz-drilldown-capture-plan.md"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(args.date, rows, command), encoding="utf-8")

    result = {"ok": True, "ticker_count": len(tickers), "tickers": tickers, "json": str(json_path), "markdown": str(md_path)}
    if args.execute:
        if not tickers:
            raise SystemExit("No tickers selected; refusing to run empty Finviz capture.")
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        result["capture_exit_code"] = completed.returncode
        if completed.returncode != 0:
            result["ok"] = False
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return completed.returncode

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
