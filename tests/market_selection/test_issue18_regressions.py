"""Regression tests for Issue #18: freshness abstention and uncovered order size."""
import unittest

from scripts.market_selection.evaluate_capture_batch import evaluate_batch
from tests.market_selection.test_evaluate_capture_batch import fixture, rec


class Issue18RegressionTests(unittest.TestCase):
    def test_capture_time_does_not_substitute_for_source_event_time(self):
        artifact = fixture()
        # The public depth payload only contains lastUpdateId, not an event timestamp.
        # Adding capture metadata must not make source freshness appear verified.
        artifact["created_at_utc"] = "2026-10-21T12:00:00Z"
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "INDETERMINATE")
        self.assertTrue(any("capture time is not a substitute" in reason for reason in market["reasons"]))

    def test_order_larger_than_captured_depth_is_indeterminate(self):
        artifact = fixture()
        depth = artifact["records"][2]["parsed_json"]
        depth["asks"] = [["100.01", "0.01"]]
        artifact["records"][2] = rec("BTC_USDT", "binance_depth", depth)
        depth["bids"] = [["99.99", "0.01"]]
        artifact["records"][2] = rec("BTC_USDT", "binance_depth", depth)

        config = {"order_size_base": 1.0, "max_slippage_bps": 10}
        market = evaluate_batch(artifact, config)["markets"][0]
        self.assertEqual(market["dimension_status"]["slippage"], "INDETERMINATE")
        self.assertGreater(market["metrics"]["buy_execution"]["uncovered_base"], 0)
        self.assertGreater(market["metrics"]["sell_execution"]["uncovered_base"], 0)
        self.assertIsNone(market["metrics"]["buy_execution"]["slippage_bps"])
        self.assertIsNone(market["metrics"]["sell_execution"]["slippage_bps"])


    def test_live_freshness_requires_approved_policy_and_clock_skew_evidence(self):
        artifact = fixture()
        artifact["live_depth_observations"] = [{
            "status": "SYNCHRONIZED", "symbol": "BTCUSDT", "read_only": True,
            "freshness_observation": {
                "source_timestamp_utc": "2026-10-21T12:00:00.000Z",
                "captured_at_utc": "2026-10-21T12:00:00.100Z",
                "evaluation_time_utc": "2026-10-21T12:00:00.200Z",
            },
        }]
        # A live timestamp alone cannot bypass owner approval or clock-quality evidence.
        market = evaluate_batch(artifact, {})["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "INDETERMINATE")

    def test_live_freshness_passes_only_with_approved_policy_and_fresh_observation(self):
        artifact = fixture()
        artifact["live_depth_observations"] = [{
            "status": "SYNCHRONIZED", "symbol": "BTCUSDT", "read_only": True,
            "clock_skew_ms": 10,
            "freshness_observation": {
                "source_timestamp_utc": "2026-10-21T12:00:00.000Z",
                "captured_at_utc": "2026-10-21T12:00:00.100Z",
                "evaluation_time_utc": "2026-10-21T12:00:00.200Z",
            },
        }]
        config = {"freshness_policy": {
            "approval_status": "APPROVED", "version": "1.0.0",
            "approval_ref": "owner-decision-2026-10-21",
            "max_source_lag_seconds": 1.0, "max_snapshot_age_seconds": 1.0,
            "max_clock_skew_ms": 100,
        }}
        market = evaluate_batch(artifact, config)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "PASS")
        self.assertAlmostEqual(market["metrics"]["source_lag_seconds"], 0.1)
        self.assertAlmostEqual(market["metrics"]["snapshot_age_seconds"], 0.1)
        self.assertEqual(market["decision_status"], "INDETERMINATE")
        self.assertFalse(evaluate_batch(artifact, config)["config_approved"])

    def test_live_freshness_fails_when_approved_age_limit_is_exceeded(self):
        artifact = fixture()
        artifact["live_depth_observations"] = [{
            "status": "SYNCHRONIZED", "symbol": "BTCUSDT", "read_only": True,
            "clock_skew_ms": 10,
            "freshness_observation": {
                "source_timestamp_utc": "2026-10-21T12:00:00.000Z",
                "captured_at_utc": "2026-10-21T12:00:02.000Z",
                "evaluation_time_utc": "2026-10-21T12:00:03.000Z",
            },
        }]
        config = {"freshness_policy": {
            "approval_status": "APPROVED", "version": "1.0.0",
            "approval_ref": "owner-decision-2026-10-21",
            "max_source_lag_seconds": 1.0, "max_snapshot_age_seconds": 1.0,
            "max_clock_skew_ms": 100,
        }}
        market = evaluate_batch(artifact, config)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "FAIL")
        self.assertEqual(market["decision_status"], "INDETERMINATE")

    def test_zero_fee_configuration_is_not_fee_evidence(self):
        artifact = fixture()
        config = {"maker_fee_bps": 0, "taker_fee_bps": 0}
        market = evaluate_batch(artifact, config)["markets"][0]
        self.assertEqual(market["dimension_status"]["fees"], "INDETERMINATE")
        self.assertEqual(market["decision_status"], "INDETERMINATE")


if __name__ == "__main__":
    unittest.main()
