import unittest
from unittest.mock import patch

from scripts.market_selection.capture_binance_spot_ohlcv import (
    BASE_URL, build_url, expected_open_times, is_interval_boundary,
    next_open_time, normalize_kline, validate_window,
)


class BinanceSpotOHLCVTests(unittest.TestCase):
    def test_normalizes_binance_kline_without_losing_quote_volume(self):
        row = [0, "10", "12", "9", "11", "5", 59_999, "55", 17, "2", "22", "0"]
        out = normalize_kline(row, "BTCUSDT", "1m", "2026-10-22T00:01:00Z")
        self.assertEqual(out["market_type"], "SPOT")
        self.assertEqual(out["open_time_ms"], 0)
        self.assertEqual(out["quote_volume"], "55")
        self.assertEqual(out["trade_count"], 17)
        self.assertEqual(out["source_timestamp_unit"], "milliseconds")

    def test_rejects_invalid_ohlc_envelope(self):
        row = [0, "10", "9", "8", "11", "5", 59_999, "55", 17, "2", "22", "0"]
        with self.assertRaisesRegex(ValueError, "OHLC high/low envelope"):
            normalize_kline(row, "BTCUSDT", "1m", "2026-10-22T00:01:00Z")

    def test_rejects_nonfinite_and_negative_volume(self):
        row = [0, "10", "12", "9", "11", "-1", 59_999, "55", 17, "2", "22", "0"]
        with self.assertRaisesRegex(ValueError, "non-negative"):
            normalize_kline(row, "BTCUSDT", "1m", "2026-10-22T00:01:00Z")
        row[5] = "NaN"
        with self.assertRaisesRegex(ValueError, "finite"):
            normalize_kline(row, "BTCUSDT", "1m", "2026-10-22T00:01:00Z")

    def test_exclusive_window_and_boundary_validation(self):
        self.assertEqual(expected_open_times(0, 180_000, "1m"), [0, 60_000, 120_000])
        validate_window(0, 180_000, "1m")
        with self.assertRaisesRegex(ValueError, "align"):
            validate_window(1, 180_000, "1m")

    def test_monthly_interval_progression_handles_december(self):
        import datetime
        dec = int(datetime.datetime(2026, 12, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        jan = int(datetime.datetime(2027, 1, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        self.assertEqual(next_open_time(dec, "1M"), jan)
        self.assertTrue(is_interval_boundary(jan, "1M"))

    def test_weekly_boundary_is_monday_utc(self):
        import datetime
        monday = int(datetime.datetime(2026, 10, 19, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        tuesday = monday + 86_400_000
        self.assertTrue(is_interval_boundary(monday, "1w"))
        self.assertFalse(is_interval_boundary(tuesday, "1w"))


    def test_invalid_payload_is_preserved_and_returns_partial_artifact(self):
        import base64
        import hashlib
        import json
        raw = json.dumps([["bad", "10", "12", "9", "11", "5", 59999, "55", 17, "2", "22"]]).encode()
        page = {
            "url": BASE_URL, "request_started_at_utc": "2026-10-22T00:00:00Z",
            "captured_at_utc": "2026-10-22T00:00:01Z", "http_status": 200,
            "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_base64": base64.b64encode(raw).decode(), "parsed_json": [["bad", "10", "12", "9", "11", "5", 59999, "55", 17, "2", "22"]],
            "capture_status": "PASS", "normalization_status": "NOT_RUN",
            "normalization_error": None, "error_type": None, "error_message": None,
        }
        with patch("scripts.market_selection.capture_binance_spot_ohlcv.request_page", return_value=page):
            result = __import__("scripts.market_selection.capture_binance_spot_ohlcv", fromlist=["capture_history"]).capture_history(
                "BTCUSDT", "1m", 0, 60_000
            )
        self.assertEqual(result["overall_status"], "PARTIAL")
        self.assertEqual(result["pages"][0]["normalization_status"], "FAIL")
        self.assertIn("kline timestamps", result["pages"][0]["normalization_error"])
        self.assertEqual(result["pages"][0]["response_sha256"], hashlib.sha256(raw).hexdigest())

    def test_url_uses_official_host_and_exclusive_end(self):
        url = build_url("BTCUSDT", "1m", 0, 180_000, 60_000)
        self.assertTrue(url.startswith(BASE_URL + "?"))
        self.assertIn("startTime=60000", url)
        self.assertIn("endTime=179999", url)
        self.assertIn("limit=1000", url)
        self.assertNotIn("api_key", url)


if __name__ == "__main__":
    unittest.main()
