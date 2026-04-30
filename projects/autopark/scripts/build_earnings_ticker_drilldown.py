#!/usr/bin/env python3
"""Score earnings-calendar tickers for deeper morning-dashboard follow-up."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from select_storylines_v2 import PROCESSED_DIR, RUNTIME_NOTION_DIR, compact_text, gather_materials, load_json

REPO_ROOT = PROCESSED_DIR.parents[3]

THEME_KEYWORDS = {
    "ai_infra": ["ai", "data center", "datacenter", "storage", "robot", "semiconductor", "chip", "compute", "power"],
    "platform": ["subscription", "platform", "aum", "deposit", "crypto", "prediction", "user", "trading"],
    "consumer": ["traffic", "same-store", "consumer", "turnaround", "price", "margin", "china"],
    "earnings_quality": ["beat", "miss", "guidance", "forecast", "outlook", "margin", "cash flow", "fcf", "revenue"],
}

BROADCAST_AXIS_KEYWORDS = {
    "theme_proof": [
        "ai",
        "data center",
        "datacenter",
        "compute",
        "computing",
        "storage",
        "robot",
        "robotics",
        "semiconductor",
        "chip",
        "physical ai",
        "power",
        "electricity",
        "infrastructure",
    ],
    "expectation_risk": [
        "guidance",
        "forecast",
        "outlook",
        "miss",
        "cautious",
        "weaker",
        "falls",
        "drops",
        "tanks",
        "slips",
        "plummets",
        "surges",
        "jumps",
        "rallies",
        "after hours",
        "pre-market",
    ],
    "operating_proof": [
        "traffic",
        "same-store",
        "comparable",
        "comp sales",
        "ticket",
        "wait time",
        "margin",
        "turnaround",
        "china",
        "inventory",
        "pricing",
        "price increase",
    ],
    "business_model_shift": [
        "subscription",
        "subscriber",
        "membership",
        "aum",
        "assets under custody",
        "net deposits",
        "deposit",
        "prediction market",
        "crypto",
        "stablecoin",
        "platform",
        "recurring",
    ],
    "financial_quality": [
        "gross margin",
        "free cash flow",
        "fcf",
        "cash flow",
        "debt",
        "deleveraging",
        "eps",
        "ebit",
        "revenue",
        "profit",
        "beat",
        "raise",
        "raises",
    ],
    "read_through": [
        "samsung",
        "sk hynix",
        "hynix",
        "memory",
        "storage",
        "automotive",
        "industrial",
        "equipment",
        "supplier",
        "supply chain",
        "semiconductor equipment",
    ],
}

AXIS_LABELS = {
    "theme_proof": "테마 증명",
    "expectation_risk": "기대감/가이던스 리스크",
    "operating_proof": "운영 지표 증명",
    "business_model_shift": "비즈니스 모델 변화",
    "financial_quality": "재무 품질",
    "read_through": "연쇄 해석",
}

TICKER_LENS_HINTS = {
    "TER": {
        "axes": {
            "theme_proof": ["AI 수요가 반도체 테스트 장비 매출로 내려오는지 확인"],
            "expectation_risk": ["높아진 AI 하드웨어 기대감 대비 가이던스 리스크"],
            "read_through": ["반도체 장비와 로보틱스 확산의 선행 사례"],
        },
        "question": "AI 하드웨어 기대가 높아진 구간에서 가이던스가 조금만 밀려도 어떤 반응이 나오는가?",
        "slot": "실적/특징주",
    },
    "SBUX": {
        "axes": {
            "operating_proof": ["Back to Starbucks가 트래픽, 객단가, 대기시간, 마진으로 증명되는지 확인"],
            "expectation_risk": ["턴어라운드 기대가 실제 숫자로 확인되는지 점검"],
        },
        "question": "턴어라운드가 슬로건이 아니라 운영 지표로 확인되는가?",
        "slot": "실적/특징주",
    },
    "NXPI": {
        "axes": {
            "theme_proof": ["피지컬 AI와 차량용 반도체 회복을 확인"],
            "operating_proof": ["차량용 재고 해소와 가격 인상에도 수요가 견고한지 확인"],
            "read_through": ["데이터센터 밖 반도체 수요의 보조 사례"],
        },
        "question": "AI/반도체가 데이터센터 밖 차량용/피지컬 AI로도 확장되는가?",
        "slot": "실적/특징주",
    },
    "HOOD": {
        "axes": {
            "business_model_shift": ["수수료 의존에서 구독/AUM/순입금/예측시장 플랫폼으로 바뀌는지 확인"],
            "expectation_risk": ["실적 miss 이후에도 체질 개선이 남아 있는지 점검"],
        },
        "question": "단순 거래 수수료 기업에서 금융 플랫폼으로 체질이 바뀌고 있는가?",
        "slot": "실적/특징주",
    },
    "STX": {
        "axes": {
            "theme_proof": ["AI 수요가 스토리지 체인으로 확산되는지 확인"],
            "financial_quality": ["매출총이익률, FCF, 부채상환, EPS 가이던스가 모두 강한지 확인"],
            "read_through": ["메모리/스토리지와 한국 반도체로 이어지는 읽을거리"],
        },
        "question": "AI 인프라 수요가 GPU를 넘어 스토리지/메모리 체인으로 확장되는가?",
        "slot": "실적/특징주",
    },
}

TAG_AXIS_HINTS = {
    "ai_infra": {
        "theme_proof": ["AI 인프라/반도체/전력/스토리지 테마 증명 후보"],
        "read_through": ["AI 공급망과 관련 종목으로 이어질 수 있음"],
    },
    "platform": {
        "business_model_shift": ["플랫폼 수익 구조, 구독, 사용자/자산 흐름 점검 후보"],
    },
    "consumer": {
        "operating_proof": ["트래픽, 객단가, 마진, 지역별 수요로 턴어라운드 확인 후보"],
    },
    "megacap": {
        "theme_proof": ["시장 전체 멀티플과 지수 방향에 영향이 큰 대형주"],
        "expectation_risk": ["높은 기대치 대비 실적/가이던스 확인 필요"],
    },
}


def ticker_pattern(ticker: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Z0-9])(?:\\${re.escape(ticker)}|{re.escape(ticker)})(?![A-Z0-9])", re.I)


def material_text(material: dict) -> str:
    return " ".join(
        str(material.get(key) or "")
        for key in ["id", "title", "headline", "summary", "source", "url", "type", "raw_text", "text"]
    )


def load_finviz(date: str) -> dict[str, dict]:
    path = PROCESSED_DIR / date / "finviz-feature-stocks.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    return {
        item.get("ticker", "").upper(): item
        for item in payload.get("items", [])
        if item.get("ticker")
    }


def keyword_hits(text: str) -> dict[str, list[str]]:
    lowered = text.lower()
    hits = {}
    for tag, keywords in THEME_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword in lowered]
        if matched:
            hits[tag] = matched
    return hits


def contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower())
    if re.search(r"\W", keyword):
        return keyword.lower() in text
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def axis_hits(text: str, ticker: str, tags: set[str]) -> dict[str, list[str]]:
    lowered = text.lower()
    axes: dict[str, list[str]] = {}
    for axis, keywords in BROADCAST_AXIS_KEYWORDS.items():
        matched = [keyword for keyword in keywords if contains_keyword(lowered, keyword)]
        if matched:
            axes.setdefault(axis, []).extend(matched[:4])

    for tag in tags:
        for axis, hints in TAG_AXIS_HINTS.get(tag, {}).items():
            axes.setdefault(axis, []).extend(hints)

    for axis, hints in TICKER_LENS_HINTS.get(ticker, {}).get("axes", {}).items():
        axes.setdefault(axis, []).extend(hints)

    return {axis: dedupe(values)[:5] for axis, values in axes.items()}


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    rows = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        rows.append(normalized)
    return rows


def axis_score(axis: str, values: list[str]) -> int:
    base = {
        "theme_proof": 4,
        "expectation_risk": 3,
        "operating_proof": 3,
        "business_model_shift": 4,
        "financial_quality": 4,
        "read_through": 3,
    }[axis]
    return min(base, len(values) + 1)


def broadcast_question(ticker: str, axes: dict[str, list[str]], tags: set[str]) -> str:
    hint = TICKER_LENS_HINTS.get(ticker, {}).get("question")
    if hint:
        return hint
    if "business_model_shift" in axes:
        return "실적 반응보다 비즈니스 모델 변화가 더 중요한 종목인가?"
    if "operating_proof" in axes:
        return "턴어라운드나 수요 회복이 실제 운영 지표로 확인되는가?"
    if "theme_proof" in axes and "expectation_risk" in axes:
        return "큰 테마는 살아 있지만 높아진 기대치가 단기 변동성을 만들고 있는가?"
    if "ai_infra" in tags:
        return "AI 인프라 수요가 이 종목의 숫자로 확인되는가?"
    return "실적 캘린더 후보 중 방송에서 추가로 설명할 만한 훅이 있는가?"


def dashboard_slot(ticker: str, axes: dict[str, list[str]]) -> str:
    hint = TICKER_LENS_HINTS.get(ticker, {}).get("slot")
    if hint:
        return hint
    if "theme_proof" in axes or "financial_quality" in axes:
        return "실적/특징주"
    if "business_model_shift" in axes or "operating_proof" in axes:
        return "실적/특징주"
    return "watchlist"


def infer_tags(ticker: str, text: str) -> list[str]:
    lowered = text.lower()
    tags = set()
    if ticker in TICKER_LENS_HINTS:
        for axis in TICKER_LENS_HINTS[ticker].get("axes", {}):
            if axis in {"theme_proof", "read_through"}:
                tags.add("ai_infra")
            if axis == "business_model_shift":
                tags.add("platform")
            if axis == "operating_proof":
                tags.add("consumer")
    if any(contains_keyword(lowered, keyword) for keyword in ["ai", "semiconductor", "storage", "robot", "data center", "compute"]):
        tags.add("ai_infra")
    if any(contains_keyword(lowered, keyword) for keyword in ["subscription", "platform", "aum", "deposit", "subscriber", "crypto"]):
        tags.add("platform")
    if any(contains_keyword(lowered, keyword) for keyword in ["traffic", "consumer", "same-store", "turnaround", "china", "restaurant"]):
        tags.add("consumer")
    return sorted(tags)


def finviz_extra_rows(calendar_rows: list[dict], finviz: dict[str, dict]) -> list[dict]:
    existing = {row.get("ticker", "").upper() for row in calendar_rows}
    extras = []
    for ticker, item in sorted(finviz.items()):
        if ticker in existing or item.get("status") != "ok":
            continue
        blob = json.dumps(item, ensure_ascii=False)
        if ticker not in TICKER_LENS_HINTS and not re.search(r"earnings|guidance|outlook|forecast|revenue|eps|beat|miss", blob, re.I):
            continue
        extras.append(
            {
                "rank": 999,
                "ticker": ticker,
                "tags": infer_tags(ticker, blob),
                "source": "Finviz 특징주",
                "source_url": item.get("url") or "",
                "created_at": item.get("captured_at") or "",
                "captured_at": item.get("captured_at") or "",
                "image_refs": [item.get("screenshot_path")] if item.get("screenshot_path") else [],
                "source_note": "Earnings calendar에는 없지만 Finviz 특징주/실적 뉴스에서 보조 후보로 추가",
            }
        )
    return extras


def score_ticker(row: dict, materials: list[dict], finviz: dict[str, dict]) -> dict:
    ticker = row["ticker"]
    pattern = ticker_pattern(ticker)
    matches = []
    all_text = ""
    for material in materials:
        text = material_text(material)
        if pattern.search(text):
            matches.append(
                {
                    "id": material.get("id") or material.get("url") or material.get("title"),
                    "title": material.get("title") or material.get("summary") or "",
                    "source": material.get("source") or material.get("source_name") or "",
                    "url": material.get("url") or "",
                    "type": material.get("type") or "",
                    "summary": compact_text(material.get("summary"), 220),
                    "visual_local_path": material.get("visual_local_path") or "",
                }
            )
            all_text += "\n" + text

    finviz_item = finviz.get(ticker)
    if finviz_item:
        all_text += "\n" + json.dumps(finviz_item, ensure_ascii=False)

    tags = set(row.get("tags") or [])
    hits = keyword_hits(all_text)
    axes = axis_hits(all_text, ticker, tags)
    axis_scores = {axis: axis_score(axis, values) for axis, values in axes.items()}
    score = 0
    score += max(0, 12 - int(row.get("rank", 99)) // 3)
    score += 5 if finviz_item and finviz_item.get("status") == "ok" else 0
    score += min(6, len(matches) * 2)
    score += 3 if "ai_infra" in tags else 0
    score += 2 if "platform" in tags else 0
    score += 2 if "consumer" in tags else 0
    score += sum(min(3, len(values)) for values in hits.values())
    score += sum(axis_scores.values())

    reason_bits = []
    if row.get("rank", 99) <= 15:
        reason_bits.append("실적 캘린더 상단부 후보")
    if finviz_item and finviz_item.get("status") == "ok":
        reason_bits.append("Finviz 일봉/뉴스 수집 가능")
    if matches:
        reason_bits.append(f"기존 뉴스/X 후보 {len(matches)}건과 연결")
    if hits:
        reason_bits.append(" / ".join(f"{tag}: {', '.join(values[:3])}" for tag, values in hits.items()))
    if axes:
        reason_bits.append(
            "방송축 "
            + ", ".join(f"{AXIS_LABELS.get(axis, axis)}+{axis_scores[axis]}" for axis in sorted(axis_scores))
        )
    if not reason_bits:
        reason_bits.append("캘린더에는 있으나 추가 자료 확인 필요")

    status = "drilldown" if score >= 12 else "watch" if score >= 7 else "backlog"
    if row.get("rank", 99) <= 20 and ({"ai_infra", "platform"} & tags):
        status = "drilldown"
    elif row.get("rank", 99) <= 10 and tags:
        status = "drilldown"
    elif score >= 10 and axes:
        status = "drilldown"

    return {
        "ticker": ticker,
        "calendar_rank": row.get("rank"),
        "tags": sorted(tags),
        "score": score,
        "score_breakdown": {
            "calendar_position": max(0, 12 - int(row.get("rank", 99)) // 3),
            "finviz_capture": 5 if finviz_item and finviz_item.get("status") == "ok" else 0,
            "material_matches": min(6, len(matches) * 2),
            "tag_bonus": (3 if "ai_infra" in tags else 0) + (2 if "platform" in tags else 0) + (2 if "consumer" in tags else 0),
            "legacy_keyword_bonus": sum(min(3, len(values)) for values in hits.values()),
            "broadcast_axis_bonus": sum(axis_scores.values()),
        },
        "broadcast_axes": [
            {
                "axis": axis,
                "label": AXIS_LABELS.get(axis, axis),
                "score": axis_scores[axis],
                "evidence": values,
            }
            for axis, values in sorted(axes.items())
        ],
        "broadcast_question": broadcast_question(ticker, axes, tags),
        "dashboard_slot": dashboard_slot(ticker, axes),
        "status": status,
        "reason": "; ".join(reason_bits),
        "finviz_status": finviz_item.get("status") if finviz_item else "",
        "finviz_news": (finviz_item or {}).get("news", [])[:3],
        "finviz_summary": (finviz_item or {}).get("quote_summary", [])[:2],
        "screenshot_path": (finviz_item or {}).get("screenshot_path") or "",
        "matched_materials": matches[:6],
    }


def render_markdown(target_date: str, rows: list[dict]) -> str:
    lines = [
        "# Earnings Ticker Drilldown",
        "",
        f"- 대상일: `{target_date}`",
        f"- drilldown: `{sum(1 for row in rows if row['status'] == 'drilldown')}`",
        f"- watch: `{sum(1 for row in rows if row['status'] == 'watch')}`",
        "",
    ]
    for status in ["drilldown", "watch", "backlog"]:
        group = [row for row in rows if row["status"] == status]
        lines.extend([f"## {status}", ""])
        if not group:
            lines.extend(["- 없음", ""])
            continue
        for row in group:
            lines.extend(
                [
                    f"### {row['ticker']}",
                    "",
                    f"- 점수: `{row['score']}` / 캘린더 순서: `{row['calendar_rank']}` / 태그: {', '.join(row['tags']) or '-'}",
                    f"- 배치: `{row.get('dashboard_slot', '-')}`",
                    f"- 방송 질문: {row.get('broadcast_question') or '-'}",
                    f"- 이유: {row['reason']}",
                ]
            )
            if row.get("score_breakdown"):
                breakdown = row["score_breakdown"]
                lines.append(
                    "- 점수 분해: "
                    + ", ".join(f"{key} `{value}`" for key, value in breakdown.items() if value)
                )
            if row.get("broadcast_axes"):
                lines.append("- 방송축:")
                for axis in row["broadcast_axes"]:
                    evidence = ", ".join(axis.get("evidence") or []) or "-"
                    lines.append(f"  - {axis['label']} `+{axis['score']}`: {evidence}")
            if row["finviz_news"]:
                lines.append("- Finviz 뉴스:")
                for news in row["finviz_news"][:2]:
                    label = news.get("headline") or news.get("url") or ""
                    url = news.get("url") or ""
                    lines.append(f"  - [{label}]({url})" if url.startswith("http") else f"  - {label}")
            if row["matched_materials"]:
                lines.append("- 연결 후보:")
                for material in row["matched_materials"][:3]:
                    title = material["title"][:120]
                    url = material["url"]
                    lines.append(f"  - [{title}]({url})" if url.startswith("http") else f"  - {title}")
            if row["screenshot_path"]:
                screenshot_path = Path(row["screenshot_path"])
                if not screenshot_path.is_absolute():
                    screenshot_path = REPO_ROOT / screenshot_path
                lines.extend(["", f"![{row['ticker']} 일봉]({screenshot_path})"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--tickers", type=Path)
    parser.add_argument("--limit-news", type=int, default=100)
    parser.add_argument("--limit-x", type=int, default=80)
    parser.add_argument("--limit-visuals", type=int, default=40)
    args = parser.parse_args()

    ticker_path = args.tickers or (PROCESSED_DIR / args.date / "earnings-calendar-tickers.json")
    ticker_payload = load_json(ticker_path)
    materials = gather_materials(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    finviz = load_finviz(args.date)
    ticker_rows = ticker_payload.get("tickers", [])
    ticker_rows = ticker_rows + finviz_extra_rows(ticker_rows, finviz)
    rows = [
        score_ticker(row, materials, finviz)
        for row in ticker_rows
    ]
    rows.sort(key=lambda row: (-row["score"], row["calendar_rank"] or 999, row["ticker"]))

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "source_file": str(ticker_path),
        "ticker_count": len(rows),
        "tickers": rows,
    }
    json_path = processed_dir / "earnings-ticker-drilldown.json"
    md_path = notion_dir / "earnings-ticker-drilldown.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(args.date, rows), encoding="utf-8")
    print(json.dumps({"ok": True, "ticker_count": len(rows), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
