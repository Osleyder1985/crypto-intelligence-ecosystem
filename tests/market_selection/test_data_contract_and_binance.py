"""Deterministic tests for normalized market data and the public Binance reader."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

import binance_public  # noqa: E402
import data_contract  # noqa: E402


def depth_payload() -> bytes:
    return json.dumps({
        "lastUpdateId": 123456,
        "bids": [["100.0", "2.0"], ["99.0", "3.0"]],
        "asks": [["101.0", "4.0"], ["102.0", "5.0"]],
    }, separators=(",", ":")).encode()


def exchange_info_payload(symbol="BTCUSDT", status="TRADING", spot=True) -> bytes:
    return json.dumps({"symbols": [{
        "symbol": symbol, "status": status, "isSpotTradingAllowed": spot,
        "baseAsset": "BTC", "quoteAsset": "USDT",
    }]}).encode()


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = {
            "contract_version": data_contract.CONTRACT_VERSION,
            "observation_id": "test-observation-1",
            "exchange_id": "binance",
            "market_type": "spot",
            "symbol_native": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
            "source_kind": "order_book_snapshot",
            "source_ref": "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=100",
            "source_timestamp_utc": None,
            "captured_at_utc": "2026-10-19T12:00:00Z",
            "payload_sha256": "a" * 64,
            "parser_version": "test-v1",
            "quality_status": "VALID",
            "limitations": [],
            "bids": [{"price": 100.0, "quantity": 1.0}],
            "asks": [{"price": 101.0, "quantity": 1.0}],
        }

    def test_valid_record_has_no_structural_errors(self) -> None:
        self.assertEqual(data_contract.validate_observation(self.record), [])

    def test_unknown_assets_require_indeterminate_quality(self) -> None:
        self.record["base_asset"] = None
        self.record["quote_asset"] = None
        self.record["quality_status"] = "INDETERMINATE"
        self.record["limitations"] = ["asset metadata not joined"]
        self.assertEqual(data_contract.validate_observation(self.record), [])
        self.record["quality_status"] = "VALID"
        self.assertTrue(any("asset metadata cannot be unknown" in e for e in data_contract.validate_observation(self.record)))

    def test_rejects_naive_timestamp(self) -> None:
        self.record["captured_at_utc"] = "2026-10-19T12:00:00"
        self.assertTrue(any("explicit timezone" in e for e in data_contract.validate_observation(self.record)))

    def test_rejects_duplicate_levels(self) -> None:
        self.record["bids"] = [{"price": 100.0, "quantity": 1.0}, {"price": 100.0, "quantity": 2.0}]
        self.assertTrue(any("duplicate price" in e for e in data_contract.validate_observation(self.record)))

    def test_hash_uses_exact_raw_bytes(self) -> None:
        raw = b'{"b":2, "a":1}'
        self.assertEqual(data_contract.sha256_hex(raw), hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(data_contract.sha256_hex(raw), data_contract.canonical_payload_hash({"b": 2, "a": 1}))


class BinanceReaderTests(unittest.TestCase):
    def test_depth_is_normalized_and_explicitly_indeterminate_without_source_timestamp(self) -> None:
        reader = binance_public.BinancePublicSpotReader(
            http_get=lambda url, timeout: depth_payload(),
            clock=lambda: "2026-10-19T12:00:00Z",
        )
        record = reader.fetch_order_book("BTCUSDT")
        self.assertEqual(record["market_type"], "spot")
        self.assertEqual(record["bids"][0], {"price": 100.0, "quantity": 2.0})
        self.assertIsNone(record["source_timestamp_utc"])
        self.assertEqual(record["quality_status"], "INDETERMINATE")
        self.assertEqual(record["payload_sha256"], hashlib.sha256(depth_payload()).hexdigest())
        self.assertFalse(record["raw_payload_retained"])
        self.assertEqual(data_contract.validate_observation(record), [])

    def test_rejects_invalid_symbol_before_http_call(self) -> None:
        calls = []
        reader = binance_public.BinancePublicSpotReader(http_get=lambda url, timeout: calls.append(url) or depth_payload())
        with self.assertRaises(ValueError):
            reader.fetch_order_book("BTC/USDT")
        self.assertEqual(calls, [])

    def test_rejects_malformed_json(self) -> None:
        reader = binance_public.BinancePublicSpotReader(http_get=lambda url, timeout: b"{not-json")
        with self.assertRaisesRegex(binance_public.ExchangeReadError, "invalid UTF-8 JSON"):
            reader.fetch_order_book("BTCUSDT")

    def test_rejects_api_error_payload(self) -> None:
        reader = binance_public.BinancePublicSpotReader(
            http_get=lambda url, timeout: b'{"code":-1003,"msg":"Too many requests"}'
        )
        with self.assertRaisesRegex(binance_public.ExchangeReadError, "API error -1003"):
            reader.fetch_order_book("BTCUSDT")

    def test_rejects_duplicate_prices(self) -> None:
        payload = json.dumps({
            "lastUpdateId": 1, "bids": [["100", "1"], ["100", "2"]], "asks": [["101", "1"]]
        }).encode()
        reader = binance_public.BinancePublicSpotReader(http_get=lambda url, timeout: payload)
        with self.assertRaisesRegex(binance_public.ExchangeReadError, "duplicate price"):
            reader.fetch_order_book("BTCUSDT")

    def test_rejects_crossed_book(self) -> None:
        payload = json.dumps({
            "lastUpdateId": 1, "bids": [["102", "1"]], "asks": [["101", "1"]]
        }).encode()
        reader = binance_public.BinancePublicSpotReader(http_get=lambda url, timeout: payload)
        with self.assertRaisesRegex(binance_public.ExchangeReadError, "crossed"):
            reader.fetch_order_book("BTCUSDT")

    def test_exact_symbol_status_confirmed(self) -> None:
        reader = binance_public.BinancePublicSpotReader(
            http_get=lambda url, timeout: exchange_info_payload(),
            clock=lambda: "2026-10-19T12:00:00Z",
        )
        result = reader.fetch_spot_symbol_status("BTCUSDT")
        self.assertEqual(result["availability_status"], "confirmed")
        self.assertEqual(result["payload_sha256"], hashlib.sha256(exchange_info_payload()).hexdigest())

    def test_non_trading_symbol_is_unavailable(self) -> None:
        reader = binance_public.BinancePublicSpotReader(
            http_get=lambda url, timeout: exchange_info_payload(status="BREAK"),
            clock=lambda: "2026-10-19T12:00:00Z",
        )
        self.assertEqual(reader.fetch_spot_symbol_status("BTCUSDT")["availability_status"], "unavailable")

    def test_empty_exact_symbol_result_is_unavailable(self) -> None:
        reader = binance_public.BinancePublicSpotReader(
            http_get=lambda url, timeout: b'{"symbols":[]}',
            clock=lambda: "2026-10-19T12:00:00Z",
        )
        self.assertEqual(reader.fetch_spot_symbol_status("BTCUSDT")["availability_status"], "unavailable")

    def test_reader_has_no_order_submission_method(self) -> None:
        self.assertFalse(hasattr(binance_public.BinancePublicSpotReader, "place_order"))
        self.assertFalse(hasattr(binance_public.BinancePublicSpotReader, "create_order"))


if __name__ == "__main__":
    unittest.main()
