import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    build_public_event_archive_coverage_manifest,
    capture_public_event_archive_article,
    promote_public_archive_candidate_to_event,
)
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.research_evidence_integration import enrich_research_report
from test_public_event_archive import ARTICLE_HTML, ARTICLE_URL, ARCHIVE_URL, candidate_from, capture_archive
from test_public_event_feed import FakeResponse, USER_AGENT, approved_source, authorization_record
from test_research_evidence_integration import causal_review_for, fact_review_for, methodology, report


class Issue132ArchiveEndToEndTests(unittest.TestCase):
    def test_synthetic_archive_to_reviewed_episode_and_declared_coverage(self):
        # Offline-only synthetic fixtures: no real-world authorization or causal proof.
        entry = approved_source("cftc_press_release_archive")
        archive_capture = capture_archive(entry, ARCHIVE_URL)
        candidate = candidate_from(archive_capture)

        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}), patch(
            "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
            return_value=FakeResponse(
                ARTICLE_HTML,
                headers={"Content-Type": "text/html; charset=utf-8"},
                final_url=ARTICLE_URL,
            ),
        ):
            article_capture = capture_public_event_archive_article(
                archive_capture,
                candidate,
                authorization_record(entry),
                USER_AGENT,
                captured_at="2026-10-22T12:32:00Z",
            )

        mapping_evidence = {
            "status": "APPROVED",
            "reviewed_by": "offline-e2e-reviewer",
            "reviewed_at": "2026-10-22T12:33:00Z",
            "evidence_record_base64": "eyJhc3NldCI6ImV4YW1wbGUtYXNzZXQifQ==",
            "evidence_record_sha256": "f0e6c5e4f6f6d6f4f8f2f2e6e4f6d6f4f8f2f2e6e4f6d6f4f8f2f2e6e4f6d6f4",
            "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
        }
        # Build valid, hashed mapping evidence from the encoded bytes to avoid a hand-entered digest.
        import base64
        import hashlib
        mapping_raw = base64.b64decode(mapping_evidence["evidence_record_base64"])
        mapping_evidence["evidence_record_sha256"] = hashlib.sha256(mapping_raw).hexdigest()

        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            event_record = promote_public_archive_candidate_to_event(
                archive_capture,
                candidate,
                article_capture,
                "REGULATORY_ENFORCEMENT",
                "Synthetic archive fixture describes a regulatory action.",
                mapping_evidence,
            )

        event_record["metadata"]["fact_review"] = fact_review_for(
            event_record, reviewed_at="2026-10-22T12:34:00Z"
        )
        event_record["metadata"]["causal_review"] = causal_review_for(
            event_record, reviewed_at="2026-10-22T12:35:00Z"
        )

        expected_partitions = [{
            "partition_id": "2026",
            "page_count": 1,
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
        }]
        segment = {
            "archive_capture": archive_capture,
            "partition_id": "2026",
            "page_index": 1,
            "expected_page_count": 1,
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            coverage = build_public_event_archive_coverage_manifest(
                "cftc_press_release_archive",
                "synthetic-cftc-2026",
                "Synthetic one-page archive fixture; not a real historical backfill",
                expected_partitions,
                [segment],
                "offline-e2e-reviewer",
                "2026-10-22T12:36:00Z",
            )
            research_report = report()
            research_report["descriptive_analyses"] = {
                "movement_episodes": {
                    "schema_version": "ohlcv-movement-episodes-v1",
                    "episodes": [{
                        "episode_id": "episode-e2e",
                        "direction": "BEARISH",
                        "classification": "OBSERVED",
                        "segment_index": 0,
                        "start": {"pivot_open_time_ms": 1792666800000},
                        "end": {"pivot_open_time_ms": 1792674000000},
                        "episode_observable_only_at_ms": 1792674060000,
                    }],
                },
            }
            enriched = enrich_research_report(
                research_report,
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_episode_id": "episode-e2e",
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-23T00:00:00Z",
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        episode = enriched["event_causal_assessment"]["episode_assessments"][0]
        self.assertEqual(archive_capture["capture_status"], "PASS")
        self.assertEqual(article_capture["capture_status"], "PASS")
        self.assertEqual(assessment["fact_verification"]["effective_decision"], "VERIFIED_PRIMARY_SOURCE")
        self.assertEqual(assessment["causal_review"]["effective_decision"], "SUPPORTED_CAUSALITY")
        self.assertEqual(assessment["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertFalse(assessment["causality_claimed"])
        self.assertEqual(episode["status"], "SUPPORTED_CAUSALITY_REVIEWED")
        self.assertFalse(episode["causality_claimed"])
        self.assertEqual(coverage["coverage_status"], "COMPLETE_FOR_DECLARED_SCOPE")
        self.assertFalse(coverage["global_archive_exhaustiveness_claimed"])
        self.assertEqual(coverage["captured_segments"][0]["page_index"], 1)


if __name__ == "__main__":
    unittest.main()
