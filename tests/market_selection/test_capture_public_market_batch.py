"""Offline tests for bounded multi-pair public market capture."""
import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_market_batch import (
    DEFAULT_MARKETS, SCHEMA_VERSION, build_requests, capture_batch, request_capture,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self.payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        return self.payload[:size]


class BatchCaptureTests(unittest.TestCase):
    def test_default_universe_is_explicit_and_small(self):
        self.assertEqual([m[0] for m in DEFAULT_MARKETS], ["BTC_USDT", "ETH_USDT", "SOL_USDT"])
        self.assertEqual(len(build_requests(DEFAULT_MARKETS)), 9)

    def test_request_matrix_has_three_providers_per_market(self):
        requests = build_requests(DEFAULT_MARKETS)
        for market, _, _, _ in DEFAULT_MARKETS:
            selected = [r for r in requests if r[0] == market]
            self.assertEqual([r[1] for r in selected], ["pionex", "binance_exchange_info", "binance_depth"])

    def test_capture_preserves_raw_bytes_and_hash(self):
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse({"result": True})):
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid")
        raw = base64.b64decode(record["response_base64"], validate=True)
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["response_bytes"], len(raw))
        self.assertEqual(record["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw), record["parsed_json"])
        self.assertIsNone(record["source_event_at_utc"])
        self.assertIsNone(record["source_timestamp_field"])
        self.assertIsNone(record["source_timestamp_semantics"])
        self.assertIsNotNone(record["captured_at_utc"])

    def test_binance_depth_sequence_id_is_not_event_timestamp(self):
        # Binance depth lastUpdateId is a sequence identifier, not an event-time timestamp.
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse({"lastUpdateId": 123456, "bids": [], "asks": []})):
            record = request_capture("BTC_USDT", "binance_depth", "https://example.invalid")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["parsed_json"]["lastUpdateId"], 123456)
        self.assertIsNone(record["source_event_at_utc"])
        self.assertIsNone(record["source_timestamp_field"])
        self.assertIsNone(record["source_timestamp_semantics"])

    def test_non_200_response_fails_and_retains_evidence(self):
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse({"message": "bad"}, 503)):
            record = request_capture("BTC_USDT", "binance_depth", "https://example.invalid")
        self.assertEqual(record["capture_status"], "FAIL")
        self.assertEqual(record["http_status"], 503)
        self.assertIsNotNone(record["response_sha256"])

    def test_batch_schema_and_expected_record_count(self):
        payloads = [FakeResponse({"ok": True}) for _ in range(9)]
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", side_effect=payloads):
            artifact = capture_batch()
        self.assertEqual(artifact["schema_version"], SCHEMA_VERSION)
        self.assertEqual(artifact["expected_record_count"], 9)
        self.assertEqual(artifact["actual_record_count"], 9)
        self.assertEqual(artifact["overall_status"], "PASS")

    def test_empty_or_duplicate_market_universe_rejected(self):
        with self.assertRaises(ValueError):
            capture_batch(())
        with self.assertRaises(ValueError):
            capture_batch((DEFAULT_MARKETS[0], DEFAULT_MARKETS[0]))


if __name__ == "__main__":
    unittest.main()
