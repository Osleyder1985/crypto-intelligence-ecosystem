import copy
import hashlib
import json
import unittest

from scripts.market_selection.normalize_binance_live_depth_evidence import (
    normalize_binance_live_depth_evidence,
)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def seal(value, field):
    result = copy.deepcopy(value)
    result[field] = digest(result)
    return result


def artifact():
    capture = {
        "status": "SYNCHRONIZED",
        "symbol": "BTCUSDT",
        "capture_started_at_utc": "2026-10-23T02:00:00Z",
        "capture_completed_at_utc": "2026-10-23T02:00:01Z",
        "source_event_at_utc": "2026-10-23T02:00:00.500Z",
        "last_event_received_at_utc": "2026-10-23T02:00:00.600Z",
        "evaluated_at_utc": "2026-10-23T02:00:00.700Z",
        "snapshot_last_update_id": 100,
        "last_applied_update_id": 101,
        "applied_event_count": 1,
        "bids": [["100.0", "2.0"], ["99.5", "3.0"]],
        "asks": [["100.5", "1.0"], ["101.0", "4.0"]],
        "freshness_observation": {
            "source_timestamp_utc": "2026-10-23T02:00:00.500Z",
            "captured_at_utc": "2026-10-23T02:00:00.600Z",
            "evaluation_time_utc": "2026-10-23T02:00:00.700Z",
            "source_to_capture_ms": 100,
            "capture_to_evaluation_ms": 100,
        },
        "messages_received": 1,
        "snapshot_attempts": 1,
        "read_only": True,
        "orders_submitted": False,
    }
    capture = seal(capture, "evidence_sha256")
    result = {
        "schema_version": "binance-live-depth-evidence-v1",
        "created_at_utc": "2026-10-23T02:00:02Z",
        "scope": "public Binance Spot WebSocket diff-depth plus REST snapshot; read-only",
        "clock_evidence": {"status": "MEASURED", "selected_probe": {"round_trip_time_ms": 5}},
        "captures": [capture],
        "overall_status": "PASS",
        "decision_status": "INDETERMINATE",
        "freshness_policy_approved": False,
        "orders_submitted": False,
        "limitations": ["Synthetic fixture"],
    }
    return seal(result, "artifact_sha256")


class NormalizeBinanceLiveDepthTests(unittest.TestCase):
    def test_converts_verified_synchronized_capture_and_preserves_timing(self):
        result = normalize_binance_live_depth_evidence(
            artifact(), symbol="btcusdt", quote_asset="usdt",
        )
        self.assertEqual(result["schema_version"], "crypto-spot-order-book-snapshot-v1")
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["provider_id"], "binance_spot_market_data")
        self.assertEqual(result["market"]["symbol_native"], "BTCUSDT")
        self.assertEqual(result["market"]["quote_asset"], "USDT")
        self.assertEqual(result["captured_at_utc"], "2026-10-23T02:00:00.700Z")
        self.assertEqual(result["bids"][0], ["100.0", "2.0"])
        self.assertEqual(result["source_evidence"]["freshness_policy_status"], "NOT_APPROVED")
        self.assertEqual(result["source_evidence"]["freshness_conclusion"], "NOT_ASSESSED")
        self.assertFalse(result["orders_submitted"])

    def test_rejects_tampered_top_level_artifact(self):
        data = artifact()
        data["captures"][0]["bids"][0][0] = "999"
        with self.assertRaisesRegex(ValueError, "artifact SHA-256 digest mismatch"):
            normalize_binance_live_depth_evidence(data, symbol="BTCUSDT", quote_asset="USDT")

    def test_rejects_tampered_capture_record(self):
        data = artifact()
        data["captures"][0]["bids"][0][0] = "999"
        data = seal({k: v for k, v in data.items() if k != "artifact_sha256"}, "artifact_sha256")
        with self.assertRaisesRegex(ValueError, "captures\[0\] SHA-256 digest mismatch"):
            normalize_binance_live_depth_evidence(data, symbol="BTCUSDT", quote_asset="USDT")

    def test_rejects_indeterminate_batch_even_when_selected_capture_is_synchronized(self):
        data = artifact()
        data["overall_status"] = "INDETERMINATE"
        data = seal({k: v for k, v in data.items() if k != "artifact_sha256"}, "artifact_sha256")
        with self.assertRaisesRegex(ValueError, "overall_status must be PASS"):
            normalize_binance_live_depth_evidence(data, symbol="BTCUSDT", quote_asset="USDT")

    def test_rejects_unapproved_freshness_being_overridden(self):
        data = artifact()
        data["freshness_policy_approved"] = True
        data = seal({k: v for k, v in data.items() if k != "artifact_sha256"}, "artifact_sha256")
        with self.assertRaisesRegex(ValueError, "must not claim an approved freshness policy"):
            normalize_binance_live_depth_evidence(data, symbol="BTCUSDT", quote_asset="USDT")

    def test_rejects_missing_or_ambiguous_symbol(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            normalize_binance_live_depth_evidence(artifact(), symbol="ETHUSDT", quote_asset="USDT")
        data = artifact()
        data["captures"].append(copy.deepcopy(data["captures"][0]))
        data["captures"][-1]["evidence_sha256"] = digest({
            k: v for k, v in data["captures"][-1].items() if k != "evidence_sha256"
        })
        data = seal({k: v for k, v in data.items() if k != "artifact_sha256"}, "artifact_sha256")
        with self.assertRaisesRegex(ValueError, "found 2"):
            normalize_binance_live_depth_evidence(data, symbol="BTCUSDT", quote_asset="USDT")


if __name__ == "__main__":
    unittest.main()
