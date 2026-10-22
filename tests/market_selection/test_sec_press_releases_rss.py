import base64
import copy
import hashlib
import io
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from scripts.market_selection.capture_sec_press_releases_rss import (
    ARTICLE_CAPTURE_SCHEMA,
    FEED_CAPTURE_SCHEMA,
    capture_sec_press_release_article,
    capture_sec_press_releases_rss,
    promote_sec_press_release_to_event,
)
from scripts.market_selection.event_source_registry import (
    EVENT_SOURCE_REGISTRY,
    validate_source_entry,
)
from scripts.market_selection.provider_license_gate import SCHEMA_VERSION as AUTH_SCHEMA_VERSION


TERMS_BYTES = b"Synthetic SEC developer terms fixture"


def approved_entry():
    entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"]["sec_press_releases"])
    entry.update({
        "status": "APPROVED",
        "terms_sha256": hashlib.sha256(TERMS_BYTES).hexdigest(),
        "terms_content_base64": base64.b64encode(TERMS_BYTES).decode("ascii"),
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T11:00:00Z",
        "allowed_use_cases": ["internal_analysis", "persistent_storage"],
    })
    return entry


def authorization_record(entry):
    return {
        "schema_version": AUTH_SCHEMA_VERSION,
        "provider_id": "sec_press_releases",
        "status": "APPROVED",
        "authorized_use_cases": ["internal_analysis", "persistent_storage"],
        "terms_url": entry["terms_url"],
        "terms_sha256": entry["terms_sha256"],
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T11:00:00Z",
    }


class FakeResponse:
    def __init__(self, raw, status=200, headers=None, error_after_bytes=None):
        self.raw = raw
        self.status = status
        self.headers = headers or {"Content-Type": "application/rss+xml", "ETag": '"fixture-etag"'}
        self.closed = False
        self.offset = 0
        self.error_after_bytes = error_after_bytes

    def read(self, size=-1):
        if self.error_after_bytes is not None and self.offset >= self.error_after_bytes:
            raise OSError("synthetic mid-stream read error")
        if self.offset >= len(self.raw):
            return b""
        limit = len(self.raw) if size is None or size < 0 else self.offset + size
        if self.error_after_bytes is not None:
            limit = min(limit, self.error_after_bytes)
        end = min(limit, len(self.raw))
        chunk = self.raw[self.offset:end]
        self.offset = end
        return chunk

    def close(self):
        self.closed = True


def rss_bytes(pub_date="Thu, 22 Oct 2026 12:00:00 GMT"):
    pub_date_xml = f"<pubDate>{pub_date}</pubDate>" if pub_date is not None else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel><title>SEC Press Releases</title>'
        '<item><title>Example enforcement announcement</title>'
        '<link>https://www.sec.gov/news/press-release/example</link>'
        '<guid>https://www.sec.gov/news/press-release/example</guid>'
        + pub_date_xml
        + '<description>Fixture summary, not a real event.</description></item>'
        '</channel></rss>'
    ).encode("utf-8")


class SecPressReleaseConnectorTests(unittest.TestCase):
    def setUp(self):
        self.captured_at = "2026-10-22T12:30:00Z"
        self.user_agent = "CryptoIntelligenceTest/1.0 (contact: offline-test-fixture)"

    def approved_registry(self):
        return patch.dict(
            EVENT_SOURCE_REGISTRY["sources"],
            {"sec_press_releases": approved_entry()},
        )

    def test_default_source_registry_blocks_before_network(self):
        opener = Mock()
        result = capture_sec_press_releases_rss(
            None, self.user_agent, 5, captured_at=self.captured_at, opener=opener,
        )
        self.assertEqual(result["schema_version"], FEED_CAPTURE_SCHEMA)
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])
        self.assertIn("SOURCE_TERMS_PENDING", result["reason_codes"])
        opener.assert_not_called()

    def test_missing_authorization_blocks_before_network_even_if_source_reviewed(self):
        with self.approved_registry() as registry:
            opener = Mock()
            result = capture_sec_press_releases_rss(
                None, self.user_agent, 5, captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])
        self.assertIn("AUTHORIZATION_RECORD_MISSING", result["reason_codes"])
        opener.assert_not_called()

    def test_missing_persistent_storage_scope_blocks_before_network(self):
        with self.approved_registry() as registry:
            entry = registry["sec_press_releases"]
            record = authorization_record(entry)
            record["authorized_use_cases"] = ["internal_analysis"]
            opener = Mock()
            result = capture_sec_press_releases_rss(
                record, self.user_agent, 5, captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("USE_CASE_NOT_EXPLICITLY_AUTHORIZED", result["reason_codes"])
        opener.assert_not_called()

    def test_terms_hash_mismatch_blocks_before_network(self):
        with self.approved_registry() as registry:
            entry = registry["sec_press_releases"]
            record = authorization_record(entry)
            record["terms_sha256"] = "f" * 64
            opener = Mock()
            result = capture_sec_press_releases_rss(
                record, self.user_agent, 5, captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("AUTHORIZATION_TERMS_HASH_MISMATCH", result["reason_codes"])
        opener.assert_not_called()

    def test_invalid_timeout_blocks_before_network(self):
        with self.approved_registry() as registry:
            opener = Mock()
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 0,
                captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("INVALID_TIMEOUT_SECONDS", result["reason_codes"])
        opener.assert_not_called()

    def test_user_agent_is_required_before_network(self):
        with self.approved_registry() as registry:
            opener = Mock()
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), None, 5,
                captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("USER_AGENT_REQUIRED", result["reason_codes"])
        opener.assert_not_called()

    def test_successful_feed_capture_preserves_full_body_headers_and_timestamps(self):
        raw = rss_bytes()
        with self.approved_registry() as registry:
            entry = registry["sec_press_releases"]
            opener = Mock(return_value=FakeResponse(raw))
            result = capture_sec_press_releases_rss(
                authorization_record(entry), self.user_agent, 5,
                captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["schema_version"], FEED_CAPTURE_SCHEMA)
        self.assertEqual(result["capture_status"], "PASS")
        self.assertTrue(result["network_request_made"])
        self.assertEqual(result["raw_response_bytes"], len(raw))
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)
        self.assertEqual(result["response_headers"]["ETag"], '"fixture-etag"')
        self.assertEqual(result["feed_item_count"], 1)
        item = result["feed_items"][0]
        self.assertEqual(item["published_at_utc"], "2026-10-22T12:00:00Z")
        self.assertEqual(item["timestamp_status"], "PARSED")
        self.assertEqual(item["entity_resolution_status"], "NOT_RESOLVED")
        self.assertIn("STABLE_ASSET_IDENTIFIER_NOT_SUPPLIED", item["reason_codes"])
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "https://www.sec.gov/news/pressreleases.rss")
        self.assertEqual(request.get_header("User-agent"), self.user_agent)
        self.assertEqual(opener.call_args.kwargs["timeout"], 5)

    def test_response_larger_than_five_mib_is_preserved_without_local_cap(self):
        raw = rss_bytes().replace(
            b"Fixture summary, not a real event.",
            b"x" * (5 * 1024 * 1024 + 123),
        )
        with self.approved_registry() as registry:
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at, opener=Mock(return_value=FakeResponse(raw)),
            )
        self.assertGreater(len(raw), 5 * 1024 * 1024)
        self.assertEqual(result["raw_response_bytes"], len(raw))
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(result["feed_items"][0]["description"]), 5 * 1024 * 1024 + 123)

    def test_missing_or_unparseable_publication_time_is_not_inferred(self):
        with self.approved_registry() as registry:
            raw = rss_bytes(pub_date=None)
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at, opener=Mock(return_value=FakeResponse(raw)),
            )
        item = result["feed_items"][0]
        self.assertEqual(result["capture_status"], "PASS")
        self.assertIsNone(item["published_at_utc"])
        self.assertEqual(item["timestamp_status"], "MISSING_PUBLISHED_AT")

    def test_midstream_read_error_preserves_all_bytes_received_before_failure(self):
        raw = rss_bytes().replace(b"Fixture summary, not a real event.", b"x" * 200000)
        cutoff = 100000
        with self.approved_registry() as registry:
            response = FakeResponse(raw, error_after_bytes=cutoff)
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at, opener=Mock(return_value=response),
            )
        partial = base64.b64decode(result["raw_response_base64"])
        self.assertEqual(result["capture_status"], "NETWORK_ERROR")
        self.assertTrue(result["capture_truncated"])
        self.assertEqual(len(partial), cutoff)
        self.assertEqual(result["raw_response_bytes"], cutoff)
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(partial).hexdigest())
        self.assertIn("NETWORK_RESPONSE_READ_FAILED", result["reason_codes"])

    def test_malformed_xml_preserves_complete_body_and_reports_parse_error(self):
        raw = b"<rss><channel><item>unfinished"
        with self.approved_registry() as registry:
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at, opener=Mock(return_value=FakeResponse(raw)),
            )
        self.assertEqual(result["capture_status"], "PARSE_ERROR")
        self.assertEqual(result["raw_response_bytes"], len(raw))
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(raw).hexdigest())

    def test_http_error_preserves_body_and_status(self):
        raw = b"SEC fixture rate limit body"
        error = HTTPError(
            "https://www.sec.gov/news/pressreleases.rss", 429, "Too Many Requests",
            {"Content-Type": "text/plain"}, io.BytesIO(raw),
        )
        with self.approved_registry() as registry:
            result = capture_sec_press_releases_rss(
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at, opener=Mock(side_effect=error),
            )
        self.assertEqual(result["capture_status"], "HTTP_ERROR")
        self.assertEqual(result["http_status"], 429)
        self.assertEqual(result["raw_response_bytes"], len(raw))
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)

    def test_unexpected_article_content_type_preserves_body_but_cannot_be_promoted(self):
        raw = b'{"not":"an article"}'
        with self.approved_registry() as registry:
            result = capture_sec_press_release_article(
                "https://www.sec.gov/news/press-release/example",
                authorization_record(registry["sec_press_releases"]), self.user_agent, 5,
                captured_at=self.captured_at,
                opener=Mock(return_value=FakeResponse(raw, headers={"Content-Type": "application/json"})),
            )
        self.assertEqual(result["capture_status"], "CONTENT_TYPE_UNEXPECTED")
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)
        self.assertIn("ARTICLE_CONTENT_TYPE_UNEXPECTED", result["reason_codes"])

    def test_article_url_outside_allowlist_is_blocked_before_network(self):
        with self.approved_registry() as registry:
            opener = Mock()
            result = capture_sec_press_release_article(
                "https://example.com/not-sec", authorization_record(registry["sec_press_releases"]),
                self.user_agent, 5, captured_at=self.captured_at, opener=opener,
            )
        self.assertEqual(result["schema_version"], ARTICLE_CAPTURE_SCHEMA)
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("ARTICLE_URL_NOT_ALLOWLISTED", result["reason_codes"])
        opener.assert_not_called()

    def test_article_capture_and_event_promotion_require_reviewed_stable_entity(self):
        feed_raw = rss_bytes()
        article_raw = b"<html><title>SEC fixture article</title><body>Fixture content</body></html>"
        with self.approved_registry() as registry:
            entry = registry["sec_press_releases"]
            record = authorization_record(entry)
            feed = capture_sec_press_releases_rss(
                record, self.user_agent, 5, captured_at=self.captured_at,
                opener=Mock(return_value=FakeResponse(feed_raw)),
            )
            article_url = feed["feed_items"][0]["link"]
            article = capture_sec_press_release_article(
                article_url, record, self.user_agent, 5,
                captured_at="2026-10-22T12:31:00Z",
                opener=Mock(return_value=FakeResponse(article_raw, headers={"Content-Type": "text/html"})),
            )
            event = promote_sec_press_release_to_event(
                feed, feed["feed_items"][0]["item_id"], article,
                "REGULATORY_ENFORCEMENT",
                "The captured SEC press release states the reviewed claim.",
                {
                    "status": "APPROVED",
                    "reviewed_by": "offline-test-fixture",
                    "reviewed_at": "2026-10-22T12:32:00Z",
                    "evidence_record_base64": base64.b64encode(b"synthetic reviewed entity mapping evidence").decode("ascii"),
                    "evidence_record_sha256": hashlib.sha256(b"synthetic reviewed entity mapping evidence").hexdigest(),
                    "entities": [{"id_type": "project_id", "id": "registry:example-project"}],
                },
            )
        self.assertEqual(article["capture_status"], "PASS")
        self.assertEqual(event["schema_version"], "crypto-external-event-record-v1")
        self.assertEqual(event["content_sha256"], hashlib.sha256(article_raw).hexdigest())
        self.assertEqual(event["entities"], [{"id_type": "project_id", "id": "registry:example-project"}])
        self.assertEqual(event["metadata"]["causality_status"], "NOT_ASSESSED")

    def test_event_promotion_rejects_ticker_only_entity_mapping(self):
        feed_raw = rss_bytes()
        article_raw = b"<html>fixture</html>"
        with self.approved_registry() as registry:
            entry = registry["sec_press_releases"]
            record = authorization_record(entry)
            feed = capture_sec_press_releases_rss(
                record, self.user_agent, 5, captured_at=self.captured_at,
                opener=Mock(return_value=FakeResponse(feed_raw)),
            )
            article = capture_sec_press_release_article(
                feed["feed_items"][0]["link"], record, self.user_agent, 5,
                captured_at="2026-10-22T12:31:00Z",
                opener=Mock(return_value=FakeResponse(article_raw, headers={"Content-Type": "text/html"})),
            )
            with self.assertRaisesRegex(ValueError, "evidence_record_base64 is required"):
                promote_sec_press_release_to_event(
                    feed, feed["feed_items"][0]["item_id"], article, "REGULATORY_ENFORCEMENT",
                    "Claim grounded in captured source.",
                    {
                        "status": "APPROVED",
                        "reviewed_by": "offline-test-fixture",
                        "reviewed_at": "2026-10-22T12:32:00Z",
                        "entities": [{"id_type": "project_id", "id": "registry:example-project"}],
                    },
                )
            with self.assertRaisesRegex(ValueError, "ticker-only matching is forbidden"):
                promote_sec_press_release_to_event(
                    feed, feed["feed_items"][0]["item_id"], article, "REGULATORY_ENFORCEMENT",
                    "Claim grounded in captured source.",
                    {
                        "status": "APPROVED",
                        "reviewed_by": "offline-test-fixture",
                        "reviewed_at": "2026-10-22T12:32:00Z",
                        "evidence_record_base64": base64.b64encode(b"synthetic reviewed entity mapping evidence").decode("ascii"),
                        "evidence_record_sha256": hashlib.sha256(b"synthetic reviewed entity mapping evidence").hexdigest(),
                        "entities": [{"id_type": "symbol", "id": "BTC"}],
                    },
                )

    def test_approved_registry_requires_hash_matching_preserved_terms(self):
        entry = approved_entry()
        entry["terms_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "does not match preserved terms_content_base64"):
            validate_source_entry(entry)

    def test_sec_rate_limit_cannot_be_configured_above_published_ceiling(self):
        entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"]["sec_press_releases"])
        entry["max_requests_per_second"] = 11
        with self.assertRaisesRegex(ValueError, "published 10 requests/second ceiling"):
            validate_source_entry(entry)


if __name__ == "__main__":
    unittest.main()
