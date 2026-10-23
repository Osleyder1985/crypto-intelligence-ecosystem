"""Offline tests for deterministic matured forecast scoring."""
import copy
import unittest

from scripts.market_selection.forecast_scoring import (
    SCORING_SCHEMA,
    score_forecast_records,
)


def record(prediction_id="p-1", forecast_return=0.12, actual_return=0.10, benchmark_return=0.0):
    return {
        "prediction_id": prediction_id,
        "asset_id": "binance:BTCUSDT",
        "methodology_id": "spot-forward-return",
        "methodology_version": "1.0.0",
        "horizon": "short",
        "issued_at": "2026-01-01T00:00:00Z",
        "target_window_start": "2026-01-01T00:01:00Z",
        "target_window_end": "2026-01-01T01:01:00Z",
        "outcome_observed_at": "2026-01-01T01:02:00Z",
        "decision_mode": "ASSESS",
        "forecast_return": forecast_return,
        "actual_return": actual_return,
        "benchmark_return": benchmark_return,
    }


class ForecastScoringTests(unittest.TestCase):
    def test_scores_matured_forecast_and_paired_benchmark(self):
        result = score_forecast_records([record()])
        self.assertEqual(result["schema_version"], SCORING_SCHEMA)
        self.assertAlmostEqual(result["metrics"]["mae"], 0.02)
        self.assertAlmostEqual(result["metrics"]["rmse"], 0.02)
        self.assertEqual(result["metrics"]["directional_accuracy"], 1.0)
        self.assertEqual(result["benchmark_metrics"]["directional_accuracy"], 0.0)
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])

    def test_counts_abstentions_and_excludes_them_from_error_metrics(self):
        abstained = record("p-2", actual_return=-0.1)
        abstained["decision_mode"] = "ABSTAIN"
        abstained["forecast_return"] = None
        result = score_forecast_records([record(), abstained])
        self.assertEqual(result["sample_count"], 2)
        self.assertEqual(result["assessed_count"], 1)
        self.assertEqual(result["abstained_count"], 1)
        self.assertEqual(result["coverage"], 0.5)
        self.assertEqual(result["scored_prediction_ids"], ["p-1"])

    def test_requires_non_empty_records(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            score_forecast_records([])

    def test_rejects_duplicate_prediction_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate prediction_id"):
            score_forecast_records([record(), record()])

    def test_rejects_mixed_methodology_versions(self):
        second = record("p-2")
        second["methodology_version"] = "2.0.0"
        with self.assertRaisesRegex(ValueError, "share asset, methodology"):
            score_forecast_records([record(), second])

    def test_rejects_outcome_observed_before_target_window_closes(self):
        value = record()
        value["outcome_observed_at"] = "2026-01-01T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "cannot precede target_window_end"):
            score_forecast_records([value])

    def test_rejects_prediction_issued_after_target_start(self):
        value = record()
        value["issued_at"] = "2026-01-01T00:02:00Z"
        with self.assertRaisesRegex(ValueError, "issued_at < target_window_start"):
            score_forecast_records([value])

    def test_rejects_naive_timestamps(self):
        value = record()
        value["issued_at"] = "2026-01-01T00:00:00"
        with self.assertRaisesRegex(ValueError, "include a timezone"):
            score_forecast_records([value])

    def test_rejects_non_finite_returns(self):
        value = record()
        value["forecast_return"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite number"):
            score_forecast_records([value])

    def test_zero_actual_returns_are_reported_not_counted_as_directional_hits(self):
        value = record(actual_return=0.0, forecast_return=0.1)
        result = score_forecast_records([value])
        self.assertIsNone(result["metrics"]["directional_accuracy"])
        self.assertEqual(result["metrics"]["directional_sample_count"], 0)
        self.assertEqual(result["metrics"]["zero_actual_return_count"], 1)

    def test_abstention_cannot_include_a_numeric_forecast(self):
        value = record()
        value["decision_mode"] = "ABSTAIN"
        with self.assertRaisesRegex(ValueError, "must be null when decision_mode is ABSTAIN"):
            score_forecast_records([value])

    def test_all_abstained_cohort_has_no_error_metrics(self):
        value = record()
        value["decision_mode"] = "ABSTAIN"
        value["forecast_return"] = None
        result = score_forecast_records([value])
        self.assertEqual(result["assessed_count"], 0)
        self.assertIsNone(result["metrics"])
        self.assertEqual(result["coverage"], 0.0)


if __name__ == "__main__":
    unittest.main()
