"""Regression tests proving provider denials happen before network access."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.market_selection import binance_depth_transport
from scripts.market_selection import capture_binance_regional_rest_diagnostic as regional
from scripts.market_selection import capture_binance_account_commission_evidence as binance_account
from scripts.market_selection import capture_pionex_fill_fee_evidence as pionex_account


BLOCKED = {
    "decision": "BLOCK",
    "reason_codes": ["AUTHORIZATION_RECORD_MISSING"],
    "provider_id": "binance_spot_market_data",
    "use_case": "internal_analysis",
}


class ProviderLicenseEnforcementTests(unittest.TestCase):
    def test_depth_snapshot_denial_precedes_http_request(self) -> None:
        with (
            patch.object(binance_depth_transport, "evaluate_provider_use", return_value=BLOCKED),
            patch.object(binance_depth_transport, "urlopen", side_effect=AssertionError("network must not be called")),
        ):
            with self.assertRaises(PermissionError):
                binance_depth_transport.fetch_public_depth_snapshot("BTCUSDT")

    def test_depth_stream_denial_precedes_websocket_connection(self) -> None:
        with (
            patch.object(binance_depth_transport, "evaluate_provider_use", return_value=BLOCKED),
            patch.object(binance_depth_transport, "_open_public_stream", side_effect=AssertionError("socket must not be opened")),
        ):
            with self.assertRaises(PermissionError):
                binance_depth_transport.capture_once("BTCUSDT")

    def test_regional_diagnostic_denial_precedes_http_request(self) -> None:
        venue = {
            "venue": "binance_global_market_data_only",
            "base_url": "https://data-api.binance.vision",
            "docs": "https://github.com/binance/binance-spot-api-docs",
        }
        with (
            patch.object(regional, "evaluate_provider_use", return_value=BLOCKED),
            patch.object(regional, "request_json", side_effect=AssertionError("network must not be called")),
        ):
            result = regional.capture_endpoint(
                venue, "server_time", "https://data-api.binance.vision/api/v3/time"
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertEqual(result["provider_use_assessment"]["decision"], "BLOCK")

    def test_binance_private_account_denial_precedes_http_request(self) -> None:
        with patch.object(binance_account, "urlopen", side_effect=AssertionError("network must not be called")):
            with self.assertRaises(PermissionError):
                binance_account.capture_commission_evidence("BTCUSDT", "key", "secret")

    def test_pionex_private_account_denial_precedes_http_request(self) -> None:
        with patch.object(pionex_account, "urlopen", side_effect=AssertionError("network must not be called")):
            with self.assertRaises(PermissionError):
                pionex_account.capture("BTC_USDT", "USDT", 1, 2, "key", "secret")

    def test_pionex_private_account_capture_runs_only_with_explicit_authorization(self) -> None:
        import json
        from scripts.market_selection.provider_license_gate import SCHEMA_VERSION

        authorization = {
            "schema_version": SCHEMA_VERSION,
            "provider_id": "pionex_spot_account_data",
            "status": "APPROVED",
            "authorized_use_cases": ["internal_analysis"],
            "terms_url": "https://www.pionex.com/terms",
            "terms_sha256": "c" * 64,
            "reviewed_at": "2026-10-22T00:00:00Z",
            "reviewed_by": "offline-test-fixture",
            "account_owner_consent_ref": "offline-pionex-consent-fixture",
            "account_owner_consent_sha256": "d" * 64,
            "credential_scope_verified": True,
        }
        raw = json.dumps({
            "result": True, "timestamp": 1200,
            "data": {"fills": [{
                "symbol": "BTC_USDT", "side": "BUY", "role": "TAKER",
                "price": "100", "size": "0.01", "fee": "0.0005",
                "feeCoin": "USDT", "timestamp": 1000,
            }]},
        }).encode("utf-8")

        class FakeResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self): return raw

        with patch.object(pionex_account, "urlopen", return_value=FakeResponse()) as transport:
            result = pionex_account.capture(
                "BTC_USDT", "USDT", 1, 2000, "key", "secret",
                authorization_record=authorization,
            )
        transport.assert_called_once()
        self.assertEqual(result["provider_use_assessment"]["decision"], "ALLOW")
        self.assertEqual(result["fills_count"], 1)

    def test_private_account_gate_requires_owner_consent_and_verified_credential_scope(self) -> None:
        from scripts.market_selection.provider_license_gate import evaluate_provider_use, SCHEMA_VERSION
        record = {
            "schema_version": SCHEMA_VERSION,
            "provider_id": "binance_spot_account_data",
            "status": "APPROVED",
            "authorized_use_cases": ["internal_analysis"],
            "terms_url": "https://www.binance.com/en/terms",
            "terms_sha256": "a" * 64,
            "reviewed_at": "2026-10-22T00:00:00Z",
            "reviewed_by": "test-reviewer",
            "account_owner_consent_ref": "consent-record-test-reference",
            "account_owner_consent_sha256": "b" * 64,
            "credential_scope_verified": True,
        }
        result = evaluate_provider_use("binance_spot_account_data", "internal_analysis", record)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["authorization"]["account_owner_consent_ref"], "consent-record-test-reference")
        self.assertEqual(result["authorization"]["account_owner_consent_sha256"], "b" * 64)
        record["credential_scope_verified"] = False
        with self.assertRaises(ValueError):
            evaluate_provider_use("binance_spot_account_data", "internal_analysis", record)

    def test_gate_allows_only_explicitly_classified_technical_test_by_default(self) -> None:
        from scripts.market_selection.provider_license_gate import evaluate_provider_use

        self.assertEqual(
            evaluate_provider_use("binance_spot_market_data", "live_technical_test")["decision"],
            "ALLOW",
        )
        self.assertEqual(
            evaluate_provider_use("binance_spot_market_data", "internal_analysis")["decision"],
            "BLOCK",
        )


if __name__ == "__main__":
    unittest.main()
