"""Source trust and usage policy for Autopark evidence.

This module is intentionally rule-based. It does not decide story order or
selection by itself; it only annotates evidence so the downstream LLM stages
know how strongly a source can support a public broadcast claim.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class SourcePolicy:
    tier: str
    authority: str
    use_role: str
    auth_profile: str
    publish_policy: str
    llm_policy: str
    lead_allowed: bool
    notes: str


DEFAULT_POLICY = SourcePolicy(
    tier="fallback",
    authority="low",
    use_role="backup",
    auth_profile="",
    publish_policy="title_source_summary_only",
    llm_policy="sanitized_summary_only",
    lead_allowed=False,
    notes="Use only as backup unless paired with stronger local evidence.",
)

POLICIES: tuple[tuple[tuple[str, ...], SourcePolicy], ...] = (
    (
        ("reuters.com", "reuters"),
        SourcePolicy(
            tier="premium",
            authority="high",
            use_role="fact_anchor",
            auth_profile="syukafriends",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=True,
            notes="Premium fact anchor. Do not store or transmit full article bodies.",
        ),
    ),
    (
        ("bloomberg.com", "bloomberg"),
        SourcePolicy(
            tier="premium",
            authority="high",
            use_role="analysis_anchor",
            auth_profile="syukafriends",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=True,
            notes="Premium analysis/context anchor. Use sanitized summary, not full article text.",
        ),
    ),
    (
        ("wsj.com", "wall street journal", "the wall street journal", "wsj"),
        SourcePolicy(
            tier="premium",
            authority="high",
            use_role="analysis_anchor",
            auth_profile="syukafriends",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=True,
            notes="Premium context anchor. Use headline and sanitized summary; avoid long quotation.",
        ),
    ),
    (
        ("factset",),
        SourcePolicy(
            tier="primary",
            authority="high",
            use_role="analysis_anchor",
            auth_profile="",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=True,
            notes="High-quality earnings context source.",
        ),
    ),
    (
        ("cmegroup", "fedwatch", "tradingeconomics", "yahoo finance", "coingecko", "finviz", "datawrapper"),
        SourcePolicy(
            tier="market_data",
            authority="high",
            use_role="market_reaction",
            auth_profile="",
            publish_policy="chart_metadata_only",
            llm_policy="metadata_and_sanitized_summary_only",
            lead_allowed=False,
            notes="Market data confirms reaction; do not use alone for causal claims.",
        ),
    ),
    (
        ("cnbc", "marketwatch", "tradingview", "investing.com"),
        SourcePolicy(
            tier="primary",
            authority="medium",
            use_role="speed_anchor",
            auth_profile="",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=True,
            notes="Fast news/context source. Prefer confirmation from premium/data evidence.",
        ),
    ),
    (
        ("x.com", "twitter.com", "reddit", "kobeissi", "wallstengine", "wall st engine"),
        SourcePolicy(
            tier="social",
            authority="low",
            use_role="sentiment_probe",
            auth_profile="x",
            publish_policy="title_source_summary_link_only",
            llm_policy="sanitized_summary_only",
            lead_allowed=False,
            notes="Sentiment or market-attention signal only; never standalone fact evidence.",
        ),
    ),
)

AUTHORITY_BONUS = {"high": 4, "medium": 2, "low": 0}
TIER_BONUS = {"premium": 4, "primary": 2, "market_data": 2, "social": 0, "fallback": -1}


def source_blob(item: dict) -> str:
    fields = [
        item.get("source"),
        item.get("source_name"),
        item.get("source_id"),
        item.get("name"),
        item.get("type"),
        item.get("category"),
        item.get("url"),
        item.get("title"),
        item.get("headline"),
    ]
    return " ".join(str(value or "") for value in fields).lower()


def infer_source_policy(item: dict) -> dict:
    blob = source_blob(item)
    if "x.com" in blob or "twitter.com" in blob or "reddit" in blob:
        for hints, policy in POLICIES:
            if "x.com" in hints:
                return asdict(policy)
    for hints, policy in POLICIES:
        if any(hint in blob for hint in hints):
            return asdict(policy)
    return asdict(DEFAULT_POLICY)


def apply_source_policy(item: dict) -> dict:
    policy = infer_source_policy(item)
    enriched = dict(item)
    field_map = {
        "tier": "source_tier",
        "authority": "source_authority",
        "use_role": "source_use_role",
        "auth_profile": "source_auth_profile",
        "publish_policy": "source_publish_policy",
        "llm_policy": "source_llm_policy",
        "lead_allowed": "source_lead_allowed",
        "notes": "source_policy_notes",
    }
    for key, value in policy.items():
        enriched.setdefault(field_map[key], value)
    if not enriched.get("source_policy"):
        enriched["source_policy"] = policy
    return enriched


def policy_score_bonus(item: dict) -> int:
    policy = item.get("source_policy") if isinstance(item.get("source_policy"), dict) else infer_source_policy(item)
    return AUTHORITY_BONUS.get(str(policy.get("authority") or ""), 0) + TIER_BONUS.get(str(policy.get("tier") or ""), 0)
