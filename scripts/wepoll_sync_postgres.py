#!/usr/bin/env python3
"""Ingest raw Wepoll CSV files and current index state into Postgres."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "db" / "wepoll_postgres.sql"
DEFAULT_STATE_DIR = ROOT / "projects" / "wepoll-panic" / "state"


def require_psycopg():
    try:
        import psycopg  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "Missing dependency: psycopg\n"
            "Install with: python3 -m pip install psycopg[binary]"
        ) from exc
    return psycopg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="Postgres connection string")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="Schema SQL path")
    parser.add_argument("--init-schema", action="store_true", help="Apply schema before ingest")
    parser.add_argument("--raw-csv", action="append", type=Path, default=[], help="Raw Wepoll CSV path; repeatable")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR, help="Directory holding appended_*.csv state files")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_timestamp(value: str | None) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


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


def parse_bool(value: str | None) -> bool | None:
    raw = (value or "").strip().lower()
    if raw in {"", "none", "null"}:
        return None
    if raw in {"1", "true", "t", "y", "yes"}:
        return True
    if raw in {"0", "false", "f", "n", "no"}:
        return False
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
    csv.field_size_limit(sys.maxsize)
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
    csv.field_size_limit(sys.maxsize)
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


def ingest_source_file(cur, path: Path) -> None:
    row_count, date_min, date_max = summarize_dates(path)
    cur.execute(
        """
        INSERT INTO wepoll_source_files (source_file, sha256, row_count, date_min, date_max)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_file) DO UPDATE SET
            sha256 = EXCLUDED.sha256,
            row_count = EXCLUDED.row_count,
            date_min = EXCLUDED.date_min,
            date_max = EXCLUDED.date_max,
            ingested_at = NOW()
        """,
        (str(path.resolve()), sha256_file(path), row_count, date_min, date_max),
    )


def ingest_raw_posts(cur, path: Path) -> int:
    rows = load_raw_posts(path)
    sql = """
        INSERT INTO wepoll_raw_posts (
            post_id, parent_post_id, depth, reply_code, board_name, content_kind,
            category, title, body, created_at, updated_at, author_id_masked,
            views, comments_count, likes_count, has_poll, source_url, source_file
        ) VALUES (
            %(post_id)s, %(parent_post_id)s, %(depth)s, %(reply_code)s, %(board_name)s, %(content_kind)s,
            %(category)s, %(title)s, %(body)s, %(created_at)s, %(updated_at)s, %(author_id_masked)s,
            %(views)s, %(comments_count)s, %(likes_count)s, %(has_poll)s, %(source_url)s, %(source_file)s
        )
        ON CONFLICT (post_id) DO UPDATE SET
            parent_post_id = EXCLUDED.parent_post_id,
            depth = EXCLUDED.depth,
            reply_code = EXCLUDED.reply_code,
            board_name = EXCLUDED.board_name,
            content_kind = EXCLUDED.content_kind,
            category = EXCLUDED.category,
            title = EXCLUDED.title,
            body = EXCLUDED.body,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at,
            author_id_masked = EXCLUDED.author_id_masked,
            views = EXCLUDED.views,
            comments_count = EXCLUDED.comments_count,
            likes_count = EXCLUDED.likes_count,
            has_poll = EXCLUDED.has_poll,
            source_url = EXCLUDED.source_url,
            source_file = EXCLUDED.source_file,
            ingested_at = NOW()
    """
    cur.executemany(sql, rows)
    return len(rows)


def ingest_daily_features(cur, path: Path) -> int:
    rows = load_csv_rows(path)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": row["date"],
                "anchor_label": row.get("anchor_label", ""),
                "anchor_bull": parse_bool(row.get("anchor_bull")) or False,
                "anchor_bear": parse_bool(row.get("anchor_bear")) or False,
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
    sql = """
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
            %(date)s, %(anchor_label)s, %(anchor_bull)s, %(anchor_bear)s, %(post_count)s,
            %(fear_weighted_mean)s, %(greed_weighted_mean)s, %(uncertainty_weighted_mean)s,
            %(fear_dominant_share)s, %(greed_dominant_share)s, %(mixed_share)s, %(uncertain_share)s,
            %(neutral_share)s, %(fear_high_share)s, %(greed_high_share)s, %(active_emotion_share)s,
            %(dominant_diff)s, %(dominant_spread)s, %(high_share_diff)s, %(high_share_spread)s,
            %(avg_engagement_weight)s, %(noise_ratio)s, %(short_ratio)s, %(question_ratio)s,
            %(meme_ratio)s, %(news_ratio)s, %(stance_calibrated_raw)s, %(stance_calibrated_0_100)s,
            %(stance_reliability)s, %(stance_calibrated_shrunk_0_100)s
        )
        ON CONFLICT (date) DO UPDATE SET
            anchor_label = EXCLUDED.anchor_label,
            anchor_bull = EXCLUDED.anchor_bull,
            anchor_bear = EXCLUDED.anchor_bear,
            post_count = EXCLUDED.post_count,
            fear_weighted_mean = EXCLUDED.fear_weighted_mean,
            greed_weighted_mean = EXCLUDED.greed_weighted_mean,
            uncertainty_weighted_mean = EXCLUDED.uncertainty_weighted_mean,
            fear_dominant_share = EXCLUDED.fear_dominant_share,
            greed_dominant_share = EXCLUDED.greed_dominant_share,
            mixed_share = EXCLUDED.mixed_share,
            uncertain_share = EXCLUDED.uncertain_share,
            neutral_share = EXCLUDED.neutral_share,
            fear_high_share = EXCLUDED.fear_high_share,
            greed_high_share = EXCLUDED.greed_high_share,
            active_emotion_share = EXCLUDED.active_emotion_share,
            dominant_diff = EXCLUDED.dominant_diff,
            dominant_spread = EXCLUDED.dominant_spread,
            high_share_diff = EXCLUDED.high_share_diff,
            high_share_spread = EXCLUDED.high_share_spread,
            avg_engagement_weight = EXCLUDED.avg_engagement_weight,
            noise_ratio = EXCLUDED.noise_ratio,
            short_ratio = EXCLUDED.short_ratio,
            question_ratio = EXCLUDED.question_ratio,
            meme_ratio = EXCLUDED.meme_ratio,
            news_ratio = EXCLUDED.news_ratio,
            stance_calibrated_raw = EXCLUDED.stance_calibrated_raw,
            stance_calibrated_0_100 = EXCLUDED.stance_calibrated_0_100,
            stance_reliability = EXCLUDED.stance_reliability,
            stance_calibrated_shrunk_0_100 = EXCLUDED.stance_calibrated_shrunk_0_100,
            updated_at = NOW()
    """
    cur.executemany(sql, normalized)
    return len(normalized)


def ingest_daily_indices(cur, path: Path) -> int:
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
    sql = """
        INSERT INTO wepoll_daily_indices (
            date, stance_internal_0_100, participation_internal_0_100,
            psychology_index_0_100, participation_index_0_100, state_label_ko,
            stance_delta, participation_delta, prev_state_label_ko, anchor_label, post_count
        ) VALUES (
            %(date)s, %(stance_internal_0_100)s, %(participation_internal_0_100)s,
            %(psychology_index_0_100)s, %(participation_index_0_100)s, %(state_label_ko)s,
            %(stance_delta)s, %(participation_delta)s, %(prev_state_label_ko)s, %(anchor_label)s, %(post_count)s
        )
        ON CONFLICT (date) DO UPDATE SET
            stance_internal_0_100 = EXCLUDED.stance_internal_0_100,
            participation_internal_0_100 = EXCLUDED.participation_internal_0_100,
            psychology_index_0_100 = EXCLUDED.psychology_index_0_100,
            participation_index_0_100 = EXCLUDED.participation_index_0_100,
            state_label_ko = EXCLUDED.state_label_ko,
            stance_delta = EXCLUDED.stance_delta,
            participation_delta = EXCLUDED.participation_delta,
            prev_state_label_ko = EXCLUDED.prev_state_label_ko,
            anchor_label = EXCLUDED.anchor_label,
            post_count = EXCLUDED.post_count,
            updated_at = NOW()
    """
    cur.executemany(sql, normalized)
    return len(normalized)


def main() -> None:
    args = parse_args()
    if not args.database_url:
        raise SystemExit("Missing Postgres connection string. Pass --database-url or set DATABASE_URL.")

    psycopg = require_psycopg()
    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            if args.init_schema:
                cur.execute(read_text(args.schema))

            raw_count = 0
            post_count = 0
            for raw_csv in args.raw_csv:
                ingest_source_file(cur, raw_csv)
                post_count += ingest_raw_posts(cur, raw_csv)
                raw_count += 1

            feature_count = ingest_daily_features(cur, args.state_dir / "appended_stance.csv")
            index_count = ingest_daily_indices(cur, args.state_dir / "appended_quadrant.csv")
        conn.commit()

    print(
        {
            "ok": True,
            "raw_files": raw_count,
            "raw_posts_upserted": post_count,
            "daily_features_upserted": feature_count,
            "daily_indices_upserted": index_count,
        }
    )


if __name__ == "__main__":
    main()
