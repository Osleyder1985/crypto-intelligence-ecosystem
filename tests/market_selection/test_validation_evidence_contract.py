"""Offline tests for out-of-sample validation evidence reports."""
import unittest

from scripts.market_selection.methodology_contract import METHODOLOGY_SCHEMA
from scripts.market_selection.validation_evidence_contract import (
    VALIDATION_REPORT_SCHEMA,
    validate_validation_report,
)


def methodology():
    return {
        "schema_version": METHODOLOGY_SCHEMA,
        "methodology_id": "spot-forward-return",
        "version": "1.0.0",
        "status": "APPROVED",
        "created_at": "2025-01-01T00:00:00Z",
        "approval": {
            "approved_by": "reviewer",
            "approved_at": "2025-01-02T00:00:00Z",
            "evidence_url": "https://example.org/methodology-approval",
        },
        "horizons": {
            "short": {"target_window_seconds": 3600, "target": "return", "target_unit": "fraction", "description": "short"},
            "medium": {"target_window_seconds": 86400, "target": "return", "target_unit": "fraction", "description": "medium"},
            "long": {"target_window_seconds": 604800, "target": "return", "target_unit": "fraction", "description": "long"},
        },
        "target_definition": {"formula": "future / entry - 1", "price_source": "closed OHLCV", "sampling_rule": "next closed candle"},
        "threshold_policy": {"status": "NOT_APPROVED"},
        "validation": {
            "walk_forward": True, "out_of_sample": True, "leakage_checks": True,
            "splits": [
                {"train_end": "2025-02-28T23:59:59Z", "test_start": "2025-03-01T00:00:00Z", "test_end": "2025-04-01T00:00:00Z"},
                {"train_end": "2025-03-31T23:59:59Z", "test_start": "2025-04-01T00:00:00Z", "test_end": "2025-05-01T00:00:00Z"},
            ],
            "baselines": ["buy_and_hold"], "metrics": ["mae", "directional_accuracy"],
        },
        "cost_model": {
            "fees": {"status": "MEASURED", "basis_points": 10, "reason": None},
            "spread": {"status": "ESTIMATED", "basis_points": 2, "reason": None},
            "slippage": {"status": "ESTIMATED", "basis_points": 3, "reason": None},
            "funding_or_borrow": {"status": "NOT_APPLICABLE", "basis_points": None, "reason": "Spot only"},
            "other": {"status": "NOT_AVAILABLE", "basis_points": None, "reason": None},
        },
        "features": [{
            "feature_id": "return_1d", "source_id": "ohlcv", "availability_timestamp_field": "closed_at",
            "transformation_version": "return-v1",
        }],
    }


def report(**overrides):
    value = {
        "schema_version": VALIDATION_REPORT_SCHEMA,
        "report_id": "validation-2025-q1-q2",
        "methodology_id": "spot-forward-return",
        "methodology_version": "1.0.0",
        "protocol_frozen_at": "2025-02-01T00:00:00Z",
        "generated_at": "2025-05-02T00:00:00Z",
        "dataset": {
            "artifact_url": "https://example.org/dataset.json",
            "sha256": "a" * 64,
            "sample_count": 10000,
            "window_start": "2025-01-01T00:00:00Z",
            "window_end": "2025-05-01T00:00:00Z",
            "point_in_time": True,
            "universe_definition": "Spot assets eligible as of each historical date",
            "delisted_asset_policy": "INCLUDED",
        },
        "split_results": [
            {"split_index": 0, "test_start": "2025-03-01T00:00:00Z", "test_end": "2025-04-01T00:00:00Z", "sample_count": 1000, "metrics": {"mae": 0.02, "directional_accuracy": 0.51}},
            {"split_index": 1, "test_start": "2025-04-01T00:00:00Z", "test_end": "2025-05-01T00:00:00Z", "sample_count": 1200, "metrics": {"mae": 0.018, "directional_accuracy": 0.52}},
        ],
        "baseline_results": [{
            "benchmark_id": "buy-and-hold", "description": "Buy and hold on same test windows",
            "metrics": {"mae": 0.021, "directional_accuracy": 0.50},
        }],
        "realized_cost_model": {
            "fees": {"status": "MEASURED", "basis_points": 10, "reason": None},
            "spread": {"status": "ESTIMATED", "basis_points": 2, "reason": None},
            "slippage": {"status": "ESTIMATED", "basis_points": 3, "reason": None},
            "funding_or_borrow": {"status": "NOT_APPLICABLE", "basis_points": None, "reason": "Spot only"},
            "other": {"status": "NOT_AVAILABLE", "basis_points": None, "reason": None},
        },
        "sensitivity_analysis": [{
            "scenario_id": "fees-plus-25pct", "description": "Increase modeled fees by 25%",
            "metrics": {"mae": 0.02, "directional_accuracy": 0.50},
        }],
        "uncertainty": {
            "method": "block bootstrap by day",
            "confidence_level": 0.95,
            "intervals": [{"metric": "directional_accuracy", "lower": 0.49, "upper": 0.54, "sample_count": 2200}],
        },
        "reproducibility": {
            "code_version": "git:abc123", "command": "python evaluate.py --config frozen.json",
            "environment_sha256": "b" * 64, "execution_artifact_url": "https://example.org/run.json",
        },
        "review": {"status": "PENDING"},
    }
    value.update(overrides)
    return value


class ValidationEvidenceContractTests(unittest.TestCase):
    def test_valid_report_is_structurally_valid_but_indeterminate(self):
        result = validate_validation_report(report(), methodology())
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(len(result["split_results"]), 2)

    def test_rejects_unapproved_methodology(self):
        value = methodology()
        value["status"] = "DRAFT"
        value.pop("approval")
        with self.assertRaisesRegex(ValueError, "APPROVED methodology"):
            validate_validation_report(report(), value)

    def test_protocol_must_be_frozen_before_test_data(self):
        value = report(protocol_frozen_at="2025-03-01T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "precede the first"):
            validate_validation_report(value, methodology())

    def test_report_cannot_be_generated_before_final_test_window(self):
        value = report(generated_at="2025-04-30T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "at or after the final"):
            validate_validation_report(value, methodology())

    def test_dataset_must_cover_all_test_windows(self):
        value = report()
        value["dataset"]["window_end"] = "2025-04-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "include all declared"):
            validate_validation_report(value, methodology())

    def test_rejects_mismatched_split_boundaries(self):
        value = report()
        value["split_results"][0]["test_start"] = "2025-03-02T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "match the pre-registered"):
            validate_validation_report(value, methodology())

    def test_requires_benchmark_and_sensitivity_metrics(self):
        value = report()
        value["baseline_results"][0]["metrics"] = {"unrelated": 1}
        with self.assertRaisesRegex(ValueError, "comparable"):
            validate_validation_report(value, methodology())

    def test_rejects_unknown_costs_as_zero(self):
        value = report()
        value["realized_cost_model"]["other"] = {"status": "NOT_AVAILABLE", "basis_points": 0, "reason": None}
        with self.assertRaisesRegex(ValueError, "must be null"):
            validate_validation_report(value, methodology())

    def test_requires_uncertainty_intervals(self):
        value = report()
        value["uncertainty"]["intervals"] = []
        with self.assertRaisesRegex(ValueError, "at least one interval"):
            validate_validation_report(value, methodology())

    def test_reviewed_report_requires_preceding_report_and_evidence(self):
        value = report()
        value["review"] = {
            "status": "REVIEWED", "reviewed_by": "reviewer",
            "reviewed_at": "2025-05-03T00:00:00Z",
            "evidence_url": "https://example.org/review.json", "evidence_sha256": "c" * 64,
        }
        result = validate_validation_report(value, methodology())
        self.assertEqual(result["review"]["status"], "REVIEWED")
        value["review"]["evidence_sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate_validation_report(value, methodology())


if __name__ == "__main__":
    unittest.main()
