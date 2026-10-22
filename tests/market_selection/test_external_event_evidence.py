"""Tests for the source-neutral external event evidence contract."""
import unittest

from scripts.market_selection.external_event_evidence import (
    INPUT_SCHEMA,
    assess_temporal_association,
    deduplicate_events,
    validate_event,
)


def event(**overrides):
    value = {
        "schema_version": INPUT_SCHEMA,
        "event_id": "event-1",
        "title": "Project announces protocol upgrade",
        "event_type": "PROTOCOL_UPDATE",
        "source": {
            "source_type": "PRIMARY_OFFICIAL",
            "url": "https://example.org/announcements/upgrade",
            "publisher": "Example Project",
        },
        "published_at": "2026-10-22T10:00:00Z",
        "captured_at": "2026-10-22T10:01:00Z",
        "entities": [{"id_type": "coingecko_id", "id": "example-coin"}],
        "evidence": [{
            "url": "https://example.org/announcements/upgrade",
            "claim": "The project announced a protocol upgrade.",
        }],
        "capture_method": "fixture",
        "content_sha256": "a" * 64,
        "license_notes": "Terms not yet reviewed",
        "metadata": {},
    }
    value.update(overrides)
    return value


class ExternalEventEvidenceTests(unittest.TestCase):
    def test_validates_and_normalizes_timestamp(self):
        normalized = validate_event(event())
        self.assertEqual(normalized["published_at"], "2026-10-22T10:00:00Z")
        self.assertEqual(normalized["entities"][0]["id"], "example-coin")

    def test_rejects_ticker_only_entity_resolution(self):
        value = event(entities=[{"id_type": "ticker", "id": "EXAMPLE"}])
        with self.assertRaisesRegex(ValueError, "ticker-only matching is forbidden"):
            validate_event(value)

    def test_rejects_timestamp_without_timezone(self):
        value = event(published_at="2026-10-22T10:00:00")
        with self.assertRaisesRegex(ValueError, "explicit UTC offset"):
            validate_event(value)

    def test_rejects_capture_before_publication(self):
        value = event(captured_at="2026-10-22T09:59:00Z")
        with self.assertRaisesRegex(ValueError, "cannot precede"):
            validate_event(value)

    def test_deduplicates_same_canonical_url_and_reports_conflict(self):
        first = event()
        second = event(event_id="event-2", title="Different claim", source={
            "source_type": "PRIMARY_OFFICIAL",
            "url": "https://example.org/announcements/upgrade",
            "publisher": "Example Project",
        })
        result = deduplicate_events([first, second])
        self.assertEqual(result["unique_count"], 1)
        self.assertEqual(result["duplicate_count"], 1)
        self.assertTrue(result["duplicates"][0]["conflict"])
        self.assertEqual(result["duplicates"][0]["resolution"], "CONFLICT_REQUIRES_REVIEW")

    def test_post_cutoff_capture_is_not_eligible_for_backtest(self):
        value = event(
            published_at="2026-10-20T10:00:00Z",
            captured_at="2026-10-22T10:01:00Z",
        )
        result = assess_temporal_association(
            value,
            movement_start="2026-10-20T09:00:00Z",
            movement_end="2026-10-20T12:00:00Z",
            evaluation_as_of="2026-10-21T00:00:00Z",
            target_entity={"id_type": "coingecko_id", "id": "example-coin"},
        )
        self.assertEqual(result["status"], "NOT_AVAILABLE_AS_OF")
        self.assertFalse(result["causality_claimed"])

    def test_overlap_is_only_temporal_association_not_causality(self):
        result = assess_temporal_association(
            event(),
            movement_start="2026-10-22T09:00:00Z",
            movement_end="2026-10-22T11:00:00Z",
            evaluation_as_of="2026-10-22T12:00:00Z",
            target_entity={"id_type": "coingecko_id", "id": "example-coin"},
        )
        self.assertEqual(result["causality_label"], "TEMPORAL_ASSOCIATION")
        self.assertFalse(result["causality_claimed"])
        self.assertTrue(result["evidence_urls"])

    def test_outside_window_does_not_invent_cause(self):
        result = assess_temporal_association(
            event(),
            movement_start="2026-10-22T12:00:00Z",
            movement_end="2026-10-22T14:00:00Z",
            evaluation_as_of="2026-10-22T15:00:00Z",
            target_entity={"id_type": "coingecko_id", "id": "example-coin"},
        )
        self.assertEqual(result["causality_label"], "CAUSE_UNIDENTIFIED")

    def test_rejects_missing_evidence(self):
        value = event(evidence=[])
        with self.assertRaisesRegex(ValueError, "at least one evidence reference"):
            validate_event(value)

    def test_does_not_associate_an_unrelated_asset(self):
        result = assess_temporal_association(
            event(),
            movement_start="2026-10-22T09:00:00Z",
            movement_end="2026-10-22T11:00:00Z",
            evaluation_as_of="2026-10-22T12:00:00Z",
            target_entity={"id_type": "coingecko_id", "id": "different-coin"},
        )
        self.assertEqual(result["status"], "ENTITY_NOT_MATCHED")
        self.assertFalse(result["entity_match"])
        self.assertEqual(result["causality_label"], "CAUSE_UNIDENTIFIED")

    def test_independent_source_urls_remain_separate_records(self):
        first = event()
        second = event(
            event_id="event-2",
            source={
                "source_type": "SECONDARY_MEDIA",
                "url": "https://news.example.net/story/123",
                "publisher": "Example News",
            },
        )
        result = deduplicate_events([first, second])
        self.assertEqual(result["unique_count"], 2)
        self.assertEqual(result["duplicate_count"], 0)


if __name__ == "__main__":
    unittest.main()
