"""Regression tests proving provider denials happen before network access."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.market_selection import binance_depth_transport
from scripts.market_selection import capture_binance_regional_rest_diagnostic as regional


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
