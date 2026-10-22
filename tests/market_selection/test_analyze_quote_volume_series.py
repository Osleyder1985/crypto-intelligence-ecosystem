import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.market_selection.analyze_quote_volume_series import analyze_artifacts


def record(exchange="binance", asset="BTC", symbol="BTCUSDT", volume="100", captured="2026-10-22T00:00:00Z",
           status="PASS", quote_status="VALID", unit="USDT", semantics="quoteVolume: rolling 24h quote-asset turnover"):
    raw = json.dumps({"symbol": symbol, "quoteVolume": volume}, separators=(",", ":")).encode()
    return {
        "exchange": exchange, "asset": asset, "symbol": symbol, "quote_currency": "USDT",
        "captured_at_utc": captured, "capture_status": status, "http_status": 200 if status == "PASS" else 403,
        "quote_volume_status": quote_status, "quote_volume_raw": volume if quote_status == "VALID" else None,
        "quote_volume_decimal": volume if quote_status == "VALID" else None, "quote_volume_unit": unit,
        "volume_semantics": semantics, "source_timestamp_raw": 1792627200000,
        "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_base64": base64.b64encode(raw).decode("ascii"),
    }


def write_artifact(path, created, records):
    path.write_text(json.dumps({
        "schema_version": "multi-exchange-spot-quote-volume-v1",
        "created_at_utc": created, "expected_record_count": len(records),
        "actual_record_count": len(records), "records": records,
    }), encoding="utf-8")
    return path


class QuoteVolumeSeriesTests(unittest.TestCase):
    def test_calculates_descriptive_delta_without_claiming_interval_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = write_artifact(Path(tmp) / "first.json", "2026-10-22T00:00:00Z",
                                   [record(volume="100", captured="2026-10-22T00:00:00Z")])
            second = write_artifact(Path(tmp) / "second.json", "2026-10-22T06:00:00Z",
                                    [record(volume="110", captured="2026-10-22T06:00:00Z")])
            result = analyze_artifacts([second, first])
        self.assertEqual(result["analysis_status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(result["input_record_count"], 2)
        row = result["series"][0]
        self.assertEqual(row["comparison_status"], "DESCRIPTIVE_COMPARISON_ONLY")
        self.assertEqual(row["valid_samples"], 2)
        self.assertEqual(row["consecutive_deltas"][0]["change_percent_between_rolling_windows"], "10.0")
        self.assertIn("not turnover traded", row["consecutive_deltas"][0]["interpretation_limit"])
        self.assertFalse(row["selection_or_ranking_performed"])

    def test_missing_turnover_is_not_converted_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write_artifact(Path(tmp) / "a.json", "2026-10-22T00:00:00Z", [
                record(volume="100", captured="2026-10-22T00:00:00Z"),
                record(exchange="okx", symbol="BTC-USDT", volume=None, quote_status="INDETERMINATE",
                       captured="2026-10-22T00:00:00Z"),
            ])
            b = write_artifact(Path(tmp) / "b.json", "2026-10-22T06:00:00Z", [
                record(volume="110", captured="2026-10-22T06:00:00Z"),
                record(exchange="okx", symbol="BTC-USDT", volume=None, quote_status="INDETERMINATE",
                       captured="2026-10-22T06:00:00Z"),
            ])
            result = analyze_artifacts([a, b])
        okx = next(row for row in result["series"] if row["exchange"] == "okx")
        self.assertEqual(okx["valid_samples"], 0)
        self.assertEqual(okx["missing_or_invalid_samples"], 2)
        self.assertEqual(okx["comparison_status"], "INSUFFICIENT_VALID_SAMPLES")
        self.assertIsNone(okx["observations"][0]["quote_volume_decimal"])

    def test_incompatible_units_do_not_get_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write_artifact(Path(tmp) / "a.json", "2026-10-22T00:00:00Z",
                               [record(volume="100", captured="2026-10-22T00:00:00Z", unit="USDT")])
            b = write_artifact(Path(tmp) / "b.json", "2026-10-22T06:00:00Z",
                               [record(volume="110", captured="2026-10-22T06:00:00Z", unit="USD")])
            result = analyze_artifacts([a, b])
        self.assertEqual(result["series"][0]["comparison_status"], "INDETERMINATE_INCOMPATIBLE_SEMANTICS_OR_UNITS")
        self.assertEqual(result["series"][0]["consecutive_deltas"], [])


    def test_missing_semantics_does_not_allow_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write_artifact(Path(tmp) / "a.json", "2026-10-22T00:00:00Z",
                               [record(volume="100", captured="2026-10-22T00:00:00Z")])
            b = write_artifact(Path(tmp) / "b.json", "2026-10-22T06:00:00Z",
                               [record(volume="110", captured="2026-10-22T06:00:00Z", semantics=None)])
            result = analyze_artifacts([a, b])
        self.assertEqual(result["series"][0]["comparison_status"], "INDETERMINATE_INCOMPATIBLE_SEMANTICS_OR_UNITS")
        self.assertEqual(result["series"][0]["consecutive_deltas"], [])

    def test_tampered_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_artifact(Path(tmp) / "bad.json", "2026-10-22T00:00:00Z",
                                  [record(volume="100", captured="2026-10-22T00:00:00Z")])
            data = json.loads(path.read_text())
            data["records"][0]["response_sha256"] = "0" * 64
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                analyze_artifacts([path])

    def test_successful_record_without_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_artifact(Path(tmp) / "bad.json", "2026-10-22T00:00:00Z",
                                  [record(volume="100", captured="2026-10-22T00:00:00Z")])
            data = json.loads(path.read_text())
            data["records"][0]["response_base64"] = None
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "no preserved response body"):
                analyze_artifacts([path])


if __name__ == "__main__":
    unittest.main()
