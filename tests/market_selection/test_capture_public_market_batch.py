"""Offline tests for bounded multi-pair public market capture."""
import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_market_batch import (
    BINANCE_DEPTH_LIMIT, DEFAULT_MARKETS, PIONEX_DEPTH_LIMIT, SCHEMA_VERSION, build_requests, capture_batch, request_capture,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self.payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.read_calls = []
        self.offset = 0
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        self.read_calls.append(size)
        if size is None or size < 0:
            chunk = self.payload[self.offset:]
            self.offset = len(self.payload)
            return chunk
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


TEST_PIONEX_AUTHORIZATION = {
    "schema_version": "crypto-provider-authorization-v1",
    "provider_id": "pionex_spot_market_data",
    "status": "APPROVED",
    "authorized_use_cases": ["live_technical_test"],
    "terms_url": "https://www.pionex.com/",
    "terms_sha256": "a" * 64,
    "reviewed_at": "2026-10-22T12:00:00Z",
    "reviewed_by": "synthetic-test-fixture",
}


class BatchCaptureTests(unittest.TestCase):

    def test_pionex_without_authorization_is_blocked_before_network_request(self):
        with patch("scripts.market_selection.capture_public_market_batch.urlopen") as network:
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid")
        network.assert_not_called()
        self.assertEqual(record["capture_status"], "BLOCKED")
        self.assertEqual(record["provider_use_assessment"]["decision"], "BLOCK")
        self.assertIn("AUTHORIZATION_RECORD_MISSING", record["provider_use_assessment"]["reason_codes"])

    def test_invalid_authorization_is_blocked_before_network_request(self):
        with patch("scripts.market_selection.capture_public_market_batch.urlopen") as network:
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid",
                                     authorization_records={"pionex_spot_market_data": {"invalid": True}})
        network.assert_not_called()
        self.assertEqual(record["capture_status"], "BLOCKED")
        self.assertIn("AUTHORIZATION_RECORD_INVALID", record["provider_use_assessment"]["reason_codes"])

    def test_default_universe_is_explicit_and_small(self):
        self.assertEqual([m[0] for m in DEFAULT_MARKETS], ["BTC_USDT", "ETH_USDT", "SOL_USDT"])
        self.assertEqual(len(build_requests(DEFAULT_MARKETS)), 12)

    def test_request_matrix_captures_market_identity_and_both_depth_sources(self):
        requests = build_requests(DEFAULT_MARKETS)
        for market, _, _, _ in DEFAULT_MARKETS:
            selected = [r for r in requests if r[0] == market]
            self.assertEqual([r[1] for r in selected], ["pionex", "pionex_depth", "binance_exchange_info", "binance_depth"])
            pionex_depth_url = next(r[2] for r in selected if r[1] == "pionex_depth")
            binance_depth_url = next(r[2] for r in selected if r[1] == "binance_depth")
            self.assertIn(f"limit={PIONEX_DEPTH_LIMIT}", pionex_depth_url)
            self.assertIn(f"limit={BINANCE_DEPTH_LIMIT}", binance_depth_url)

    def test_capture_preserves_raw_bytes_and_hash(self):
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse({"result": True})):
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid", authorization_records={"pionex_spot_market_data": TEST_PIONEX_AUTHORIZATION})
        raw = base64.b64decode(record["response_base64"], validate=True)
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["response_bytes"], len(raw))
        self.assertEqual(record["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw), record["parsed_json"])
        self.assertIsNone(record["source_event_at_utc"])
        self.assertEqual(record["source_timestamp_field"], "timestamp")
        self.assertIn("response timestamp", record["source_timestamp_semantics"])
        self.assertIsNone(record["source_response_at_utc"])
        self.assertEqual(record["source_response_timestamp_status"], "MISSING")
        self.assertIsNotNone(record["captured_at_utc"])

    def test_response_larger_than_five_mib_is_preserved_without_arbitrary_cap(self):
        payload = {"data": "x" * (5 * 1024 * 1024 + 128)}
        response = FakeResponse(payload)
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=response):
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid")
        raw = base64.b64decode(record["response_base64"], validate=True)
        self.assertGreater(len(raw), 5 * 1024 * 1024)
        self.assertGreater(len(response.read_calls), 1)
        self.assertTrue(all(size == 64 * 1024 for size in response.read_calls))
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["response_bytes"], len(raw))
        self.assertEqual(record["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw.decode("utf-8")), payload)
        self.assertEqual(record["parsed_json"], payload)

    def test_pionex_response_timestamp_is_normalized_separately_from_market_event_time(self):
        payload = {"result": True, "timestamp": 1792610282496, "data": {"symbols": []}}
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse(payload)):
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["source_response_at_utc"], "2026-10-21T19:18:02.496Z")
        self.assertEqual(record["source_response_timestamp_status"], "VALID")
        self.assertEqual(record["source_timestamp_field"], "timestamp")
        self.assertIn("response timestamp", record["source_timestamp_semantics"])
        self.assertIsNone(record["source_event_at_utc"])

    def test_pionex_invalid_response_timestamp_is_not_normalized(self):
        payload = {"result": True, "timestamp": "not-a-timestamp", "data": {"symbols": []}}
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse(payload)):
            record = request_capture("BTC_USDT", "pionex", "https://example.invalid")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertIsNone(record["source_response_at_utc"])
        self.assertEqual(record["source_response_timestamp_status"], "INVALID")
        self.assertIsNone(record["source_event_at_utc"])

    def test_pionex_depth_update_time_is_normalized_separately(self):
        payload = {
            "result": True,
            "timestamp": 1792610400000,
            "data": {"updateTime": 1792610399123, "bids": [["100", "2"]], "asks": [["101", "3"]]},
        }
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse(payload)):
            record = request_capture("BTC_USDT", "pionex_depth", "https://example.invalid", authorization_records={"pionex_spot_market_data": TEST_PIONEX_AUTHORIZATION})
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["source_market_update_at_utc"], "2026-10-21T19:19:59.123Z")
        self.assertEqual(record["source_market_update_timestamp_status"], "VALID")
        self.assertEqual(record["source_timestamp_field"], "data.updateTime")
        self.assertIn("order-book update timestamp", record["source_timestamp_semantics"])
        self.assertEqual(record["source_response_at_utc"], "2026-10-21T19:20:00.000Z")
        self.assertIsNone(record["source_event_at_utc"])

    def test_pionex_depth_missing_update_time_stays_missing(self):
        payload = {"result": True, "timestamp": 1792610400000, "data": {"bids": [], "asks": []}}
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", return_value=FakeResponse(payload)):
            record = request_capture("BTC_USDT", "pionex_depth", "https://example.invalid")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertIsNone(record["source_market_update_at_utc"])
        self.assertEqual(record["source_market_update_timestamp_status"], "MISSING")
        self.assertEqual(record["source_timestamp_field"], "data.updateTime")

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
        payloads = [FakeResponse({"ok": True}) for _ in range(12)]
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", side_effect=payloads):
            artifact = capture_batch(authorization_records={"pionex_spot_market_data": TEST_PIONEX_AUTHORIZATION})
        self.assertEqual(artifact["schema_version"], SCHEMA_VERSION)
        self.assertEqual(artifact["expected_record_count"], 12)
        self.assertEqual(artifact["actual_record_count"], 12)
        self.assertEqual(artifact["overall_status"], "PASS")


    def test_batch_blocks_unlicensed_provider_calls_before_network(self):
        # Binance technical-test calls are permitted by baseline; Pionex remains blocked.
        payloads = [FakeResponse({"ok": True}) for _ in range(6)]
        with patch("scripts.market_selection.capture_public_market_batch.urlopen", side_effect=payloads) as network:
            artifact = capture_batch()
        self.assertEqual(network.call_count, 6)
        pionex_records = [r for r in artifact["records"] if str(r["provider"]).startswith("pionex")]
        self.assertEqual(len(pionex_records), 6)
        self.assertTrue(all(r["capture_status"] == "BLOCKED" for r in pionex_records))
        self.assertTrue(all(r["provider_use_assessment"]["decision"] == "BLOCK" for r in pionex_records))
        self.assertEqual(artifact["overall_status"], "FAIL")

    def test_empty_or_duplicate_market_universe_rejected(self):
        with self.assertRaises(ValueError):
            capture_batch(())
        with self.assertRaises(ValueError):
            capture_batch((DEFAULT_MARKETS[0], DEFAULT_MARKETS[0]))


if __name__ == "__main__":
    unittest.main()
