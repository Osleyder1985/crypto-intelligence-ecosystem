"""Offline tests for snapshot + buffered Binance depth-event synchronization."""
import unittest

from scripts.market_selection.binance_depth_stream import synchronize_snapshot_with_events


def snapshot():
    return {
        "lastUpdateId": 100,
        "bids": [["99.0", "2.0"], ["98.0", "3.0"]],
        "asks": [["101.0", "4.0"], ["102.0", "5.0"]],
    }


def event(first=101, final=102, **overrides):
    value = {
        "e": "depthUpdate",
        "E": 1_797_000_000_123,
        "s": "BTCUSDT",
        "U": first,
        "u": final,
        "b": [],
        "a": [],
    }
    value.update(overrides)
    return value


class SnapshotSynchronizationTests(unittest.TestCase):
    def test_bridges_snapshot_and_applies_updates_in_price_order(self):
        result = synchronize_snapshot_with_events(snapshot(), [
            event(first=99, final=100, b=[["97", "1"]]),  # old, ignored
            event(
                first=101,
                final=102,
                b=[["99.0", "0"], ["100.0", "1.5"]],
                a=[["101.0", "3.0"], ["100.5", "2.0"]],
            ),
        ])
        self.assertEqual(result["status"], "SYNCHRONIZED")
        self.assertEqual(result["last_applied_update_id"], 102)
        self.assertEqual(result["applied_event_count"], 1)
        self.assertEqual(result["bids"], [["100.0", "1.5"], ["98.0", "3.0"]])
        self.assertEqual(result["asks"], [["100.5", "2.0"], ["101.0", "3.0"], ["102.0", "5.0"]])
        self.assertTrue(result["last_event_time_utc"].endswith("Z"))

    def test_initial_gap_requires_resynchronization_and_exposes_no_book(self):
        result = synchronize_snapshot_with_events(snapshot(), [event(first=102, final=103)])
        self.assertEqual(result["status"], "RESYNC_REQUIRED")
        self.assertIsNone(result["bids"])
        self.assertIsNone(result["asks"])

    def test_gap_after_applied_event_discards_partial_book(self):
        result = synchronize_snapshot_with_events(snapshot(), [
            event(first=101, final=102),
            event(first=104, final=105),
        ])
        self.assertEqual(result["status"], "RESYNC_REQUIRED")
        self.assertEqual(result["applied_event_count"], 1)
        self.assertIsNone(result["bids"])

    def test_no_event_bridging_snapshot_is_indeterminate(self):
        result = synchronize_snapshot_with_events(snapshot(), [event(first=98, final=100)])
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertIsNone(result["asks"])

    def test_rejects_crossed_snapshot(self):
        bad = snapshot()
        bad["bids"] = [["102", "1"]]
        with self.assertRaisesRegex(ValueError, "locked or crossed"):
            synchronize_snapshot_with_events(bad, [])

    def test_rejects_duplicate_snapshot_price(self):
        bad = snapshot()
        bad["bids"] = [["99", "1"], ["99", "2"]]
        with self.assertRaisesRegex(ValueError, "duplicate price"):
            synchronize_snapshot_with_events(bad, [])

    def test_rejects_buffered_events_from_different_symbols(self):
        with self.assertRaisesRegex(ValueError, "same symbol"):
            synchronize_snapshot_with_events(snapshot(), [
                event(first=101, final=102, s="BTCUSDT"),
                event(first=103, final=104, s="ETHUSDT"),
            ])

    def test_discards_book_if_applied_event_crosses_bid_and_ask(self):
        result = synchronize_snapshot_with_events(snapshot(), [
            event(first=101, final=102, b=[["102", "1"]]),
        ])
        self.assertEqual(result["status"], "RESYNC_REQUIRED")
        self.assertIn("crossed", result["reason"])
        self.assertIsNone(result["bids"])
        self.assertIsNone(result["asks"])

    def test_discards_book_if_applied_event_removes_entire_side(self):
        result = synchronize_snapshot_with_events(snapshot(), [
            event(first=101, final=102, b=[["99.0", "0"], ["98.0", "0"]]),
        ])
        self.assertEqual(result["status"], "RESYNC_REQUIRED")
        self.assertIsNone(result["bids"])

    def test_freshness_adapter_keeps_source_and_receive_times_separate(self):
        from scripts.market_selection.binance_depth_stream import freshness_observation_from_sync
        result = synchronize_snapshot_with_events(snapshot(), [event(first=101, final=102)])
        observation = freshness_observation_from_sync(
            result, "2026-10-21T12:00:02Z", "2026-10-21T12:00:05Z"
        )
        self.assertEqual(observation["source_timestamp_utc"], result["last_event_time_utc"])
        self.assertEqual(observation["captured_at_utc"], "2026-10-21T12:00:02Z")
        self.assertNotEqual(observation["source_timestamp_utc"], observation["captured_at_utc"])

    def test_freshness_adapter_rejects_unsynchronized_book(self):
        from scripts.market_selection.binance_depth_stream import freshness_observation_from_sync
        with self.assertRaisesRegex(ValueError, "SYNCHRONIZED"):
            freshness_observation_from_sync({"status": "RESYNC_REQUIRED"}, "2026-10-21T12:00:02Z", "2026-10-21T12:00:05Z")

    def test_freshness_adapter_requires_receive_and_evaluation_times(self):
        from scripts.market_selection.binance_depth_stream import freshness_observation_from_sync
        result = synchronize_snapshot_with_events(snapshot(), [event(first=101, final=102)])
        with self.assertRaisesRegex(ValueError, "received_at_utc"):
            freshness_observation_from_sync(result, None, "2026-10-21T12:00:05Z")
    def test_rejects_malformed_event_in_buffer(self):
        with self.assertRaisesRegex(ValueError, "event type"):
            synchronize_snapshot_with_events(snapshot(), [{"e": "trade"}])


if __name__ == "__main__":
    unittest.main()
