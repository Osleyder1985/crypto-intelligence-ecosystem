"""Deterministic tests for exact Pionex Spot symbol availability."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

import pionex_public  # noqa: E402


def response(symbol="BTC_USDT", enabled=True, market_type="SPOT", base="BTC", quote="USDT", timestamp=1792368000000):
    symbols = [] if symbol is None else [{
        "symbol": symbol, "type": market_type, "baseCurrency": base,
        "quoteCurrency": quote, "enable": enabled,
    }]
    return json.dumps({"result": True, "timestamp": timestamp, "data": {"symbols": symbols}}).encode()


class PionexPublicSpotReaderTests(unittest.TestCase):
    def make_reader(self, payload, calls=None):
        return pionex_public.PionexPublicSpotReader(
            http_get=lambda url, timeout: (calls.append(url) if calls is not None else None) or payload,
            clock=lambda: "2026-10-19T00:00:01Z",
        )

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
