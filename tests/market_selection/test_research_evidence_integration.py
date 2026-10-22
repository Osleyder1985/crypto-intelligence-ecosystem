import unittest
from scripts.market_selection.provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION

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


def report():
    return {
        "schema_version": "crypto-asset-research-report-v2",
        "source_artifact": {"provider_use_assessment": {
            "schema_version": ASSESSMENT_SCHEMA_VERSION, "policy_version": POLICY_VERSION,
            "provider_id": "binance_spot_market_data", "use_case": "internal_analysis", "decision": "ALLOW",
            "reason_codes": ["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization": {"authorized_use_cases": ["internal_analysis"], "authorization_record_sha256": "b" * 64},
        }},
        "decision_status": "INDETERMINATE",
        "horizons": {h: {"status": "INDETERMINATE", "conclusion": "INDETERMINATE", "reason_codes": []} for h in ("short", "medium", "long")},
        "limitations": [],
        "orders_submitted": False,
        "network_requests_made": False,
    }


def event():
    return {
        "schema_version": INPUT_SCHEMA,
        "event_id": "event-1",
        "title": "Protocol update",
        "event_type": "PROTOCOL_UPDATE",
        "source": {"source_type": "PRIMARY_OFFICIAL", "url": "https://example.org/update", "publisher": "Example"},
        "published_at": "2026-10-20T10:00:00Z",
        "captured_at": "2026-10-20T10:01:00Z",
        "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
        "evidence": [{"url": "https://example.org/update", "claim": "An update was announced"}],
        "capture_method": "fixture",
        "content_sha256": "a" * 64,
        "license_notes": "Review pending",
        "metadata": {},
    }


class ResearchEvidenceIntegrationTests(unittest.TestCase):
    def test_integrates_contracts_without_promoting_investment_decision(self):
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
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertFalse(enriched["methodology_assessment"]["predictive_performance_validated"])
        self.assertEqual(enriched["fundamental_onchain_assessment"]["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["orders_submitted"])
        self.assertFalse(enriched["network_requests_made"])

    def test_rejects_event_captured_after_historical_cutoff_as_eligible(self):
        ev = event()
        ev["captured_at"] = "2026-10-22T10:01:00Z"
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
