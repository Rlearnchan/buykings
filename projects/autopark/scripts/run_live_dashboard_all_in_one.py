#!/usr/bin/env python3
"""Run the Autopark live dashboard pipeline from collection to Notion publish."""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from autopark_calendar import DEFAULT_CALENDAR, resolve_operation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
KST = ZoneInfo("Asia/Seoul")
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MARKET_CHARTS = ["us10y", "crude-oil-wti", "crude-oil-brent", "dollar-index", "usd-krw", "bitcoin"]
FINVIZ_SOURCES = ["finviz-index-futures", "finviz-sp500-heatmap", "finviz-russell-heatmap"]
CME_PROBABILITY_SOURCES = ["cme-fedwatch"]
DEFAULT_POLYMARKET_SOURCE = "polymarket-fed-rates"
RUNTIME_COPY_PATTERNS = [
    ("notion", "projects/autopark/runtime/notion/{date}"),
    ("processed", "projects/autopark/data/processed/{date}"),
    ("reviews", "projects/autopark/runtime/reviews/{date}"),
    ("logs", "projects/autopark/runtime/logs/{date}*"),
    ("charts", "projects/autopark/charts/*datawrapper.json"),
    ("prepared", "projects/autopark/prepared/*{date}*"),
    ("exports-current", "projects/autopark/exports/current/*"),
]


def load_env_file(path: Path) -> dict[str, str]:
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


def cdp_available(endpoint: str) -> bool:
    try:
        with urllib.request.urlopen(f"{endpoint.rstrip('/')}/json/version", timeout=5):
            return True
    except (urllib.error.URLError, TimeoutError):
        return False


def default_chrome_path() -> str:
    env_value = os.environ.get("AUTOPARK_CHROME_PATH")
    if env_value:
        return env_value
    candidates = []
    if IS_WINDOWS:
        program_files = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")]
        candidates.extend(
            Path(root) / "Google/Chrome/Application/chrome.exe"
            for root in program_files
            if root
        )
    elif IS_MAC:
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    else:
        for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
            if path := shutil.which(name):
                return path
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "chrome.exe" if IS_WINDOWS else "google-chrome"


def resolve_state_root(env: dict[str, str]) -> Path:
    configured = env.get("AUTOPARK_STATE_ROOT")
    if configured:
        return Path(configured).expanduser()
    return REPO_ROOT / ".server-state" / "autopark"


def launch_chrome_cdp(args: argparse.Namespace, env: dict[str, str], results: list["StepResult"]) -> StepResult:
    started = now_kst()
    monotonic = time.monotonic()
    endpoint = args.cdp_endpoint
    if cdp_available(endpoint):
        ended = now_kst()
        return StepResult(
            "launch chrome cdp profile",
            "ok",
            started.isoformat(timespec="seconds"),
            ended.isoformat(timespec="seconds"),
            round(time.monotonic() - monotonic, 2),
            [],
            0,
            f"already available at {endpoint}",
            [],
        )

    if IS_MAC:
        result, _ = run(["osascript", "-e", 'tell application "Google Chrome" to quit'], "quit chrome before cdp launch", 30, allow_fail=True)
        append_step(results, result)
        result, _ = run(["bash", "projects/autopark/scripts/launch_chrome_cdp_profile.sh"], "launch chrome cdp profile", 90)
        return result

    port = endpoint.rstrip("/").rsplit(":", 1)[-1]
    if "/" in port:
        port = "9222"
    profile_dir = Path(env.get("AUTOPARK_CDP_PROFILE") or resolve_state_root(env) / "profiles" / "chrome-cdp").expanduser()
    profile_dir.mkdir(parents=True, exist_ok=True)
    command = [
        default_chrome_path(),
        f"--remote-debugging-address={env.get('AUTOPARK_CDP_REMOTE_ADDRESS', '127.0.0.1')}",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--profile-directory=Default",
        "--start-maximized",
        "--window-size=1920,1080",
        "--force-device-scale-factor=1",
        env.get("AUTOPARK_START_URL", "https://x.com/wallstengine"),
    ]
    try:
        subprocess.Popen(command, cwd=REPO_ROOT, env=env)
        time.sleep(5)
        status = "ok" if cdp_available(endpoint) else "warn"
        summary = f"started profile at {profile_dir}; endpoint={endpoint}"
        returncode = 0 if status == "ok" else None
    except OSError as exc:
        status = "warn"
        summary = f"unable to start Chrome: {exc}"
        returncode = None
    ended = now_kst()
    return StepResult(
        "launch chrome cdp profile",
        status,
        started.isoformat(timespec="seconds"),
        ended.isoformat(timespec="seconds"),
        round(time.monotonic() - monotonic, 2),
        command,
        returncode,
        summary,
        [],
    )


@dataclass
class StepResult:
    name: str
    status: str
    started_at: str
    ended_at: str
    elapsed_seconds: float
    command: list[str] = field(default_factory=list)
    returncode: int | None = None
    summary: str = ""
    artifacts: list[str] = field(default_factory=list)


def rel(path: str | Path | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    try:
        return str(candidate.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(candidate)


def now_kst() -> datetime:
    return datetime.now(KST)


def flag_enabled(env: dict[str, str], key: str, default: bool = True) -> bool:
    value = env.get(key)
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def compact_command(command: list[str]) -> str:
    return " ".join(command)


def parse_json(stdout: str | None, stderr: str | None = "") -> dict:
    for blob in (stdout, stderr):
        if blob is None:
            continue
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


def run(command: list[str], name: str, timeout: int, allow_fail: bool = False, env: dict[str, str] | None = None) -> tuple[StepResult, dict]:
    started = now_kst()
    monotonic = time.monotonic()
    run_env = {**os.environ, **(env or {})}
    run_env.setdefault("PYTHONUTF8", "1")
    run_env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
            env=run_env,
        )
        elapsed = time.monotonic() - monotonic
        ended = now_kst()
        payload = parse_json(completed.stdout, completed.stderr)
        ok = completed.returncode == 0 or allow_fail
        status = "ok" if completed.returncode == 0 else ("warn" if allow_fail else "fail")
        summary = summarize_payload(payload, completed.stderr)
        return (
            StepResult(
                name=name,
                status=status if ok else "fail",
                started_at=started.isoformat(timespec="seconds"),
                ended_at=ended.isoformat(timespec="seconds"),
                elapsed_seconds=round(elapsed, 2),
                command=command,
                returncode=completed.returncode,
                summary=summary,
                artifacts=extract_artifacts(payload),
            ),
            payload,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - monotonic
        ended = now_kst()
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        payload = parse_json(stdout, stderr)
        return (
            StepResult(
                name=name,
                status="warn" if allow_fail else "fail",
                started_at=started.isoformat(timespec="seconds"),
                ended_at=ended.isoformat(timespec="seconds"),
                elapsed_seconds=round(elapsed, 2),
                command=command,
                returncode=124,
                summary=f"timeout after {timeout}s",
                artifacts=extract_artifacts(payload),
            ),
            payload,
        )


def summarize_payload(payload: dict, stderr: str = "") -> str:
    if not payload:
        return stderr.strip()[:300] if stderr else ""
    if payload.get("page_url"):
        return f"published {payload.get('page_url')}"
    if payload.get("results"):
        first = payload["results"][0] if payload["results"] else {}
        if first.get("url"):
            return f"published {first.get('url')}"
    if payload.get("url"):
        return f"url={payload.get('url')}"
    if payload.get("source_results"):
        source_results = payload["source_results"]
        ok_sources = sum(1 for row in source_results if row.get("status") == "ok")
        if payload.get("candidates") is not None:
            return f"candidates={len(payload.get('candidates', []))}; ok_sources={ok_sources}/{len(source_results)}"
        posts = len(payload.get("posts", []))
        return f"posts={posts}; ok_sources={ok_sources}/{len(source_results)}"
    if payload.get("candidate_count") is not None:
        return f"candidates={payload.get('candidate_count')}"
    if payload.get("cards") is not None:
        return f"cards={len(payload.get('cards', []))}"
    if payload.get("rows") is not None:
        return f"rows={payload.get('rows')}"
    if payload.get("count") is not None:
        return f"count={payload.get('count')}"
    if payload.get("events") is not None:
        return f"events={len(payload.get('events') or [])}"
    if payload.get("fallback") is not None and payload.get("storyline_count") is not None:
        summary = f"fallback={payload.get('fallback')}; storylines={payload.get('storyline_count')}"
        if payload.get("fallback_reason"):
            summary += f"; reason={str(payload.get('fallback_reason'))[:120]}"
        return summary
    if payload.get("fallback") is not None and payload.get("agenda_count") is not None:
        summary = f"fallback={payload.get('fallback')}; agenda={payload.get('agenda_count')}"
        if payload.get("fallback_code"):
            summary += f"; code={payload.get('fallback_code')}"
        if payload.get("fallback_reason"):
            summary += f"; reason={str(payload.get('fallback_reason'))[:120]}"
        return summary
    if payload.get("fallback") is not None and payload.get("focus_count") is not None:
        summary = f"fallback={payload.get('fallback')}; focuses={payload.get('focus_count')}; gaps={payload.get('source_gap_count')}"
        if payload.get("fallback_code"):
            summary += f"; code={payload.get('fallback_code')}"
        if payload.get("fallback_reason"):
            summary += f"; reason={str(payload.get('fallback_reason'))[:120]}"
        return summary
    if payload.get("output"):
        return f"output={rel(payload.get('output'))}"
    if payload.get("markdown_path"):
        return f"markdown={rel(payload.get('markdown_path'))}"
    if payload.get("gate"):
        return f"gate={payload.get('gate')}; format={payload.get('format_score')}; content={payload.get('content_score')}"
    if payload.get("ok") is not None:
        return f"ok={payload.get('ok')}"
    return ""


def extract_artifacts(payload: dict) -> list[str]:
    artifacts: list[str] = []
    for key in ["output", "markdown", "markdown_path", "json_path", "prepared_csv", "spec", "raw_metadata", "json", "markdown_output", "json_output"]:
        if payload.get(key):
            artifacts.append(rel(payload[key]))
    for key in ["datawrapper"]:
        nested = payload.get(key) or {}
        for nested_key in ["prepared_csv", "spec"]:
            if nested.get(nested_key):
                artifacts.append(rel(nested[nested_key]))
    metadata = payload.get("metadata") or {}
    if metadata.get("screenshot_path"):
        artifacts.append(rel(metadata["screenshot_path"]))
    if payload.get("output") and str(payload["output"]).endswith(".png"):
        artifacts.append(rel(payload["output"]))
    return sorted(set(item for item in artifacts if item))


def read_chart_id(spec_path: Path) -> str:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    chart_id = spec.get("chart_id")
    if not chart_id:
        raise RuntimeError(f"Missing chart_id in {spec_path}")
    return chart_id


def append_step(results: list[StepResult], result: StepResult) -> None:
    results.append(result)
    print(json.dumps({"step": result.name, "status": result.status, "seconds": result.elapsed_seconds, "summary": result.summary}, ensure_ascii=False), flush=True)


def render_log(date_value: str, started_at: str, ended_at: str, results: list[StepResult], notion_url: str | None) -> str:
    ok = sum(1 for row in results if row.status == "ok")
    warn = sum(1 for row in results if row.status == "warn")
    fail = sum(1 for row in results if row.status == "fail")
    lines = [
        f"# Autopark Live Run - {date_value}",
        "",
        f"- 시작: `{started_at}`",
        f"- 종료: `{ended_at}`",
        f"- 결과: ok {ok} / warn {warn} / fail {fail}",
    ]
    if notion_url:
        lines.append(f"- Notion: {notion_url}")
    lines.extend(["", "## Steps", "", "| step | status | seconds | summary |", "|---|---:|---:|---|"])
    for row in results:
        summary = row.summary.replace("|", "\\|")
        lines.append(f"| {row.name} | {row.status} | {row.elapsed_seconds:.1f} | {summary} |")
    lines.extend(["", "## Commands", ""])
    for row in results:
        lines.extend([f"### {row.name}", "", "```bash", compact_command(row.command), "```", ""])
    artifacts = [(row.name, artifact) for row in results for artifact in row.artifacts]
    lines.extend(["## Artifacts", ""])
    if artifacts:
        for name, artifact in artifacts:
            lines.append(f"- {name}: `{artifact}`")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def publish_info(payload: dict) -> dict:
    if not payload:
        return {}
    if payload.get("results"):
        first = payload["results"][0] if payload["results"] else {}
        return {
            "status": first.get("status"),
            "page_id": first.get("page_id"),
            "url": first.get("url"),
            "block_count": first.get("block_count"),
            "source": first.get("source"),
            "title": first.get("title"),
        }
    return {
        "status": payload.get("status"),
        "page_id": payload.get("page_id"),
        "url": payload.get("url") or payload.get("page_url"),
        "block_count": payload.get("block_count"),
        "source": payload.get("source"),
        "title": payload.get("title"),
    }


def make_step(name: str, status: str, summary: str, artifacts: list[str] | None = None) -> StepResult:
    now = now_kst().isoformat(timespec="seconds")
    return StepResult(name, status, now, now, 0.0, [], None, summary, artifacts or [])


def cdp_option(endpoint: str | None) -> list[str]:
    return ["--cdp-endpoint", endpoint] if endpoint else []


def auth_profile_option(endpoint: str | None) -> list[str]:
    return [] if endpoint else ["--use-auth-profiles"]


def resolve_probability_sources(args: argparse.Namespace, env: dict[str, str]) -> tuple[list[str], str]:
    sources = list(CME_PROBABILITY_SOURCES)
    policy = (args.polymarket_policy or env.get("AUTOPARK_POLYMARKET_POLICY") or "issue").lower()
    if policy not in {"issue", "always", "never"}:
        policy = "issue"
    configured_source = args.polymarket_source or env.get("AUTOPARK_POLYMARKET_SOURCE")
    if policy == "never":
        return sources, "skipped: polymarket policy is never"
    if policy == "always":
        sources.append(configured_source or DEFAULT_POLYMARKET_SOURCE)
        return sources, f"included by polymarket policy {policy}"
    if configured_source and configured_source != DEFAULT_POLYMARKET_SOURCE:
        sources.append(configured_source)
        return sources, f"included issue-specific polymarket source {configured_source}"
    return sources, "skipped: no issue-specific Polymarket source configured"


def write_post_publish_review(
    date_value: str,
    publish_policy: str,
    review_payload: dict,
    publish_payload: dict,
    dashboard_path: str,
    results: list[StepResult],
) -> tuple[Path, Path]:
    review_dir = PROJECT_ROOT / "runtime" / "reviews" / date_value
    review_dir.mkdir(parents=True, exist_ok=True)
    info = publish_info(publish_payload)
    quality_gate = review_payload.get("gate") or "-"
    format_score = review_payload.get("format_score", "-")
    content_score = review_payload.get("content_score", "-")
    finding_count = review_payload.get("finding_count", "-")
    warnings = [row for row in results if row.status == "warn"]
    failures = [row for row in results if row.status == "fail"]
    published = bool(info.get("url") or info.get("page_id"))
    now = now_kst().strftime("%y.%m.%d %H:%M")
    md_path = review_dir / "post-publish-review.md"
    json_path = review_dir / "post-publish-review.json"
    lines = [
        f"# Autopark Post Publish Review - {date_value}",
        "",
        f"- 리뷰 시각: `{now} (KST)`",
        f"- 발행 정책: `{publish_policy}`",
        f"- 품질 게이트: `{quality_gate}` (format {format_score}, content {content_score}, findings {finding_count})",
        f"- Notion 발행: `{'published' if published else 'skipped'}`",
        f"- Markdown: `{rel(dashboard_path)}`",
    ]
    if info.get("url"):
        lines.append(f"- Notion URL: {info['url']}")
    if info.get("page_id"):
        lines.append(f"- Notion page_id: `{info['page_id']}`")
    if info.get("block_count") is not None:
        lines.append(f"- block count: `{info['block_count']}`")
    lines.extend(["", "## 자체 리뷰", ""])
    if failures:
        lines.append("- 실행 실패가 있어 발행 결과를 신뢰하기 어렵다. 실패 step을 먼저 복구한다.")
    elif quality_gate != "pass":
        lines.append("- 품질 게이트가 pass가 아니므로 자동 발행을 막았다. 리뷰 JSON의 finding을 고친 뒤 재발행한다.")
    elif published:
        lines.append("- 수집, 작성, 품질검토, Notion 발행이 일관된 순서로 완료됐다.")
    else:
        lines.append("- 발행 정책 또는 `--skip-publish` 때문에 Notion 발행은 생략됐고, 로컬 산출물만 보존됐다.")
    if warnings:
        lines.append(f"- 경고 step {len(warnings)}개: " + ", ".join(row.name for row in warnings[:8]))
    else:
        lines.append("- 경고 step 없음.")
    lines.extend(["", "## 다음 확인", ""])
    lines.append("- Notion 페이지에서 이미지 누락 또는 지나친 페이지 길이가 없는지 육안 확인.")
    lines.append("- 실제 PPT가 도착하면 hit / low-ranked hit / miss / false positive 장부를 갱신.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_payload = {
        "ok": not failures,
        "date": date_value,
        "reviewed_at": now,
        "publish_policy": publish_policy,
        "quality_gate": quality_gate,
        "format_score": format_score,
        "content_score": content_score,
        "finding_count": finding_count,
        "published": published,
        "publish": info,
        "dashboard_path": rel(dashboard_path),
        "warn_steps": [row.name for row in warnings],
        "fail_steps": [row.name for row in failures],
        "markdown_output": rel(md_path),
        "json_output": rel(json_path),
    }
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def mirror_runtime_artifacts(date_value: str, env: dict[str, str]) -> tuple[Path, list[str]]:
    state_root = resolve_state_root(env)
    run_root = state_root / "runs" / date_value
    copied: list[str] = []
    for label, raw_pattern in RUNTIME_COPY_PATTERNS:
        target_dir = run_root / label
        pattern = str(REPO_ROOT / raw_pattern.format(date=date_value))
        for match in glob.glob(pattern):
            source = Path(match)
            if not source.exists():
                continue
            if source.is_dir():
                destination = target_dir / source.name
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
                copied.append(str(destination))
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                destination = target_dir / source.name
                shutil.copy2(source, destination)
                copied.append(str(destination))
    manifest = {
        "ok": True,
        "date": date_value,
        "mirrored_at": now_kst().isoformat(timespec="seconds"),
        "state_root": str(state_root),
        "run_root": str(run_root),
        "copied_count": len(copied),
        "copied": copied,
    }
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "mirror-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run_root, copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=now_kst().date().isoformat())
    parser.add_argument("--collected-at", default=None)
    parser.add_argument("--cdp-endpoint", default=None)
    parser.add_argument("--x-profile", default="market_radar")
    parser.add_argument("--news-limit", type=int, default=80)
    parser.add_argument("--x-max-posts", type=int, default=8)
    parser.add_argument("--skip-chrome-launch", action="store_true")
    parser.add_argument("--skip-finviz", action="store_true")
    parser.add_argument("--skip-fed-probabilities", action="store_true")
    parser.add_argument("--polymarket-policy", choices=["issue", "always", "never"], default=None)
    parser.add_argument("--polymarket-source", default=None)
    parser.add_argument("--skip-datawrapper-export", action="store_true")
    parser.add_argument("--preflight-with-web", action="store_true")
    parser.add_argument("--skip-preflight-agenda", action="store_true")
    parser.add_argument("--preflight-response-fixture", type=Path, default=None)
    parser.add_argument("--market-focus-response-fixture", type=Path, default=None)
    parser.add_argument("--synthetic-preflight-smoke", action="store_true")
    parser.add_argument("--synthetic-market-focus-smoke", action="store_true")
    parser.add_argument("--market-focus-with-web", action="store_true")
    parser.add_argument("--skip-market-focus-brief", action="store_true")
    parser.add_argument("--skip-publish", action="store_true")
    parser.add_argument("--publish-policy", choices=["gate", "always", "never"], default=None)
    parser.add_argument("--operation-mode", choices=["auto", "daily_broadcast", "monday_catchup", "no_broadcast"], default="auto")
    parser.add_argument("--broadcast-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--skip-state-mirror", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    file_env = load_env_file(REPO_ROOT / ".env")
    for key, value in file_env.items():
        os.environ.setdefault(key, value)
    run_env = {**os.environ, **file_env}
    use_cdp = str(run_env.get("AUTOPARK_USE_CDP") or "1").lower() not in {"0", "false", "no", "off"}
    args.cdp_endpoint = (args.cdp_endpoint or run_env.get("AUTOPARK_CDP_ENDPOINT") or "http://127.0.0.1:9222") if use_cdp else None
    operation = resolve_operation(args.date, calendar_path=args.broadcast_calendar, requested_mode=args.operation_mode)
    calendar_publish_policy = str(operation.get("publish_policy") or "gate").lower()
    if not operation.get("expected_broadcast") and args.publish_policy is None:
        publish_policy = calendar_publish_policy
    else:
        publish_policy = args.publish_policy or run_env.get("AUTOPARK_PUBLISH_POLICY") or calendar_publish_policy
    publish_policy = publish_policy.lower()
    if publish_policy not in {"gate", "always", "never"}:
        publish_policy = "gate"
    news_lookback = str(int(operation.get("news_lookback_hours") or 24))
    batch_b_lookback = str(int(operation.get("batch_b_lookback_hours") or 36))
    x_lookback = str(int(operation.get("x_lookback_hours") or 24))
    effective_news_limit = max(args.news_limit, int(operation.get("news_limit") or args.news_limit))
    effective_x_max_posts = max(args.x_max_posts, int(operation.get("x_max_posts") or args.x_max_posts))
    run_env["AUTOPARK_OPERATION_MODE"] = str(operation.get("mode") or "daily_broadcast")
    run_env["AUTOPARK_EXPECTED_BROADCAST"] = "1" if operation.get("expected_broadcast") else "0"
    run_env["AUTOPARK_OPERATION_NOTE"] = str(operation.get("note") or "")
    preflight_enabled = flag_enabled(run_env, "AUTOPARK_PREFLIGHT_ENABLED", True) and not args.skip_preflight_agenda
    market_focus_with_web = args.market_focus_with_web or flag_enabled(run_env, "AUTOPARK_MARKET_FOCUS_WITH_WEB_DEFAULT", False)

    py = resolve_python()
    node = resolve_node()
    probability_sources, polymarket_summary = resolve_probability_sources(args, run_env)
    collected_at = args.collected_at or now_kst().strftime("%y.%m.%d %H:%M")
    started_at = now_kst().isoformat(timespec="seconds")
    results: list[StepResult] = []
    notion_url: str | None = None
    publish_payload: dict = {}
    review_payload: dict = {}
    preflight_payload: dict = {}
    market_focus_payload: dict = {}
    editorial_payload: dict = {}

    if args.dry_run:
        planned = [
            "launch chrome cdp",
            "preflight",
            "build market preflight agenda",
            "collect news batch a/b",
            "collect x",
            "build visual cards",
            "capture finviz market images",
            "fetch/publish/export datawrapper charts",
            "build market radar",
            "build market focus brief",
            "build editorial brief",
            "render notion markdown",
            "quality review",
            f"publish notion ({publish_policy})",
            "post-publish review",
            "state mirror",
        ]
        if args.skip_market_focus_brief:
            planned = [step for step in planned if step != "build market focus brief"]
        if not preflight_enabled:
            planned = [step for step in planned if step != "build market preflight agenda"]
        browser_commands = [
            [
                py,
                "projects/autopark/scripts/preflight_0430.py",
                "--date",
                args.date,
            ] + cdp_option(args.cdp_endpoint),
            [
                node,
                "projects/autopark/scripts/collect_x_timeline.mjs",
                "--date",
                args.date,
                "--run-name",
                "x-timeline",
                "--source-profile",
                args.x_profile,
            ] + cdp_option(args.cdp_endpoint),
            [
                node,
                "projects/autopark/scripts/collect_x_timeline.mjs",
                "--date",
                args.date,
                "--run-name",
                "earnings-calendar-x",
                "--source",
                "fixed-earnings-calendar",
            ] + cdp_option(args.cdp_endpoint),
            *([] if args.skip_finviz else [
                [
                    node,
                    "projects/autopark/scripts/capture_source.mjs",
                    "--date",
                    args.date,
                    "--source",
                    source,
                ] + cdp_option(args.cdp_endpoint) + auth_profile_option(args.cdp_endpoint)
                for source in [*FINVIZ_SOURCES, "cnn-fear-greed"]
            ]),
            *[
                [
                    node,
                    "projects/autopark/scripts/capture_source.mjs",
                    "--date",
                    args.date,
                    "--source",
                    source,
                ] + cdp_option(args.cdp_endpoint) + auth_profile_option(args.cdp_endpoint)
                for source in ([] if args.skip_fed_probabilities else probability_sources)
            ],
            *([] if args.skip_finviz else [[
                node,
                "projects/autopark/scripts/capture_finviz_feature_stocks.mjs",
                "--date",
                args.date,
                "--tickers",
                "XLE,CVX,XOM,GOOGL,MSFT,META,AMZN,V,PI,UBER",
            ] + cdp_option(args.cdp_endpoint)]),
        ]
        forbidden_browser_args = {"--profile", "--headed", "--browser-channel"}
        browser_arg_violations = sorted(
            {
                arg
                for command in browser_commands
                for arg in command
                if arg in forbidden_browser_args
            }
        )
        print(
            json.dumps(
                {
                    "ok": not browser_arg_violations,
                    "date": args.date,
                    "planned": planned,
                    "python": py,
                    "node": node,
                    "cdp_endpoint": args.cdp_endpoint,
                    "probability_sources": [] if args.skip_fed_probabilities else probability_sources,
                    "polymarket": polymarket_summary,
                    "operation": operation,
                    "effective": {
                        "publish_policy": publish_policy,
                        "news_lookback_hours": news_lookback,
                        "batch_b_lookback_hours": batch_b_lookback,
                        "x_lookback_hours": x_lookback,
                        "news_limit": effective_news_limit,
                        "x_max_posts": effective_x_max_posts,
                    },
                    "editorial": {
                        "preflight_enabled": preflight_enabled,
                        "preflight_step": "build market preflight agenda" if preflight_enabled else "skipped by flag/env",
                        "preflight_output": str(PROJECT_ROOT / "data" / "processed" / args.date / "market-preflight-agenda.json"),
                        "market_focus_enabled": not args.skip_market_focus_brief,
                        "market_focus_policy": "all-in-one runs by default; use --skip-market-focus-brief only for emergency/debug reruns",
                        "market_focus_step": "build market focus brief" if not args.skip_market_focus_brief else "skipped by flag",
                        "market_focus_output": str(PROJECT_ROOT / "data" / "processed" / args.date / "market-focus-brief.json"),
                        "step": "build editorial brief",
                        "fallback": "unknown_until_run",
                        "output": str(PROJECT_ROOT / "data" / "processed" / args.date / "editorial-brief.json"),
                    },
                    "browser_arg_violations": browser_arg_violations,
                    "browser_commands": browser_commands,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    append_step(
        results,
        make_step(
            "resolve broadcast calendar",
            "ok",
            f"mode={operation.get('mode')}; publish_policy={publish_policy}; note={operation.get('note') or ''}",
        ),
    )

    if not args.skip_chrome_launch:
        result = launch_chrome_cdp(args, run_env, results)
        append_step(results, result)

    result, _ = run(
        [
            py,
            "projects/autopark/scripts/preflight_0430.py",
            "--date",
            args.date,
            "--collected-at",
            collected_at,
            "--timeout",
            "120",
        ] + cdp_option(args.cdp_endpoint),
        "preflight",
        180,
        allow_fail=True,
    )
    append_step(results, result)

    if not preflight_enabled:
        now = now_kst().isoformat(timespec="seconds")
        reason = (
            "--skip-preflight-agenda was set; fixed collection continues without agenda prior."
            if args.skip_preflight_agenda
            else "AUTOPARK_PREFLIGHT_ENABLED disabled the preflight agenda stage; fixed collection continues."
        )
        fallback_code = "preflight_skipped_by_flag" if args.skip_preflight_agenda else "preflight_disabled_by_env"
        preflight_payload = {
            "ok": True,
            "skipped": True,
            "fallback": True,
            "fallback_code": fallback_code,
            "fallback_reason": reason,
            "output": str(PROJECT_ROOT / "data" / "processed" / args.date / "market-preflight-agenda.json"),
        }
        result = StepResult(
            "build market preflight agenda",
            "warn",
            now,
            now,
            0.0,
            [],
            None,
            reason,
            [],
        )
    else:
        preflight_command = [py, "projects/autopark/scripts/build_market_preflight_agenda.py", "--date", args.date]
        if args.preflight_with_web:
            preflight_command.append("--with-web")
        if args.preflight_response_fixture:
            preflight_command.extend(["--response-fixture", str(args.preflight_response_fixture)])
        if args.synthetic_preflight_smoke:
            preflight_command.append("--synthetic-smoke")
        preflight_command.extend(["--prompt-output", f"projects/autopark/runtime/openai-prompts/{args.date}-market-preflight-prompt.json"])
        result, preflight_payload = run(
            preflight_command,
            "build market preflight agenda",
            180,
            allow_fail=True,
            env=run_env,
        )
    append_step(results, result)

    for batch_name, extra in [
        ("collect news batch a", []),
        ("collect news batch b", ["--batch-b-default"]),
    ]:
        command = [
            py,
            "projects/autopark/scripts/collect_today_misc.py",
            "--date",
            args.date,
            "--run-name",
            "today-misc-batch-a" if not extra else "today-misc-batch-b",
            "--overall-limit",
            str(effective_news_limit),
            "--limit-per-source",
            "15" if not extra else "12",
            "--lookback-hours",
            news_lookback if not extra else batch_b_lookback,
        ] + extra
        result, _ = run(command, batch_name, args.timeout, allow_fail=True)
        append_step(results, result)

    result, _ = run(
        [
            node,
            "projects/autopark/scripts/collect_x_timeline.mjs",
            "--date",
            args.date,
            "--run-name",
            "x-timeline",
            "--source-profile",
            args.x_profile,
            "--max-posts",
            str(effective_x_max_posts),
            "--lookback-hours",
            x_lookback,
            "--scrolls",
            "4" if int(x_lookback) > 24 else "2",
        ] + cdp_option(args.cdp_endpoint),
        "collect x timeline",
        args.timeout,
        allow_fail=True,
    )
    append_step(results, result)

    result, _ = run(
        [
            node,
            "projects/autopark/scripts/collect_x_timeline.mjs",
            "--date",
            args.date,
            "--run-name",
            "earnings-calendar-x",
            "--source",
            "fixed-earnings-calendar",
            "--max-posts",
            "4",
            "--lookback-hours",
            "168",
            "--scrolls",
            "3",
            "--min-text-length",
            "10",
        ] + cdp_option(args.cdp_endpoint),
        "collect earnings calendar x",
        args.timeout,
        allow_fail=True,
    )
    append_step(results, result)

    result, _ = run(
        [
            py,
            "projects/autopark/scripts/parse_earnings_calendar_tickers.py",
            "--date",
            args.date,
            "--input",
            f"projects/autopark/data/processed/{args.date}/earnings-calendar-x-posts.json",
        ],
        "parse earnings calendar tickers",
        90,
        allow_fail=True,
    )
    append_step(results, result)

    result, _ = run([py, "projects/autopark/scripts/build_visual_cards.py", "--date", args.date], "build visual cards", 120, allow_fail=True)
    append_step(results, result)

    if not args.skip_finviz:
        if args.cdp_endpoint:
            result = make_step("sync finviz chrome profile", "ok", "using shared Autopark CDP Chrome profile")
        elif IS_MAC:
            result, _ = run(
                ["bash", "projects/autopark/scripts/sync_chrome_profile_for_playwright.sh"],
                "sync finviz chrome profile",
                120,
                allow_fail=True,
            )
        else:
            result = make_step("sync finviz chrome profile", "ok", "using server-local persistent Playwright profile")
        append_step(results, result)
        for source in FINVIZ_SOURCES:
            result, _ = run(
                [
                    node,
                    "projects/autopark/scripts/capture_source.mjs",
                    "--date",
                    args.date,
                    "--source",
                    source,
                ] + cdp_option(args.cdp_endpoint) + auth_profile_option(args.cdp_endpoint),
                f"capture {source}",
                args.timeout,
                allow_fail=True,
            )
            append_step(results, result)
        result, _ = run(
            [
                node,
                "projects/autopark/scripts/capture_source.mjs",
                "--date",
                args.date,
                "--source",
                "cnn-fear-greed",
            ] + cdp_option(args.cdp_endpoint) + auth_profile_option(args.cdp_endpoint),
            "capture cnn-fear-greed",
            args.timeout,
            allow_fail=True,
        )
        append_step(results, result)

    if args.skip_fed_probabilities:
        append_step(results, make_step("capture fed probability sources", "warn", "skipped by --skip-fed-probabilities"))
    else:
        for source in probability_sources:
            result, _ = run(
                [
                    node,
                    "projects/autopark/scripts/capture_source.mjs",
                    "--date",
                    args.date,
                    "--source",
                    source,
                    "--timeout-ms",
                    "45000",
                ] + cdp_option(args.cdp_endpoint) + auth_profile_option(args.cdp_endpoint),
                f"capture {source}",
                args.timeout,
                allow_fail=True,
            )
            append_step(results, result)
        if DEFAULT_POLYMARKET_SOURCE not in probability_sources and not any(source.startswith("polymarket-") for source in probability_sources):
            append_step(results, make_step("capture polymarket", "warn", polymarket_summary))

    result, fedwatch_split_payload = run(
        [py, "projects/autopark/scripts/prepare_fedwatch_datawrapper_splits.py", "--date", args.date],
        "prepare fedwatch datawrapper splits",
        60,
        allow_fail=True,
    )
    append_step(results, result)
    if result.status != "ok":
        append_step(results, make_step("publish/export fedwatch split datawrapper", "warn", "skipped because split preparation failed"))
    elif not args.skip_datawrapper_export:
        for fedwatch_slug in ["fedwatch-conditional-probabilities-short-term", "fedwatch-conditional-probabilities-long-term"]:
            spec_path = PROJECT_ROOT / "charts" / f"{fedwatch_slug}-datawrapper.json"
            result, _ = run([py, "scripts/datawrapper_publish.py", str(spec_path)], f"publish datawrapper {fedwatch_slug}", 120, allow_fail=True, env=run_env)
            append_step(results, result)
            try:
                chart_id = read_chart_id(spec_path)
                result, _ = run(
                    [
                        py,
                        "scripts/datawrapper_export_png.py",
                        chart_id,
                        str(PROJECT_ROOT / "exports/current" / f"{fedwatch_slug}.png"),
                        "--brand-logo",
                        "--logo-max-height-px",
                        "64",
                    ],
                    f"export png {fedwatch_slug}",
                    120,
                    allow_fail=True,
                    env=run_env,
                )
            except Exception as exc:  # noqa: BLE001
                now = now_kst().isoformat(timespec="seconds")
                result = StepResult(f"export png {fedwatch_slug}", "warn", now, now, 0.0, [], None, str(exc), [])
            append_step(results, result)

    for chart in MARKET_CHARTS:
        result, _ = run(
            [
                py,
                "projects/autopark/scripts/fetch_market_chart_data.py",
                "--date",
                args.date,
                "--chart",
                chart,
                "--collected-at",
                collected_at,
            ],
            f"fetch chart {chart}",
            90,
            allow_fail=True,
        )
        append_step(results, result)
        if not args.skip_datawrapper_export:
            spec_path = PROJECT_ROOT / "charts" / f"{chart}-datawrapper.json"
            result, _ = run([py, "scripts/datawrapper_publish.py", str(spec_path)], f"publish datawrapper {chart}", 120, allow_fail=True, env=run_env)
            append_step(results, result)
            try:
                chart_id = read_chart_id(spec_path)
                result, _ = run(
                    [
                        py,
                        "scripts/datawrapper_export_png.py",
                        chart_id,
                        str(PROJECT_ROOT / "exports/current" / f"{chart}.png"),
                        "--brand-logo",
                        "--logo-max-height-px",
                        "72",
                    ],
                    f"export png {chart}",
                    120,
                    allow_fail=True,
                    env=run_env,
                )
            except Exception as exc:  # noqa: BLE001
                now = now_kst().isoformat(timespec="seconds")
                result = StepResult(f"export png {chart}", "warn", now, now, 0.0, [], None, str(exc), [])
            append_step(results, result)

    result, _ = run(
        [
            py,
            "projects/autopark/scripts/fetch_economic_calendar.py",
            "--date",
            args.date,
            "--min-importance",
            "2",
            "--limit",
            "10",
            "--collected-at",
            collected_at,
        ],
        "fetch economic calendar",
        90,
        allow_fail=True,
    )
    append_step(results, result)
    if not args.skip_datawrapper_export:
        for calendar_slug in ["economic-calendar-us", "economic-calendar-global"]:
            spec_path = PROJECT_ROOT / "charts" / f"{calendar_slug}-datawrapper.json"
            result, _ = run([py, "scripts/datawrapper_publish.py", str(spec_path)], f"publish datawrapper {calendar_slug}", 120, allow_fail=True, env=run_env)
            append_step(results, result)
            try:
                chart_id = read_chart_id(spec_path)
                result, _ = run(
                    [
                        py,
                        "scripts/datawrapper_export_png.py",
                        chart_id,
                        str(PROJECT_ROOT / "exports/current" / f"{calendar_slug}.png"),
                        "--brand-logo",
                        "--logo-max-height-px",
                        "64",
                    ],
                    f"export png {calendar_slug}",
                    120,
                    allow_fail=True,
                    env=run_env,
                )
            except Exception as exc:  # noqa: BLE001
                now = now_kst().isoformat(timespec="seconds")
                result = StepResult(f"export png {calendar_slug}", "warn", now, now, 0.0, [], None, str(exc), [])
            append_step(results, result)

    result, _ = run(
        [
            py,
            "projects/autopark/scripts/build_market_radar.py",
            "--date",
            args.date,
            "--limit-news",
            "120",
            "--limit-x",
            "120",
            "--limit-visuals",
            "60",
        ],
        "build market radar",
        120,
        allow_fail=True,
    )
    append_step(results, result)

    if args.skip_market_focus_brief:
        now = now_kst().isoformat(timespec="seconds")
        market_focus_payload = {
            "ok": True,
            "skipped": True,
            "fallback": True,
            "fallback_code": "market_focus_skipped_by_flag",
            "fallback_reason": "--skip-market-focus-brief was set; editorial brief may use existing market-focus-brief.json if present.",
            "output": str(PROJECT_ROOT / "data" / "processed" / args.date / "market-focus-brief.json"),
        }
        result = StepResult(
            "build market focus brief",
            "warn",
            now,
            now,
            0.0,
            [],
            None,
            market_focus_payload["fallback_reason"],
            [],
        )
    else:
        market_focus_command = [py, "projects/autopark/scripts/build_market_focus_brief.py", "--date", args.date]
        if market_focus_with_web:
            market_focus_command.append("--with-web")
        if args.market_focus_response_fixture:
            market_focus_command.extend(["--response-fixture", str(args.market_focus_response_fixture)])
        if args.synthetic_market_focus_smoke:
            market_focus_command.append("--synthetic-smoke")
        market_focus_command.extend(["--prompt-output", f"projects/autopark/runtime/openai-prompts/{args.date}-market-focus-prompt.json"])
        result, market_focus_payload = run(
            market_focus_command,
            "build market focus brief",
            240,
            allow_fail=True,
            env=run_env,
        )
    append_step(results, result)

    result, editorial_payload = run(
        [py, "projects/autopark/scripts/build_editorial_brief.py", "--date", args.date],
        "build editorial brief",
        180,
        allow_fail=True,
        env=run_env,
    )
    append_step(results, result)

    result, _ = run(
        [py, "projects/autopark/scripts/build_earnings_ticker_drilldown.py", "--date", args.date],
        "build earnings ticker drilldown",
        120,
        allow_fail=True,
    )
    append_step(results, result)

    if not args.skip_finviz:
        result, _ = run(
            [
                node,
                "projects/autopark/scripts/capture_finviz_feature_stocks.mjs",
                "--date",
                args.date,
                "--tickers",
                "XLE,CVX,XOM,GOOGL,MSFT,META,AMZN,V,PI,UBER",
            ] + cdp_option(args.cdp_endpoint),
            "capture finviz feature stocks",
            max(args.timeout, 180),
            allow_fail=True,
        )
        append_step(results, result)

        result, _ = run(
            [py, "projects/autopark/scripts/build_earnings_ticker_drilldown.py", "--date", args.date],
            "rebuild earnings ticker drilldown",
            120,
            allow_fail=True,
        )
        append_step(results, result)

    result, dashboard_payload = run([py, "projects/autopark/scripts/build_live_notion_dashboard.py", "--date", args.date], "build notion markdown", 90)
    append_step(results, result)
    dashboard_path = dashboard_payload.get("output") or str(PROJECT_ROOT / "runtime/notion" / args.date / f"{datetime.fromisoformat(args.date).strftime('%y.%m.%d')}.md")

    result, review_payload = run([py, "projects/autopark/scripts/review_dashboard_quality.py", "--date", args.date, "--json"], "review dashboard quality", 90, allow_fail=True)
    append_step(results, result)

    should_publish = (
        not args.skip_publish
        and publish_policy != "never"
        and (publish_policy == "always" or review_payload.get("gate") == "pass")
    )
    if should_publish:
        result, publish_payload = run(
            [py, "projects/autopark/scripts/publish_recon_to_notion.py", "--replace-existing", dashboard_path],
            "publish notion",
            240,
        )
        append_step(results, result)
        if isinstance(publish_payload, list) and publish_payload:
            notion_url = publish_payload[0].get("url")
        elif isinstance(publish_payload, dict):
            notion_url = publish_payload.get("url") or publish_payload.get("page_url")
            if not notion_url and publish_payload.get("results"):
                notion_url = publish_payload["results"][0].get("url")
    else:
        if args.skip_publish:
            reason = "--skip-publish"
        elif publish_policy == "never":
            reason = "AUTOPARK_PUBLISH_POLICY=never"
        else:
            reason = f"quality gate is {review_payload.get('gate', 'unknown')}"
        result = make_step("publish notion", "warn", f"skipped: {reason}")
        append_step(results, result)

    review_md, review_json = write_post_publish_review(
        args.date,
        publish_policy,
        review_payload,
        publish_payload,
        dashboard_path,
        results,
    )
    append_step(
        results,
        make_step(
            "post-publish review",
            "ok",
            f"markdown={rel(review_md)}",
            [rel(review_md), rel(review_json)],
        ),
    )

    ended_at = now_kst().isoformat(timespec="seconds")
    log_dir = PROJECT_ROOT / "runtime/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    md_path = log_dir / f"{args.date}-live-all-in-one.md"
    json_path = log_dir / f"{args.date}-live-all-in-one.json"
    md_path.write_text(render_log(args.date, started_at, ended_at, results, notion_url), encoding="utf-8")
    state_mirror = {}
    if not args.skip_state_mirror:
        try:
            run_root, copied = mirror_runtime_artifacts(args.date, run_env)
            state_mirror = {"run_root": str(run_root), "copied_count": len(copied)}
            append_step(results, make_step("state mirror", "ok", f"{len(copied)} files copied to {run_root}", [str(run_root / "mirror-manifest.json")]))
        except Exception as exc:  # noqa: BLE001
            state_mirror = {"error": str(exc)}
            append_step(results, make_step("state mirror", "warn", f"mirror failed: {exc}"))
    else:
        append_step(results, make_step("state mirror", "warn", "skipped by --skip-state-mirror"))

    md_path.write_text(render_log(args.date, started_at, ended_at, results, notion_url), encoding="utf-8")
    payload = {
        "ok": not any(row.status == "fail" for row in results),
        "date": args.date,
        "started_at": started_at,
        "ended_at": ended_at,
        "notion_url": notion_url,
        "publish_policy": publish_policy,
        "operation": operation,
        "preflight_agenda": {
            "enabled": preflight_enabled,
            "skipped": bool(preflight_payload.get("skipped")),
            "fallback": bool(preflight_payload.get("fallback")),
            "fallback_code": preflight_payload.get("fallback_code"),
            "fallback_reason": preflight_payload.get("fallback_reason"),
            "model": preflight_payload.get("model"),
            "with_web": bool(preflight_payload.get("with_web")),
            "agenda_count": preflight_payload.get("agenda_count"),
            "output": preflight_payload.get("output"),
            "markdown_output": preflight_payload.get("markdown_output"),
        },
        "market_focus": {
            "enabled": not args.skip_market_focus_brief,
            "skipped": bool(market_focus_payload.get("skipped")),
            "fallback": bool(market_focus_payload.get("fallback")),
            "fallback_code": market_focus_payload.get("fallback_code"),
            "fallback_reason": market_focus_payload.get("fallback_reason"),
            "model": market_focus_payload.get("model"),
            "with_web": bool(market_focus_payload.get("with_web")),
            "focus_count": market_focus_payload.get("focus_count"),
            "source_gap_count": market_focus_payload.get("source_gap_count"),
            "output": market_focus_payload.get("output"),
            "markdown_output": market_focus_payload.get("markdown_output"),
        },
        "editorial_fallback": bool(editorial_payload.get("fallback")),
        "editorial": {
            "fallback": bool(editorial_payload.get("fallback")),
            "fallback_reason": editorial_payload.get("fallback_reason"),
            "model": editorial_payload.get("model"),
            "storyline_count": editorial_payload.get("storyline_count"),
            "output": editorial_payload.get("output"),
        },
        "quality_gate": review_payload.get("gate"),
        "publish": publish_info(publish_payload),
        "state_mirror": state_mirror,
        "markdown_log": rel(md_path),
        "json_log": rel(json_path),
        "steps": [row.__dict__ for row in results],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if state_mirror.get("run_root"):
        final_log_dir = Path(state_mirror["run_root"]) / "logs"
        final_log_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(md_path, final_log_dir / md_path.name)
        shutil.copy2(json_path, final_log_dir / json_path.name)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
