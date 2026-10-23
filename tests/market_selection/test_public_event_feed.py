import base64
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    FEED_CAPTURE_SCHEMA,
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
    def __init__(self, body, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "application/rss+xml", "ETag": '"synthetic"'}
        self.offset = 0
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False

    def close(self):
        self.closed = True

    def read(self, size=-1):
        if self.offset >= len(self.body):
            return b""
        limit = len(self.body) if size is None or size < 0 else min(len(self.body), self.offset + size)
        data = self.body[self.offset:limit]
        self.offset = limit
        return data


def approved_source():
    entry = copy.deepcopy(EVENT_SOURCE_REGISTRY["sources"]["cftc_general_press_releases"])
    entry.update({
        "status": "APPROVED",
        "terms_sha256": hashlib.sha256(TERMS).hexdigest(),
        "terms_content_base64": base64.b64encode(TERMS).decode("ascii"),
        "reviewed_by": "offline-test-fixture",
        "reviewed_at": "2026-10-22T12:00:00Z",
        "allowed_use_cases": ["internal_analysis", "persistent_storage"],
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
        event = promote_public_feed_candidate_to_event(
            capture,
            capture["feed_items"][0]["candidate_id"],
            "REGULATORY_ENFORCEMENT",
            "The preserved feed summary reports a regulatory announcement.",
            resolution,
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
        with self.assertRaisesRegex(ValueError, "stable identifier"):
            promote_public_feed_candidate_to_event(
                capture,
                capture["feed_items"][0]["candidate_id"],
                "REGULATORY_ENFORCEMENT",
                "Explicit claim from the preserved feed.",
                resolution,
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


if __name__ == "__main__":
    unittest.main()
