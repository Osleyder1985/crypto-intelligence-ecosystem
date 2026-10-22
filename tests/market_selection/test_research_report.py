import base64
import hashlib
import json
import unittest

from scripts.market_selection.research_report import build_research_report


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
        "overall_status": overall_status,
        "market": {
            "exchange": "binance",
            "market_type": "SPOT",
            "symbol_native": "BTCUSDT",
            "base_asset": base_asset,
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

    def test_assembles_existing_analyses_and_abstains_on_all_horizons(self):
        report = build_research_report(self.source, config(), "BTC", self.raw)
        self.assertEqual(report["schema_version"], "crypto-asset-research-report-v1")
        self.assertEqual(report["report_status"], "TECHNICAL_BASELINE_ASSEMBLED")
        self.assertEqual(report["decision_status"], "INDETERMINATE")
        self.assertEqual(report["asset_identity_status"], "VERIFIED")
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

    def test_source_bytes_must_match_the_analyzed_artifact(self):
        with self.assertRaisesRegex(ValueError, "do not match"):
            build_research_report(self.source, config(), "BTC", b'{}')

    def test_missing_asset_identity_is_indeterminate_not_inferred_from_ticker(self):
        source = artifact(self.source["candles"], base_asset=None)
        source["market"].pop("base_asset")
        report = build_research_report(source, config(), "BTC")
        self.assertEqual(report["asset_identity_status"], "INDETERMINATE")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(report["decision_status"], "INDETERMINATE")

    def test_mismatched_asset_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "does not match artifact base asset"):
            build_research_report(self.source, config(), "ETH")

    def test_partial_capture_is_not_reported_complete(self):
        source = artifact(self.source["candles"], overall_status="PARTIAL")
        report = build_research_report(source, config(), "BTC")
        self.assertEqual(report["report_status"], "PARTIAL")
        self.assertEqual(report["data_quality"]["status"], "INCOMPLETE_OR_UNVERIFIED")
        self.assertEqual(report["source_artifact"]["capture_status"], "PARTIAL")

    def test_missing_explicit_method_parameter_is_rejected(self):
        invalid = config()
        invalid["movement"].pop("return_threshold_pct")
        with self.assertRaisesRegex(ValueError, "return_threshold_pct is required"):
            build_research_report(self.source, invalid, "BTC")


if __name__ == "__main__":
    unittest.main()
