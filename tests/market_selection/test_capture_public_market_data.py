import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_market_data import request_capture


class Response:
    def __init__(self, payload):
        self.status = 200
        self.headers = {}
        self.payload = json.dumps(payload, separators=(",", ":")).encode()
        self.calls = []
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        self.calls.append(size)
        if size is None or size < 0:
            chunk = self.payload[self.offset:]
            self.offset = len(self.payload)
            return chunk
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class CompleteResponseTests(unittest.TestCase):
    def test_large_binance_metadata_is_preserved(self):
        payload = {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING", "isSpotTradingAllowed": True}], "padding": "x" * (5 * 1024 * 1024 + 128)}
        response = Response(payload)
        with patch("scripts.market_selection.capture_public_market_data.urlopen", return_value=response):
            record = request_capture("binance_exchange_info", "https://example.invalid")
        raw = base64.b64decode(record["response_base64"], validate=True)
        self.assertGreater(len(raw), 5 * 1024 * 1024)
        self.assertGreater(len(response.calls), 1)
        self.assertTrue(all(size == 64 * 1024 for size in response.calls))
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["response_bytes"], len(raw))
        self.assertEqual(record["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw), payload)
        self.assertEqual(record["parsed_json"], payload)


if __name__ == "__main__":
    unittest.main()
