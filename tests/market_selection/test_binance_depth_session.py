"""Offline lifecycle tests for the transport-agnostic depth session."""
import unittest

from scripts.market_selection.binance_depth_session import (
    APPLY,
    BUFFERING,
    DISCONNECTED,
    RESYNC_REQUIRED,
    SYNCHRONIZED,
    DepthBookSession,
)


def snapshot():
    return {
        "lastUpdateId": 100,
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "4"], ["102", "5"]],
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


class DepthBookSessionTests(unittest.TestCase):
    def test_buffers_then_installs_snapshot_and_applies_live_events(self):
        session = DepthBookSession()
        self.assertEqual(session.state, DISCONNECTED)
        session.begin_resync("BTCUSDT")
        self.assertEqual(session.state, BUFFERING)
        self.assertEqual(session.receive_event(event(), "2026-10-21T12:00:02Z")["action"], "BUFFERED")

        installed = session.install_snapshot(snapshot())
        self.assertEqual(installed["state"], SYNCHRONIZED)
        self.assertEqual(installed["action"], "BOOK_READY")
        self.assertEqual(session.current_book["last_applied_update_id"], 102)

        applied = session.receive_event(event(first=103, final=104, b=[["100", "1"]]), "2026-10-21T12:00:03Z")
        self.assertEqual(applied["action"], APPLY)
        self.assertEqual(session.current_book["last_applied_update_id"], 104)
        self.assertEqual(session.current_book["bids"][0], ["100", "1"])

    def test_sequence_gap_invalidates_book_until_resync(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02Z")
        session.install_snapshot(snapshot())
        result = session.receive_event(event(first=104, final=105), "2026-10-21T12:00:04Z")
        self.assertEqual(result["action"], "RESYNC_REQUIRED")
        self.assertEqual(session.state, RESYNC_REQUIRED)
        self.assertIsNone(session.current_book)

    def test_disconnect_invalidates_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02Z")
        session.install_snapshot(snapshot())
        result = session.disconnect()
        self.assertEqual(result["action"], "BOOK_INVALIDATED")
        self.assertEqual(session.state, DISCONNECTED)
        self.assertIsNone(session.current_book)

    def test_wrong_symbol_invalidates_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02Z")
        session.install_snapshot(snapshot())
        result = session.receive_event(event(first=103, final=104, s="ETHUSDT"), "2026-10-21T12:00:03Z")
        self.assertEqual(result["action"], "RESYNC_REQUIRED")
        self.assertIsNone(session.current_book)

    def test_snapshot_without_bridging_event_never_exposes_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(first=98, final=100), "2026-10-21T12:00:01Z")
        result = session.install_snapshot(snapshot())
        self.assertEqual(result["state"], RESYNC_REQUIRED)
        self.assertIsNone(result["book"])
        self.assertIsNone(session.current_book)

    def test_cannot_install_snapshot_without_starting_resync(self):
        session = DepthBookSession()
        with self.assertRaisesRegex(RuntimeError, "begin_resync"):
            session.install_snapshot(snapshot())

    def test_current_book_is_defensive_copy(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02Z")
        session.install_snapshot(snapshot())
        copy = session.current_book
        copy["bids"].clear()
        self.assertTrue(session.current_book["bids"])



    def test_freshness_observation_uses_event_and_receive_times_separately(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02.123Z")
        session.install_snapshot(snapshot())
        observation = session.freshness_observation("2026-10-21T12:00:05Z")
        self.assertEqual(observation["captured_at_utc"], "2026-10-21T12:00:02.123Z")
        self.assertEqual(observation["source_timestamp_utc"], session.current_book["last_event_time_utc"])
        self.assertEqual(observation["evaluation_time_utc"], "2026-10-21T12:00:05Z")

    def test_receive_timestamp_requires_explicit_timezone(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            session.receive_event(event(), "2026-10-21T12:00:02")

    def test_receive_timestamp_must_be_valid_iso8601(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        with self.assertRaisesRegex(ValueError, "ISO-8601"):
            session.receive_event(event(), "not-a-timestamp")

    def test_freshness_observation_rejects_invalidated_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(), "2026-10-21T12:00:02Z")
        session.install_snapshot(snapshot())
        session.disconnect()
        with self.assertRaisesRegex(ValueError, "SYNCHRONIZED"):
            session.freshness_observation("2026-10-21T12:00:05Z")

if __name__ == "__main__":
    unittest.main()
