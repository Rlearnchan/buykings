#!/usr/bin/env python3
"""Build 04.21-style feature-stock cards for a reconstruction page."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"


FEATURE_SETS = {
    "26.04.22": {
        "target_date": "2026-04-28",
        "cards": [
            {
                "title": "이번 주 실적발표 스케줄",
                "quote": "당일 실적 이벤트와 이번 주 대형주 실적 일정을 먼저 확인해, 장중 특징주 후보를 좁히는 자료입니다.",
                "source_url": "https://x.com/eWhispers",
                "date_label": "26.04.22",
                "date_kind": "작성 시점",
                "details": [
                    "실적 시즌의 핵심 대형주와 섹터 이벤트를 한눈에 확인하는 출발점입니다.",
                    "인튜이티브 서지컬과 유나이티드 에어라인은 당일 실적 반응 확인 대상으로 분리합니다.",
                ],
            },
            {
                "title": "인튜이티브 서지컬",
                "quote": "의료장비 섹터에서 실적 서프라이즈와 로봇수술 수요를 동시에 확인할 수 있는 당일 실적 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=ISRG&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": [
                    "티커: ISRG",
                    "필요 자료: 실적 요약, 5분봉, 일봉",
                    "해석 포인트: 실적 서프라이즈, 가이던스, 의료장비 섹터 심리",
                ],
            },
            {
                "title": "유나이티드 에어라인",
                "quote": "항공 수요와 유가 부담, 가이던스를 함께 볼 수 있는 경기민감 실적 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=UAL&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": [
                    "티커: UAL",
                    "필요 자료: 실적 요약, 일봉",
                    "해석 포인트: 여행 수요, 유가 부담, 비용 통제, 향후 가이던스",
                ],
            },
            {
                "title": "스페이스X IPO와 AI 인프라 부채",
                "quote": "우주기업 IPO 기대 뒤에 AI 인프라 투자와 부채 증가가 숨어 있다는 별도 성장주 리스크 소재입니다.",
                "source_url": "https://www.sec.gov/edgar/search/#/q=SpaceX",
                "date_label": "26.04.22",
                "date_kind": "작성 시점",
                "details": [
                    "확인할 축: IPO 준비, 자본 지출, AI 인프라 임대 계약, 현금흐름",
                    "방송 활용: 비상장 성장주도 AI 인프라 비용 경쟁에서 자유롭지 않다는 연결고리",
                    "확인 필요: 원문 서류/보도 출처가 확보되기 전에는 수치 인용을 보수적으로 다룹니다.",
                ],
            },
            {
                "title": "메가캡 성장주 및 기술주의 상대적 강도",
                "quote": "시장 전체보다 성장주와 기술주가 더 강한지 확인해, 특징주 묶음의 배경으로 쓰는 상대강도 자료입니다.",
                "source_url": "https://finviz.com/map.ashx?t=sec",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": [
                    "기술주가 시장 대비 강한지 먼저 확인한 뒤 개별 차트로 내려갑니다.",
                    "MSFT, PANW, AMD, COIN, CSCO, MRVL, ON, COHR를 같은 묶음에서 봅니다.",
                    "해석 포인트: AI/반도체/네트워크/크립토 관련 위험선호 확산 여부",
                ],
            },
            {
                "title": "마이크로소프트",
                "quote": "대형 AI 플랫폼과 클라우드 기대가 유지되는지 확인하는 메가캡 대표 차트입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=MSFT&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: MSFT", "필요 자료: 일봉, 당일 뉴스, 거래량", "역할: 메가캡 성장주 상대강도 확인"],
            },
            {
                "title": "팔로알토 네트웍스",
                "quote": "사이버보안 소프트웨어가 AI/클라우드 인프라 랠리에 동참하는지 보는 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=PANW&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: PANW", "필요 자료: 일봉, 당일 뉴스, 거래량", "역할: 보안 소프트웨어 위험선호 확인"],
            },
            {
                "title": "AMD",
                "quote": "AI 반도체 기대와 기술주 상대강도를 동시에 확인할 수 있는 대표 반도체 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=AMD&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: AMD", "필요 자료: 일봉, 당일 뉴스, 거래량", "역할: AI 반도체 투자심리 확인"],
            },
            {
                "title": "코인베이스",
                "quote": "비트코인과 위험자산 선호가 되살아날 때 가장 민감하게 반응하는 크립토 베타 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=COIN&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: COIN", "필요 자료: 일봉, 비트코인 동행 여부, 거래량", "역할: 위험자산 선호 회복 확인"],
            },
            {
                "title": "시스코",
                "quote": "데이터센터 네트워크 장비 수요를 통해 AI 인프라가 하드웨어 전반으로 확산되는지 보는 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=CSCO&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: CSCO", "필요 자료: 일봉, 네트워크 장비 관련 뉴스", "역할: 데이터센터 네트워크 수혜 확인"],
            },
            {
                "title": "마벨 테크놀로지",
                "quote": "AI 커스텀 칩과 데이터센터 반도체 기대를 확인하는 고베타 반도체 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=MRVL&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: MRVL", "필요 자료: 일봉, AI 반도체 뉴스", "역할: AI 인프라 반도체 확산 확인"],
            },
            {
                "title": "온 세미컨덕터",
                "quote": "반도체 섹터 전반의 강세가 전력/자동차 반도체까지 번지는지 보는 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=ON&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: ON", "필요 자료: 일봉, 반도체 섹터 동행 여부", "역할: 섹터 확산 확인"],
            },
            {
                "title": "코히런트",
                "quote": "광통신과 AI 데이터센터 인프라 수요가 주가에 반영되는지 확인하는 후보입니다.",
                "source_url": "https://finviz.com/quote.ashx?t=COHR&p=d",
                "date_label": "26.04.22 05:30",
                "date_kind": "수집 시점",
                "details": ["티커: COHR", "필요 자료: 일봉, 광통신/데이터센터 관련 뉴스", "역할: AI 인프라 주변주 확산 확인"],
            },
        ],
    }
}


ISSUE_QUOTE_OVERRIDES = {
    "ISRG": "Q1 실적이 예상치를 웃돌고 연간 전망을 상향하면서 로봇수술 수요 회복이 부각됐습니다.",
    "UAL": "아메리칸항공과의 합병 논의가 결렬됐다는 보도로 항공주 재편 기대가 흔들렸습니다.",
    "MSFT": "OpenAI 매출·사용자 목표 미달 보도와 Microsoft-OpenAI 계약 재조정 이슈가 AI 플랫폼 기대를 압박했습니다.",
    "PANW": "ServiceNow·IBM 실적 이후 AI 소프트웨어 우려가 재점화되며 보안 소프트웨어주도 점검 대상이 됐습니다.",
    "AMD": "OpenAI 목표 미달 보도가 AI 인프라 종목 전반을 압박하며 AMD 등 반도체주에 부담으로 작용했습니다.",
    "COIN": "위험자산 반등 장세와 크립토 관련 뉴스가 겹치며 Coinbase 등 거래 플랫폼주가 주목받았습니다.",
    "CSCO": "Cisco가 양자 네트워킹 스위치 프로토타입을 공개하며 인프라 장비주 모멘텀이 부각됐습니다.",
    "MRVL": "Marvell의 Celestial AI 관련 주문 취소와 POET 급락 소식이 AI 커스텀칩 기대에 균열을 냈습니다.",
    "ON": "onsemi가 NIO·Geely와 차세대 EV 플랫폼 협력을 확대하며 전력·자동차 반도체 수요가 부각됐습니다.",
    "COHR": "실적 발표 일정과 AI 광통신 수요 기대를 함께 점검할 수 있는 데이터센터 주변주로 묶였습니다.",
}


def card_ticker(card: dict) -> str | None:
    for detail in card.get("details", []):
        if detail.startswith("티커: "):
            return detail.split(":", 1)[1].strip().upper()
    source_url = card.get("source_url", "")
    if "finviz.com/quote.ashx" not in source_url:
        return None
    marker = "t="
    if marker not in source_url:
        return None
    return source_url.split(marker, 1)[1].split("&", 1)[0].upper()


def load_finviz_enrichment(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["ticker"].upper(): item
        for item in payload.get("items", [])
        if item.get("ticker") and item.get("status") == "ok"
    }


def load_x_enrichment(path: Path | None) -> dict[str, dict]:
    if not path or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for post in payload.get("posts", []):
        source_id = post.get("source_id") or ""
        images = [
            image
            for image in post.get("image_refs", [])
            if image.get("download_status") == "ok" and image.get("local_path")
        ]
        if source_id and images and source_id not in result:
            result[source_id] = {
                "visual_local_path": images[0]["local_path"],
                "status_url": post.get("status_url") or post.get("url") or "",
                "published_at": post.get("published_at") or post.get("created_at") or post.get("created_at_inferred") or "",
                "text": post.get("text") or "",
            }
    return result


def display_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:16].replace("T", " ")
    kst = parsed.astimezone(timezone(timedelta(hours=9)))
    return kst.strftime("%y.%m.%d %H:%M")


def enrich_cards(cards: list[dict], finviz: dict[str, dict]) -> list[dict]:
    enriched = []
    for card in cards:
        next_card = dict(card)
        ticker = card_ticker(card)
        item = finviz.get(ticker or "")
        if item:
            next_card["visual_local_path"] = item.get("screenshot_path")
            next_card["finviz_news"] = item.get("news") or []
            next_card["finviz_summary"] = item.get("quote_summary") or []
            next_card["date_label"] = card.get("date_label") or item.get("captured_at", "")[:10]
            next_card["date_kind"] = normalize_date_kind(card.get("date_kind", "수집 시점"))
        enriched.append(next_card)
    return enriched


def enrich_x_cards(cards: list[dict], x_posts: dict[str, dict]) -> list[dict]:
    enriched = []
    for card in cards:
        next_card = dict(card)
        source_url = card.get("source_url", "").lower()
        if "x.com/ewhispers" in source_url:
            post = x_posts.get("fixed-earnings-calendar") or x_posts.get("x-ewhispers")
            if post:
                next_card["visual_local_path"] = post.get("visual_local_path")
                next_card["source_url"] = post.get("status_url") or card["source_url"]
                if post.get("published_at"):
                    next_card["date_label"] = display_datetime(post["published_at"])
                post_text = (post.get("text") or "").strip()
                if post_text:
                    next_card["details"] = [*card.get("details", [])[:2], post_text[:220]]
        enriched.append(next_card)
    return enriched


def compact_detail(detail: str) -> str | None:
    if detail.startswith("티커: "):
        return detail
    if detail.startswith("필요 자료: "):
        return None
    if detail.startswith("역할: "):
        return detail.replace("역할: ", "", 1)
    if detail.startswith("해석 포인트: "):
        return detail.replace("해석 포인트: ", "", 1)
    if detail.startswith("확인할 축: "):
        return detail.replace("확인할 축: ", "", 1)
    if detail.startswith("방송 활용: "):
        return detail.replace("방송 활용: ", "", 1)
    return detail


def normalize_date_kind(value: str) -> str:
    return {
        "캡처": "수집 시점",
        "작성 일자": "작성 시점",
    }.get(value, value or "작성 시점")


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url.startswith("http") else label


def source_label(url: str) -> str:
    lowered = url.lower()
    if "x.com/ewhispers" in lowered:
        return "Earnings Whispers"
    if "x.com/" in lowered:
        return "X"
    if "finviz.com" in lowered:
        return "Finviz"
    if "sec.gov" in lowered:
        return "SEC"
    match = re.match(r"^https?://(?:www\.)?([^/]+)", lowered)
    return match.group(1) if match else url


def card_quote(card: dict, ticker: str | None) -> str | None:
    if not ticker:
        return None
    if ticker in ISSUE_QUOTE_OVERRIDES:
        return ISSUE_QUOTE_OVERRIDES[ticker]
    if card.get("finviz_summary"):
        return card["finviz_summary"][0]
    if card.get("finviz_news"):
        return card["finviz_news"][0].get("headline")
    return card.get("quote")


def render_markdown(page_date: str, cards: list[dict]) -> str:
    lines = ["## 3. 실적/특징주 분석", ""]
    for card in cards:
        ticker = card_ticker(card)
        title = f"{card['title']} ({ticker})" if ticker else card["title"]
        heading = "####" if ticker else "###"
        lines.extend([f"{heading} {title}", ""])
        quote = card_quote(card, ticker)
        if quote:
            lines.extend([f"> {quote}", ""])
        lines.extend(
            [
                f"출처: {link(source_label(card['source_url']), card['source_url'])} · {normalize_date_kind(card.get('date_kind', '작성 시점'))}: `{card['date_label']}`",
                "",
            ]
        )
        details = [compact_detail(detail) for detail in card.get("details", [])]
        for detail in [detail for detail in details if detail][:1]:
            if detail.startswith("티커: "):
                continue
            lines.append(f"- {detail}")
        if card.get("finviz_summary") and not quote:
            for summary in card["finviz_summary"][:1]:
                lines.append(f"- {summary}")
        if card.get("visual_local_path"):
            lines.extend(["", f"![{title}]({card['visual_local_path']})"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-date", default="26.04.22")
    parser.add_argument("--date", default=None)
    parser.add_argument("--finviz-enrichment", type=Path)
    parser.add_argument("--x-enrichment", type=Path)
    args = parser.parse_args()

    feature_set = FEATURE_SETS.get(args.page_date)
    if not feature_set:
        raise SystemExit(f"No feature stock set for {args.page_date}")
    target_date = args.date or feature_set["target_date"]
    cards = enrich_cards(feature_set["cards"], load_finviz_enrichment(args.finviz_enrichment))
    cards = enrich_x_cards(cards, load_x_enrichment(args.x_enrichment))
    payload = {
        "ok": True,
        "page_date": args.page_date,
        "target_date": target_date,
        "source_note": "Reverse-engineered from local broadcast PPT text for dashboard planning only.",
        "cards": cards,
    }
    processed_dir = PROCESSED_DIR / target_date
    notion_dir = RUNTIME_NOTION_DIR / target_date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "feature-stock-cards.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output = notion_dir / "feature-stock-cards.md"
    output.write_text(render_markdown(args.page_date, cards), encoding="utf-8")
    print(json.dumps({"ok": True, "cards": len(cards), "markdown": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
