import base64
import copy
import hashlib
import unittest
from unittest.mock import patch
from scripts.market_selection.provider_license_gate import (
    ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION, SCHEMA_VERSION as AUTH_SCHEMA_VERSION, evaluate_provider_use,
)
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY, source_entry_sha256

from scripts.market_selection.research_evidence_integration import enrich_research_report
from scripts.market_selection.external_event_evidence import INPUT_SCHEMA
from scripts.market_selection.methodology_contract import METHODOLOGY_SCHEMA


def methodology():
    return {
        "schema_version": METHODOLOGY_SCHEMA,
        "methodology_id": "methodology-test",
        "version": "1.0.0",
        "status": "DRAFT",
        "created_at": "2026-10-20T00:00:00Z",
        "horizons": {
            "short": {"target_window_seconds": 3600, "target": "return", "target_unit": "fraction", "description": "test short"},
            "medium": {"target_window_seconds": 86400, "target": "return", "target_unit": "fraction", "description": "test medium"},
            "long": {"target_window_seconds": 604800, "target": "return", "target_unit": "fraction", "description": "test long"},
        },
        "target_definition": {"formula": "close_end / close_start - 1", "price_source": "fixture", "sampling_rule": "closed candle"},
        "threshold_policy": {"status": "NOT_APPROVED"},
        "validation": {
            "walk_forward": True, "out_of_sample": True, "leakage_checks": True,
            "splits": [{"train_end": "2026-01-01T00:00:00Z", "test_start": "2026-01-02T00:00:00Z", "test_end": "2026-01-03T00:00:00Z"}],
        },
        "cost_model": {
            "fees": {"status": "NOT_AVAILABLE", "basis_points": None},
            "spread": {"status": "NOT_AVAILABLE", "basis_points": None},
            "slippage": {"status": "NOT_AVAILABLE", "basis_points": None},
            "funding_or_borrow": {"status": "NOT_APPLICABLE", "basis_points": None, "reason": "Spot-only fixture"},
            "other": {"status": "NOT_AVAILABLE", "basis_points": None},
        },
        "features": [{"feature_id": "close", "source_id": "fixture", "availability_timestamp_field": "close_time", "transformation_version": "1"}],
    }


def approved_event_source():
    entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"]["sec_press_releases"])
    terms = b"synthetic SEC terms fixture for integration tests"
    entry.update({
        "status": "APPROVED",
        "terms_sha256": hashlib.sha256(terms).hexdigest(),
        "terms_content_base64": base64.b64encode(terms).decode("ascii"),
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T00:00:00Z",
        "allowed_use_cases": ["internal_analysis", "persistent_storage"],
    })
    return entry


def event_authorization(entry):
    return {
        "schema_version": AUTH_SCHEMA_VERSION,
        "provider_id": "sec_press_releases",
        "status": "APPROVED",
        "authorized_use_cases": ["internal_analysis", "persistent_storage"],
        "terms_url": entry["terms_url"],
        "terms_sha256": entry["terms_sha256"],
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T00:00:00Z",
    }


def report():
    return {
        "schema_version": "crypto-asset-research-report-v2",
        "source_artifact": {"provider_use_assessment": {
            "schema_version": ASSESSMENT_SCHEMA_VERSION, "policy_version": POLICY_VERSION,
            "provider_id": "binance_spot_market_data", "use_case": "internal_analysis", "decision": "ALLOW",
            "reason_codes": ["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization": {"authorized_use_cases": ["internal_analysis", "persistent_storage"], "authorization_record_sha256": "b" * 64},
        }},
        "decision_status": "INDETERMINATE",
        "horizons": {h: {"status": "INDETERMINATE", "conclusion": "INDETERMINATE", "reason_codes": []} for h in ("short", "medium", "long")},
        "limitations": [],
        "orders_submitted": False,
        "network_requests_made": False,
    }


def event():
    entry = approved_event_source()
    record = event_authorization(entry)
    internal = evaluate_provider_use("sec_press_releases", "internal_analysis", record)
    storage = evaluate_provider_use("sec_press_releases", "persistent_storage", record)
    return {
        "schema_version": INPUT_SCHEMA,
        "event_id": "event-1",
        "title": "Protocol update",
        "event_type": "PROTOCOL_UPDATE",
        "source": {
            "source_type": "REGULATORY",
            "url": "https://www.sec.gov/news/press-release/example",
            "publisher": "U.S. Securities and Exchange Commission",
        },
        "published_at": "2026-10-20T10:00:00Z",
        "captured_at": "2026-10-20T10:01:00Z",
        "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
        "evidence": [{"url": "https://www.sec.gov/news/press-release/example", "claim": "An update was announced"}],
        "capture_method": "fixture",
        "content_sha256": "a" * 64,
        "license_notes": "Synthetic test authorization; no real source approval.",
        "metadata": {},
        "source_id": "sec_press_releases",
        "provider_id": "sec_press_releases",
        "source_registry_status": "APPROVED",
        "source_registry_entry_sha256": source_entry_sha256(entry),
        "provider_use_assessment": internal,
        "persistent_storage_assessment": storage,
        "provider_policy_assessments": [internal, storage],
    }


class ResearchEvidenceIntegrationTests(unittest.TestCase):
    def test_integrates_contracts_without_promoting_investment_decision(self):
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertEqual(enriched["external_event_evidence"]["assessments"][0]["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(enriched["external_event_evidence"]["assessments"][0]["source_use_assessment"]["decision"], "ALLOW")
        self.assertEqual(enriched["external_event_evidence"]["assessments"][0]["source_storage_assessment"]["decision"], "ALLOW")
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertFalse(enriched["methodology_assessment"]["predictive_performance_validated"])
        self.assertEqual(enriched["fundamental_onchain_assessment"]["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["orders_submitted"])
        self.assertFalse(enriched["network_requests_made"])

    def test_rejects_event_captured_after_historical_cutoff_as_eligible(self):
        ev = event()
        ev["captured_at"] = "2026-10-22T10:01:00Z"
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": ev,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        self.assertEqual(enriched["external_event_evidence"]["assessments"][0]["status"], "NOT_AVAILABLE_AS_OF")
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")

    def test_rejects_duplicate_event_ids(self):
        item = {"event": event(), "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"}}
        with self.assertRaisesRegex(ValueError, "duplicate event_id"):
            with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
                enrich_research_report(
                    report(), events=[item, item], observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )

    def test_missing_provider_authorization_blocks_evidence_integration(self):
        invalid = report()
        invalid.pop("source_artifact")
        with self.assertRaisesRegex(PermissionError, "blocked before use"):
            enrich_research_report(
                invalid, events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_event_without_provider_authorization_is_blocked(self):
        ev = event()
        ev.pop("provider_use_assessment")
        ev.pop("persistent_storage_assessment")
        ev.pop("provider_policy_assessments")
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(PermissionError, "event evidence blocked before use"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": ev,
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )

    def test_event_from_terms_pending_source_is_blocked(self):
        ev = event()
        with self.assertRaisesRegex(PermissionError, "event source registry is not approved"):
            enrich_research_report(
                report(),
                events=[{
                    "event": ev,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_missing_persistent_storage_scope_blocks_report_integration(self):
        invalid = report()
        invalid["source_artifact"]["provider_use_assessment"]["authorization"]["authorized_use_cases"] = ["internal_analysis"]
        with self.assertRaisesRegex(PermissionError, "storage blocked before use"):
            enrich_research_report(
                invalid, events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_rejects_unknown_report_schema(self):
        invalid = report()
        invalid["schema_version"] = "unknown"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            enrich_research_report(
                invalid, events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
