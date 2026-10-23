import unittest

from scripts.market_selection.build_movement_episodes import build_movement_episodes


def pivot(kind, segment, pivot_ms, confirmed_ms, price):
    return {
        "event_type": "pivot_confirmed", "kind": kind, "segment_index": segment,
        "pivot_open_time_ms": pivot_ms, "event_time_ms": confirmed_ms,
        "available_from_ms": confirmed_ms + 1, "pivot_price": str(price),
    }


def result(events):
    return {"schema_version": "ohlcv-support-resistance-events-v1", "events": events}


class MovementEpisodeTests(unittest.TestCase):
    def test_builds_bullish_and_bearish_episodes_with_confirmation_times(self):
        output = build_movement_episodes(result([
            pivot("support", 0, 100, 130, 10),
            pivot("resistance", 0, 200, 230, 12),
            pivot("support", 0, 300, 330, 9),
        ]))
        self.assertEqual([item["direction"] for item in output["episodes"]], ["BULLISH", "BEARISH"])
        self.assertEqual(output["episodes"][0]["price_change_pct_between_pivots"], 20.0)
        self.assertEqual(output["episodes"][0]["start"]["confirmed_at_ms"], 130)
        self.assertEqual(output["episodes"][0]["episode_observable_only_at_ms"], 231)
        self.assertEqual(output["episodes"][1]["price_change_pct_between_pivots"], -25.0)
        self.assertTrue(all(item["causality_status"] == "NOT_ASSESSED" for item in output["episodes"]))

    def test_never_pairs_pivots_across_gap_segments(self):
        output = build_movement_episodes(result([
            pivot("support", 0, 100, 130, 10),
            pivot("resistance", 1, 200, 230, 12),
        ]))
        self.assertEqual(output["episodes"], [])

    def test_same_kind_pivot_replaces_prior_pairing_candidate(self):
        output = build_movement_episodes(result([
            pivot("support", 0, 100, 130, 10),
            pivot("support", 0, 150, 180, 9),
            pivot("resistance", 0, 200, 230, 12),
        ]))
        self.assertEqual(len(output["episodes"]), 1)
        self.assertEqual(output["episodes"][0]["start"]["pivot_open_time_ms"], 150)

    def test_rejects_missing_segment_or_bad_time(self):
        event = pivot("support", 0, 100, 130, 10)
        del event["segment_index"]
        with self.assertRaisesRegex(ValueError, "missing valid segment"):
            build_movement_episodes(result([event]))

    def test_rejects_unsupported_schema(self):
        with self.assertRaisesRegex(ValueError, "schema_version"):
            build_movement_episodes({"schema_version": "wrong", "events": []})


if __name__ == "__main__":
    unittest.main()
