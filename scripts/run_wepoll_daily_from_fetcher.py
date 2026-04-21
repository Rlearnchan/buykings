#!/usr/bin/env python3
"""Download Wepoll raw CSV via the long-lived fetcher and run daily append."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FETCHER = "http://127.0.0.1:8777"
DEFAULT_DOWNLOAD_DIR = ROOT / "runtime" / "downloads" / "wepoll"
DEFAULT_MANIFEST_DIR = ROOT / "runtime" / "logs" / "wepoll-fetcher"


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Fetcher API error ({exc.code}) on {method} {url}:\n{details}") from exc


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetcher-url", default=DEFAULT_FETCHER)
    parser.add_argument("--period-label", default="최근 3일")
    parser.add_argument("--board-label", default="경제")
    parser.add_argument("--include-label", default="글만")
    parser.add_argument("--format-label", default="CSV")
    parser.add_argument("--download-dir", type=Path, default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--skip-append", action="store_true")
    parser.add_argument("--skip-healthcheck", action="store_true")
    parser.add_argument("--skip-sqlite-sync", action="store_true")
    parser.add_argument("--sqlite-init-schema", action="store_true")
    parser.add_argument("--target-date")
    parser.add_argument("--min-rows", type=int)
    parser.add_argument("--today")
    parser.add_argument("--model")
    parser.add_argument("--timeseries-spec", type=Path)
    parser.add_argument("--bubble-spec", type=Path)
    parser.add_argument("--panic-root", type=Path)
    parser.add_argument("--python-executable")
    parser.add_argument("--second-pass-backend")
    parser.add_argument("--ollama-host")
    parser.add_argument("--openai-api-key")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--skip-publish", action="store_true")
    args = parser.parse_args()

    args.download_dir.mkdir(parents=True, exist_ok=True)
    args.manifest_dir.mkdir(parents=True, exist_ok=True)

    base_url = args.fetcher_url.rstrip("/")
    if not args.skip_healthcheck:
        health = request_json("GET", f"{base_url}/health")
        if not health.get("ok"):
            raise SystemExit(f"Fetcher health check failed: {health}")
        if not health.get("authenticated"):
            raise SystemExit(f"Fetcher is not authenticated: {json.dumps(health, ensure_ascii=False)}")

    download_payload = {
        "periodLabel": args.period_label,
        "boardLabel": args.board_label,
        "includeLabel": args.include_label,
        "formatLabel": args.format_label,
        "outputDir": str(args.download_dir.resolve()),
    }
    download_result = request_json("POST", f"{base_url}/download", download_payload)
    if not download_result.get("ok"):
        raise SystemExit(f"Fetcher download failed: {json.dumps(download_result, ensure_ascii=False)}")

    raw_csv = Path(download_result["downloaded_file"]).resolve()
    if not raw_csv.exists():
        raise SystemExit(f"Fetcher reported a downloaded file that does not exist: {raw_csv}")

    manifest_path = args.manifest_dir / f"{raw_csv.stem}.json"
    manifest_path.write_text(
        json.dumps(download_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    append_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_wepoll_daily_append.py"),
        "--input",
        str(raw_csv),
    ]
    if args.target_date:
        append_cmd.extend(["--target-date", args.target_date])
    if args.min_rows is not None:
        append_cmd.extend(["--min-rows", str(args.min_rows)])
    if args.today:
        append_cmd.extend(["--today", args.today])
    if args.model:
        append_cmd.extend(["--model", args.model])
    if args.timeseries_spec:
        append_cmd.extend(["--timeseries-spec", str(args.timeseries_spec.resolve())])
    if args.bubble_spec:
        append_cmd.extend(["--bubble-spec", str(args.bubble_spec.resolve())])
    if args.panic_root:
        append_cmd.extend(["--panic-root", str(args.panic_root.resolve())])
    if args.python_executable:
        append_cmd.extend(["--python-executable", args.python_executable])
    if args.second_pass_backend:
        append_cmd.extend(["--second-pass-backend", args.second_pass_backend])
    if args.ollama_host:
        append_cmd.extend(["--ollama-host", args.ollama_host])
    if args.openai_api_key:
        append_cmd.extend(["--openai-api-key", args.openai_api_key])
    if args.env_file:
        append_cmd.extend(["--env-file", str(args.env_file.resolve())])
    if args.skip_publish:
        append_cmd.append("--skip-publish")

    if not args.skip_append:
        run(append_cmd)

    if not args.skip_sqlite_sync:
        sqlite_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "wepoll_sync_sqlite.py"),
            "--raw-csv",
            str(raw_csv),
        ]
        if args.sqlite_init_schema:
            sqlite_cmd.insert(2, "--init-schema")
        run(sqlite_cmd)

    print(
        json.dumps(
            {
                "ok": True,
                "raw_csv": str(raw_csv),
                "manifest": str(manifest_path),
                "append_ran": not args.skip_append,
                "sqlite_sync_ran": not args.skip_sqlite_sync,
                "fetcher_url": args.fetcher_url,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
