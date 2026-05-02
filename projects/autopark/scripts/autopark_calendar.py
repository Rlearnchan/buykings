#!/usr/bin/env python3
"""Resolve Autopark broadcast calendar operation modes."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CALENDAR = PROJECT_ROOT / "config" / "broadcast_calendar.json"
WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load_calendar(path: Path | None = None) -> dict:
    calendar_path = path or DEFAULT_CALENDAR
    if not calendar_path.exists():
        return {}
    return json.loads(calendar_path.read_text(encoding="utf-8"))


def _default_config() -> dict:
    return {
        "mode": "daily_broadcast",
        "expected_broadcast": True,
        "publish_policy": "gate",
        "retrospective_enabled": True,
        "news_lookback_hours": 24,
        "batch_b_lookback_hours": 36,
        "x_lookback_hours": 24,
        "news_limit": 80,
        "x_max_posts": 8,
        "note": "일반 방송일",
    }


def resolve_operation(
    target_date: str,
    *,
    calendar_path: Path | None = None,
    requested_mode: str | None = None,
) -> dict:
    calendar = load_calendar(calendar_path)
    resolved = _default_config()
    resolved.update(deepcopy(calendar.get("default") or {}))

    day = datetime.fromisoformat(target_date).date()
    weekday = WEEKDAY_NAMES[day.weekday()]
    weekday_config = deepcopy((calendar.get("weekday_modes") or {}).get(weekday) or {})
    if weekday_config:
        resolved.update(weekday_config)

    date_config = deepcopy((calendar.get("dates") or {}).get(target_date) or {})
    if date_config:
        resolved.update(date_config)

    if requested_mode and requested_mode != "auto":
        overrides = {
            "daily_broadcast": {
                "expected_broadcast": True,
                "publish_policy": "gate",
                "retrospective_enabled": True,
            },
            "monday_catchup": {
                "expected_broadcast": True,
                "publish_policy": "gate",
                "retrospective_enabled": True,
                "news_lookback_hours": 72,
                "batch_b_lookback_hours": 72,
                "x_lookback_hours": 72,
                "news_limit": max(140, int(resolved.get("news_limit") or 0)),
                "x_max_posts": max(16, int(resolved.get("x_max_posts") or 0)),
            },
            "no_broadcast": {
                "expected_broadcast": False,
                "publish_policy": "never",
                "retrospective_enabled": False,
            },
        }
        resolved.update(overrides.get(requested_mode, {}))
        resolved["mode"] = requested_mode
        resolved["note"] = f"명령행에서 {requested_mode} 모드를 강제했습니다."

    resolved["date"] = target_date
    resolved["weekday"] = weekday
    resolved["calendar_path"] = str((calendar_path or DEFAULT_CALENDAR).resolve())
    return resolved
