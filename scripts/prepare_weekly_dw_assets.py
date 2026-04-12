#!/usr/bin/env python3
"""Prepare recurring weekly Datawrapper assets and semantic/fightin tables."""

from __future__ import annotations

import csv
import html
import math
import os
import re
from collections import Counter
from datetime import datetime
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PANIC_TIMESERIES_SOURCE = ROOT.parent / "wepoll-panic" / "docs" / "report_assets" / "2026-04-06" / "psychology_participation_postcount_timeseries_append_2026-04-05.csv"
PANIC_BUBBLE_SOURCE = ROOT.parent / "wepoll-panic" / "output" / "yearly_hybrid_batch_v4" / "weekly_bubble_points_2026-02-23_2026-04-05.csv"

SEMANTIC_EXPORT_DIR = ROOT / "exports" / "wepoll-samsung" / "semantic-periods"
FIGHTIN_DIR = ROOT.parent / "wepoll-samsung" / "output" / "event_analysis" / "fightin_words"
FIGHTIN_PREPOST_DIR = ROOT.parent / "wepoll-samsung" / "output" / "event_analysis" / "fightin_words_prepost" / "2026-04-06_pre14_post7"
PANIC_MERGED_SOURCE = ROOT.parent / "wepoll-panic" / "output" / "yearly_hybrid_batch_v4" / "yearly_merged_posts_greed_v8_full.csv"
EVENT_WEEK_SOURCE = Path(
    os.environ.get(
        "EVENT_WEEK_SOURCE",
        ROOT / "projects" / "wepoll-samsung" / "incoming" / "wepoll_stock_eventweek.csv",
    )
)

PANIC_PREPARED_DIR = ROOT / "projects" / "wepoll-panic" / "prepared"
SAMSUNG_PREPARED_DIR = ROOT / "projects" / "wepoll-samsung" / "prepared"
MEMBERS = ["슈카", "알상무", "니니"]
ALIASES = {
    "슈카": ["슈카", "슈사장", "슈카형", "슈카님", "슈형", "슈카월드", "슈카친구들"],
    "알상무": ["알상무", "알상무님", "알버트", "알반꿀"],
    "니니": ["니니", "니황", "니니님"],
}
STOPWORDS = {
    "그리고", "그래서", "근데", "그냥", "정말", "진짜", "너무", "오늘", "내일", "지금", "이번", "최근",
    "관련", "대한", "이런", "그런", "합니다", "입니다", "있는데", "있습니다", "같은", "으로", "에서",
    "하는", "하면", "하게", "했다", "이후", "하네요", "가즈아", "하나", "정도", "있는", "없는",
    "했던", "하며", "한다", "되는", "보면", "보는", "라고", "이라", "해서", "한번", "현재", "하지만",
    "많이", "있음", "것이", "아니라", "결국", "어떻게", "https", "com", "www", "해요", "있을",
    "같아요", "같습니다", "하세요", "드립니다", "우리", "여기", "이거", "저거", "한국", "미국",
    "경제", "시장", "주식", "투자", "보고", "영상", "라이브", "코믹스", "youtube", "youtu", "be",
    "방송", "방송에서", "위폴", "위폴에",
}
PERIODS = {
    "2025": (date(2025, 3, 28), date(2025, 12, 31)),
    "2026": (date(2026, 1, 1), date(2026, 4, 5)),
    "이벤트주간": (date(2026, 4, 6), date(2026, 4, 11)),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value[:10], "%Y-%m-%d")


def period_slug(name: str) -> str:
    return {"2025": "2025", "2026": "2026", "이벤트주간": "eventweek"}[name]


def normalize_text(text: str) -> str:
    out = html.unescape(str(text))
    out = re.sub(r"<[^>]+>", " ", out)
    out = re.sub(r"https?://\S+", " ", out)
    out = re.sub(r"www\.\S+", " ", out)
    for canonical, aliases in ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            out = out.replace(alias, canonical)
    return re.sub(r"\s+", " ", out).strip()


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z]{2,}", normalize_text(text))
    clean = []
    for token in tokens:
        if token in STOPWORDS or len(token) < 2:
            continue
        clean.append(token)
    return clean


def extract_context_tokens(text: str, member: str, window: int = 20) -> list[str]:
    tokens = tokenize(text)
    contexts: list[str] = []
    for idx, token in enumerate(tokens):
        if token != member:
            continue
        left = max(0, idx - window)
        right = min(len(tokens), idx + window + 1)
        for cand in tokens[left:right]:
            if cand == member or cand in MEMBERS or cand in STOPWORDS:
                continue
            if any(cand.endswith(suffix) for suffix in ["의", "가", "이", "은", "는", "를", "을", "님"]):
                base = cand[:-1]
                if len(base) >= 2 and base not in MEMBERS and base not in STOPWORDS:
                    cand = base
                else:
                    continue
            contexts.append(cand)
    return contexts


def load_period_member_contexts(window: int = 20) -> dict[str, dict[str, Counter]]:
    out = {period: {member: Counter() for member in MEMBERS} for period in PERIODS}
    csv.field_size_limit(10**9)

    with PANIC_MERGED_SOURCE.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                current = parse_date(row["created_at"]).date()
            except Exception:
                continue
            text = normalize_text(f"{row.get('title', '')} {row.get('body_text', '')}")
            for period, (start, end) in PERIODS.items():
                if period == "이벤트주간":
                    continue
                if start <= current <= end:
                    for member in MEMBERS:
                        if member in text:
                            out[period][member].update(extract_context_tokens(text, member, window=window))
                    break

    with EVENT_WEEK_SOURCE.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            created = row.get("작성시각", "")
            if not created:
                continue
            try:
                current = parse_date(created).date()
            except Exception:
                continue
            start, end = PERIODS["이벤트주간"]
            if not (start <= current <= end):
                continue
            text = normalize_text(f"{row.get('제목', '')} {row.get('본문', '')}")
            for member in MEMBERS:
                if member in text:
                    out["이벤트주간"][member].update(extract_context_tokens(text, member, window=window))

    return out


def weighted_log_odds(counts_a: Counter, counts_b: Counter, prior: Counter) -> list[dict[str, object]]:
    vocab = sorted(set(counts_a) | set(counts_b) | set(prior))
    n1 = sum(counts_a.values())
    n2 = sum(counts_b.values())
    alpha0 = sum(prior.values())
    rows = []
    for term in vocab:
        y1 = counts_a.get(term, 0)
        y2 = counts_b.get(term, 0)
        alpha = prior.get(term, 0)
        if y1 + y2 == 0:
            continue
        delta = math.log((y1 + alpha) / (n1 + alpha0 - y1 - alpha + 1e-12)) - math.log(
            (y2 + alpha) / (n2 + alpha0 - y2 - alpha + 1e-12)
        )
        var = 1.0 / (y1 + alpha + 1e-12) + 1.0 / (y2 + alpha + 1e-12)
        z = delta / math.sqrt(var)
        rows.append({"term": term, "z": z})
    rows.sort(key=lambda row: row["z"], reverse=True)
    return rows


def prepare_weekly_timeseries() -> tuple[Path, Path]:
    rows = read_csv(PANIC_TIMESERIES_SOURCE)
    rows.sort(key=lambda row: row["date"])
    recent = rows[-42:]

    out_rows = []
    state_ranges = []
    current_state = None
    current_start = None
    previous_date = None

    for idx, row in enumerate(recent, start=1):
        out_rows.append(
            {
                "plot_seq": idx,
                "date": row["date"],
                "display_date": f"{parse_date(row['date']).month}/{parse_date(row['date']).day}",
                "state_label_ko": row["state_label_ko"],
                "psychology_index_0_100": f"{float(row['psychology_index_0_100']):.2f}",
                "participation_index_0_100": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": int(float(row["post_count"])),
            }
        )

        if row["state_label_ko"] != current_state:
            if current_state is not None:
                state_ranges.append(
                    {
                        "state_label_ko": current_state,
                        "start_date": current_start,
                        "end_date": previous_date,
                    }
                )
            current_state = row["state_label_ko"]
            current_start = row["date"]
        previous_date = row["date"]

    if current_state is not None and current_start is not None and previous_date is not None:
        state_ranges.append(
            {
                "state_label_ko": current_state,
                "start_date": current_start,
                "end_date": previous_date,
            }
        )

    main_path = PANIC_PREPARED_DIR / "dw_weekly_timeseries_recent6w.csv"
    ranges_path = PANIC_PREPARED_DIR / "dw_weekly_timeseries_state_ranges_recent6w.csv"
    write_csv(
        main_path,
        out_rows,
        [
            "plot_seq",
            "date",
            "display_date",
            "state_label_ko",
            "psychology_index_0_100",
            "participation_index_0_100",
            "post_count",
        ],
    )
    write_csv(ranges_path, state_ranges, ["state_label_ko", "start_date", "end_date"])
    return main_path, ranges_path


def prepare_weekly_bubble() -> Path:
    rows = read_csv(PANIC_BUBBLE_SOURCE)
    rows.sort(key=lambda row: row["date"])
    latest_week = rows[-1]["week_range"]
    week_rows = [row for row in rows if row["week_range"] == latest_week]
    week_rows.sort(key=lambda row: row["date"])

    out_rows = []
    for idx, row in enumerate(week_rows, start=1):
        out_rows.append(
            {
                "day_seq": idx,
                "day_label": f"{idx}일차",
                "date": row["date"],
                "week_range": row["week_range"],
                "state_label_ko": row["state_label_ko"],
                "psychology_index_0_100": f"{float(row['psychology_index_0_100']):.2f}",
                "participation_index_0_100": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": int(float(row["post_count"])),
            }
        )

    path = PANIC_PREPARED_DIR / "dw_weekly_bubble_latest_week.csv"
    write_csv(
        path,
        out_rows,
        [
            "day_seq",
            "day_label",
            "date",
            "week_range",
            "state_label_ko",
            "psychology_index_0_100",
            "participation_index_0_100",
            "post_count",
        ],
    )
    return path


def prepare_semantic_candidates() -> tuple[Path, Path]:
    candidate_rows = []
    similar_rows = []

    for period in ["2025", "2026", "이벤트주간"]:
        pca_rows = read_csv(SEMANTIC_EXPORT_DIR / f"{period}_pca_points.csv")
        for rank, row in enumerate(pca_rows, start=1):
            group = "anchor"
            recommended_keep = "yes" if row["kind"] == "member" else ""
            if 2 <= rank <= 18:
                group = "anchor_neighbor"
                recommended_keep = "yes"
            elif rank > 18:
                group = "top_token"
            candidate_rows.append(
                {
                    "period": period,
                    "rank": rank,
                    "label": row["label"],
                    "kind": row["kind"],
                    "candidate_group": group,
                    "recommended_keep": recommended_keep,
                    "x": row["x"],
                    "y": row["y"],
                }
            )

        neighbor_rows = read_csv(SEMANTIC_EXPORT_DIR / f"{period}_neighbors.csv")
        member_rank = {}
        for row in neighbor_rows:
            member = row["anchor"]
            member_rank[member] = member_rank.get(member, 0) + 1
            similar_rows.append(
                {
                    "period": period,
                    "member": member,
                    "rank": member_rank[member],
                    "neighbor": row["neighbor"],
                    "cosine": f"{float(row['cosine']):.4f}",
                }
            )

    candidate_path = SAMSUNG_PREPARED_DIR / "dw_member_word2vec_candidate_dots.csv"
    similar_path = SAMSUNG_PREPARED_DIR / "dw_member_word2vec_similar_table.csv"
    write_csv(
        candidate_path,
        candidate_rows,
        ["period", "rank", "label", "kind", "candidate_group", "recommended_keep", "x", "y"],
    )
    write_csv(
        similar_path,
        similar_rows,
        ["period", "member", "rank", "neighbor", "cosine"],
    )
    return candidate_path, similar_path


def prepare_semantic_period_views() -> list[Path]:
    selected_source = SAMSUNG_PREPARED_DIR / "dw_member_word2vec_selected_dots.csv"
    similar_source = SAMSUNG_PREPARED_DIR / "dw_member_word2vec_similar_table.csv"
    selected_rows = read_csv(selected_source)
    similar_rows = read_csv(similar_source)
    outputs: list[Path] = []

    period_slug = {"2025": "2025", "2026": "2026", "이벤트주간": "eventweek"}
    for period, slug in period_slug.items():
        selected_path = SAMSUNG_PREPARED_DIR / f"dw_member_word2vec_selected_dots_{slug}.csv"
        period_selected = [
            {
                "label": row["label"],
                "kind": row["kind"],
                "selection_group": row["selection_group"],
                "x": row["x"],
                "y": row["y"],
            }
            for row in selected_rows
            if row["period"] == period
        ]
        write_csv(selected_path, period_selected, ["label", "kind", "selection_group", "x", "y"])
        outputs.append(selected_path)

        similar_path = SAMSUNG_PREPARED_DIR / f"dw_member_word2vec_similar_table_{slug}.csv"
        period_similar = [
            {
                "member": row["member"],
                "rank": row["rank"],
                "neighbor": row["neighbor"],
                "cosine": row["cosine"],
            }
            for row in similar_rows
            if row["period"] == period
        ]
        write_csv(similar_path, period_similar, ["member", "rank", "neighbor", "cosine"])
        outputs.append(similar_path)

    return outputs


def prepare_member_similar_member_tables() -> list[Path]:
    similar_rows = read_csv(SAMSUNG_PREPARED_DIR / "dw_member_word2vec_similar_table.csv")
    outputs: list[Path] = []
    for member in MEMBERS:
        rows = []
        for rank in range(1, 6):
            row = {"rank": rank}
            for period in ["2025", "2026", "이벤트주간"]:
                match = next(
                    (
                        current
                        for current in similar_rows
                        if current["member"] == member and current["period"] == period and int(current["rank"]) == rank
                    ),
                    None,
                )
                row[period] = f"{match['neighbor']} ({match['cosine']})" if match else ""
            rows.append(row)
        out = SAMSUNG_PREPARED_DIR / f"dw_member_word2vec_similar_table_{member}.csv"
        write_csv(out, rows, ["rank", "2025", "2026", "이벤트주간"])
        outputs.append(out)
    return outputs


def prepare_member_fightin_period_tables() -> list[Path]:
    outputs: list[Path] = []
    counts_by_period = load_period_member_contexts(window=20)
    combined_cells: dict[str, dict[str, list[str]]] = {
        member: {period: [] for period in PERIODS} for member in MEMBERS
    }

    for period in PERIODS:
        prior = Counter()
        for member in MEMBERS:
            prior.update(counts_by_period[period][member])
        tables: dict[str, list[dict[str, object]]] = {}
        for member in MEMBERS:
            reference = Counter()
            for other in MEMBERS:
                if other != member:
                    reference.update(counts_by_period[period][other])
            tables[member] = weighted_log_odds(counts_by_period[period][member], reference, prior)[:10]

        for member in MEMBERS:
            period_out = SAMSUNG_PREPARED_DIR / f"dw_fightin_words_period_table_{member}_{period_slug(period)}.csv"
            period_rows = [
                {"rank": idx, "term": row["term"], "z": f"{row['z']:.3f}"}
                for idx, row in enumerate(tables[member], start=1)
            ]
            combined_cells[member][period] = [f"{row['term']} ({row['z']:.3f})" for row in tables[member]]
            write_csv(period_out, period_rows, ["rank", "term", "z"])
            outputs.append(period_out)

    for member in MEMBERS:
        rows = []
        for rank in range(1, 11):
            row = {"rank": rank}
            for period in ["2025", "2026", "이벤트주간"]:
                cells = combined_cells[member][period]
                row[period] = cells[rank - 1] if rank - 1 < len(cells) else ""
            rows.append(row)
        out = SAMSUNG_PREPARED_DIR / f"dw_fightin_words_period_table_{member}.csv"
        write_csv(out, rows, ["rank", "2025", "2026", "이벤트주간"])
        outputs.append(out)

    return outputs


def prepare_fightin_tables() -> tuple[Path, Path]:
    summary_rows = []
    prepost_rows = []

    for member in ["슈카", "알상무", "니니"]:
        path = FIGHTIN_DIR / f"fightin_words_{member}.csv"
        rows = read_csv(path)[:15]
        for rank, row in enumerate(rows, start=1):
            summary_rows.append(
                {
                    "scope": "overall",
                    "member": member,
                    "rank": rank,
                    "term": row["term"],
                    "count_target": row["count_target"],
                    "count_reference": row["count_reference"],
                    "delta": f"{float(row['delta']):.4f}",
                    "z": f"{float(row['z']):.4f}",
                }
            )

        path = FIGHTIN_PREPOST_DIR / f"prepost_{member}.csv"
        rows = read_csv(path)[:12]
        for rank, row in enumerate(rows, start=1):
            prepost_rows.append(
                {
                    "scope": "prepost",
                    "member": member,
                    "rank": rank,
                    "term": row["term"],
                    "count_post": row["count_post"],
                    "count_pre": row["count_pre"],
                    "z": f"{float(row['z']):.4f}",
                }
            )

    overall_path = SAMSUNG_PREPARED_DIR / "dw_fightin_words_overall_table.csv"
    prepost_path = SAMSUNG_PREPARED_DIR / "dw_fightin_words_prepost_table.csv"
    write_csv(
        overall_path,
        summary_rows,
        ["scope", "member", "rank", "term", "count_target", "count_reference", "delta", "z"],
    )
    write_csv(
        prepost_path,
        prepost_rows,
        ["scope", "member", "rank", "term", "count_post", "count_pre", "z"],
    )
    return overall_path, prepost_path


def main() -> None:
    timeseries_path, ranges_path = prepare_weekly_timeseries()
    bubble_path = prepare_weekly_bubble()
    candidate_path, similar_path = prepare_semantic_candidates()
    semantic_view_paths = prepare_semantic_period_views()
    similar_member_paths = prepare_member_similar_member_tables()
    overall_path, prepost_path = prepare_fightin_tables()
    fightin_period_paths = prepare_member_fightin_period_tables()

    print(f"timeseries={timeseries_path}")
    print(f"ranges={ranges_path}")
    print(f"bubble={bubble_path}")
    print(f"semantic_candidates={candidate_path}")
    print(f"semantic_similar={similar_path}")
    for path in semantic_view_paths:
        print(f"semantic_view={path}")
    for path in similar_member_paths:
        print(f"semantic_member_table={path}")
    print(f"fightin_overall={overall_path}")
    print(f"fightin_prepost={prepost_path}")
    for path in fightin_period_paths:
        print(f"fightin_period_table={path}")


if __name__ == "__main__":
    main()
