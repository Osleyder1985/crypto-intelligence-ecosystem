"""Offline tests for the live depth evidence artifact contract."""
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection import capture_binance_live_depth_evidence as capture


class LiveDepthEvidenceTests(unittest.TestCase):
    def test_hash_is_stable_for_canonical_json(self):
        first = {"bids": [["1.0", "2"]], "asks": [["2.0", "3"]]}
        second = {"asks": [["2.0", "3"]], "bids": [["1.0", "2"]]}
        self.assertEqual(capture.sha256_json(first), capture.sha256_json(second))
        self.assertEqual(len(capture.sha256_json(first)), 64)

    def test_clock_uses_lowest_rtt_probe_without_grading_threshold(self):
        probes = [
            {"status": "MEASURED", "round_trip_time_ms": 12.0, "local_minus_server_offset_ms": 3.0},
            {"status": "MEASURED", "round_trip_time_ms": 4.0, "local_minus_server_offset_ms": -2.0},
            {"status": "MEASURED", "round_trip_time_ms": 8.0, "local_minus_server_offset_ms": 1.0},
        ]
        with patch.object(capture, "clock_probe", side_effect=probes):
            result = capture.measure_clock()
        self.assertEqual(result["status"], "MEASURED")
        self.assertEqual(result["selected_probe"]["round_trip_time_ms"], 4.0)
        self.assertIn("not a policy threshold", result["selection_method"])
        self.assertEqual(len(result["probes"]), 3)

    def test_partial_clock_probe_is_not_silently_called_measured(self):
        probes = [
            {"status": "MEASURED", "round_trip_time_ms": 4.0, "local_minus_server_offset_ms": 1.0},
            {"status": "FAIL", "error_type": "TimeoutError"},
            {"status": "MEASURED", "round_trip_time_ms": 6.0, "local_minus_server_offset_ms": 2.0},
        ]
        with patch.object(capture, "clock_probe", side_effect=probes):
            result = capture.measure_clock()
        self.assertEqual(result["status"], "PARTIAL")

    def test_all_clock_probes_failed_is_indeterminate(self):
        with patch.object(capture, "clock_probe", return_value={"status": "FAIL"}):
            result = capture.measure_clock()
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertEqual(len(result["probes"]), 3)

    def test_batch_remains_indeterminate_even_when_capture_and_clock_pass(self):
        clock = {
            "status": "MEASURED",
            "selected_probe": {"local_minus_server_offset_ms": 2.0},
            "probes": [],
        }
        captures = [
            {"status": "SYNCHRONIZED", "symbol": symbol, "evidence_sha256": "a" * 64}
            for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT")
        ]
        with patch.object(capture, "measure_clock", return_value=clock), patch.object(
            capture, "capture_symbol", side_effect=captures
        ):
            artifact = capture.capture_batch()
        self.assertEqual(artifact["overall_status"], "PASS")
        self.assertEqual(artifact["decision_status"], "INDETERMINATE")
        self.assertFalse(artifact["freshness_policy_approved"])
        self.assertFalse(artifact["orders_submitted"])
        self.assertEqual(artifact["artifact_sha256"], capture.sha256_json({
            key: value for key, value in artifact.items() if key != "artifact_sha256"
        }))

    def test_batch_is_indeterminate_if_any_capture_fails(self):
        clock = {"status": "MEASURED", "selected_probe": {}, "probes": []}
        captures = [
            {"status": "SYNCHRONIZED", "symbol": "BTCUSDT"},
            {"status": "FAIL", "symbol": "ETHUSDT"},
            {"status": "SYNCHRONIZED", "symbol": "SOLUSDT"},
        ]
        with patch.object(capture, "measure_clock", return_value=clock), patch.object(
            capture, "capture_symbol", side_effect=captures
        ):
            artifact = capture.capture_batch()
        self.assertEqual(artifact["overall_status"], "INDETERMINATE")
        self.assertEqual(artifact["decision_status"], "INDETERMINATE")

    def test_rejects_duplicate_or_invalid_symbols(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            capture.capture_batch(("BTCUSDT", "BTCUSDT"))
        with self.assertRaisesRegex(ValueError, "ASCII alphanumeric"):
            capture.capture_batch(("BTC/USDT",))


if __name__ == "__main__":
    unittest.main()
