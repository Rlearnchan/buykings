#!/usr/bin/env python3
"""Fetch historical index data from Investing.com pages and save as CSV.

The page HTML currently embeds a `historicalDataStore.historicalData.data`
array inside the initial Next.js payload. This script extracts that JSON and
writes a local CSV compatible with the existing `import_market_csvs.py` flow.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path


PRESETS = {
    "kospi": "https://kr.investing.com/indices/kospi-historical-data",
    "kosdaq": "https://kr.investing.com/indices/kosdaq-historical-data",
    "vkospi": "https://kr.investing.com/indices/kospi-volatility-historical-data",
}

HISTORICAL_DATA_MARKER = '"historicalData":{"data":'


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_historical_rows(html: str) -> list[dict[str, object]]:
    idx = html.find(HISTORICAL_DATA_MARKER)
    if idx == -1:
        raise SystemExit("Could not find historicalData marker in Investing.com page HTML.")

    payload = html[idx + len(HISTORICAL_DATA_MARKER) :]
    rows, _ = json.JSONDecoder().raw_decode(payload)
    if not isinstance(rows, list) or not rows:
        raise SystemExit("Parsed historicalData payload, but it was empty.")
    return rows


def normalize_volume(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text in {"", "0", "0.0"}:
        return ""
    return text


def normalize_change_percent(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    return text if text.endswith("%") else f"{text}%"


def rows_to_csv_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        date_value = str(row["rowDateTimestamp"])[:10]
        out.append(
            {
                "날짜": date_value,
                "종가": str(row.get("last_close", "")).strip(),
                "시가": str(row.get("last_open", "")).strip(),
                "고가": str(row.get("last_max", "")).strip(),
                "저가": str(row.get("last_min", "")).strip(),
                "거래량": normalize_volume(row.get("volume")),
                "변동 %": normalize_change_percent(row.get("change_precent", "")),
            }
        )
    return out


def validate_required_dates(rows: list[dict[str, str]], required_dates: list[str]) -> None:
    if not required_dates:
        return
    dates = {row["날짜"] for row in rows}
    missing = [date for date in required_dates if date not in dates]
    if missing:
        raise SystemExit(
            "Missing required dates in Investing.com historical data: "
            + ", ".join(missing)
        )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["날짜", "종가", "시가", "고가", "저가", "거래량", "변동 %"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS))
    parser.add_argument("--url")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--required-date", action="append", default=[])
    args = parser.parse_args()

    url = args.url or (PRESETS.get(args.preset) if args.preset else None)
    if not url:
        raise SystemExit("Provide either --preset or --url.")

    html = fetch_html(url)
    rows = rows_to_csv_rows(extract_historical_rows(html))
    validate_required_dates(rows, args.required_date)
    write_csv(args.output, rows)

    print(
        json.dumps(
            {
                "ok": True,
                "url": url,
                "rows": len(rows),
                "latest_date": rows[0]["날짜"],
                "oldest_date": rows[-1]["날짜"],
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
