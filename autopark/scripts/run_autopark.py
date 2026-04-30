#!/usr/bin/env python3
"""Run the Autopark morning preparation pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "autopark.json"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def list_items(config: dict) -> dict:
    return {
        "name": config.get("name", "autopark"),
        "stages": [
            {
                "id": stage["id"],
                "enabled": stage.get("enabled", False),
                "description": stage.get("description", ""),
            }
            for stage in config.get("stages", [])
        ],
        "sources": [
            {
                "id": source["id"],
                "enabled": source.get("enabled", False),
                "kind": source.get("kind", ""),
                "url": source.get("url", ""),
            }
            for source in config.get("sources", [])
        ],
    }


def planned_run(config: dict, target_date: str) -> dict:
    stages = config.get("stages", [])
    enabled_stages = [stage for stage in stages if stage.get("enabled", False)]
    return {
        "ok": True,
        "mode": "dry-run",
        "name": config.get("name", "autopark"),
        "target_date": target_date,
        "enabled_stage_count": len(enabled_stages),
        "planned_stages": [
            {
                "id": stage["id"],
                "status": "planned",
                "description": stage.get("description", ""),
            }
            for stage in enabled_stages
        ],
        "note": "No stages are executed yet; enable and implement stages as site specs arrive.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=date.today().isoformat(), help="Target date in YYYY-MM-DD")
    parser.add_argument("--list", action="store_true", help="List configured stages and sources")
    parser.add_argument("--dry-run", action="store_true", help="Print the current execution plan")
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = load_config(config_path)

    if args.list:
        print(json.dumps(list_items(config), ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        print(json.dumps(planned_run(config, args.date), ensure_ascii=False, indent=2))
        return

    raise SystemExit("Autopark stages are not implemented yet. Use --list or --dry-run.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
