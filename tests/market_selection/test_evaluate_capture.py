"""Tests for deterministic evaluation of preserved public market captures."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

from evaluate_capture import evaluate_capture  # noqa: E402


def record(provider, payload, captured="2026-10-20T03:00:00Z"):
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return {
        "provider": provider,
        "capture_status": "PASS",
        "http_status": 200,
        "response_base64": base64.b64encode(raw).decode(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "parsed_json": json.loads(raw),
        "captured_at_utc": captured,
    }


def fixture():
    return {
        "schema_version": "public-market-capture-v1",
        "created_at_utc": "2026-10-20T03:00:00Z",
        "overall_status": "PASS",
        "records": [
            record("pionex", {"result": True, "data": {"symbols": [{
                "symbol": "BTC_USDT", "type": "SPOT", "baseCurrency": "BTC",
                "quoteCurrency": "USDT", "enable": True,
            }]}}),
            record("binance_exchange_info", {"symbols": [{
                "symbol": "BTCUSDT", "status": "TRADING", "isSpotTradingAllowed": True,
                "baseAsset": "BTC", "quoteAsset": "USDT",
            }]}),
            record("binance_depth", {
                "lastUpdateId": 123,
                "bids": [["99.9", "2"], ["99.0", "3"]],
                "asks": [["100.1", "2"], ["101.0", "3"]],
            }),
        ],
    }


class EvaluateCaptureTests(unittest.TestCase):
    def test_metrics_are_reproducible_without_network_or_policy(self):
        source = fixture()
        first = evaluate_capture(source)
        second = evaluate_capture(source)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first["metrics"]["spread_bps"], 20.0)
        self.assertEqual(first["dimension_status"]["pionex_availability"], "PASS")
        self.assertEqual(first["dimension_status"]["binance_spot_market"], "PASS")
        self.assertEqual(first["dimension_status"]["source_freshness"], "INDETERMINATE")
        self.assertEqual(first["decision_status"], "INDETERMINATE")
        self.assertFalse(first["network_requests_made"])
        self.assertFalse(first["orders_submitted"])

    def test_optional_depth_and_slippage_scenario_inputs(self):
        result = evaluate_capture(fixture(), {
            "depth_band_bps": 150.0,
            "min_depth_quote": 100.0,
            "order_size_base": 1.0,
            "max_slippage_bps": 30.0,
            "max_spread_bps": 30.0,
        })
        self.assertEqual(result["dimension_status"]["depth"], "PASS")
        self.assertEqual(result["dimension_status"]["slippage"], "PASS")
        self.assertEqual(result["dimension_status"]["spread"], "PASS")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_raw_byte_hash_mismatch_is_rejected(self):
        source = fixture()
        source["records"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            evaluate_capture(source)

    def test_parsed_payload_cannot_diverge_from_preserved_bytes(self):
        source = fixture()
        source["records"][0]["parsed_json"]["result"] = False
        with self.assertRaisesRegex(ValueError, "does not match"):
            evaluate_capture(source)

    def test_incomplete_depth_does_not_claim_slippage_pass(self):
        source = fixture()
        depth = source["records"][2]
        depth["parsed_json"]["bids"] = [["99.9", "0.01"]]
        raw = json.dumps(depth["parsed_json"], separators=(",", ":"), sort_keys=True).encode()
        depth["response_base64"] = base64.b64encode(raw).decode()
        depth["response_sha256"] = hashlib.sha256(raw).hexdigest()
        depth["response_bytes"] = len(raw)
        result = evaluate_capture(source, {"order_size_base": 1.0, "max_slippage_bps": 20.0})
        self.assertEqual(result["dimension_status"]["slippage"], "INDETERMINATE")

    def test_boolean_is_not_accepted_as_numeric_scenario_input(self):
        with self.assertRaisesRegex(ValueError, "positive finite number"):
            evaluate_capture(fixture(), {"order_size_base": True})

    def test_crossed_book_is_rejected(self):
        source = fixture()
        depth = source["records"][2]
        depth["parsed_json"]["bids"] = [["101", "2"]]
        depth["parsed_json"]["asks"] = [["100", "2"]]
        raw = json.dumps(depth["parsed_json"], separators=(",", ":"), sort_keys=True).encode()
        depth["response_base64"] = base64.b64encode(raw).decode()
        depth["response_sha256"] = hashlib.sha256(raw).hexdigest()
        depth["response_bytes"] = len(raw)
        with self.assertRaisesRegex(ValueError, "crossed"):
            evaluate_capture(source)


if __name__ == "__main__":
    unittest.main()
