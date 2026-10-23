"""Offline tests for attaching matured forecast scores to research reports."""
import copy
import hashlib
import json
import unittest

from scripts.market_selection.attach_forecast_scoring_to_report import (
    INTEGRATION_SCHEMA,
    attach_forecast_scoring,
)
from scripts.market_selection.research_report import REPORT_SCHEMA


def report():
    return {
        "schema_version": REPORT_SCHEMA,
        "requested_asset_id": "binance:BTCUSDT",
        "decision_status": "INDETERMINATE",
        "orders_submitted": False,
        "horizons": {
            "short": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
            "medium": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
            "long": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
        },
    }


def records():
    return [{
        "prediction_id": "p-1",
        "asset_id": "binance:BTCUSDT",
        "methodology_id": "spot-forward-return",
        "methodology_version": "1.0.0",
        "horizon": "short",
        "issued_at": "2026-01-01T00:00:00Z",
        "target_window_start": "2026-01-01T00:01:00Z",
        "target_window_end": "2026-01-01T01:01:00Z",
        "outcome_observed_at": "2026-01-01T01:02:00Z",
        "decision_mode": "ASSESS",
        "forecast_return": 0.12,
        "actual_return": 0.10,
        "benchmark_return": 0.0,
    }]


class AttachForecastScoringTests(unittest.TestCase):
    def test_attaches_scores_without_changing_horizons_or_decision(self):
        original = report()
        result = attach_forecast_scoring(original, records())
        self.assertEqual(result["forecast_evaluation"]["integration_schema"], INTEGRATION_SCHEMA)
        self.assertEqual(result["forecast_evaluation"]["status"], "DESCRIPTIVE_SCORING_ATTACHED")
        self.assertAlmostEqual(result["forecast_evaluation"]["scoring"]["metrics"]["mae"], 0.02)
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(result["horizons"], original["horizons"])
        self.assertNotIn("forecast_evaluation", original)

    def test_preserves_exact_source_hashes(self):
        value = report()
        items = records()
        report_raw = json.dumps(value, sort_keys=True).encode("utf-8")
        records_raw = json.dumps(items, sort_keys=True).encode("utf-8")
        result = attach_forecast_scoring(value, items, report_bytes=report_raw, records_bytes=records_raw)
        self.assertEqual(result["forecast_evaluation"]["source_report_sha256"], hashlib.sha256(report_raw).hexdigest())
        self.assertEqual(result["forecast_evaluation"]["source_records_sha256"], hashlib.sha256(records_raw).hexdigest())

    def test_rejects_asset_mismatch(self):
        value = records()
        value[0]["asset_id"] = "binance:ETHUSDT"
        with self.assertRaisesRegex(ValueError, "exactly match"):
            attach_forecast_scoring(report(), value)

    def test_rejects_wrong_report_schema(self):
        value = report()
        value["schema_version"] = "unknown"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            attach_forecast_scoring(value, records())

    def test_rejects_non_indeterminate_report(self):
        value = report()
        value["decision_status"] = "FAVORABLE"
        with self.assertRaisesRegex(ValueError, "only INDETERMINATE"):
            attach_forecast_scoring(value, records())

    def test_rejects_report_that_claims_orders_were_submitted(self):
        value = report()
        value["orders_submitted"] = True
        with self.assertRaisesRegex(ValueError, "orders_submitted must be false"):
            attach_forecast_scoring(value, records())

    def test_refuses_to_overwrite_existing_forecast_evidence(self):
        value = report()
        value["forecast_evaluation"] = {"status": "EXISTING"}
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            attach_forecast_scoring(value, records())

    def test_rejects_mismatched_raw_report_bytes(self):
        with self.assertRaisesRegex(ValueError, "report_bytes do not match"):
            attach_forecast_scoring(report(), records(), report_bytes=b'{"wrong": true}')

    def test_rejects_mismatched_raw_record_bytes(self):
        with self.assertRaisesRegex(ValueError, "records_bytes do not match"):
            attach_forecast_scoring(report(), records(), records_bytes=b"[]")

    def test_rejects_non_object_report(self):
        with self.assertRaisesRegex(ValueError, "report must be a JSON object"):
            attach_forecast_scoring([], records())


if __name__ == "__main__":
    unittest.main()
