"""Small editorial-policy helpers for Autopark pipeline enrichment.

The YAML manifests in ``projects/autopark/config`` are the human-readable
policy source. These helpers keep the daily automation dependency-free and
conservative when adding optional broadcast-editor fields.
"""

from __future__ import annotations

import re

from source_policy import apply_source_policy, infer_source_policy, policy_score_bonus


SOCIAL_HINTS = ("x.com", "twitter.com", "reddit.com", "reddit", "x_social")
VISUAL_HINTS = ("finviz", "heatmap", "chart", "screenshot", "visual_card", "datawrapper")
OFFICIAL_HINTS = ("federalreserve", "sec.gov", "treasury.gov", "bls.gov", "bea.gov", "whitehouse.gov")
COMPANY_HINTS = ("investor.", "ir.", "press release", "earnings release")
FACT_HINTS = ("reuters", "apnews", "associated press")
ANALYSIS_HINTS = ("bloomberg", "wsj", "financial times", "ft.com", "factset", "advisorperspectives", "advisor perspectives")
SPEED_HINTS = ("cnbc", "marketwatch", "yahoo", "investing.com")
DATA_HINTS = ("tradingeconomics", "cmegroup", "fedwatch", "coingecko", "fred", "economic-calendar", "isabelnet")


def _blob(*values: object) -> str:
    return " ".join(str(value or "") for value in values).lower()


def infer_source_role(material: dict) -> str:
    policy = infer_source_policy(material)
    if policy.get("use_role") in {"fact_anchor", "analysis_anchor", "market_reaction", "sentiment_probe", "speed_anchor"}:
        return str(policy["use_role"])
    blob = _blob(material.get("source"), material.get("source_name"), material.get("source_id"), material.get("type"), material.get("url"), material.get("title"))
    if any(hint in blob for hint in SOCIAL_HINTS):
        return "sentiment_probe"
    if any(hint in blob for hint in OFFICIAL_HINTS):
        return "official_policy"
    if any(hint in blob for hint in COMPANY_HINTS):
        return "company_primary"
    if any(hint in blob for hint in FACT_HINTS):
        return "fact_anchor"
    if any(hint in blob for hint in DATA_HINTS):
        return "data_anchor"
    if any(hint in blob for hint in VISUAL_HINTS) or material.get("visual_local_path"):
        return "market_reaction"
    if any(hint in blob for hint in ANALYSIS_HINTS):
        return "analysis_anchor"
    if any(hint in blob for hint in SPEED_HINTS):
        return "speed_anchor"
    return "weak_or_unverified"


def infer_evidence_role(source_role: str, material: dict) -> str:
    if source_role == "sentiment_probe":
        return "sentiment"
    if source_role in {"market_reaction", "visual_anchor"}:
        return "visual" if material.get("visual_local_path") else "market_reaction"
    if source_role in {"data_anchor", "official_policy", "company_primary"}:
        return "data" if source_role == "data_anchor" else "fact"
    if source_role == "analysis_anchor":
        return "analysis"
    if source_role == "fact_anchor":
        return "fact"
    if source_role == "speed_anchor":
        return "analysis"
    return "context"


def infer_asset_type(material: dict) -> str:
    blob = _blob(material.get("source"), material.get("source_id"), material.get("title"), material.get("url"), material.get("type"))
    if "heatmap" in blob and ("sp500" in blob or "s&p" in blob or "russell" in blob):
        return "sector_heatmap"
    if "fedwatch" in blob or "polymarket" in blob:
        return "fedwatch_chart"
    if "fomc" in blob or "federal reserve" in blob:
        return "fomc_statement"
    if "earnings calendar" in blob or "earnings-whispers" in blob:
        return "earnings_calendar"
    if "earnings" in blob:
        return "earnings_card"
    if "us10y" in blob or "treasury" in blob or "yield" in blob:
        return "rates_chart"
    if "wti" in blob or "brent" in blob or "oil" in blob:
        return "oil_chart"
    if "dxy" in blob or "dollar" in blob or "usd-krw" in blob or "fx" in blob:
        return "fx_chart"
    if "bitcoin" in blob or "btc" in blob or "crypto" in blob:
        return "crypto_chart"
    if "finviz-index" in blob or "index futures" in blob:
        return "index_chart"
    if material.get("visual_local_path") and any(hint in blob for hint in SOCIAL_HINTS):
        return "x_post_screenshot"
    if material.get("visual_local_path"):
        return "article_screenshot"
    if material.get("tickers"):
        return "company_chart"
    return "article_screenshot"


def infer_signal_or_noise(themes: dict | list, source_role: str, score: int | float) -> str:
    theme_count = len(themes or [])
    if source_role in {"weak_or_unverified", "sentiment_probe"} and theme_count <= 1:
        return "noise"
    if score >= 14 or theme_count >= 2:
        return "signal"
    return "watch"


def infer_signal_axes(theme_keys: list[str]) -> list[str]:
    mapping = {
        "ai_infra": "ai_infra_expectation",
        "market_positioning": "risk_appetite_positioning",
        "rates_macro": "rates_policy_path",
        "energy_geopolitics": "oil_geopolitical_risk",
        "earnings_signal": "earnings_expectation_gap",
        "side_dish": "attention_light_segment",
    }
    return [mapping.get(theme, theme) for theme in theme_keys]


def infer_expectation_gap(theme_keys: list[str], material: dict) -> str:
    text = _blob(material.get("title"), material.get("summary"))
    if "earnings_signal" in theme_keys or any(token in text for token in ("earnings", "eps", "revenue", "guidance", "forecast", "예상", "가이던스")):
        return "required"
    if "rates_macro" in theme_keys or any(token in text for token in ("fed", "fomc", "inflation", "jobs", "pce")):
        return "check_market_pricing"
    return "not_primary"


def infer_prepricing_risk(theme_keys: list[str], material: dict) -> str:
    text = _blob(material.get("title"), material.get("summary"))
    if any(token in text for token in ("already priced", "priced in", "expectation", "guidance", "rally", "surge", "record high")):
        return "check"
    if "market_positioning" in theme_keys or "earnings_signal" in theme_keys:
        return "possible"
    return "low"


def infer_market_reaction(source_role: str, material: dict) -> str:
    text = _blob(material.get("title"), material.get("summary"), material.get("source_id"))
    if source_role in {"market_reaction", "data_anchor"} or material.get("visual_local_path"):
        return "visible_market_reaction"
    if any(token in text for token in ("futures", "yield", "oil", "dollar", "bitcoin", "stock", "shares", "market")):
        return "mentions_market_reaction"
    return "not_shown"


def infer_first_5min_fit(theme_keys: list[str], source_role: str) -> str:
    if "side_dish" in theme_keys and len(theme_keys) == 1:
        return "low"
    if source_role in {"fact_anchor", "data_anchor", "market_reaction", "analysis_anchor"}:
        return "high"
    return "medium"


def infer_korea_open_relevance(theme_keys: list[str], material: dict) -> str:
    text = _blob(material.get("title"), material.get("summary"))
    if any(token in text for token in ("korea", "south korea", "won", "usd/krw", "semiconductor", "asia", "japan", "china")):
        return "high"
    if {"rates_macro", "energy_geopolitics", "ai_infra"} & set(theme_keys):
        return "medium"
    return "low"


def infer_drop_risk(source_role: str, evidence_role: str, signal_or_noise: str) -> str:
    if source_role == "sentiment_probe":
        return "sentiment_only_not_fact"
    if evidence_role in {"visual", "market_reaction"}:
        return "visual_only_not_causality"
    if signal_or_noise == "noise":
        return "weak_or_unverified"
    return ""


def infer_talk_vs_slide(material: dict, asset_type: str, evidence_role: str) -> str:
    if material.get("visual_local_path") or asset_type in {"index_chart", "sector_heatmap", "rates_chart", "oil_chart", "fx_chart", "crypto_chart", "fedwatch_chart", "earnings_calendar", "company_chart"}:
        return "slide"
    if evidence_role == "sentiment":
        return "talk_only"
    return "talk_or_slide"


def enrich_candidate_row(material: dict, row: dict, themes: dict[str, list[str]]) -> dict:
    material = apply_source_policy(material)
    source_role = infer_source_role(material)
    evidence_role = infer_evidence_role(source_role, material)
    theme_keys = sorted(themes)
    asset_type = infer_asset_type(material)
    signal_or_noise = infer_signal_or_noise(themes, source_role, row.get("score") or 0)
    talk_vs_slide = infer_talk_vs_slide(material, asset_type, evidence_role)
    item_id = str(row.get("id") or material.get("id") or material.get("url") or material.get("title") or "")
    return {
        "item_id": item_id,
        "source_role": source_role,
        "evidence_role": evidence_role,
        "topic_cluster": theme_keys[0] if theme_keys else "general",
        "asset_type": asset_type,
        "market_reaction": infer_market_reaction(source_role, material),
        "related_assets": [row.get("visual_local_path")] if row.get("visual_local_path") else [],
        "signal_or_noise": signal_or_noise,
        "signal_axes": infer_signal_axes(theme_keys),
        "expectation_gap": infer_expectation_gap(theme_keys, material),
        "prepricing_risk": infer_prepricing_risk(theme_keys, material),
        "korea_open_relevance": infer_korea_open_relevance(theme_keys, material),
        "first_5min_fit": infer_first_5min_fit(theme_keys, source_role),
        "ppt_asset_candidate": talk_vs_slide in {"slide", "talk_or_slide"},
        "talk_vs_slide": talk_vs_slide,
        "drop_risk": infer_drop_risk(source_role, evidence_role, signal_or_noise),
        "source_tier": material.get("source_tier") or "",
        "source_authority": material.get("source_authority") or "",
        "source_use_role": material.get("source_use_role") or "",
        "source_publish_policy": material.get("source_publish_policy") or "",
        "source_llm_policy": material.get("source_llm_policy") or "",
        "source_lead_allowed": bool(material.get("source_lead_allowed")),
        "source_policy_notes": material.get("source_policy_notes") or "",
        "source_policy_bonus": policy_score_bonus(material),
    }


def ppt_asset_from_row(row: dict, storyline_id: str, priority: int) -> dict:
    return {
        "asset_id": f"{storyline_id}:{row.get('item_id') or row.get('id')}",
        "source": row.get("source") or "",
        "source_role": row.get("source_role") or "weak_or_unverified",
        "visual_asset_role": row.get("asset_type") or "article_screenshot",
        "storyline_id": storyline_id,
        "slide_priority": priority,
        "use_as_slide": row.get("talk_vs_slide") in {"slide", "talk_or_slide"},
        "use_as_talk_only": row.get("talk_vs_slide") == "talk_only",
        "caption": row.get("title") or "",
        "why_this_visual": row.get("radar_question") or row.get("summary") or "",
        "risks_or_caveats": row.get("drop_risk") or "",
    }


def enrich_storyline(storyline: dict, rows: list[dict], rank: int | None = None) -> dict:
    storyline_id = storyline.get("storyline_id") or f"storyline-{rank or 0}"
    roles = {row.get("evidence_role") for row in rows}
    signal_values = [row.get("signal_or_noise") for row in rows]
    slide_assets = [row for row in rows if row.get("ppt_asset_candidate")]
    use_items = [
        {
            "item_id": row.get("item_id") or row.get("id") or "",
            "evidence_id": row.get("item_id") or row.get("id") or "",
            "title": row.get("title") or "",
            "source_role": row.get("source_role") or "weak_or_unverified",
            "evidence_role": row.get("evidence_role") or "context",
            "reason": row.get("radar_question") or row.get("summary") or "",
        }
        for row in rows
    ]
    drop_items = [
        {
            "item_id": row.get("item_id") or row.get("id") or "",
            "evidence_id": row.get("item_id") or row.get("id") or "",
            "title": row.get("title") or "",
            "source_role": row.get("source_role") or "weak_or_unverified",
            "evidence_role": row.get("evidence_role") or "context",
            "drop_code": row.get("drop_risk") or "support_only",
            "reason": row.get("drop_risk") or "메인 주장보다는 보조 자료로만 적합합니다.",
        }
        for row in rows
        if row.get("drop_risk") or row.get("signal_or_noise") == "noise"
    ]
    storyline.update(
        {
            "storyline_id": storyline_id,
            "rank": rank or 0,
            "lead_candidate_reason": storyline.get("why_selected") or "",
            "signal_or_noise": "signal" if "signal" in signal_values else "watch",
            "market_causality": "needs_fact_or_analysis_pairing" if roles <= {"visual", "market_reaction", "sentiment"} else "supported_by_mixed_evidence",
            "expectation_gap": "required" if any(row.get("expectation_gap") == "required" for row in rows) else "check_if_relevant",
            "prepricing_risk": "check" if any(row.get("prepricing_risk") in {"check", "possible"} for row in rows) else "low",
            "first_5min_fit": "high" if any(row.get("first_5min_fit") == "high" for row in rows) else "medium",
            "korea_open_relevance": "high" if any(row.get("korea_open_relevance") == "high" for row in rows) else "medium",
            "ppt_asset_queue": [ppt_asset_from_row(row, storyline_id, idx) for idx, row in enumerate(slide_assets[:4], start=1)],
            "evidence_to_use": use_items,
            "evidence_to_drop": drop_items,
            "drop_code": ",".join(sorted({item["drop_code"] for item in drop_items})) if drop_items else "",
            "talk_vs_slide": "slide_supported" if slide_assets else "talk_only",
        }
    )
    return storyline
