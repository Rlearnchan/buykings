from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_evidence_microcopy as evidence_microcopy
import build_market_focus_brief as market_focus
import build_editorial_brief as editorial
import source_policy


class SourcePolicyContractTest(unittest.TestCase):
    def test_premium_sources_use_syukafriends_and_sanitized_policy(self) -> None:
        for source, url in [
            ("Reuters", "https://www.reuters.com/markets/"),
            ("Bloomberg", "https://www.bloomberg.com/news/articles/example"),
            ("The Wall Street Journal", "https://www.wsj.com/articles/example"),
        ]:
            policy = source_policy.infer_source_policy({"source": source, "url": url})
            self.assertEqual("premium", policy["tier"])
            self.assertEqual("high", policy["authority"])
            self.assertEqual("syukafriends", policy["auth_profile"])
            self.assertEqual("sanitized_summary_only", policy["llm_policy"])
            self.assertTrue(policy["lead_allowed"])

    def test_social_and_market_data_are_not_standalone_fact_anchors(self) -> None:
        social = source_policy.infer_source_policy({"source": "X", "url": "https://x.com/example"})
        x_reuters = source_policy.infer_source_policy({"source": "Reuters", "url": "https://x.com/Reuters"})
        market_data = source_policy.infer_source_policy({"source": "CME FedWatch", "url": "https://www.cmegroup.com/"})

        self.assertEqual("social", social["tier"])
        self.assertEqual("sentiment_probe", social["use_role"])
        self.assertFalse(social["lead_allowed"])
        self.assertEqual("social", x_reuters["tier"])
        self.assertEqual("market_data", market_data["tier"])
        self.assertEqual("market_reaction", market_data["use_role"])
        self.assertFalse(market_data["lead_allowed"])

    def test_evidence_microcopy_prompt_carries_source_policy(self) -> None:
        item = {
            "id": "r1",
            "title": "Fed officials discuss inflation risk",
            "source": "Reuters",
            "url": "https://www.reuters.com/markets/",
            "summary": "A sanitized local summary.",
        }
        compact = evidence_microcopy.compact_item_for_prompt(item)

        self.assertEqual("premium", compact["source_policy"]["tier"])
        self.assertEqual("fact_anchor", compact["source_policy"]["use_role"])
        self.assertEqual("sanitized_summary_only", compact["source_policy"]["llm_policy"])

    def test_market_focus_and_editorial_candidates_carry_source_policy(self) -> None:
        item = {
            "id": "b1",
            "item_id": "b1",
            "title": "Bloomberg analysis on market positioning",
            "source": "Bloomberg",
            "url": "https://www.bloomberg.com/news/articles/example",
            "summary": "Sanitized summary only.",
            "theme_keys": ["market_positioning"],
        }

        focus_candidate = market_focus.compact_candidate(item)
        editorial_candidate = editorial.compact_candidate(item, include_url=False, include_paths=False)

        self.assertEqual("premium", focus_candidate["source_tier"])
        self.assertEqual("analysis_anchor", focus_candidate["source_use_role"])
        self.assertTrue(focus_candidate["source_lead_allowed"])
        self.assertEqual("premium", editorial_candidate["source_tier"])
        self.assertEqual("analysis_anchor", editorial_candidate["source_use_role"])
        self.assertTrue(editorial_candidate["source_lead_allowed"])


if __name__ == "__main__":
    unittest.main()
