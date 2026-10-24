import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    ARCHIVE_CAPTURE_SCHEMA,
    build_public_event_archive_coverage_manifest,
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
    b"<html><body><div class='release'><time>10/22/2026</time>"
    b"<a href='/PressRoom/PressReleases/2026/press-1'>"
    b"CFTC Announces Crypto-Related Enforcement Action</a></div></body></html>"
)
ARTICLE_HTML = b"<html><head><title>CFTC Announces Crypto-Related Enforcement Action</title></head><body>Official archive article body.</body></html>"


def capture_archive(entry, archive_url=ARCHIVE_URL):
    with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}), patch(
        "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
        return_value=FakeResponse(
            ARCHIVE_HTML,
            headers={"Content-Type": "text/html; charset=utf-8"},
            final_url=archive_url,
        ),
    ):
        return capture_public_event_archive_index(
            "cftc_press_release_archive",
            archive_url,
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
            published_at="2026-10-22T12:00:00Z",
            publication_time_evidence="10/22/2026",
            selected_by="offline-archive-reviewer",
            selected_at="2026-10-22T12:31:00Z",
            selection_rationale="Synthetic test fixture: URL, title and date are present in the preserved archive page.",
        )


class PublicEventArchiveTests(unittest.TestCase):
    def test_archive_text_evidence_excludes_embedded_scripts_and_media(self):
        from scripts.market_selection.capture_public_event_feed import _ArchiveHTMLParser

        parser = _ArchiveHTMLParser()
        parser.feed(
            '<html><body><script><a href="https://third-party.example/leak">Injected</a>'
            'SECRET_SCRIPT_TEXT</script><style>SECRET_STYLE_TEXT</style>'
            '<iframe>SECRET_FRAME_TEXT</iframe><svg><text>SECRET_SVG_TEXT</text></svg>'
            '<img src="https://third-party.example/image.png" alt="Third party image">'
            '<a href="/newsevents/pressreleases/bcreg20260924a.htm">'
            'Federal Reserve Board requests public comment</a>'
            '<p>Published September 24, 2026</p></body></html>'
        )
        parser.close()
        extracted = " ".join(parser.page_text)
        self.assertNotIn("SECRET_SCRIPT_TEXT", extracted)
        self.assertNotIn("SECRET_STYLE_TEXT", extracted)
        self.assertNotIn("SECRET_FRAME_TEXT", extracted)
        self.assertNotIn("SECRET_SVG_TEXT", extracted)
        self.assertNotIn("Third party image", extracted)
        self.assertEqual(len(parser.anchors), 1)
        self.assertEqual(
            parser.anchors[0]["href"],
            "/newsevents/pressreleases/bcreg20260924a.htm",
        )
        self.assertIn("Federal Reserve Board requests public comment", extracted)

    def test_federal_reserve_archive_persists_only_extracted_text_and_hashes_full_response(self):
        source_id = "federal_reserve_press_release_archive"
        archive_url = "https://www.federalreserve.gov/newsevents/pressreleases.htm"
        article_url = "https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260924a.htm"
        original = (
            b'<html><body><script>THIRD_PARTY_SCRIPT_SECRET</script>'
            b'<a href="/newsevents/pressreleases/bcreg20260924a.htm">'
            b'Federal Reserve Board requests public comment on two proposals</a>'
            b'<p>September 24, 2026</p></body></html>'
        )
        entry = approved_source(source_id)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}), patch(
            "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
            return_value=FakeResponse(
                original,
                headers={"Content-Type": "text/html; charset=utf-8"},
                final_url=archive_url,
            ),
        ):
            capture = capture_public_event_archive_index(
                source_id,
                archive_url,
                authorization_record(entry),
                USER_AGENT,
                captured_at="2026-10-24T02:00:00Z",
            )
        self.assertEqual(capture["capture_status"], "PASS")
        self.assertEqual(capture["stored_content_mode"], "EXTRACTED_TEXT_EVIDENCE")
        self.assertIsNone(capture["raw_response_base64"])
        self.assertEqual(capture["raw_response_bytes"], len(original))
        self.assertEqual(capture["raw_response_sha256"], hashlib.sha256(original).hexdigest())
        encoded_evidence = base64.b64decode(capture["text_evidence_base64"])
        self.assertEqual(
            capture["text_evidence_sha256"],
            hashlib.sha256(encoded_evidence).hexdigest(),
        )
        evidence = encoded_evidence.decode("utf-8")
        self.assertNotIn("THIRD_PARTY_SCRIPT_SECRET", evidence)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}):
            candidate = select_public_event_archive_candidate(
                capture,
                candidate_url=article_url,
                title="Federal Reserve Board requests public comment on two proposals",
                published_at="2026-09-24T16:00:00Z",
                publication_time_evidence="September 24, 2026",
                selected_by="offline-regression-reviewer",
                selected_at="2026-10-24T02:01:00Z",
                selection_rationale="Synthetic fixture verifies text-only archive evidence handling.",
            )
        self.assertEqual(candidate["archive_capture_sha256"], capture["raw_response_sha256"])
        article_raw = (
            b'<html><body><script>THIRD_PARTY_ARTICLE_SCRIPT</script>'
            b'<article><h1>Federal Reserve Board requests public comment</h1>'
            b'<p>Official text about payment stablecoin proposals.</p></article></body></html>'
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}), patch(
            "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
            return_value=FakeResponse(
                article_raw,
                headers={"Content-Type": "text/html; charset=utf-8"},
                final_url=article_url,
            ),
        ):
            article_capture = capture_public_event_archive_article(
                capture,
                candidate,
                authorization_record(entry),
                USER_AGENT,
                captured_at="2026-10-24T02:02:00Z",
            )
        self.assertEqual(article_capture["capture_status"], "PASS")
        self.assertEqual(article_capture["stored_content_mode"], "EXTRACTED_TEXT_EVIDENCE")
        self.assertIsNone(article_capture["raw_response_base64"])
        article_evidence = base64.b64decode(article_capture["text_evidence_base64"]).decode("utf-8")
        self.assertNotIn("THIRD_PARTY_ARTICLE_SCRIPT", article_evidence)

        mapping_bytes = b'{"asset":"stablecoin-regulatory-framework","review":"synthetic text-only test"}'
        resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-regression-reviewer",
            "reviewed_at": "2026-10-24T02:03:00Z",
            "evidence_record_base64": base64.b64encode(mapping_bytes).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(mapping_bytes).hexdigest(),
            "entities": [{"id_type": "project_id", "id": "stablecoin-regulatory-framework"}],
        }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}):
            event_record = promote_public_archive_candidate_to_event(
                capture,
                candidate,
                article_capture,
                "REGULATORY_POLICY_PROPOSAL",
                "The official release describes proposed rules; market causality has not been assessed.",
                resolution,
            )
            manifest = build_public_event_archive_coverage_manifest(
                source_id,
                "federal-reserve-2026",
                "Single synthetic archive page for the 2026-09-24 historical candidate test.",
                [{
                    "partition_id": "2026",
                    "page_count": 1,
                    "period_start": "2026-01-01",
                    "period_end": "2026-12-31",
                }],
                [{
                    "archive_capture": capture,
                    "partition_id": "2026",
                    "page_index": 1,
                    "expected_page_count": 1,
                }],
                "offline-regression-reviewer",
                "2026-10-24T02:04:00Z",
            )
        self.assertEqual(event_record["metadata"]["causality_status"], "NOT_ASSESSED")
        self.assertEqual(manifest["coverage_status"], "COMPLETE_FOR_DECLARED_SCOPE")
        self.assertEqual(
            manifest["segments"][0]["stored_content_mode"],
            "EXTRACTED_TEXT_EVIDENCE",
        )

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

    def test_coverage_manifest_distinguishes_complete_declared_scope_from_missing_page(self):
        entry = approved_source("cftc_press_release_archive")
        first = capture_archive(entry, "https://www.cftc.gov/PressRoom/PressReleases?page=0")
        second = capture_archive(entry, "https://www.cftc.gov/PressRoom/PressReleases?page=1")
        expected_partitions = [{
            "partition_id": "2026",
            "page_count": 2,
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
        }]
        def segment(capture, page_index):
            return {
                "archive_capture": capture,
                "partition_id": "2026",
                "page_index": page_index,
                "expected_page_count": 2,
            }
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            complete = build_public_event_archive_coverage_manifest(
                "cftc_press_release_archive", "cftc-2026", "CFTC releases dated in 2026, pages 0–1",
                expected_partitions, [segment(first, 1), segment(second, 2)],
                "offline-archive-reviewer", "2026-10-22T12:40:00Z",
            )
            partial = build_public_event_archive_coverage_manifest(
                "cftc_press_release_archive", "cftc-2026", "CFTC releases dated in 2026, pages 0–1",
                expected_partitions, [segment(first, 1)],
                "offline-archive-reviewer", "2026-10-22T12:40:00Z",
            )
        self.assertEqual(complete["coverage_status"], "COMPLETE_FOR_DECLARED_SCOPE")
        self.assertFalse(complete["global_archive_exhaustiveness_claimed"])
        self.assertEqual(partial["coverage_status"], "PARTIAL")
        self.assertEqual(partial["missing_pages"], [{"partition_id": "2026", "page_index": 2}])

    def test_archive_candidate_requires_url_title_and_date_evidence(self):
        entry = approved_source("cftc_press_release_archive")
        archive_capture = capture_archive(entry)
        candidate = candidate_from(archive_capture)
        self.assertEqual(candidate["candidate_url"], ARTICLE_URL)
        self.assertEqual(candidate["published_at"], "2026-10-22T12:00:00Z")
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_press_release_archive": entry}):
            with self.assertRaisesRegex(PermissionError, "URL/title"):
                select_public_event_archive_candidate(
                    archive_capture,
                    candidate_url=ARTICLE_URL,
                    title="An unrelated announcement",
                    published_at="2026-10-22T12:00:00Z",
                    publication_time_evidence="10/22/2026",
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
                    "movement_window": {"start": "2026-10-22T11:00:00Z", "end": "2026-10-22T13:00:00Z"},
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


    def test_every_pending_archive_source_is_blocked_before_network(self):
        # Archive IDs are separate authorization scopes from their related feeds.
        for source_id, entry in EVENT_SOURCE_REGISTRY["sources"].items():
            if "archive" not in source_id or entry["status"] != "TERMS_PENDING":
                continue
            with self.subTest(source_id=source_id):
                with patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as network:
                    result = capture_public_event_archive_index(
                        source_id,
                        entry["source_url"] + ("?page=0" if "?" not in entry["source_url"] else ""),
                        authorization_record=None,
                        user_agent=USER_AGENT,
                        captured_at="2026-10-22T12:30:00Z",
                    )
                network.assert_not_called()
                self.assertEqual(result["capture_status"], "BLOCKED")
                self.assertFalse(result["network_request_made"])


if __name__ == "__main__":
    unittest.main()
