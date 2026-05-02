#!/usr/bin/env python3
"""Fetch the post-live Korean YouTube transcript for Wepoll morning streams."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DEFAULT_CHANNEL_URL = "https://www.youtube.com/@wepoll_original/streams"


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return env


@dataclass(frozen=True)
class Segment:
    start_seconds: int
    end_seconds: int | None
    text: str


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact(value: object, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def yt_dlp_command(explicit: str | None = None) -> list[str]:
    if explicit:
        return [explicit]
    found = shutil.which("yt-dlp")
    if found:
        return [found]
    return [sys.executable, "-m", "yt_dlp"]


def run_json(cmd: list[str], timeout: int) -> dict:
    completed = subprocess.run(
        cmd,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=subprocess_env(),
        capture_output=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"command failed: {' '.join(cmd)}")
    text = completed.stdout.strip()
    if not text:
        return {}
    return json.loads(text)


def run_command(cmd: list[str], timeout: int) -> tuple[int, str, str]:
    completed = subprocess.run(
        cmd,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=subprocess_env(),
        capture_output=True,
        timeout=timeout,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def seconds_from_timestamp(value: str) -> float:
    raw = value.strip().replace(",", ".")
    parts = raw.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def clean_caption_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d+>", " ", text)
    text = re.sub(r"</?c(?:\.[^>]+)?>|</?v[^>]*>|</?i>|</?b>|</?u>|<ruby>|</ruby>|<rt>|</rt>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text.replace("\u200b", " ")).strip()


def parse_vtt(path: Path) -> list[Segment]:
    segments: list[Segment] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if "-->" not in line:
            index += 1
            continue
        start_raw, end_raw = [part.strip().split(" ", 1)[0] for part in line.split("-->", 1)]
        text_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            cleaned = clean_caption_text(lines[index])
            if cleaned:
                text_lines.append(cleaned)
            index += 1
        text = clean_caption_text(" ".join(text_lines))
        if text:
            segments.append(
                Segment(
                    start_seconds=int(seconds_from_timestamp(start_raw)),
                    end_seconds=int(seconds_from_timestamp(end_raw)),
                    text=text,
                )
            )
        index += 1
    return dedupe_segments(segments)


def parse_srt(path: Path) -> list[Segment]:
    segments: list[Segment] = []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="replace"))
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        time_line = next((line for line in lines if "-->" in line), "")
        if not time_line:
            continue
        start_raw, end_raw = [part.strip().split(" ", 1)[0] for part in time_line.split("-->", 1)]
        text = clean_caption_text(" ".join(line for line in lines if line != time_line and not line.isdigit()))
        if text:
            segments.append(
                Segment(
                    start_seconds=int(seconds_from_timestamp(start_raw)),
                    end_seconds=int(seconds_from_timestamp(end_raw)),
                    text=text,
                )
            )
    return dedupe_segments(segments)


def merge_overlap(previous: str, current: str) -> str:
    previous = clean_caption_text(previous)
    current = clean_caption_text(current)
    if not previous:
        return current
    if not current or current in previous:
        return previous
    if previous in current:
        return current
    for size in range(min(len(previous), len(current)), 4, -1):
        if previous[-size:] == current[:size]:
            return clean_caption_text(previous + current[size:])
    return f"{previous} {current}"


def dedupe_segments(segments: list[Segment]) -> list[Segment]:
    cleaned: list[Segment] = []
    last_start: int | None = None
    for segment in segments:
        text = clean_caption_text(segment.text)
        if not text:
            continue
        if not cleaned or last_start is None or segment.start_seconds - last_start > 35:
            cleaned.append(Segment(segment.start_seconds, segment.end_seconds, text))
            last_start = segment.start_seconds
            continue
        merged = merge_overlap(cleaned[-1].text, text)
        if merged == cleaned[-1].text:
            last_start = segment.start_seconds
            continue
        if len(merged) <= 520:
            cleaned[-1] = Segment(cleaned[-1].start_seconds, segment.end_seconds, merged)
        else:
            cleaned.append(Segment(segment.start_seconds, segment.end_seconds, text))
        last_start = segment.start_seconds
    return cleaned


def load_segments(path: Path) -> list[Segment]:
    if path.suffix.lower() == ".srt":
        return parse_srt(path)
    return parse_vtt(path)


def format_timestamp(seconds: int) -> str:
    minutes, sec = divmod(max(0, int(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def transcript_markdown(target_date: str, meta: dict, segments: list[Segment], host_minutes: int) -> str:
    lines = [
        f"# Wepoll Morning Transcript - {target_date}",
        "",
        f"- video_id: `{meta.get('id') or '-'}`",
        f"- title: {meta.get('title') or '-'}",
        f"- url: {meta.get('webpage_url') or meta.get('original_url') or '-'}",
        f"- host window: `00:00-{host_minutes:02d}:00`",
        "",
        "## 진행자 구간",
        "",
    ]
    for segment in segments:
        lines.append(f"- `{format_timestamp(segment.start_seconds)}` {segment.text}")
    return "\n".join(lines).rstrip() + "\n"


def normalize_upload_date(value: object) -> str:
    text = str(value or "")
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def select_video(entries: list[dict], target_date: str, *, allow_nearest: bool = False) -> dict | None:
    dated = []
    fallback = []
    compact_target = target_date.replace("-", "")
    for entry in entries:
        video_id = entry.get("id")
        if not video_id:
            continue
        upload_date = str(entry.get("upload_date") or "")
        live_status = str(entry.get("live_status") or "")
        item = {**entry, "upload_date_normalized": normalize_upload_date(upload_date)}
        if upload_date == compact_target:
            dated.append(item)
        if live_status not in {"is_upcoming", "is_live"}:
            fallback.append(item)
    if dated:
        return dated[0]
    if allow_nearest and fallback:
        return fallback[0]
    return None


def list_streams(channel_url: str, command: list[str], limit: int, timeout: int) -> dict:
    cmd = [
        *command,
        "--dump-single-json",
        "--flat-playlist",
        "--playlist-end",
        str(limit),
        "--no-warnings",
        channel_url,
    ]
    return run_json(cmd, timeout)


def fetch_video_meta(video_url: str, command: list[str], timeout: int) -> dict:
    cmd = [*command, "--dump-single-json", "--skip-download", "--no-warnings", video_url]
    return run_json(cmd, timeout)


def subtitle_files(output_dir: Path, video_id: str) -> list[Path]:
    return sorted(output_dir.glob(f"*__{video_id}__*.ko.vtt")) + sorted(output_dir.glob(f"*__{video_id}__*.ko.srt"))


def download_subtitles(video_url: str, video_id: str, output_dir: Path, command: list[str], timeout: int) -> tuple[list[Path], str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(output_dir / f"%(upload_date>%Y-%m-%d)s__{video_id}__%(title).80s")
    modes = [
        ["--write-sub"],
        ["--write-auto-sub"],
    ]
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    for flags in modes:
        cmd = [
            *command,
            video_url,
            "-o",
            out_tmpl,
            "--skip-download",
            "--ignore-no-formats-error",
            *flags,
            "--sub-langs",
            "ko",
            "--sub-format",
            "vtt/srt/best",
            "--write-info-json",
            "--ignore-errors",
            "--no-warnings",
            "--retries",
            "3",
            "--sleep-requests",
            "1",
            "--sleep-subtitles",
            "1",
        ]
        returncode, stdout, stderr = run_command(cmd, timeout)
        stdout_parts.append(stdout)
        stderr_parts.append(stderr)
        files = subtitle_files(output_dir, video_id)
        if files:
            return files, "\n".join(stdout_parts), "\n".join(stderr_parts)
        if returncode != 0 and "requested format is not available" not in stderr.lower():
            continue
    return subtitle_files(output_dir, video_id), "\n".join(stdout_parts), "\n".join(stderr_parts)


def clear_stale_outputs(*paths: Path) -> None:
    for path in paths:
        try:
            if path.exists() and path.is_file():
                path.unlink()
        except OSError:
            continue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--channel-url", default=DEFAULT_CHANNEL_URL)
    parser.add_argument("--video-url", help="Use a specific YouTube video URL instead of scanning the streams page.")
    parser.add_argument("--video-id", help="Use a specific YouTube video id.")
    parser.add_argument("--allow-nearest", action="store_true", help="If no stream matches --date, use the newest finished stream anyway.")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--host-minutes", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=RUNTIME_DIR / "broadcast")
    parser.add_argument("--yt-dlp", default=None, help="Explicit yt-dlp executable path.")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--env", type=Path, default=REPO_ROOT / ".env")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    command = yt_dlp_command(args.yt_dlp or env.get("AUTOPARK_YT_DLP"))
    day_dir = args.output_dir / args.date
    raw_dir = day_dir / "youtube"
    result_path = day_dir / "wepoll-transcript.json"
    md_path = day_dir / "host-segment.md"

    if args.video_url:
        video_url = args.video_url
    elif args.video_id:
        video_url = f"https://www.youtube.com/watch?v={args.video_id}"
    else:
        video_url = ""

    if args.dry_run:
        payload = {
            "ok": True,
            "status": "dry-run",
            "date": args.date,
            "channel_url": args.channel_url,
            "video_url": video_url or None,
            "command": command,
            "output_dir": str(day_dir),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        if not video_url:
            stream_info = list_streams(args.channel_url, command, args.max_results, args.timeout)
            selected = select_video(stream_info.get("entries") or [], args.date, allow_nearest=args.allow_nearest)
            if not selected:
                clear_stale_outputs(md_path)
                payload = {
                    "ok": True,
                    "status": "video_not_found",
                    "date": args.date,
                    "checked_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
                    "channel_url": args.channel_url,
                    "message": "No stream on the channel page matched the target upload date. Retry later or pass --video-url.",
                }
                write_json(result_path, payload)
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0
            video_url = selected.get("url") or selected.get("webpage_url") or f"https://www.youtube.com/watch?v={selected['id']}"
            if not video_url.startswith("http"):
                video_url = f"https://www.youtube.com/watch?v={video_url}"

        meta = fetch_video_meta(video_url, command, args.timeout)
        video_id = str(meta.get("id") or args.video_id or "").strip()
        if not video_id:
            raise RuntimeError("video_id_not_found")
        files, stdout, stderr = download_subtitles(video_url, video_id, raw_dir, command, args.timeout)
        if not files:
            clear_stale_outputs(md_path)
            payload = {
                "ok": True,
                "status": "transcript_unavailable",
                "date": args.date,
                "checked_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
                "video_id": video_id,
                "video_url": video_url,
                "title": meta.get("title"),
                "stdout_tail": compact(stdout, 1000),
                "stderr_tail": compact(stderr, 1000),
                "message": "Korean subtitles are not available yet. Retry later.",
            }
            write_json(result_path, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        subtitle_path = files[0]
        all_segments = load_segments(subtitle_path)
        cutoff = max(1, args.host_minutes) * 60
        host_segments = [segment for segment in all_segments if segment.start_seconds < cutoff]
        md_path.write_text(transcript_markdown(args.date, meta, host_segments, args.host_minutes), encoding="utf-8")
        payload = {
            "ok": True,
            "status": "downloaded",
            "date": args.date,
            "checked_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "video_id": video_id,
            "video_url": video_url,
            "title": meta.get("title"),
            "upload_date": normalize_upload_date(meta.get("upload_date")),
            "subtitle_path": str(subtitle_path),
            "host_segment_markdown": str(md_path),
            "segment_count": len(all_segments),
            "host_segment_count": len(host_segments),
            "host_minutes": args.host_minutes,
            "segments": [asdict(segment) for segment in host_segments],
        }
        write_json(result_path, payload)
        print(json.dumps({k: payload[k] for k in payload if k != "segments"}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        payload = {
            "ok": False,
            "status": "error",
            "date": args.date,
            "checked_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "error": f"{type(exc).__name__}: {exc}",
            "command": command,
        }
        write_json(result_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
