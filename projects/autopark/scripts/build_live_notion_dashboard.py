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

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
CHART_DIR = PROJECT_ROOT / "charts"
LOG_DIR = PROJECT_ROOT / "runtime" / "logs"
EXPORTS_DIR = PROJECT_ROOT / "exports" / "current"
FEDWATCH_HEATMAP_DIR = PROJECT_ROOT / "runtime" / "assets"


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


def clean_complete(value: str | None, limit: int | None = None) -> str:
    text = clean(value)
    if not limit or len(text) <= limit:
        return text.rstrip("…").rstrip()
    clipped = text[:limit].rstrip()
    sentence_end = max(clipped.rfind(mark) for mark in [".", "?", "!", "다.", "요.", "함.", "음."])
    if sentence_end >= max(40, limit // 2):
        return clipped[: sentence_end + 1].rstrip()
    return clipped.rstrip("…").rstrip()


def compact_status(value: str | None, default: str = "medium") -> str:
    text = clean(value or default)
    for marker in ["—", "-", ":", "·"]:
        if marker in text:
            head = clean(text.split(marker, 1)[0])
            if head:
                return head
    return clean(text, 32)


PUBLIC_LABELS = {
    "supported_by_mixed_evidence": "근거는 있으나 수치 확인 필요",
    "check_market_pricing": "시장 가격 반영 여부 확인 필요",
    "prepricing check": "시장 가격 반영 여부 확인 필요",
    "check_if_relevant": "필요 시 확인",
    "visual_only_not_causality": "차트는 반응 확인용",
    "sentiment_only_not_fact": "소셜 반응은 분위기 참고용",
    "fact_anchor": "사실 확인 근거",
    "analysis_anchor": "해석 참고",
    "data_anchor": "숫자 근거",
    "market_reaction": "시장 반응",
    "sentiment_probe": "분위기 참고",
    "sentiment": "분위기",
    "support_only": "보조 자료",
}


INTERNAL_LABELS = set(PUBLIC_LABELS) | {
    "source_role",
    "evidence_role",
    "drop_code",
    "item_id",
    "evidence_id",
    "visual_asset_role",
    "use_as_slide",
    "use_as_talk_only",
}


MARKET_CHART_HINTS = {
    "us10y": ["10Y", "10년물", "treasury", "국채"],
    "crude-oil-wti": ["WTI", "crude", "원유"],
    "crude-oil-brent": ["Brent", "브렌트"],
    "dollar-index": ["DXY", "dollar", "달러"],
    "usd-krw": ["USD/KRW", "원달러", "달러"],
    "bitcoin": ["Bitcoin", "비트코인"],
}


def public_label(value: str | None, limit: int | None = None) -> str:
    text = clean(value)
    if not text:
        return ""
    lowered = text.lower()
    if lowered in PUBLIC_LABELS:
        return clean(PUBLIC_LABELS[lowered], limit)
    for raw, human in PUBLIC_LABELS.items():
        text = re.sub(re.escape(raw), human, text, flags=re.I)
    return clean(text, limit)


def public_editorial_text(value: str | None, limit: int | None = None) -> str:
    text = clean(value)
    text = re.sub(r"\bUnknown Error\b", "수집 상태 확인 필요", text, flags=re.I)
    text = re.sub(r"^자동 보강:\s*", "", text)
    text = text.replace(
        "sentiment 단독 스토리라인이 되지 않도록 같은 테마의 fact/data/analysis 후보를 추가했습니다.",
        "소셜 근거만 남지 않도록 같은 주제의 기사·분석 후보를 함께 붙였습니다.",
    )
    text = re.sub(r"\s*/\s*auto_added_fact_data_analysis_support\b", "", text)
    text = text.replace("auto_added_fact_data_analysis_support", "")
    text = re.sub(r"^retrospective_learning:\s*", "", text)
    text = text.replace("causal anchor", "핵심 근거")
    return public_label(text, limit)


def first_sentences(value: str | None, max_sentences: int = 2, limit: int = 180) -> str:
    text = public_editorial_text(value, limit * 2)
    if not text:
        return ""
    parts = [part.strip() for part in re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+", text) if part.strip()]
    if not parts:
        return clean_complete(text, limit)
    return clean_complete(" ".join(parts[:max_sentences]), limit)


def generated_market_asset_blob() -> str:
    hints = []
    for chart_id, tokens in MARKET_CHART_HINTS.items():
        if (EXPORTS_DIR / f"{chart_id}.png").exists():
            hints.extend(tokens)
    return " ".join(hints)


def chart_title(chart_id: str) -> str:
    return clean(load_json(CHART_DIR / f"{chart_id}-datawrapper.json").get("title"), 120)


def chart_delta_is_negative(chart_id: str) -> bool:
    title = chart_title(chart_id)
    return bool(re.search(r"\((?:-|−)", title))


def oil_price_reaction_weak() -> bool:
    titles = [chart_title("crude-oil-wti"), chart_title("crude-oil-brent")]
    if not any(titles):
        return False
    return any(chart_delta_is_negative(chart_id) for chart_id in ["crude-oil-wti", "crude-oil-brent"])


def openai_number_supported(storyline: dict) -> bool:
    evidence_blob = storyline_asset_blob(storyline)
    if "openai" not in evidence_blob.lower():
        return False
    chunks = re.split(r"[.;\n]|(?<=다\.)\s+", evidence_blob)
    return any(
        "openai" in chunk.lower()
        and re.search(r"\d|contract|revenue|sales|capex|매출|계약|수주|투자", chunk, flags=re.I)
        for chunk in chunks
    )


def story_display_title(storyline: dict) -> str:
    raw = clean(storyline.get("display_title") or storyline.get("title"), 90)
    lowered = raw.lower()
    blob = storyline_blob(storyline)
    if "openai" in lowered and not openai_number_supported(storyline):
        return "AI 인프라 수요는 아직 살아 있다"
    if ("유가" in raw or "oil" in lowered or "brent" in lowered or "wti" in lowered) and oil_price_reaction_weak():
        if re.search(r"프리미엄|급등|되살아난|rally|surge|spike", raw, flags=re.I):
            return "유가 리스크는 있지만 가격 반응은 약하다"
    if raw.endswith("인가") or raw.endswith("인가?"):
        if "금리" in raw and "달러" in raw:
            return "실적은 좋은데, 금리·달러가 발목을 잡는다"
        if "AI" in raw or "ai" in lowered:
            return "AI 인프라 수요는 아직 살아 있다"
        if "유가" in raw:
            return "유가 리스크는 가격 반응과 함께 봐야 한다"
    if "금리" in blob and "달러" in blob and "숨은 제약" in raw:
        return "실적은 좋은데, 금리·달러가 발목을 잡는다"
    return raw


def story_logic_flags(storyline: dict) -> list[str]:
    flags = []
    raw = clean(storyline.get("title"), 120)
    if "openai" in raw.lower() and not openai_number_supported(storyline):
        flags.append("AI 제목에 OpenAI 숫자를 쓰기에는 OpenAI 전용 숫자/계약 근거가 부족함")
    if ("유가" in raw or "oil" in raw.lower() or "brent" in raw.lower() or "wti" in raw.lower()) and oil_price_reaction_weak():
        if re.search(r"프리미엄|급등|되살아난|rally|surge|spike", raw, flags=re.I):
            flags.append("headline_risk_but_price_reaction_weak")
    return flags


def signal_label(value: str | None) -> str:
    text = clean(value or "watch").lower()
    if text.startswith("signal"):
        return "신호"
    if text.startswith("noise"):
        return "소음"
    if text.startswith("watch"):
        return "점검"
    return clean(value or "점검", 24)


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


def notion_image(alt: str, path: str | Path) -> str:
    return f"![{public_editorial_text(alt, 80)}]({image_path(str(path))})"


def chart_heading(title: str) -> str:
    return title.split(":", 1)[0].strip() or title


def code_meta(value: str) -> str:
    return f"`{value}`" if value and not value.startswith("`") else value


def capture_meta(target_date: str, source_id: str) -> str:
    payload = load_json(PROJECT_ROOT / "data" / "raw" / target_date / f"{source_id}.json")
    captured = display_dt(payload.get("captured_at")) if payload.get("captured_at") else ""
    return f"수집 시점: `{captured}`" if captured and captured != "-" else "수집 시점: `-`"


def captured_from_file(path: str | Path) -> str:
    try:
        mtime = Path(path).stat().st_mtime
    except OSError:
        return ""
    return datetime.fromtimestamp(mtime, ZoneInfo("Asia/Seoul")).strftime("%y.%m.%d %H:%M")


def screenshot_source_line(target_date: str, source_id: str, source_md: str) -> str:
    return f"출처: {source_md} · {capture_meta(target_date, source_id)}"


def fedwatch_probability_rows(target_date: str) -> list[list[str]]:
    payload = load_json(PROJECT_ROOT / "data" / "raw" / target_date / "cme-fedwatch.json")
    fedwatch = ((payload.get("extracted") or {}).get("fedwatch") or {})
    table = fedwatch.get("selected_table") or {}
    rows = table.get("rows") or fedwatch.get("fallback_rows") or []
    parsed = []
    for row in rows:
        cells = row if isinstance(row, list) else [str(row)]
        if len(cells) == 1:
            cells = re.split(r"\s+", cells[0].strip())
        cells = [clean(cell) for cell in cells if clean(cell)]
        if not cells:
            continue
        parsed.append(cells)
    header_index = next((index for index, row in enumerate(parsed) if "meeting date" in " ".join(row).lower()), None)
    if header_index is not None:
        header = parsed[header_index]
        data_rows = []
        for row in parsed[header_index + 1 :]:
            if len(row) < 3:
                continue
            if not re.match(r"\d{4}-\d{2}-\d{2}", row[0]):
                continue
            data_rows.append(row[: len(header)])
        return data_rows[:16]
    data_rows = [row for row in parsed if any("%" in cell for cell in row)]
    normalized = []
    for row in data_rows:
        joined = " ".join(row)
        target_match = re.search(r"\b\d{3,4}-\d{3,4}\b", joined)
        if not target_match:
            continue
        values = re.findall(r"\(Current\)|\d+(?:\.\d+)?%", joined)
        if not values:
            continue
        normalized.append([target_match.group(0), *values[:4]])
    return normalized[:8]


def fedwatch_probability_headers(target_date: str, row_width: int) -> list[str]:
    payload = load_json(PROJECT_ROOT / "data" / "raw" / target_date / "cme-fedwatch.json")
    fedwatch = ((payload.get("extracted") or {}).get("fedwatch") or {})
    table = fedwatch.get("selected_table") or {}
    raw_rows = table.get("rows") or fedwatch.get("fallback_rows") or []
    parsed_rows = []
    for row in raw_rows:
        cells = row if isinstance(row, list) else [str(row)]
        if len(cells) == 1:
            cells = re.split(r"\s+", cells[0].strip())
        cells = [clean(cell) for cell in cells if clean(cell)]
        if cells:
            parsed_rows.append(cells)
    for row in parsed_rows:
        if "meeting date" in " ".join(row).lower():
            headers = ["회의일" if cell.lower() == "meeting date" else cell for cell in row]
            return headers[:row_width]
    raw_text = " ".join(" ".join(row) if isinstance(row, list) else str(row) for row in raw_rows)
    date_labels = []
    for month, day, year in re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[ .-]+(\d{1,2})[,. -]+(20\d{2})\b", raw_text, re.I):
        date_labels.append(f"{month.title()} {int(day)}, {year}")
    wanted = max(0, row_width - 1)
    if date_labels:
        return ["목표금리"] + date_labels[:wanted]
    return ["목표금리"] + [f"차후 결정 {index}" for index in range(1, wanted + 1)]


def percent_value(value: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", clean(value))
    return float(match.group(0)) if match else 0.0


def trim_fedwatch_matrix(headers: list[str], rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    if not rows or len(headers) <= 2:
        return headers, rows
    max_by_col = []
    for index in range(1, len(headers)):
        values = [percent_value(row[index]) for row in rows if index < len(row)]
        max_by_col.append(max(values or [0.0]))
    keep = [0]
    active = [index + 1 for index, value in enumerate(max_by_col) if value >= 0.5]
    if active:
        lo = max(1, min(active))
        hi = min(len(headers) - 1, max(active) + 1)
        keep.extend(range(lo, hi + 1))
    else:
        keep.extend(range(1, min(len(headers), 9)))
    trimmed_headers = [headers[index] for index in keep]
    trimmed_rows = [[row[index] if index < len(row) else "" for index in keep] for row in rows]
    return trimmed_headers, trimmed_rows


def heat_color(value: float) -> tuple[int, int, int]:
    value = max(0.0, min(100.0, value)) / 100.0
    if value <= 0:
        return (248, 250, 252)
    # Light blue to yellow-green, close to CME's quick visual emphasis.
    low = (224, 244, 250)
    mid = (102, 204, 213)
    high = (255, 235, 132)
    if value < 0.55:
        t = value / 0.55
        return tuple(round(low[i] + (mid[i] - low[i]) * t) for i in range(3))
    t = (value - 0.55) / 0.45
    return tuple(round(mid[i] + (high[i] - mid[i]) * t) for i in range(3))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fill: tuple[int, int, int], text_font) -> None:
    bbox = draw.textbbox((0, 0), text, font=text_font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = box[0] + (box[2] - box[0] - width) / 2
    y = box[1] + (box[3] - box[1] - height) / 2 - 1
    draw.text((x, y), text, fill=fill, font=text_font)


def render_fedwatch_heatmap(target_date: str, headers: list[str], rows: list[list[str]]) -> str:
    if not rows or len(headers) <= 2:
        return ""
    out_dir = FEDWATCH_HEATMAP_DIR / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fedwatch-conditional-probabilities.png"
    cell_w = 74
    date_w = 104
    header_h = 38
    row_h = 30
    pad_x = 18
    title_h = 48
    note_h = 24
    width = pad_x * 2 + date_w + cell_w * (len(headers) - 1)
    height = title_h + header_h + row_h * len(rows) + note_h + 16
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = font(18, bold=True)
    header_font = font(12, bold=True)
    cell_font = font(12)
    small_font = font(11)
    draw.text((pad_x, 14), "CME FedWatch - Conditional Meeting Probabilities", fill=(15, 23, 42), font=title_font)
    x0 = pad_x
    y0 = title_h
    draw.rectangle((x0, y0, width - pad_x, y0 + header_h), fill=(241, 245, 249), outline=(203, 213, 225))
    draw_center(draw, (x0, y0, x0 + date_w, y0 + header_h), headers[0], (15, 23, 42), header_font)
    for idx, header in enumerate(headers[1:], start=0):
        left = x0 + date_w + idx * cell_w
        draw.rectangle((left, y0, left + cell_w, y0 + header_h), outline=(203, 213, 225))
        draw_center(draw, (left, y0, left + cell_w, y0 + header_h), header, (15, 23, 42), header_font)
    for r_idx, row in enumerate(rows):
        top = y0 + header_h + r_idx * row_h
        fill = (248, 250, 252) if r_idx % 2 else (255, 255, 255)
        draw.rectangle((x0, top, x0 + date_w, top + row_h), fill=fill, outline=(226, 232, 240))
        draw_center(draw, (x0, top, x0 + date_w, top + row_h), row[0], (15, 23, 42), cell_font)
        for c_idx, value in enumerate(row[1:], start=0):
            left = x0 + date_w + c_idx * cell_w
            val = percent_value(value)
            draw.rectangle((left, top, left + cell_w, top + row_h), fill=heat_color(val), outline=(226, 232, 240))
            draw_center(draw, (left, top, left + cell_w, top + row_h), value, (15, 23, 42), cell_font)
    draw.text((pad_x, height - note_h), "Color intensity highlights where the market-implied probability is concentrated.", fill=(71, 85, 105), font=small_font)
    img.save(out_path)
    return str(out_path)


def summarize_material_text(row: dict, limit: int = 220) -> str:
    text = clean(row.get("summary") or row.get("text") or row.get("headline") or row.get("title"), limit)
    if not text:
        return ""
    blob = f"{row.get('title') or ''} {row.get('summary') or ''}".lower()
    if "south korea" in blob and "exports" in blob and "semiconductor" in blob:
        return "한국 수출이 반도체 수요에 힘입어 강하게 유지됐다는 자료입니다. 유가 리스크와 함께 보면 지정학 부담 속에서도 AI·반도체 수요가 경기 해석을 지탱하는지 볼 수 있습니다."
    if "us stocks advanced" in blob and "oil supply shock" in blob:
        return "유가 충격에도 미국 증시가 실적 호조를 근거로 버틴 장면입니다. 지정학 리스크보다 실적과 AI 기대가 우선 가격에 반영되는지 확인할 수 있습니다."
    if "australia and japan markets" in blob and "iran" in blob:
        return "아시아 증시가 이란발 유가 부담을 일단 넘겨보려는 분위기를 보여주는 자료입니다. 글로벌 위험선호가 아직 꺾이지 않았는지 확인할 수 있습니다."
    if "standard intelligence" in blob and ("$75m" in blob or "computer use ai" in blob):
        return "컴퓨터 사용 AI 스타트업의 대형 투자 유치입니다. 시장 포지셔닝보다는 AI 응용 분야의 투자 열기를 보여주는 단신에 가깝습니다."
    if "s&p is considering rule changes" in blob and "index" in blob:
        return "S&P와 Nasdaq이 신규 상장사의 지수 편입 속도를 높일 수 있다는 내용입니다. 대형 IPO가 나오면 지수 수요가 더 빨리 붙을 수 있다는 시장 구조 소재입니다."
    if "ai is reshaping the american workplace" in blob:
        return "고소득 근로자일수록 업무에서 AI 도구를 더 많이 쓰고 있다는 자료입니다. AI 기대가 생산성 논리로 확장되는지 볼 수 있습니다."
    if "real capex" in blob and "ai" in blob:
        return "실질 설비투자가 AI 투자에 힘입어 강하게 늘었다는 자료입니다. AI 테마가 주가 기대를 넘어 실제 투자 사이클로 이어지는지 확인하는 근거입니다."
    if "huawei" in blob and "ai chip" in blob and ("60%" in blob or "surge" in blob):
        return "화웨이 AI 칩 매출이 크게 늘 것으로 예상된다는 자료입니다. 중국 AI 반도체 수요와 Nvidia 공백을 함께 볼 수 있습니다."
    if "breaking: apple stock" in blob or ("apple stock" in blob and "earnings" in blob):
        return "애플 실적 발표 직후 주가가 상승했다는 반응 자료입니다. 실적이 유가 부담을 일부 상쇄했다는 흐름을 설명할 때 보조로 쓸 수 있습니다."
    if "godaddy" in blob and "ai" in blob and "revenue" in blob:
        return "GoDaddy가 AI 기능 확대를 배경으로 예상보다 높은 매출 전망을 제시했다는 자료입니다. AI 수요가 소프트웨어 실적으로 번지는지 확인할 수 있습니다."
    if "white house ai memo" in blob or ("bloomberg:" in blob and "ai memo" in blob):
        return "백악관 AI 메모가 정부·국방 영역의 AI 조달 원칙을 바꾸려는 흐름을 보여주는 자료입니다. AI 인프라와 정책 수요가 기업 실적으로 이어질 수 있는지 볼 때 참고할 만합니다."
    if "tech stocks today" in blob or ("big tech earnings" in blob and "ai spending" in blob):
        return "빅테크 실적 이후 시장이 매출 성장보다 AI 투자 부담과 회수 속도를 더 따져보고 있다는 자료입니다."
    if "stocks mixed" in blob and ("strong earnings" in blob or "ai hopes" in blob):
        return "실적 호조가 지수 전체를 한 방향으로 끌기보다 AI 기대와 비용 부담을 동시에 가격에 반영하는 장면입니다."
    if "retail investors are piling" in blob and "semiconductor" in blob:
        return "개인 투자자가 3배 레버리지 반도체 ETF에 몰리면서, AI 반도체 기대가 위험선호와 과열 신호를 동시에 만들고 있다는 내용입니다."
    if "both wholesale" in blob and "retail" in blob and "inventor" in blob:
        return "도매와 소매 재고가 함께 늘었다는 자료입니다. 수요 둔화인지, 재고 재축적인지 소비 경기 해석에 붙일 수 있습니다."
    if "point72 founder steve cohen" in blob:
        return "스티브 코언이 Point72 전략과 운영 방향을 함께 볼 집행위원회를 만들었다는 내용입니다. 시장 소재보다는 금융가 단신에 가깝습니다."
    if "google q1 revenues" in blob or "cloud revenue grew" in blob:
        return "구글 매출, 순이익, 클라우드 매출이 큰 폭으로 늘었다는 자료입니다. AI 인프라 투자가 실제 실적으로 이어지는지 볼 때 쓸 수 있습니다."
    if "compute constrain" in blob:
        return "구글 클라우드가 수요를 모두 감당할 컴퓨팅 여력이 부족하다고 언급한 자료입니다. AI 인프라 공급 부족과 데이터센터 투자 논리로 연결됩니다."
    lowered = text.lower()
    if any(token in lowered for token in [" oil", "brent", "wti", "iran", "hormuz", "opec"]):
        return f"유가와 지정학 리스크 관련 내용입니다. {text}"
    if any(token in lowered for token in [" fed", "inflation", "pce", "rate", "powell"]):
        return f"연준과 인플레이션 경로를 보는 자료입니다. {text}"
    if any(token in lowered for token in [" ai", "google", "alphabet", "tpu", "cloud", "capex", "semiconductor"]):
        return f"AI 투자와 빅테크 실적을 연결해 볼 자료입니다. {text}"
    if any(token in lowered for token in ["call option", "retail", "positioning", "valuation"]):
        return f"위험선호와 포지셔닝 과열을 점검할 자료입니다. {text}"
    return text


def is_raw_english_title(value: str) -> bool:
    text = clean(value)
    if not text:
        return False
    ascii_letters = sum(1 for char in text if "A" <= char <= "Z" or "a" <= char <= "z")
    korean = sum(1 for char in text if "\uac00" <= char <= "\ud7a3")
    return ascii_letters >= 12 and ascii_letters > korean * 2


def filtered_storylines(storylines: list[dict], radar_by_id: dict) -> list[dict]:
    filtered = []
    used_ids = set()
    for storyline in storylines:
        rows = [radar_by_id.get(item_id) for item_id in storyline.get("selected_item_ids", [])]
        rows = [row for row in rows if row]
        if "강세장의 연료" in clean(storyline.get("title")) and len(rows) < 2:
            continue
        filtered.append(storyline)
        used_ids.update(storyline.get("selected_item_ids", []))
    if len(filtered) < 5:
        earnings_rows = [
            row
            for row in sorted(radar_by_id.values(), key=lambda item: item.get("score", 0), reverse=True)
            if row.get("id") not in used_ids
            and "earnings_signal" in set(row.get("theme_keys") or [])
            and ("ai_infra" in set(row.get("theme_keys") or []) or "market_positioning" in set(row.get("theme_keys") or []))
        ]
        if earnings_rows:
            selected = earnings_rows[:3]
            filtered.append(
                {
                    "title": "실적은 AI 기대를 증명하는가",
                    "one_liner": "빅테크 실적과 AI 투자 자료를 묶어 시장이 기대를 숫자로 확인하고 있는지 보는 축입니다.",
                    "why_selected": "0501 수집 자료에는 구글, 클라우드, AI 투자와 실적 반응을 연결하는 후보가 반복해서 잡혔습니다.",
                    "angle": "개별 종목 등락보다 AI 투자와 실적 숫자가 서로 맞물리는지 먼저 설명하고, 관련 종목 차트로 확인합니다.",
                    "selected_item_ids": [row.get("id") for row in selected if row.get("id")],
                }
            )
    return filtered[:5]


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


def source_status_table(target_date: str) -> list[str]:
    processed = PROCESSED_DIR / target_date
    rows = []
    for name, label in [
        ("today-misc-batch-a-candidates.json", "뉴스 A"),
        ("today-misc-batch-b-candidates.json", "뉴스 B"),
        ("x-timeline-posts.json", "X"),
        ("visual-cards.json", "시각 자료"),
        ("finviz-feature-stocks.json", "특징주"),
    ]:
        payload = load_json(processed / name)
        if not payload:
            continue
        ok_count = sum(1 for row in payload.get("source_results", []) if row.get("status") == "ok")
        error_count = sum(1 for row in payload.get("source_results", []) if row.get("status") == "error")
        item_count = len(payload.get("candidates") or payload.get("posts") or payload.get("cards") or payload.get("items") or [])
        captured = short_dt(payload.get("captured_at") or payload.get("created_at"))
        rows.append([label, captured or "-", str(item_count), str(ok_count), str(error_count)])
    if not rows:
        return []
    lines = [
        "| 구분 | 수집 시각 | 후보/자료 | 성공 소스 | 실패 소스 |",
        "|---|---:|---:|---:|---:|",
    ]
    lines.extend(f"| {label} | {captured} | {items} | {ok} | {errors} |" for label, captured, items, ok, errors in rows)
    return lines


def keyword_example_title(item: dict) -> str:
    text = clean(f"{item.get('headline') or item.get('title') or ''} {item.get('summary') or item.get('text') or ''}")
    lowered = text.lower()
    if "entry-level jobs" in lowered and "ai" in lowered:
        return "AI가 바꾸는 신입 채용"
    if "sell in may" in lowered:
        return "5월 증시 계절성 논쟁"
    if "tesla stock" in lowered:
        return "테슬라 실적 반응"
    if "meta stock" in lowered or ("meta" in lowered and "ai spending" in lowered):
        return "메타 AI 투자 부담"
    if "oil & gas" in lowered or "commodity bull" in lowered:
        return "에너지주와 원자재 강세"
    if "series i" in lowered or "treasury department" in lowered:
        return "미 국채·저축채권 금리"
    if "iran blockade" in lowered or "hormuz" in lowered:
        return "이란·호르무즈 유가 리스크"
    if "tech stocks" in lowered and "big tech" in lowered:
        return "빅테크 실적 랠리"
    if "netomi" in lowered:
        return "AI 고객지원 스타트업 투자"
    if "amazon" in lowered and "backlog" in lowered:
        return "아마존 수주잔고와 클라우드"
    if "us stocks mixed" in lowered:
        return "미 증시 혼조"
    if "market concentration" in lowered:
        return "대형주 쏠림"
    if "sector p/e" in lowered or "valuations" in lowered:
        return "섹터 밸류에이션"
    return clean(item.get("headline") or item.get("title") or item.get("summary") or item.get("text"), 30)


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
                    row["examples"].append(keyword_example_title(item))
    ranked = sorted(rows_by_theme.values(), key=lambda row: (-row["count"], row["keyword"]))
    return [row for row in ranked if row["count"]][:limit]


def selected_rows(ledger: list[dict]) -> list[dict]:
    return [row for row in ledger if row.get("selection_status") == "selected"]


def reserve_rows(ledger: list[dict]) -> list[dict]:
    return [row for row in ledger if row.get("selection_status") == "reserve"]


def material_title(row: dict, limit: int = 42) -> str:
    return clean(compact_radar_title(row) or row.get("headline") or row.get("title") or row.get("summary") or row.get("id"), limit)


def radar_material_title(row: dict, limit: int = 46) -> str:
    return clean(row.get("title") or row.get("summary") or row.get("id"), limit)


def compact_radar_title(row: dict) -> str:
    text = clean(f"{row.get('title') or ''} {row.get('summary') or ''}")
    lowered = text.lower()
    if "south korea" in lowered and "exports" in lowered and "semiconductor" in lowered:
        return "한국 수출과 반도체 수요"
    if "us stocks advanced" in lowered and "oil supply shock" in lowered:
        return "유가 충격에도 버틴 미국 증시"
    if "australia and japan markets" in lowered and "iran" in lowered:
        return "이란 리스크를 넘겨보는 아시아 증시"
    if "standard intelligence" in lowered and ("$75m" in lowered or "computer use ai" in lowered):
        return "컴퓨터 사용 AI 투자 열기"
    if "s&p is considering rule changes" in lowered and "index" in lowered:
        return "신규 상장사 지수 편입 논의"
    if "ai is reshaping the american workplace" in lowered:
        return "AI 도구가 바꾸는 고소득 업무"
    if "real capex" in lowered and "ai" in lowered:
        return "AI 투자가 끌어올린 설비투자"
    if "huawei" in lowered and "ai chip" in lowered and ("60%" in lowered or "surge" in lowered):
        return "화웨이 AI 칩 매출 급증"
    if "breaking: apple stock" in lowered or ("apple stock" in lowered and "earnings" in lowered):
        return "애플 실적 반응"
    if "godaddy" in lowered and "ai" in lowered and "revenue" in lowered:
        return "GoDaddy의 AI 기반 매출 가이던스"
    if "white house ai memo" in lowered or ("bloomberg:" in lowered and "ai memo" in lowered):
        return "백악관 AI 조달 메모"
    if "tech stocks today" in lowered or ("big tech earnings" in lowered and "ai spending" in lowered):
        return "빅테크 실적과 AI 투자 부담"
    if "stocks mixed" in lowered and ("strong earnings" in lowered or "ai hopes" in lowered):
        return "실적 호조 속 미 증시 혼조"
    if "brent crude oil prices" in lowered or ("brent" in lowered and "$120" in lowered):
        return "브렌트 120달러 돌파"
    if "rubio" in lowered and "wang yi" in lowered and "iran" in lowered:
        return "미중의 이란 관련 통화"
    if "trump to get briefed" in lowered and "iran" in lowered:
        return "트럼프의 이란 대응 브리핑"
    if "compute constrain" in lowered or ("googl" in lowered and "compute" in lowered):
        return "구글 AI 컴퓨팅 부족"
    if "retail investors are piling" in lowered and "semiconductor" in lowered:
        return "개인 레버리지 반도체 ETF 과열"
    if "both wholesale" in lowered and "retail" in lowered and "inventor" in lowered:
        return "도소매 재고 증가"
    if "point72 founder steve cohen" in lowered:
        return "스티브 코언의 운용조직 개편"
    if "google q1 revenues" in lowered or "cloud revenue grew" in lowered:
        return "구글 실적과 클라우드 성장"
    if "semiconduct" in lowered and ("s&p 500" in lowered or "breaking" in lowered):
        return "반도체 지수 강세"
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
    if "한국 수출" in title:
        return "반도체 수요가 유가·지정학 부담 속에서도 경기 해석의 버팀목이 되는지 보여주는 자료입니다."
    if "버틴 미국 증시" in title:
        return "유가 충격에도 실적과 AI 기대가 지수를 방어하는지 확인할 수 있는 시장 반응 자료입니다."
    if "아시아 증시" in title:
        return "아시아 장이 이란 리스크를 어떻게 소화하는지 보며 글로벌 위험선호의 온도를 확인할 수 있습니다."
    if "컴퓨터 사용 AI" in title:
        return "AI 기대가 인프라를 넘어 실제 업무 자동화 스타트업 투자로 확산되는지 보여주는 단신입니다."
    if "지수 편입" in title:
        return "대형 IPO와 지수 수요가 만날 때 시장 구조가 어떻게 바뀔 수 있는지 보여주는 자료입니다."
    if "고소득 업무" in title:
        return "AI 도입이 소비자 유행이 아니라 고소득 업무 생산성 논리로 이동하고 있음을 보여주는 자료입니다."
    if "설비투자" in title:
        return "AI 테마가 실제 기업 투자와 CapEx 사이클로 이어지는지 확인하는 매크로 근거입니다."
    if "화웨이 AI 칩" in title:
        return "중국 AI 반도체 수요가 Nvidia 공백과 맞물려 실제 매출 성장으로 이어지는지 보여주는 자료입니다."
    if "GoDaddy" in title:
        return "AI 기능이 중소기업 소프트웨어 매출 전망까지 끌어올리는지 확인할 수 있는 실적 가이던스 자료입니다."
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
        lines.append(f"작성 시점: `{display_dt(row.get('published_at'))}`")
    summary = summarize_material_text(row)
    if summary:
        lines.append(f"- 요약: {summary}")
    if row.get("visual_local_path"):
        lines.extend(["", notion_image(title, row["visual_local_path"])])
    lines.append("")


def render_support_card(lines: list[str], row: dict) -> None:
    title = compact_radar_title({"title": row.get("headline") or row.get("title") or "", "summary": row.get("summary") or ""})
    lines.extend([f"### {title}", ""])
    lines.extend([f"> {material_quote(title, {'summary': row.get('summary') or row.get('headline') or ''})}", ""])
    label = source_label(row.get("source_name") or row.get("source_id"), row.get("url") or "")
    lines.append(f"출처: {link(label, row.get('url') or '')}")
    if row.get("published_at"):
        lines.append(f"작성 시점: `{display_dt(row.get('published_at'))}`")
    lines.append(f"- {clean(row.get('summary') or row.get('headline'), 150)}")
    for image in row.get("image_refs") or []:
        if image.get("local_path"):
            lines.extend(["", notion_image(title, image["local_path"])])
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
    ticker = (row.get("ticker") or "-").upper()
    lines.extend([f"### {company_heading(ticker)}", ""])
    lines.extend([f"> {feature_stock_focus(row)}", ""])
    news = finviz_news_line(row)
    lines.append(f"출처: {link('Finviz', row.get('url') or '')}")
    if news.get("headline"):
        prefix = f"{news.get('time')}: " if news.get("time") else ""
        lines.append(f"- Finviz 한 줄 뉴스: {link(clean(prefix + news.get('headline'), 150), news.get('url') or row.get('url') or '')}")
    if row.get("screenshot_path"):
        lines.extend(["", notion_image(f"{company_heading(ticker)} 일봉", row["screenshot_path"])])
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
        lines.append(f"작성 시점: `{display_dt(row.get('published_at'))}`")
    if row.get("summary"):
        lines.append(f"- 요약: {material_summary(row, 180)}")
    if row.get("visual_local_path"):
        lines.extend(["", notion_image(title, row["visual_local_path"])])
    lines.append("")


def storyline_refs(storyline: dict, radar_by_id: dict, ledger: list[dict]) -> list[str]:
    refs = []
    seen = set()
    for item_id in storyline.get("selected_item_ids", []):
        match = radar_by_id.get(item_id) or next((row for row in ledger if row.get("id") == item_id), None)
        if not match:
            continue
        title = compact_radar_title(match)
        if title in seen:
            continue
        seen.add(title)
        refs.append(title)
    return refs


def public_selection_reason(reason: str, title: str) -> str:
    text = clean(reason, 180)
    internal_patterns = [
        "출처가 같은 방향의 신호",
        "점수와 구체성이",
        "기존 점수 기반",
        "dynamic_cluster",
        "cluster_score",
        "selection_method",
    ]
    if any(pattern in text for pattern in internal_patterns):
        if "유가" in title or "에너지" in title:
            return "유가와 지정학 뉴스가 에너지주, 인플레이션 기대, 위험선호를 함께 흔들 수 있는 구간이라 방송 꼭지로 쓰기 좋습니다."
        if "실적" in title:
            return "실적 숫자가 시장 기대를 실제로 뒷받침하는지 확인할 수 있는 자료들이 모여 있어 메인 꼭지 후보로 적합합니다."
        if "AI" in title or "OpenAI" in title:
            return "AI 기대가 매출, 투자, 반도체 수요로 이어지는지 확인할 수 있는 자료들이 있어 독립 꼭지로 다룰 만합니다."
        return "오늘 수집 자료에서 시장 반응과 방송 자료를 함께 만들기 좋은 각도로 잡힌 후보입니다."
    return text


def render_storyline(lines: list[str], index: int, storyline: dict, radar_by_id: dict, ledger: list[dict]) -> None:
    refs = storyline_refs(storyline, radar_by_id, ledger)
    title = clean(storyline.get("title"))
    recommendation = clean(storyline.get("recommendation") or "")
    recommendation_label = clean(storyline.get("recommendation_label") or "")
    lines.extend(
        [
            f"## {index}. {title}",
            "",
            f"추천도: `{recommendation}` {recommendation_label}".rstrip(),
            "",
            f"> {clean(storyline.get('one_liner'), 150)}",
            "",
            "### 선정 이유",
            "",
            f"- {public_selection_reason(storyline.get('why_selected'), title)}",
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
        lines.append(f"- 마지막으로 `{refs[2]}` 자료를 통해 시각자료와 특징주 정리")
    lines.extend(["", "### 방송 멘트 초안", ""])
    if "유가" in title:
        lines.append("- 오늘 시장은 유가와 지정학 이슈를 무시하는 것처럼 보이지만, 실제로는 AI 기대가 그 충격을 덮고 있는지 확인해야 합니다.")
        lines.append("- 첫 장은 리스크를 던지고, 다음 장에서 투자자들의 위험선호가 얼마나 강한지 보여주면 흐름이 자연스럽습니다.")
    elif "강세장" in title or "과열" in title:
        lines.append("- 두 번째 꼭지는 시장이 비싼 줄 알면서도 왜 계속 사는지 묻는 흐름으로 잡습니다.")
        lines.append("- 포지셔닝, 콜옵션, 밸류에이션 경고를 이어 붙이면 강세장의 연료와 과열 신호를 동시에 보여줄 수 있습니다.")
    elif "실적" in title:
        lines.append("- AI 기대가 계속 시장을 지탱하려면 결국 실적과 클라우드 성장, CapEx 숫자로 확인돼야 합니다.")
        lines.append("- 캘린더 이미지는 일정 확인용으로만 두고, 실제 방송에서는 알파벳과 빅테크 차트로 기대가 가격에 반영되는지 확인합니다.")
    else:
        lines.append("- AI 이야기는 이제 기대감이 아니라 매출, CapEx, 생산성으로 증명되는 단계인지가 핵심입니다.")
        lines.append("- 구글 TPU, AI 노동 자동화, 기업인의 AI 발언을 묶으면 ‘성장에 꽂힌 시장’이라는 꼭지로 독립 배치할 수 있습니다.")
    lines.append("")


def valid_editorial_brief(brief: dict) -> bool:
    return bool(
        brief
        and isinstance(brief.get("storylines"), list)
        and len(brief.get("storylines") or []) >= 3
        and brief.get("daily_thesis")
    )


def stars_text(value: int | str | None) -> str:
    try:
        stars = max(1, min(3, int(value or 1)))
    except (TypeError, ValueError):
        stars = 1
    return "★" * stars + "☆" * (3 - stars)


def evidence_title(evidence: dict, radar_by_id: dict) -> str:
    item_id = evidence.get("item_id") or ""
    row = radar_by_id.get(item_id)
    raw = clean(evidence.get("title") or "")
    if row:
        compact = compact_radar_title({**row, "title": raw or row.get("title") or ""})
        if should_localize_title(raw):
            localized = localize_title(raw)
            return clean(localized if localized and localized != raw else compact, 80)
        return clean(compact or raw or item_id, 80)
    localized = localize_title(raw) if should_localize_title(raw) else ""
    return clean(localized or raw or item_id, 80)


def should_localize_title(value: str) -> bool:
    text = clean(value)
    if not text:
        return False
    if re.search(r"[가-힣]", text):
        return False
    lowered = text.lower()
    return any(
        token in lowered
        for token in [
            "tech stocks today",
            "big tech earnings",
            "brent",
            "oil prices",
            "compute constrained",
            "google q1",
            "microsoft q1",
            "meta q1",
            "google cloud",
            "retail investors",
            "semiconductor",
            "trump",
            "trader or driller",
            "33 minutes ago reuters",
            "huawei expects ai chip",
            "us stocks advanced",
            "breaking: apple stock",
            "apple $aapl guide",
            "real capex",
            "oil holds weekly gain",
            "exxon mobil",
            "stock market just had its best month",
            "s&p 500 officially posts",
            "manias, panics",
            "equity market concentration",
            "sector p/e valuations",
            "bull and bear indicator",
            "australia and japan markets",
            "standard intelligence raises",
        ]
    )


def localize_title(value: str) -> str:
    text = clean(value, 140)
    lowered = text.lower()
    if "tech stocks today" in lowered or "big tech earnings" in lowered:
        return "빅테크 실적과 AI 투자 부담"
    if "brent" in lowered and "$120" in lowered:
        return "브렌트유 $120 돌파 캡처"
    if "oil prices" in lowered or "us oil prices" in lowered:
        return "유가 급등 캡처"
    if "trump" in lowered and ("iran" in lowered or "blockade" in lowered):
        return "이란 봉쇄 발언과 유가 리스크"
    if "trader or driller" in lowered:
        return "에너지 업종 영향 분석"
    if "compute constrained" in lowered:
        return "구글 클라우드 컴퓨트 제약 발언"
    if "google q1" in lowered or "google q1 revenues" in lowered:
        return "구글 1분기 실적 요약"
    if "microsoft q1" in lowered or "azure" in lowered:
        return "마이크로소프트 Azure 성장 요약"
    if "meta q1" in lowered:
        return "메타 실적과 AI 투자 요약"
    if "google cloud" in lowered:
        return "구글 클라우드와 AI 투자 경쟁"
    if "retail investors" in lowered and "semiconductor" in lowered:
        return "개인 레버리지 반도체 ETF 쏠림"
    if "semiconductor" in lowered and "41.9" in lowered:
        return "반도체 업종 집중도 41.9%"
    if "huawei expects ai chip" in lowered or ("reuters" in lowered and "ai chip" in lowered):
        return "화웨이 AI 칩 매출 전망"
    if "us stocks advanced" in lowered:
        return "유가 충격에도 오른 미국 증시"
    if "breaking: apple stock" in lowered or ("apple stock" in lowered and "earnings" in lowered):
        return "애플 실적 반응"
    if "apple $aapl guide" in lowered or ("aapl" in lowered and "guide" in lowered):
        return "애플 분기 가이던스"
    if "real capex" in lowered and "ai" in lowered:
        return "AI 투자가 끌어올린 실질 설비투자"
    if "oil holds weekly gain" in lowered:
        return "유가 주간 상승과 지정학 리스크"
    if "trump bets hormuz" in lowered or ("hormuz" in lowered and "blockade" in lowered):
        return "호르무즈 봉쇄 리스크"
    if "exxon mobil" in lowered or "chevron" in lowered:
        return "에너지주 실적 일정"
    if "stock market just had its best month" in lowered:
        return "2020년 이후 최고의 월간 랠리"
    if "s&p 500 officially posts" in lowered:
        return "S&P500 사상 최고치"
    if "manias, panics" in lowered:
        return "과열과 신고가 차트 점검"
    if "equity market concentration" in lowered:
        return "S&P500 상위 종목 집중도"
    if "sector p/e valuations" in lowered:
        return "S&P500 섹터 밸류에이션"
    if "bull and bear indicator" in lowered:
        return "S&P500 강세·약세 지표"
    if "australia and japan markets" in lowered:
        return "이란 리스크를 넘겨보는 아시아 증시"
    if "standard intelligence raises" in lowered:
        return "컴퓨터 사용 AI 투자 열기"
    return text


def short_reference_id(value: object) -> str:
    text = clean(str(value or ""), 120)
    if not text.startswith("http"):
        return text
    match = re.search(r"https?://(?:www\.)?([^/]+)/(.+)", text)
    if not match:
        return "url-ref"
    host = match.group(1).replace("twitter.com", "x.com")
    tail = match.group(2).rstrip("/").split("/")[-1] or host
    if host == "x.com":
        return f"x:{tail}"
    return clean(f"{host}:{tail}", 80)


def slide_order_title(value: str, radar_by_id: dict) -> str:
    text = clean(value, 140)
    row = radar_by_id.get(text)
    if row:
        return compact_radar_title(row)
    if text.startswith("http"):
        return clean(Path(text.rstrip("/")).name or text, 80)
    return text


def evidence_kind_label(value: str | None) -> str:
    role = clean(value or "").lower()
    return {
        "fact": "팩트",
        "data": "데이터",
        "analysis": "분석",
        "sentiment": "시장 반응",
        "visual": "시각자료",
        "market_reaction": "시장 반응",
    }.get(role, "맥락")


def visual_role_label(value: str | None) -> str:
    role = clean(value or "").lower()
    if "fact" in role:
        return "팩트 장표"
    if "analysis" in role:
        return "분석 장표"
    if "data" in role or "chart" in role:
        return "차트"
    if "x_post" in role or "screenshot" in role:
        return "캡처"
    if "visual" in role:
        return "시각자료"
    return "장표"


def is_sentiment_asset(asset: dict) -> bool:
    blob = clean(
        " ".join(
            str(asset.get(key) or "")
            for key in ["source", "source_role", "visual_asset_role", "caption", "why_this_visual", "risks_or_caveats", "url"]
        )
    ).lower()
    return bool(
        "sentiment" in blob
        or "x_post" in blob
        or "x.com" in blob
        or "twitter.com" in blob
        or "reddit" in blob
        or "소셜" in blob
    )


def asset_allowed_as_slide(asset: dict) -> bool:
    if not asset.get("use_as_slide"):
        return False
    if is_sentiment_asset(asset) and not clean(asset.get("slide_exception_reason")):
        return False
    return True


def storyline_blob(storyline: dict) -> str:
    parts = []
    for key in [
        "title",
        "hook",
        "lead_candidate_reason",
        "why_now",
        "core_argument",
        "talk_track",
        "market_causality",
        "expectation_gap",
        "prepricing_risk",
    ]:
        parts.append(str(storyline.get(key) or ""))
    for evidence in (storyline.get("evidence_to_use") or []) + (storyline.get("evidence_to_drop") or []):
        for key in ["title", "source", "source_role", "evidence_role", "reason"]:
            parts.append(str(evidence.get(key) or ""))
    for asset in storyline.get("ppt_asset_queue") or []:
        for key in ["caption", "visual_asset_role", "why_this_visual", "risks_or_caveats"]:
            parts.append(str(asset.get(key) or ""))
    return clean(" ".join(parts), 4000).lower()


def storyline_asset_blob(storyline: dict) -> str:
    parts = []
    for evidence in storyline.get("evidence_to_use") or []:
        for key in ["title", "source", "source_role", "evidence_role", "reason"]:
            parts.append(str(evidence.get(key) or ""))
    for asset in storyline.get("ppt_asset_queue") or []:
        for key in ["caption", "visual_asset_role", "why_this_visual", "risks_or_caveats"]:
            parts.append(str(asset.get(key) or ""))
    return clean(" ".join(parts), 4000).lower()


LEAD_REQUIREMENTS = [
    {
        "axis": "rates_macro",
        "label": "금리·달러",
        "axis_patterns": [r"\brate", r"\brates", r"\bfed\b", r"\bfomc\b", r"\bdxy\b", r"\bdollar", r"금리", r"달러", r"연준"],
        "required": {
            "10Y": [r"\b10y\b", r"10-year", r"10년", r"treasury", r"국채"],
            "DXY/달러": [r"\bdxy\b", r"dollar", r"달러", r"원달러"],
            "TLT": [r"\btlt\b"],
            "나스닥/성장주 반응": [r"nasdaq", r"qqq", r"growth", r"duration", r"나스닥", r"성장주"],
        },
        "minimum": 2,
    },
    {
        "axis": "oil",
        "label": "유가",
        "axis_patterns": [r"\boil\b", r"\bwti\b", r"brent", r"crude", r"opec", r"hormuz", r"유가", r"원유", r"호르무즈"],
        "required": {
            "WTI": [r"\bwti\b", r"crude", r"원유"],
            "Brent": [r"brent", r"브렌트"],
            "XLE/에너지주": [r"\bxle\b", r"energy", r"에너지", r"xom", r"cvx"],
            "OPEC/EIA/호르무즈": [r"opec", r"eia", r"hormuz", r"inventory", r"호르무즈", r"재고"],
        },
        "minimum": 2,
    },
    {
        "axis": "earnings",
        "label": "실적",
        "axis_patterns": [r"earnings", r"\beps\b", r"revenue", r"guidance", r"실적", r"가이던스", r"매출"],
        "required": {
            "EPS": [r"\beps\b", r"주당순이익"],
            "매출": [r"revenue", r"sales", r"매출"],
            "가이던스": [r"guidance", r"outlook", r"forecast", r"가이던스", r"전망"],
            "주가 반응": [r"after[- ]?hours", r"pre[- ]?market", r"reaction", r"shares", r"주가", r"시간외"],
        },
        "minimum": 2,
    },
    {
        "axis": "ai",
        "label": "AI",
        "axis_patterns": [r"\bai\b", r"artificial intelligence", r"capex", r"cloud", r"semiconductor", r"data center", r"인공지능", r"반도체", r"데이터센터"],
        "required": {
            "CapEx": [r"capex", r"capital expenditure", r"투자"],
            "클라우드/매출": [r"cloud", r"revenue", r"sales", r"클라우드", r"매출"],
            "반도체 반응": [r"semiconductor", r"nvidia", r"nvda", r"amd", r"반도체"],
            "데이터센터 수요": [r"data center", r"datacenter", r"데이터센터"],
        },
        "minimum": 2,
    },
]


def match_any(blob: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, blob, flags=re.I) for pattern in patterns)


def lead_requirement_status(storyline: dict) -> dict:
    blob = storyline_blob(storyline)
    asset_blob = f"{storyline_asset_blob(storyline)} {generated_market_asset_blob()}"
    for spec in LEAD_REQUIREMENTS:
        if not match_any(blob, spec["axis_patterns"]):
            continue
        present = [
            label
            for label, patterns in spec["required"].items()
            if match_any(asset_blob, patterns)
        ]
        missing = [label for label in spec["required"] if label not in present]
        minimum = int(spec["minimum"])
        return {
            "axis": spec["axis"],
            "label": spec["label"],
            "present": present,
            "missing": missing,
            "minimum": minimum,
            "met": len(present) >= minimum,
        }
    return {"axis": "", "label": "", "present": [], "missing": [], "minimum": 0, "met": True}


def lead_status_text(storyline: dict) -> str:
    status = lead_requirement_status(storyline)
    if not status["axis"]:
        return "리드 확정 가능"
    if status["met"]:
        return f"{status['label']} 리드 확정 가능"
    return f"{status['label']} 리드 후보: 수치 확인 필요"


def evidence_brief_title(item: dict, radar_by_id: dict, limit: int = 44) -> str:
    return clean(evidence_title(item, radar_by_id), limit)


def story_slide_titles(storyline: dict, radar_by_id: dict, limit: int = 5) -> list[str]:
    values = []
    for asset in storyline.get("ppt_asset_queue") or []:
        if asset_allowed_as_slide(asset):
            caption = clean(asset.get("caption"), 80)
            if caption:
                values.append(caption)
    for item in storyline.get("slide_plan") or storyline.get("slide_order") or []:
        title = slide_order_title(item, radar_by_id)
        if title and title not in values:
            values.append(title)
    for evidence in storyline.get("evidence_to_use") or []:
        role = clean(evidence.get("evidence_role")).lower()
        if role in {"fact", "data", "analysis", "market_reaction", "visual"}:
            title = evidence_brief_title(evidence, radar_by_id)
            if title and title not in values:
                values.append(title)
    return values[:limit]


def evidence_source_label(evidence: dict, radar_by_id: dict) -> str:
    row = radar_by_id.get(evidence.get("item_id") or "") or {}
    source = evidence.get("source") or row.get("source") or row.get("type") or ""
    url = evidence.get("url") or row.get("url") or ""
    return source_label(source, url)


def evidence_reference_values(evidence: dict) -> set[str]:
    values = set()
    for key in ["item_id", "evidence_id", "id", "url"]:
        value = clean(str(evidence.get(key) or ""))
        if value:
            values.add(value)
            values.add(short_reference_id(value))
    return values


def asset_reference_values(asset: dict) -> set[str]:
    values = set()
    for key in ["asset_id", "evidence_id", "item_id", "url"]:
        value = clean(str(asset.get(key) or ""))
        if not value:
            continue
        values.add(value)
        values.add(short_reference_id(value))
        if ":" in value:
            tail = value.split(":", 1)[1]
            if tail.startswith("http"):
                values.add(tail)
                values.add(short_reference_id(tail))
    return values


def slide_asset_reference_values(brief: dict) -> set[str]:
    values: set[str] = set()
    for asset in flatten_ppt_assets(brief):
        if not asset_allowed_as_slide(asset):
            continue
        values.update(asset_reference_values(asset))
    return {value for value in values if value}


def render_editorial_storyline(lines: list[str], index: int, storyline: dict, radar_by_id: dict) -> None:
    title = clean(storyline.get("title"), 90)
    evidence_to_use = storyline.get("evidence_to_use") or []
    evidence_to_drop = storyline.get("evidence_to_drop") or []
    slide_order = [
        slide_order_title(item, radar_by_id)
        for item in (storyline.get("slide_plan") or storyline.get("slide_order") or [])
        if clean(item)
        and "auto_added_fact_data_analysis_support" not in clean(item)
        and "자동 보강" not in clean(item)
        and "causal anchor" not in clean(item).lower()
    ]
    ppt_assets = storyline.get("ppt_asset_queue") or []
    lines.extend(
        [
            f"## {index}. {title}",
            "",
            f"추천도: `{stars_text(storyline.get('recommendation_stars'))}` {clean_complete(storyline.get('rating_reason'), 180)}".rstrip(),
            "",
            f"- 첫 꼭지 판단: {public_editorial_text(storyline.get('lead_candidate_reason') or ('보조 꼭지 후보' if index > 1 else ''), 220)}",
            f"- 신호/소음: `{signal_label(storyline.get('signal_or_noise'))}`",
            f"- 원인 판단: {public_editorial_text(storyline.get('market_causality') or '근거 조합 확인 필요', 180)}",
            f"- 기대/선반영: 기대 `{public_editorial_text(storyline.get('expectation_gap') or 'check_if_relevant', 110)}` · 선반영 `{public_editorial_text(storyline.get('prepricing_risk') or 'check_if_relevant', 110)}`",
            f"- 첫 5분 적합도/한국장 관련성: `{compact_status(storyline.get('first_5min_fit'), 'medium')}` / `{compact_status(storyline.get('korea_open_relevance'), 'medium')}`",
            "",
            f"> {public_editorial_text(storyline.get('hook'), 220)}",
            "",
            "### 왜 지금",
            "",
            public_editorial_text(storyline.get("why_now"), 320),
            "",
            "### 핵심 주장",
            "",
            public_editorial_text(storyline.get("core_argument"), 320),
            "",
            "### 쓸 자료",
            "",
        ]
    )
    if evidence_to_use:
        for item in evidence_to_use[:5]:
            title = evidence_title(item, radar_by_id)
            reason = public_editorial_text(item.get("reason"), 180)
            source = evidence_source_label(item, radar_by_id)
            kind = evidence_kind_label(item.get("evidence_role"))
            lines.append(f"- `{title}`: {reason} (출처: {source}, 성격: {kind})")
    else:
        lines.append("- 핵심 근거가 부족합니다. 방송 전 수동 확인이 필요합니다.")
    if evidence_to_drop:
        lines.extend(["", "### 버릴 자료", ""])
        for item in evidence_to_drop[:3]:
            title = evidence_title(item, radar_by_id)
            reason = public_editorial_text(item.get("reason"), 160)
            drop_code = clean(item.get("drop_code") or storyline.get("drop_code") or "support_only", 60)
            lines.append(f"- `{title}` / `{drop_code}`: {reason}")
    if ppt_assets:
        slide_assets = [asset for asset in ppt_assets if asset.get("use_as_slide")]
        lines.extend(["", "### PPT 캡처/장표 후보", ""])
        for asset in slide_assets[:5]:
            caption = clean(asset.get("caption"), 120)
            why = public_editorial_text(asset.get("why_this_visual"), 160)
            caveat = public_editorial_text(asset.get("risks_or_caveats"), 120)
            lines.append(f"- {caption}: {why} / 주의: {caveat}")
        if not slide_assets:
            lines.append("- 이 꼭지는 말로만 처리하는 편이 낫습니다.")
    lines.extend(["", "### 구성", ""])
    if slide_order:
        for item in slide_order[:5]:
            lines.append(f"- {item}")
    else:
        lines.append("- 훅 → 핵심 근거 → 반론/주의점 순서로 구성합니다.")
    lines.extend(
        [
            "",
            "### 방송 멘트 초안",
            "",
            public_editorial_text(storyline.get("talk_track"), 420),
            "",
            "### 반론/주의점",
            "",
            public_editorial_text(storyline.get("counterpoint"), 260),
            "",
            "### 판단이 바뀌는 조건",
            "",
            public_editorial_text(storyline.get("what_would_change_my_mind"), 240),
            "",
            "### 클로징 한 줄",
            "",
            public_editorial_text(storyline.get("closing_line"), 220),
            "",
        ]
    )


def editorial_summary_bullets(brief: dict) -> list[str]:
    summary = clean(brief.get("editorial_summary"), 700)
    if not summary:
        return []
    parts = [part.strip() for part in re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+", summary) if part.strip()]
    return [clean_complete(part, 180) for part in (parts[:3] if parts else [summary])]


def flatten_ppt_assets(brief: dict) -> list[dict]:
    assets = list(brief.get("ppt_asset_queue") or [])
    seen = {item.get("asset_id") for item in assets if item.get("asset_id")}
    for story in brief.get("storylines") or []:
        for asset in story.get("ppt_asset_queue") or []:
            key = asset.get("asset_id") or f"{asset.get('storyline_id')}:{asset.get('caption')}"
            if key in seen:
                continue
            seen.add(key)
            assets.append(asset)
    return sorted(assets, key=lambda item: int(item.get("slide_priority") or 99))


def flatten_talk_only(brief: dict) -> list[dict]:
    slide_refs = slide_asset_reference_values(brief)
    rows = list(brief.get("talk_only_queue") or [])
    filtered_rows = []
    seen = set()
    for item in rows:
        refs = evidence_reference_values(item)
        if refs & slide_refs:
            continue
        key = item.get("item_id") or item.get("evidence_id")
        if key:
            seen.add(key)
        filtered_rows.append(item)
    rows = filtered_rows
    for story in brief.get("storylines") or []:
        for evidence in story.get("evidence_to_use") or []:
            if evidence.get("evidence_role") != "sentiment":
                continue
            if evidence_reference_values(evidence) & slide_refs:
                continue
            if evidence.get("item_id") in seen:
                continue
            seen.add(evidence.get("item_id"))
            rows.append(evidence)
        for asset in story.get("ppt_asset_queue") or []:
            if not is_sentiment_asset(asset) or clean(asset.get("slide_exception_reason")):
                continue
            key = asset.get("asset_id") or asset.get("item_id") or asset.get("evidence_id") or asset.get("caption")
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "item_id": asset.get("item_id") or asset.get("asset_id"),
                    "evidence_id": asset.get("evidence_id"),
                    "title": asset.get("caption") or asset.get("source") or "소셜 반응",
                    "evidence_role": "sentiment",
                    "reason": asset.get("risks_or_caveats") or asset.get("why_this_visual") or "분위기 참고용이라 장표 대신 말로만 처리",
                }
            )
    return rows


def flatten_drop_items(brief: dict) -> list[dict]:
    rows = list(brief.get("drop_list") or [])
    seen = {item.get("item_id") for item in rows if item.get("item_id")}
    for story in brief.get("storylines") or []:
        for evidence in story.get("evidence_to_drop") or []:
            if evidence.get("item_id") in seen:
                continue
            seen.add(evidence.get("item_id"))
            rows.append(evidence)
    return rows


def compact_broadcast_order(brief: dict, storylines: list[dict]) -> list[str]:
    lead = storylines[0] if storylines else {}
    order = [
        "시장은 지금: 지수와 금리·달러의 온도",
    ]
    if lead:
        order.append(f"리드: {clean(story_display_title(lead), 64)}")
    for story in storylines[1:4]:
        title = clean(story_display_title(story), 56)
        if title:
            order.append(f"보조 꼭지: {title}")
    order.append("특징주: 실적과 종목 반응")
    return order[:5]


def compact_news_bullets(brief: dict, fallback: list[str]) -> list[str]:
    bullets = editorial_summary_bullets(brief)
    if not bullets:
        bullets = [clean_complete(item, 160) for item in fallback[:3]]
    public_bullets = []
    for item in bullets[:3]:
        raw = clean(item)
        if not raw:
            continue
        if "내부 준비안" in raw:
            continue
        if "소셜" in raw and ("sentiment" in raw.lower() or "사실 근거" in raw):
            continue
        public_bullets.append(public_editorial_text(raw, 150))
    return public_bullets


def status_from_paths(paths: list[str | Path], default: str = "미수집") -> str:
    return "확인 완료" if any(Path(path).exists() for path in paths if path) else default


def chart_status(*chart_ids: str) -> str:
    return status_from_paths([EXPORTS_DIR / f"{chart_id}.png" for chart_id in chart_ids])


def screenshot_status(target_date: str | None, *patterns: str) -> str:
    if not target_date:
        return "확인 필요"
    return "확인 완료" if screenshots_for(target_date, *patterns) else "미수집"


def asset_queue_status(assets: list[dict]) -> str:
    return "후보 있음" if assets else "미수집"


def table_cell(value: object, limit: int = 90) -> str:
    return clean(str(value or "").replace("|", "/"), limit) or "-"


def ppt_table_row(slide: str, title: str, material: str, status: str, action: str) -> str:
    return f"| {table_cell(slide, 12)} | {table_cell(title, 70)} | {table_cell(material, 110)} | {table_cell(status, 24)} | {table_cell(action, 90)} |"


def chart_takeaway(*chart_ids: str) -> str:
    titles = [chart_title(chart_id) for chart_id in chart_ids if chart_title(chart_id)]
    return " / ".join(titles) if titles else "최신 차트 확인"


def render_compact_host_view(
    lines: list[str],
    brief: dict,
    storylines: list[dict],
    radar_by_id: dict,
    today_axis: str,
    market_map_summary: str,
    summary_fallback: list[str],
) -> None:
    lead = storylines[0] if storylines else {}
    lead_status = lead_requirement_status(lead) if lead else {"present": [], "missing": [], "met": True, "label": ""}
    lead_assets = [clean(item, 36) for item in (story_slide_titles(lead, radar_by_id, 4) if lead else [])]
    talk_items = [
        evidence_brief_title(item, radar_by_id, 42)
        for item in (lead.get("evidence_to_use") or [])
        if clean(item.get("evidence_role")).lower() == "sentiment"
    ][:3]
    needed = lead_status["missing"][:4] if not lead_status["met"] else []
    news_bullets = compact_news_bullets(brief, summary_fallback)

    core_viewpoint = public_editorial_text(today_axis, 60)
    if core_viewpoint.endswith("…") and lead:
        core_viewpoint = story_display_title(lead)
    lines.extend(["# 진행자용 1페이지 요약", "", "## 오늘의 핵심 관점", "", f"- {core_viewpoint}", ""])
    lines.extend(["## 주요 뉴스 요약", ""])
    for bullet in news_bullets:
        lines.append(f"- {bullet}")
    if not news_bullets:
        lines.append("- 지수·금리·달러·유가 반응을 먼저 확인하고 리드 후보를 확정합니다.")
    lines.extend(["", "## 오늘 방송 순서", ""])
    for index, item in enumerate(compact_broadcast_order(brief, storylines), start=1):
        lines.append(f"{index}. {item}")

    lines.extend(["", "## 첫 꼭지", ""])
    if lead:
        check_lines = [f"{item} 확인 완료" for item in lead_status.get("present", [])[:3]]
        check_lines.extend(f"{item} 미수집" for item in needed[: max(0, 4 - len(check_lines))])
        lines.extend(
            [
                f"- 제목: {story_display_title(lead)}",
                f"- 상태: {lead_status_text(lead)}",
                f"- 왜 지금: {first_sentences(lead.get('lead_candidate_reason') or lead.get('why_now'), 2, 150)}",
                f"- 시장 지도: {public_editorial_text(market_map_summary, 160)}",
                "- 보여줄 자료: " + (", ".join(lead_assets[:3]) if lead_assets else "10Y/DXY/지수 반응 등 수동 확인"),
                "- 말로 처리: " + (", ".join(talk_items) if talk_items else "소셜 반응과 해석 보조는 짧게 언급"),
                "- 방송 전 체크: " + (", ".join(check_lines) if check_lines else "리드 핵심 수치와 최신 시세 재확인"),
            ]
        )
    else:
        lines.append("- 리드 후보 없음. market-radar와 editorial-brief fallback 여부를 확인하세요.")
    lines.append("")


def render_host_storyline(lines: list[str], index: int, storyline: dict, radar_by_id: dict) -> None:
    title = story_display_title(storyline)
    quote = public_editorial_text(storyline.get("hook") or storyline.get("core_argument"), 180)
    slide_titles = story_slide_titles(storyline, radar_by_id, 5)
    evidence_titles = [
        f"`{evidence_brief_title(item, radar_by_id, 42)}` ({evidence_kind_label(item.get('evidence_role'))})"
        for item in (storyline.get("evidence_to_use") or [])[:4]
    ]
    check_items = lead_requirement_status(storyline).get("missing", [])[:3]
    lines.extend(
        [
            f"### {index}. {title}",
            "",
            f"추천도: `{stars_text(storyline.get('recommendation_stars'))}`",
            "",
            f"> {quote}",
            "",
            "#### 선정 이유",
            "",
        ]
    )
    reason = first_sentences(storyline.get("lead_candidate_reason") or storyline.get("why_now"), 2, 180)
    lines.append(f"- {reason}")
    lines.append(f"- 신호 판단: {signal_label(storyline.get('signal_or_noise'))}")
    lines.extend(["", "#### 슬라이드 구성", ""])
    if slide_titles:
        for item in slide_titles:
            lines.append(f"- {item}")
    else:
        lines.append("- 훅 → 시장 지도 → 핵심 근거 → 반론/주의점")
    lines.extend(["", "#### 자료 배치", ""])
    if evidence_titles:
        for item in evidence_titles:
            lines.append(f"- {item}")
    else:
        lines.append("- 방송 전 fact/data/analysis 근거를 추가 확인")
    if check_items:
        lines.extend(["", "#### 확인 필요", ""])
        for item in check_items:
            lines.append(f"- {item}")
    short_hook = first_sentences(storyline.get("talk_track") or storyline.get("hook"), 1, 120)
    research_note = public_editorial_text(storyline.get("talk_track") or storyline.get("core_argument"), 320)
    lines.extend(["", "#### 짧은 말문", "", short_hook or quote, "", "#### 리서치 설명", "", research_note, ""])


def render_ppt_asset_queue(lines: list[str], brief: dict, target_date: str | None = None, radar_by_id: dict | None = None) -> None:
    assets = [asset for asset in flatten_ppt_assets(brief) if asset_allowed_as_slide(asset)]
    stories = brief.get("storylines") or []
    lead = next((story for story in stories if int(story.get("rank") or 0) == 1), stories[0] if stories else {})
    lead_id = lead.get("storyline_id") if lead else ""
    lead_assets = [asset for asset in assets if asset.get("storyline_id") == lead_id]
    other_assets = [asset for asset in assets if asset not in lead_assets]
    lead_materials = [clean(asset.get("caption"), 54) for asset in lead_assets[:2] if clean(asset.get("caption"))]
    other_materials = [clean(asset.get("caption"), 48) for asset in other_assets[:2] if clean(asset.get("caption"))]

    title_candidate = story_display_title(lead) if lead else "오늘 시장의 핵심 제약과 기회"
    lines.extend(
        [
            "## 슬라이드 제작 순서",
            "",
            "| 슬라이드 | 제목 | 자료 | 상태 | 작업 |",
            "|---:|---|---|---|---|",
            ppt_table_row("0", "타이틀", title_candidate, "초안 완료" if lead else "확인 필요", "표지 제목으로 사용"),
            ppt_table_row("1", "시장은 지금", "주요 지수 흐름", screenshot_status(target_date, "finviz-index-futures-*.png"), "오프닝 시장 지도"),
            ppt_table_row("2", "S&P500/Nasdaq", "지수 흐름 또는 선물 캡처", screenshot_status(target_date, "finviz-index-futures-*.png"), "위험선호 방향 확인"),
            ppt_table_row("3", "히트맵", "S&P500·러셀 히트맵", screenshot_status(target_date, "finviz-sp500-heatmap*.png", "*russell*heatmap*.png", "*iwm*heatmap*.png"), "섹터 확산 확인"),
            ppt_table_row("4", "10년물 금리", chart_takeaway("us10y"), chart_status("us10y"), "리드의 금리 축 확인"),
            ppt_table_row("5", "유가", chart_takeaway("crude-oil-wti", "crude-oil-brent"), chart_status("crude-oil-wti", "crude-oil-brent"), "headline과 가격 반응 비교"),
            ppt_table_row("6", "달러/원달러", chart_takeaway("dollar-index", "usd-krw"), chart_status("dollar-index", "usd-krw"), "환율 부담 확인"),
            ppt_table_row("7", "비트코인", chart_takeaway("bitcoin"), chart_status("bitcoin"), "위험자산 보조 온도계"),
            ppt_table_row("8", "리드", ", ".join(lead_materials) or "리드 근거 후보 없음", asset_queue_status(lead_assets), "큰 캡처 또는 핵심 문장 강조"),
            ppt_table_row("9", "보조/특징주", ", ".join(other_materials) or "실적/특징주 섹션에서 선별", asset_queue_status(other_assets), "짧은 보조 꼭지로 사용"),
            "",
        ]
    )


def render_talk_only_queue(lines: list[str], brief: dict, radar_by_id: dict) -> None:
    rows = flatten_talk_only(brief)
    if not rows:
        lines.append("- 말로만 처리할 자료가 별도로 지정되지 않았습니다.")
        return
    for item in rows[:10]:
        title = evidence_title(item, radar_by_id)
        role = evidence_kind_label(item.get("evidence_role") or "context")
        reason = public_editorial_text(item.get("reason"), 140)
        lines.append(f"- `{title}` / `{role}`: {reason}")


def render_drop_queue(lines: list[str], brief: dict, radar_by_id: dict) -> None:
    rows = flatten_drop_items(brief)
    if not rows:
        lines.append("- 버릴 자료가 별도로 지정되지 않았습니다.")
        return
    for item in rows[:10]:
        title = evidence_title(item, radar_by_id)
        drop_code = public_label(item.get("drop_code") or "support_only", 50)
        reason = public_editorial_text(item.get("reason"), 140)
        lines.append(f"- {title} / {drop_code}: {reason}")


def render_audit_log(lines: list[str], brief: dict, radar_by_id: dict, target_date: str | None = None) -> None:
    lines.extend(["# 검증 로그/회고용", "", "이 섹션은 진행자용 상단 화면이 아니라 품질검수와 방송 후 회고를 위한 내부 장부입니다.", ""])
    if target_date:
        status_table = source_status_table(target_date)
        if status_table:
            lines.extend(["## 수집 현황 표", "", *status_table, ""])
    for index, story in enumerate(brief.get("storylines") or [], start=1):
        story_id = clean(story.get("storyline_id") or f"storyline-{index}", 80)
        lines.extend([f"## {index}. {clean(story.get('title'), 90)}", "", f"- storyline_id: `{story_id}`"])
        flags = story_logic_flags(story)
        if flags:
            lines.append("- logic_flags: `" + "`, `".join(flags) + "`")
        for key in ["signal_or_noise", "market_causality", "expectation_gap", "prepricing_risk", "first_5min_fit", "korea_open_relevance"]:
            value = clean(story.get(key), 140)
            if value:
                lines.append(f"- {key}: `{value}`")
        status = lead_requirement_status(story)
        if status.get("axis"):
            lines.append(
                f"- lead_required_assets: axis=`{status['axis']}` present=`{', '.join(status['present']) or '-'}` missing=`{', '.join(status['missing']) or '-'}`"
            )
        use_items = story.get("evidence_to_use") or []
        if use_items:
            lines.extend(["", "### evidence_to_use", ""])
            for item in use_items[:8]:
                title = evidence_title(item, radar_by_id)
                item_id = clean(item.get("item_id"), 90)
                evidence_id = clean(item.get("evidence_id"), 90)
                source_role = clean(item.get("source_role"), 60)
                evidence_role = clean(item.get("evidence_role"), 60)
                reason = clean(item.get("reason"), 180)
                lines.append(
                    f"- `{title}` item_id=`{item_id}` evidence_id=`{evidence_id}` source_role=`{source_role}` evidence_role=`{evidence_role}` reason={reason}"
                )
        drop_items = story.get("evidence_to_drop") or []
        if drop_items:
            lines.extend(["", "### evidence_to_drop", ""])
            for item in drop_items[:8]:
                title = evidence_title(item, radar_by_id)
                item_id = clean(item.get("item_id"), 90)
                evidence_id = clean(item.get("evidence_id"), 90)
                drop_code = clean(item.get("drop_code") or story.get("drop_code"), 60)
                reason = clean(item.get("reason"), 180)
                lines.append(f"- `{title}` item_id=`{item_id}` evidence_id=`{evidence_id}` drop_code=`{drop_code}` reason={reason}")
        assets = story.get("ppt_asset_queue") or []
        if assets:
            lines.extend(["", "### ppt_asset_queue", ""])
            for asset in assets[:8]:
                caption = clean(asset.get("caption"), 100)
                asset_id = clean(asset.get("asset_id"), 100)
                visual_role = clean(asset.get("visual_asset_role"), 70)
                lines.append(
                    f"- `{caption}` asset_id=`{asset_id}` visual_asset_role=`{visual_role}` use_as_slide=`{asset.get('use_as_slide')}` use_as_talk_only=`{asset.get('use_as_talk_only')}`"
                )
        lines.append("")
    rows = flatten_drop_items(brief)
    if rows:
        lines.extend(["## 전체 drop_code 장부", ""])
        for item in rows[:16]:
            lines.append(
                f"- `{evidence_title(item, radar_by_id)}` item_id=`{clean(item.get('item_id'), 90)}` drop_code=`{clean(item.get('drop_code') or 'support_only', 60)}`"
            )
        lines.append("")


COMPANY_NAMES = {
    "AAPL": "애플",
    "AMZN": "아마존",
    "CVX": "셰브론",
    "GOOGL": "알파벳",
    "META": "메타",
    "MSFT": "마이크로소프트",
    "PI": "임핀지",
    "UBER": "우버",
    "V": "비자",
    "XLE": "에너지 섹터 ETF",
    "XOM": "엑슨모빌",
}


def company_heading(ticker: str) -> str:
    name = COMPANY_NAMES.get(ticker.upper())
    return f"{name} ({ticker.upper()})" if name else ticker.upper()


def feature_stock_focus(row: dict) -> str:
    ticker = (row.get("ticker") or "").upper()
    text = clean(" ".join([*(row.get("quote_summary") or []), *((news.get("headline") or "") for news in row.get("news") or [])]))
    lowered = text.lower()
    if ticker == "XLE":
        return "유가 급등에도 에너지 ETF가 얼마나 따라붙는지 확인하려는 섹터 프록시입니다. 개별 종목보다 에너지 업종 전체의 반응을 보는 용도입니다."
    if ticker in {"CVX", "XOM"}:
        if "venezuela" in lowered:
            return "베네수엘라 원유 사업 재검토와 유가 전쟁 프리미엄이 겹치며 대형 에너지주의 지정학 민감도를 확인할 수 있습니다."
        if "earnings" in lowered:
            return "Big Oil 실적 둔화 우려와 유가 상승이 서로 충돌하는 구간이라, 에너지주가 원유 가격을 얼마나 따라가는지 보는 후보입니다."
        return "유가 상승이 실제 대형 에너지 기업 이익 기대와 주가로 이어지는지 확인하려는 대표 종목입니다."
    if ticker == "GOOGL":
        return "Q1 실적 서프라이즈와 Google Cloud 63% 성장, 주가 급등이 함께 잡혀 AI 인프라 기대가 숫자로 확인된 사례입니다."
    if ticker == "MSFT":
        return "강한 실적과 가이던스에도 주가가 밀렸다는 뉴스가 있어, AI 기대가 이미 가격에 많이 반영됐는지 확인하는 후보입니다."
    if ticker == "META":
        return "빅테크 실적 시즌에서 Google과 대비되는 반응이 잡혀, AI 투자 부담을 시장이 어떻게 차별화하는지 보는 후보입니다."
    if ticker == "AMZN":
        return "AWS와 AI 투자 기대가 남아 있지만 빅테크 실적 반응이 엇갈려, 클라우드 성장 기대의 지속성을 확인하는 후보입니다."
    if ticker == "V":
        return "Visa 실적과 소비 지출 뉴스가 같이 잡혀, 소비 둔화 우려 속 결제 네트워크의 방어력을 보는 후보입니다."
    if ticker == "PI":
        return "반도체 주변부 실적 모멘텀이 AI 공급망 기대와 이어지는지 확인하는 후보입니다."
    if ticker == "UBER":
        return "플랫폼 수요와 AI 기반 예약·운영 자동화 기대를 같이 볼 수 있어, 소비 플랫폼 쪽 AI 적용 사례로 보는 후보입니다."
    if "oil" in lowered:
        return "유가 변동이 관련 업종 주가로 전이되는지 확인하는 후보입니다."
    if "ai" in lowered or "cloud" in lowered:
        return "AI 투자와 실적 기대가 실제 주가 반응으로 이어지는지 확인하는 후보입니다."
    return "오늘 시장의 테마가 개별 종목 차트와 뉴스에 실제로 반영되는지 확인하는 후보입니다."


def finviz_news_line(row: dict) -> dict:
    ticker = (row.get("ticker") or "").upper()
    keywords = {
        "XLE": ["xle", "energy", "oil", "gas", "sector"],
        "CVX": ["chevron", "cvx", "oil", "energy", "venezuela"],
        "XOM": ["exxon", "xom", "oil", "energy", "venezuela"],
        "GOOGL": ["alphabet", "google", "googl", "cloud"],
        "MSFT": ["microsoft", "msft", "azure"],
        "META": ["meta", "facebook"],
        "AMZN": ["amazon", "amzn", "aws"],
        "V": ["visa", "card", "spending", "consumer"],
        "PI": ["impinj", "pi"],
        "UBER": ["uber"],
    }.get(ticker, [ticker.lower()])

    def relevant(text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in keywords)

    for line in row.get("quote_summary") or []:
        text = clean(line)
        match = re.match(r"^(Today|Yesterday|[A-Z][a-z]{2}\s+\d{1,2}),?\s+(\d{1,2}:\d{2}\s*[AP]M)(.+)$", text)
        if match and relevant(match.group(3)):
            return {"time": f"{match.group(1)} {match.group(2)}", "headline": clean(match.group(3), 140), "url": row.get("url") or ""}
    for news in row.get("news") or []:
        headline = clean(news.get("headline"), 140)
        time_text = clean(news.get("time"))
        if headline and relevant(headline) and (time_text.lower().startswith("today") or re.match(r"^\d{1,2}:\d{2}\s*[AP]M$", time_text, re.I)):
            return {"time": clean(news.get("time")), "headline": headline, "url": news.get("url") or ""}
    return {}


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
    editorial_brief = load_json(processed / "editorial-brief.json")
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
    use_editorial = valid_editorial_brief(editorial_brief)
    display_storylines = editorial_brief.get("storylines", []) if use_editorial else filtered_storylines(radar_storylines or storylines, radar_by_id)
    today_axis = (
        clean_complete(editorial_brief.get("one_line_market_frame") or editorial_brief.get("daily_thesis"), 220)
        if use_editorial
        else infer_today_axis(display_storylines, radar_candidates)
    )
    market_map_summary = clean(editorial_brief.get("market_map_summary"), 220) if use_editorial else "지수, 히트맵, 금리, 유가, 달러, 원달러, 비트코인 순서로 시장 반응을 먼저 확인합니다."
    lead_story = display_storylines[0] if display_storylines else {}

    lines = [
        f"# {title}",
        "",
        f"최종 수정 일시: `{now} (KST)`",
        "",
        f"수집 구간: `{window} (KST)`",
        "",
        f"시장 데이터 기준: {code_meta(chart_rows()[0][2] if chart_rows() and chart_rows()[0][2] else '-')}",
        "",
    ]
    summary_bullets = editorial_summary_bullets(editorial_brief) if use_editorial else selection.get("dashboard_summary_bullets", [])
    render_compact_host_view(
        lines,
        editorial_brief if use_editorial else {"editorial_summary": "\n".join(summary_bullets)},
        display_storylines,
        radar_by_id,
        today_axis,
        market_map_summary,
        [story.get("one_liner") for story in radar_storylines[1:4]] if radar_storylines else summary_bullets,
    )
    lines.extend(["# PPT 제작 큐", ""])
    if use_editorial:
        render_ppt_asset_queue(lines, editorial_brief, target_date, radar_by_id)
    else:
        render_ppt_asset_queue(lines, {"editorial_summary": "\n".join(summary_bullets), "storylines": display_storylines}, target_date, radar_by_id)
    lines.extend(["", "## 말로만 처리할 자료", ""])
    if use_editorial:
        render_talk_only_queue(lines, editorial_brief, radar_by_id)
    else:
        lines.append("- editorial brief가 유효하지 않아 별도 talk-only 큐가 없습니다.")

    lines.extend(["", "# 자료 수집 상세", "", "## 추천 스토리라인", ""])
    for index, storyline in enumerate(display_storylines, start=1):
        if use_editorial:
            render_host_storyline(lines, index, storyline, radar_by_id)
        else:
            render_storyline(lines, index, storyline, radar_by_id, ledger)
    lines.extend(
        [
            "",
            "## 경제 일정/실적 일정",
            "",
            "- 경제 일정은 아래 `오늘의 경제 일정` 표/이미지에서 확인합니다.",
            "- 실적 일정과 특징주는 아래 `실적/특징주` 섹션에서 확인합니다.",
            "",
            "## 자료 수집",
            "",
            "## 1. 시장은 지금",
            "",
        ]
    )
    index_futures = screenshots_for(target_date, "finviz-index-futures-*.png")
    if index_futures:
        lines.extend(["### 주요 지수 흐름", "", screenshot_source_line(target_date, "finviz-index-futures", "[Finviz](https://finviz.com/)"), ""])
        for idx, index_future in enumerate(index_futures, start=1):
            label = "주요 지수 흐름" if idx == 1 else f"주요 지수 흐름 {idx}"
            lines.extend([notion_image(label, index_future), ""])
    sp500_heatmap = screenshot_for(target_date, "finviz-sp500-heatmap*.png")
    if sp500_heatmap:
        lines.extend(["### S&P500 히트맵", "", screenshot_source_line(target_date, "finviz-sp500-heatmap", "[Finviz](https://finviz.com/map.ashx?t=sec)"), "", notion_image("S&P500 히트맵", sp500_heatmap), ""])
    russell_heatmap = screenshot_for(target_date, "*russell*heatmap*.png", "*iwm*heatmap*.png")
    lines.extend(["### 러셀 2000 히트맵", ""])
    if russell_heatmap:
        lines.extend([screenshot_source_line(target_date, "finviz-russell-heatmap", "[Finviz](https://finviz.com/map?t=sec_rut)"), "", notion_image("러셀 2000 히트맵", russell_heatmap), ""])
    else:
        lines.append("- 수집 이미지 없음")
    for chart_id, chart_title, subtitle, source_name, source_url in chart_rows():
        png = EXPORTS_DIR / f"{chart_id}.png"
        if png.exists():
            heading = chart_heading(chart_title)
            lines.extend([f"### {heading}", ""])
            meta = f"출처: {link(source_name, source_url)}"
            if subtitle:
                meta += f" · {code_meta(subtitle)}"
            lines.extend([meta, "", notion_image(heading, png), ""])
        else:
            lines.append(f"- {chart_title} / 출처: {link(source_name, source_url)}")
    fear_greed = screenshot_for(target_date, "*fear*greed*.png", "*fear-greed*.png")
    if fear_greed:
        lines.extend(["", "### 공포탐욕지수", ""])
        lines.extend([screenshot_source_line(target_date, "cnn-fear-greed", "[CNN](https://edition.cnn.com/markets/fear-and-greed)"), "", notion_image("공포탐욕지수", fear_greed)])
    else:
        lines.extend(["", "### 공포탐욕지수", "", "- 이번 자동 실행에서는 이미지 수집 제외. 필요 시 CNN 캡처 루트 복구.", ""])

    lines.extend(["", "### 오늘의 경제 일정", ""])
    us_calendar_png = EXPORTS_DIR / "economic-calendar-us.png"
    global_calendar_png = EXPORTS_DIR / "economic-calendar-global.png"
    calendar_png = EXPORTS_DIR / "economic-calendar.png"
    if us_calendar_png.exists() or global_calendar_png.exists():
        lines.extend(["출처: [Trading Economics](https://ko.tradingeconomics.com/calendar) · Datawrapper 표", ""])
        if us_calendar_png.exists():
            lines.extend([notion_image("오늘의 미국 경제 일정", us_calendar_png), ""])
        if global_calendar_png.exists():
            lines.extend([notion_image("오늘의 글로벌 경제 일정", global_calendar_png), ""])
    elif calendar_png.exists():
        lines.extend(["출처: [Trading Economics](https://ko.tradingeconomics.com/calendar) · Datawrapper 표", "", notion_image("오늘의 경제 일정", calendar_png), ""])
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
            lines.append("- 오늘 표시할 주요 경제 일정 없음" if economic else "- 경제 일정 수집 상태 확인 필요")

    fedwatch_rows = fedwatch_probability_rows(target_date)
    if fedwatch_rows:
        lines.extend(["", "### FedWatch 금리 확률", ""])
        lines.append(screenshot_source_line(target_date, "cme-fedwatch", "[CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)"))
        lines.append("")
        headers = fedwatch_probability_headers(target_date, max(len(row) for row in fedwatch_rows))
        heat_headers, heat_rows = trim_fedwatch_matrix(headers, fedwatch_rows)
        split_heatmaps = [
            (EXPORTS_DIR / "fedwatch-conditional-probabilities-short-term.png", "FedWatch 단기 금리확률 히트맵"),
            (EXPORTS_DIR / "fedwatch-conditional-probabilities-long-term.png", "FedWatch 장기 금리확률 히트맵"),
        ]
        rendered_split = [item for item in split_heatmaps if item[0].exists()]
        if rendered_split:
            for heatmap_path, alt in rendered_split:
                lines.extend([notion_image(alt, heatmap_path), ""])
        else:
            datawrapper_heatmap = EXPORTS_DIR / "fedwatch-conditional-probabilities.png"
            heatmap = str(datawrapper_heatmap) if datawrapper_heatmap.exists() else render_fedwatch_heatmap(target_date, heat_headers, heat_rows)
            if heatmap:
                lines.extend([notion_image("FedWatch 조건부 금리확률 히트맵", heatmap), ""])

    fed_screens = [] if fedwatch_rows else screenshots_for(target_date, "*fedwatch*.png", "*cme-fedwatch*.png", "*polymarket*.png")
    if fed_screens:
        lines.extend(["", "### FedWatch/Polymarket 확률", ""])
        for screen in fed_screens[:3]:
            name = Path(screen).name.lower()
            if "fedwatch" in name:
                source_line = screenshot_source_line(target_date, "cme-fedwatch", "[CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)")
                label = "FedWatch 확률표"
            elif "polymarket" in name:
                source_line = screenshot_source_line(target_date, "polymarket-fed-rates", "[Polymarket](https://polymarket.com/)")
                label = "Polymarket 확률 자료"
            else:
                source_line = "출처: 시장 확률 자료"
                label = "시장 확률 자료"
            lines.extend([source_line, "", notion_image(label, screen), ""])

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
    show_fed_package = False
    misc_section_number = 2
    feature_section_number = misc_section_number + 1
    if show_fed_package:
        lines.extend(["", "## 2. Fed/FOMC package", ""])
        lines.append("> 경제 일정 표와 별도로, 시장이 금리 경로를 어떻게 확률로 가격에 넣는지 보는 블록입니다.")
        lines.append("")
        if fed_screens:
            for screen in fed_screens[:3]:
                label = "FedWatch/Polymarket 확률 자료"
                lines.extend([notion_image(label, screen), ""])
        else:
            lines.append("- FedWatch/Polymarket 캡처는 이번 실행에서 확보되지 않았습니다. 금리인하 베팅이 메인 이슈면 수동 확인 필요.")
            lines.append("")
        for index, row in enumerate(fed_rows, start=1):
            next_title = compact_radar_title(fed_rows[index]) if index < len(fed_rows) else ""
            render_radar_card(lines, row, index, next_title)

    lines.extend(["", f"## {misc_section_number}. 보조 꼭지 후보", ""])
    radar_misc_rows = []
    seen_radar_ids = set()
    seen_radar_titles = set()
    misc_source_storylines = radar_storylines
    if use_editorial:
        misc_source_storylines = [
            {
                "selected_item_ids": [
                    item.get("item_id")
                    for item in (storyline.get("evidence_to_use") or [])
                    if item.get("item_id")
                ]
            }
            for storyline in display_storylines
        ]
    for storyline in misc_source_storylines:
        for item_id in storyline.get("selected_item_ids", []):
            row = radar_by_id.get(item_id)
            if row and not row.get("visual_local_path") and candidate_by_id.get(item_id):
                images = candidate_by_id[item_id].get("image_refs") or []
                local = next((image.get("local_path") for image in images if image.get("local_path")), "")
                if local:
                    row = {**row, "visual_local_path": local}
            if row and is_fed_material(row):
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

    lines.extend([f"## {feature_section_number}. 실적/특징주", ""])
    earnings_image = screenshot_for(target_date, "*earnings-calendar*.jpg", "*earnings-calendar*.png")
    if earnings_image:
        earnings_captured = capture_meta(target_date, "earnings-calendar-x")
        if earnings_captured.endswith("`-`"):
            file_time = captured_from_file(earnings_image)
            earnings_captured = f"수집 시점: `{file_time}`" if file_time else earnings_captured
        lines.extend(["### 이번 주 실적 캘린더", "", "출처: [Earnings Whispers](https://x.com/eWhispers) · " + earnings_captured, "", notion_image("이번 주 실적 캘린더", earnings_image), ""])
    if not earnings_image:
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
        lines.append("")
        for row in feature_rows[:5]:
            render_feature_stock(lines, row)
    lines.extend(["", "## 방송 후 회고 입력용 메모", ""])
    if use_editorial:
        watchpoints = editorial_brief.get("retrospective_watchpoints") or []
        if watchpoints:
            for item in watchpoints[:8]:
                lines.append(f"- {public_editorial_text(item, 160)}")
        else:
            lines.append("- 리드 스토리라인이 실제 첫 꼭지로 쓰였는지 기록.")
            lines.append("- PPT 캡처 후보 중 실제 장표화된 자료와 말로만 처리된 자료를 구분.")
            lines.append("- 대시보드에는 있었지만 쓰이지 않은 자료의 이유를 drop_code 후보로 기록.")
    else:
        lines.append("- editorial brief fallback 또는 누락 상태입니다. 실제 방송 사용 여부를 수동 기록하세요.")
    if use_editorial:
        lines.extend([""])
        render_audit_log(lines, editorial_brief, radar_by_id, target_date)
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
