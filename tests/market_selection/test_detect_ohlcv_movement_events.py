import base64
import hashlib
import unittest

from scripts.market_selection.provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION
from scripts.market_selection.detect_ohlcv_movement_events import analyze_movement_events


def candle(i, close, quote_volume, *, closed=True):
    open_ms = i * 3_600_000
    return {
        "open_time_ms": open_ms, "close_time_ms": open_ms + 3_599_999,
        "open": str(close), "high": str(close), "low": str(close), "close": str(close),
        "base_volume": "10", "quote_volume": str(quote_volume), "trade_count": 10,
        "closed_at_capture": closed, "eligible_for_closed_candle_analysis": closed,
    }


def artifact(rows):
    raw = b"synthetic preserved response body"
    return {
        "schema_version": "binance-spot-ohlcv-capture-v1",
        "provider_use_assessment": {"schema_version": ASSESSMENT_SCHEMA_VERSION, "policy_version": POLICY_VERSION,
            "provider_id": "binance_spot_market_data", "use_case": "internal_analysis", "decision": "ALLOW",
            "reason_codes": ["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization": {"authorized_use_cases": ["internal_analysis"], "authorization_record_sha256": "b" * 64}}, "overall_status": "PASS",
        "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": "BTCUSDT", "interval": "1h"},
        "pages": [{"capture_status": "PASS", "response_base64": base64.b64encode(raw).decode("ascii"),
                   "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest()}],
        "candles": rows,
    }


class OHLCVMovementEventTests(unittest.TestCase):
    def test_price_move_uses_previous_closed_close_and_explicit_threshold(self):
        result = analyze_movement_events(artifact([
            candle(0, "100", "100"), candle(1, "101", "100"),
            candle(2, "110", "100"), candle(3, "111", "100"),
        ]), lookback_bars=2, return_threshold_pct=5, volume_ratio_threshold=3)
        event = next(e for e in result["events"] if e["source_candle_open_time_ms"] == 2 * 3_600_000)
        self.assertEqual(event["event_type"], "PRICE_MOVE")
        self.assertEqual(event["direction"], "UP")
        self.assertAlmostEqual(event["simple_return_pct"], 8.9108910891)
        self.assertEqual(event["lookahead_bars"], 0)
        self.assertEqual(event["causal_attribution"], "NOT_ESTABLISHED")

    def test_volume_spike_uses_prior_median_not_current_value(self):
        result = analyze_movement_events(artifact([
            candle(0, "100", "100"), candle(1, "100", "100"),
            candle(2, "100", "500"), candle(3, "100", "100"),
        ]), lookback_bars=2, return_threshold_pct=10, volume_ratio_threshold=3)
        event = next(e for e in result["events"] if e["source_candle_open_time_ms"] == 2 * 3_600_000)
        self.assertEqual(event["event_type"], "VOLUME_SPIKE")
        self.assertEqual(event["prior_window_quote_volume_median"], 100)
        self.assertEqual(event["quote_volume_ratio_to_prior_median"], 5)

    def test_future_candles_do_not_change_past_events(self):
        base = [candle(0, "100", "100"), candle(1, "100", "100"), candle(2, "110", "100")]
        extended = base + [candle(3, "100", "100"), candle(4, "101", "100")]
        first = analyze_movement_events(artifact(base), 2, 5, 3)
        second = analyze_movement_events(artifact(extended), 2, 5, 3)
        cutoff = 2 * 3_600_000 + 3_599_999
        self.assertEqual([e for e in first["events"] if e["event_time_ms"] <= cutoff],
                         [e for e in second["events"] if e["event_time_ms"] <= cutoff])

    def test_gaps_break_the_baseline_and_mark_quality_incomplete(self):
        rows = [candle(0, "100", "100"), candle(1, "100", "100"),
                candle(3, "120", "10000"), candle(4, "120", "10000"),
                candle(5, "120", "10000")]
        result = analyze_movement_events(artifact(rows), 2, 5, 3)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")
        self.assertEqual(result["sample"]["gap_or_segment_break_count"], 1)
        self.assertFalse(any(e["source_candle_open_time_ms"] == 3 * 3_600_000 for e in result["events"]))

    def test_open_candle_is_not_used_as_return_or_volume_baseline(self):
        rows = [candle(0, "100", "100"), candle(1, "100", "100"),
                candle(2, "10000", "100000", closed=False), candle(3, "100", "100"),
                candle(4, "101", "100")]
        result = analyze_movement_events(artifact(rows), 2, 5, 3)
        self.assertEqual(result["sample"]["excluded_open_or_unconfirmed_count"], 1)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")
        self.assertFalse(any(e["source_candle_open_time_ms"] == 4 * 3_600_000 for e in result["events"]))

    def test_tampered_source_hash_fails_closed(self):
        a = artifact([candle(0, "100", "100"), candle(1, "101", "100")])
        a["pages"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_movement_events(a, 2, 5, 3)


if __name__ == "__main__":
    unittest.main()
