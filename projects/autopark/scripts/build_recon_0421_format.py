#!/usr/bin/env python3
"""Build a reconstruction page that matches the 04.21 dashboard layout."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

COLLECTED_AT = "26.04.28 05:00"


SHORT_TITLE_OVERRIDES = {
    "U.S. Stock Market Bull and Bear Indicator – S&P 500": "S&P500 강세/약세 지표",
    "Discretionary Positioning and Earnings Growth": "포지셔닝 vs 실적",
    "China has maintained massive crude inventories despite Middle East supply disruptions": "중국 원유 재고 방어선",
    "Oil retakes $110 in wait for US to respond to Iran proposal": "유가 110달러 재돌파",
    "yesterday TradingView USD/JPY: Dollar Elevated Near Multi-Year High Against Yen as Rate Decisions Loom": "달러/엔 고점권",
    "Bank of Japan keeps policy rate steady while raising inflation forecast on Iran war worries": "BOJ 동결과 물가 전망",
    "Indexed Returns of AI-Related Portfolios vs. Equal-Weight S&P 500": "AI 인프라 vs 소프트웨어",
    "GM raises 2026 guidance as tariffs credit boosts outlook": "GM 가이던스 상향",
    "GM raises 2026 guidance amid $500 million tariff refund, topping Wall Street's earnings expectations": "GM 가이던스 상향",
    "S&P 500 Index and Technical Score": "S&P 기술점수 과열 신호",
    "S&P 500 Trend Channel": "S&P 추세 채널",
    "S&P 500 Around Major Geopolitical Events Since 1939": "지정학 이벤트 후 S&P",
    "Different Market Sentiment Indicators": "시장심리 Risk-On 전환",
    "S&P 500 Index Returns Past 10 Years (May – October)": "Sell in May 반례",
    "S&P 500 Index Returns Past 10 Years (May - October)": "Sell in May 반례",
    "구글 직원 560명, AI 군사 이용 반대 공개서한": "구글 AI 군사이용 반발",
    "금 가격 금리 결정 앞두고 1.2% 하락": "금값, FOMC 앞두고 하락",
    "일본은행, 정책금리 동결 및 인플레이션 전망 상향": "BOJ 동결과 물가 전망",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing Markdown: {path}")
    return path.read_text(encoding="utf-8")


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url.startswith("http") else label


def display_url(url: str, fallback: str = "-") -> str:
    return f"[{url}]({url})" if url.startswith("http") else fallback


def compact_source_label(source: str, url: str = "") -> str:
    text = (source or "").strip()
    lowered = f"{text} {url}".lower()
    if "kobeissi" in lowered:
        return "KobeissiLetter"
    if "isabelnet" in lowered:
        return "Isabelnet"
    if "tradingview" in lowered:
        return "TradingView"
    if "yahoo" in lowered:
        return "Yahoo Finance"
    if "finviz" in lowered:
        return "Finviz"
    if "coingecko" in lowered:
        return "CoinGecko"
    if "tradingeconomics" in lowered:
        return "Trading Economics"
    if "cnn.com" in lowered or "fear-and-greed" in lowered:
        return "CNN"
    return text or source_label_from_url(url) or "-"


def source_label_from_url(url: str) -> str:
    if not url.startswith("http"):
        return ""
    match = re.match(r"^https?://(?:www\.)?([^/]+)", url)
    if not match:
        return ""
    domain = match.group(1).lower()
    labels = {
        "x.com": "X",
        "finviz.com": "Finviz",
        "finance.yahoo.com": "Yahoo Finance",
        "tradingview.com": "TradingView",
        "isabelnet.com": "Isabelnet",
        "coingecko.com": "CoinGecko",
        "ko.tradingeconomics.com": "Trading Economics",
        "edition.cnn.com": "CNN",
    }
    return labels.get(domain, domain)


def display_source(source: str, url: str) -> str:
    label = compact_source_label(source, url)
    return link(label, url) if url.startswith("http") else label


def clean_title(value: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", value or "").strip()


def short_material_title(title: str) -> str:
    title = clean_title(title)
    if title in SHORT_TITLE_OVERRIDES:
        return SHORT_TITLE_OVERRIDES[title]
    cleaned = re.sub(r"^yesterday\s+TradingView\s+", "", title, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[A-Z]{2,6}/[A-Z]{2,6}:\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= 34:
        return cleaned
    cut = re.split(r"[:;,.—–-]\s+", cleaned, maxsplit=1)[0].strip()
    if 8 <= len(cut) <= 34:
        return cut
    words = cleaned.split()
    return " ".join(words[:6]).rstrip(".,:;") + "..."


def render_top_summary(selection: dict) -> str:
    lines = ["# 🗞️ 주요 뉴스 요약", ""]
    for item in selection.get("dashboard_summary_bullets", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n\n"


def render_top_storylines(selection: dict) -> str:
    lines = ["# 📚 추천 스토리라인", ""]
    selected_items = {item.get("id"): item for item in selection.get("selected_items", [])}
    for index, storyline in enumerate(selection.get("storylines", []), start=1):
        material_titles = [
            selected_items[item_id].get("short_title") or short_material_title(selected_items[item_id].get("title") or "")
            for item_id in storyline.get("selected_item_ids", [])
            if item_id in selected_items and (selected_items[item_id].get("title") or selected_items[item_id].get("short_title"))
        ]
        lines.extend(
            [
                f"## {index}. {clean_title(storyline.get('title', ''))}",
                "",
                f"> {storyline.get('one_liner', '')}",
                "",
                "### 선정 이유",
                "",
                f"- {storyline.get('why_selected', '')}",
                "",
                "### 슬라이드 구성",
                "",
            ]
        )
        for flow in storyline.get("slide_flow", []):
            lines.append(f"- {flow}")
        if material_titles:
            lines.append("")
            lines.append(f"참고 자료: {' → '.join(f'`{title}`' for title in material_titles)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n\n"


def render_today_misc(selection: dict, target_date: str) -> str:
    lines = ["## 2. 오늘의 이모저모", ""]
    selected_items = selection.get("selected_items", [])
    display_date = short_date(target_date)
    for item in selected_items:
        original_title = item.get("title") or item.get("id") or "Untitled"
        title = item.get("short_title") or short_material_title(original_title)
        url = item.get("url") or ""
        quote = item.get("storyline_fit") or item.get("selection_reason") or ""
        details = unique_nonempty(
            [
                item.get("selection_reason"),
                item.get("storyline_fit"),
                item.get("verification_note"),
            ]
        )
        lines.extend(
            [
                f"### {title}",
                "",
                f"> {quote}",
                "",
                f"출처: {display_source(item.get('source') or '-', url)} · 작성 시점: `{display_date}`",
                "",
            ]
        )
        if item.get("visual_local_path"):
            lines.extend([f"![{title}]({item['visual_local_path']})", ""])
        if original_title != title:
            lines.append(f"- 원문: {original_title}")
        for detail in details[:2]:
            lines.append(f"- {detail}")
        lines.append("")
    return "\n".join(lines).strip() + "\n\n"


def render_collection_status(selection: dict, finviz_enrichment: dict | None = None) -> str:
    selected_items = selection.get("selected_items", [])
    visual_count = sum(1 for item in selected_items if item.get("visual_local_path"))
    source_counts: dict[str, int] = {}
    image_counts: dict[str, int] = {}
    for item in selected_items:
        source = item.get("source") or "Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
        if item.get("visual_local_path"):
            image_counts[source] = image_counts.get(source, 0) + 1

    rows = []
    rows.append(("뉴스/시각자료", "선별 자료", "성공", str(len(selected_items)), str(visual_count), "스토리라인 후보에 연결"))
    for source, count in sorted(source_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:6]:
        rows.append(("소스", compact_source_label(source), "성공", str(count), str(image_counts.get(source, 0)), "오늘의 이모저모 반영"))
    if finviz_enrichment:
        items = finviz_enrichment.get("items") or []
        ok_items = [item for item in items if item.get("status") == "ok"]
        image_items = [item for item in ok_items if item.get("screenshot_path")]
        rows.append(("특징주", "Finviz", "성공", str(len(ok_items)), str(len(image_items)), "일봉/최근 뉴스 반영"))

    lines = ["## 수집 현황", ""]
    lines.extend(
        [
            "| 구분 | 소스 | 상태 | 수집 | 이미지 | 비고 |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        safe = [str(value).replace("|", "/") for value in row]
        lines.append("| " + " | ".join(safe) + " |")
    return "\n".join(lines).strip() + "\n\n"


def short_date(value: str) -> str:
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", value or "")
    if not match:
        return value or "-"
    return f"{match.group(1)[2:]}.{match.group(2)}.{match.group(3)}"


def unique_nonempty(values: list[str | None]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        output.append(cleaned)
    return output


def replace_between(markdown: str, start_pattern: str, end_pattern: str, replacement: str) -> str:
    pattern = re.compile(start_pattern + r".*?(?=" + end_pattern + r")", flags=re.MULTILINE | re.DOTALL)
    updated, count = pattern.subn(replacement, markdown)
    if count != 1:
        raise SystemExit(f"Expected one replacement for {start_pattern}, got {count}")
    return updated


def strip_pipeline_memo(markdown: str) -> str:
    return re.sub(r"\n# 파이프라인 점검 메모\n.*\Z", "\n", markdown, flags=re.DOTALL).rstrip() + "\n"


def flatten_metadata_bullets(markdown: str) -> str:
    label_map = {
        "출처": "출처",
        "데이터": "데이터",
        "캡처": "수집 시점",
        "수집 시점": "수집 시점",
        "작성 일자": "작성 시점",
        "작성 시점": "작성 시점",
    }
    metadata_labels = tuple(label_map)
    output: list[str] = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        matches: list[tuple[str, str]] = []
        cursor = index
        while cursor < len(lines):
            match = re.match(r"^-\s+([^:]+):\s+(.+)$", lines[cursor])
            if not match or match.group(1).strip() not in metadata_labels:
                break
            matches.append((match.group(1).strip(), match.group(2).strip()))
            cursor += 1
        if len(matches) >= 2:
            output.append(" · ".join(f"{label_map[label]}: {value}" for label, value in matches))
            index = cursor
            continue
        output.append(line)
        index += 1
    return "\n".join(output) + ("\n" if markdown.endswith("\n") else "")


def normalize_market_now(markdown: str) -> str:
    """Remove internal implementation notes from the fixed market section."""
    markdown = re.sub(r"\n- 필요 캡처: .+", "", markdown)
    markdown = re.sub(r"\n- 필요 자료: .+", "", markdown)
    markdown = re.sub(r"\n- 상태: .+", "", markdown)
    markdown = re.sub(r"\n- 메모: .+", "", markdown)
    markdown = re.sub(r"\n- 해석 포인트: .+", "", markdown)

    markdown = re.sub(r"^최종 수정 일시: (.+?) 기준 준비 대시보드 역구성 초안$", r"최종 수정 일시: \1", markdown, flags=re.MULTILINE)
    markdown = markdown.replace("- 출처: [Finviz](https://finviz.com/#)", "- 출처: [Finviz](https://finviz.com/#)")
    markdown = markdown.replace(
        "- 출처: [Finviz S&P500 Map](https://finviz.com/map.ashx?t=sec)",
        "- 출처: [Finviz](https://finviz.com/map.ashx?t=sec)",
    )
    markdown = markdown.replace(
        "- 출처: [CNN Fear & Greed](https://edition.cnn.com/markets/fear-and-greed)",
        "- 출처: [CNN](https://edition.cnn.com/markets/fear-and-greed)",
    )
    markdown = markdown.replace("- 캡처: 테스트 캡처 `26.04.27`", f"- 수집 시점: `{COLLECTED_AT}`")
    markdown = markdown.replace("- 자동 추출: `66 (Greed)`", "- CNN Fear & Greed 기준 66, Greed 구간")

    markdown = markdown.replace(
        "### 10년물 국채금리\n\n"
        "- 출처: FRED `DGS10`\n"
        "- 제작: Datawrapper `nofn2`",
        "### 10년물 국채금리\n\n"
        "- 출처: [Yahoo Finance](https://finance.yahoo.com/quote/%5ETNX)\n"
        f"- 수집 시점: `{COLLECTED_AT}`",
    )
    markdown = markdown.replace(
        "### 경제지표\n\n"
        "- 출처: Trading Economics 공개 경제캘린더\n"
        "- 제작: Datawrapper `mPSRp`",
        "### 경제지표\n\n"
        "- 출처: [Trading Economics](https://ko.tradingeconomics.com/calendar)\n"
        f"- 수집 시점: `{COLLECTED_AT}`",
    )
    markdown = re.sub(
        r"### WTI / 브렌트\n\n"
        r"- 출처: FRED `DCOILWTICO`, `DCOILBRENTEU`\n"
        r"- 제작: Datawrapper `TYqZk`, `jZDeO`\n\n"
        r"!\[WTI\]\(([^)]+)\)\n\n"
        r"!\[브렌트\]\(([^)]+)\)",
        "### WTI\n\n"
        "- 출처: [Yahoo Finance](https://finance.yahoo.com/quote/CL%3DF)\n"
        f"- 수집 시점: `{COLLECTED_AT}`\n\n"
        r"![WTI](\1)"
        "\n\n"
        "### 브렌트\n\n"
        "- 출처: [Yahoo Finance](https://finance.yahoo.com/quote/BZ%3DF)\n"
        f"- 수집 시점: `{COLLECTED_AT}`\n\n"
        r"![브렌트](\2)",
        markdown,
    )
    markdown = re.sub(
        r"### 달러 인덱스 / 원달러 / 비트코인\n\n"
        r"- 출처: FRED `DTWEXBGS`, `DEXKOUS`; CoinGecko `bitcoin`\n\n"
        r"!\[달러 지수\]\(([^)]+)\)\n\n"
        r"!\[원달러\]\(([^)]+)\)\n\n"
        r"!\[비트코인\]\(([^)]+)\)",
        "### DXY\n\n"
        "- 출처: [Yahoo Finance](https://finance.yahoo.com/quote/DX-Y.NYB)\n"
        f"- 수집 시점: `{COLLECTED_AT}`\n\n"
        r"![달러 지수](\1)"
        "\n\n"
        "### 원/달러\n\n"
        "- 출처: [Yahoo Finance](https://finance.yahoo.com/quote/KRW%3DX)\n"
        f"- 수집 시점: `{COLLECTED_AT}`\n\n"
        r"![원달러](\2)"
        "\n\n"
        "### 비트코인\n\n"
        "- 출처: [CoinGecko](https://www.coingecko.com/en/coins/bitcoin)\n"
        f"- 수집 시점: `{COLLECTED_AT}`\n\n"
        r"![비트코인](\3)",
        markdown,
    )
    return markdown


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recon", type=Path)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--feature-stocks", type=Path)
    parser.add_argument("--finviz-enrichment", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = load_json(args.selection.resolve())
    selection = payload.get("selection") or {}
    for item in selection.get("selected_items", []):
        item["short_title"] = item.get("short_title") or short_material_title(item.get("title") or item.get("id") or "")
    finviz_enrichment = load_json(args.finviz_enrichment.resolve()) if args.finviz_enrichment else None
    target_date = payload.get("target_date") or "unknown"
    markdown = read(args.recon.resolve())
    markdown = replace_between(markdown, r"^# 주요 뉴스 요약\n", r"^# 추천 스토리라인\n", render_top_summary(selection))
    markdown = replace_between(markdown, r"^# 추천 스토리라인\n", r"^# 자료 수집\n", render_top_storylines(selection))
    markdown = markdown.replace("# 자료 수집", "# 🤖 자료 수집", 1)
    markdown = markdown.replace("# 🤖 자료 수집\n\n", "# 🤖 자료 수집\n\n" + render_collection_status(selection, finviz_enrichment), 1)
    markdown = replace_between(markdown, r"^## 2\. 오늘의 이모저모\n", r"^## 3\. ", render_today_misc(selection, target_date))
    if args.feature_stocks:
        markdown = replace_between(
            markdown,
            r"^## 3\. 실적/특징주 분석\n",
            r"^# 파이프라인 점검 메모\n|\Z",
            read(args.feature_stocks.resolve()),
        )
    markdown = normalize_market_now(markdown)
    markdown = flatten_metadata_bullets(markdown)
    markdown = strip_pipeline_memo(markdown)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
