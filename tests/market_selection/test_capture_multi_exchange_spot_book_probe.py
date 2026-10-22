import unittest
import base64
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from scripts.market_selection.capture_multi_exchange_spot_book_probe import (
    SCHEMA_VERSION, READ_CHUNK_BYTES, PROVIDER_IDS, build_requests, capture_one, extract_top_of_book,
)


class MultiExchangeSpotBookProbeTests(unittest.TestCase):
    @staticmethod
    def authorization_record(provider_id):
        return {
            "schema_version": "crypto-provider-authorization-v1",
            "provider_id": provider_id,
            "status": "APPROVED",
            "authorized_use_cases": ["persistent_storage"],
            "terms_url": "https://example.com/terms",
            "terms_sha256": "a" * 64,
            "reviewed_at": "2026-10-22T00:00:00Z",
            "reviewed_by": "offline-test-fixture",
        }

    def test_missing_authorization_blocks_before_network_for_every_venue(self):
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", side_effect=AssertionError("network must not be called")):
            for spec in build_requests():
                with self.subTest(exchange=spec["exchange"], symbol=spec["symbol"]):
                    result = capture_one(spec)
                    self.assertEqual(result["capture_status"], "BLOCKED")
                    self.assertEqual(result["provider_use_assessment"]["decision"], "BLOCK")

    def test_authorization_outside_provider_or_use_scope_blocks_before_network(self):
        spec = build_requests()[0]
        provider_id = PROVIDER_IDS[spec["exchange"]]
        bad_record = self.authorization_record(provider_id)
        bad_record["authorized_use_cases"] = ["live_technical_test"]
        records = {provider_id: bad_record}
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", side_effect=AssertionError("network must not be called")):
            result = capture_one(spec, records)
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertEqual(result["provider_use_assessment"]["decision"], "BLOCK")

    def test_probe_covers_seven_required_exchanges_and_three_assets(self):
        requests = build_requests()
        self.assertEqual(len(requests), 21)
        self.assertEqual({r["exchange"] for r in requests},
                         {"binance", "okx", "bybit", "mexc", "gate", "bitget", "pionex"})
        self.assertEqual({r["asset"] for r in requests}, {"BTC", "ETH", "SOL"})
        self.assertTrue(all(r["url"].startswith("https://") for r in requests))

    def test_okx_response_contract(self):
        bids, asks, timestamp = extract_top_of_book("okx", {
            "code": "0", "data": [{"bids": [["100", "2"]], "asks": [["101", "3"]], "ts": "123"}]
        })
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertEqual(timestamp, "123")

    def test_bybit_rejects_api_error(self):
        with self.assertRaises(ValueError):
            extract_top_of_book("bybit", {"retCode": 10001, "retMsg": "bad request"})

    def test_binance_depth_has_no_source_event_timestamp(self):
        bids, asks, timestamp = extract_top_of_book("binance", {"lastUpdateId": 123, "bids": [["100", "2"]], "asks": [["101", "3"]]})
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertIsNone(timestamp)

    def test_mexc_depth_has_no_source_event_timestamp(self):
        bids, asks, timestamp = extract_top_of_book("mexc", {"lastUpdateId": 123, "bids": [["100", "2"]], "asks": [["101", "3"]]})
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertIsNone(timestamp)

    def test_gate_depth_timestamp_is_update_time(self):
        bids, asks, timestamp = extract_top_of_book("gate", {"current": 200, "update": 199, "bids": [["100", "2"]], "asks": [["101", "3"]]})
        self.assertEqual(timestamp, 199)

    def test_bitget_contract(self):
        bids, asks, timestamp = extract_top_of_book("bitget", {"code": "00000", "data": {"b": [["100", "2"]], "a": [["101", "3"]], "ts": "123"}})
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertEqual(timestamp, "123")

    def test_pionex_uses_book_update_time_not_wrapper_time(self):
        bids, asks, timestamp = extract_top_of_book("pionex", {"result": True, "timestamp": 500, "data": {"bids": [["100", "2"]], "asks": [["101", "3"]], "updateTime": 400}})
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertEqual(timestamp, 400)

    def test_reads_complete_valid_response_larger_than_old_cap(self):
        spec = build_requests()[1]
        body = json_bytes = b'{"code":"0","data":[{"bids":[["100","2"]],"asks":[["101","3"]],"ts":"123"}]}' + b" " * (READ_CHUNK_BYTES * 2)
        class FakeResponse:
            status = 200
            headers = {"Content-Length": str(len(body))}
            def __init__(self): self.remaining = body
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size=-1):
                if size < 0:
                    result, self.remaining = self.remaining, b""
                else:
                    result, self.remaining = self.remaining[:size], self.remaining[size:]
                return result
        authorization_records = {PROVIDER_IDS[spec["exchange"]]: self.authorization_record(PROVIDER_IDS[spec["exchange"]])}
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", return_value=FakeResponse()):
            result = capture_one(spec, authorization_records)
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["response_bytes"], len(body))
        self.assertEqual(result["response_bytes_observed"], len(body))
        self.assertEqual(result["response_limit_bytes"], None)
        self.assertEqual(result["response_base64"], base64.b64encode(body).decode("ascii"))

    def test_http_error_is_recorded_not_raised(self):
        spec = build_requests()[0]
        error = HTTPError(spec["url"], 451, "restricted", {}, BytesIO(b"blocked"))
        authorization_records = {PROVIDER_IDS[spec["exchange"]]: self.authorization_record(PROVIDER_IDS[spec["exchange"]])}
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", side_effect=error):
            result = capture_one(spec, authorization_records)
        self.assertEqual(result["capture_status"], "FAIL")
        self.assertEqual(result["http_status"], 451)
        self.assertEqual(result["error_type"], "HTTPError")
        self.assertIn("restricted", result["error_message"])


if __name__ == "__main__":
    unittest.main()
