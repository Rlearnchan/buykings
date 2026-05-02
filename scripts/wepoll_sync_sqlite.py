#!/usr/bin/env python3
"""Ingest raw Wepoll CSV files and current index state into SQLite."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "db" / "wepoll.sqlite3"
DEFAULT_SCHEMA = ROOT / "db" / "wepoll_sqlite.sql"
DEFAULT_STATE_DIR = ROOT / "projects" / "wepoll-panic" / "state"


def set_csv_field_limit() -> None:
    for limit in (sys.maxsize, 2_147_483_647, 1_000_000_000):
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            continue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite db path")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Schema SQL path")
    parser.add_argument("--init-schema", action="store_true", help="Apply schema before ingest")
    parser.add_argument("--raw-csv", action="append", type=Path, default=[], help="Raw Wepoll CSV path; repeatable")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR, help="Directory holding appended_*.csv state files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_timestamp(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return value


def parse_int(value: str | None) -> int | None:
    raw = (value or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def parse_float(value: str | None) -> float | None:
    raw = (value or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        return float(raw)
    except Exception:
        return None


def parse_bool(value: str | None) -> int | None:
    raw = (value or "").strip().lower()
    if raw in {"", "none", "null"}:
        return None
    if raw in {"1", "true", "t", "y", "yes"}:
        return 1
    if raw in {"0", "false", "f", "n", "no"}:
        return 0
    return None


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return ""


def mask_author(author_id: str) -> str:
    author_id = author_id.strip()
    if not author_id:
        return ""
    if "*" in author_id:
        return author_id
    if len(author_id) <= 2:
        return "*" * len(author_id)
    return f"{author_id[:2]}***"


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def summarize_dates(path: Path) -> tuple[int, str | None, str | None]:
    set_csv_field_limit()
    count = 0
    dates: Counter[str] = Counter()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            count += 1
            created = first_value(row, "작성시각", "created_at")
            if created:
                dates[created[:10]] += 1
    if not dates:
        return count, None, None
    ordered = sorted(dates)
    return count, ordered[0], ordered[-1]


def normalize_raw_post(row: dict[str, str], source_file: str) -> dict[str, object]:
    author = first_value(row, "작성자ID_익명", "작성자ID")
    return {
        "post_id": first_value(row, "글ID", "ID"),
        "parent_post_id": first_value(row, "원글ID"),
        "depth": parse_int(first_value(row, "깊이")),
        "reply_code": first_value(row, "답글코드"),
        "board_name": first_value(row, "게시판"),
        "content_kind": first_value(row, "구분"),
        "category": first_value(row, "카테고리"),
        "title": first_value(row, "제목"),
        "body": first_value(row, "본문"),
        "created_at": parse_timestamp(first_value(row, "작성시각")),
        "updated_at": parse_timestamp(first_value(row, "수정시각")),
        "author_id_masked": mask_author(author),
        "views": parse_int(first_value(row, "조회수")),
        "comments_count": parse_int(first_value(row, "댓글수")),
        "likes_count": parse_int(first_value(row, "좋아요수")),
        "has_poll": parse_bool(first_value(row, "투표여부")),
        "source_url": first_value(row, "원본URL"),
        "source_file": source_file,
    }


def load_raw_posts(path: Path) -> list[dict[str, object]]:
    set_csv_field_limit()
    source_file = str(path.resolve())
    posts: dict[str, dict[str, object]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            normalized = normalize_raw_post(row, source_file)
            post_id = str(normalized["post_id"])
            if not post_id:
                continue
            if normalized["content_kind"] and normalized["content_kind"] != "글":
                continue
            depth = normalized["depth"]
            if depth not in (None, 0):
                continue
            posts[post_id] = normalized
    return [posts[key] for key in sorted(posts)]


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ingest_source_file(cur: sqlite3.Cursor, path: Path) -> None:
    row_count, date_min, date_max = summarize_dates(path)
    cur.execute(
        """
        INSERT INTO wepoll_source_files (source_file, sha256, row_count, date_min, date_max)
        VALUES (:source_file, :sha256, :row_count, :date_min, :date_max)
        ON CONFLICT(source_file) DO UPDATE SET
            sha256 = excluded.sha256,
            row_count = excluded.row_count,
            date_min = excluded.date_min,
            date_max = excluded.date_max,
            ingested_at = CURRENT_TIMESTAMP
        """,
        {
            "source_file": str(path.resolve()),
            "sha256": sha256_file(path),
            "row_count": row_count,
            "date_min": date_min,
            "date_max": date_max,
        },
    )


def ingest_raw_posts(cur: sqlite3.Cursor, path: Path) -> int:
    rows = load_raw_posts(path)
    cur.executemany(
        """
        INSERT INTO wepoll_raw_posts (
            post_id, parent_post_id, depth, reply_code, board_name, content_kind,
            category, title, body, created_at, updated_at, author_id_masked,
            views, comments_count, likes_count, has_poll, source_url, source_file
        ) VALUES (
            :post_id, :parent_post_id, :depth, :reply_code, :board_name, :content_kind,
            :category, :title, :body, :created_at, :updated_at, :author_id_masked,
            :views, :comments_count, :likes_count, :has_poll, :source_url, :source_file
        )
        ON CONFLICT(post_id) DO UPDATE SET
            parent_post_id = excluded.parent_post_id,
            depth = excluded.depth,
            reply_code = excluded.reply_code,
            board_name = excluded.board_name,
            content_kind = excluded.content_kind,
            category = excluded.category,
            title = excluded.title,
            body = excluded.body,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at,
            author_id_masked = excluded.author_id_masked,
            views = excluded.views,
            comments_count = excluded.comments_count,
            likes_count = excluded.likes_count,
            has_poll = excluded.has_poll,
            source_url = excluded.source_url,
            source_file = excluded.source_file,
            ingested_at = CURRENT_TIMESTAMP
        """,
        rows,
    )
    return len(rows)


def ingest_daily_features(cur: sqlite3.Cursor, path: Path) -> int:
    rows = load_csv_rows(path)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": row["date"],
                "anchor_label": row.get("anchor_label", ""),
                "anchor_bull": parse_bool(row.get("anchor_bull")) or 0,
                "anchor_bear": parse_bool(row.get("anchor_bear")) or 0,
                "post_count": parse_int(row.get("post_count")),
                "fear_weighted_mean": parse_float(row.get("fear_weighted_mean")),
                "greed_weighted_mean": parse_float(row.get("greed_weighted_mean")),
                "uncertainty_weighted_mean": parse_float(row.get("uncertainty_weighted_mean")),
                "fear_dominant_share": parse_float(row.get("fear_dominant_share")),
                "greed_dominant_share": parse_float(row.get("greed_dominant_share")),
                "mixed_share": parse_float(row.get("mixed_share")),
                "uncertain_share": parse_float(row.get("uncertain_share")),
                "neutral_share": parse_float(row.get("neutral_share")),
                "fear_high_share": parse_float(row.get("fear_high_share")),
                "greed_high_share": parse_float(row.get("greed_high_share")),
                "active_emotion_share": parse_float(row.get("active_emotion_share")),
                "dominant_diff": parse_float(row.get("dominant_diff")),
                "dominant_spread": parse_float(row.get("dominant_spread")),
                "high_share_diff": parse_float(row.get("high_share_diff")),
                "high_share_spread": parse_float(row.get("high_share_spread")),
                "avg_engagement_weight": parse_float(row.get("avg_engagement_weight")),
                "noise_ratio": parse_float(row.get("noise_ratio")),
                "short_ratio": parse_float(row.get("short_ratio")),
                "question_ratio": parse_float(row.get("question_ratio")),
                "meme_ratio": parse_float(row.get("meme_ratio")),
                "news_ratio": parse_float(row.get("news_ratio")),
                "stance_calibrated_raw": parse_float(row.get("stance_calibrated_raw")),
                "stance_calibrated_0_100": parse_float(row.get("stance_calibrated_0_100")),
                "stance_reliability": parse_float(row.get("stance_reliability")),
                "stance_calibrated_shrunk_0_100": parse_float(row.get("stance_calibrated_shrunk_0_100")),
            }
        )
    cur.executemany(
        """
        INSERT INTO wepoll_daily_features (
            date, anchor_label, anchor_bull, anchor_bear, post_count,
            fear_weighted_mean, greed_weighted_mean, uncertainty_weighted_mean,
            fear_dominant_share, greed_dominant_share, mixed_share, uncertain_share,
            neutral_share, fear_high_share, greed_high_share, active_emotion_share,
            dominant_diff, dominant_spread, high_share_diff, high_share_spread,
            avg_engagement_weight, noise_ratio, short_ratio, question_ratio,
            meme_ratio, news_ratio, stance_calibrated_raw, stance_calibrated_0_100,
            stance_reliability, stance_calibrated_shrunk_0_100
        ) VALUES (
            :date, :anchor_label, :anchor_bull, :anchor_bear, :post_count,
            :fear_weighted_mean, :greed_weighted_mean, :uncertainty_weighted_mean,
            :fear_dominant_share, :greed_dominant_share, :mixed_share, :uncertain_share,
            :neutral_share, :fear_high_share, :greed_high_share, :active_emotion_share,
            :dominant_diff, :dominant_spread, :high_share_diff, :high_share_spread,
            :avg_engagement_weight, :noise_ratio, :short_ratio, :question_ratio,
            :meme_ratio, :news_ratio, :stance_calibrated_raw, :stance_calibrated_0_100,
            :stance_reliability, :stance_calibrated_shrunk_0_100
        )
        ON CONFLICT(date) DO UPDATE SET
            anchor_label = excluded.anchor_label,
            anchor_bull = excluded.anchor_bull,
            anchor_bear = excluded.anchor_bear,
            post_count = excluded.post_count,
            fear_weighted_mean = excluded.fear_weighted_mean,
            greed_weighted_mean = excluded.greed_weighted_mean,
            uncertainty_weighted_mean = excluded.uncertainty_weighted_mean,
            fear_dominant_share = excluded.fear_dominant_share,
            greed_dominant_share = excluded.greed_dominant_share,
            mixed_share = excluded.mixed_share,
            uncertain_share = excluded.uncertain_share,
            neutral_share = excluded.neutral_share,
            fear_high_share = excluded.fear_high_share,
            greed_high_share = excluded.greed_high_share,
            active_emotion_share = excluded.active_emotion_share,
            dominant_diff = excluded.dominant_diff,
            dominant_spread = excluded.dominant_spread,
            high_share_diff = excluded.high_share_diff,
            high_share_spread = excluded.high_share_spread,
            avg_engagement_weight = excluded.avg_engagement_weight,
            noise_ratio = excluded.noise_ratio,
            short_ratio = excluded.short_ratio,
            question_ratio = excluded.question_ratio,
            meme_ratio = excluded.meme_ratio,
            news_ratio = excluded.news_ratio,
            stance_calibrated_raw = excluded.stance_calibrated_raw,
            stance_calibrated_0_100 = excluded.stance_calibrated_0_100,
            stance_reliability = excluded.stance_reliability,
            stance_calibrated_shrunk_0_100 = excluded.stance_calibrated_shrunk_0_100,
            updated_at = CURRENT_TIMESTAMP
        """,
        normalized,
    )
    return len(normalized)


def ingest_daily_indices(cur: sqlite3.Cursor, path: Path) -> int:
    rows = load_csv_rows(path)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": row["date"],
                "stance_internal_0_100": parse_float(row.get("stance_internal_0_100")),
                "participation_internal_0_100": parse_float(row.get("participation_internal_0_100")),
                "psychology_index_0_100": parse_float(row.get("stance_index_0_100") or row.get("psychology_index_0_100")),
                "participation_index_0_100": parse_float(row.get("participation_index_0_100")),
                "state_label_ko": row.get("state_label_ko", ""),
                "stance_delta": parse_float(row.get("stance_delta")),
                "participation_delta": parse_float(row.get("participation_delta")),
                "prev_state_label_ko": row.get("prev_state_label_ko", ""),
                "anchor_label": row.get("anchor_label", ""),
                "post_count": parse_int(row.get("post_count")),
            }
        )
    cur.executemany(
        """
        INSERT INTO wepoll_daily_indices (
            date, stance_internal_0_100, participation_internal_0_100,
            psychology_index_0_100, participation_index_0_100, state_label_ko,
            stance_delta, participation_delta, prev_state_label_ko, anchor_label, post_count
        ) VALUES (
            :date, :stance_internal_0_100, :participation_internal_0_100,
            :psychology_index_0_100, :participation_index_0_100, :state_label_ko,
            :stance_delta, :participation_delta, :prev_state_label_ko, :anchor_label, :post_count
        )
        ON CONFLICT(date) DO UPDATE SET
            stance_internal_0_100 = excluded.stance_internal_0_100,
            participation_internal_0_100 = excluded.participation_internal_0_100,
            psychology_index_0_100 = excluded.psychology_index_0_100,
            participation_index_0_100 = excluded.participation_index_0_100,
            state_label_ko = excluded.state_label_ko,
            stance_delta = excluded.stance_delta,
            participation_delta = excluded.participation_delta,
            prev_state_label_ko = excluded.prev_state_label_ko,
            anchor_label = excluded.anchor_label,
            post_count = excluded.post_count,
            updated_at = CURRENT_TIMESTAMP
        """,
        normalized,
    )
    return len(normalized)


def main() -> None:
    args = parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        if args.init_schema:
            cur.executescript(read_text(args.schema))

        raw_count = 0
        post_count = 0
        for raw_csv in args.raw_csv:
            ingest_source_file(cur, raw_csv)
            post_count += ingest_raw_posts(cur, raw_csv)
            raw_count += 1

        feature_count = ingest_daily_features(cur, args.state_dir / "appended_stance.csv")
        index_count = ingest_daily_indices(cur, args.state_dir / "appended_quadrant.csv")
        conn.commit()
    finally:
        conn.close()

    print(
        {
            "ok": True,
            "db": str(args.db.resolve()),
            "raw_files": raw_count,
            "raw_posts_upserted": post_count,
            "daily_features_upserted": feature_count,
            "daily_indices_upserted": index_count,
        }
    )


if __name__ == "__main__":
    main()
