"""Offline tests for independent horizon assessment contract."""
import copy
import unittest

from scripts.market_selection.horizon_assessment_contract import (
    ASSESSMENT_SCHEMA,
    validate_horizon_assessment,
)


def dimension(status="SUPPORTED"):
    return {"status": status, "rationale": "Grounded in recorded evidence", "evidence_refs": ["evidence-1"]}


def horizon(conclusion="BASE", decision_mode="ASSESS", abstention_reasons=None):
    return {
        "conclusion": conclusion,
        "decision_mode": decision_mode,
        "abstention_reasons": abstention_reasons or [],
        "evidence_quality": dimension(),
        "asset_risk": dimension("LIMITED"),
        "horizon_opportunity": dimension(),
        "confidence": dimension("LIMITED"),
        "factors": [{
            "factor_id": "closed-candle-return",
            "category": "PRICE_VOLUME",
            "decision": "INCLUDED",
            "rationale": "Available closed-candle return is relevant to this horizon",
            "source_id": "spot-ohlcv",
            "transformation_version": "return-v1",
            "observed_at": "2026-10-20T09:58:00Z",
            "captured_at": "2026-10-20T09:59:00Z",
        }, {
            "factor_id": "unverified-rumor",
            "category": "EXTERNAL_EVENT",
            "decision": "EXCLUDED",
            "rationale": "No verifiable source or publication timestamp",
            "source_id": "unverified",
            "transformation_version": "raw-v1",
            "observed_at": "2026-10-20T09:00:00Z",
            "captured_at": "2026-10-20T09:30:00Z",
        }],
        "scenarios": {
            "FAVORABLE": {"conditions": ["Observed support holds"], "invalidation_rules": ["Support breaks on a closed candle"]},
            "BASE": {"conditions": ["Price remains in the observed range"], "invalidation_rules": ["Range boundary closes outside"]},
            "ADVERSE": {"conditions": ["Liquidity deteriorates"], "invalidation_rules": ["Liquidity normalizes under the declared rule"]},
        },
    }


def assessment():
    return {
        "schema_version": ASSESSMENT_SCHEMA,
        "assessment_id": "asset-assessment-001",
        "methodology_id": "spot-forward-return",
        "methodology_version": "1.0.0",
        "asset_id": "binance:BTCUSDT",
        "generated_at": "2026-10-20T10:00:00Z",
        "data_as_of": "2026-10-20T09:59:00Z",
        "horizons": {
            "short": horizon("FAVORABLE"),
            "medium": horizon("BASE"),
            "long": horizon("ADVERSE"),
        },
    }


class HorizonAssessmentContractTests(unittest.TestCase):
    def test_valid_horizons_are_independent_and_not_aggregated(self):
        result = validate_horizon_assessment(assessment())
        self.assertEqual(result["horizons"]["short"]["conclusion"], "FAVORABLE")
        self.assertEqual(result["horizons"]["medium"]["conclusion"], "BASE")
        self.assertEqual(result["horizons"]["long"]["conclusion"], "ADVERSE")
        self.assertEqual(result["aggregation"], "NONE")
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])

    def test_requires_exactly_three_horizons(self):
        value = assessment()
        value["horizons"].pop("medium")
        with self.assertRaisesRegex(ValueError, "exactly short, medium, and long"):
            validate_horizon_assessment(value)

    def test_abstention_requires_reason_and_indeterminate_conclusion(self):
        value = assessment()
        value["horizons"]["short"]["decision_mode"] = "ABSTAIN"
        value["horizons"]["short"]["conclusion"] = "BASE"
        value["horizons"]["short"]["abstention_reasons"] = ["insufficient evidence"]
        with self.assertRaisesRegex(ValueError, "must be INDETERMINATE"):
            validate_horizon_assessment(value)
        value["horizons"]["short"]["conclusion"] = "INDETERMINATE"
        value["horizons"]["short"]["abstention_reasons"] = []
        with self.assertRaisesRegex(ValueError, "required when abstaining"):
            validate_horizon_assessment(value)

    def test_rejects_factor_observed_after_data_cutoff(self):
        value = assessment()
        value["horizons"]["short"]["factors"][0]["captured_at"] = "2026-10-20T10:00:01Z"
        with self.assertRaisesRegex(ValueError, "not available at data_as_of"):
            validate_horizon_assessment(value)

    def test_requires_excluded_factors_to_have_rationale(self):
        value = assessment()
        value["horizons"]["short"]["factors"][1]["rationale"] = " "
        with self.assertRaisesRegex(ValueError, "rationale must be a non-empty string"):
            validate_horizon_assessment(value)

    def test_requires_all_three_scenarios(self):
        value = assessment()
        value["horizons"]["long"]["scenarios"].pop("ADVERSE")
        with self.assertRaisesRegex(ValueError, "FAVORABLE, BASE, and ADVERSE"):
            validate_horizon_assessment(value)

    def test_separates_evidence_quality_risk_opportunity_and_confidence(self):
        value = assessment()
        value["horizons"]["short"].pop("asset_risk")
        with self.assertRaisesRegex(ValueError, "asset_risk must be an object"):
            validate_horizon_assessment(value)

    def test_rejects_duplicate_factor_ids_within_horizon(self):
        value = assessment()
        value["horizons"]["short"]["factors"].append(copy.deepcopy(value["horizons"]["short"]["factors"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate factor_id"):
            validate_horizon_assessment(value)


if __name__ == "__main__":
    unittest.main()
