import base64
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
from scripts.market_selection.provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION, SCHEMA_VERSION as AUTH_SCHEMA_VERSION
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY, source_entry_sha256
from scripts.market_selection.capture_sec_press_releases_rss import (
    capture_sec_press_release_article, capture_sec_press_releases_rss, promote_sec_press_release_to_event,
)

from scripts.market_selection.research_evidence_integration import enrich_research_report, _verify_source_capture
from scripts.market_selection.methodology_contract import METHODOLOGY_SCHEMA
from test_analyze_support_resistance import artifact as support_artifact, candle as support_candle


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
        "reviewed_at": "2026-10-19T00:00:00Z",
        "allowed_use_cases": ["internal_analysis", "persistent_storage"],
        "approval_scope": {
            "allowed_content": {
                "metadata": True,
                "official_text": True,
                "full_html": True,
                "attachments": False,
            },
            "third_party_content": {"handling": "EXCLUDED"},
            "retention": {
                "stored_fields": ["source URL", "original response bytes", "SHA-256"],
                "duration": "Synthetic fixture only; not a production retention policy",
                "deletion_or_recheck_rule": "Re-review before any non-test use",
            },
            "attribution": {"required": True, "format": "Synthetic test fixture; source URL"},
            "automated_access": {
                "approved_endpoint": entry["source_url"],
                "user_agent": "CryptoIntelligenceTest/1.0 (contact: offline-test-fixture)",
                "max_aggregate_requests_per_second": entry["max_requests_per_second"],
                "timeout_seconds": 5,
                "redirect_policy": "HTTPS only; each redirect must remain inside the source allowlist",
            },
            "limitations": ["Synthetic approval fixture; grants no real-world permission"],
            "decision_rationale": "Fixture solely for offline contract tests.",
        },
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
        "reviewed_at": "2026-10-19T00:00:00Z",
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


def support_resistance_input(*, stable_id="example-asset", category="smart_contract_token"):
    rows = [
        support_candle(0, 10, 11, 9, 10),
        support_candle(1, 10, 11, 8, 9),
        support_candle(2, 9, 10, 7, 8),
        support_candle(3, 8, 9, 8, 8.5),
        support_candle(4, 8.5, 10, 8, 9.5),
        support_candle(5, 9.5, 11, 9, 10.5),
    ]
    base_ms = 1792454400000
    for index, row in enumerate(rows):
        row["open_time_ms"] = base_ms + index * 3_600_000
        row["close_time_ms"] = base_ms + (index + 1) * 3_600_000 - 1
    return {
        "schema_version": "research-support-resistance-input-v1",
        "asset": {"stable_id": stable_id, "category": category},
        "asset_mapping_evidence_url": "https://example.org/reviewed-token-market-mapping",
        "artifacts": [support_artifact(rows)],
        "parameters": {
            "pivot_left": 1,
            "pivot_right": 1,
            "tolerance_bps": 100,
            "confluence_tolerance_bps": 100,
        },
    }


def fundamental_observation(*, terms_status="REVIEW_PENDING", authorization_record=None):
    source = {
        "source_id": "defillama-free-api",
        "provider_id": "defillama_api",
        "source_type": "aggregator",
        "url": "https://api.llama.fi/protocol/example",
        "methodology_url": "https://defillama.com/data-definitions",
        "terms_status": terms_status,
    }
    if authorization_record is not None:
        source["authorization_record"] = authorization_record
    return {
        "schema_version": "crypto-fundamental-observation-v1",
        "observation_id": "tvl-example-20261020",
        "asset": {"category": "smart_contract_token", "stable_id": "example-asset"},
        "metric_id": "protocol.tvl",
        "status": "OBSERVED",
        "value": 123456.0,
        "unit": "usd",
        "period_start": None,
        "period_end": "2026-10-20T10:00:00Z",
        "block_height": None,
        "published_at": None,
        "publication_time_status": "UNKNOWN",
        "observed_at": "2026-10-20T10:00:00Z",
        "captured_at": "2026-10-20T10:01:00Z",
        "source": source,
        "quality_notes": "Synthetic test fixture; not real provider authorization.",
        "metadata": {"protocol_slug": "example"},
    }


def approved_defillama_authorization_fixture():
    # Synthetic fixture for exercising policy logic only; it grants no real-world rights.
    return {
        "schema_version": AUTH_SCHEMA_VERSION,
        "provider_id": "defillama_api",
        "status": "APPROVED",
        "authorized_use_cases": ["internal_analysis", "persistent_storage"],
        "terms_url": "https://defillama.com/terms",
        "terms_sha256": "a" * 64,
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-20T00:00:00Z",
        "written_authorization_url": "https://example.org/synthetic-authorization-fixture",
        "written_authorization_sha256": "b" * 64,
    }


class FakeResponse:
    def __init__(self, raw, headers):
        self.raw = raw
        self.headers = headers
        self.status = 200
        self.offset = 0

    def read(self, size=-1):
        if self.offset >= len(self.raw):
            return b""
        end = len(self.raw) if size is None or size < 0 else min(len(self.raw), self.offset + size)
        chunk = self.raw[self.offset:end]
        self.offset = end
        return chunk

    def close(self):
        pass


def event():
    entry = approved_event_source()
    record = event_authorization(entry)
    feed_raw = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel><title>SEC fixture feed</title>'
        '<item><title>Protocol update</title>'
        '<link>https://www.sec.gov/news/press-release/example</link>'
        '<guid>https://www.sec.gov/news/press-release/example</guid>'
        '<pubDate>Tue, 20 Oct 2026 10:00:00 GMT</pubDate>'
        '<description>An update was announced</description></item>'
        '</channel></rss>'
    ).encode("utf-8")
    article_raw = b"<html><title>Protocol update</title><body>An update was announced</body></html>"
    mapping_raw = b"synthetic reviewed entity mapping evidence"
    user_agent = "CryptoIntelligenceTest/1.0 (contact: offline-test-fixture)"
    with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": entry}):
        feed = capture_sec_press_releases_rss(
            record, user_agent, 5, captured_at="2026-10-20T10:01:00Z",
            opener=lambda *args, **kwargs: FakeResponse(feed_raw, {"Content-Type": "application/rss+xml"}),
        )
        feed_item = feed["feed_items"][0]
        article = capture_sec_press_release_article(
            feed_item["link"], record, user_agent, 5, captured_at="2026-10-20T10:02:00Z",
            opener=lambda *args, **kwargs: FakeResponse(article_raw, {"Content-Type": "text/html"}),
        )
        return promote_sec_press_release_to_event(
            feed, feed_item["item_id"], article, "PROTOCOL_UPDATE", "An update was announced",
            {
                "status": "APPROVED",
                "reviewed_by": "offline-test-fixture",
                "reviewed_at": "2026-10-20T10:03:00Z",
                "evidence_record_base64": base64.b64encode(mapping_raw).decode("ascii"),
                "evidence_record_sha256": hashlib.sha256(mapping_raw).hexdigest(),
                "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
            },
        )


def fact_review_for(event_record, decision="VERIFIED_PRIMARY_SOURCE", reviewed_at="2026-10-20T10:04:00Z", evidence_refs=None):
    refs = evidence_refs or [{
        "url": event_record["source"]["url"],
        "role": "PRIMARY_SOURCE",
        "publisher": "SEC",
    }]
    review_record = {
        "schema_version": "crypto-event-fact-review-v1",
        "event_id": event_record["event_id"],
        "decision": decision,
        "reviewed_by": "offline-fact-reviewer",
        "reviewed_at": reviewed_at,
        "rationale": "Synthetic reviewer rationale; this fixture is not a real fact verification.",
        "evidence_refs": refs,
    }
    raw = json.dumps(review_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **review_record,
        "evidence_record_base64": base64.b64encode(raw).decode("ascii"),
        "evidence_record_sha256": hashlib.sha256(raw).hexdigest(),
    }


def causal_review_for(event_record, decision="SUPPORTED_CAUSALITY", reviewed_at="2026-10-20T10:05:00Z", evidence_refs=None, alternative_explanations=None):
    refs = evidence_refs or [
        {"url": event_record["source"]["url"], "role": "PRIMARY_SOURCE", "publisher": "SEC"},
        {"url": "https://data.example.org/market-snapshot/123", "role": "MARKET_DATA", "publisher": "MarketDataProvider"},
    ]
    alternatives = alternative_explanations or [
        "Broad market movement may explain part of the price response.",
        "Concurrent liquidity changes may be a confounding factor.",
    ]
    review_record = {
        "schema_version": "crypto-event-causal-review-v1",
        "event_id": event_record["event_id"],
        "decision": decision,
        "reviewed_by": "offline-causal-reviewer",
        "reviewed_at": reviewed_at,
        "rationale": "Synthetic reviewed causal rationale; fixture is not proof of real-world causality.",
        "methodology_id": "event-causality-review-v1",
        "evidence_refs": refs,
        "alternative_explanations": alternatives,
    }
    raw = json.dumps(review_record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **review_record,
        "evidence_record_base64": base64.b64encode(raw).decode("ascii"),
        "evidence_record_sha256": hashlib.sha256(raw).hexdigest(),
    }


class ResearchEvidenceIntegrationTests(unittest.TestCase):
    def test_source_capture_verifier_accepts_hash_checked_text_only_archive_evidence(self):
        entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"]["federal_reserve_press_release_archive"])
        registry_hash = source_entry_sha256(entry)
        evidence_bytes = json.dumps(
            {
                "schema_version": "official-archive-text-evidence-v1",
                "anchors": [{"href": "/newsevents/pressreleases/example.htm", "text": "Official title"}],
                "page_text": ["Official title", "September 24, 2026"],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        capture = {
            "capture_status": "PASS",
            "capture_truncated": False,
            "network_request_made": True,
            "source_registry_status": "APPROVED",
            "source_registry_entry_sha256": registry_hash,
            "source_url": entry["source_url"],
            "requested_url": entry["source_url"],
            "provider_use_assessment": {"provider_id": entry["provider_id"], "decision": "ALLOW"},
            "persistent_storage_assessment": {"provider_id": entry["provider_id"], "decision": "ALLOW"},
            "raw_response_sha256": "a" * 64,
            "raw_response_bytes": 98765,
            "stored_content_mode": "EXTRACTED_TEXT_EVIDENCE",
            "raw_response_base64": None,
            "text_evidence_base64": base64.b64encode(evidence_bytes).decode("ascii"),
            "text_evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "text_evidence_bytes": len(evidence_bytes),
        }
        verified = _verify_source_capture(
            capture,
            field="test.archive_capture",
            source_entry=entry,
            registry_hash=registry_hash,
            expected_requested_url=entry["source_url"],
        )
        self.assertEqual(verified, evidence_bytes)
        capture["text_evidence_sha256"] = "b" * 64
        with self.assertRaisesRegex(PermissionError, "extracted text evidence integrity"):
            _verify_source_capture(
                capture,
                field="test.archive_capture",
                source_entry=entry,
                registry_hash=registry_hash,
                expected_requested_url=entry["source_url"],
            )


    def test_event_for_different_stable_entity_does_not_support_movement_episode(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-entity-mismatch",
                "direction": "BULLISH",
                "start": {"pivot_open_time_ms": 1792486800000},  # 09:00Z
                "end": {"pivot_open_time_ms": 1792494000000},    # 11:00Z
                "episode_observable_only_at_ms": 1792494000001,
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),  # Explicitly identifies example-asset.
                    "target_entity": {"id_type": "coingecko_id", "id": "different-asset"},
                    "movement_episode_id": "swing-entity-mismatch",
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        summary = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertFalse(assessment["entity_match"])
        self.assertEqual(assessment["status"], "ENTITY_NOT_MATCHED")
        self.assertEqual(assessment["causality_label"], "CAUSE_UNIDENTIFIED")
        self.assertEqual(summary["status"], "NO_SUPPORTING_EVENT_IN_SUPPLIED_EVIDENCE")
        self.assertFalse(assessment["causality_claimed"])
        self.assertFalse(summary["causality_claimed"])

    def test_terms_pending_event_source_blocks_network_capture(self):
        authorization = event_authorization(approved_event_source())

        def forbidden_opener(*args, **kwargs):
            raise AssertionError("network opener must not be called for a terms-pending source")

        result = capture_sec_press_releases_rss(
            authorization,
            "CryptoIntelligenceTest/1.0 (contact: offline-test-fixture)",
            5,
            captured_at="2026-10-20T10:01:00Z",
            opener=forbidden_opener,
        )

        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])
        self.assertIn("SOURCE_TERMS_PENDING", result["reason_codes"])
        self.assertIn("SOURCE_USE_CASES_NOT_APPROVED", result["reason_codes"])

    def test_event_captured_after_evaluation_cutoff_is_not_available_as_of(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-evaluation-cutoff",
                "direction": "BEARISH",
                "start": {"pivot_open_time_ms": 1792483200000},  # 08:00Z
                "end": {"pivot_open_time_ms": 1792488600000},    # 09:30Z
                "episode_observable_only_at_ms": 1792488660000,  # 09:31Z
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),  # published 10:00Z, captured 10:02Z
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-evaluation-cutoff",
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-20T10:01:00Z",
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        summary = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertEqual(assessment["status"], "NOT_AVAILABLE_AS_OF")
        self.assertEqual(assessment["causality_label"], "CAUSE_UNIDENTIFIED")
        self.assertEqual(assessment["movement_episode"]["event_relation_to_swing"], "FOLLOWS_SWING")
        self.assertEqual(summary["status"], "NO_SUPPORTING_EVENT_IN_SUPPLIED_EVIDENCE")
        self.assertFalse(assessment["causality_claimed"])
        self.assertFalse(summary["causality_claimed"])

    def test_episode_summary_reports_temporal_association_without_causal_claim(self):
        enriched_report = report()
        start_ms = 1792486800000
        end_ms = 1792494000000
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {
                "schema_version": "ohlcv-movement-episodes-v1",
                "episodes": [{
                    "episode_id": "swing-1", "direction": "BULLISH",
                    "start": {"pivot_open_time_ms": start_ms},
                    "end": {"pivot_open_time_ms": end_ms},
                    "episode_observable_only_at_ms": end_ms + 1,
                }],
            },
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-1",
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        summary = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertEqual(summary["status"], "TEMPORAL_ASSOCIATION_ONLY")
        self.assertEqual(summary["event_ids"], [enriched["external_event_evidence"]["assessments"][0]["event_id"]])
        self.assertFalse(summary["causality_claimed"])

    def test_episode_link_excludes_event_captured_after_observability_cutoff(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-cutoff",
                "direction": "BEARISH",
                "start": {"pivot_open_time_ms": 1792483200000},  # 08:00Z
                "end": {"pivot_open_time_ms": 1792488600000},    # 09:30Z
                "episode_observable_only_at_ms": 1792490460000,  # 10:01Z
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),  # published 10:00Z, captured 10:02Z
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-cutoff",
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        summary = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertEqual(assessment["status"], "NOT_AVAILABLE_AT_DECISION_TIME")
        self.assertEqual(assessment["causality_label"], "CAUSE_UNIDENTIFIED")
        self.assertEqual(assessment["movement_episode"]["event_relation_to_swing"], "FOLLOWS_SWING")
        self.assertEqual(summary["status"], "NO_SUPPORTING_EVENT_IN_SUPPLIED_EVIDENCE")
        self.assertFalse(assessment["causality_claimed"])
        self.assertFalse(summary["causality_claimed"])

    def test_episode_summary_does_not_claim_absence_of_cause_without_evidence(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-1", "direction": "BEARISH",
                "start": {"pivot_open_time_ms": 1}, "end": {"pivot_open_time_ms": 2},
            }]},
        }
        enriched = enrich_research_report(
            enriched_report, events=[], observations=[], methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        summary = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertEqual(summary["status"], "NOT_ASSESSED_NO_EVENT_EVIDENCE_SUPPLIED")
        self.assertFalse(summary["causality_claimed"])
        self.assertIn("does not prove", summary["interpretation"])

    def test_episode_link_rejects_cutoff_before_observability(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-1", "direction": "BULLISH", "classification": "TECHNICAL_SWING_CANDIDATE",
                "segment_index": 0, "start": {"pivot_open_time_ms": 1792486800000},
                "end": {"pivot_open_time_ms": 1792494000000},
                "episode_observable_only_at_ms": 1792497600000,
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "was not observable at evaluation_as_of"):
                enrich_research_report(
                    enriched_report,
                    events=[{
                        "event": event(), "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_episode_id": "swing-1",
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-20T11:30:00Z",
                )

    def test_event_relation_can_identify_publication_before_swing_without_claiming_cause(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-1", "direction": "BULLISH", "classification": "TECHNICAL_SWING_CANDIDATE",
                "segment_index": 0, "start": {"pivot_open_time_ms": 1792494000000},
                "end": {"pivot_open_time_ms": 1792501200000},
                "episode_observable_only_at_ms": 1792504800000,
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(), "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-1",
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["status"], "OUTSIDE_MOVEMENT_WINDOW")
        self.assertEqual(assessment["movement_episode"]["event_relation_to_swing"], "PRECEDES_SWING")
        self.assertFalse(assessment["causality_claimed"])

    def test_derives_event_window_from_report_movement_episode(self):
        enriched_report = report()
        start_ms = int(__import__("datetime").datetime.fromisoformat("2026-10-20T09:00:00+00:00").timestamp() * 1000)
        end_ms = int(__import__("datetime").datetime.fromisoformat("2026-10-20T11:00:00+00:00").timestamp() * 1000)
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {
                "schema_version": "ohlcv-movement-episodes-v1",
                "episodes": [{
                    "episode_id": "swing-1",
                    "direction": "BULLISH",
                    "classification": "TECHNICAL_SWING_CANDIDATE",
                    "segment_index": 0,
                    "start": {"pivot_open_time_ms": start_ms},
                    "end": {"pivot_open_time_ms": end_ms},
                    "episode_observable_only_at_ms": end_ms + 1,
                }],
            },
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-1",
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(assessment["movement_episode"]["episode_id"], "swing-1")
        self.assertEqual(assessment["movement_episode"]["direction"], "BULLISH")
        self.assertEqual(
            assessment["availability_cutoff"],
            __import__("datetime").datetime.fromtimestamp(
                (end_ms + 1) / 1000, tz=__import__("datetime").timezone.utc
).isoformat().replace("+00:00", "Z"),
        )
        self.assertFalse(assessment["causality_claimed"])

    def test_explicit_window_with_episode_link_classifies_event_against_actual_swing(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-1", "direction": "BULLISH",
                "start": {"pivot_open_time_ms": 1792494000000},
                "end": {"pivot_open_time_ms": 1792501200000},
                "episode_observable_only_at_ms": 1792504800000,
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),  # published at 10:00Z, before the 11:00Z swing start
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-1",
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T14:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(assessment["movement_episode"]["event_relation_to_swing"], "PRECEDES_SWING")
        self.assertFalse(assessment["causality_claimed"])

    def test_explicit_window_does_not_hide_event_after_swing(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {"episodes": [{
                "episode_id": "swing-1", "direction": "BULLISH",
                "start": {"pivot_open_time_ms": 1792483200000},
                "end": {"pivot_open_time_ms": 1792486800000},
                "episode_observable_only_at_ms": 1792488600000,
            }]},
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),  # published at 10:00Z, after the 09:00Z swing end
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-1",
                    "movement_window": {"start": "2026-10-20T08:00:00Z", "end": "2026-10-20T14:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["movement_episode"]["event_relation_to_swing"], "FOLLOWS_SWING")
        self.assertFalse(assessment["causality_claimed"])

    def test_integrates_multi_timeframe_support_resistance_without_promoting_decision(self):
        source = support_resistance_input()
        enriched = enrich_research_report(
            report(), events=[], observations=[], methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-20T04:59:59.999Z",
            support_resistance_input=source,
        )
        technical = enriched["technical_structure_assessment"]
        self.assertEqual(technical["status"], "ASSESSED")
        self.assertEqual(technical["asset_mapping"]["status"], "CALLER_SUPPLIED_REQUIRES_REVIEW")
        self.assertEqual(technical["excluded_after_cutoff_candle_count"], 1)
        self.assertEqual(technical["analysis"]["timeframe_count"], 1)
        self.assertEqual(technical["analysis"]["timeframes"][0]["sample"]["input_candle_count"], 5)
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["orders_submitted"])

    def test_support_resistance_requires_target_asset_mapping(self):
        source = support_resistance_input(stable_id="different-asset")
        with self.assertRaisesRegex(ValueError, "must match the target stable_id and category"):
            enrich_research_report(
                report(), events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-20T04:59:59.999Z",
                support_resistance_input=source,
            )

    def test_report_marks_support_resistance_unavailable_when_not_supplied(self):
        enriched = enrich_research_report(
            report(), events=[], observations=[], methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )
        self.assertEqual(enriched["technical_structure_assessment"]["status"], "NOT_AVAILABLE")
        self.assertEqual(enriched["technical_structure_assessment"]["reason_code"], "NO_SUPPORT_RESISTANCE_INPUT_SUPPLIED")
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")

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


    def test_fundamental_observation_from_terms_pending_provider_is_blocked(self):
        with self.assertRaisesRegex(PermissionError, "fundamental source terms are not approved"):
            enrich_research_report(
                report(), events=[], observations=[fundamental_observation()],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_fundamental_observation_requires_provider_authorization_for_both_uses(self):
        observation = fundamental_observation(terms_status="APPROVED")
        with self.assertRaisesRegex(PermissionError, "blocked for internal_analysis"):
            enrich_research_report(
                report(), events=[], observations=[observation],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )


    def test_observation_cannot_self_authorize_with_embedded_record(self):
        observation = fundamental_observation(
            terms_status="APPROVED",
            authorization_record=approved_defillama_authorization_fixture(),
        )
        with self.assertRaisesRegex(PermissionError, "blocked for internal_analysis"):
            enrich_research_report(
                report(), events=[], observations=[observation],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_authorized_fundamental_observation_records_both_use_assessments(self):
        observation = fundamental_observation(terms_status="APPROVED")
        enriched = enrich_research_report(
            report(), events=[], observations=[observation],
            methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            provider_authorization_registry={
                "defillama_api": approved_defillama_authorization_fixture()
            },
        )
        self.assertEqual(enriched["fundamental_onchain_assessment"]["coverage"]["observed_metric_count"], 1)
        assessments = enriched["fundamental_source_use_assessments"]
        self.assertEqual([item["use_case"] for item in assessments], ["internal_analysis", "persistent_storage"])
        self.assertTrue(all(item["decision"] == "ALLOW" for item in assessments))
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")


    def test_integrated_report_applies_explicit_fundamental_freshness_policy(self):
        observation = fundamental_observation(terms_status="APPROVED")
        enriched = enrich_research_report(
            report(), events=[], observations=[observation],
            methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            provider_authorization_registry={
                "defillama_api": approved_defillama_authorization_fixture()
            },
            fundamental_freshness_policy_seconds={"protocol.tvl": 3600},
        )
        metric = enriched["fundamental_onchain_assessment"]["metrics"]["protocol.tvl"]
        self.assertEqual(metric["status"], "STALE")
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["stale_observation_ids"], ["tvl-example-20261020"])
        self.assertEqual(
            enriched["fundamental_onchain_assessment"]["coverage"]["freshness_policy_seconds"],
            {"protocol.tvl": 3600},
        )
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")

    def test_fundamental_source_cannot_claim_a_different_provider(self):
        observation = fundamental_observation(
            terms_status="APPROVED",
            authorization_record=approved_defillama_authorization_fixture(),
        )
        observation["source"]["provider_id"] = "coingecko_api"
        with self.assertRaisesRegex(PermissionError, "provider id does not match source registry"):
            enrich_research_report(
                report(), events=[], observations=[observation],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_fundamental_source_url_must_match_registered_provider_host(self):
        observation = fundamental_observation(
            terms_status="APPROVED",
            authorization_record=approved_defillama_authorization_fixture(),
        )
        observation["source"]["url"] = "https://attacker.example/protocol/example"
        with self.assertRaisesRegex(PermissionError, "URL is outside registry allowlist"):
            enrich_research_report(
                report(), events=[], observations=[observation],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

    def test_rejects_event_captured_after_historical_cutoff_as_eligible(self):
        ev = event()
        ev["captured_at"] = "2026-10-22T10:01:00Z"
        ev["source_capture_assessments"]["article"]["captured_at"] = "2026-10-22T10:01:00Z"
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
        ev.pop("source_capture_assessments")
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

    def test_tampered_event_capture_body_is_blocked(self):
        ev = event()
        ev["source_capture_assessments"]["article"]["raw_response_base64"] = base64.b64encode(b"tampered article bytes").decode("ascii")
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(PermissionError, "raw response SHA-256 mismatch"):
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


    def test_integrated_report_is_deterministic_for_identical_historical_inputs(self):
        base_report = report()
        original_report = copy.deepcopy(base_report)
        original_methodology = methodology()
        original_support_input = support_resistance_input()

        first = enrich_research_report(
            copy.deepcopy(base_report),
            events=[],
            observations=[],
            methodology=copy.deepcopy(original_methodology),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-20T04:59:59.999Z",
            support_resistance_input=copy.deepcopy(original_support_input),
        )
        second = enrich_research_report(
            copy.deepcopy(base_report),
            events=[],
            observations=[],
            methodology=copy.deepcopy(original_methodology),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-20T04:59:59.999Z",
            support_resistance_input=copy.deepcopy(original_support_input),
        )

        canonical_first = json.dumps(first, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        canonical_second = json.dumps(second, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertEqual(
            hashlib.sha256(canonical_first.encode("utf-8")).hexdigest(),
            hashlib.sha256(canonical_second.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(first, second)
        self.assertEqual(base_report, original_report)
        self.assertEqual(original_methodology, methodology())
        self.assertEqual(original_support_input, support_resistance_input())
        self.assertEqual(first["decision_status"], "INDETERMINATE")
        self.assertFalse(first["orders_submitted"])
        self.assertFalse(first["network_requests_made"])


    def test_missing_evidence_remains_explicitly_unavailable_without_zero_fill(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {
                "schema_version": "ohlcv-movement-episodes-v1",
                "episodes": [{
                    "episode_id": "swing-no-evidence",
                    "direction": "BEARISH",
                    "start": {"pivot_open_time_ms": 1792486800000},
                    "end": {"pivot_open_time_ms": 1792494000000},
                    "episode_observable_only_at_ms": 1792494000001,
                }],
            },
        }
        enriched = enrich_research_report(
            enriched_report,
            events=[],
            observations=[],
            methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
        )

        self.assertEqual(enriched["external_event_evidence"]["status"], "NOT_AVAILABLE")
        self.assertEqual(enriched["external_event_evidence"]["event_count"], 0)
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertEqual(enriched["event_causal_assessment"]["status"], "NOT_ASSESSED")
        self.assertEqual(
            enriched["event_causal_assessment"]["episode_assessments"][0]["status"],
            "NOT_ASSESSED_NO_EVENT_EVIDENCE_SUPPLIED",
        )
        self.assertEqual(
            enriched["fundamental_onchain_assessment"]["coverage"]["observed_metric_count"], 0
        )
        self.assertEqual(enriched["technical_structure_assessment"]["status"], "NOT_AVAILABLE")
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["methodology_assessment"]["predictive_performance_validated"])
        self.assertFalse(enriched["network_requests_made"])
        self.assertFalse(enriched["orders_submitted"])

    def test_composes_market_movement_levels_events_and_fundamentals_in_one_report(self):
        enriched_report = report()
        enriched_report["descriptive_analyses"] = {
            "movement_episodes": {
                "schema_version": "ohlcv-movement-episodes-v1",
                "episodes": [{
                    "episode_id": "swing-composite-1",
                    "direction": "BULLISH",
                    "start": {"pivot_open_time_ms": 1792486800000},
                    "end": {"pivot_open_time_ms": 1792494000000},
                    "episode_observable_only_at_ms": 1792494000001,
                }],
            },
            "order_book": {
                "status": "DESCRIPTIVE_SNAPSHOT",
                "captured_at_utc": "2026-10-20T10:00:00Z",
                "limitations": ["Visible depth is not the full market and does not guarantee execution."],
            },
        }
        observation = fundamental_observation(terms_status="APPROVED")
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                enriched_report,
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "swing-composite-1",
                }],
                observations=[observation],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
                support_resistance_input=support_resistance_input(),
                provider_authorization_registry={
                    "defillama_api": approved_defillama_authorization_fixture()
                },
            )

        self.assertEqual(enriched["technical_structure_assessment"]["status"], "ASSESSED")
        self.assertEqual(enriched["external_event_evidence"]["event_count"], 1)
        self.assertEqual(enriched["external_event_evidence"]["assessments"][0]["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertEqual(enriched["fundamental_onchain_assessment"]["coverage"]["observed_metric_count"], 1)
        self.assertEqual(len(enriched["fundamental_source_use_assessments"]), 2)
        self.assertTrue(all(item["decision"] == "ALLOW" for item in enriched["fundamental_source_use_assessments"]))
        self.assertEqual(enriched["descriptive_analyses"]["order_book"]["status"], "DESCRIPTIVE_SNAPSHOT")
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["methodology_assessment"]["predictive_performance_validated"])
        self.assertFalse(enriched["orders_submitted"])
        self.assertFalse(enriched["network_requests_made"])

    def test_explicit_pre_movement_window_is_applied_and_reported(self):
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T10:30:00Z", "end": "2026-10-20T11:00:00Z"},
                    "pre_movement_window_minutes": 30,
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["status"], "TEMPORALLY_ELIGIBLE")
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(assessment["pre_movement_window_minutes"], 30)
        self.assertEqual(assessment["association_window"]["start"], "2026-10-20T10:00:00Z")
        self.assertFalse(assessment["causality_claimed"])

    def test_invalid_pre_movement_window_is_rejected(self):
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "pre_movement_window_minutes must be a non-negative integer"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event(),
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T10:30:00Z", "end": "2026-10-20T11:00:00Z"},
                        "pre_movement_window_minutes": True,
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )



    def test_source_coverage_distinguishes_blocked_from_no_items(self):
        blocked = {
            "source_id": "cftc_general_press_releases",
            "capture_status": "BLOCKED",
            "captured_at": "2026-10-20T10:05:00Z",
            "network_request_made": False,
            "capture_truncated": False,
            "feed_item_count": 0,
            "coverage_scope": "Current feed only",
            "errors": [],
        }
        enriched = enrich_research_report(
            report(), events=[], observations=[], methodology=methodology(),
            asset={"stable_id": "example-asset", "category": "smart_contract_token"},
            evaluation_as_of="2026-10-21T00:00:00Z",
            event_source_coverage=[blocked],
        )
        coverage = enriched["external_event_evidence"]["source_coverage"]
        self.assertEqual(coverage["sources"][0]["coverage_status"], "BLOCKED_BY_SOURCE_POLICY")
        self.assertIn("does not establish absence", coverage["sources"][0]["interpretation"])

        approved = approved_event_source()
        empty_capture = {
            "source_id": "sec_press_releases",
            "capture_status": "PASS",
            "captured_at": "2026-10-20T10:05:00Z",
            "network_request_made": True,
            "capture_truncated": False,
            "feed_item_count": 0,
            "coverage_scope": "Current feed only; not a historical archive",
            "errors": [],
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved}):
            enriched = enrich_research_report(
                report(), events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
                event_source_coverage=[empty_capture],
            )
        coverage = enriched["external_event_evidence"]["source_coverage"]
        self.assertEqual(coverage["sources"][0]["coverage_status"], "CAPTURED_NO_ITEMS_IN_RETURNED_FEED")
        self.assertIn("does not establish absence", coverage["sources"][0]["interpretation"])

    def test_source_coverage_captured_after_cutoff_is_not_available_as_of(self):
        approved = approved_event_source()
        capture = {
            "source_id": "sec_press_releases",
            "capture_status": "PASS",
            "captured_at": "2026-10-22T10:05:00Z",
            "network_request_made": True,
            "capture_truncated": False,
            "feed_item_count": 2,
            "coverage_scope": "Current feed only",
            "errors": [],
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved}):
            enriched = enrich_research_report(
                report(), events=[], observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
                event_source_coverage=[capture],
            )
        self.assertEqual(
            enriched["external_event_evidence"]["source_coverage"]["sources"][0]["coverage_status"],
            "NOT_AVAILABLE_AS_OF",
        )



    def test_explicit_post_movement_window_is_applied_and_reported(self):
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event(),
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T09:59:00Z"},
                    "post_movement_window_minutes": 1,
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["status"], "TEMPORALLY_ELIGIBLE")
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(assessment["post_movement_window_minutes"], 1)
        self.assertEqual(assessment["association_window"]["end"], "2026-10-20T10:00:00Z")
        self.assertIn("follows movement end", assessment["reason"].lower())
        self.assertFalse(assessment["causality_claimed"])

    def test_invalid_post_movement_window_is_rejected_in_report_integration(self):
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "post_movement_window_minutes must be a non-negative integer"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event(),
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T09:59:00Z"},
                        "post_movement_window_minutes": True,
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )



    def test_fact_verification_is_not_inferred_from_article_or_temporal_proximity(self):
        event_record = event()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertEqual(assessment["fact_verification"]["effective_decision"], "NOT_REVIEWED")
        self.assertFalse(assessment["fact_verification"]["available_as_of"])

    def test_valid_primary_source_fact_review_is_reported_separately_from_causality(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(event_record)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["fact_verification"]["effective_decision"], "VERIFIED_PRIMARY_SOURCE")
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertFalse(assessment["causality_claimed"])

    def test_fact_review_after_evaluation_cutoff_is_not_used_as_historical_knowledge(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(
            event_record, reviewed_at="2026-10-22T10:04:00Z",
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        fact = enriched["external_event_evidence"]["assessments"][0]["fact_verification"]
        self.assertEqual(fact["decision"], "VERIFIED_PRIMARY_SOURCE")
        self.assertEqual(fact["effective_decision"], "NOT_AVAILABLE_AS_OF")
        self.assertFalse(fact["available_as_of"])

    def test_fact_review_rejects_tampered_evidence_hash(self):
        event_record = event()
        review = fact_review_for(event_record)
        review["evidence_record_sha256"] = "0" * 64
        event_record["metadata"]["fact_review"] = review
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(PermissionError, "SHA-256 mismatch"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event_record,
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )

    def test_conflicting_fact_review_requires_two_distinct_sources(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(
            event_record,
            decision="CONFLICTING_SOURCES",
            evidence_refs=[{
                "url": event_record["source"]["url"],
                "role": "PRIMARY_SOURCE",
                "publisher": "SEC",
            }],
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "at least two distinct URLs"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event_record,
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )



    def test_supported_causality_requires_verified_fact_market_data_and_alternatives(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(event_record)
        event_record["metadata"]["causal_review"] = causal_review_for(event_record)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["causal_review"]["effective_decision"], "SUPPORTED_CAUSALITY")
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertFalse(assessment["causality_claimed"])

    def test_supported_causality_is_rejected_without_fact_verification(self):
        event_record = event()
        event_record["metadata"]["causal_review"] = causal_review_for(event_record)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "supported causality requires fact verification"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event_record,
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )

    def test_causal_review_after_cutoff_is_not_used_as_historical_conclusion(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(event_record)
        event_record["metadata"]["causal_review"] = causal_review_for(
            event_record, reviewed_at="2026-10-22T10:05:00Z",
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        causal = enriched["external_event_evidence"]["assessments"][0]["causal_review"]
        self.assertEqual(causal["decision"], "SUPPORTED_CAUSALITY")
        self.assertEqual(causal["effective_decision"], "NOT_AVAILABLE_AS_OF")
        self.assertFalse(causal["available_as_of"])

    def test_plausible_hypothesis_requires_market_evidence_and_alternatives(self):
        event_record = event()
        event_record["metadata"]["causal_review"] = causal_review_for(
            event_record,
            decision="PLAUSIBLE_HYPOTHESIS",
            evidence_refs=[{"url": event_record["source"]["url"], "role": "PRIMARY_SOURCE", "publisher": "SEC"}],
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            with self.assertRaisesRegex(ValueError, "requires market-reaction evidence"):
                enrich_research_report(
                    report(),
                    events=[{
                        "event": event_record,
                        "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                        "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                    }],
                    observations=[], methodology=methodology(),
                    asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                    evaluation_as_of="2026-10-21T00:00:00Z",
                )



    def test_episode_aggregate_reports_supported_causality_only_with_reviewed_evidence(self):
        event_record = event()
        event_record["metadata"]["fact_review"] = fact_review_for(event_record)
        event_record["metadata"]["causal_review"] = causal_review_for(event_record)
        research_report = report()
        research_report["descriptive_analyses"] = {
            "movement_episodes": {
                "episodes": [{
                    "episode_id": "episode-1",
                    "direction": "BULLISH",
                    "classification": "OBSERVED",
                    "segment_index": 0,
                    "start": {"pivot_open_time_ms": 1792486800000},
                    "end": {"pivot_open_time_ms": 1792494000000},
                    "episode_observable_only_at_ms": 1792495800000,
                }]
            }
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"sec_press_releases": approved_event_source()}):
            enriched = enrich_research_report(
                research_report,
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "episode-1",
                }],
                observations=[], methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )
        self.assertEqual(
            enriched["event_causal_assessment"]["episode_assessments"][0]["status"],
            "SUPPORTED_CAUSALITY_REVIEWED",
        )
        self.assertEqual(
            enriched["external_event_evidence"]["assessments"][0]["causal_review"]["effective_decision"],
            "SUPPORTED_CAUSALITY",
        )



if __name__ == "__main__":
    unittest.main()
