import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.market_selection.research_report import build_research_report
from scripts.market_selection.capture_binance_spot_research import EXCHANGE_INFO_URL, capture_and_build_report
from scripts.market_selection.provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION, evaluate_provider_use
from scripts.market_selection.canonical_asset_identity import SCHEMA_VERSION as IDENTITY_SCHEMA_VERSION


def candle(index, open_price, high, low, close, *, closed=True, quote_volume="1000"):
    opened = index * 3_600_000
    return {
        "open_time_ms": opened,
        "close_time_ms": opened + 3_599_999,
        "open": str(open_price),
        "high": str(high),
        "low": str(low),
        "close": str(close),
        "base_volume": "10",
        "quote_volume": str(quote_volume),
        "trade_count": 10,
        "closed_at_capture": closed,
        "eligible_for_closed_candle_analysis": closed,
    }


def artifact(rows, *, base_asset="BTC", overall_status="PASS"):
    raw = b"preserved OHLCV source response"
    return {
        "schema_version": "binance-spot-ohlcv-capture-v1",
        "provider_use_assessment": {
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "provider_id": "binance_spot_market_data",
            "use_case": "internal_analysis",
            "decision": "ALLOW",
            "reason_codes": ["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization_evidence_status": "RECORD_VALIDATED_NOT_LEGAL_ADVICE",
            "authorization": {"terms_url": "https://www.binance.com/en/terms", "terms_sha256": "a" * 64,
                              "reviewed_at": "2026-10-22T00:00:00Z", "reviewed_by": "offline-test-fixture",
                              "authorized_use_cases": ["internal_analysis"], "authorization_record_sha256": "b" * 64},
        },
        "overall_status": overall_status,
        "market": {
            "exchange": "binance",
            "market_type": "SPOT",
            "symbol_native": "BTCUSDT",
            "base_asset": base_asset,
            "quote_asset": "USDT",
            "symbol_status_at_capture": "TRADING",
            "is_spot_trading_allowed_at_capture": True,
            "market_resolution": {
                "schema_version": "binance-spot-market-candidate-resolution-v1",
                "resolution_status": "UNIQUE_MARKET",
                "candidate_count": 1,
                "selected_market": {
                    "symbol_native": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "status": "TRADING",
                    "is_spot_trading_allowed": True,
                },
                "candidates": [{
                    "symbol_native": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "status": "TRADING",
                    "is_spot_trading_allowed": True,
                }],
            },
            "interval": "1h",
        },
        "window": {
            "start_time_ms_inclusive": rows[0]["open_time_ms"],
            "end_time_ms_exclusive": rows[-1]["open_time_ms"] + 3_600_000,
        },
        "pages": [{
            "capture_status": "PASS",
            "response_base64": base64.b64encode(raw).decode("ascii"),
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }],
        "candles": rows,
    }


def identity_evidence():
    return {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "stable_id": "registry:bitcoin",
        "asset_type": "NATIVE_ASSET",
        "symbol": "BTC",
        "name": "Bitcoin",
        "chain_id": "bitcoin",
        "contract_address": None,
        "resolution": {
            "status": "VERIFIED_UNIQUE",
            "candidate_count": 1,
            "review_status": "APPROVED",
            "reviewed_by": "offline-test-fixture",
            "reviewed_at": "2026-10-22T00:00:00Z",
        },
        "source": {
            "source_type": "AUTHORITATIVE_REGISTRY",
            "url": "https://example.invalid/registry/bitcoin",
            "publisher": "Synthetic fixture only",
            "captured_at": "2026-10-22T00:00:00Z",
            "content_sha256": hashlib.sha256(b"synthetic identity registry content").hexdigest(),
            "content_base64": base64.b64encode(b"synthetic identity registry content").decode("ascii"),
        },
    }


def config():
    return {
        "methodology_id": "technical-descriptive-baseline",
        "methodology_version": "1.0.0",
        "movement": {
            "lookback_bars": 2,
            "return_threshold_pct": 5.0,
            "volume_ratio_threshold": 3.0,
        },
        "support_resistance": {
            "pivot_left": 1,
            "pivot_right": 1,
            "tolerance_bps": 100.0,
        },
    }


class FakeExchangeInfoResponse:
    def __init__(self, raw):
        self.raw = raw
        self.position = 0
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if self.position >= len(self.raw):
            return b""
        end = min(self.position + min(size, 13), len(self.raw))
        chunk = self.raw[self.position:end]
        self.position = end
        return chunk


class ResearchReportTests(unittest.TestCase):
    def setUp(self):
        self.source = artifact([
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8, quote_volume="5000"),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
            candle(5, 9.5, 11, 9, 10.5),
        ])
        self.raw = json.dumps(self.source, ensure_ascii=False, sort_keys=True).encode("utf-8")

    def test_offline_end_to_end_from_base_ticker_to_reproducible_report(self):
        exchange_payload = {
            "symbols": [
                {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT",
                 "status": "TRADING", "isSpotTradingAllowed": True,
                 "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": []},
                {"symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC",
                 "status": "TRADING", "isSpotTradingAllowed": True,
                 "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": []},
            ]
        }
        metadata_raw = json.dumps(exchange_payload, separators=(",", ":")).encode("utf-8")
        allowed_test_assessment = {
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "provider_id": "binance_spot_market_data",
            "use_case": "internal_analysis",
            "decision": "ALLOW",
            "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"],
            "authorization_evidence_status": "SYNTHETIC_TEST_GATE_ONLY",
        }
        with patch(
            "scripts.market_selection.capture_binance_spot_research.urlopen",
            return_value=FakeExchangeInfoResponse(metadata_raw),
        ) as network, patch(
            "scripts.market_selection.capture_binance_spot_research.evaluate_provider_use",
            return_value=allowed_test_assessment,
        ), patch(
            "scripts.market_selection.capture_binance_spot_research.capture_history",
            return_value=self.source,
        ) as candles, patch(
            "scripts.market_selection.research_report.evaluate_artifact_use",
            return_value={
                "decision": "ALLOW",
                "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"],
                "authorization_evidence_status": "SYNTHETIC_TEST_GATE_ONLY",
            },
        ), patch(
            "scripts.market_selection.analyze_ohlcv_risk_profile.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.analyze_support_resistance.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.detect_ohlcv_movement_events.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ):
            captured, report = capture_and_build_report(
                symbol=None,
                base_asset_ticker="BTC",
                quote_asset="USDT",
                interval="1h",
                start_time_ms=0,
                end_time_ms_exclusive=6 * 3_600_000,
                config=config(),
                use_case="internal_analysis",
                requested_identifier_type="symbol",
                requested_asset_identifier="BTC",
            )

        network.assert_called_once()
        self.assertEqual(network.call_args.args[0].full_url, EXCHANGE_INFO_URL)
        candles.assert_called_once_with(
            "BTCUSDT", "1h", 0, 6 * 3_600_000,
            use_case="internal_analysis", authorization_record=None,
        )
        self.assertEqual(captured["artifact"]["market"]["symbol_native"], "BTCUSDT")
        self.assertEqual(captured["artifact"]["market"]["base_asset"], "BTC")
        self.assertEqual(captured["artifact"]["market"]["quote_asset"], "USDT")
        self.assertEqual(report["schema_version"], "crypto-asset-research-report-v2")
        self.assertEqual(report["pipeline"]["market_identity_basis"], "BINANCE_EXCHANGE_INFO_BASE_ASSET_ONLY")
        self.assertEqual(report["canonical_asset_identity_status"], "NOT_RESOLVED")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(set(report["horizons"]), {"short", "medium", "long"})
        self.assertTrue(all(item["status"] == "INDETERMINATE" for item in report["horizons"].values()))
        self.assertFalse(report["orders_submitted"])
        self.assertTrue(report["pipeline"]["capture_artifact_sha256"])
        self.assertEqual(report["pipeline"]["capture_artifact_bytes"], len(captured["raw_bytes"]))

    def test_assembles_existing_analyses_and_abstains_on_all_horizons(self):
        report = build_research_report(self.source, config(), "BTC", self.raw)
        self.assertEqual(report["schema_version"], "crypto-asset-research-report-v2")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(report["decision_status"], "INDETERMINATE")
        self.assertEqual(report["asset_identity_status"], "INDETERMINATE")
        self.assertEqual(report["canonical_asset_identity_status"], "NOT_RESOLVED")
        self.assertEqual(report["market_base_asset_mapping_status"], "VERIFIED")
        self.assertEqual(report["market"]["symbol_native"], "BTCUSDT")
        self.assertEqual(report["market"]["base_asset"], "BTC")
        self.assertEqual(report["market"]["quote_asset"], "USDT")
        self.assertEqual(report["market"]["market_resolution"]["resolution_status"], "UNIQUE_MARKET")
        self.assertEqual(report["source_artifact"]["hash_basis"], "RAW_SOURCE_FILE_BYTES")
        self.assertEqual(report["source_artifact"]["sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertIn("risk_profile", report["descriptive_analyses"])
        self.assertIn("movement_events", report["descriptive_analyses"])
        self.assertIn("support_resistance", report["descriptive_analyses"])
        self.assertEqual(set(report["horizons"]), {"short", "medium", "long"})
        self.assertTrue(all(h["status"] == "INDETERMINATE" for h in report["horizons"].values()))
        self.assertFalse(report["event_causal_assessment"]["causality_claimed"])
        self.assertFalse(report["orders_submitted"])
        self.assertFalse(report["network_requests_made"])

    def test_reviewed_unique_identity_evidence_verifies_canonical_asset(self):
        report = build_research_report(self.source, config(), "BTC", self.raw, identity_evidence=identity_evidence())
        self.assertEqual(report["asset_identity_status"], "VERIFIED")
        self.assertEqual(report["canonical_asset_identity_status"], "VERIFIED")
        self.assertEqual(report["market_base_asset_mapping_status"], "VERIFIED")
        self.assertEqual(report["canonical_asset_identity"]["stable_id"], "registry:bitcoin")
        self.assertRegex(report["canonical_asset_identity"]["identity_evidence"]["identity_evidence_record_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(report["report_status"], "TECHNICAL_BASELINE_ASSEMBLED")

    def test_technical_test_capture_cannot_be_used_for_internal_analysis(self):
        source = dict(self.source)
        source["provider_use_assessment"] = evaluate_provider_use("binance_spot_market_data", "live_technical_test")
        with self.assertRaisesRegex(PermissionError, "blocked before analysis"):
            build_research_report(source, config(), "BTC")

    def test_missing_provider_assessment_blocks_report(self):
        source = dict(self.source)
        source.pop("provider_use_assessment")
        with self.assertRaisesRegex(PermissionError, "blocked before analysis"):
            build_research_report(source, config(), "BTC")

    def test_source_bytes_must_match_the_analyzed_artifact(self):
        with self.assertRaisesRegex(ValueError, "do not match"):
            build_research_report(self.source, config(), "BTC", b'{}')

    def test_missing_asset_identity_is_indeterminate_not_inferred_from_ticker(self):
        source = artifact(self.source["candles"], base_asset=None)
        source["market"].pop("base_asset")
        report = build_research_report(source, config(), "BTC")
        self.assertEqual(report["asset_identity_status"], "INDETERMINATE")
        self.assertEqual(report["canonical_asset_identity_status"], "NOT_RESOLVED")
        self.assertEqual(report["market_base_asset_mapping_status"], "INDETERMINATE")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(report["decision_status"], "INDETERMINATE")

    def test_mismatched_asset_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "canonical asset identity evidence conflicts"):
            build_research_report(self.source, config(), "ETH")

    def test_partial_capture_is_not_reported_complete(self):
        source = artifact(self.source["candles"], overall_status="PARTIAL")
        report = build_research_report(source, config(), "BTC")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(report["data_quality"]["status"], "INCOMPLETE_OR_UNVERIFIED")
        self.assertEqual(report["source_artifact"]["capture_status"], "PARTIAL")

    def test_cli_end_to_end_writes_a_report_from_preserved_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact_path = root / "ohlcv.json"
            config_path = root / "methodology.json"
            output_path = root / "report.json"
            identity_path = root / "identity.json"
            artifact_path.write_text(json.dumps(self.source, sort_keys=True), encoding="utf-8")
            config_path.write_text(json.dumps(config(), sort_keys=True), encoding="utf-8")
            identity_path.write_text(json.dumps(identity_evidence(), sort_keys=True), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.market_selection.research_report",
                    "--asset-id",
                    "BTC",
                    "--artifact",
                    str(artifact_path),
                    "--config",
                    str(config_path),
                    "--output",
                    str(output_path),
                    "--identity-evidence",
                    str(identity_path),
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "crypto-asset-research-report-v2")
            self.assertEqual(
                report["source_artifact"]["sha256"],
                hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(report["decision_status"], "INDETERMINATE")
            self.assertEqual(report["asset_identity_status"], "VERIFIED")
            self.assertEqual(report["canonical_asset_identity_status"], "VERIFIED")
            self.assertEqual(report["canonical_asset_identity"]["stable_id"], "registry:bitcoin")
            self.assertEqual(set(report["horizons"]), {"short", "medium", "long"})

    def test_missing_explicit_method_parameter_is_rejected(self):
        invalid = config()
        invalid["movement"].pop("return_threshold_pct")
        with self.assertRaisesRegex(ValueError, "return_threshold_pct is required"):
            build_research_report(self.source, invalid, "BTC")

    def test_methodology_config_rejects_invalid_integer_parameters(self):
        cases = [
            (("movement", "lookback_bars"), 0, "lookback_bars must be a positive integer"),
            (("movement", "lookback_bars"), True, "lookback_bars must be a positive integer"),
            (("support_resistance", "pivot_left"), 1.5, "pivot_left must be a positive integer"),
            (("support_resistance", "pivot_right"), False, "pivot_right must be a positive integer"),
        ]
        for (section, key), value, message in cases:
            with self.subTest(section=section, key=key, value=value):
                invalid = config()
                invalid[section][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    build_research_report(self.source, invalid, "BTC")

    def test_methodology_config_rejects_nonpositive_or_nonfinite_thresholds(self):
        cases = [
            (("movement", "return_threshold_pct"), 0, "return_threshold_pct must be a finite number greater than zero"),
            (("movement", "return_threshold_pct"), float("inf"), "return_threshold_pct must be a finite number greater than zero"),
            (("movement", "volume_ratio_threshold"), float("nan"), "volume_ratio_threshold must be a finite number greater than zero"),
            (("movement", "volume_ratio_threshold"), True, "volume_ratio_threshold must be a finite number greater than zero"),
            (("support_resistance", "tolerance_bps"), -1, "tolerance_bps must be a finite number from 0 to 10000"),
            (("support_resistance", "tolerance_bps"), 10001, "tolerance_bps must be a finite number from 0 to 10000"),
        ]
        for (section, key), value, message in cases:
            with self.subTest(section=section, key=key, value=value):
                invalid = config()
                invalid[section][key] = value
                with self.assertRaisesRegex(ValueError, message):
                    build_research_report(self.source, invalid, "BTC")


if __name__ == "__main__":
    unittest.main()
