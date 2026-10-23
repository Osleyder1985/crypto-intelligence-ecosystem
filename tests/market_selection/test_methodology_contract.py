"""Offline tests for methodology versioning and prediction temporal controls."""
import unittest

from scripts.market_selection.methodology_contract import (
    METHODOLOGY_SCHEMA,
    PREDICTION_SCHEMA,
    validate_methodology,
    validate_prediction_record,
)


def methodology(**overrides):
    value = {
        "schema_version": METHODOLOGY_SCHEMA,
        "methodology_id": "spot-forward-return",
        "version": "1.0.0",
        "status": "DRAFT",
        "created_at": "2026-01-01T00:00:00Z",
        "horizons": {
            "short": {"target_window_seconds": 3600, "target": "forward_return", "target_unit": "fraction", "description": "Short horizon defined by this version"},
            "medium": {"target_window_seconds": 86400, "target": "forward_return", "target_unit": "fraction", "description": "Medium horizon defined by this version"},
            "long": {"target_window_seconds": 604800, "target": "forward_return", "target_unit": "fraction", "description": "Long horizon defined by this version"},
        },
        "target_definition": {
            "formula": "(future_close / entry_close) - 1",
            "price_source": "closed Binance Spot OHLCV capture",
            "sampling_rule": "next fully closed candle after generated_at",
        },
        "threshold_policy": {"status": "NOT_APPROVED"},
        "validation": {
            "walk_forward": True,
            "out_of_sample": True,
            "leakage_checks": True,
            "splits": [{
                "train_end": "2025-06-30T23:59:59Z",
                "test_start": "2025-07-01T00:00:00Z",
                "test_end": "2025-08-01T00:00:00Z",
            }],
            "baselines": ["buy_and_hold"],
            "metrics": ["mae", "directional_accuracy"],
        },
        "cost_model": {
            "fees": {"status": "MEASURED", "basis_points": 10, "reason": None},
            "spread": {"status": "ESTIMATED", "basis_points": 2, "reason": None},
            "slippage": {"status": "ESTIMATED", "basis_points": 3, "reason": None},
            "funding_or_borrow": {"status": "NOT_APPLICABLE", "basis_points": None, "reason": "Spot-only methodology"},
            "other": {"status": "NOT_AVAILABLE", "basis_points": None, "reason": None},
        },
        "features": [{
            "feature_id": "ohlcv_return_1d",
            "source_id": "binance_spot_ohlcv",
            "availability_timestamp_field": "closed_at_utc",
            "transformation_version": "return-v1",
        }],
    }
    value.update(overrides)
    return value


def approved_methodology():
    value = methodology()
    value["status"] = "APPROVED"
    value["approval"] = {
        "approved_by": "test-reviewer",
        "approved_at": "2026-01-02T00:00:00Z",
        "evidence_url": "https://example.org/approval-record",
    }
    return value


def prediction(**overrides):
    value = {
        "schema_version": PREDICTION_SCHEMA,
        "prediction_id": "prediction-1",
        "methodology_id": "spot-forward-return",
        "methodology_version": "1.0.0",
        "asset": {"stable_id": "binance:BTCUSDT", "category": "native_l1"},
        "horizon": "short",
        "generated_at": "2026-10-20T10:00:00Z",
        "data_as_of": "2026-10-20T09:59:00Z",
        "model_training_data_end": "2026-10-19T23:59:59Z",
        "target_window_start": "2026-10-20T10:00:01Z",
        "target_window_end": "2026-10-20T11:00:01Z",
        "features": [{
            "feature_id": "ohlcv_return_1d",
            "source_id": "binance_spot_ohlcv",
            "transformation_version": "return-v1",
            "observed_at": "2026-10-20T09:58:00Z",
            "captured_at": "2026-10-20T09:59:00Z",
        }],
        "output": {
            "probability_up": 0.62,
            "expected_return": 0.01,
            "probability_calibration": {
                "status": "VALIDATED",
                "method": "isotonic regression",
                "metric": "BRIER_SCORE",
                "score": 0.18,
                "evaluation_start": "2026-10-01T00:00:00Z",
                "evaluation_end": "2026-10-15T00:00:00Z",
                "sample_count": 200,
                "evidence_url": "https://example.org/calibration-evidence",
                "evidence_sha256": "a" * 64,
                "reviewed_by": "test-reviewer",
                "reviewed_at": "2026-10-16T00:00:00Z",
            },
        },
    }
    value.update(overrides)
    return value


class MethodologyContractTests(unittest.TestCase):
    def test_methodology_is_versioned_and_decision_remains_indeterminate(self):
        result = validate_methodology(methodology())
        self.assertEqual(result["methodology_id"], "spot-forward-return")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_requires_exact_short_medium_long_horizons(self):
        value = methodology()
        value["horizons"].pop("medium")
        with self.assertRaisesRegex(ValueError, "exactly short, medium, and long"):
            validate_methodology(value)

    def test_horizon_order_is_short_then_medium_then_long(self):
        value = methodology()
        value["horizons"]["short"]["target_window_seconds"] = 604800
        value["horizons"]["long"]["target_window_seconds"] = 3600
        with self.assertRaisesRegex(ValueError, "strictly ordered"):
            validate_methodology(value)

    def test_horizon_duration_must_be_whole_seconds(self):
        value = methodology()
        value["horizons"]["short"]["target_window_seconds"] = 1.5
        with self.assertRaisesRegex(ValueError, "whole number"):
            validate_methodology(value)

    def test_walk_forward_out_of_sample_and_leakage_checks_are_required(self):
        value = methodology()
        value["validation"]["out_of_sample"] = False
        with self.assertRaisesRegex(ValueError, "validation.out_of_sample"):
            validate_methodology(value)

    def test_train_must_end_before_test_and_test_splits_must_not_overlap(self):
        value = methodology()
        value["validation"]["splits"][0]["train_end"] = "2025-07-02T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "train_end < test_start"):
            validate_methodology(value)

    def test_all_cost_components_must_be_explicit(self):
        value = methodology()
        value["cost_model"].pop("fees")
        with self.assertRaisesRegex(ValueError, "cost_model must explicitly define"):
            validate_methodology(value)

    def test_missing_cost_cannot_be_filled_with_zero(self):
        value = methodology()
        value["cost_model"]["other"] = {"status": "NOT_AVAILABLE", "basis_points": 0, "reason": None}
        with self.assertRaisesRegex(ValueError, "must be null"):
            validate_methodology(value)

    def test_approved_methodology_requires_approval_evidence(self):
        value = methodology(status="APPROVED")
        with self.assertRaisesRegex(ValueError, "requires an approval record"):
            validate_methodology(value)

    def test_approved_methodology_with_explicit_evidence_validates(self):
        result = validate_methodology(approved_methodology())
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_prediction_rejected_for_draft_methodology(self):
        with self.assertRaisesRegex(ValueError, "non-APPROVED methodology"):
            validate_prediction_record(prediction(), methodology())

    def test_valid_prediction_checks_feature_provenance_and_horizon(self):
        result = validate_prediction_record(prediction(), approved_methodology())
        self.assertEqual(result["horizon"], "short")
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])

    def test_feature_captured_after_data_cutoff_is_rejected(self):
        value = prediction()
        value["features"][0]["captured_at"] = "2026-10-20T10:00:01Z"
        with self.assertRaisesRegex(ValueError, "not available at data_as_of"):
            validate_prediction_record(value, approved_methodology())

    def test_feature_transformation_must_match_methodology(self):
        value = prediction()
        value["features"][0]["transformation_version"] = "return-v2"
        with self.assertRaisesRegex(ValueError, "transformation_version does not match"):
            validate_prediction_record(value, approved_methodology())

    def test_training_data_cannot_extend_after_data_as_of(self):
        value = prediction()
        value["model_training_data_end"] = "2026-10-20T09:59:30Z"
        with self.assertRaisesRegex(ValueError, "cannot be after data_as_of"):
            validate_prediction_record(value, approved_methodology())

    def test_target_window_must_start_after_prediction_and_match_horizon(self):
        value = prediction()
        value["target_window_start"] = "2026-10-20T09:59:59Z"
        with self.assertRaisesRegex(ValueError, "must be after generated_at"):
            validate_prediction_record(value, approved_methodology())

    def test_probability_requires_explicit_calibration_evidence(self):
        value = prediction()
        value["output"].pop("probability_calibration")
        with self.assertRaisesRegex(ValueError, "requires probability_calibration evidence"):
            validate_prediction_record(value, approved_methodology())

    def test_probability_calibration_requires_a_valid_digest(self):
        value = prediction()
        value["output"]["probability_calibration"]["evidence_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "64-character hexadecimal SHA-256"):
            validate_prediction_record(value, approved_methodology())

    def test_probability_calibration_must_be_available_before_prediction(self):
        value = prediction()
        value["output"]["probability_calibration"]["reviewed_at"] = "2026-10-20T10:00:01Z"
        with self.assertRaisesRegex(ValueError, "review must be available by generated_at"):
            validate_prediction_record(value, approved_methodology())

    def test_probability_must_be_between_zero_and_one(self):
        value = prediction()
        value["output"]["probability_up"] = 1.1
        with self.assertRaisesRegex(ValueError, "must be <= 1"):
            validate_prediction_record(value, approved_methodology())

    def test_unregistered_feature_is_rejected(self):
        value = prediction()
        value["features"][0]["feature_id"] = "untracked_feature"
        with self.assertRaisesRegex(ValueError, "not declared"):
            validate_prediction_record(value, approved_methodology())


if __name__ == "__main__":
    unittest.main()