from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_broadcast_retrospective as retrospective


class RetrospectiveContractTest(unittest.TestCase):
    def test_retrospective_schema_carries_asset_labels(self) -> None:
        self.assertIn("used_as_lead", retrospective.RETROSPECTIVE_LABELS)
        self.assertIn("used_as_slide", retrospective.RETROSPECTIVE_LABELS)
        self.assertIn("false_positive_visual_only", retrospective.RETROSPECTIVE_LABELS)
        required = set(retrospective.RETROSPECTIVE_SCHEMA["required"])
        self.assertLessEqual({"asset_usage_labels", "ppt_outline_comparison"}, required)


if __name__ == "__main__":
    unittest.main()
