import base64
import copy
import hashlib
import json
import unittest
import socket
from urllib.error import URLError
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    ARTICLE_CAPTURE_SCHEMA,
    FEED_CAPTURE_SCHEMA,
    capture_public_event_article,
    capture_public_event_feed,
)
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.provider_license_gate import SCHEMA_VERSION as AUTH_SCHEMA_VERSION
from scripts.market_selection.capture_public_event_feed import promote_public_feed_candidate_to_event
from scripts.market_selection.research_evidence_integration import _verify_promoted_public_feed_event
from scripts.market_selection.event_source_registry import source_entry_sha256


TERMS = b"Synthetic reviewed source terms fixture"
USER_AGENT = "CryptoIntelligenceTest/1.0 (contact: offline-test-fixture)"


class FakeResponse:
    def __init__(self, body, status=200, headers=None, final_url=None):
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "application/rss+xml", "ETag": '"synthetic"'}
        self.final_url = final_url
        self.offset = 0
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def close(self):
        self.closed = True

    def geturl(self):
        return self.final_url or "https://www.cftc.gov/PressRoom/press-1"

    def read(self, size=-1):
        if self.offset >= len(self.body):
            return b""
        limit = len(self.body) if size is None or size < 0 else min(len(self.body), self.offset + size)
        data = self.body[self.offset:limit]
        self.offset = limit
        return data


def approved_source(source_id="cftc_general_press_releases"):
    entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"][source_id])
    entry.update({
        "status": "APPROVED",
        "terms_sha256": hashlib.sha256(TERMS).hexdigest(),
        "terms_content_base64": base64.b64encode(TERMS).decode("ascii"),
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T12:00:00Z",
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
            "attribution": {
                "required": True,
                "format": "Synthetic test fixture; source URL",
            },
            "automated_access": {
                "approved_endpoint": entry["source_url"],
                "user_agent": USER_AGENT,
                "max_aggregate_requests_per_second": entry["max_requests_per_second"],
                "timeout_seconds": 5,
                "redirect_policy": "HTTPS only; each redirect must remain inside the source allowlist",
            },
            "limitations": ["Synthetic approval fixture; grants no real-world permission"],
            "decision_rationale": "Fixture solely for offline contract tests.",
        },
    })
    return entry


def authorization_record(entry):
    return {
        "schema_version": AUTH_SCHEMA_VERSION,
        "provider_id": entry["provider_id"],
        "status": "APPROVED",
        "authorized_use_cases": ["internal_analysis", "persistent_storage"],
        "terms_url": entry["terms_url"],
        "terms_sha256": entry["terms_sha256"],
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T12:00:00Z",
    }


def feed_xml():
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<rss version="2.0"><channel><title>Fixture</title>'
        b'<item><title>Crypto enforcement update</title><link>https://www.cftc.gov/PressRoom/press-1</link>'
        b'<guid>release-1</guid><pubDate>Thu, 22 Oct 2026 12:00:00 GMT</pubDate>'
        b'<description>Fixture summary</description></item>'
        b'<item><title>Duplicate title</title><link>https://www.cftc.gov/PressRoom/press-2</link>'
        b'<guid>release-1</guid><pubDate>Thu, 22 Oct 2026 12:00:00 GMT</pubDate></item>'
        b'<item><title>Undated notice</title><link>https://www.cftc.gov/PressRoom/press-3</link>'
        b'<guid>release-3</guid><description>No published timestamp in this fixture.</description></item>'
        b'</channel></rss>'
    )


def capture_article(entry, feed_capture, *, final_url=None, captured_at="2026-10-22T12:31:00Z"):
    raw = b"<html><head><title>Official announcement</title></head><body>Full preserved article body.</body></html>"
    candidate = feed_capture["feed_items"][0]
    with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
        "scripts.market_selection.capture_public_event_feed._open_allowlisted_url",
        return_value=FakeResponse(
            raw, headers={"Content-Type": "text/html; charset=utf-8"}, final_url=final_url
        ),
    ):
        result = capture_public_event_article(
            feed_capture,
            candidate["candidate_id"],
            authorization_record(entry),
            USER_AGENT,
            captured_at=captured_at,
        )
    return result


class PublicEventFeedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.captured_at = "2026-10-22T12:30:00Z"

    def test_terms_pending_source_blocks_before_network(self):
        with patch("scripts.market_selection.capture_public_event_feed.urlopen") as network:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=None,
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        network.assert_not_called()
        self.assertEqual(result["schema_version"], FEED_CAPTURE_SCHEMA)
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])
        self.assertIn("SOURCE_TERMS_PENDING", result["reason_codes"])

    def test_approved_generic_rss_capture_preserves_body_and_deduplicates(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(feed_xml()),
        ) as network:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        network.assert_called_once()
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["raw_response_bytes"], len(feed_xml()))
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(feed_xml()).hexdigest())
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), feed_xml())
        self.assertEqual(result["feed_item_count"], 3)
        self.assertEqual(result["unique_item_count"], 2)
        self.assertEqual(result["duplicate_item_count"], 1)
        self.assertEqual(result["feed_items"][0]["publication_time_status"], "PARSED")
        self.assertEqual(result["feed_items"][1]["publication_time_status"], "MISSING")
        self.assertEqual(result["feed_items"][1]["published_at"], None)
        self.assertEqual(result["feed_items"][0]["asset_identity_status"], "NOT_RESOLVED")
        self.assertFalse(result["events_promoted"])
        self.assertFalse(result["orders_submitted"])

    def test_promotes_candidate_only_with_explicit_reviewed_stable_entity_mapping(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(feed_xml()),
        ):
            capture = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        evidence = b'{"asset":"example-asset","mapping":"reviewed"}'
        resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-reviewer",
            "reviewed_at": "2026-10-22T12:20:00Z",
            "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
            "evidence_record_base64": base64.b64encode(evidence).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(evidence).hexdigest(),
        }
        article = capture_article(entry, capture)
        self.assertEqual(article["schema_version"], ARTICLE_CAPTURE_SCHEMA)
        self.assertEqual(article["capture_status"], "PASS")
        self.assertEqual(article["raw_response_sha256"], hashlib.sha256(
            base64.b64decode(article["raw_response_base64"])
        ).hexdigest())
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}):
            event = promote_public_feed_candidate_to_event(
                capture,
                capture["feed_items"][0]["candidate_id"],
                "REGULATORY_ENFORCEMENT",
                "The preserved article body reports a regulatory announcement.",
                resolution,
                article_capture=article,
            )
        self.assertEqual(event["source_id"], "cftc_general_press_releases")
        self.assertEqual(event["entities"], [{"id_type": "coingecko_id", "id": "example-asset"}])
        self.assertFalse(event["causality_claimed"])
        self.assertFalse(event["orders_submitted"])
        self.assertEqual(event["metadata"]["causality_status"], "NOT_ASSESSED")
        _verify_promoted_public_feed_event(event, entry, source_entry_sha256(entry))

    def test_promotion_rejects_ticker_only_entity_mapping(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(feed_xml()),
        ):
            capture = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        evidence = b'{"ticker":"BTC"}'
        resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-reviewer",
            "reviewed_at": "2026-10-22T12:20:00Z",
            "entities": [{"id_type": "ticker", "id": "BTC"}],
            "evidence_record_base64": base64.b64encode(evidence).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(evidence).hexdigest(),
        }
        article = capture_article(entry, capture)
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}):
            with self.assertRaisesRegex(ValueError, "stable identifier"):
                promote_public_feed_candidate_to_event(
                    capture,
                    capture["feed_items"][0]["candidate_id"],
                    "REGULATORY_ENFORCEMENT",
                    "Explicit claim from the preserved article.",
                    resolution,
                    article_capture=article,
                )

    def test_future_publication_timestamp_is_flagged_against_capture_cutoff(self):
        entry = approved_source()
        raw = (
            b'<rss><channel><item><title>Scheduled notice</title>'
            b'<link>https://www.cftc.gov/PressRoom/press-future</link><guid>future-1</guid>'
            b'<pubDate>Fri, 23 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(raw),
        ):
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["feed_items"][0]["publication_time_status"], "AFTER_CAPTURE_CUTOFF")
        self.assertEqual(result["feed_items"][0]["event_verification_status"], "CANDIDATE_ONLY")

    def test_missing_user_agent_blocks_before_network(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen"
        ) as network:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=None,
                captured_at=self.captured_at,
            )
        network.assert_not_called()
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertIn("USER_AGENT_REQUIRED", result["reason_codes"])

    def test_off_host_item_link_is_flagged_and_never_fetched(self):
        entry = approved_source()
        raw = (
            b'<rss><channel><item><title>External link</title>'
            b'<link>https://evil.example/news</link><guid>off-host-1</guid>'
            b'<pubDate>Thu, 22 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>'
        )
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(raw),
        ) as network:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(result["feed_items"][0]["url_status"], "OUTSIDE_SOURCE_ALLOWLIST")
        network.assert_called_once()

    def test_malformed_feed_preserves_full_response_and_reports_parse_error(self):
        entry = approved_source()
        raw = b"<rss><channel><item>"
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(raw),
        ):
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        self.assertEqual(result["capture_status"], "PARSE_ERROR")
        self.assertEqual(base64.b64decode(result["raw_response_base64"]), raw)
        self.assertEqual(result["raw_response_bytes"], len(raw))
        self.assertFalse(result["events_promoted"])


    def test_invalid_authorization_record_fails_closed_without_network(self):
        entry = approved_source()
        invalid_authorization = {"schema_version": "invalid-schema"}
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen"
        ) as network:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=invalid_authorization,
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        network.assert_not_called()
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])
        self.assertTrue(any(
            reason in result["reason_codes"]
            for reason in ("AUTHORIZATION_RECORD_INVALID", "AUTHORIZATION_TERMS_HASH_MISMATCH")
        ))



    def test_feed_capture_retries_transient_dns_resolution_failure(self):
        entry = approved_source()
        response = FakeResponse(feed_xml())
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            side_effect=[URLError(socket.gaierror(-3, "temporary DNS failure")), response],
        ) as network, patch("scripts.market_selection.capture_public_event_feed.time.sleep") as sleep:
            result = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        self.assertEqual(result["capture_status"], "PASS")
        self.assertTrue(result["network_request_made"])
        self.assertEqual(network.call_count, 2)
        sleep.assert_called_once_with(0.25)

    def test_article_capture_blocks_terms_pending_source_before_network(self):
        blocked_feed = capture_public_event_feed(
            "cftc_general_press_releases", authorization_record=None,
            user_agent=USER_AGENT, captured_at=self.captured_at,
        )
        with patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as network:
            result = capture_public_event_article(
                blocked_feed, "candidate-1", authorization_record=None,
                user_agent=USER_AGENT, captured_at="2026-10-22T12:31:00Z",
            )
        network.assert_not_called()
        self.assertEqual(result["capture_status"], "BLOCKED")
        self.assertFalse(result["network_request_made"])

    def test_article_capture_blocks_off_allowlist_final_url(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(feed_xml()),
        ):
            feed = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=authorization_record(entry),
                user_agent=USER_AGENT,
                captured_at=self.captured_at,
            )
        result = capture_article(
            entry, feed, final_url="https://evil.example/redirected-article",
        )
        self.assertEqual(result["capture_status"], "BLOCKED_REDIRECT_TARGET")
        self.assertIn("FINAL_URL_OUTSIDE_ALLOWLIST", result["reason_codes"])


    def test_every_registry_source_pending_is_blocked_before_network(self):
        # This invariant applies to all feed and archive source IDs, including
        # sources added in the future: no pending registry entry may reach I/O.
        for source_id, entry in EVENT_SOURCE_REGISTRY["sources"].items():
            if entry["status"] != "TERMS_PENDING":
                continue
            with self.subTest(source_id=source_id):
                with patch("scripts.market_selection.capture_public_event_feed.urlopen") as network, patch(
                    "scripts.market_selection.capture_public_event_feed._open_allowlisted_url"
                ) as article_network:
                    result = capture_public_event_feed(
                        source_id,
                        authorization_record=None,
                        user_agent=USER_AGENT,
                        captured_at=self.captured_at,
                    )
                network.assert_not_called()
                article_network.assert_not_called()
                self.assertEqual(result["capture_status"], "BLOCKED")
                self.assertFalse(result["network_request_made"])
                self.assertIn("SOURCE_TERMS_PENDING", result["reason_codes"])

    def test_approved_source_requires_explicit_decision_scope(self):
        entry = approved_source()
        entry.pop("approval_scope")
        with self.assertRaisesRegex(ValueError, "approval_scope"):
            source_entry_sha256(entry)

    def test_approved_source_rejects_excessive_aggregate_access_scope(self):
        entry = approved_source()
        entry["approval_scope"]["automated_access"]["max_aggregate_requests_per_second"] = (
            entry["max_requests_per_second"] + 1
        )
        with self.assertRaisesRegex(ValueError, "exceeds the source registry ceiling"):
            source_entry_sha256(entry)

    def test_approved_source_rejects_unapproved_endpoint_host(self):
        entry = approved_source()
        entry["approval_scope"]["automated_access"]["approved_endpoint"] = "https://unapproved.example/feed"
        with self.assertRaisesRegex(ValueError, "outside allowed_article_hosts"):
            source_entry_sha256(entry)

    def test_approved_source_rejects_archive_endpoint_outside_path_prefix(self):
        entry = approved_source("cftc_press_release_archive")
        entry["approval_scope"]["automated_access"]["approved_endpoint"] = (
            "https://www.cftc.gov/PressRoom/PressReleasesEvil"
        )
        with self.assertRaisesRegex(ValueError, "outside allowed_archive_path_prefixes"):
            source_entry_sha256(entry)

    def test_approved_source_rejects_invalid_registry_rate_before_comparison(self):
        entry = approved_source()
        entry["max_requests_per_second"] = "not-a-number"
        with self.assertRaisesRegex(ValueError, "max_requests_per_second must be positive"):
            source_entry_sha256(entry)


if __name__ == "__main__":
    unittest.main()
