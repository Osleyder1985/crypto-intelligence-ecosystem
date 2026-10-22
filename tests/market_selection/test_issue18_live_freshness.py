"""Regression fixtures for freshness policy gates; fixture thresholds are not product policy."""
import unittest

from scripts.market_selection.evaluate_capture_batch import _live_freshness


def observation(source="2026-10-22T00:00:00.000Z", captured="2026-10-22T00:00:00.100Z",
                evaluated="2026-10-22T00:00:00.200Z", skew=10):
    return {
        "symbol": "BTCUSDT",
        "status": "SYNCHRONIZED",
        "read_only": True,
        "clock_skew_ms": skew,
        "freshness_observation": {
            "source_timestamp_utc": source,
            "captured_at_utc": captured,
            "evaluation_time_utc": evaluated,
        },
    }


def approved_config():
    # Synthetic test-only limits. They are not approved product thresholds.
    return {"freshness_policy": {
        "approval_status": "APPROVED",
        "version": "fixture-v1",
        "approval_ref": "TEST-FIXTURE-ONLY",
        "max_source_lag_seconds": 0.5,
        "max_snapshot_age_seconds": 1.0,
        "max_clock_skew_ms": 50,
    }}


class LiveFreshnessFixtureTests(unittest.TestCase):
    def test_missing_live_observation_is_indeterminate(self):
        status, metrics, reason = _live_freshness({}, "BTCUSDT", approved_config())
        self.assertEqual(status, "INDETERMINATE")
        self.assertEqual(metrics, {})
        self.assertIn("no live source-event timestamp", reason)

    def test_unapproved_policy_is_indeterminate(self):
        cfg = approved_config()
        cfg["freshness_policy"]["approval_status"] = "PENDING"
        status, _, reason = _live_freshness({"live_depth_observations": [observation()]}, "BTCUSDT", cfg)
        self.assertEqual(status, "INDETERMINATE")
        self.assertIn("not been explicitly approved", reason)

    def test_fresh_observation_passes_only_with_explicit_policy_fixture(self):
        status, metrics, reason = _live_freshness(
            {"live_depth_observations": [observation()]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "PASS")
        self.assertAlmostEqual(metrics["source_lag_seconds"], 0.1)
        self.assertAlmostEqual(metrics["snapshot_age_seconds"], 0.1)
        self.assertEqual(metrics["freshness_policy_approval_ref"], "TEST-FIXTURE-ONLY")
        self.assertIn("approved policy", reason)

    def test_stale_source_event_fails_approved_policy_fixture(self):
        obs = observation(source="2026-10-21T23:59:58.000Z")
        status, metrics, reason = _live_freshness(
            {"live_depth_observations": [obs]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "FAIL")
        self.assertGreater(metrics["source_lag_seconds"], 0.5)
        self.assertIn("exceeds an approved age limit", reason)

    def test_stale_snapshot_fails_approved_policy_fixture(self):
        obs = observation(evaluated="2026-10-22T00:00:03.000Z")
        status, metrics, reason = _live_freshness(
            {"live_depth_observations": [obs]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "FAIL")
        self.assertGreater(metrics["snapshot_age_seconds"], 1.0)
        self.assertIn("exceeds an approved age limit", reason)

    def test_clock_skew_over_approved_fixture_limit_fails(self):
        status, metrics, reason = _live_freshness(
            {"live_depth_observations": [observation(skew=51)]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "FAIL")
        self.assertEqual(metrics["clock_skew_ms"], 51)
        self.assertIn("clock skew exceeds", reason)

    def test_missing_timestamp_is_indeterminate(self):
        obs = observation()
        del obs["freshness_observation"]["source_timestamp_utc"]
        status, _, reason = _live_freshness(
            {"live_depth_observations": [obs]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "INDETERMINATE")
        self.assertIn("timestamps are invalid or inconsistent", reason)

    def test_future_timestamp_is_indeterminate_not_pass(self):
        obs = observation(source="2026-10-22T00:00:01.000Z")
        status, _, reason = _live_freshness(
            {"live_depth_observations": [obs]}, "BTCUSDT", approved_config()
        )
        self.assertEqual(status, "INDETERMINATE")
        self.assertIn("timestamps are invalid or inconsistent", reason)

    def test_invalid_policy_limit_is_indeterminate(self):
        cfg = approved_config()
        cfg["freshness_policy"]["max_source_lag_seconds"] = -1
        status, _, reason = _live_freshness(
            {"live_depth_observations": [observation()]}, "BTCUSDT", cfg
        )
        self.assertEqual(status, "INDETERMINATE")
        self.assertIn("timestamps are invalid or inconsistent", reason)


if __name__ == "__main__":
    unittest.main()
