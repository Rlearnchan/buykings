#!/usr/bin/env python3
"""Run the portable Wepoll daily compute batch against the sibling wepoll-panic repo."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PANIC_ROOT = Path(
    os.environ.get("WEPOLL_PANIC_ROOT", str((ROOT.parent / "wepoll-panic").resolve()))
).resolve()


def run(cmd: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(cmd, check=True, env=env)


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def build_env(src_dir: Path, openai_api_key: str | None) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(src_dir) if not existing else f"{src_dir}{os.pathsep}{existing}"
    if openai_api_key:
        env["OPENAI_API_KEY"] = openai_api_key
    return env


def run_python(
    python_executable: str,
    script_path: Path,
    args: list[str],
    *,
    env: dict[str, str],
) -> None:
    run([python_executable, str(script_path), *args], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panic-root", type=Path, default=DEFAULT_PANIC_ROOT)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--wepoll-export", type=Path, required=True)
    parser.add_argument("--kospi-csv", type=Path, required=True)
    parser.add_argument("--kosdaq-csv", type=Path, required=True)
    parser.add_argument("--vkospi-csv", type=Path, required=True)
    parser.add_argument("--anchors-csv", type=Path)
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--second-pass-backend", default=os.environ.get("WEPOLL_SECOND_PASS_BACKEND", "ollama"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    args = parser.parse_args()

    panic_root = args.panic_root.resolve()
    src_dir = panic_root / "src"
    module_dir = src_dir / "wepoll_fear_index"
    anchors_csv = args.anchors_csv or (panic_root / "data" / "market_anchor_windows.csv")
    workdir = args.workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    delivery_dir = workdir / "delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)

    env = build_env(src_dir, args.openai_api_key)

    preprocessed = workdir / "preprocessed_posts.csv"
    first_pass = workdir / "weak_first_pass.csv"
    fear_candidates = workdir / "fear_candidates.csv"
    fear_second_pass = workdir / "fear_second_pass.csv"
    fear_merged = workdir / "fear_merged.csv"
    greed_candidates = workdir / "greed_candidates.csv"
    greed_second_pass = workdir / "greed_second_pass.csv"
    final_merged = workdir / "final_merged.csv"
    daily_features = workdir / "calibration_daily_features.csv"
    stance_csv = workdir / "anchor_stance.csv"
    stance_svg = workdir / "anchor_stance.svg"
    stance_summary = workdir / "anchor_stance.txt"
    market_normalized = workdir / "market_daily_normalized.csv"
    quadrant_csv = workdir / "quadrant.csv"
    quadrant_svg = workdir / "quadrant.svg"
    latest_json = delivery_dir / "latest_state.json"
    history_csv = delivery_dir / "history.csv"
    history_json = delivery_dir / "history.json"

    run_python(
        args.python_executable,
        module_dir / "preprocess_posts.py",
        ["--input", str(args.wepoll_export.resolve()), "--output", str(preprocessed)],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "weak_supervision_first_pass.py",
        ["--input", str(preprocessed), "--output", str(first_pass)],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "select_fear_candidates.py",
        ["--input", str(first_pass), "--output", str(fear_candidates)],
        env=env,
    )

    if count_rows(fear_candidates) > 0:
        run_python(
            args.python_executable,
            module_dir / "fear_second_pass_runner.py",
            [
                "--input",
                str(fear_candidates),
                "--output",
                str(fear_second_pass),
                "--backend",
                args.second_pass_backend,
                "--model",
                args.model,
                "--ollama-host",
                args.ollama_host,
            ],
            env=env,
        )
        run_python(
            args.python_executable,
            module_dir / "merge_fear_second_pass.py",
            [
                "--first-pass",
                str(first_pass),
                "--second-pass",
                str(fear_second_pass),
                "--output",
                str(fear_merged),
            ],
            env=env,
        )
    else:
        fear_merged.write_text(first_pass.read_text(encoding="utf-8"), encoding="utf-8")

    run_python(
        args.python_executable,
        module_dir / "select_greed_candidates.py",
        ["--input", str(fear_merged), "--output", str(greed_candidates)],
        env=env,
    )

    if count_rows(greed_candidates) > 0:
        run_python(
            args.python_executable,
            module_dir / "greed_second_pass_runner.py",
            [
                "--input",
                str(greed_candidates),
                "--output",
                str(greed_second_pass),
                "--backend",
                args.second_pass_backend,
                "--model",
                args.model,
                "--ollama-host",
                args.ollama_host,
            ],
            env=env,
        )
        run_python(
            args.python_executable,
            module_dir / "merge_greed_second_pass.py",
            [
                "--first-pass",
                str(fear_merged),
                "--second-pass",
                str(greed_second_pass),
                "--output",
                str(final_merged),
            ],
            env=env,
        )
    else:
        final_merged.write_text(fear_merged.read_text(encoding="utf-8"), encoding="utf-8")

    run_python(
        args.python_executable,
        module_dir / "build_calibration_dataset.py",
        [
            "--input",
            str(final_merged),
            "--anchors",
            str(anchors_csv.resolve()),
            "--output",
            str(daily_features),
        ],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "build_anchor_calibrated_stance.py",
        [
            "--input",
            str(daily_features),
            "--output-csv",
            str(stance_csv),
            "--output-svg",
            str(stance_svg),
            "--output-summary",
            str(stance_summary),
        ],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "import_market_csvs.py",
        [
            "--kospi",
            str(args.kospi_csv.resolve()),
            "--kosdaq",
            str(args.kosdaq_csv.resolve()),
            "--vkospi",
            str(args.vkospi_csv.resolve()),
            "--output",
            str(market_normalized),
        ],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "build_anchor_quadrant.py",
        [
            "--stance-input",
            str(stance_csv),
            "--features-input",
            str(daily_features),
            "--market-input",
            str(market_normalized),
            "--output-csv",
            str(quadrant_csv),
            "--output-svg",
            str(quadrant_svg),
            "--title",
            "Wepoll Quadrant (Psychology x Participation)",
        ],
        env=env,
    )
    run_python(
        args.python_executable,
        module_dir / "build_manager_delivery.py",
        [
            "--quadrant-input",
            str(quadrant_csv),
            "--merged-input",
            str(final_merged),
            "--market-input",
            str(market_normalized),
            "--output-latest-json",
            str(latest_json),
            "--output-history-csv",
            str(history_csv),
            "--output-history-json",
            str(history_json),
        ],
        env=env,
    )

    print(
        json.dumps(
            {
                "ok": True,
                "panic_root": str(panic_root),
                "workdir": str(workdir),
                "final_merged": str(final_merged),
                "daily_features": str(daily_features),
                "quadrant_csv": str(quadrant_csv),
                "latest_json": str(latest_json),
                "history_csv": str(history_csv),
                "second_pass_backend": args.second_pass_backend,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
