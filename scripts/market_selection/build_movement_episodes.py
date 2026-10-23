"""Build descriptive directional swing episodes from confirmed support/resistance pivots.

Episodes are technical swing windows, not claims that a catalyst caused the move.
Only confirmed pivot events are consumed; pivot time and confirmation availability
are kept separate to prevent look-ahead in historical replay.
"""
from __future__ import annotations

OUTPUT_SCHEMA = "ohlcv-movement-episodes-v1"


def build_movement_episodes(support_resistance: dict) -> dict:
    if not isinstance(support_resistance, dict):
        raise ValueError("support_resistance must be an object")
    if support_resistance.get("schema_version") != "ohlcv-support-resistance-events-v1":
        raise ValueError("support_resistance schema_version is unsupported")
    events = support_resistance.get("events")
    if not isinstance(events, list):
        raise ValueError("support_resistance.events must be a list")

    pivots = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"support_resistance.events[{index}] must be an object")
        if event.get("event_type") != "pivot_confirmed":
            continue
        kind = event.get("kind")
        if kind not in {"support", "resistance"}:
            raise ValueError(f"pivot event {index} has invalid kind")
        try:
            segment = int(event.get("segment_index"))
            pivot_time = int(event.get("pivot_open_time_ms"))
            confirmed_at = int(event.get("event_time_ms"))
            available_from = int(event.get("available_from_ms"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"pivot event {index} is missing valid segment/timestamps") from exc
        if segment < 0 or pivot_time < 0 or confirmed_at < pivot_time or available_from <= confirmed_at:
            raise ValueError(f"pivot event {index} has inconsistent timestamps")
        price = event.get("pivot_price")
        try:
            price_number = float(price)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"pivot event {index} has invalid pivot_price") from exc
        if not (price_number > 0 and price_number < float("inf")):
            raise ValueError(f"pivot event {index} has invalid pivot_price")
        pivots.append({
            "kind": kind, "segment_index": segment, "pivot_open_time_ms": pivot_time,
            "confirmed_at_ms": confirmed_at, "available_from_ms": available_from,
            "price": str(price), "_price_number": price_number,
        })

    pivots.sort(key=lambda item: (item["segment_index"], item["pivot_open_time_ms"], item["confirmed_at_ms"], item["kind"]))
    episodes = []
    previous_by_segment = {}
    for pivot in pivots:
        previous = previous_by_segment.get(pivot["segment_index"])
        previous_by_segment[pivot["segment_index"]] = pivot
        if previous is None or previous["kind"] == pivot["kind"]:
            continue
        start, end = previous, pivot
        direction = "BULLISH" if start["kind"] == "support" and end["kind"] == "resistance" else "BEARISH"
        change_pct = ((end["_price_number"] - start["_price_number"]) / start["_price_number"]) * 100
        episodes.append({
            "episode_id": f"swing-{len(episodes) + 1}",
            "direction": direction,
            "classification": "TECHNICAL_SWING_CANDIDATE",
            "segment_index": pivot["segment_index"],
            "start": {
                "pivot_kind": start["kind"], "pivot_open_time_ms": start["pivot_open_time_ms"],
                "confirmed_at_ms": start["confirmed_at_ms"], "available_from_ms": start["available_from_ms"],
                "pivot_price": start["price"],
            },
            "end": {
                "pivot_kind": end["kind"], "pivot_open_time_ms": end["pivot_open_time_ms"],
                "confirmed_at_ms": end["confirmed_at_ms"], "available_from_ms": end["available_from_ms"],
                "pivot_price": end["price"],
            },
            "price_change_pct_between_pivots": round(change_pct, 8),
            "duration_ms_between_pivots": end["pivot_open_time_ms"] - start["pivot_open_time_ms"],
            "episode_observable_only_at_ms": end["available_from_ms"],
            "causality_status": "NOT_ASSESSED",
        })
    return {
        "schema_version": OUTPUT_SCHEMA,
        "status": "DESCRIPTIVE_ONLY",
        "method": {
            "name": "adjacent alternating confirmed local pivots",
            "bullish_definition": "support pivot followed by resistance pivot in the same contiguous candle segment",
            "bearish_definition": "resistance pivot followed by support pivot in the same contiguous candle segment",
            "pivot_time_basis": "pivot candle open time",
            "confirmation_time_basis": "close of the rightmost confirming candle",
            "lookahead_policy": "episode is only observable after end pivot confirmation; pivot timestamps are not treated as real-time known before confirmation",
        },
        "sample": {"confirmed_pivot_count": len(pivots), "episode_count": len(episodes)},
        "episodes": episodes,
        "limitations": [
            "Episodes describe swings between confirmed local pivots and do not prove exact movement starts, ends, or causal catalysts.",
            "Only adjacent alternating pivots are paired; consecutive pivots of the same kind replace the prior candidate for pairing.",
            "Pivots across missing-candle segments are never joined.",
            "Price change is computed between pivot prices, not a return series or executable trade result.",
            "Causality remains NOT_ASSESSED until authorized external evidence is validated and temporally associated.",
        ],
    }
