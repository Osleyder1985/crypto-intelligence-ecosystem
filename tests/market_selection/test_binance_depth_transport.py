"""Offline tests for the bounded read-only Binance transport adapter."""
import json
import unittest

from scripts.market_selection.binance_depth_transport import capture_once


def event(first, final, **overrides):
    value = {
        "e": "depthUpdate",
        "E": 1797000000123,
        "s": "BTCUSDT",
        "U": first,
        "u": final,
        "b": [],
        "a": [],
    }
    value.update(overrides)
    return json.dumps(value)


def snapshot(last_update_id=100):
    return {
        "lastUpdateId": last_update_id,
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "4"], ["102", "5"]],
    }


class FakeSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.closed = False

    def recv(self):
        if not self.messages:
            raise AssertionError("test stream exhausted unexpectedly")
        return self.messages.pop(0)

    def close(self):
        self.closed = True


class BinanceDepthTransportTests(unittest.TestCase):
    def test_capture_returns_synchronized_read_only_book_and_closes_socket(self):
        socket = FakeSocket([
            event(101, 102),
            event(103, 104, b=[["100", "1"]]),
        ])
        snapshots = []

        def fetcher(symbol, timeout):
            snapshots.append((symbol, timeout))
            return snapshot(100)

        times = iter([
            "2026-10-21T12:00:02.100Z",
            "2026-10-21T12:00:02.200Z",
            "2026-10-21T12:00:02.300Z",
        ])
        result = capture_once(
            "btcusdt",
            websocket_factory=lambda symbol, timeout: socket,
            snapshot_fetcher=fetcher,
            clock=lambda: next(times),
            max_messages=10,
        )
        self.assertEqual(result["status"], "SYNCHRONIZED")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["last_applied_update_id"], 104)
        self.assertEqual(result["bids"][0], ["100", "1"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(result["freshness_observation"]["captured_at_utc"], "2026-10-21T12:00:02.200Z")
        self.assertEqual(result["freshness_observation"]["evaluation_time_utc"], "2026-10-21T12:00:02.300Z")
        self.assertEqual(snapshots, [("BTCUSDT", 5.0)])
        self.assertTrue(socket.closed)

    def test_capture_restarts_after_sequence_gap(self):
        socket = FakeSocket([
            event(101, 102),
            event(104, 105),
            event(106, 107),
            event(108, 109),
        ])
        calls = []

        def fetcher(symbol, timeout):
            calls.append(symbol)
            return snapshot(100 if len(calls) == 1 else 105)

        times = iter([
            "2026-10-21T12:00:02.100Z",
            "2026-10-21T12:00:02.200Z",
            "2026-10-21T12:00:02.300Z",
            "2026-10-21T12:00:02.400Z",
            "2026-10-21T12:00:02.500Z",
        ])
        result = capture_once(
            "BTCUSDT",
            websocket_factory=lambda symbol, timeout: socket,
            snapshot_fetcher=fetcher,
            clock=lambda: next(times),
            max_messages=10,
            max_resync_attempts=3,
        )
        self.assertEqual(result["status"], "SYNCHRONIZED")
        self.assertEqual(result["last_applied_update_id"], 109)
        self.assertEqual(result["snapshot_attempts"], 2)
        self.assertEqual(len(calls), 2)
        self.assertTrue(socket.closed)

    def test_capture_fails_closed_when_message_bound_is_exhausted(self):
        socket = FakeSocket([event(101, 102)])
        with self.assertRaisesRegex(RuntimeError, "configured bounds"):
            capture_once(
                "BTCUSDT",
                websocket_factory=lambda symbol, timeout: socket,
                snapshot_fetcher=lambda symbol, timeout: snapshot(),
                clock=lambda: "2026-10-21T12:00:02Z",
                max_messages=1,
            )
        self.assertTrue(socket.closed)

    def test_rejects_invalid_capture_bounds(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            capture_once("BTCUSDT", websocket_factory=lambda *_: FakeSocket([]), max_messages=0)


if __name__ == "__main__":
    unittest.main()
