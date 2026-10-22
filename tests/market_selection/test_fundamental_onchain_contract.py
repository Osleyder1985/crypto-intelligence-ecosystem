"""Offline tests for versioned fundamental/on-chain evidence contracts."""
import unittest

from scripts.market_selection.fundamental_onchain_contract import (
    METRIC_CATALOG,
    OBSERVATION_SCHEMA,
    evaluate_observations,
    validate_observation,
)


def obs(**overrides):
    value = {
        "schema_version": OBSERVATION_SCHEMA,
        "observation_id": "obs-1",
        "asset": {"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
        "metric_id": "supply.circulating",
        "status": "OBSERVED",
        "value": 123456.0,
        "unit": "token",
        "period_start": None,
        "period_end": None,
        "block_height": 21000000,
        "published_at": "2026-10-20T10:00:00Z",
        "observed_at": "2026-10-20T09:59:00Z",
        "captured_at": "2026-10-20T10:01:00Z",
        "source": {
            "source_id": "provider-a",
            "source_type": "market_data_provider",
            "url": "https://example.org/asset",
            "methodology_url": "https://example.org/methodology",
            "terms_status": "REVIEW_PENDING",
        },
        "quality_notes": "",
        "metadata": {},
    }
    value.update(overrides)
    return value


class FundamentalOnchainContractTests(unittest.TestCase):
    def test_catalog_is_versioned_and_contains_metric_definitions(self):
        self.assertGreaterEqual(len(METRIC_CATALOG), 10)
        self.assertIn("supply.circulating", METRIC_CATALOG)
        self.assertIn("caveat", METRIC_CATALOG["supply.circulating"])

    def test_valid_observation_normalizes_timestamps(self):
        result = validate_observation(obs())
        self.assertEqual(result["captured_at"], "2026-10-20T10:01:00Z")
        self.assertEqual(result["unit"], "token")

    def test_missing_data_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "value=null, never a fabricated zero"):
            validate_observation(obs(status="NOT_AVAILABLE", value=0))

    def test_non_observed_status_requires_null_value(self):
        result = validate_observation(obs(status="INACCESSIBLE", value=None))
        self.assertEqual(result["status"], "INACCESSIBLE")

    def test_unit_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unit must match catalog unit"):
            validate_observation(obs(unit="usd"))

    def test_future_publication_is_rejected_from_asof_assessment(self):
        result = evaluate_observations(
            [obs(published_at="2026-10-22T11:00:00Z", captured_at="2026-10-22T11:01:00Z")],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["coverage"]["rejected_after_cutoff_observation_ids"], ["obs-1"])
        self.assertEqual(result["metrics"]["supply.circulating"]["status"], "NOT_AVAILABLE")
        self.assertEqual(result["decision_status"], "INDETERMINATE")

    def test_future_capture_is_not_available_at_historical_cutoff(self):
        result = evaluate_observations(
            [obs(captured_at="2026-10-22T11:01:00Z")],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["metrics"]["supply.circulating"]["status"], "NOT_AVAILABLE")
        self.assertIn("obs-1", result["coverage"]["rejected_after_cutoff_observation_ids"])

    def test_conflicting_provider_values_are_not_averaged_or_silently_selected(self):
        second = obs(observation_id="obs-2", value=999999.0,
                     source={"source_id": "provider-b", "source_type": "market_data_provider",
                             "url": "https://other.example.org/asset", "methodology_url": None,
                             "terms_status": "UNKNOWN"})
        result = evaluate_observations(
            [obs(), second],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["metrics"]["supply.circulating"]["status"], "CONFLICT")
        self.assertIsNone(result["metrics"]["supply.circulating"]["value"])

    def test_agreeing_provider_values_are_retained_with_both_sources(self):
        second = obs(observation_id="obs-2", source={
            "source_id": "provider-b", "source_type": "market_data_provider",
            "url": "https://other.example.org/asset", "methodology_url": None, "terms_status": "UNKNOWN"
        })
        result = evaluate_observations(
            [obs(), second],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        metric = result["metrics"]["supply.circulating"]
        self.assertEqual(metric["status"], "OBSERVED")
        self.assertEqual(metric["source_ids"], ["provider-a", "provider-b"])

    def test_asset_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "exact target stable_id"):
            evaluate_observations(
                [obs()],
                asset={"category": "smart_contract_token", "stable_id": "ethereum:0xdef"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_category_specific_metric_is_not_applicable_without_zero(self):
        result = evaluate_observations(
            [],
            asset={"category": "native_l1", "stable_id": "bitcoin"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["metrics"]["stablecoin.reserve_attestation"]["status"], "NOT_APPLICABLE")
        self.assertIsNone(result["metrics"]["stablecoin.reserve_attestation"]["value"])

    def test_wrong_category_for_metric_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not defined as applicable"):
            validate_observation(obs(metric_id="stablecoin.reserve_attestation", unit="categorical_or_usd"))

    def test_capture_before_observation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot precede observed_at"):
            validate_observation(obs(captured_at="2026-10-20T09:00:00Z"))

    def test_na_is_explicit_not_numeric_zero(self):
        result = evaluate_observations(
            [],
            asset={"category": "native_l1", "stable_id": "bitcoin"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        metric = result["metrics"]["stablecoin.reserve_attestation"]
        self.assertEqual(metric["status"], "NOT_APPLICABLE")
        self.assertIsNone(metric["value"])

    def test_quantitative_metric_rejects_categorical_value(self):
        with self.assertRaisesRegex(ValueError, "quantitative metric values must be numeric"):
            validate_observation(obs(value="one hundred"))

    def test_fraction_outside_unit_interval_is_rejected(self):
        value = obs(metric_id="distribution.holder_concentration", unit="fraction", value=1.5)
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            validate_observation(value)

    def test_applicable_metric_can_be_not_applicable_only_with_reason(self):
        value = obs(status="NOT_APPLICABLE", value=None, applicability_override_reason="Asset has no token unlock schedule by design.")
        result = validate_observation(value)
        self.assertEqual(result["status"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
