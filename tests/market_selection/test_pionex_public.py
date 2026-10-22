"""Deterministic tests for exact Pionex Spot symbol availability."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

import pionex_public  # noqa: E402
from scripts.market_selection.provider_license_gate import SCHEMA_VERSION

PIONEX_AUTHORIZATION_RECORD = {
    "schema_version": SCHEMA_VERSION,
    "provider_id": "pionex_spot_market_data",
    "status": "APPROVED",
    "authorized_use_cases": ["internal_analysis"],
    "terms_url": "https://www.pionex.com/terms",
    "terms_sha256": "b" * 64,
    "reviewed_at": "2026-10-22T00:00:00Z",
    "reviewed_by": "offline-test-fixture",
}


def response(symbol="BTC_USDT", enabled=True, market_type="SPOT", base="BTC", quote="USDT", timestamp=1792368000000):
    symbols = [] if symbol is None else [{
        "symbol": symbol, "type": market_type, "baseCurrency": base,
        "quoteCurrency": quote, "enable": enabled,
    }]
    return json.dumps({"result": True, "timestamp": timestamp, "data": {"symbols": symbols}}).encode()


class ChunkedHTTPResponse:
    status = 200

    def __init__(self, body: bytes):
        self.body = body
        self.offset = 0
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        self.read_sizes.append(size)
        if size is None or size < 0:
            chunk = self.body[self.offset:]
            self.offset = len(self.body)
            return chunk
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class PionexPublicSpotReaderTests(unittest.TestCase):
    def make_reader(self, payload, calls=None):
        return pionex_public.PionexPublicSpotReader(
            http_get=lambda url, timeout: (calls.append(url) if calls is not None else None) or payload,
            clock=lambda: "2026-10-19T00:00:01Z",
            authorization_record=PIONEX_AUTHORIZATION_RECORD,
        )

    def test_response_larger_than_five_mib_is_fully_read_and_parsed(self):
        payload = json.loads(response())
        payload["padding"] = "x" * (5 * 1024 * 1024 + 128)
        raw = json.dumps(payload, separators=(",", ":")).encode()
        transport = ChunkedHTTPResponse(raw)
        with patch.object(pionex_public, "urlopen", return_value=transport):
            transported = pionex_public._default_http_get("https://example.invalid", 10.0, PIONEX_AUTHORIZATION_RECORD)
        self.assertEqual(transported, raw)
        self.assertGreater(len(transport.read_sizes), 1)
        self.assertTrue(all(size == 64 * 1024 for size in transport.read_sizes))
        result = self.make_reader(transported).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "confirmed")
        self.assertEqual(result["payload_sha256"], hashlib.sha256(raw).hexdigest())

    def test_exact_enabled_spot_pair_is_confirmed(self):
        raw = response()
        result = self.make_reader(raw).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "confirmed")
        self.assertEqual(result["freshness_status"], "PASS")
        self.assertEqual(result["base_asset"], "BTC")
        self.assertEqual(result["quote_asset"], "USDT")
        self.assertEqual(result["payload_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(result["raw_payload_retained"])

    def test_missing_symbol_is_unavailable(self):
        result = self.make_reader(response(symbol=None)).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "unavailable")
        self.assertIsNone(result["detail"])

    def test_disabled_symbol_is_unavailable(self):
        result = self.make_reader(response(enabled=False)).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "unavailable")

    def test_non_spot_symbol_is_unavailable(self):
        result = self.make_reader(response(market_type="PERP")).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "unavailable")

    def test_mismatched_base_or_quote_metadata_is_rejected(self):
        reader = self.make_reader(response(base="ETH"))
        with self.assertRaisesRegex(pionex_public.PionexReadError, "does not match"):
            reader.check_spot_symbol("BTC_USDT")

    def test_missing_authorization_blocks_before_transport(self):
        calls = []
        reader = pionex_public.PionexPublicSpotReader(http_get=lambda url, timeout: calls.append(url) or response())
        with self.assertRaisesRegex(pionex_public.PionexReadError, "provider use blocked before network"):
            reader.check_spot_symbol("BTC_USDT")
        self.assertEqual(calls, [])

    def test_invalid_symbol_never_calls_transport(self):
        calls = []
        reader = self.make_reader(response(), calls)
        with self.assertRaises(ValueError):
            reader.check_spot_symbol("BTCUSDT")
        self.assertEqual(calls, [])

    def test_api_failure_and_invalid_json_are_not_treated_as_unavailable(self):
        with self.assertRaisesRegex(pionex_public.PionexReadError, "result is missing"):
            self.make_reader(b'{"result":false}').check_spot_symbol("BTC_USDT")
        with self.assertRaisesRegex(pionex_public.PionexReadError, "invalid UTF-8 JSON"):
            self.make_reader(b"{invalid").check_spot_symbol("BTC_USDT")

    def test_missing_timestamp_does_not_invent_freshness(self):
        raw = b'{"result":true,"data":{"symbols":[{"symbol":"BTC_USDT","type":"SPOT","baseCurrency":"BTC","quoteCurrency":"USDT","enable":true}]}}'
        result = self.make_reader(raw).check_spot_symbol("BTC_USDT")
        self.assertEqual(result["availability_status"], "confirmed")
        self.assertEqual(result["freshness_status"], "INDETERMINATE")
        self.assertIsNone(result["source_timestamp_utc"])

    def test_reader_has_no_order_submission_method(self):
        self.assertFalse(hasattr(pionex_public.PionexPublicSpotReader, "place_order"))
        self.assertFalse(hasattr(pionex_public.PionexPublicSpotReader, "create_order"))


if __name__ == "__main__":
    unittest.main()
