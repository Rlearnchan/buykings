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
        )
        self.assertIn("UTC 일봉 26.05.04 00:00 기준", coverage["coverage_label"])
        self.assertIn("확인", coverage["coverage_label"])

    def test_oil_charts_explain_settlement_window_without_calling_it_collection(self) -> None:
        coverage = charts.chart_coverage_label(
            {"id": "crude-oil-wti"},
            "yahoo_finance",
            [{"date": "2026-05-01", "WTI": 63.02}],
            1777854600,
        )
        self.assertIn("WTI 일봉 26.05.01 기준", coverage["basis_label"])
        self.assertIn("14:28-14:30 ET", coverage["basis_label"])
        self.assertNotIn("수집", coverage["coverage_label"])

    def test_economic_calendar_subtitle_separates_schedule_date_from_check_time(self) -> None:
        subtitle = economic_calendar.economic_calendar_subtitle("2026-05-04", "26.05.04 05:36", "us")
        self.assertIn("KST 일정 26.05.04 기준", subtitle)
        self.assertIn("확인 26.05.04 05:36 KST", subtitle)
        self.assertNotIn("수집", subtitle)


if __name__ == "__main__":
    unittest.main()
