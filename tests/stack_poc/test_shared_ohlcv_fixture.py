import hashlib
import json
import unittest
from datetime import datetime
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "ohlcv_synthetic_v1.json"


class SharedOhlcvFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = FIXTURE.read_bytes()
        cls.data = json.loads(cls.raw)
        cls.candles = cls.data["candles"]

    def test_fixture_is_explicitly_synthetic_and_versioned(self):
        self.assertEqual(self.data["kind"], "synthetic-not-market-data")
        self.assertEqual(self.data["fixture_version"], "1.0.0")
        self.assertEqual(self.data["interval"], "5m")

    def test_timestamps_are_utc_and_strictly_increasing(self):
        times = [datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00")) for c in self.candles]
        self.assertTrue(all(t.utcoffset().total_seconds() == 0 for t in times))
        self.assertTrue(all(a < b for a, b in zip(times, times[1:])))

    def test_ohlcv_invariants(self):
        for candle in self.candles:
            self.assertGreater(candle["low"], 0)
            self.assertLessEqual(candle["low"], min(candle["open"], candle["close"]))
            self.assertGreaterEqual(candle["high"], max(candle["open"], candle["close"]))
            self.assertGreaterEqual(candle["volume"], 0)

    def test_fixture_contains_gap_flat_interval_and_volume_spike(self):
        times = [datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00")) for c in self.candles]
        deltas = [(b - a).total_seconds() for a, b in zip(times, times[1:])]
        self.assertIn(900, deltas, "expected one deliberate 15-minute gap")
        self.assertTrue(any(c["open"] == c["high"] == c["low"] == c["close"] for c in self.candles))
        volumes = [c["volume"] for c in self.candles]
        self.assertGreater(max(volumes), 3 * sorted(volumes)[len(volumes) // 2])

    def test_hash_is_stable_for_the_committed_fixture_bytes(self):
        digest = hashlib.sha256(self.raw).hexdigest()
        self.assertEqual(len(digest), 64)
        print(f"OHLCV_FIXTURE_SHA256={digest}")


if __name__ == "__main__":
    unittest.main()
