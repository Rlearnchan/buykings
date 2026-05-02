#!/usr/bin/env python3
"""Fetch market data and prepare Autopark Datawrapper inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import http.client
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from math import floor, ceil
from pathlib import Path

from prepare_datawrapper_inputs import (
    DEFAULT_CONFIG,
    PREPARED_DIR,
    find_chart,
    load_config,
    write_chart_spec,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
COINGECKO_MARKET_CHART_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"


class FetchError(RuntimeError):
    """Raised when a data source cannot return usable chart data."""


def yahoo_symbol(symbol: dict) -> str:
    return symbol.get("yahoo_symbol") or symbol["symbol"]


def fetch_yahoo_series(symbol: dict, range_value: str, interval: str) -> dict[str, float]:
    encoded_symbol = urllib.parse.quote(yahoo_symbol(symbol), safe="")
    query = urllib.parse.urlencode(
        {
            "range": range_value,
            "interval": interval,
            "includePrePost": "true",
            "events": "div,splits",
        }
    )
    request = urllib.request.Request(
        YAHOO_CHART_URL.format(symbol=encoded_symbol) + f"?{query}",
        headers={"User-Agent": "Mozilla/5.0 Autopark/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise FetchError(f"Yahoo Finance request failed for {yahoo_symbol(symbol)}: {exc}") from exc

    result = payload.get("chart", {}).get("result", [])
    if not result:
        error = payload.get("chart", {}).get("error")
        raise FetchError(f"Yahoo Finance returned no data for {yahoo_symbol(symbol)}: {error}")

    chart = result[0]
    timestamps = chart.get("timestamp") or []
    closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close") or []
    scale = float(symbol.get("scale", 1))
    series: dict[str, float] = {}
    for timestamp, close in zip(timestamps, closes, strict=False):
        if close is None:
            continue
        day = date.fromtimestamp(timestamp).isoformat()
        series[day] = round(float(close) * scale, 6)
    return series


def fred_series_id(symbol: dict) -> str:
    return symbol.get("fred_series_id") or symbol["symbol"]


def coingecko_id(symbol: dict) -> str:
    return symbol.get("coingecko_id") or symbol["symbol"].lower()


def fetch_text_with_curl_fallback(url: str, request: urllib.request.Request, timeout: int = 8) -> str:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8-sig")
    except (TimeoutError, urllib.error.URLError, http.client.HTTPException):
        completed = subprocess.run(
            ["curl", "-fsSL", "--max-time", "15", url],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or f"curl exited {completed.returncode}"
            raise FetchError(details)
        return completed.stdout


def fetch_fred_series(symbol: dict, observation_start: str) -> dict[str, float]:
    # FRED graph CSV uses cosd/cosd rather than the API's observation_start.
    # Keep this endpoint keyless and filter again locally for safety.
    query = urllib.parse.urlencode({"id": fred_series_id(symbol), "cosd": observation_start})
    request = urllib.request.Request(
        f"{FRED_CSV_URL}?{query}",
        headers={"User-Agent": "Mozilla/5.0 Autopark/0.1"},
    )
    try:
        text = fetch_text_with_curl_fallback(f"{FRED_CSV_URL}?{query}", request)
    except FetchError as exc:
        raise FetchError(f"FRED request failed for {fred_series_id(symbol)}: {exc}") from exc

    lines = text.splitlines()
    if not lines:
        raise FetchError(f"FRED returned no CSV rows for {fred_series_id(symbol)}")

    reader = csv.DictReader(lines)
    value_column = fred_series_id(symbol)
    scale = float(symbol.get("scale", 1))
    series: dict[str, float] = {}
    for row in reader:
        if row.get("observation_date", "") < observation_start:
            continue
        value = row.get(value_column)
        if value in ("", ".", None):
            continue
        try:
            series[row["observation_date"]] = round(float(value) * scale, 6)
        except ValueError:
            continue
    if not series:
        raise FetchError(f"FRED returned no numeric observations for {fred_series_id(symbol)}")
    return series


def fetch_coingecko_series(symbol: dict, days: str) -> dict[str, float]:
    coin_id = coingecko_id(symbol)
    query = urllib.parse.urlencode({"vs_currency": "usd", "days": days, "interval": "daily"})
    url = COINGECKO_MARKET_CHART_URL.format(coin_id=urllib.parse.quote(coin_id, safe="")) + f"?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 Autopark/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError, http.client.HTTPException) as exc:
        raise FetchError(f"CoinGecko request failed for {coin_id}: {exc}") from exc

    prices = payload.get("prices") or []
    if not prices:
        raise FetchError(f"CoinGecko returned no prices for {coin_id}: {payload}")

    scale = float(symbol.get("scale", 1))
    series: dict[str, float] = {}
    for timestamp_ms, value in prices:
        day = date.fromtimestamp(timestamp_ms / 1000).isoformat()
        series[day] = round(float(value) * scale, 6)
    return series


def write_wide_csv(chart: dict, target_date: str, rows: list[dict]) -> Path:
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = PREPARED_DIR / f"{chart['id']}-{target_date}.csv"
    labels = [symbol["label"] for symbol in chart.get("symbols", [])]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", *labels])
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def write_raw_metadata(chart: dict, target_date: str, source_name: str, source_payload: dict) -> Path:
    target_dir = RAW_DIR / target_date
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{chart['id']}-market-data.json"
    payload = {
        "ok": True,
        "chart_id": chart["id"],
        "target_date": target_date,
        "fetched_at_epoch": int(time.time()),
        "source": source_name,
        "data": source_payload,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_rows_for_source(chart: dict, source: str, range_value: str, interval: str, observation_start: str) -> tuple[list[dict], dict]:
    symbols = chart.get("symbols") or []
    if not symbols:
        raise SystemExit(
            f"{chart['id']} is a template chart. Pass concrete symbols after we wire the feature-stock selector."
        )

    fetched: dict[str, dict[str, float]] = {}
    metadata = {"source": source, "symbols": []}
    for symbol in symbols:
        if source == "fred":
            series = fetch_fred_series(symbol, observation_start)
        elif source == "coingecko":
            series = fetch_coingecko_series(symbol, "365" if chart.get("target_window") != "intraday_or_1d" else "1")
        elif source == "yahoo_finance":
            series = fetch_yahoo_series(symbol, range_value, interval)
        else:
            raise FetchError(f"Unsupported data source for {chart['id']}: {source}")
        fetched[symbol["label"]] = series
        symbol_meta = {"label": symbol["label"], "symbol": symbol["symbol"], "points": len(series)}
        if source == "fred":
            symbol_meta["fred_series_id"] = fred_series_id(symbol)
        if source == "yahoo_finance":
            symbol_meta["yahoo_symbol"] = yahoo_symbol(symbol)
        if source == "coingecko":
            symbol_meta["coingecko_id"] = coingecko_id(symbol)
        metadata["symbols"].append(symbol_meta)

    all_dates = sorted({day for series in fetched.values() for day in series})
    rows = []
    for day in all_dates:
        row = {"date": day}
        for label, series in fetched.items():
            row[label] = series.get(day, "")
        rows.append(row)
    return rows, metadata


def source_candidates(chart: dict, requested_source: str | None) -> list[str]:
    if requested_source:
        return [requested_source]
    preferred = chart.get("preferred_data_source")
    fallback_sources = chart.get("fallback_sources", [])
    candidates = [preferred, *fallback_sources]
    return [source for source in candidates if source]


def build_rows(chart: dict, source: str | None, range_value: str, interval: str, observation_start: str) -> tuple[list[dict], dict]:
    errors = []
    for candidate in source_candidates(chart, source):
        try:
            rows, metadata = build_rows_for_source(chart, candidate, range_value, interval, observation_start)
            metadata["fallback_errors"] = errors
            return rows, metadata
        except FetchError as exc:
            errors.append({"source": candidate, "error": str(exc)})
    raise SystemExit(f"All data sources failed for {chart['id']}: {errors}")


def parse_number(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_value(rows: list[dict], label: str) -> tuple[str, float] | None:
    for row in reversed(rows):
        value = parse_number(row.get(label))
        if value is not None:
            return row["date"], value
    return None


def latest_pair(rows: list[dict], label: str) -> tuple[str, float, str, float] | None:
    current: tuple[str, float] | None = None
    for row in reversed(rows):
        value = parse_number(row.get(label))
        if value is None:
            continue
        if current is None:
            current = (row["date"], value)
            continue
        return current[0], current[1], row["date"], value
    return None


def format_market_value(value: float, unit: str, decimals: int | None = None) -> str:
    if decimals is None:
        decimals = 2 if unit in {"$", "원"} else 3
    if unit == "$":
        return f"${value:,.{decimals}f}"
    if unit == "원":
        return f"{value:,.{decimals}f}원"
    if unit:
        return f"{value:.{decimals}f}{unit}"
    return f"{value:.{decimals}f}"


def format_market_delta(current: float, previous: float, unit: str) -> str:
    delta = current - previous
    sign = "+" if delta >= 0 else ""
    if unit == "%":
        return f"{sign}{delta * 100:.1f}bp"
    if unit == "$":
        return f"{sign}${abs(delta):,.2f}" if delta >= 0 else f"-${abs(delta):,.2f}"
    if unit == "원":
        return f"{sign}{delta:,.2f}원"
    return f"{sign}{delta:.3f}"


def latest_values(rows: list[dict], chart: dict, labels: list[str]) -> tuple[str, list[str]] | None:
    values = []
    latest_dates = []
    symbols = chart.get("symbols", [])
    for label in labels:
        pair = latest_pair(rows, label)
        current = latest_value(rows, label)
        if current is None and pair is None:
            continue
        if pair:
            current_date, value, _, previous = pair
        else:
            current_date, value = current
            previous = None
        latest_dates.append(current_date)
        unit = next((symbol.get("unit", "") for symbol in symbols if symbol["label"] == label), "")
        include_label = chart.get("subtitle_include_series_label", True)
        prefix = f"{label} " if include_label else ""
        value_text = format_market_value(value, unit)
        if previous is not None:
            value_text += f"({format_market_delta(value, previous, unit)})"
        values.append(f"{prefix}{value_text}")
    if not values:
        return None
    return max(latest_dates), values


def padded_y_range(rows: list[dict], labels: list[str]) -> list[str]:
    values = [
        value
        for row in rows
        for label in labels
        for value in [parse_number(row.get(label))]
        if value is not None
    ]
    if not values:
        return ["", ""]
    low = min(values)
    high = max(values)
    span = high - low or abs(high) * 0.1 or 1
    padded_low = low - span * 0.16
    padded_high = high + span * 0.16
    # Hundredth-level rounding gives rate/price charts enough breathing room
    # without making the axis feel arbitrary.
    return [f"{floor(padded_low * 100) / 100:.2f}", f"{ceil(padded_high * 100) / 100:.2f}"]


def source_label(source: str, metadata: dict | None = None) -> tuple[str, str]:
    symbols = (metadata or {}).get("symbols") or []
    if source == "fred":
        first_series = next((item.get("fred_series_id") for item in symbols if item.get("fred_series_id")), "")
        url = f"https://fred.stlouisfed.org/series/{first_series}" if first_series else "https://fred.stlouisfed.org/"
        return ("FRED, Federal Reserve Bank of St. Louis", url)
    if source == "coingecko":
        first_coin = next((item.get("coingecko_id") for item in symbols if item.get("coingecko_id")), "")
        url = f"https://www.coingecko.com/en/coins/{first_coin}" if first_coin else "https://www.coingecko.com/"
        return ("CoinGecko", url)
    if source == "yahoo_finance":
        first_symbol = next((item.get("yahoo_symbol") for item in symbols if item.get("yahoo_symbol")), "")
        url = f"https://finance.yahoo.com/quote/{urllib.parse.quote(first_symbol, safe='')}" if first_symbol else "https://finance.yahoo.com/"
        return ("Yahoo Finance", url)
    return (source, "")


def default_observation_start(chart: dict, target_date: str) -> str:
    target = date.fromisoformat(target_date)
    target_window = chart.get("target_window")
    if target_window == "1y":
        try:
            return target.replace(year=target.year - 1).isoformat()
        except ValueError:
            return (target - timedelta(days=365)).isoformat()
    if target_window in {"3m_or_1y", "intraday_or_1d"}:
        return (target - timedelta(days=365)).isoformat()
    return (target - timedelta(days=730)).isoformat()


def display_collected_at(value: str | None, target_date: str) -> str:
    if value:
        return value
    return target_date[2:].replace("-", ".")


def update_spec_from_rows(
    spec_path: Path,
    chart: dict,
    rows: list[dict],
    target_date: str,
    metadata: dict,
    collected_at: str | None,
    subtitle_label: str | None = None,
) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    labels = [symbol["label"] for symbol in chart.get("symbols", [])]
    source = metadata["source"]
    if chart.get("subtitle_latest_value") and labels:
        current = latest_values(rows, chart, labels)
        if current:
            _, values = current
            date_label = display_collected_at(collected_at, target_date)
            spec["title"] = f"{chart['title']}: {' / '.join(values)}"
            spec["subtitle"] = subtitle_label or f"{date_label} 기준"
            spec.setdefault("metadata", {}).setdefault("describe", {})["intro"] = spec["subtitle"]
            spec.setdefault("metadata", {}).setdefault("annotate", {})["notes"] = ""
    if chart["chart_type"] in {"d3-lines", "multiple-lines"}:
        spec.setdefault("metadata", {}).setdefault("visualize", {})["custom-range-y"] = padded_y_range(rows, labels)
    spec["source_name"], spec["source_url"] = source_label(source, metadata)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--chart", required=True, help="Chart id from config/market_charts.json")
    parser.add_argument("--range", default=None, help="Yahoo Finance range, e.g. 5d, 3mo, 1y")
    parser.add_argument("--interval", default="1d", help="Yahoo Finance interval, e.g. 5m, 1d")
    parser.add_argument("--source", choices=["fred", "coingecko", "yahoo_finance"], help="Override configured data source priority")
    parser.add_argument("--observation-start", default=None, help="FRED observation_start, defaults to a 2-year backstop")
    parser.add_argument("--collected-at", default=None, help="Display timestamp for chart subtitle, e.g. 26.04.28 05:00")
    parser.add_argument("--subtitle-label", default=None, help="Exact subtitle label, e.g. 26.04.29 06:00 종가")
    args = parser.parse_args()

    config = load_config(args.config)
    chart = find_chart(config, args.chart)

    range_value = args.range or ("5d" if chart.get("target_window") == "intraday_or_1d" else "1y")
    observation_start = args.observation_start or default_observation_start(chart, args.date)
    rows, metadata = build_rows(chart, args.source, range_value, args.interval, observation_start)
    if not rows:
        raise SystemExit(f"No rows produced for {chart['id']}")

    csv_path = write_wide_csv(chart, args.date, rows)
    spec_path = write_chart_spec(
        chart,
        csv_path,
        args.date,
        config.get("default_theme", "datawrapper-high-contrast"),
    )
    update_spec_from_rows(spec_path, chart, rows, args.date, metadata, args.collected_at, args.subtitle_label)
    raw_path = write_raw_metadata(
        chart,
        args.date,
        metadata["source"],
        {
            **metadata,
            "range": range_value,
            "interval": args.interval,
            "observation_start": observation_start,
            "rows": len(rows),
            "first_date": rows[0]["date"],
            "last_date": rows[-1]["date"],
        },
    )
    print(
        json.dumps(
            {
                "ok": True,
                "chart": chart["id"],
                "date": args.date,
                "source": metadata["source"],
                "prepared_csv": str(csv_path),
                "spec": str(spec_path),
                "raw_metadata": str(raw_path),
                "rows": len(rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
