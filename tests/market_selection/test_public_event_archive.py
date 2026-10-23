import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    ARCHIVE_CAPTURE_SCHEMA,
    capture_public_event_archive_article,
    capture_public_event_archive_index,
    promote_public_archive_candidate_to_event,
    select_public_event_archive_candidate,
)
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.research_evidence_integration import enrich_research_report
from test_public_event_feed import FakeResponse, USER_AGENT, approved_source, authorization_record
from test_research_evidence_integration import methodology, report


ARCHIVE_URL = "https://www.cftc.gov/PressRoom/PressReleases?page=0"
ARTICLE_URL = "https://www.cftc.gov/PressRoom/PressReleases/2026/press-1"
ARCHIVE_HTML = (
    b"<html><body><div class='release'><time>10/20/2026</time>"
    b"<a href='/PressRoom/PressReleases/2026/press-1'>"
    b"CFTC Announces Crypto-Related Enforcement Action</a></div></body></html>"
)
ARTICLE_HTML = b"<html><head><title>CFTC Announces Crypto-Related Enforcement Action</title></head><body>Official archive article body.</body></html>"


def capture_archive(entry):
    with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}), patch(
        "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
        return_value=FakeResponse(
            ARCHIVE_HTML,
            headers={"Content-Type": "text/html; charset=utf-8"},
            final_url=ARCHIVE_URL,
        ),
    ):
        return capture_public_event_archive_index(
            "cftc_press_release_archive",
            ARCHIVE_URL,
            authorization_record(entry),
            USER_AGENT,
            captured_at="2026-10-22T12:30:00Z",
        )


def candidate_from(archive_capture):
    entry = approved_source("cftc_press_release_archive")
    with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
        return select_public_event_archive_candidate(
            archive_capture,
            candidate_url=ARTICLE_URL,
            title="CFTC Announces Crypto-Related Enforcement Action",
            published_at="2026-10-20T10:00:00Z",
            publication_time_evidence="10/20/2026",
            selected_by="offline-archive-reviewer",
            selected_at="2026-10-22T12:31:00Z",
            selection_rationale="Synthetic test fixture: URL, title and date are present in the preserved archive page.",
        )


class PublicEventArchiveTests(unittest.TestCase):
    def test_archive_capture_blocks_terms_pending_source_before_network(self):
        with patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as network:
            result = capture_public_event_archive_index(
                "cftc_press_release_archive",
                ARCHIVE_URL,
                authorization_record=None,
                user_agent=USER_AGENT,
                captured_at="2026-10-22T12:30:00Z",
            )
        network.assert_not_called()
        self.assertEqual(result["schema_version"], ARCHIVE_CAPTURE_SCHEMA)
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])

    def test_archive_article_capture_blocks_before_candidate_validation_when_terms_pending(self):
        blocked_archive = capture_public_event_archive_index(
            "cftc_press_release_archive",
            ARCHIVE_URL,
            authorization_record=None,
            user_agent=USER_AGENT,
            captured_at="2026-10-22T12:30:00Z",
        )
        with patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as network:
            result = capture_public_event_archive_article(
                blocked_archive,
                {},
                authorization_record=None,
                user_agent=USER_AGENT,
                captured_at="2026-10-22T12:32:00Z",
            )
        network.assert_not_called()
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])

    def test_archive_path_prefix_does_not_allow_similar_unregistered_path(self):
        entry = approved_source("cftc_press_release_archive")
        bad_url = "https://www.cftc.gov/PressRoom/PressReleasesEvil?page=0"
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}), patch(
            "scripts.market_selection.capture_public_event_feed._open_allowlisted_url"
        ) as network:
            result = capture_public_event_archive_index(
                "cftc_press_release_archive",
                bad_url,
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at="2026-10-22T12:30:00Z",
            )
        network.assert_not_called()
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("ARCHIVE_URL_OUTSIDE_ALLOWLIST", result["reason_codes"])

    def test_archive_candidate_requires_url_title_and_date_evidence(self):
        entry = approved_source("cftc_press_release_archive")
        archive_capture = capture_archive(entry)
        candidate = candidate_from(archive_capture)
        self.assertEqual(candidate["candidate_url"], ARTICLE_URL)
        self.assertEqual(candidate["published_at"], "2026-10-20T10:00:00Z")
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            with self.assertRaisesRegex(PermissionError, "URL/title"):
                select_public_event_archive_candidate(
                    archive_capture,
                    candidate_url=ARTICLE_URL,
                    title="An unrelated announcement",
                    published_at="2026-10-20T10:00:00Z",
                    publication_time_evidence="10/20/2026",
                    selected_by="offline-archive-reviewer",
                    selected_at="2026-10-22T12:31:00Z",
                    selection_rationale="Negative test.",
                )

    def test_archive_article_promotion_and_report_integration(self):
        entry = approved_source("cftc_press_release_archive")
        archive_capture = capture_archive(entry)
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
        self.assertEqual(article_capture["capture_status"], "PASS")
        mapping_bytes = b'{"asset":"example-asset","review":"synthetic archive mapping"}'
        resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-archive-reviewer",
            "reviewed_at": "2026-10-22T12:31:30Z",
            "evidence_record_base64": base64.b64encode(mapping_bytes).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(mapping_bytes).hexdigest(),
            "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            event_record = promote_public_archive_candidate_to_event(
                archive_capture,
                candidate,
                article_capture,
                "REGULATORY_ENFORCEMENT",
                "The preserved archive article reports a regulatory action.",
                resolution,
            )
            enriched = enrich_research_report(
                report(),
                events=[{
                    "event": event_record,
                    "target_entity": {"id_type": "coingecko_id", "id": "example-asset"},
                    "movement_window": {"start": "2026-10-20T09:00:00Z", "end": "2026-10-20T11:00:00Z"},
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-23T00:00:00Z",
            )
        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["status"], "TEMPORALLY_ELIGIBLE")
        self.assertEqual(assessment["fact_verification"]["effective_decision"], "NOT_REVIEWED")
        self.assertEqual(assessment["causal_review"]["effective_decision"], "NOT_ASSESSED")
        self.assertEqual(event_record["capture_method"], "public_event_archive_html_v1")
        self.assertEqual(event_record["metadata"]["archive_raw_response_sha256"], archive_capture["raw_response_sha256"])


if __name__ == "__main__":
    unittest.main()
