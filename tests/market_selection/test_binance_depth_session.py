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
        self.assertEqual(session.receive_event(event())["action"], "BUFFERED")

        installed = session.install_snapshot(snapshot())
        self.assertEqual(installed["state"], SYNCHRONIZED)
        self.assertEqual(installed["action"], "BOOK_READY")
        self.assertEqual(session.current_book["last_applied_update_id"], 102)

        applied = session.receive_event(event(first=103, final=104, b=[["100", "1"]]))
        self.assertEqual(applied["action"], APPLY)
        self.assertEqual(session.current_book["last_applied_update_id"], 104)
        self.assertEqual(session.current_book["bids"][0], ["100", "1"])

    def test_sequence_gap_invalidates_book_until_resync(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event())
        session.install_snapshot(snapshot())
        result = session.receive_event(event(first=104, final=105))
        self.assertEqual(result["action"], "RESYNC_REQUIRED")
        self.assertEqual(session.state, RESYNC_REQUIRED)
        self.assertIsNone(session.current_book)

    def test_disconnect_invalidates_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event())
        session.install_snapshot(snapshot())
        result = session.disconnect()
        self.assertEqual(result["action"], "BOOK_INVALIDATED")
        self.assertEqual(session.state, DISCONNECTED)
        self.assertIsNone(session.current_book)

    def test_wrong_symbol_invalidates_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event())
        session.install_snapshot(snapshot())
        result = session.receive_event(event(first=103, final=104, s="ETHUSDT"))
        self.assertEqual(result["action"], "RESYNC_REQUIRED")
        self.assertIsNone(session.current_book)

    def test_snapshot_without_bridging_event_never_exposes_book(self):
        session = DepthBookSession()
        session.begin_resync("BTCUSDT")
        session.receive_event(event(first=98, final=100))
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
        session.receive_event(event())
        session.install_snapshot(snapshot())
        copy = session.current_book
        copy["bids"].clear()
        self.assertTrue(session.current_book["bids"])


if __name__ == "__main__":
    unittest.main()
