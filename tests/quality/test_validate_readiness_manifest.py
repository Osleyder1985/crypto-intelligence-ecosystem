import unittest
from scripts.quality.validate_readiness_manifest import REQUIRED_GATES, validate_manifest


def valid_manifest():
    return {
        "case_id": "readiness-test-001",
        "product_version": "candidate-0.1",
        "product_sha": "a" * 40,
        "environment": "isolated-test-environment",
        "executed_at_utc": "2026-10-20T12:00:00Z",
        "executor": "test-operator-role",
        "independent_reviewer": "reviewer-role-identified",
        "risk_acceptance_authority": "release-authority-role",
        "decision": "NOT_READY",
        "gates": [
            {"id": gate, "status": "NOT_RUN"}
            for gate in sorted(REQUIRED_GATES)
        ],
        "residual_risks": [],
    }


class ReadinessManifestTests(unittest.TestCase):
    def test_complete_not_ready_manifest_is_valid(self):
        self.assertEqual(validate_manifest(valid_manifest()), [])

    def test_missing_gate_is_rejected(self):
        manifest = valid_manifest()
        manifest["gates"].pop()
        self.assertTrue(any("Falta la puerta obligatoria" in e for e in validate_manifest(manifest)))

    def test_pass_requires_result_evidence_and_execution_time(self):
        manifest = valid_manifest()
        manifest["gates"][0].update({"status": "PASS"})
        errors = validate_manifest(manifest)
        self.assertTrue(any("observed_result" in e for e in errors))
        self.assertTrue(any("evidencia verificable" in e for e in errors))
        self.assertTrue(any("executed_at_utc" in e for e in errors))

    def test_ready_rejected_when_any_gate_not_pass(self):
        manifest = valid_manifest()
        manifest["decision"] = "READY"
        errors = validate_manifest(manifest)
        self.assertTrue(any("decision=READY no permitido" in e for e in errors))

    def test_invalid_utc_timestamp_is_rejected(self):
        manifest = valid_manifest()
        manifest["executed_at_utc"] = "2026-10-20T12:00:00+02:00"
        self.assertTrue(any("formato inválido" in e for e in validate_manifest(manifest)))

    def test_unapproved_high_risk_is_rejected(self):
        manifest = valid_manifest()
        manifest["residual_risks"] = [{"severity": "high", "status": "open"}]
        self.assertTrue(any("sin excepción aprobada" in e for e in validate_manifest(manifest)))

    def test_high_risk_exception_requires_approver_justification_and_utc_expiry(self):
        manifest = valid_manifest()
        manifest["residual_risks"] = [{
            "severity": "HIGH",
            "status": "approved_exception",
            "approved_by": "release-authority",
            "justification": "temporary documented mitigation",
            "expires_at_utc": "2026-12-01T00:00:00Z",
        }]
        self.assertEqual(validate_manifest(manifest), [])

    def test_high_risk_exception_without_approval_evidence_is_rejected(self):
        manifest = valid_manifest()
        manifest["residual_risks"] = [{
            "severity": "High",
            "status": "approved_exception",
        }]
        self.assertTrue(any("excepción aprobada completa" in e for e in validate_manifest(manifest)))

    def test_high_risk_exception_requires_utc_expiry(self):
        manifest = valid_manifest()
        manifest["residual_risks"] = [{
            "severity": "critical",
            "status": "approved_exception",
            "approved_by": "release-authority",
            "justification": "temporary documented mitigation",
            "expires_at_utc": "2026-12-01T02:00:00+02:00",
        }]
        self.assertTrue(any("expires_at_utc debe ser ISO 8601 UTC" in e for e in validate_manifest(manifest)))

    def test_expired_high_risk_exception_is_rejected_at_execution_time(self):
        manifest = valid_manifest()
        manifest["residual_risks"] = [{
            "severity": "critical",
            "status": "approved_exception",
            "approved_by": "release-authority",
            "justification": "temporary documented mitigation",
            "expires_at_utc": "2026-10-19T23:59:59Z",
        }]
        errors = validate_manifest(manifest)
        self.assertTrue(any("ya había expirado en executed_at_utc" in e for e in errors))

    def test_non_object_root_is_rejected(self):
        self.assertTrue(validate_manifest([]))


if __name__ == "__main__":
    unittest.main()
