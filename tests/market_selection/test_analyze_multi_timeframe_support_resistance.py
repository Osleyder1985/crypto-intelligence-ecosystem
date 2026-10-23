import unittest
from decimal import Decimal

from scripts.market_selection.analyze_multi_timeframe_support_resistance import (
    INPUT_SCHEMA, analyze_multi_timeframe_support_resistance, _within_price_tolerance,
)
from test_analyze_support_resistance import artifact, candle


class MultiTimeframeSupportResistanceTests(unittest.TestCase):
    def test_price_tolerance_is_symmetric_around_midpoint(self):
        tolerance = Decimal("99.5")
        self.assertFalse(_within_price_tolerance(Decimal("100"), Decimal("101"), tolerance))
        self.assertFalse(_within_price_tolerance(Decimal("101"), Decimal("100"), tolerance))
        self.assertTrue(_within_price_tolerance(Decimal("100"), Decimal("101"), Decimal("100")))

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
        self.assertTrue(any("not computed" in item for item in result["limitations"]))
        self.assertTrue(all("zones" in item and "events" in item for item in result["timeframes"]))

    def test_rejects_mixed_symbols(self):
        with self.assertRaisesRegex(ValueError, "same exchange, market type, and native symbol"):
            self.analyze([self.fixture("1h"), self.fixture("4h", symbol="ETHUSDT")])

    def test_rejects_mixed_exchanges(self):
        with self.assertRaisesRegex(ValueError, "same exchange, market type, and native symbol"):
            self.analyze([self.fixture("1h"), self.fixture("4h", exchange="other")])

    def test_rejects_mixed_quote_assets(self):
        primary = self.fixture("1h")
        secondary = self.fixture("4h")
        secondary["market"]["quote_asset"] = "USDC"
        with self.assertRaisesRegex(ValueError, "same quote asset"):
            self.analyze([primary, secondary])

    def test_allows_missing_quote_asset_metadata(self):
        primary = self.fixture("1h")
        secondary = self.fixture("4h")
        secondary["market"].pop("quote_asset", None)
        self.assertEqual(self.analyze([primary, secondary])["timeframe_count"], 2)

    def test_rejects_duplicate_intervals(self):
        with self.assertRaisesRegex(ValueError, "duplicate timeframe"):
            self.analyze([self.fixture("1h"), self.fixture("1h")])

    def test_explicit_tolerance_computes_cross_timeframe_confluence_groups(self):
        result = analyze_multi_timeframe_support_resistance(
            [self.fixture("1h"), self.fixture("4h")],
            pivot_left=1, pivot_right=1, tolerance_bps=100,
            confluence_tolerance_bps=25,
        )
        self.assertEqual(result["cross_timeframe_confluence"], "COMPUTED_BY_EXPLICIT_PRICE_TOLERANCE")
        self.assertTrue(any("computed only from same-kind zones" in item for item in result["limitations"]))
        self.assertFalse(any("cross-timeframe confluence is not computed" in item for item in result["limitations"]))
        self.assertEqual(result["confluence_tolerance_bps"], 25)
        self.assertTrue(result["confluence_groups"])
        self.assertTrue(all(group["timeframe_count"] >= 2 for group in result["confluence_groups"]))
        self.assertTrue(all(len({ref["interval"] for ref in group["zone_refs"]}) == group["timeframe_count"] for group in result["confluence_groups"]))

    def test_confluence_remains_uncomputed_without_explicit_tolerance(self):
        result = self.analyze([self.fixture("1h"), self.fixture("4h")])
        self.assertEqual(result["cross_timeframe_confluence"], "NOT_COMPUTED")
        self.assertEqual(result["confluence_groups"], [])

    def test_rejects_invalid_confluence_tolerance(self):
        with self.assertRaisesRegex(ValueError, "confluence_tolerance_bps"):
            analyze_multi_timeframe_support_resistance(
                [self.fixture("1h"), self.fixture("4h")],
                pivot_left=1, pivot_right=1, tolerance_bps=100,
                confluence_tolerance_bps=float("nan"),
            )

    def test_rejects_empty_inputs(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            self.analyze([])


if __name__ == "__main__":
    unittest.main()
