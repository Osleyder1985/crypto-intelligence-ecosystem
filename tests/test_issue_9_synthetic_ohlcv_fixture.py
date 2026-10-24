"""Deterministic integrity checks for the shared Issue 9 synthetic OHLCV fixture."""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "issue_9_synthetic_ohlcv_v1.json"


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"timestamp must be UTC: {value}")
    return parsed


class SyntheticOhlcvFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.candles = cls.fixture["candles"]

    def test_fixture_is_explicitly_synthetic(self):
        self.assertEqual(self.fixture["fixture_id"], "issue-9-synthetic-ohlcv-v1")
        self.assertIn("not historical market evidence", self.fixture["description"])

    def test_timestamps_are_utc_and_strictly_increasing(self):
        timestamps = [parse_utc(candle["timestamp"]) for candle in self.candles]
        self.assertEqual(timestamps, sorted(timestamps))
        self.assertEqual(len(timestamps), len(set(timestamps)))

    def test_ohlcv_values_obey_candle_invariants(self):
        self.assertGreater(len(self.candles), 0)
        for candle in self.candles:
            with self.subTest(timestamp=candle["timestamp"]):
                opened = candle["open"]
                high = candle["high"]
                low = candle["low"]
                close = candle["close"]
                volume = candle["volume"]
                self.assertGreater(low, 0)
                self.assertLessEqual(low, min(opened, close))
                self.assertLessEqual(max(opened, close), high)
                self.assertGreaterEqual(volume, 0)

    def test_fixture_contains_gap_flat_candle_and_high_volume(self):
        timestamps = [parse_utc(candle["timestamp"]) for candle in self.candles]
        gaps = [(right - left).total_seconds() for left, right in zip(timestamps, timestamps[1:])]
        self.assertTrue(any(gap > self.fixture["interval_seconds"] for gap in gaps))
        self.assertTrue(any(c["open"] == c["high"] == c["low"] == c["close"] for c in self.candles))
        volumes = [c["volume"] for c in self.candles]
        self.assertGreater(max(volumes), 3 * sorted(volumes)[len(volumes) // 2])

    def test_fixture_shape_is_suitable_for_cross_client_assertions(self):
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        for candle in self.candles:
            self.assertEqual(set(candle), required)
        self.assertEqual(self.fixture["interval_seconds"], 60)
        self.assertEqual(self.candles[0]["timestamp"], "2026-01-01T00:00:00Z")
        self.assertEqual(self.candles[-1]["timestamp"], "2026-01-01T00:13:00Z")


if __name__ == "__main__":
    unittest.main()
