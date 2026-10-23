import unittest

from scripts.market_selection.build_movement_episodes import build_movement_episodes


def pivot(kind, segment, opened, confirmed, price):
    return {
        "event_type": "pivot_confirmed", "kind": kind, "segment_index": segment,
        "pivot_open_time_ms": opened, "event_time_ms": confirmed,
        "available_from_ms": confirmed + 1, "pivot_price": str(price),
    }


def source(events):
    return {"schema_version": "ohlcv-support-resistance-events-v1", "events": events}


class MovementEpisodeTests(unittest.TestCase):
    def test_builds_bullish_and_bearish_swings_and_preserves_confirmation_times(self):
        result = build_movement_episodes(source([
            pivot("support", 0, 100, 130, 10),
            pivot("resistance", 0, 200, 230, 15),
            pivot("support", 0, 300, 330, 12),
        ]))
        self.assertEqual([item["direction"] for item in result["episodes"]], ["bullish", "bearish"])
        self.assertEqual(result["episodes"][0]["price_change_pct"], "50.000000")
        self.assertEqual(result["episodes"][1]["price_change_pct"], "-20.000000")
        self.assertEqual(result["episodes"][0]["start_confirmed_at_ms"], 130)
        self.assertEqual(result["episodes"][0]["end_confirmed_at_ms"], 230)
        self.assertEqual(result["episodes"][0]["causality_status"], "NOT_ASSESSED")

    def test_never_connects_pivots_across_segments(self):
        result = build_movement_episodes(source([
            pivot("support", 0, 100, 130, 10),
            pivot("resistance", 1, 200, 230, 15),
        ]))
        self.assertEqual(result["episode_count"], 0)

    def test_collapses_consecutive_same_type_to_more_extreme_pivot(self):
        result = build_movement_episodes(source([
            pivot("support", 0, 100, 130, 12),
            pivot("support", 0, 150, 180, 10),
            pivot("resistance", 0, 200, 230, 15),
        ]))
        episode = result["episodes"][0]
        self.assertEqual(episode["start_pivot_open_time_ms"], 150)
        self.assertEqual(episode["start_price"], "10")
        self.assertEqual(episode["price_change_pct"], "50.000000")

    def test_rejects_unconfirmed_or_malformed_pivot_provenance(self):
        bad = pivot("support", 0, 100, 130, 10)
        bad["available_from_ms"] = 130
        with self.assertRaisesRegex(ValueError, "must follow confirmation"):
            build_movement_episodes(source([bad]))

    def test_ignores_non_pivot_events(self):
        result = build_movement_episodes(source([
            {"event_type": "zone_touch", "event_time_ms": 120},
            pivot("support", 0, 100, 130, 10),
        ]))
        self.assertEqual(result["episode_count"], 0)


if __name__ == "__main__":
    unittest.main()
