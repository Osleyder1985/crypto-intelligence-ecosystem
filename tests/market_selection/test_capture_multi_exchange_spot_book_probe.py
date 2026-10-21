import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from scripts.market_selection.capture_multi_exchange_spot_book_probe import (
    SCHEMA_VERSION, MAX_BYTES, ResponseTooLarge, build_requests, capture_one, extract_top_of_book,
)


class MultiExchangeSpotBookProbeTests(unittest.TestCase):
    def test_probe_covers_four_exchanges_and_three_assets(self):
        requests = build_requests()
        self.assertEqual(len(requests), 12)
        self.assertEqual({r["exchange"] for r in requests},
                         {"okx", "bybit", "coinbase_exchange", "kraken"})
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

    def test_kraken_response_contract(self):
        bids, asks, timestamp = extract_top_of_book("kraken", {
            "error": [], "result": {"XXBTZUSD": {"bids": [["100", "2", "1"]], "asks": [["101", "3", "1"]]}}
        })
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertIsNone(timestamp)

    def test_coinbase_response_contract(self):
        bids, asks, timestamp = extract_top_of_book("coinbase_exchange", {
            "bids": [["100", "2", 1]], "asks": [["101", "3", 1]], "time": "2026-10-21T00:00:00Z"
        })
        self.assertEqual(bids[0][0], "100")
        self.assertEqual(asks[0][0], "101")
        self.assertEqual(timestamp, "2026-10-21T00:00:00Z")

    def test_response_limit_records_exact_boundary_and_overflow(self):
        class FakeResponse:
            status = 200
            headers = {"Content-Length": str(MAX_BYTES)}
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size=-1): return self.body[:size]
        spec = build_requests()[0]
        exact = FakeResponse(b"x" * MAX_BYTES)
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", return_value=exact):
            result = capture_one(spec)
        self.assertEqual(result["response_bytes"], MAX_BYTES)
        self.assertEqual(result["capture_status"], "FAIL")
        large = FakeResponse(b"x" * (MAX_BYTES + 1))
        large.headers = {"Content-Length": str(MAX_BYTES + 1)}
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", return_value=large):
            result = capture_one(spec)
        self.assertEqual(result["capture_status"], "FAIL")
        self.assertEqual(result["response_bytes_observed"], MAX_BYTES + 1)
        self.assertEqual(result["response_limit_bytes"], MAX_BYTES)
        self.assertEqual(result["content_length_header"], str(MAX_BYTES + 1))
        self.assertEqual(len(result["oversize_prefix_sha256"]), 64)
        self.assertIsNone(result["response_base64"])
    def test_http_error_is_recorded_not_raised(self):
        spec = build_requests()[0]
        error = HTTPError(spec["url"], 451, "restricted", {}, BytesIO(b"blocked"))
        with patch("scripts.market_selection.capture_multi_exchange_spot_book_probe.urlopen", side_effect=error):
            result = capture_one(spec)
        self.assertEqual(result["capture_status"], "FAIL")
        self.assertEqual(result["http_status"], None)
        self.assertEqual(result["error_type"], "HTTPError")
        self.assertIn("restricted", result["error_message"])


if __name__ == "__main__":
    unittest.main()
