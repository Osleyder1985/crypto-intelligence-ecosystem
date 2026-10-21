"""Offline contract tests for Binance Spot diff-depth events."""
import unittest

from scripts.market_selection.binance_depth_stream import (
    APPLY,
    GAP,
    IGNORE_OLD,
    classify_depth_event,
    validate_depth_event,
)


def event(**overrides):
    value = {
        "e": "depthUpdate",
        "E": 1_797_000_000_123,
        "s": "BTCUSDT",
        "U": 101,
        "u": 103,
        "b": [["100.0", "2.0"], ["99.0", "0"]],
        "a": [["101.0", "4.0"]],
    }
    value.update(overrides)
    return value


class BinanceDepthEventContractTests(unittest.TestCase):
    def test_valid_event_preserves_event_time_and_sequence_range(self):
        result = validate_depth_event(event())
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["event_time_ms"], 1_797_000_000_123)
        self.assertTrue(result["event_time_utc"].endswith("Z"))
        self.assertEqual((result["first_update_id"], result["final_update_id"]), (101, 103))

    def test_zero_quantity_is_allowed_for_level_deletion(self):
        self.assertEqual(validate_depth_event(event())["final_update_id"], 103)

    def test_empty_sides_are_allowed(self):
        self.assertEqual(validate_depth_event(event(b=[], a=[]))["symbol"], "BTCUSDT")

    def test_rejects_wrong_event_type(self):
        with self.assertRaisesRegex(ValueError, "event type"):
            validate_depth_event(event(e="trade"))

    def test_rejects_missing_or_malformed_event_timestamp(self):
        for value in (None, True, -1, "1797000000123", 1.5):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "E"):
                validate_depth_event(event(E=value))

    def test_rejects_invalid_sequence_range(self):
        with self.assertRaisesRegex(ValueError, "U must be"):
            validate_depth_event(event(U=104, u=103))

    def test_rejects_malformed_levels_and_negative_quantity(self):
        with self.assertRaisesRegex(ValueError, "price and quantity"):
            validate_depth_event(event(b=[["100"]]))
        with self.assertRaisesRegex(ValueError, "non-negative"):
            validate_depth_event(event(a=[["101", "-1"]]))

    def test_classifies_old_event_as_ignored(self):
        self.assertEqual(classify_depth_event(103, event(U=100, u=103))["state"], IGNORE_OLD)

    def test_classifies_overlapping_next_id_as_applicable(self):
        self.assertEqual(classify_depth_event(100, event(U=99, u=102))["state"], APPLY)

    def test_classifies_sequence_gap_as_resynchronization_required(self):
        result = classify_depth_event(103, event(U=105, u=106))
        self.assertEqual(result["state"], GAP)
        self.assertIn("re-synchronized", result["reason"])

    def test_requires_nonnegative_integer_local_update_id(self):
        with self.assertRaisesRegex(ValueError, "last_applied_update_id"):
            classify_depth_event(True, event())


if __name__ == "__main__":
    unittest.main()
