from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import fetch_market_chart_data as charts  # noqa: E402
import fetch_economic_calendar as economic_calendar  # noqa: E402


class MarketChartTimingContractTest(unittest.TestCase):
    def test_yahoo_daily_epoch_uses_exchange_timezone(self) -> None:
        # 2026-05-01 20:00 UTC is still the May 1 US session in New York.
        epoch = 1777665600
        self.assertEqual("2026-05-01", charts.date_from_epoch(epoch, "America/New_York"))

    def test_coingecko_subtitle_marks_utc_daily_basis(self) -> None:
        coverage = charts.chart_coverage_label(
            {"id": "bitcoin"},
            "coingecko",
            [{"date": "2026-05-04", "BTC/USD": 78174.06}],
            1777854600,
            {"symbols": [{"last_valid_time": 1777852800}]},
        )
        self.assertEqual("26.05.04 09:00 KST", coverage["coverage_label"])

    def test_treasury_chart_uses_single_kst_basis_timestamp(self) -> None:
        coverage = charts.chart_coverage_label(
            {"id": "us10y"},
            "yahoo_finance",
            [{"date": "2026-05-01", "US10Y": 4.378}],
            1777854600,
            {"symbols": [{"last_valid_time": 1777665900}]},
        )
        self.assertEqual("26.05.02 05:05 KST", coverage["basis_label"])
        self.assertNotIn("확인", coverage["coverage_label"])

    def test_economic_calendar_subtitle_keeps_rules_without_check_time(self) -> None:
        subtitle = economic_calendar.economic_calendar_subtitle("2026-05-04", "26.05.04 05:36", "us")
        self.assertIn("26.05.04 KST 일정 기준", subtitle)
        self.assertIn("미국 2", subtitle)
        self.assertNotIn("확인", subtitle)
        self.assertNotIn("수집", subtitle)


if __name__ == "__main__":
    unittest.main()
