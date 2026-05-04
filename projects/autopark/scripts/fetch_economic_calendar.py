#!/usr/bin/env python3
"""Fetch and parse the Trading Economics public calendar HTML."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
PREPARED_DIR = PROJECT_ROOT / "prepared"
CHARTS_DIR = PROJECT_ROOT / "charts"
CALENDAR_URL = "https://ko.tradingeconomics.com/calendar"
DEFAULT_COUNTRIES = ("US", "KR", "CN", "JP", "EU", "DE", "GB", "CA", "FR", "ES")


@dataclass
class CalendarEvent:
    id: str
    url: str
    country: str
    country_name: str
    category: str
    event: str
    importance: int
    utc_datetime: str | None
    local_datetime: str | None
    local_date: str | None
    actual: str
    previous: str
    consensus: str
    forecast: str


class CalendarFetchError(RuntimeError):
    """Raised when the calendar page cannot be fetched or parsed."""


def fetch_html(min_importance: int) -> str:
    if min_importance <= 1:
        url = CALENDAR_URL
    else:
        query = urllib.parse.urlencode({"importance": str(min_importance)})
        url = f"{CALENDAR_URL}?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "Mozilla/5.0 Autopark/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except (TimeoutError, urllib.error.URLError) as exc:
        completed = subprocess.run(
            ["curl", "-fsSL", "--max-time", "20", url],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or f"curl exited {completed.returncode}"
            raise CalendarFetchError(f"Trading Economics request failed: {details}") from exc
        return completed.stdout


def clean_fragment(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<.*?>", "", value, flags=re.S)
    return " ".join(html.unescape(without_tags).split())


def first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags)
    return match.group(1) if match else ""


def parse_utc_datetime(day: str, time_text: str) -> datetime | None:
    if not day or not time_text:
        return None
    if "Tentative" in time_text or "잠정" in time_text:
        return None
    try:
        parsed_time = datetime.strptime(time_text.strip(), "%I:%M %p").time()
    except ValueError:
        return None
    return datetime.combine(date.fromisoformat(day), parsed_time, tzinfo=timezone.utc)


def split_rows(page: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"<tr data-url=", page)]
    if not starts:
        return []
    rows = [page[starts[index] : starts[index + 1]] for index in range(len(starts) - 1)]
    rows.append(page[starts[-1] :])
    return rows


def parse_calendar_html(page: str, local_offset_minutes: int) -> list[CalendarEvent]:
    local_tz = timezone(timedelta(minutes=local_offset_minutes))
    events: list[CalendarEvent] = []
    for row in split_rows(page):
        importance_text = first_match(r"calendar-date-(\d)", row)
        if not importance_text:
            continue

        day = first_match(r"class='\s*([0-9-]{10})", row)
        time_text = clean_fragment(first_match(r'calendar-date-\d">\s*([^<]+)', row))
        utc_dt = parse_utc_datetime(day, time_text)
        local_dt = utc_dt.astimezone(local_tz) if utc_dt else None

        country_name = first_match(r'td title="([^"]+)"[^>]*class="calendar-iso"', row)
        event_html = first_match(r"<a class='calendar-event'[^>]*>(.*?)</a>", row, re.S)
        event = clean_fragment(event_html) or clean_fragment(
            first_match(r'data-event="([^"]+)"', row)
        ).title()

        events.append(
            CalendarEvent(
                id=first_match(r'data-id="([^"]+)"', row),
                url="https://ko.tradingeconomics.com"
                + first_match(r'data-url="([^"]+)"', row),
                country=clean_fragment(first_match(r'class="calendar-iso">([^<]+)', row)),
                country_name=html.unescape(country_name),
                category=html.unescape(first_match(r'data-category="([^"]+)"', row)),
                event=event,
                importance=int(importance_text),
                utc_datetime=utc_dt.isoformat() if utc_dt else None,
                local_datetime=local_dt.isoformat() if local_dt else None,
                local_date=local_dt.date().isoformat() if local_dt else day or None,
                actual=clean_fragment(first_match(r"id='actual'>(.*?)</span>", row, re.S)),
                previous=clean_fragment(first_match(r"id='previous'>(.*?)</span>", row, re.S)),
                consensus=clean_fragment(first_match(r"id='consensus'[^>]*>(.*?)</a>", row, re.S)),
                forecast=clean_fragment(first_match(r"id='forecast'[^>]*>(.*?)</a>", row, re.S)),
            )
        )
    return events


def importance_rule_text() -> str:
    return "미국 2★ 이상, 기타 국가 3★"


def passes_importance_rule(event: CalendarEvent) -> bool:
    if event.country.upper() == "US":
        return event.importance >= 2
    return event.importance >= 3


def expected_value(event: CalendarEvent) -> str:
    return event.consensus or event.forecast


def event_quality(event: CalendarEvent) -> tuple[int, int, int, int]:
    return (
        1 if expected_value(event) else 0,
        1 if event.previous else 0,
        1 if event.actual else 0,
        event.importance,
    )


def dedupe_events(events: list[CalendarEvent]) -> list[CalendarEvent]:
    best: dict[tuple[str, str, str], CalendarEvent] = {}
    for event in events:
        key = (event.local_datetime or "", event.country.upper(), event.event)
        current = best.get(key)
        if current is None or event_quality(event) > event_quality(current):
            best[key] = event
    return sorted(best.values(), key=lambda event: (event.local_datetime or "", -event.importance, event.country))


def overflow_drop_rank(event: CalendarEvent) -> tuple[int, str, str, str]:
    country = event.country.upper()
    if country == "US" and event.importance == 2:
        rank = 0
    elif country != "US" and event.importance == 3:
        rank = 1
    elif country == "US" and event.importance == 3:
        rank = 2
    else:
        rank = 3
    return (rank, event.local_datetime or "", country, event.event)


def trim_to_limit(events: list[CalendarEvent], limit: int) -> list[CalendarEvent]:
    if limit <= 0 or len(events) <= limit:
        return events
    keep = sorted(events, key=overflow_drop_rank, reverse=True)[:limit]
    return sorted(keep, key=lambda event: (event.local_datetime or "", -event.importance, event.country))


def render_markdown(events: list[CalendarEvent], target_date: str, local_offset_minutes: int) -> str:
    offset_hours = local_offset_minutes / 60
    tz_label = f"UTC{offset_hours:+g}"
    lines = [
        f"# 경제캘린더 {target_date}",
        "",
        f"- 기준: Trading Economics 공개 캘린더 HTML, {importance_rule_text()}, {tz_label} 변환",
        "",
    ]
    if not events:
        lines.append("- 해당 조건의 이벤트 없음")
        return "\n".join(lines) + "\n"

    for event in events:
        when = event.local_datetime[11:16] if event.local_datetime else "시간미정"
        stars = "★" * event.importance
        values = []
        if expected_value(event):
            values.append(f"예상 {expected_value(event)}")
        if event.previous:
            values.append(f"이전 {event.previous}")
        if event.actual:
            values.append(f"실제 {event.actual}")
        suffix = f" / {' / '.join(values)}" if values else ""
        lines.append(f"- {stars} {when} {event.country} {event.event}{suffix}")
    return "\n".join(lines) + "\n"


def calendar_group_title(group: str) -> str:
    if group == "us":
        return "오늘의 미국 경제 일정"
    if group == "global":
        return "오늘의 글로벌 경제 일정"
    return "오늘의 경제 일정"


def calendar_group_slug(group: str) -> str:
    if group == "all":
        return "economic-calendar"
    return f"economic-calendar-{group}"


def calendar_group_note(group: str) -> str:
    if group == "us":
        return "미국 2★ 이상"
    if group == "global":
        return "미국 제외 3★"
    return importance_rule_text()


def economic_calendar_subtitle(target_date: str, collected_at: str | None, group: str) -> str:
    title_date = target_date.replace("-", ".")[2:]
    note = calendar_group_note(group)
    if collected_at:
        checked = collected_at if "KST" in collected_at else f"{collected_at} KST"
        return f"KST 일정 {title_date} 기준 · 확인 {checked}, {note}"
    return f"KST 일정 {title_date} 기준, {note}"


def write_one_datawrapper_input(
    events: list[CalendarEvent],
    target_date: str,
    collected_at: str | None,
    group: str,
) -> tuple[Path, Path]:
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = calendar_group_slug(group)
    csv_path = PREPARED_DIR / f"{slug}-{target_date}.csv"
    spec_path = CHARTS_DIR / f"{slug}-datawrapper.json"

    fieldnames = ["시각", "중요도", "국가", "이벤트", "예상"]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "시각": event.local_datetime[11:16] if event.local_datetime else "시간미정",
                    "중요도": "★" * event.importance,
                    "국가": event.country,
                    "이벤트": event.event,
                    "예상": f"\u200b{expected_value(event)}" if expected_value(event) else "",
                }
            )

    subtitle = economic_calendar_subtitle(target_date, collected_at, group)
    spec = {
        "project": "autopark",
        "slug": slug,
        "title": calendar_group_title(group),
        "subtitle": subtitle,
        "chart_type": "tables",
        "theme": "datawrapper-high-contrast",
        "prepared_csv": f"../prepared/{csv_path.name}",
        "source_name": "Trading Economics",
        "source_url": CALENDAR_URL,
        "byline": "",
        "metadata": {
            "describe": {
                "intro": subtitle,
                "aria-description": f"Trading Economics 공개 경제캘린더 HTML에서 파싱한 {calendar_group_title(group)}",
            },
            "publish": {
                "embed-width": 600,
                "embed-height": table_embed_height(events),
            },
            "visualize": {
                "perPage": 10,
                "striped": True,
                "pagination": False,
                "columns": {
                    "시각": {"align": "left", "width": 0.09},
                    "중요도": {"align": "left", "width": 0.10},
                    "국가": {"align": "left", "width": 0.07},
                    "이벤트": {"align": "left", "width": 0.48},
                    "예상": {"align": "left", "width": 0.26},
                },
            },
        },
    }
    if spec_path.exists():
        previous = json.loads(spec_path.read_text(encoding="utf-8"))
        if previous.get("chart_id"):
            spec["chart_id"] = previous["chart_id"]
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, spec_path


def write_datawrapper_inputs(events: list[CalendarEvent], target_date: str, collected_at: str | None = None) -> dict[str, dict[str, str]]:
    groups = {
        "us": [event for event in events if event.country.upper() == "US"],
        "global": [event for event in events if event.country.upper() != "US"],
        # Keep the legacy combined chart spec updated for compatibility with older scripts.
        "all": events,
    }
    outputs: dict[str, dict[str, str]] = {}
    for group, group_events in groups.items():
        csv_path, spec_path = write_one_datawrapper_input(group_events, target_date, collected_at, group)
        outputs[group] = {"prepared_csv": str(csv_path), "spec": str(spec_path)}
    return outputs


def display_width(text: str) -> int:
    """Approximate table wrapping width; Korean/full-width glyphs take more room."""
    width = 0
    for char in text:
        if char.isspace() or ord(char) < 128:
            width += 1
        else:
            width += 2
    return width


def wrapped_lines(text: str, chars_per_line: int) -> int:
    if not text:
        return 1
    return max(1, math.ceil(display_width(text) / chars_per_line))


def table_embed_height(events: list[CalendarEvent]) -> int:
    """Conservative Datawrapper table height for PNG export.

    Datawrapper crops exported table PNGs at ``publish.embed-height``. The Korean
    calendar labels wrap in the 600px layout, so a fixed height can clip the last
    rows on days with close to ten events.
    """
    title_and_header = 130
    footer_padding = 52
    row_total = 0
    for event in events:
        event_lines = wrapped_lines(event.event, 18)
        expected_lines = wrapped_lines(expected_value(event), 10) if expected_value(event) else 1
        row_total += 28 + max(event_lines, expected_lines) * 20
    return max(380, min(760, title_and_header + row_total + footer_padding))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat(), help="Local date YYYY-MM-DD")
    parser.add_argument("--min-importance", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--countries", nargs="*", default=list(DEFAULT_COUNTRIES))
    parser.add_argument("--all-countries", action="store_true")
    parser.add_argument("--local-offset-minutes", type=int, default=540, help="KST is 540")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--collected-at", default=None, help="Display timestamp for Datawrapper subtitle, e.g. 26.04.29 06:54")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_countries = {country.upper() for country in args.countries}
    page = fetch_html(args.min_importance)
    events = parse_calendar_html(page, args.local_offset_minutes)

    filtered = [
        event
        for event in events
        if event.local_date == args.date
        and event.importance >= args.min_importance
        and passes_importance_rule(event)
        and (args.all_countries or event.country.upper() in target_countries)
    ]
    filtered = dedupe_events(filtered)
    if args.limit > 0:
        filtered = trim_to_limit(filtered, args.limit)

    payload = {
        "source": CALENDAR_URL,
        "target_date": args.date,
        "local_offset_minutes": args.local_offset_minutes,
        "min_importance": args.min_importance,
        "countries": "all" if args.all_countries else sorted(target_countries),
        "events": [asdict(event) for event in filtered],
    }

    if not args.no_write:
        raw_dir = RAW_DIR / args.date
        processed_dir = PROCESSED_DIR / args.date
        notion_dir = RUNTIME_NOTION_DIR / args.date
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        notion_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"tradingeconomics-calendar-importance{args.min_importance}.html").write_text(
            page, encoding="utf-8"
        )
        (processed_dir / "economic-calendar.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (notion_dir / "economic-calendar.md").write_text(
            render_markdown(filtered, args.date, args.local_offset_minutes), encoding="utf-8"
        )
        payload["datawrapper"] = write_datawrapper_inputs(filtered, args.date, args.collected_at)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
