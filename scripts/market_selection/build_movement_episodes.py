"""Reconstruct descriptive bullish/bearish swing episodes from confirmed pivots.

Episodes are technical swing windows, not claims about causal news or future returns.
Only pivots confirmed by the support/resistance analyzer are accepted.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

INPUT_SCHEMA = "ohlcv-support-resistance-events-v1"
OUTPUT_SCHEMA = "ohlcv-movement-episodes-v1"


def _timestamp(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer timestamp")
    return value


def _price(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a decimal price") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return result


def build_movement_episodes(support_resistance: dict) -> dict:
    if not isinstance(support_resistance, dict) or support_resistance.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    events = support_resistance.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    pivots = []
    for index, event in enumerate(events):
        if not isinstance(event, dict) or event.get("event_type") != "pivot_confirmed":
            continue
        kind = event.get("kind")
        if kind not in {"support", "resistance"}:
            raise ValueError(f"events[{index}].kind must be support or resistance")
        segment = event.get("segment_index")
        if isinstance(segment, bool) or not isinstance(segment, int) or segment < 0:
            raise ValueError(f"events[{index}].segment_index must be a non-negative integer")
        pivot_time = _timestamp(event.get("pivot_open_time_ms"), f"events[{index}].pivot_open_time_ms")
        confirmed_at = _timestamp(event.get("event_time_ms"), f"events[{index}].event_time_ms")
        available_from = _timestamp(event.get("available_from_ms"), f"events[{index}].available_from_ms")
        if available_from <= confirmed_at:
            raise ValueError(f"events[{index}].available_from_ms must follow confirmation")
        price = _price(event.get("pivot_price"), f"events[{index}].pivot_price")
        pivots.append({
            "kind": kind, "segment_index": segment, "pivot_open_time_ms": pivot_time,
            "confirmed_at_ms": confirmed_at, "available_from_ms": available_from, "price": price,
        })

    # Segment then pivot time makes chronology explicit; confirmation time is preserved separately.
    pivots.sort(key=lambda p: (p["segment_index"], p["pivot_open_time_ms"], p["confirmed_at_ms"], p["kind"]))
    episodes = []
    for segment_index in sorted({p["segment_index"] for p in pivots}):
        segment_pivots = [p for p in pivots if p["segment_index"] == segment_index]
        swings = []
        for pivot in segment_pivots:
            if not swings or swings[-1]["kind"] != pivot["kind"]:
                swings.append(pivot)
                continue
            # Collapse consecutive same-type extrema to the more extreme confirmed pivot.
            previous = swings[-1]
            more_extreme = (pivot["price"] < previous["price"] if pivot["kind"] == "support"
                            else pivot["price"] > previous["price"])
            if more_extreme:
                swings[-1] = pivot

        for start, end in zip(swings, swings[1:]):
            if start["kind"] == end["kind"]:
                continue
            direction = "bullish" if start["kind"] == "support" and end["kind"] == "resistance" else "bearish"
            change_pct = (end["price"] - start["price"]) / start["price"] * Decimal(100)
            episodes.append({
                "episode_id": f"segment-{segment_index}-episode-{len(episodes) + 1}",
                "direction": direction,
                "status": "COMPLETED_SWING",
                "segment_index": segment_index,
                "start_pivot_kind": start["kind"],
                "end_pivot_kind": end["kind"],
                "start_price": str(start["price"]),
                "end_price": str(end["price"]),
                "price_change_pct": str(change_pct.quantize(Decimal("0.000001"))),
                "start_pivot_open_time_ms": start["pivot_open_time_ms"],
                "end_pivot_open_time_ms": end["pivot_open_time_ms"],
                "start_confirmed_at_ms": start["confirmed_at_ms"],
                "end_confirmed_at_ms": end["confirmed_at_ms"],
                "start_available_from_ms": start["available_from_ms"],
                "end_available_from_ms": end["available_from_ms"],
                "measurement_note": "Pivot timestamps estimate swing turning points; the pivots become knowable only at their confirmation timestamps.",
                "causality_status": "NOT_ASSESSED",
            })
    episodes.sort(key=lambda episode: (
        episode["start_pivot_open_time_ms"], episode["segment_index"], episode["end_pivot_open_time_ms"]
    ))
    for index, episode in enumerate(episodes, start=1):
        episode["episode_id"] = f"movement-{index}"
    return {
        "schema_version": OUTPUT_SCHEMA,
        "status": "DESCRIPTIVE_ONLY",
        "episode_count": len(episodes),
        "episodes": episodes,
        "method": {
            "name": "alternating confirmed local pivots",
            "bullish_definition": "confirmed support pivot followed by confirmed resistance pivot in the same contiguous segment",
            "bearish_definition": "confirmed resistance pivot followed by confirmed support pivot in the same contiguous segment",
            "same_type_pivots": "consecutive pivots of the same type collapse to the more extreme pivot",
            "lookahead_policy": "no episode endpoint is considered knowable before its endpoint pivot confirmation",
        },
        "limitations": [
            "Episodes describe technical swings, not necessarily the complete start or end of a market regime.",
            "Pivot timestamps are retrospective turning-point estimates; confirmation occurs later after right-side candles close.",
            "No news/event causality is inferred. Event association requires separate timestamped, identity-verified and authorized evidence.",
            "Only completed alternating-pivot swings are emitted; an unfinished terminal swing is not labelled a completed episode.",
            "Segments separated by candle gaps are never joined.",
        ],
    }
