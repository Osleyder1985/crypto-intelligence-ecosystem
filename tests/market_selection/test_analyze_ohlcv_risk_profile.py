import base64
import hashlib
import unittest

from scripts.market_selection.analyze_ohlcv_risk_profile import analyze_artifact


def candle(open_ms, close, *, closed=True, quote_volume="1000", base_volume="10"):
    return {
        "open_time_ms": open_ms, "close_time_ms": open_ms + 3_599_999,
        "open": str(close), "high": str(close), "low": str(close), "close": str(close),
        "base_volume": base_volume, "quote_volume": quote_volume, "trade_count": 10,
        "closed_at_capture": closed, "eligible_for_closed_candle_analysis": closed,
    }


def artifact(rows):
    raw = b"synthetic preserved response body"
    return {
        "schema_version": "binance-spot-ohlcv-capture-v1",
        "overall_status": "PASS",
        "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": "BTCUSDT", "interval": "1h"},
        "window": {"start_time_ms_inclusive": rows[0]["open_time_ms"], "end_time_ms_exclusive": rows[-1]["open_time_ms"] + 3_600_000},
        "pages": [{"capture_status": "PASS", "response_base64": base64.b64encode(raw).decode("ascii"), "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest()}],
        "candles": rows,
    }


class OHLCVRiskProfileTests(unittest.TestCase):
    def test_drawdown_and_period_return_use_closed_observed_closes(self):
        result = analyze_artifact(artifact([
            candle(0, "100"), candle(3_600_000, "110"),
            candle(7_200_000, "99"), candle(10_800_000, "101"),
        ]))
        self.assertEqual(result["analysis_status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(result["data_quality_status"], "COMPLETE")
        self.assertAlmostEqual(result["metrics"]["observed_period_return_pct"], 1.0)
        self.assertAlmostEqual(result["metrics"]["maximum_observed_close_to_close_drawdown_pct"], -10.0)
        self.assertEqual(result["sample"]["consecutive_interval_return_count"], 3)
        self.assertIsNone(result["metrics"]["annualized_log_volatility"])

    def test_open_candle_is_excluded_from_metrics(self):
        result = analyze_artifact(artifact([
            candle(0, "100"), candle(3_600_000, "105"),
            candle(7_200_000, "10000", closed=False),
        ]))
        self.assertEqual(result["sample"]["closed_candle_count"], 2)
        self.assertEqual(result["sample"]["excluded_open_or_unconfirmed_count"], 1)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")
        self.assertAlmostEqual(result["metrics"]["observed_period_return_pct"], 5.0)

    def test_gap_is_reported_and_cross_gap_return_is_not_counted_as_one_bar(self):
        result = analyze_artifact(artifact([
            candle(0, "100"), candle(3_600_000, "110"), candle(10_800_000, "80"),
        ]))
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")
        self.assertEqual(result["sample"]["gap_count"], 1)
        self.assertEqual(result["sample"]["consecutive_interval_return_count"], 1)
        self.assertEqual(result["sample"]["returns_skipped_across_gaps"], 1)
        self.assertEqual(result["gaps"][0]["expected_next_open_time_ms"], 7_200_000)

    def test_explicit_annualization_is_not_assumed(self):
        a = artifact([candle(0, "100"), candle(3_600_000, "101"), candle(7_200_000, "99")])
        per_bar = analyze_artifact(a)
        annualized = analyze_artifact(a, periods_per_year=8760)
        self.assertIsNone(per_bar["metrics"]["annualized_log_volatility"])
        self.assertIsNotNone(annualized["metrics"]["annualized_log_volatility"])
        self.assertEqual(annualized["metrics"]["annualization_periods_per_year"], 8760)


    def test_tampered_source_response_hash_fails_closed(self):
        a = artifact([candle(0, "100"), candle(3_600_000, "101")])
        a["pages"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_artifact(a)

    def test_successful_page_without_preserved_body_fails_closed(self):
        a = artifact([candle(0, "100"), candle(3_600_000, "101")])
        a["pages"][0]["response_base64"] = None
        with self.assertRaisesRegex(ValueError, "no preserved response body"):
            analyze_artifact(a)


    def test_partial_source_artifact_cannot_be_marked_complete(self):
        a = artifact([candle(0, "100"), candle(3_600_000, "101")])
        a["overall_status"] = "PARTIAL"
        result = analyze_artifact(a)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")

    def test_duplicate_or_out_of_order_candles_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            analyze_artifact(artifact([candle(3_600_000, "100"), candle(0, "101")]))

    def test_invalid_close_or_negative_volume_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            analyze_artifact(artifact([candle(0, "0"), candle(3_600_000, "101")]))
        with self.assertRaisesRegex(ValueError, "non-negative"):
            analyze_artifact(artifact([candle(0, "100", quote_volume="-1"), candle(3_600_000, "101")]))


if __name__ == "__main__":
    unittest.main()
