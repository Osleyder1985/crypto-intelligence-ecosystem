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

    def test_zero_fee_configuration_is_not_fee_evidence(self):
        artifact = fixture()
        config = {"maker_fee_bps": 0, "taker_fee_bps": 0}
        market = evaluate_batch(artifact, config)["markets"][0]
        self.assertEqual(market["dimension_status"]["fees"], "INDETERMINATE")
        self.assertEqual(market["decision_status"], "INDETERMINATE")


if __name__ == "__main__":
    unittest.main()
