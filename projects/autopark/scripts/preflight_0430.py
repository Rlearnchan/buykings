#!/usr/bin/env python3
"""Run a compact Autopark preflight before the live morning dashboard."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
DEFAULT_ENV = REPO_ROOT / ".env"
KST = ZoneInfo("Asia/Seoul")


@dataclass
class Check:
    name: str
    status: str
    details: str = ""
    elapsed_seconds: float = 0.0
    artifacts: list[str] = field(default_factory=list)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_python() -> str:
    env_value = os.environ.get("AUTOPARK_PYTHON") or os.environ.get("PYTHON")
    if env_value:
        return env_value
    candidates = [
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / ".venv" / "bin" / "python",
        REPO_ROOT / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def resolve_node() -> str:
    env_value = os.environ.get("AUTOPARK_NODE_PATH") or os.environ.get("AUTOPARK_NODE")
    if env_value:
        return env_value
    if node := shutil.which("node"):
        return node
    return "node"


def chrome_browser_args() -> list[str]:
    if os.environ.get("AUTOPARK_CHROME_PATH"):
        return []
    return ["--browser-channel", "chrome"]


def rel(path: Path | str | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    try:
        return str(candidate.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(candidate)


def run_command(command: list[str], timeout: int = 90) -> tuple[int, str, str, float]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.monotonic() - started
        return completed.returncode, completed.stdout, completed.stderr, elapsed
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, stdout, stderr or f"timed out after {timeout}s", elapsed


def parse_json_output(stdout: str, stderr: str = "") -> dict:
    for blob in (stdout, stderr):
        blob = blob.strip()
        if not blob:
            continue
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            start = blob.find("{")
            end = blob.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(blob[start : end + 1])
                except json.JSONDecodeError:
                    pass
    return {}


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def check_env(env_path: Path) -> Check:
    env = {**load_env(env_path), **os.environ}
    keys = ["NOTION_API_KEY", "OPENAI_API_KEY", "DATAWRAPPER_ACCESS_TOKEN"]
    present = [key for key in keys if env.get(key)]
    missing = [key for key in keys if not env.get(key)]
    status = "ok" if not missing else "warn"
    details = f"present={', '.join(present) or '-'}; missing={', '.join(missing) or '-'}"
    return Check("env keys", status, details)


def check_notion(env_path: Path) -> Check:
    started = time.monotonic()
    env = {**load_env(env_path), **os.environ}
    token = env.get("NOTION_API_KEY")
    if not token:
        return Check("notion parent access", "fail", "missing NOTION_API_KEY")
    try:
        config = json.loads((PROJECT_ROOT / "config/autopark.json").read_text(encoding="utf-8"))
        parent_id = config.get("integrations", {}).get("notion", {}).get("dashboard_parent_page_id")
    except (OSError, json.JSONDecodeError):
        parent_id = None
    if not parent_id:
        return Check("notion parent access", "fail", "missing integrations.notion.dashboard_parent_page_id")
    request = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{parent_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2026-03-11",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        elapsed = time.monotonic() - started
        title = ""
        if payload.get("type") == "child_page":
            title = payload.get("child_page", {}).get("title", "")
        details = f"parent_id={parent_id}; title={title or payload.get('type', '-')}"
        return Check("notion parent access", "ok", details, elapsed)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        elapsed = time.monotonic() - started
        return Check("notion parent access", "fail", f"parent_id={parent_id}; error={exc}", elapsed)


def check_cdp(endpoint: str) -> Check:
    started = time.monotonic()
    try:
        with urllib.request.urlopen(f"{endpoint.rstrip('/')}/json/version", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        elapsed = time.monotonic() - started
        browser = payload.get("Browser", "Chrome")
        return Check("chrome cdp endpoint", "ok", f"{endpoint} ({browser})", elapsed)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        elapsed = time.monotonic() - started
        details = f"{endpoint} unavailable: {exc}. Run ops/windows/start_autopark_chrome.ps1 or projects/autopark/scripts/launch_chrome_cdp_profile.sh first."
        return Check("chrome cdp endpoint", "fail", details, elapsed)


def check_x_cdp(args: argparse.Namespace) -> Check:
    command = [
        resolve_node(),
        "projects/autopark/scripts/collect_x_timeline.mjs",
        "--date",
        args.date,
        "--run-name",
        "preflight-x-cdp",
        "--cdp-endpoint",
        args.cdp_endpoint,
        "--max-posts",
        str(args.x_max_posts),
        "--lookback-hours",
        str(args.x_lookback_hours),
        "--scrolls",
        str(args.x_scrolls),
        "--min-text-length",
        "20",
        "--no-download-images",
        "--dry-run",
    ]
    x_sources = [source.strip() for source in args.x_sources.split(",") if source.strip()]
    if x_sources:
        for source in x_sources:
            command.extend(["--source", source])
    else:
        command.extend(["--source-profile", args.x_profile])
    code, stdout, stderr, elapsed = run_command(command, timeout=args.timeout)
    payload = parse_json_output(stdout, stderr)
    results = payload.get("source_results", [])
    ok_sources = [item["source_id"] for item in results if item.get("post_count", 0) > 0]
    zero_sources = [item["source_id"] for item in results if item.get("status") == "ok" and item.get("post_count", 0) == 0]
    error_sources = [item["source_id"] for item in results if item.get("status") != "ok"]
    post_count = len(payload.get("posts", []))
    if code == 0 and post_count:
        status = "ok"
    elif code == 0:
        status = "warn"
    else:
        status = "fail"
    details = f"posts={post_count}; ok={len(ok_sources)}; zero={zero_sources or '-'}; errors={error_sources or '-'}"
    if code == 124:
        status = "fail"
        details = f"{details}; timeout={args.timeout}s"
    return Check("x cdp collection", status, details, elapsed)


def check_finviz(args: argparse.Namespace) -> Check:
    command = [
        resolve_node(),
        "projects/autopark/scripts/capture_source.mjs",
        "--date",
        args.date,
        "--source",
        args.finviz_source,
        "--use-auth-profiles",
        "--headed",
        *chrome_browser_args(),
        "--timeout-ms",
        "45000",
        "--no-full-page",
    ]
    code, stdout, stderr, elapsed = run_command(command, timeout=args.timeout)
    payload = parse_json_output(stdout, stderr)
    metadata = payload.get("metadata", {})
    status_value = metadata.get("status") or "unknown"
    screenshot = metadata.get("screenshot_path")
    if code == 0 and status_value == "ok":
        status = "ok"
    elif status_value in {"partial", "blocked"}:
        status = "warn"
    else:
        status = "fail"
    details = f"{args.finviz_source}: status={status_value}; title={metadata.get('title', '-')}"
    artifacts = [rel(screenshot)] if screenshot else []
    return Check("finviz headed capture", status, details, elapsed, artifacts)


def check_market_data(args: argparse.Namespace) -> Check:
    chart = args.market_chart
    subtitle = args.collected_at or datetime.now().strftime("%y.%m.%d %H:%M")
    command = [
        resolve_python(),
        "projects/autopark/scripts/fetch_market_chart_data.py",
        "--date",
        args.date,
        "--chart",
        chart,
        "--collected-at",
        subtitle,
    ]
    code, stdout, stderr, elapsed = run_command(command, timeout=args.timeout)
    payload = parse_json_output(stdout, stderr)
    artifacts: list[str] = []
    if payload.get("prepared_csv"):
        artifacts.append(rel(payload["prepared_csv"]))
    if payload.get("spec"):
        artifacts.append(rel(payload["spec"]))
    spec_title = "-"
    spec_subtitle = "-"
    spec_path = Path(payload["spec"]) if payload.get("spec") else None
    if spec_path and spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec_title = spec.get("title") or "-"
            spec_subtitle = spec.get("subtitle") or "-"
        except json.JSONDecodeError:
            pass
    rows = payload.get("rows")
    status = "ok" if code == 0 and rows else "fail"
    details = f"{chart}: rows={rows or 0}; title={spec_title}; subtitle={spec_subtitle}"
    if code != 0 and stderr:
        details = f"{details}; error={stderr.strip()[:240]}"
    return Check("market data fetch", status, details, elapsed, artifacts)


def check_economic_calendar(args: argparse.Namespace) -> Check:
    subtitle = args.collected_at or datetime.now().strftime("%y.%m.%d %H:%M")
    command = [
        resolve_python(),
        "projects/autopark/scripts/fetch_economic_calendar.py",
        "--date",
        args.date,
        "--min-importance",
        "2",
        "--limit",
        "10",
        "--collected-at",
        subtitle,
    ]
    code, stdout, stderr, elapsed = run_command(command, timeout=args.timeout)
    payload = parse_json_output(stdout, stderr)
    artifacts: list[str] = []
    datawrapper = payload.get("datawrapper") or {}
    if datawrapper.get("prepared_csv"):
        artifacts.append(rel(datawrapper["prepared_csv"]))
    if datawrapper.get("spec"):
        artifacts.append(rel(datawrapper["spec"]))
    embed_height = "-"
    spec_path = Path(datawrapper["spec"]) if datawrapper.get("spec") else None
    if spec_path and spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            embed_height = spec.get("metadata", {}).get("publish", {}).get("embed-height", "-")
        except json.JSONDecodeError:
            pass
    count = payload.get("count") or len(payload.get("events", []))
    status = "ok" if code == 0 else "fail"
    details = f"events={count}; limit=10; embed_height={embed_height}; US>=2 stars / non-US=3 stars"
    if code != 0 and stderr:
        details = f"{details}; error={stderr.strip()[:240]}"
    return Check("economic calendar fetch", status, details, elapsed, artifacts)


def check_current_pngs() -> Check:
    expected = [
        "us10y.png",
        "crude-oil-wti.png",
        "crude-oil-brent.png",
        "dollar-index.png",
        "usd-krw.png",
        "bitcoin.png",
        "economic-calendar-us.png",
        "economic-calendar-global.png",
    ]
    current = PROJECT_ROOT / "exports/current"
    missing: list[str] = []
    too_short: list[str] = []
    artifacts: list[str] = []
    sizes: list[str] = []
    for name in expected:
        path = current / name
        size = png_size(path)
        if not size:
            missing.append(name)
            continue
        width, height = size
        artifacts.append(rel(path))
        sizes.append(f"{name}={width}x{height}")
        if name.startswith("economic-calendar") and height < 420:
            too_short.append(f"{name}={width}x{height}")
    status = "ok" if not missing and not too_short else "warn"
    details = f"missing={missing or '-'}; crop_watch={too_short or '-'}; sizes={'; '.join(sizes)}"
    return Check("current png inventory", status, details, artifacts=artifacts)


def render_markdown(date_value: str, checks: list[Check]) -> str:
    now = datetime.now(KST).strftime("%y.%m.%d %H:%M")
    ok_count = sum(1 for check in checks if check.status == "ok")
    warn_count = sum(1 for check in checks if check.status == "warn")
    fail_count = sum(1 for check in checks if check.status == "fail")
    lines = [
        f"# Autopark Preflight - {date_value}",
        "",
        f"- 실행 시각: {now} KST",
        f"- 결과: ok {ok_count} / warn {warn_count} / fail {fail_count}",
        "",
        "## Checks",
        "",
        "| check | status | seconds | details |",
        "|---|---:|---:|---|",
    ]
    for check in checks:
        details = check.details.replace("|", "\\|")
        lines.append(f"| {check.name} | {check.status} | {check.elapsed_seconds:.1f} | {details} |")
    lines.extend(["", "## Artifacts", ""])
    artifact_lines = []
    for check in checks:
        for artifact in check.artifacts:
            artifact_lines.append(f"- {check.name}: `{artifact}`")
    lines.extend(artifact_lines or ["- none"])
    lines.extend(
        [
            "",
            "## Morning Notes",
            "",
            "- X가 fail이면 Windows에서는 `ops/windows/start_autopark_chrome.ps1`, Mac에서는 `projects/autopark/scripts/launch_chrome_cdp_profile.sh`를 먼저 실행하고 재시도한다.",
            "- Finviz가 fail이면 같은 persistent profile을 쓰는 다른 Chrome/Playwright 창이 열려 있는지 확인한다.",
            "- 경제 일정 PNG는 export 후 하단 crop 여부를 다시 육안 확인한다.",
            "- Notion 본문에는 내부 점수/장부를 넣지 않고 04.21처럼 얇게 배치한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Autopark live dashboard preflight")
    parser.add_argument("--date", default=datetime.now(KST).date().isoformat())
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--cdp-endpoint", default=None)
    parser.add_argument("--x-profile", default="market_radar")
    parser.add_argument("--x-sources", default="x-kobeissiletter,x-wallstengine,x-bloomberg,x-cnbc", help="Comma-separated fast X smoke-test source ids. Empty string uses --x-profile.")
    parser.add_argument("--x-max-posts", type=int, default=2)
    parser.add_argument("--x-lookback-hours", type=int, default=48)
    parser.add_argument("--x-scrolls", type=int, default=1)
    parser.add_argument("--finviz-source", default="finviz-russell-heatmap")
    parser.add_argument("--market-chart", default="us10y")
    parser.add_argument("--collected-at", default=None)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--skip-x", action="store_true")
    parser.add_argument("--skip-finviz", action="store_true")
    parser.add_argument("--skip-data", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    file_env = load_env(args.env.resolve())
    for key, value in file_env.items():
        os.environ.setdefault(key, value)
    args.cdp_endpoint = args.cdp_endpoint or os.environ.get("AUTOPARK_CDP_ENDPOINT") or "http://127.0.0.1:9222"

    checks: list[Check] = [check_env(args.env.resolve()), check_notion(args.env.resolve()), check_cdp(args.cdp_endpoint)]
    if not args.skip_x:
        checks.append(check_x_cdp(args))
    if not args.skip_finviz:
        checks.append(check_finviz(args))
    if not args.skip_data:
        checks.append(check_market_data(args))
        checks.append(check_economic_calendar(args))
    checks.append(check_current_pngs())

    output_dir = PROJECT_ROOT / "runtime/logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output or output_dir / f"{args.date}-preflight.md"
    json_path = output_path.with_suffix(".json")
    output_path.write_text(render_markdown(args.date, checks), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "ok": not any(check.status == "fail" for check in checks),
                "date": args.date,
                "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
                "checks": [check.__dict__ for check in checks],
                "markdown_path": rel(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": not any(check.status == "fail" for check in checks), "markdown_path": rel(output_path), "json_path": rel(json_path)}, ensure_ascii=False, indent=2))
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
