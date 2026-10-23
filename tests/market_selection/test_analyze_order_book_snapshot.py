import unittest

from scripts.market_selection.analyze_order_book_snapshot import (
    INPUT_SCHEMA, analyze_order_book_snapshot,
)
from scripts.market_selection.provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION


def authorized_assessment():
    return {
        "schema_version": ASSESSMENT_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "provider_id": "binance_spot_market_data",
        "use_case": "internal_analysis",
        "decision": "ALLOW",
        "reason_codes": ["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
        "authorization_evidence_status": "RECORD_VALIDATED_NOT_LEGAL_ADVICE",
        "authorization": {
            "terms_url": "https://example.invalid/terms",
            "terms_sha256": "a" * 64,
            "reviewed_at": "2026-10-22T00:00:00Z",
            "reviewed_by": "synthetic-test-fixture",
            "authorized_use_cases": ["internal_analysis"],
            "authorization_record_sha256": "b" * 64,
        },
    }


def snapshot():
    return {
        "schema_version": INPUT_SCHEMA,
        "capture_status": "PASS",
        "provider_use_assessment": authorized_assessment(),
        "market": {"exchange": "binance", "symbol_native": "BTCUSDT", "quote_asset": "USDT"},
        "captured_at_utc": "2026-10-22T00:00:00Z",
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "1"], ["102", "4"]],
    }


class AnalyzeOrderBookSnapshotTests(unittest.TestCase):
    def test_computes_spread_and_visible_depth_without_predictive_claims(self):
        result = analyze_order_book_snapshot(snapshot())
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
        artifact = snapshot()
        artifact["provider_use_assessment"]["authorization"]["authorized_use_cases"] = ["live_technical_test"]
        with self.assertRaises(PermissionError):
            analyze_order_book_snapshot(artifact)

    def test_rejects_crossed_book(self):
        artifact = snapshot()
        artifact["asks"][0][0] = "98"
        with self.assertRaises(ValueError):
            analyze_order_book_snapshot(artifact)

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
