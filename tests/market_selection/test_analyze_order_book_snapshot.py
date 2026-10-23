import unittest
from unittest.mock import patch

from scripts.market_selection.analyze_order_book_snapshot import (
    INPUT_SCHEMA, analyze_order_book_snapshot,
)


def snapshot():
    return {
        "schema_version": INPUT_SCHEMA,
        "capture_status": "PASS",
        "provider_id": "binance_spot_market_data",
        "market": {"exchange": "binance", "symbol_native": "BTCUSDT", "quote_asset": "USDT"},
        "captured_at_utc": "2026-10-22T00:00:00Z",
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "1"], ["102", "4"]],
    }


class AnalyzeOrderBookSnapshotTests(unittest.TestCase):
    def test_computes_spread_and_visible_depth_without_predictive_claims(self):
        with patch("scripts.market_selection.analyze_order_book_snapshot.evaluate_provider_use", return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]}):
            result = analyze_order_book_snapshot(snapshot(), {"binance_spot_market_data": {"trusted": True}})
        book = result["book"]
        self.assertEqual(book["best_bid"], "99")
        self.assertEqual(book["best_ask"], "101")
        self.assertEqual(book["mid_price"], "100")
        self.assertEqual(book["spread_absolute"], "2")
        self.assertEqual(book["visible_bid_quote_notional"], "492")
        self.assertEqual(book["visible_ask_quote_notional"], "509")
        self.assertAlmostEqual(book["spread_bps"], 200)
        self.assertFalse(result["orders_submitted"])
        self.assertIn("bids", book)
        self.assertIn("asks", book)

    def test_blocks_missing_authorization(self):
        with self.assertRaises(PermissionError):
            analyze_order_book_snapshot(snapshot())

    def test_rejects_crossed_book(self):
        artifact = snapshot()
        artifact["asks"][0][0] = "98"
        with patch("scripts.market_selection.analyze_order_book_snapshot.evaluate_provider_use", return_value={"decision": "ALLOW", "reason_codes": []}):
            with self.assertRaises(ValueError):
                analyze_order_book_snapshot(artifact, {"binance_spot_market_data": {"trusted": True}})

    def test_rejects_unsorted_levels(self):
        artifact = snapshot()
        artifact["bids"] = [["98", "2"], ["99", "3"]]
        with self.assertRaises(ValueError):
            analyze_order_book_snapshot(artifact)

    def test_rejects_failed_capture(self):
        artifact = snapshot()
        artifact["capture_status"] = "PARTIAL"
        with self.assertRaises(ValueError):
            analyze_order_book_snapshot(artifact)


if __name__ == "__main__":
    unittest.main()
