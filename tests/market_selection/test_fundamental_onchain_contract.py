"""Offline tests for versioned fundamental/on-chain evidence contracts."""
import unittest

from scripts.market_selection.fundamental_onchain_contract import (
    METRIC_CATALOG,
    OBSERVATION_SCHEMA,
    adapt_defillama_protocol_tvl,
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

    def test_configured_freshness_policy_marks_old_observation_stale(self):
        result = evaluate_observations(
            [obs()],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            freshness_policy_seconds={"supply.circulating": 3600},
        )
        metric = result["metrics"]["supply.circulating"]
        self.assertEqual(metric["status"], "STALE")
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["stale_observation_ids"], ["obs-1"])
        self.assertEqual(metric["freshness_policy_max_age_seconds"], 3600)
        self.assertEqual(result["coverage"]["stale_observation_ids"], ["obs-1"])

    def test_fresh_observation_wins_over_stale_observation_without_hiding_stale_evidence(self):
        fresh = obs(
            observation_id="obs-fresh",
            value=456.0,
            observed_at="2026-10-20T23:30:00Z",
            captured_at="2026-10-20T23:31:00Z",
            published_at="2026-10-20T23:29:00Z",
        )
        result = evaluate_observations(
            [obs(), fresh],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            freshness_policy_seconds={"supply.circulating": 3600},
        )
        metric = result["metrics"]["supply.circulating"]
        self.assertEqual(metric["status"], "OBSERVED")
        self.assertEqual(metric["value"], 456.0)
        self.assertEqual(metric["stale_observation_ids"], ["obs-1"])
        self.assertEqual(metric["observation_ids"], ["obs-1", "obs-fresh"])

    def test_freshness_policy_is_opt_in_and_does_not_invent_default_age_thresholds(self):
        result = evaluate_observations(
            [obs()],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["metrics"]["supply.circulating"]["status"], "OBSERVED")
        self.assertEqual(result["metrics"]["supply.circulating"]["freshness_policy_max_age_seconds"], None)
        self.assertEqual(result["coverage"]["freshness_policy_seconds"], {})

    def test_rejects_invalid_freshness_policy(self):
        for policy in (
            {"unknown.metric": 3600},
            {"supply.circulating": 0},
            {"supply.circulating": -1},
            {"supply.circulating": True},
            {"supply.circulating": 1.5},
        ):
            with self.subTest(policy=policy):
                with self.assertRaises(ValueError):
                    evaluate_observations(
                        [],
                        asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
                        evaluation_as_of="2026-10-21T00:00:00Z",
                        freshness_policy_seconds=policy,
                    )

    def test_assessment_preserves_source_timestamps_and_quality_evidence(self):
        value = obs(
            quality_notes="Synthetic fixture for provenance retention",
            metadata={"snapshot": "block-21000000"},
        )
        result = evaluate_observations(
            [value],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        evidence = result["metrics"]["supply.circulating"]["observation_evidence"][0]
        self.assertEqual(evidence["observation_id"], "obs-1")
        self.assertEqual(evidence["source"]["source_id"], "provider-a")
        self.assertEqual(evidence["source"]["url"], "https://example.org/asset")
        self.assertEqual(evidence["published_at"], "2026-10-20T10:00:00Z")
        self.assertEqual(evidence["observed_at"], "2026-10-20T09:59:00Z")
        self.assertEqual(evidence["captured_at"], "2026-10-20T10:01:00Z")
        self.assertEqual(evidence["quality_notes"], "Synthetic fixture for provenance retention")
        self.assertEqual(evidence["metadata"], {"snapshot": "block-21000000"})
        self.assertEqual(evidence["assessment_status"], "OBSERVED")
        self.assertEqual(evidence["assessment_value"], 123456.0)

    def test_stale_observation_preserves_raw_value_and_exposes_effective_assessment(self):
        result = evaluate_observations(
            [obs()],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            freshness_policy_seconds={"supply.circulating": 3600},
        )
        evidence = result["metrics"]["supply.circulating"]["observation_evidence"][0]
        self.assertEqual(evidence["status"], "OBSERVED")
        self.assertEqual(evidence["value"], 123456.0)
        self.assertEqual(evidence["assessment_status"], "STALE")
        self.assertIsNone(evidence["assessment_value"])

    def test_future_cutoff_rejection_preserves_observation_evidence(self):
        future = obs(
            published_at="2026-10-21T00:59:00Z",
            observed_at="2026-10-21T01:00:00Z",
            captured_at="2026-10-21T01:01:00Z",
        )
        result = evaluate_observations(
            [future],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        rejected = result["coverage"]["rejected_after_cutoff_observations"]
        self.assertEqual([item["observation_id"] for item in rejected], ["obs-1"])
        self.assertEqual(rejected[0]["source"]["source_id"], "provider-a")
        self.assertEqual(rejected[0]["captured_at"], "2026-10-21T01:01:00Z")
        self.assertEqual(
            result["coverage"]["rejected_after_cutoff_observation_ids"],
            ["obs-1"],
        )

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

    def test_explicit_provider_conflict_cannot_be_overridden_by_an_observed_value(self):
        conflict = obs(
            observation_id="obs-conflict",
            status="CONFLICT",
            value=None,
            source={
                "source_id": "provider-b",
                "source_type": "market_data_provider",
                "url": "https://other.example.org/asset",
                "methodology_url": None,
                "terms_status": "UNKNOWN",
            },
        )
        result = evaluate_observations(
            [obs(), conflict],
            asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        metric = result["metrics"]["supply.circulating"]
        self.assertEqual(metric["status"], "CONFLICT")
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["observation_ids"], ["obs-1", "obs-conflict"])

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

    def test_duplicate_observation_ids_are_rejected(self):
        first = obs(observation_id="duplicate-id", value=123.0)
        second = obs(observation_id="duplicate-id", value=456.0)
        with self.assertRaisesRegex(ValueError, "observation_id values must be unique"):
            evaluate_observations(
                [first, second],
                asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

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
            validate_observation(obs(metric_id="stablecoin.reserve_attestation", unit="categorical_or_usd", value="ATTESTED"))

    def test_period_timestamps_are_normalized_and_ordered(self):
        value = obs(
            period_start="2026-10-19T00:00:00+00:00",
            period_end="2026-10-20T10:00:00+00:00",
        )
        result = validate_observation(value)
        self.assertEqual(result["period_start"], "2026-10-19T00:00:00Z")
        self.assertEqual(result["period_end"], "2026-10-20T10:00:00Z")

    def test_invalid_or_reversed_period_timestamps_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "period_start must be a valid ISO-8601 timestamp"):
            validate_observation(obs(period_start="yesterday"))
        with self.assertRaisesRegex(ValueError, "period_start cannot be after period_end"):
            validate_observation(
                obs(
                    period_start="2026-10-21T00:00:00Z",
                    period_end="2026-10-20T00:00:00Z",
                )
            )

    def test_block_height_must_be_a_non_negative_integer_or_null(self):
        for block_height in (-1, True, 1.5, "21000000"):
            with self.subTest(block_height=block_height):
                with self.assertRaisesRegex(ValueError, "block_height must be a non-negative integer"):
                    validate_observation(obs(block_height=block_height))
        self.assertIsNone(validate_observation(obs(block_height=None))["block_height"])

    def test_invalid_metadata_and_quality_notes_are_rejected_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, "metadata must be an object"):
            validate_observation(obs(metadata=["unexpected"]))
        with self.assertRaisesRegex(ValueError, "quality_notes must be a string"):
            validate_observation(obs(quality_notes={"note": "unexpected"}))

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

    def test_partial_and_provider_error_states_remain_explicit(self):
        for state in ("PARTIAL", "PROVIDER_ERROR", "STALE", "CONFLICT"):
            with self.subTest(state=state):
                result = evaluate_observations(
                    [obs(status=state, value=None)],
                    asset={"category": "smart_contract_token", "stable_id": "ethereum:0xabc"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )
                self.assertEqual(result["metrics"]["supply.circulating"]["status"], state)
                self.assertIsNone(result["metrics"]["supply.circulating"]["value"])

    def test_not_applicable_for_applicable_metric_requires_reason(self):
        with self.assertRaisesRegex(ValueError, "applicability_override_reason"):
            validate_observation(obs(status="NOT_APPLICABLE", value=None))

    def test_defillama_adapter_normalizes_captured_protocol_tvl(self):
        rows = adapt_defillama_protocol_tvl(
            {"name": "Example", "tvl": [
                {"date": 1792368000, "totalLiquidityUSD": 1200.5},
                {"date": 1792454400, "totalLiquidityUSD": 1300.0},
            ]},
            protocol_slug="example-protocol",
            asset_category="defi_protocol_token",
            asset_stable_id="ethereum:0xabc",
            captured_at="2026-10-20T10:00:00Z",
            mapping_evidence_url="https://example.org/token-protocol-relationship",
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["metric_id"], "protocol.tvl")
        self.assertEqual(rows[-1]["source"]["source_id"], "defillama-free-api")
        self.assertEqual(rows[-1]["publication_time_status"], "UNKNOWN")
        self.assertIsNone(rows[-1]["published_at"])
        validated = [validate_observation(row) for row in rows]
        self.assertEqual(validated[-1]["value"], 1300.0)

    def test_defillama_tvl_captured_today_is_rejected_for_past_cutoff(self):
        rows = adapt_defillama_protocol_tvl(
            {"tvl": [{"date": 1792454400, "totalLiquidityUSD": 1300.0}]},
            protocol_slug="example-protocol",
            asset_category="defi_protocol_token",
            asset_stable_id="ethereum:0xabc",
            captured_at="2026-10-22T10:00:00Z",
            mapping_evidence_url="https://example.org/token-protocol-relationship",
        )
        result = evaluate_observations(
            rows,
            asset={"category": "defi_protocol_token", "stable_id": "ethereum:0xabc"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(result["metrics"]["protocol.tvl"]["status"], "NOT_AVAILABLE")
        self.assertEqual(result["coverage"]["rejected_after_cutoff_observation_ids"], [rows[0]["observation_id"]])

    def test_defillama_adapter_rejects_negative_tvl(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            adapt_defillama_protocol_tvl(
                {"tvl": [{"date": 1792454400, "totalLiquidityUSD": -1.0}]},
                protocol_slug="example-protocol",
                asset_category="defi_protocol_token",
                asset_stable_id="ethereum:0xabc",
                captured_at="2026-10-22T10:00:00Z",
                mapping_evidence_url="https://example.org/token-protocol-relationship",
            )

    def test_defillama_adapter_rejects_conflicting_duplicate_timestamps(self):
        with self.assertRaisesRegex(ValueError, "conflicting DefiLlama TVL values"):
            adapt_defillama_protocol_tvl(
                {"tvl": [
                    {"date": 1792454400, "totalLiquidityUSD": 100.0},
                    {"date": 1792454400, "totalLiquidityUSD": 101.0},
                ]},
                protocol_slug="example-protocol",
                asset_category="defi_protocol_token",
                asset_stable_id="ethereum:0xabc",
                captured_at="2026-10-22T10:00:00Z",
                mapping_evidence_url="https://example.org/token-protocol-relationship",
            )


if __name__ == "__main__":
    unittest.main()
