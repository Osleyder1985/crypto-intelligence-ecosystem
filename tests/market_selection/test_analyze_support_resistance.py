import base64
import hashlib
import unittest

from scripts.market_selection.analyze_support_resistance import analyze_support_resistance


def candle(i, o, h, l, c, *, closed=True):
    open_ms = i * 3_600_000
    return {
        "open_time_ms": open_ms, "close_time_ms": open_ms + 3_599_999,
        "open": str(o), "high": str(h), "low": str(l), "close": str(c),
        "base_volume": "10", "quote_volume": "1000", "trade_count": 10,
        "closed_at_capture": closed, "eligible_for_closed_candle_analysis": closed,
    }


def artifact(rows):
    raw = b"synthetic preserved response body"
    return {
        "schema_version": "binance-spot-ohlcv-capture-v1", "overall_status": "PASS",
        "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": "BTCUSDT", "interval": "1h"},
        "pages": [{"capture_status": "PASS", "response_base64": base64.b64encode(raw).decode("ascii"),
                   "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest()}],
        "candles": rows,
    }


class SupportResistanceTests(unittest.TestCase):
    def test_pivot_is_available_only_after_right_bars_close(self):
        a = artifact([
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
            candle(5, 9.5, 11, 9, 10.5),
        ])
        result = analyze_support_resistance(a, pivot_left=1, pivot_right=1, tolerance_bps=100)
        created = [e for e in result["events"] if e["event_type"] == "zone_created" and e["kind"] == "support"]
        self.assertTrue(created)
        self.assertEqual(created[0]["pivot_open_time_ms"], 2 * 3_600_000)
        self.assertEqual(created[0]["event_time_ms"], 3 * 3_600_000 + 3_599_999)
        self.assertEqual(created[0]["available_from_ms"], 4 * 3_600_000)

    def test_future_candles_do_not_change_events_before_cutoff(self):
        base = [
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
        ]
        extended = base + [candle(5, 9.5, 11, 9, 10.5), candle(6, 10.5, 12, 10, 11.5)]
        first = analyze_support_resistance(artifact(base), 1, 1, 100)
        second = analyze_support_resistance(artifact(extended), 1, 1, 100)
        cutoff = 4 * 3_600_000 + 3_599_999
        prefix_first = [e for e in first["events"] if e["event_time_ms"] <= cutoff]
        prefix_second = [e for e in second["events"] if e["event_time_ms"] <= cutoff]
        self.assertEqual(prefix_first, prefix_second)

    def test_gaps_split_segments_and_pivots_do_not_cross_them(self):
        rows = [candle(0, 10, 11, 9, 10), candle(1, 10, 11, 8, 9),
                candle(3, 9, 10, 7, 8), candle(4, 8, 9, 8, 8.5),
                candle(5, 8.5, 10, 8, 9.5)]
        result = analyze_support_resistance(artifact(rows), 1, 1, 100)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")
        self.assertEqual(result["sample"]["gap_count"], 1)
        self.assertEqual(result["sample"]["contiguous_segment_count"], 2)

    def test_open_candle_is_excluded(self):
        result = analyze_support_resistance(artifact([
            candle(0, 10, 11, 9, 10), candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8, closed=False),
        ]), 1, 1, 100)
        self.assertEqual(result["sample"]["excluded_open_or_unconfirmed_count"], 1)
        self.assertEqual(result["data_quality_status"], "INCOMPLETE")

    def test_invalid_parameters_and_bad_ohlc_fail_closed(self):
        a = artifact([candle(0, 10, 11, 9, 10), candle(1, 10, 11, 8, 9)])
        with self.assertRaisesRegex(ValueError, "pivot_left"):
            analyze_support_resistance(a, 0, 1, 100)
        bad = artifact([candle(0, 10, 8, 9, 10), candle(1, 10, 11, 8, 9)])
        with self.assertRaisesRegex(ValueError, "OHLC envelope"):
            analyze_support_resistance(bad, 1, 1, 100)

    def test_tampered_page_hash_fails_closed(self):
        a = artifact([candle(0, 10, 11, 9, 10), candle(1, 10, 11, 8, 9)])
        a["pages"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_support_resistance(a, 1, 1, 100)


if __name__ == "__main__":
    unittest.main()
