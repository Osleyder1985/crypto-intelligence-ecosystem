import unittest

from scripts.market_selection.analyze_multi_timeframe_support_resistance import (
    INPUT_SCHEMA, analyze_multi_timeframe_support_resistance,
)
from test_analyze_support_resistance import artifact, candle


class MultiTimeframeSupportResistanceTests(unittest.TestCase):
    def fixture(self, interval="1h", symbol="BTCUSDT", exchange="binance", rows=None):
        value = artifact(rows or [
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
        ])
        value["market"]["interval"] = interval
        duration_ms = {"1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}.get(interval)
        if duration_ms is None:
            raise ValueError("unsupported test interval")
        for index, row in enumerate(value["candles"]):
            row["open_time_ms"] = index * duration_ms
            row["close_time_ms"] = (index + 1) * duration_ms - 1
        value["market"]["symbol_native"] = symbol
        value["market"]["exchange"] = exchange
        return value

    def analyze(self, artifacts):
        return analyze_multi_timeframe_support_resistance(
            artifacts, pivot_left=1, pivot_right=1, tolerance_bps=100,
        )

    def test_preserves_independent_timeframes_without_claiming_confluence(self):
        result = self.analyze([self.fixture("1h"), self.fixture("4h")])
        self.assertEqual(result["schema_version"], "multi-timeframe-support-resistance-events-v1")
        self.assertEqual(result["timeframe_count"], 2)
        self.assertEqual([item["interval"] for item in result["timeframes"]], ["1h", "4h"])
        self.assertEqual(result["cross_timeframe_confluence"], "NOT_COMPUTED")
        self.assertTrue(all("zones" in item and "events" in item for item in result["timeframes"]))

    def test_rejects_mixed_symbols(self):
        with self.assertRaisesRegex(ValueError, "same exchange, market type, and native symbol"):
            self.analyze([self.fixture("1h"), self.fixture("4h", symbol="ETHUSDT")])

    def test_rejects_mixed_exchanges(self):
        with self.assertRaisesRegex(ValueError, "same exchange, market type, and native symbol"):
            self.analyze([self.fixture("1h"), self.fixture("4h", exchange="other")])

    def test_rejects_duplicate_intervals(self):
        with self.assertRaisesRegex(ValueError, "duplicate timeframe"):
            self.analyze([self.fixture("1h"), self.fixture("1h")])

    def test_rejects_empty_inputs(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            self.analyze([])


if __name__ == "__main__":
    unittest.main()
