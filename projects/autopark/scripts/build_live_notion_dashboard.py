#!/usr/bin/env python3
"""Render a Notion-ready live experiment dashboard for a target date."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
CHART_DIR = PROJECT_ROOT / "charts"
LOG_DIR = PROJECT_ROOT / "runtime" / "logs"
EXPORTS_DIR = PROJECT_ROOT / "exports" / "current"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def short_dt(value: str | None) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Seoul"))
        return dt.strftime("%H:%M")
    except ValueError:
        return value[:16]


def display_dt(value: str | None) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Seoul"))
        if dt.strftime("%H:%M") == "00:00":
            return dt.strftime("%y.%m.%d")
        return dt.strftime("%y.%m.%d %H:%M")
    except ValueError:
        if re.match(r"\d{4}-\d{2}-\d{2}$", value):
            return datetime.fromisoformat(value).strftime("%y.%m.%d")
        return value[:16]


def display_date_title(target_date: str) -> str:
    dt = datetime.fromisoformat(target_date)
    return dt.strftime("%y.%m.%d")


def clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url.startswith("http") else label


def source_label(value: str | None, url: str | None = None) -> str:
    text = clean(value or "")
    blob = f"{text} {url or ''}".lower()
    if "kobeissi" in blob:
        return "KobeissiLetter"
    if "wallstengine" in blob or "wall st engine" in blob:
        return "Wall St Engine"
    if "isabelnet" in blob:
        return "IsabelNet"
    if "reuters" in blob:
        return "Reuters"
    if "charliebilello" in blob or "charlie bilello" in blob:
        return "Charlie Bilello"
    if "bloomberg" in blob:
        return "Bloomberg"
    if "cnbc" in blob:
        return "CNBC"
    if "yahoo" in blob:
        return "Yahoo Finance"
    if "investinq" in blob or "stockmarket.news" in blob:
        return "StockMarket.News"
    if "finviz" in blob:
        return "Finviz"
    if "earnings whispers" in blob or "ewhispers" in blob:
        return "Earnings Whispers"
    if "coingecko" in blob:
        return "CoinGecko"
    return clean(text or "source", 24)


def row_blob(row: dict) -> str:
    return clean(
        " ".join(
            str(row.get(key) or "")
            for key in ["title", "headline", "summary", "text", "source", "type", "radar_question"]
        )
    ).lower()


def is_fed_material(row: dict) -> bool:
    blob = row_blob(row)
    return any(term in blob for term in ["fed", "fomc", "powell", "rate cut", "rate-cut", "interest rate", "fedwatch", "polymarket", "금리", "연준"])


def infer_today_axis(storylines: list[dict], candidates: list[dict]) -> str:
    blob = " ".join(
        clean(str(item.get(key) or ""))
        for item in [*storylines, *candidates[:40]]
        for key in ["title", "one_liner", "summary", "text"]
    ).lower()
    has_ai = any(term in blob for term in ["ai", "cloud", "capex", "data center", "semiconductor", "nvidia", "big tech"])
    has_earnings = any(term in blob for term in ["earnings", "eps", "revenue", "guidance", "실적"])
    has_fed = any(term in blob for term in ["fed", "fomc", "powell", "rate cut", "금리", "연준"])
    has_oil = any(term in blob for term in ["oil", "wti", "brent", "opec", "iran", "유가", "원유"])
    if (has_ai or has_earnings) and (has_fed or has_oil):
        return "실적 성장과 AI 기대가 금리·유가 부담을 이길 수 있는가"
    if has_earnings:
        return "실적 숫자가 높아진 기대를 다시 정당화할 수 있는가"
    if has_fed:
        return "Fed 완화 기대와 인플레 재상승 우려 중 무엇이 시장을 움직이는가"
    if has_oil:
        return "에너지 리스크가 위험선호를 누를 만큼 커졌는가"
    if storylines:
        return clean(storylines[0].get("one_liner") or storylines[0].get("title"), 120)
    return "위험선호와 실적 검증 중 어느 쪽이 오늘 시장의 중심인가"


def first_existing(paths: list[Path]) -> str:
    for path in paths:
        if path.exists():
            return str(path)
    return ""


def screenshot_for(target_date: str, *names: str) -> str:
    matches = screenshots_for(target_date, *names)
    return matches[0] if matches else ""


def screenshots_for(target_date: str, *names: str) -> list[str]:
    roots = [
        PROJECT_ROOT / "runtime" / "screenshots" / target_date,
        PROJECT_ROOT / "runtime" / "assets" / target_date,
        PROJECT_ROOT / "exports" / "current",
    ]
    paths = []
    for root in roots:
        for name in names:
            paths.extend(root.glob(name))
            paths.extend(root.glob(f"**/{name}"))
    return [str(path) for path in sorted(set(paths))]


def image_path(value: str | None) -> str:
    if not value:
        return ""
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(REPO_ROOT / path)


def chart_rows() -> list[tuple[str, str, str, str, str]]:
    rows = []
    for chart_id in ["us10y", "crude-oil-wti", "crude-oil-brent", "dollar-index", "usd-krw", "bitcoin"]:
        spec = load_json(CHART_DIR / f"{chart_id}-datawrapper.json")
        if not spec:
            continue
        png = EXPORTS_DIR / f"{chart_id}.png"
        rows.append(
            (
                chart_id,
                spec.get("title", chart_id),
                spec.get("subtitle", ""),
                spec.get("source_name", "-"),
                spec.get("source_url", ""),
            )
        )
    return rows


def run_window(target_date: str) -> str:
    payload = load_json(LOG_DIR / f"{target_date}-live-all-in-one.json")
    steps = payload.get("steps") or []
    wanted = {
        "collect news batch a",
        "collect news batch b",
        "collect x timeline",
        "build visual cards",
        "capture finviz-index-futures",
        "capture finviz-sp500-heatmap",
        "capture finviz-russell-heatmap",
        "fetch economic calendar",
    }
    starts = []
    ends = []
    for step in steps:
        if step.get("name") not in wanted:
            continue
        try:
            if step.get("started_at"):
                starts.append(datetime.fromisoformat(step["started_at"]).astimezone(ZoneInfo("Asia/Seoul")))
            if step.get("ended_at"):
                ends.append(datetime.fromisoformat(step["ended_at"]).astimezone(ZoneInfo("Asia/Seoul")))
        except ValueError:
            continue
    if starts and ends:
        return f"{min(starts).strftime('%H:%M')}-{max(ends).strftime('%H:%M')}"
    return ""


def source_status_lines(target_date: str) -> list[str]:
    processed = PROCESSED_DIR / target_date
    lines = []
    for name in ["today-misc-batch-a-candidates.json", "today-misc-batch-b-candidates.json", "x-timeline-posts.json"]:
        payload = load_json(processed / name)
        if not payload:
            continue
        ok_count = sum(1 for row in payload.get("source_results", []) if row.get("status") == "ok")
        error_count = sum(1 for row in payload.get("source_results", []) if row.get("status") == "error")
        item_count = len(payload.get("candidates") or payload.get("posts") or [])
        captured = short_dt(payload.get("captured_at"))
        lines.append(f"- `{name}`: {captured} 수집, 성공 {ok_count}, 실패 {error_count}, 후보 {item_count}")
        for row in payload.get("source_results", []):
            if row.get("status") == "error":
                lines.append(f"  - 실패: {row.get('source_id')} - {clean(row.get('error'), 120)}")
    finviz = load_json(processed / "finviz-feature-stocks.json")
    if finviz:
        statuses = Counter(row.get("status") for row in finviz.get("items", []))
        lines.append(f"- `finviz-feature-stocks.json`: 성공 {statuses.get('ok', 0)}, 차단 {statuses.get('blocked', 0)}")
    return lines


def core_keyword_rows(*payloads: dict, limit: int = 8) -> list[dict]:
    themes = [
        ("유가/에너지 리스크", ["oil", "crude", "brent", "wti", "opec", "uae", "iran", "hormuz", "energy", "xle"]),
        ("AI 인프라/빅테크", ["ai", "artificial intelligence", "data center", "cloud", "capex", "tpu", "openai", "nvidia"]),
        ("실적/가이던스", ["earnings", "revenue", "profit", "guidance", "eps", "results", "quarter"]),
        ("연준/금리", ["fed", "powell", "rate", "treasury", "yield", "inflation", "dissent"]),
        ("위험선호/포지셔닝", ["call option", "risk appetite", "positioning", "rally", "valuation", "market cap"]),
        ("소비/재량주", ["consumer", "discretionary", "retail", "spending", "visa", "mastercard"]),
        ("중국/무역", ["china", "tariff", "trade", "export", "import", "beijing"]),
        ("단신/화제성", ["musk", "altman", "openai", "charles", "king", "spacex", "ipo"]),
    ]
    rows_by_theme = {
        label: {"keyword": label, "count": 0, "sources": set(), "examples": []}
        for label, _ in themes
    }
    for payload in payloads:
        items = (payload.get("candidates") or []) + (payload.get("posts") or [])
        for item in items:
            text = clean(
                " ".join(
                    str(item.get(key) or "")
                    for key in ["headline", "title", "summary", "text", "source", "type"]
                )
            )
            lowered = text.lower()
            if not lowered:
                continue
            source = source_label(item.get("source") or item.get("type"), item.get("url") or "")
            for label, terms in themes:
                if not any(term in lowered for term in terms):
                    continue
                row = rows_by_theme[label]
                row["count"] += 1
                row["sources"].add(source)
                if len(row["examples"]) < 2:
                    row["examples"].append(clean(item.get("headline") or item.get("title") or item.get("summary") or item.get("text"), 42))
    ranked = sorted(rows_by_theme.values(), key=lambda row: (-row["count"], row["keyword"]))
    return [row for row in ranked if row["count"]][:limit]


def selected_rows(ledger: list[dict]) -> list[dict]:
    return [row for row in ledger if row.get("selection_status") == "selected"]


def reserve_rows(ledger: list[dict]) -> list[dict]:
    return [row for row in ledger if row.get("selection_status") == "reserve"]


def material_title(row: dict, limit: int = 42) -> str:
    return clean(row.get("headline") or row.get("title") or row.get("summary") or row.get("id"), limit)


def radar_material_title(row: dict, limit: int = 46) -> str:
    return clean(row.get("title") or row.get("summary") or row.get("id"), limit)


def compact_radar_title(row: dict) -> str:
    text = clean(f"{row.get('title') or ''} {row.get('summary') or ''}")
    lowered = text.lower()
    if "uae" in lowered and "opec" in lowered:
        return "UAE의 OPEC 탈퇴"
    if "oil" in lowered and ("$100" in text or "$105" in text or "iran" in lowered or "hormuz" in lowered):
        return "유가 100달러와 이란 리스크"
    if "call option" in lowered or "risk appetite" in lowered:
        return "개인 투자자 콜옵션 매수 급증"
    if "discretionary positioning" in lowered:
        return "재량주 포지셔닝과 실적 성장"
    if "paul tudor jones" in lowered or "market cap to gdp" in lowered:
        return "폴 튜더 존스의 밸류에이션 경고"
    if "ai-related portfolios" in lowered or "fangmat" in lowered:
        return "AI 포트폴리오와 시장 수익률"
    if "s&p 500 is up" in lowered or "best monthly performance" in lowered:
        return "AI 주도 S&P500 월간 랠리"
    if "stock picker" in lowered and "norway" in lowered:
        return "노르웨이 국부펀드가 보는 AI 장세"
    if "oil prices" in lowered and "record highs" in lowered:
        return "유가 리스크를 덮는 AI 기대"
    if "seagate" in lowered:
        return "씨게이트와 AI 스토리지 수요"
    if "googl" in lowered and ("tpu" in lowered or "data center" in lowered or "capex" in lowered):
        return "구글 TPU 매출과 AI 인프라 수요"
    if "alphabet" in lowered and ("cloud" in lowered or "earnings" in lowered):
        return "구글 클라우드 실적"
    if "mercor" in lowered or "teaching ai" in lowered:
        return "AI가 사람의 일을 배우는 방식"
    if "mark cuban" in lowered:
        return "마크 큐반의 AI 생존법"
    if "iran-linked oil tankers" in lowered or "oil tankers" in lowered:
        return "이란 유조선 압류와 에너지 긴장"
    if "openai" in lowered and "amazon" in lowered:
        return "OpenAI와 Amazon 협력 확대"
    if "stocks slip" in lowered and "oil surges" in lowered:
        return "주식 약세와 유가 급등"
    if "fed" in lowered and ("dissent" in lowered or "powell" in lowered or "holds rates" in lowered or "rate decision" in lowered):
        return "연준 결정과 Powell 잔류"
    if "trump" in lowered and "iran" in lowered:
        return "트럼프의 이란 압박"
    if "amazon" in lowered and ("earnings" in lowered or "cloud" in lowered):
        return "아마존 실적과 클라우드 성장"
    if "microsoft" in lowered and "ai" in lowered:
        return "마이크로소프트 AI 매출 성장"
    if "meta" in lowered and "ai" in lowered:
        return "메타 AI 투자 부담"
    return clean(text, 34)


def material_quote(title: str, row: dict) -> str:
    lowered = f"{title} {row.get('title') or ''} {row.get('summary') or ''}".lower()
    if "유가 100달러" in title or ("oil" in lowered and ("iran" in lowered or "hormuz" in lowered)):
        return "유가가 다시 시장의 최상단 변수로 올라오며, AI 강세장이 지정학 리스크를 어디까지 견딜 수 있는지 보여주는 자료입니다."
    if "UAE의 OPEC 탈퇴" in title:
        return "UAE의 OPEC 탈퇴 이슈는 단순 유가 뉴스가 아니라, OPEC의 가격 통제력과 에너지 질서 변화를 함께 볼 수 있는 소재입니다."
    if "개인 투자자 콜옵션" in title:
        return "개인 투자자의 콜옵션 매수가 급증하면서, 시장의 위험선호가 강세장의 연료인지 과열 신호인지 점검할 수 있습니다."
    if "재량주 포지셔닝" in title:
        return "재량소비주 포지셔닝과 실적 기대가 함께 움직이는지 보며, 투자자들이 경기민감 영역까지 확신을 넓히고 있는지 확인할 수 있습니다."
    if "폴 튜더 존스" in title:
        return "폴 튜더 존스의 밸류에이션 경고는 현재 랠리가 얼마나 비싼 구간에서 진행되는지 환기하는 자료로 쓸 수 있습니다."
    if "AI 주도 S&P500" in title:
        return "S&P500의 월간 랠리가 AI 관련주 중심으로 만들어졌다는 점을 보여주며, 현재 시장의 주도 테마를 압축해 보여주는 자료입니다."
    if "OpenAI" in title:
        return "OpenAI와 빅테크 파트너십 변화는 AI 생태계의 힘의 이동과 클라우드 경쟁을 함께 볼 수 있는 소재입니다."
    if "AI 포트폴리오" in title:
        return "AI 관련 포트폴리오가 시장 대비 얼마나 앞서가고 있는지 보여주며, AI 기대가 아직 주가를 떠받치는지 점검할 수 있습니다."
    if "노르웨이 국부펀드" in title:
        return "대형 기관투자자의 시각을 통해 지금 장세가 개별 종목 장세인지, 거대한 테마 장세인지 생각해볼 수 있습니다."
    if "구글 TPU" in title:
        return "구글이 TPU 판매 매출을 언급하면서 AI 인프라 투자가 실제 매출과 가이던스로 연결되는지 확인할 수 있는 자료입니다."
    if "AI가 사람의 일을" in title:
        return "AI 스타트업이 고숙련 노동자의 업무를 학습시키는 흐름은 AI가 단순 도구를 넘어 노동시장과 기업 생산성을 바꾸는 소재입니다."
    if "마크 큐반" in title:
        return "마크 큐반의 발언은 기업들이 AI를 채택하지 않으면 경쟁에서 밀릴 수 있다는 분위기를 단신처럼 환기하기 좋습니다."
    if "이란 유조선" in title:
        return "이란 관련 유조선 압류는 유가 리스크가 단순 가격 이슈가 아니라 제재·해상 수송·지정학으로 확장되는 장면입니다."
    if "연준" in title:
        return "연준 결정 이후 시장이 금리보다 Powell 거취와 정책 독립성 논쟁을 어떻게 받아들이는지 확인할 수 있습니다."
    if "트럼프의 이란" in title:
        return "이란 관련 정치적 압박은 유가·해상 수송 리스크를 방송 초반에 환기하는 단신으로 쓰기 좋습니다."
    if "아마존" in title or "마이크로소프트" in title or "메타" in title:
        return "빅테크 실적은 AI 투자가 매출 성장으로 증명되는지, 혹은 비용 부담으로 읽히는지 갈라지는 지점입니다."
    return clean(row.get("radar_question") or row.get("summary"), 130)


def material_question(title: str, row: dict) -> str:
    if "유가" in title or "UAE" in title or "이란" in title:
        return "에너지·지정학 리스크가 시장의 위험선호를 어디까지 누르는가?"
    if "콜옵션" in title or "포지셔닝" in title or "밸류에이션" in title:
        return "지금의 강세는 과열인가, 아니면 강세장의 연료인가?"
    if "구글 TPU" in title or "AI가 사람의 일을" in title or "마크 큐반" in title or "OpenAI" in title:
        return "AI 기대가 실제 매출·생산성·기업 의사결정으로 확인되는가?"
    if "연준" in title:
        return "금리 결정 이후 시장은 정책 방향보다 Fed 독립성 리스크를 더 보려는가?"
    if "아마존" in title or "마이크로소프트" in title or "메타" in title:
        return "AI 투자가 실적 성장으로 보이는가, 비용 부담으로 보이는가?"
    return clean(row.get("radar_question") or material_quote(title, row), 120)


def radar_theme_text(row: dict) -> str:
    themes = row.get("themes") or []
    labels = [theme.get("label") for theme in themes if theme.get("label")]
    return ", ".join(labels) or "-"


def render_radar_card(lines: list[str], row: dict, index: int | None = None, next_title: str = "") -> None:
    title = compact_radar_title(row)
    heading = f"### {title}" if index is None else f"### {title}"
    lines.extend([heading, ""])
    lines.extend([f"> {material_quote(title, row)}", ""])
    label = source_label(row.get("source") or row.get("type"), row.get("url") or "")
    lines.append(f"출처: {link(label, row.get('url') or '')}")
    if row.get("published_at"):
        lines.append(f"작성 시점: {display_dt(row.get('published_at'))}")
    question = material_question(title, row)
    if question:
        lines.append(f"- 이 자료가 여는 질문: {question}")
    if next_title:
        lines.append(f"- 다음에 붙일 자료: `{next_title}`")
    if row.get("summary"):
        lines.append(f"- {clean(row.get('summary'), 150)}")
    if row.get("visual_local_path"):
        lines.extend(["", f"![{title}]({image_path(row['visual_local_path'])})"])
    lines.append("")


def render_support_card(lines: list[str], row: dict) -> None:
    title = compact_radar_title({"title": row.get("headline") or row.get("title") or "", "summary": row.get("summary") or ""})
    lines.extend([f"### {title}", ""])
    lines.extend([f"> {material_quote(title, {'summary': row.get('summary') or row.get('headline') or ''})}", ""])
    label = source_label(row.get("source_name") or row.get("source_id"), row.get("url") or "")
    lines.append(f"출처: {link(label, row.get('url') or '')}")
    if row.get("published_at"):
        lines.append(f"작성 시점: {display_dt(row.get('published_at'))}")
    lines.append(f"- {clean(row.get('summary') or row.get('headline'), 150)}")
    for image in row.get("image_refs") or []:
        if image.get("local_path"):
            lines.extend(["", f"![{title}]({image_path(image['local_path'])})"])
            break
    lines.append("")


def relevant_finviz_news(row: dict) -> dict:
    ticker = (row.get("ticker") or "").upper()
    keyword_map = {
        "GOOGL": ["alphabet", "google", "tpu", "cloud", "ai"],
        "MSFT": ["microsoft", "azure", "cloud", "ai"],
        "META": ["meta", "ai", "capex", "ad"],
        "AMZN": ["amazon", "aws", "cloud", "capex"],
        "PI": ["impinj", "pi"],
        "UBER": ["uber", "expedia", "hotel", "travel", "everything app"],
        "EXPE": ["expedia", "uber", "hotel", "travel"],
        "V": ["visa", "spending", "card", "stablecoin", "ai agent"],
    }
    keywords = keyword_map.get(ticker, [ticker.lower()])
    for news in row.get("news") or []:
        headline = (news.get("headline") or "").lower()
        if any(keyword in headline for keyword in keywords):
            return news
    return (row.get("news") or [{}])[0]


def relevant_finviz_summary(row: dict) -> str:
    ticker = (row.get("ticker") or "").upper()
    keywords = {
        "GOOGL": ["alphabet", "google", "tpu", "cloud", "ai"],
        "MSFT": ["microsoft", "cloud", "ai"],
        "META": ["meta", "ai", "capex"],
        "AMZN": ["amazon", "aws", "cloud", "capex"],
        "PI": ["impinj"],
        "UBER": ["uber", "expedia", "hotel"],
        "EXPE": ["expedia", "uber", "hotel"],
        "V": ["visa", "card", "spending"],
    }.get(ticker, [ticker.lower()])
    for summary in row.get("quote_summary") or []:
        lowered = summary.lower()
        if any(keyword in lowered for keyword in keywords):
            return summary
    news = relevant_finviz_news(row)
    return news.get("headline") or ""


def render_feature_stock(lines: list[str], row: dict) -> None:
    ticker = row.get("ticker") or "-"
    lines.extend([f"#### {ticker}", ""])
    summary = relevant_finviz_summary(row)
    news = relevant_finviz_news(row)
    if summary:
        lines.append(f"> {clean(summary, 150)}")
        lines.append("")
    lines.append(f"출처: {link('Finviz', row.get('url') or '')}")
    if news:
        lines.append(f"- 최근 뉴스: {clean(news.get('headline'), 120)}")
    if row.get("screenshot_path"):
        lines.extend(["", f"![{ticker} 일봉]({image_path(row['screenshot_path'])})"])
    lines.append("")


def render_material_card(lines: list[str], row: dict, index: int | None = None) -> None:
    title = material_title(row)
    heading = f"### {index}. {title}" if index else f"### {title}"
    lines.extend([heading, ""])
    if row.get("selection_reason") or row.get("storyline_fit"):
        lines.extend([f"> {clean(row.get('selection_reason') or row.get('storyline_fit'), 150)}", ""])
    label = source_label(row.get("source") or row.get("type"), row.get("url") or "")
    lines.append(f"출처: {link(label, row.get('url') or '')}")
    if row.get("published_at"):
        lines.append(f"작성 시점: {display_dt(row.get('published_at'))}")
    if row.get("summary"):
        lines.append(f"- {clean(row.get('summary'), 180)}")
    if row.get("visual_local_path"):
        lines.extend(["", f"![{title}]({image_path(row['visual_local_path'])})"])
    lines.append("")


def storyline_refs(storyline: dict, radar_by_id: dict, ledger: list[dict]) -> list[str]:
    refs = []
    seen = set()
    for item_id in storyline.get("selected_item_ids", []):
        match = radar_by_id.get(item_id) or next((row for row in ledger if row.get("id") == item_id), None)
        if not match:
            continue
        title = compact_radar_title(match) if item_id in radar_by_id else material_title(match)
        if title in seen:
            continue
        seen.add(title)
        refs.append(title)
    return refs


def render_storyline(lines: list[str], index: int, storyline: dict, radar_by_id: dict, ledger: list[dict]) -> None:
    refs = storyline_refs(storyline, radar_by_id, ledger)
    lines.extend(
        [
            f"## {index}. {clean(storyline.get('title'))}",
            "",
            f"> {clean(storyline.get('one_liner'), 150)}",
            "",
            "### 선정 이유",
            "",
            f"- {clean(storyline.get('why_selected'), 150)}",
        ]
    )
    if refs:
        lines.append(f"- 참고 자료: {' → '.join(f'`{ref}`' for ref in refs[:4])}")
    lines.extend(["", "### 슬라이드 구성", ""])
    if storyline.get("angle"):
        lines.append(f"- {clean(storyline.get('angle'), 150)}")
    elif refs:
        lines.append(f"- {refs[0]}를 시작점으로 오늘 시장이 보는 질문을 제시")
    if len(refs) >= 2:
        lines.append(f"- 이어서 `{refs[1]}` 자료로 시장 반응 또는 보조 근거 연결")
    if len(refs) >= 3:
        lines.append(f"- 마지막으로 `{refs[2]}` 자료를 통해 시각자료, 특징주, 후속 질문 정리")
    lines.extend(["", "### 방송 멘트 초안", ""])
    if index == 1:
        lines.append("- 오늘 시장은 유가와 지정학 이슈를 무시하는 것처럼 보이지만, 실제로는 AI 기대가 그 충격을 덮고 있는지 확인해야 합니다.")
        lines.append("- 첫 장은 리스크를 던지고, 다음 장에서 투자자들의 위험선호가 얼마나 강한지 보여주면 흐름이 자연스럽습니다.")
    elif index == 2:
        lines.append("- 두 번째 꼭지는 시장이 비싼 줄 알면서도 왜 계속 사는지 묻는 흐름으로 잡습니다.")
        lines.append("- 포지셔닝, 콜옵션, 밸류에이션 경고를 이어 붙이면 강세장의 연료와 과열 신호를 동시에 보여줄 수 있습니다.")
    else:
        lines.append("- AI 이야기는 이제 기대감이 아니라 매출, CapEx, 생산성으로 증명되는 단계인지가 핵심입니다.")
        lines.append("- 구글 TPU, AI 노동 자동화, 기업인의 AI 발언을 묶으면 ‘성장에 꽂힌 시장’이라는 꼭지로 독립 배치할 수 있습니다.")
    lines.append("")


def render_dashboard(target_date: str) -> str:
    title = display_date_title(target_date)
    processed = PROCESSED_DIR / target_date
    live_pack = load_json(processed / "live-experiment-pack.json")
    selection = load_json(processed / "storyline-selection-v4.json").get("selection", {})
    earnings_drilldown = load_json(processed / "earnings-ticker-drilldown.json")
    finviz_features = load_json(processed / "finviz-feature-stocks.json")
    batch_a = load_json(processed / "today-misc-batch-a-candidates.json")
    batch_b = load_json(processed / "today-misc-batch-b-candidates.json")
    side_dish = load_json(processed / "side-dish-candidates.json")
    market_radar = load_json(processed / "market-radar.json")
    economic = load_json(processed / "economic-calendar.json")
    ledger = live_pack.get("ledger", [])
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%y.%m.%d %H:%M")
    start_times = []
    end_times = []
    for filename in ["today-misc-batch-a-candidates.json", "today-misc-batch-b-candidates.json", "x-timeline-posts.json"]:
        payload = load_json(processed / filename)
        if payload.get("captured_at"):
            start_times.append(short_dt(payload.get("captured_at")))
            end_times.append(short_dt(payload.get("captured_at")))
    freeze_time = short_dt(live_pack.get("freeze_time"))
    if freeze_time != "-":
        end_times.append(freeze_time)
    window = run_window(target_date) or f"{min(start_times) if start_times else '-'}-{max(end_times) if end_times else '-'}"
    counts = Counter(row.get("selection_status") for row in ledger)
    selected = selected_rows(ledger)
    reserve = reserve_rows(ledger)
    storylines = selection.get("storylines", [])
    radar_storylines = market_radar.get("storylines") or []
    radar_candidates = market_radar.get("candidates") or []
    radar_by_id = {row.get("id"): row for row in radar_candidates}
    candidate_by_id = {
        row.get("id"): row
        for row in (batch_a.get("candidates") or []) + (batch_b.get("candidates") or [])
        if row.get("id")
    }
    display_storylines = (radar_storylines or storylines)[:3]
    today_axis = infer_today_axis(display_storylines, radar_candidates)

    lines = [
        f"# {title}",
        "",
        f"최종 수정 일시: `{now} (KST)`",
        "",
        f"뉴스/X 수집 구간: `{window} (KST)`",
        "",
        f"시장 데이터 기준: `{chart_rows()[0][2] if chart_rows() and chart_rows()[0][2] else '-'}`",
        "",
        "# 🗞️ 주요 뉴스 요약",
        "",
        f"- 오늘의 대립축: {today_axis}",
    ]
    summary_bullets = selection.get("dashboard_summary_bullets", [])
    if summary_bullets:
        for bullet in summary_bullets[:3]:
            lines.append(f"- {clean(bullet, 110)}")
    elif radar_storylines:
        for storyline in radar_storylines[1:3]:
            lines.append(f"- {clean(storyline.get('one_liner'), 110)}")
    lines.extend(["", "# 📚 추천 스토리라인", ""])
    for index, storyline in enumerate(display_storylines, start=1):
        render_storyline(lines, index, storyline, radar_by_id, ledger)

    lines.extend(["# 🤖 자료 수집", "", "## 1. 시장은 지금", ""])
    index_futures = screenshots_for(target_date, "finviz-index-futures-*.png")
    if index_futures:
        lines.extend(["### 주요 지수 흐름", "", "출처: [Finviz](https://finviz.com/) · 수집 시점: 자동 수집", ""])
        for idx, index_future in enumerate(index_futures, start=1):
            label = "주요 지수 흐름" if idx == 1 else f"주요 지수 흐름 {idx}"
            lines.extend([f"![{label}]({index_future})", ""])
    sp500_heatmap = screenshot_for(target_date, "finviz-sp500-heatmap*.png")
    if sp500_heatmap:
        lines.extend(["### S&P500 히트맵", "", "출처: [Finviz](https://finviz.com/map.ashx?t=sec) · 수집 시점: 자동 수집", "", f"![S&P500 히트맵]({sp500_heatmap})", ""])
    russell_heatmap = screenshot_for(target_date, "*russell*heatmap*.png", "*iwm*heatmap*.png")
    lines.extend(["### 러셀 2000 히트맵", ""])
    if russell_heatmap:
        lines.extend(["출처: [Finviz](https://finviz.com/map?t=sec_rut) · 수집 시점: 자동 수집", "", f"![러셀 2000 히트맵]({russell_heatmap})", ""])
    else:
        lines.append("- 수집 이미지 없음")
    for chart_id, chart_title, subtitle, source_name, source_url in chart_rows():
        png = EXPORTS_DIR / f"{chart_id}.png"
        if png.exists():
            lines.extend([f"### {chart_title}", ""])
            meta = f"출처: {link(source_name, source_url)}"
            if subtitle:
                meta += f" · {subtitle}"
            lines.extend([meta, "", f"![{chart_title}]({png})", ""])
        else:
            lines.append(f"- {chart_title} / 출처: {link(source_name, source_url)}")
    fear_greed = screenshot_for(target_date, "*fear*greed*.png", "*fear-greed*.png")
    if fear_greed:
        lines.extend(["", "### 공포탐욕지수", ""])
        lines.extend(["출처: [CNN](https://edition.cnn.com/markets/fear-and-greed) · 수집 시점: 자동 수집", "", f"![공포탐욕지수]({fear_greed})"])
    else:
        lines.extend(["", "### 공포탐욕지수", "", "- 이번 자동 실행에서는 이미지 수집 제외. 필요 시 CNN 캡처 루트 복구.", ""])

    lines.extend(["", "### 오늘의 경제 일정", ""])
    us_calendar_png = EXPORTS_DIR / "economic-calendar-us.png"
    global_calendar_png = EXPORTS_DIR / "economic-calendar-global.png"
    calendar_png = EXPORTS_DIR / "economic-calendar.png"
    if us_calendar_png.exists() or global_calendar_png.exists():
        lines.extend(["출처: [Trading Economics](https://ko.tradingeconomics.com/calendar) · Datawrapper 표", ""])
        if us_calendar_png.exists():
            lines.extend([f"![오늘의 미국 경제 일정]({us_calendar_png})", ""])
        if global_calendar_png.exists():
            lines.extend([f"![오늘의 글로벌 경제 일정]({global_calendar_png})", ""])
    elif calendar_png.exists():
        lines.extend(["출처: [Trading Economics](https://ko.tradingeconomics.com/calendar) · Datawrapper 표", "", f"![오늘의 경제 일정]({calendar_png})", ""])
    else:
        events = economic.get("events", [])[:8]
        if events:
            lines.append("| 시간 | 국가 | 이벤트 | 예상 | 이전 |")
            lines.append("|---|---|---|---:|---:|")
            for event in events:
                lines.append(
                    f"| {short_dt(event.get('local_datetime'))} | {event.get('country')} | {clean(event.get('event'), 32)} | {event.get('forecast') or event.get('consensus') or '-'} | {event.get('previous') or '-'} |"
                )
        else:
            lines.append("- 경제일정 후보 없음")

    fed_rows = []
    fed_seen = set()
    for row in radar_candidates:
        if not is_fed_material(row):
            continue
        title = compact_radar_title(row)
        if title in fed_seen:
            continue
        fed_seen.add(title)
        fed_rows.append(row)
        if len(fed_rows) >= 3:
            break
    fed_screens = screenshots_for(target_date, "*fedwatch*.png", "*cme-fedwatch*.png", "*polymarket*.png")
    show_fed_package = bool(fed_rows)
    misc_section_number = 3 if show_fed_package else 2
    feature_section_number = misc_section_number + 1
    if show_fed_package:
        lines.extend(["", "## 2. Fed/FOMC package", ""])
        lines.append("> 경제 일정 표와 별도로, 시장이 금리 경로를 어떻게 확률로 가격에 넣는지 보는 블록입니다.")
        lines.append("")
        if fed_screens:
            for screen in fed_screens[:3]:
                label = "FedWatch/Polymarket 확률 자료"
                lines.extend([f"![{label}]({screen})", ""])
        else:
            lines.append("- FedWatch/Polymarket 캡처는 이번 실행에서 확보되지 않았습니다. 금리인하 베팅이 메인 이슈면 수동 확인 필요.")
            lines.append("")
        for index, row in enumerate(fed_rows, start=1):
            next_title = compact_radar_title(fed_rows[index]) if index < len(fed_rows) else ""
            render_radar_card(lines, row, index, next_title)

    lines.extend(["", f"## {misc_section_number}. 오늘의 이모저모", ""])
    radar_misc_rows = []
    seen_radar_ids = set()
    seen_radar_titles = set()
    for storyline in radar_storylines:
        for item_id in storyline.get("selected_item_ids", []):
            row = radar_by_id.get(item_id)
            if row and not row.get("visual_local_path") and candidate_by_id.get(item_id):
                images = candidate_by_id[item_id].get("image_refs") or []
                local = next((image.get("local_path") for image in images if image.get("local_path")), "")
                if local:
                    row = {**row, "visual_local_path": local}
            if show_fed_package and row and is_fed_material(row):
                continue
            title_key = compact_radar_title(row) if row else ""
            if row and item_id not in seen_radar_ids and title_key not in seen_radar_titles:
                radar_misc_rows.append(row)
                seen_radar_ids.add(item_id)
                seen_radar_titles.add(title_key)
    if radar_misc_rows:
        visible_rows = radar_misc_rows[:6]
        for index, row in enumerate(visible_rows, start=1):
            next_title = compact_radar_title(visible_rows[index]) if index < len(visible_rows) else ""
            render_radar_card(lines, row, index, next_title)
    misc_rows = [] if radar_misc_rows else selected[:4]
    side_dish_rows = side_dish.get("candidates", [])
    for index, row in enumerate(misc_rows, start=1):
        render_material_card(lines, row, index)
    if side_dish_rows:
        lines.extend(["### 단신/환기 소재", ""])
        added = 0
        for row in side_dish_rows:
            title = compact_radar_title({"title": row.get("headline") or ""})
            if title in seen_radar_titles:
                continue
            lines.append(f"- `{clean(row.get('headline'), 54)}` / {link(source_label(row.get('source') or row.get('type'), row.get('url') or ''), row.get('url') or '')}")
            added += 1
            if added >= 2:
                break
        lines.append("")

    def support_rank(row: dict) -> int:
        text = f"{row.get('headline') or ''} {row.get('summary') or ''}".lower()
        if "gold" in text or re.search(r"\bapr\s+(1\d|2[0-7])\b", text):
            return 0
        if "uae" in text and "opec" in text:
            return 100
        if "iran" in text or "hormuz" in text:
            return 90
        if "fed" in text and ("dissent" in text or "powell" in text or "rate" in text):
            return 70
        if "microsoft" in text or "amazon" in text or "meta" in text or "alphabet" in text:
            return 65
        if "ai data center" in text or "ai spending" in text:
            return 60
        return 0

    ranked_support = []
    for row in batch_a.get("candidates") or []:
        title_key = compact_radar_title({"title": row.get("headline") or "", "summary": row.get("summary") or ""})
        rank = support_rank(row)
        if not rank:
            continue
        ranked_support.append((rank, title_key, row))
    support_rows = []
    seen_support_titles = set()
    for _, title_key, row in sorted(ranked_support, key=lambda item: (-item[0], item[1])):
        if title_key in seen_support_titles:
            continue
        seen_support_titles.add(title_key)
        support_rows.append(row)
        if len(support_rows) >= 6:
            break
    if support_rows:
        lines.extend(["### 보강 후보", ""])
        for row in support_rows[:3]:
            title = compact_radar_title({"title": row.get("headline") or "", "summary": row.get("summary") or ""})
            label = source_label(row.get("source_name") or row.get("source_id"), row.get("url") or "")
            lines.append(f"- `{title}` / {link(label, row.get('url') or '')}")
        lines.append("- 전체 보강 후보와 원문 장부는 내부 JSON에 보존.")
        if any("oil" in row_blob(row) or "opec" in row_blob(row) or "iran" in row_blob(row) for row in support_rows):
            lines.extend(
                [
                    "",
                    "### 에너지 리스크 체크리스트",
                    "",
                    "- OPEC/UAE: 생산량, 점유율, 쿼터(quota), spare capacity를 추가 확인.",
                    "- 호르무즈/수송: Strait of Hormuz 봉쇄·shipping 병목 가능성을 유가 반응과 함께 확인.",
                    "- 에너지주 차트: XLE, OIH, 셰브론(CVX), 엑슨(XOM), SLB/HAL 같은 에너지주가 실제로 반응하는지 확인.",
                    "- EIA 이벤트: 주간 원유재고·휘발유재고 발표가 유가 변동을 증폭시키는지 확인.",
                ]
            )
        lines.append("")

    keyword_rows = core_keyword_rows(batch_a, batch_b, side_dish, load_json(processed / "x-timeline-posts.json"))
    if keyword_rows:
        lines.extend(["### 오늘의 핵심 키워드", ""])
        lines.append("| 키워드 | 감지량 | 주로 나온 곳 | 예시 소재 |")
        lines.append("|---|---:|---|---|")
        for row in keyword_rows:
            sources = ", ".join(sorted(row["sources"])[:4]) or "-"
            examples = " / ".join(example for example in row["examples"] if example) or "-"
            lines.append(f"| **{row['keyword']}** | {row['count']} | {sources} | {examples} |")
        lines.append("")

    lines.extend([f"## {feature_section_number}. 실적/특징주", ""])
    earnings_image = screenshot_for(target_date, "*earnings-calendar*.jpg", "*earnings-calendar*.png")
    if earnings_image:
        lines.extend(["### 이번 주 실적 캘린더", "", "출처: [Earnings Whispers](https://x.com/eWhispers) · 수집 시점: 자동 수집", "", f"![이번 주 실적 캘린더]({earnings_image})", ""])
    drilldown_rows = [row for row in earnings_drilldown.get("tickers", []) if row.get("status") == "drilldown"]
    if drilldown_rows:
        lines.extend(["### 실적 캘린더 기반 후보", ""])
        for row in drilldown_rows[:8]:
            tags = ", ".join(row.get("tags") or []) or "-"
            lines.append(f"- `{row.get('ticker')}`: {clean(row.get('broadcast_question') or row.get('reason'), 110)}")
            if row.get("broadcast_question"):
                continue
            if row.get("matched_materials"):
                material = row["matched_materials"][0]
                lines.append(f"  - 연결 후보: {link(source_label(material.get('source') or material.get('type'), material.get('url') or ''), material.get('url') or '')}: {clean(material.get('title'), 80)}")
            if row.get("finviz_news"):
                news = row["finviz_news"][0]
                lines.append(f"  - {link(clean(news.get('headline'), 80), news.get('url') or '')}")
        lines.append("")
    elif not earnings_image:
        lines.extend(
            [
                "### 이번 주 실적 캘린더",
                "",
                "- 이번 자동 실행에서는 Earnings Whispers 캘린더 이미지를 확보하지 못했습니다. 05.01 실행 전 X 캘린더 캡처 루트를 재점검합니다.",
                "",
                "### 테마 증명 후보",
                "",
                "- `GOOGL`: TPU 매출 인식과 2027년 데이터센터 CapEx 증가 가능성. AI 인프라 수요가 실적으로 연결되는지 보는 후보.",
                "- `PI`: 매출·EPS 상회와 Q2 가이던스 상향. AI/반도체 주변부의 실적 모멘텀 후보.",
                "- `UBER`/`EXPE`: 호텔 예약 제휴와 OpenAI 기반 음성 예약. AI가 소비 플랫폼 UX로 내려오는지 보는 후보.",
                "- `V`: 결제/소비 경기의 방어력 확인 후보.",
            ]
        )
    feature_rows = [row for row in finviz_features.get("items", []) if row.get("status") == "ok"]
    if feature_rows:
        lines.extend(["", "### Finviz 일봉/핫뉴스", ""])
        for row in feature_rows[:5]:
            render_feature_stock(lines, row)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or (RUNTIME_NOTION_DIR / args.date / f"{display_date_title(args.date)}.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_dashboard(args.date), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
