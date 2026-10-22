"""Tests for fail-closed provider authorization gate."""
import unittest

from scripts.market_selection.provider_license_gate import (
    SCHEMA_VERSION,
    POLICY_VERSION,
    evaluate_artifact_use,
    evaluate_provider_use,
)

BASE = {
    "schema_version": SCHEMA_VERSION,
    "provider_id": "coingecko_api",
    "status": "APPROVED",
    "authorized_use_cases": ["internal_analysis"],
    "terms_url": "https://www.coingecko.com/en/api_terms",
    "terms_sha256": "a" * 64,
    "reviewed_at": "2026-10-22T12:00:00Z",
    "reviewed_by": "source-governance-review",
    "plan_name": "Analyst",
}


class ProviderLicenseGateTests(unittest.TestCase):
    def test_authorization_evidence_includes_policy_version_scope_and_record_hash(self):
        result = evaluate_provider_use("coingecko_api", "internal_analysis", BASE)
        self.assertEqual(result["policy_version"], POLICY_VERSION)
        self.assertEqual(result["authorization"]["authorized_use_cases"], ["internal_analysis"])
        self.assertRegex(result["authorization"]["authorization_record_sha256"], r"^[0-9a-f]{64}$")

    def test_artifact_use_requires_explicit_downstream_scope(self):
        record = dict(BASE, provider_id="binance_spot_market_data", authorized_use_cases=["persistent_storage", "internal_analysis"])
        capture = evaluate_provider_use("binance_spot_market_data", "persistent_storage", record)
        allowed = evaluate_artifact_use({"provider_use_assessment": capture}, "internal_analysis")
        self.assertEqual(allowed["decision"], "ALLOW")
        record["authorized_use_cases"] = ["persistent_storage"]
        capture = evaluate_provider_use("binance_spot_market_data", "persistent_storage", record)
        blocked = evaluate_artifact_use({"provider_use_assessment": capture}, "internal_analysis")
        self.assertEqual(blocked["decision"], "BLOCK")
        self.assertIn("DOWNSTREAM_USE_CASE_NOT_EXPLICITLY_AUTHORIZED", blocked["reason_codes"])

    def test_downstream_consumer_blocks_unreviewed_provider_even_with_claimed_allow(self):
        forged = {"schema_version": "crypto-provider-use-assessment-v1", "policy_version": POLICY_VERSION,
                  "provider_id": "unknown_feed", "use_case": "persistent_storage", "decision": "ALLOW",
                  "authorization": {"authorized_use_cases": ["internal_analysis"], "authorization_record_sha256": "b" * 64}}
        result = evaluate_artifact_use({"provider_use_assessment": forged}, "internal_analysis")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("PROVIDER_NOT_REVIEWED", result["reason_codes"])

    def test_technical_test_permission_does_not_authorize_internal_analysis(self):
        capture = evaluate_provider_use("binance_spot_market_data", "live_technical_test")
        result = evaluate_artifact_use({"provider_use_assessment": capture}, "internal_analysis")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("AUTHORIZATION_EVIDENCE_MISSING_FOR_DOWNSTREAM_USE", result["reason_codes"])

    def test_binance_only_allows_live_technical_test_by_baseline(self):
        allowed = evaluate_provider_use("binance_spot_market_data", "live_technical_test")
        self.assertEqual(allowed["decision"], "ALLOW")
        self.assertEqual(allowed["authorization_evidence_status"], "NOT_A_COMMERCIAL_LICENSE")
        blocked = evaluate_provider_use("binance_spot_market_data", "persistent_storage")
        self.assertEqual(blocked["decision"], "BLOCK")

    def test_sec_press_releases_is_registered_but_requires_explicit_authorization(self):
        for use_case in SUPPORTED_USE_CASES:
            with self.subTest(use_case=use_case):
                result = evaluate_provider_use("sec_press_releases", use_case, None)
                self.assertEqual(result["decision"], "BLOCK")
                self.assertIn("AUTHORIZATION_RECORD_MISSING", result["reason_codes"])

    def test_unknown_provider_fails_closed(self):
        result = evaluate_provider_use("unknown_feed", "internal_analysis")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("PROVIDER_NOT_REVIEWED", result["reason_codes"])

    def test_defillama_requires_written_authorization(self):
        result = evaluate_provider_use("defillama_api", "internal_analysis")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("AUTHORIZATION_RECORD_MISSING", result["reason_codes"])

    def test_defillama_written_authorization_is_required_even_when_approved(self):
        record = dict(BASE, provider_id="defillama_api", authorized_use_cases=["internal_analysis"])
        with self.assertRaisesRegex(ValueError, "written_authorization_url"):
            evaluate_provider_use("defillama_api", "internal_analysis", record)

    def test_coingecko_missing_record_blocks(self):
        result = evaluate_provider_use("coingecko_api", "public_display")
        self.assertEqual(result["decision"], "BLOCK")

    def test_coingecko_demo_plan_blocks_commercial_use(self):
        record = dict(BASE, authorized_use_cases=["public_display"], plan_name="Demo")
        record.update(attribution_text="Data powered by CoinGecko", attribution_url="https://www.coingecko.com/en/api")
        result = evaluate_provider_use("coingecko_api", "public_display", record)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("PAID_PLAN_REQUIRED_FOR_COMMERCIAL_PRODUCT", result["reason_codes"])

    def test_coingecko_public_display_requires_attribution(self):
        record = dict(BASE, authorized_use_cases=["public_display"])
        with self.assertRaisesRegex(ValueError, "attribution_text"):
            evaluate_provider_use("coingecko_api", "public_display", record)

    def test_coingecko_cache_policy_requires_refresh_encryption_and_deletion(self):
        record = dict(BASE, authorized_use_cases=["persistent_storage"], cache_refresh_hours=24,
                      encrypted_storage=True, delete_on_termination=True)
        result = evaluate_provider_use("coingecko_api", "persistent_storage", record)
        self.assertEqual(result["decision"], "ALLOW")
        bad = dict(record, cache_refresh_hours=25)
        with self.assertRaisesRegex(ValueError, "at most 24"):
            evaluate_provider_use("coingecko_api", "persistent_storage", bad)

    def test_coingecko_redistribution_requires_custom_rights(self):
        record = dict(BASE, authorized_use_cases=["export_redistribution"])
        result = evaluate_provider_use("coingecko_api", "export_redistribution", record)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("CUSTOM_REDISTRIBUTION_RIGHTS_REQUIRED", result["reason_codes"])

    def test_scope_mismatch_blocks(self):
        result = evaluate_provider_use("coingecko_api", "persistent_storage", BASE)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("USE_CASE_NOT_EXPLICITLY_AUTHORIZED", result["reason_codes"])

    def test_authorization_record_provider_mismatch_rejected(self):
        record = dict(BASE, provider_id="defillama_api")
        with self.assertRaisesRegex(ValueError, "does not match requested provider"):
            evaluate_provider_use("coingecko_api", "internal_analysis", record)

    def test_invalid_terms_hash_rejected(self):
        record = dict(BASE, terms_sha256="not-a-hash")
        with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
            evaluate_provider_use("coingecko_api", "internal_analysis", record)


if __name__ == "__main__":
    unittest.main()
