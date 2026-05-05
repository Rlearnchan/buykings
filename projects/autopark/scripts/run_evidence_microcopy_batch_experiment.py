#!/usr/bin/env python3
"""Prepare, submit, and inspect OpenAI Batch experiments for evidence microcopy.

The default mode is non-mutating to OpenAI: it only writes a JSONL request file
and a local manifest under data/processed/<date>/experiments/.
Use --submit to upload and create a Batch API job.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_evidence_microcopy import (
    DEFAULT_ENV,
    DEFAULT_GROUP_SIZE,
    DEFAULT_MODEL,
    EVIDENCE_MICROCOPY_RESPONSE_SCHEMA,
    OPENAI_API,
    build_prompt,
    chunked,
    group_size_from,
    load_env,
    microcopy_source_items,
    write_json,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
FILES_API = "https://api.openai.com/v1/files"
BATCHES_API = "https://api.openai.com/v1/batches"


def now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def estimate_prompt_tokens(prompt: str) -> int:
    return max(1, int((len(prompt or "") + 3) / 4))


def batch_request_body(prompt: str, model: str) -> dict:
    return {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_evidence_microcopy",
                "strict": True,
                "schema": EVIDENCE_MICROCOPY_RESPONSE_SCHEMA,
            }
        },
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def prepare_batch_payload(target_date: str, model: str, limit: int, llm_limit: int, group_size: int) -> tuple[list[dict], dict]:
    items, source_counts = microcopy_source_items(target_date, limit)
    llm_items = items[: max(0, min(len(items), llm_limit))]
    rows: list[dict] = []
    group_stats: list[dict] = []
    groups = list(chunked(llm_items, group_size))
    for index, group in enumerate(groups, start=1):
        prompt = build_prompt(target_date, group)
        custom_id = f"evidence-{target_date}-g{len(group):02d}-{index:03d}"
        rows.append(
            {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": batch_request_body(prompt, model),
            }
        )
        group_stats.append(
            {
                "custom_id": custom_id,
                "group_index": index,
                "item_count": len(group),
                "prompt_chars": len(prompt),
                "estimated_prompt_tokens": estimate_prompt_tokens(prompt),
            }
        )
    manifest = {
        "ok": True,
        "date": target_date,
        "model": model,
        "created_at": now_iso(),
        "endpoint": "/v1/responses",
        "completion_window": "24h",
        "limit": limit,
        "llm_limit": llm_limit,
        "group_size": group_size,
        "source_item_count": len(items),
        "llm_item_count": len(llm_items),
        "request_count": len(rows),
        **source_counts,
        "groups": group_stats,
    }
    return rows, manifest


def multipart_upload(path: Path, token: str) -> dict:
    boundary = f"autopark-{int(time.time() * 1000)}"
    file_bytes = path.read_bytes()
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n".encode("utf-8"),
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            "Content-Type: application/jsonl\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    request = urllib.request.Request(
        FILES_API,
        data=b"".join(parts),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=None) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, token: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=None) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=None) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(url: str, token: str) -> bytes:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=None) as response:
        return response.read()


def submit_batch(input_path: Path, token: str) -> dict:
    uploaded = multipart_upload(input_path, token)
    batch = post_json(
        BATCHES_API,
        token,
        {
            "input_file_id": uploaded["id"],
            "endpoint": "/v1/responses",
            "completion_window": "24h",
            "metadata": {
                "project": "autopark",
                "experiment": "evidence_microcopy_latency",
            },
        },
    )
    return {"uploaded_file": uploaded, "batch": batch}


def retrieve_batch(batch_id: str, token: str, output_dir: Path) -> dict:
    batch = get_json(f"{BATCHES_API}/{batch_id}", token)
    saved: dict[str, str] = {}
    for field, name in [("output_file_id", "output.jsonl"), ("error_file_id", "errors.jsonl")]:
        file_id = batch.get(field)
        if not file_id:
            continue
        content = get_bytes(f"{FILES_API}/{file_id}/content", token)
        path = output_dir / name
        path.write_bytes(content)
        saved[field] = str(path)
    return {"batch": batch, "saved_files": saved, "retrieved_at": now_iso()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--llm-limit", type=int, default=30)
    parser.add_argument("--group-size", type=int, default=DEFAULT_GROUP_SIZE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--retrieve", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    model = args.model or env.get("AUTOPARK_EVIDENCE_MICROCOPY_MODEL") or DEFAULT_MODEL
    group_size = group_size_from(args.group_size)
    output_dir = args.output_dir or (PROCESSED_DIR / args.date / "experiments" / f"evidence-batch-{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    existing_manifest = {}
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_manifest = {}

    rows, manifest = prepare_batch_payload(args.date, model, args.limit, args.llm_limit, group_size)
    input_path = output_dir / "input.jsonl"
    write_jsonl(input_path, rows)
    if existing_manifest:
        manifest.update(
            {
                key: existing_manifest[key]
                for key in ["submission", "submitted_at", "retrieval_history"]
                if key in existing_manifest
            }
        )
    manifest["input_jsonl"] = str(input_path)
    manifest["manifest_path"] = str(manifest_path)

    token = env.get("OPENAI_API_KEY") or ""
    if args.submit:
        if not token:
            raise RuntimeError("missing_openai_api_key")
        manifest["submission"] = submit_batch(input_path, token)
        manifest["submitted_at"] = now_iso()

    if args.batch_id or (args.retrieve and (manifest.get("submission") or {}).get("batch", {}).get("id")):
        if not token:
            raise RuntimeError("missing_openai_api_key")
        batch_id = args.batch_id or manifest["submission"]["batch"]["id"]
        retrieval = retrieve_batch(batch_id, token, output_dir)
        manifest["retrieval"] = retrieval
        history = list(manifest.get("retrieval_history") or [])
        history.append(retrieval)
        manifest["retrieval_history"] = history[-20:]

    write_json(manifest_path, manifest)
    print_json(
        {
            "ok": True,
            "output_dir": str(output_dir),
            "input_jsonl": str(input_path),
            "manifest": str(manifest_path),
            "request_count": manifest["request_count"],
            "submitted": bool(manifest.get("submission")),
            "batch_id": ((manifest.get("submission") or {}).get("batch") or {}).get("id") or args.batch_id or "",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
