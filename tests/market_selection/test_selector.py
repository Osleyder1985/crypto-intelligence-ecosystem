"""Deterministic tests for the read-only spot selector prototype."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "market_selection"))

import selector  # noqa: E402

BASE_OBSERVATION = {
    "market_type": "spot",
    "availability_status": "confirmed",
    "bids": [
        {"price": 99.9, "quantity": 20.0},
        {"price": 99.0, "quantity": 30.0},
    ],
    "asks": [
        {"price": 100.1, "quantity": 20.0},
        {"price": 101.0, "quantity": 30.0},
    ],
}

BASE_CONFIG = {
    "max_spread_bps": 30.0,
    "depth_band_bps": 150.0,
    "min_depth_quote": 1000.0,
    "order_size_base": 1.0,
    "max_slippage_bps": 30.0,
    "critical_dimensions": ["market_type", "spread", "depth", "slippage", "availability"],
    "config_approval_status": "approved",
    "config_version": "synthetic-fixture-v1",
    "config_approval_ref": "TEST-ONLY; not an approved trading baseline",
}


class SpotSelectorTests(unittest.TestCase):
    def test_spread_formula(self) -> None:
        self.assertAlmostEqual(selector.spread_bps(99.0, 101.0), 200.0)

    def test_spread_rejects_crossed_book(self) -> None:
        with self.assertRaisesRegex(ValueError, "crossed"):
            selector.spread_bps(101.0, 99.0)

    def test_spread_rejects_non_finite_values(self) -> None:
        with self.assertRaises(ValueError):
            selector.spread_bps(float("nan"), 100.0)

    def test_depth_counts_only_levels_inside_band(self) -> None:
        levels = [
            {"price": 100.0, "quantity": 2.0},
            {"price": 102.0, "quantity": 5.0},
        ]
        self.assertAlmostEqual(selector.depth_quote(levels, 100.0, 100.0, "asks"), 200.0)

    def test_buy_slippage_uses_vwap_and_reports_full_fill(self) -> None:
        result = selector.estimate_slippage_bps(
            [{"price": 100.0, "quantity": 1.0}, {"price": 110.0, "quantity": 1.0}],
            100.0,
            1.5,
            "asks",
        )
        self.assertAlmostEqual(result["vwap"], 103.3333333333)
        self.assertAlmostEqual(result["slippage_bps"], 333.3333333)
        self.assertEqual(result["uncovered_base"], 0.0)

    def test_sell_slippage_uses_bid_side(self) -> None:
        result = selector.estimate_slippage_bps(
            [{"price": 100.0, "quantity": 1.0}, {"price": 90.0, "quantity": 1.0}],
            100.0,
            1.5,
            "bids",
        )
        self.assertAlmostEqual(result["vwap"], 96.6666666667)
        self.assertAlmostEqual(result["slippage_bps"], 333.3333333)

    def test_insufficient_book_does_not_claim_full_size_slippage(self) -> None:
        result = selector.estimate_slippage_bps(
            [{"price": 100.0, "quantity": 0.25}], 100.0, 1.0, "asks"
        )
        self.assertEqual(result["uncovered_base"], 0.75)
        self.assertIsNone(result["slippage_bps"])

    def test_non_spot_market_is_excluded(self) -> None:
        observation = dict(BASE_OBSERVATION, market_type="future")
        result = selector.evaluate_market(observation, BASE_CONFIG)
        self.assertEqual(result["decision_status"], "FAIL")
        self.assertEqual(result["dimension_status"]["market_type"], "FAIL")

    def test_missing_threshold_never_defaults_to_pass(self) -> None:
        config = dict(BASE_CONFIG)
        del config["max_spread_bps"]
        result = selector.evaluate_market(BASE_OBSERVATION, config)
        self.assertEqual(result["dimension_status"]["spread"], "INDETERMINATE")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_unconfirmed_availability_blocks_global_decision(self) -> None:
        observation = dict(BASE_OBSERVATION, availability_status=None)
        result = selector.evaluate_market(observation, BASE_CONFIG)
        self.assertEqual(result["dimension_status"]["availability"], "INDETERMINATE")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_confirmed_unavailable_pair_fails_critical_dimension(self) -> None:
        observation = dict(BASE_OBSERVATION, availability_status="unavailable")
        result = selector.evaluate_market(observation, BASE_CONFIG)
        self.assertEqual(result["dimension_status"]["availability"], "FAIL")
        self.assertEqual(result["decision_status"], "FAIL")

    def test_invalid_order_book_is_indeterminate(self) -> None:
        observation = dict(BASE_OBSERVATION, bids=[])
        result = selector.evaluate_market(observation, BASE_CONFIG)
        self.assertEqual(result["dimension_status"]["spread"], "INDETERMINATE")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_repeated_evaluation_is_deterministic_except_no_dynamic_fields_exist(self) -> None:
        first = selector.evaluate_market(BASE_OBSERVATION, BASE_CONFIG)
        second = selector.evaluate_market(BASE_OBSERVATION, BASE_CONFIG)
        self.assertEqual(first, second)

    def test_unapproved_configuration_blocks_global_decision(self) -> None:
        config = dict(BASE_CONFIG, config_approval_status="proposed")
        result = selector.evaluate_market(BASE_OBSERVATION, config)
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertTrue(any("configuration approval" in reason for reason in result["decision_reasons"]))

    def test_bad_critical_dimension_list_blocks_global_decision(self) -> None:
        config = dict(BASE_CONFIG, critical_dimensions=["unknown"])
        result = selector.evaluate_market(BASE_OBSERVATION, config)
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_result_explicitly_disclaims_live_data_and_orders(self) -> None:
        result = selector.evaluate_market(BASE_OBSERVATION, BASE_CONFIG)
        self.assertFalse(result["live_data_used"])
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(result["execution_mode"], "read_only")


if __name__ == "__main__":
    unittest.main()
