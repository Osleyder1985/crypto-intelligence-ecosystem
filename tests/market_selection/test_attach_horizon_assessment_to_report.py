"""Pruebas offline para adjuntar evaluaciones independientes por horizonte a informes."""
import copy
import hashlib
import json
import unittest

from scripts.market_selection.attach_horizon_assessment_to_report import (
    INTEGRATION_SCHEMA,
    attach_horizon_assessment,
)
from scripts.market_selection.horizon_assessment_contract import ASSESSMENT_SCHEMA
from scripts.market_selection.research_report import REPORT_SCHEMA


def dimension(status="SUPPORTED"):
    return {"status": status, "rationale": "Basado en evidencia registrada", "evidence_refs": ["evidence-1"]}


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
            "rationale": "El rendimiento de velas cerradas está disponible para este horizonte",
            "source_id": "spot-ohlcv",
            "transformation_version": "return-v1",
            "observed_at": "2026-10-20T09:58:00Z",
            "captured_at": "2026-10-20T09:59:00Z",
        }, {
            "factor_id": "unverified-rumor",
            "category": "EXTERNAL_EVENT",
            "decision": "EXCLUDED",
            "rationale": "No hay fuente verificable ni fecha de publicación",
            "source_id": "unverified",
            "transformation_version": "raw-v1",
            "observed_at": "2026-10-20T09:00:00Z",
            "captured_at": "2026-10-20T09:30:00Z",
        }],
        "scenarios": {
            "FAVORABLE": {"conditions": ["El soporte observado se mantiene"], "invalidation_rules": ["Cierre de vela por debajo del soporte"]},
            "BASE": {"conditions": ["El precio permanece en el rango observado"], "invalidation_rules": ["Cierre fuera del límite del rango"]},
            "ADVERSE": {"conditions": ["La liquidez se deteriora"], "invalidation_rules": ["La liquidez se normaliza según la regla declarada"]},
        },
    }


def assessment():
    return {
        "schema_version": ASSESSMENT_SCHEMA,
        "assessment_id": "evaluacion-activo-001",
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


class AttachHorizonAssessmentTests(unittest.TestCase):
    def test_attaches_independent_horizons_without_aggregation_or_decision_change(self):
        original = report()
        result = attach_horizon_assessment(original, assessment())
        attached = result["horizon_assessment"]
        self.assertEqual(attached["integration_schema"], INTEGRATION_SCHEMA)
        self.assertEqual(attached["status"], "VALIDATED_ASSESSMENT_ATTACHED")
        self.assertEqual(attached["assessment"]["horizons"]["short"]["conclusion"], "FAVORABLE")
        self.assertEqual(attached["assessment"]["horizons"]["medium"]["conclusion"], "BASE")
        self.assertEqual(attached["assessment"]["horizons"]["long"]["conclusion"], "ADVERSE")
        self.assertEqual(attached["assessment"]["aggregation"], "NONE")
        self.assertEqual(result["horizons"], original["horizons"])
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])
        self.assertNotIn("horizon_assessment", original)

    def test_preserves_exact_source_hashes(self):
        original, item = report(), assessment()
        report_raw = json.dumps(original, sort_keys=True).encode("utf-8")
        assessment_raw = json.dumps(item, sort_keys=True).encode("utf-8")
        result = attach_horizon_assessment(original, item, report_bytes=report_raw, assessment_bytes=assessment_raw)
        attached = result["horizon_assessment"]
        self.assertEqual(attached["source_report_sha256"], hashlib.sha256(report_raw).hexdigest())
        self.assertEqual(attached["source_assessment_sha256"], hashlib.sha256(assessment_raw).hexdigest())

    def test_rejects_asset_mismatch(self):
        item = assessment()
        item["asset_id"] = "binance:ETHUSDT"
        with self.assertRaisesRegex(ValueError, "exactly match"):
            attach_horizon_assessment(report(), item)

    def test_rejects_wrong_report_schema(self):
        item = report()
        item["schema_version"] = "unknown"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            attach_horizon_assessment(item, assessment())

    def test_rejects_non_indeterminate_report(self):
        item = report()
        item["decision_status"] = "FAVORABLE"
        with self.assertRaisesRegex(ValueError, "only INDETERMINATE"):
            attach_horizon_assessment(item, assessment())

    def test_rejects_order_submission_claim(self):
        item = report()
        item["orders_submitted"] = True
        with self.assertRaisesRegex(ValueError, "orders_submitted must be false"):
            attach_horizon_assessment(item, assessment())

    def test_refuses_to_overwrite_existing_assessment(self):
        item = report()
        item["horizon_assessment"] = {"status": "EXISTING"}
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            attach_horizon_assessment(item, assessment())

    def test_rejects_mismatched_raw_bytes(self):
        with self.assertRaisesRegex(ValueError, "report_bytes do not match"):
            attach_horizon_assessment(report(), assessment(), report_bytes=b'{"wrong": true}')

    def test_rejects_feature_after_data_cutoff(self):
        item = assessment()
        item["horizons"]["short"]["factors"][0]["captured_at"] = "2026-10-20T10:00:01Z"
        with self.assertRaisesRegex(ValueError, "not available at data_as_of"):
            attach_horizon_assessment(report(), item)

    def test_rejects_abstention_with_non_indeterminate_conclusion(self):
        item = assessment()
        item["horizons"]["short"]["decision_mode"] = "ABSTAIN"
        item["horizons"]["short"]["abstention_reasons"] = ["Evidencia insuficiente"]
        with self.assertRaisesRegex(ValueError, "must be INDETERMINATE"):
            attach_horizon_assessment(report(), item)

    def test_rejects_non_object_report(self):
        with self.assertRaisesRegex(ValueError, "report must be a JSON object"):
            attach_horizon_assessment([], assessment())


if __name__ == "__main__":
    unittest.main()
