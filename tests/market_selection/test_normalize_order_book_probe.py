import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.normalize_order_book_probe import (
    normalize_multi_exchange_order_book_probe,
)
from scripts.market_selection.capture_multi_exchange_spot_book_probe import SCHEMA_VERSION


def probe_artifact():
    payload = {
        "lastUpdateId": 123,
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "1"], ["102", "4"]],
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    record = {
        "exchange": "binance",
        "asset": "BTC",
        "symbol": "BTCUSDT",
        "url": "https://data-api.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=100",
        "capture_status": "PASS",
        "http_status": 200,
        "error_type": None,
        "captured_at_utc": "2026-10-22T00:00:00Z",
        "response_bytes": len(raw),
        "response_base64": base64.b64encode(raw).decode("ascii"),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "parsed_json": payload,
        "provider_use_assessment": {"decision": "ALLOW", "use_case": "persistent_storage"},
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "overall_status": "PARTIAL",
        "records": [record],
    }


class NormalizeOrderBookProbeTests(unittest.TestCase):
    def test_normalizes_verified_selected_record_with_trusted_internal_use(self):
        with patch(
            "scripts.market_selection.normalize_order_book_probe.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ):
            result = normalize_multi_exchange_order_book_probe(
                probe_artifact(),
                exchange="BINANCE",
                symbol="btcusdt",
                authorization_registry={"binance_spot_market_data": {"trusted": True}},
            )
        self.assertEqual(result["schema_version"], "crypto-spot-order-book-snapshot-v1")
        self.assertEqual(result["market"]["symbol_native"], "BTCUSDT")
        self.assertEqual(result["market"]["quote_asset"], "USDT")
        self.assertEqual(result["bids"][0], ["99", "2"])
        self.assertEqual(result["capture_evidence"]["source_response_integrity"], "VERIFIED")
        self.assertEqual(result["source_capture_status"], "PARTIAL")
        self.assertFalse(result["orders_submitted"])

    def test_rejects_missing_trusted_authorization(self):
        with self.assertRaises(PermissionError):
            normalize_multi_exchange_order_book_probe(
                probe_artifact(), exchange="binance", symbol="BTCUSDT",
            )

    def test_rejects_ambiguous_or_missing_record(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            normalize_multi_exchange_order_book_probe(
                probe_artifact(), exchange="binance", symbol="ETHUSDT",
                authorization_registry={"binance_spot_market_data": {"trusted": True}},
            )

    def test_rejects_tampered_preserved_response(self):
        artifact = probe_artifact()
        artifact["records"][0]["response_base64"] = base64.b64encode(b'{"bids":[],"asks":[]}').decode("ascii")
        with patch(
            "scripts.market_selection.normalize_order_book_probe.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": []},
        ):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                normalize_multi_exchange_order_book_probe(
                    artifact, exchange="binance", symbol="BTCUSDT",
                    authorization_registry={"binance_spot_market_data": {"trusted": True}},
                )

    def test_rejects_record_url_not_matching_registered_market(self):
        artifact = probe_artifact()
        artifact["records"][0]["url"] = "https://data-api.binance.vision/api/v3/depth?symbol=ETHUSDT&limit=100"
        with patch(
            "scripts.market_selection.normalize_order_book_probe.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": []},
        ):
            with self.assertRaisesRegex(ValueError, "URL or asset"):
                normalize_multi_exchange_order_book_probe(
                    artifact, exchange="binance", symbol="BTCUSDT",
                    authorization_registry={"binance_spot_market_data": {"trusted": True}},
                )

    def test_rejects_parsed_payload_not_matching_preserved_bytes(self):
        artifact = probe_artifact()
        artifact["records"][0]["parsed_json"]["lastUpdateId"] = 999
        with patch(
            "scripts.market_selection.normalize_order_book_probe.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": []},
        ):
            with self.assertRaisesRegex(ValueError, "does not match"):
                normalize_multi_exchange_order_book_probe(
                    artifact, exchange="binance", symbol="BTCUSDT",
                    authorization_registry={"binance_spot_market_data": {"trusted": True}},
                )


if __name__ == "__main__":
    unittest.main()
