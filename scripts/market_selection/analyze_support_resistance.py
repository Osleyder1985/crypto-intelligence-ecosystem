"""Detect causal pivot-based support/resistance zones from closed Spot candles."""
from __future__ import annotations

from scripts.market_selection.provider_license_gate import evaluate_artifact_use

import argparse
import json
import math
from decimal import Decimal
from pathlib import Path

from scripts.market_selection.analyze_ohlcv_risk_profile import next_open_time, verify_page_integrity

INPUT_SCHEMA = "binance-spot-ohlcv-capture-v1"
OUTPUT_SCHEMA = "ohlcv-support-resistance-events-v1"


def _positive_decimal(value, field):
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field} must be decimal") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return number


def _candle(row, index, interval):
    opened = int(row["open_time_ms"])
    closed = int(row["close_time_ms"])
    if opened < 0 or closed < opened:
        raise ValueError(f"candles[{index}] has invalid timestamps")
    expected_close = next_open_time(opened, interval) - 1
    if closed != expected_close:
        raise ValueError(f"candles[{index}] close time does not match interval boundary")
    op = _positive_decimal(row.get("open"), f"candles[{index}].open")
    hi = _positive_decimal(row.get("high"), f"candles[{index}].high")
    lo = _positive_decimal(row.get("low"), f"candles[{index}].low")
    cl = _positive_decimal(row.get("close"), f"candles[{index}].close")
    if hi < max(op, cl, lo) or lo > min(op, cl, hi):
        raise ValueError(f"candles[{index}] has invalid OHLC envelope")
    return {
        "open_time_ms": opened, "close_time_ms": closed,
        "open": op, "high": hi, "low": lo, "close": cl,
    }


def analyze_support_resistance(artifact: dict, pivot_left: int, pivot_right: int, tolerance_bps: float) -> dict:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    provider_use = evaluate_artifact_use(artifact, "internal_analysis")
    if provider_use["decision"] != "ALLOW":
        raise PermissionError("support/resistance analysis blocked before use: " + ",".join(provider_use["reason_codes"]))
    source_integrity_status = verify_page_integrity(artifact)
    market = artifact.get("market")
    if not isinstance(market, dict) or market.get("market_type") != "SPOT":
        raise ValueError("market.market_type must be SPOT")
    if isinstance(pivot_left, bool) or not isinstance(pivot_left, int) or pivot_left < 1:
        raise ValueError("pivot_left must be an integer >= 1")
    if isinstance(pivot_right, bool) or not isinstance(pivot_right, int) or pivot_right < 1:
        raise ValueError("pivot_right must be an integer >= 1")
    if isinstance(tolerance_bps, bool) or not isinstance(tolerance_bps, (int, float)) or not math.isfinite(tolerance_bps) or tolerance_bps < 0:
        raise ValueError("tolerance_bps must be finite and non-negative")
    interval = market.get("interval")
    if not isinstance(interval, str) or not interval:
        raise ValueError("market.interval is required")
    rows = artifact.get("candles")
    if not isinstance(rows, list):
        raise ValueError("candles must be a list")

    closed = []
    excluded_open = 0
    last_open = None
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"candles[{index}] must be an object")
        opened = int(row.get("open_time_ms"))
        if last_open is not None and opened <= last_open:
            raise ValueError("candles must be strictly increasing by open_time_ms with no duplicates")
        last_open = opened
        if row.get("closed_at_capture") is not True or row.get("eligible_for_closed_candle_analysis") is not True:
            excluded_open += 1
            continue
        closed.append(_candle(row, index, interval))

    segments = []
    current = []
    gaps = []
    for candle in closed:
        if current and candle["open_time_ms"] != next_open_time(current[-1]["open_time_ms"], interval):
            gaps.append({
                "previous_open_time_ms": current[-1]["open_time_ms"],
                "expected_next_open_time_ms": next_open_time(current[-1]["open_time_ms"], interval),
                "observed_next_open_time_ms": candle["open_time_ms"],
            })
            segments.append(current)
            current = []
        current.append(candle)
    if current:
        segments.append(current)

    candidates_by_confirmation = {}
    for segment_index, segment in enumerate(segments):
        for pivot_index in range(pivot_left, len(segment) - pivot_right):
            left = pivot_index - pivot_left
            right = pivot_index + pivot_right
            window = segment[left:right + 1]
            pivot = segment[pivot_index]
            confirm = segment[right]
            low_values = [item["low"] for item in window]
            high_values = [item["high"] for item in window]
            if low_values.count(pivot["low"]) == 1 and pivot["low"] == min(low_values):
                candidates_by_confirmation.setdefault(confirm["open_time_ms"], []).append({
                    "kind": "support", "price": pivot["low"], "pivot_open_time_ms": pivot["open_time_ms"],
                    "confirmation_open_time_ms": confirm["open_time_ms"], "confirmation_close_time_ms": confirm["close_time_ms"],
                    "segment_index": segment_index,
                })
            if high_values.count(pivot["high"]) == 1 and pivot["high"] == max(high_values):
                candidates_by_confirmation.setdefault(confirm["open_time_ms"], []).append({
                    "kind": "resistance", "price": pivot["high"], "pivot_open_time_ms": pivot["open_time_ms"],
                    "confirmation_open_time_ms": confirm["open_time_ms"], "confirmation_close_time_ms": confirm["close_time_ms"],
                    "segment_index": segment_index,
                })

    zones = []
    events = []
    next_zone_number = {"support": 1, "resistance": 1}
    for segment_index, segment in enumerate(segments):
        for candle in segment:
            # Update previously available zones using only this closed candle.
            for zone in zones:
                if zone["segment_index"] != segment_index or zone["invalidated_at_ms"] is not None:
                    continue
                if candle["open_time_ms"] < zone["available_from_ms"]:
                    continue
                low, high, close = candle["low"], candle["high"], candle["close"]
                intersects = low <= zone["upper_bound_price"] and high >= zone["lower_bound_price"]
                was_intersecting = zone["currently_intersecting"]
                if not intersects:
                    zone["currently_intersecting"] = False
                    zone["rejection_recorded_for_episode"] = False
                else:
                    zone["currently_intersecting"] = True
                    if not was_intersecting:
                        zone["touch_count"] += 1
                        zone["last_touch_at_ms"] = candle["close_time_ms"]
                        events.append({
                            "event_type": "zone_touch", "zone_id": zone["zone_id"],
                            "event_time_ms": candle["close_time_ms"], "source_candle_open_time_ms": candle["open_time_ms"],
                        })
                    rejection = (
                        zone["kind"] == "support" and close > zone["upper_bound_price"]
                    ) or (
                        zone["kind"] == "resistance" and close < zone["lower_bound_price"]
                    )
                    if rejection and not zone["rejection_recorded_for_episode"]:
                        zone["rejection_count"] += 1
                        zone["rejection_recorded_for_episode"] = True
                        events.append({
                            "event_type": "support_rejection" if zone["kind"] == "support" else "resistance_rejection",
                            "zone_id": zone["zone_id"], "event_time_ms": candle["close_time_ms"],
                            "source_candle_open_time_ms": candle["open_time_ms"],
                        })
                invalidated = (
                    zone["kind"] == "support" and close < zone["lower_bound_price"]
                ) or (
                    zone["kind"] == "resistance" and close > zone["upper_bound_price"]
                )
                if invalidated:
                    zone["invalidated_at_ms"] = candle["close_time_ms"]
                    events.append({
                        "event_type": "zone_invalidated", "zone_id": zone["zone_id"],
                        "event_time_ms": candle["close_time_ms"], "source_candle_open_time_ms": candle["open_time_ms"],
                    })

            for candidate in candidates_by_confirmation.get(candle["open_time_ms"], []):
                if candidate["segment_index"] != segment_index:
                    continue
                kind = candidate["kind"]
                price = candidate["price"]
                tolerance = Decimal(str(tolerance_bps)) / Decimal(10_000)
                lower = price * (Decimal(1) - tolerance)
                upper = price * (Decimal(1) + tolerance)
                event_time = candidate["confirmation_close_time_ms"]
                available_from = event_time + 1
                events.append({
                    "event_type": "pivot_confirmed", "zone_id": None, "kind": kind,
                    "pivot_open_time_ms": candidate["pivot_open_time_ms"],
                    "event_time_ms": event_time, "available_from_ms": available_from,
                    "pivot_price": str(price),
                })
                matching = [
                    zone for zone in zones
                    if zone["kind"] == kind and zone["segment_index"] == segment_index
                    and zone["invalidated_at_ms"] is None
                    and abs(price - zone["center_price"]) / zone["center_price"] * Decimal(10_000) <= Decimal(str(tolerance_bps))
                ]
                if matching:
                    zone = min(matching, key=lambda item: (abs(price - item["center_price"]), item["zone_id"]))
                    zone["pivot_count"] += 1
                    events.append({
                        "event_type": "zone_reinforced", "zone_id": zone["zone_id"],
                        "event_time_ms": event_time, "pivot_open_time_ms": candidate["pivot_open_time_ms"],
                        "pivot_price": str(price),
                    })
                else:
                    zone_id = f"{kind}-{next_zone_number[kind]}"
                    next_zone_number[kind] += 1
                    zone = {
                        "zone_id": zone_id, "kind": kind, "segment_index": segment_index,
                        "center_price": price, "lower_bound_price": lower, "upper_bound_price": upper,
                        "created_at_ms": event_time, "available_from_ms": available_from,
                        "pivot_count": 1, "touch_count": 0, "rejection_count": 0,
                        "last_touch_at_ms": None, "invalidated_at_ms": None,
                        "currently_intersecting": False, "rejection_recorded_for_episode": False,
                    }
                    zones.append(zone)
                    events.append({
                        "event_type": "zone_created", "zone_id": zone_id,
                        "event_time_ms": event_time, "available_from_ms": available_from,
                        "kind": kind, "pivot_open_time_ms": candidate["pivot_open_time_ms"],
                        "center_price": str(price), "lower_bound_price": str(lower), "upper_bound_price": str(upper),
                    })

    events.sort(key=lambda item: item["event_time_ms"])  # stable sort preserves within-close causal insertion order
    data_quality = "INCOMPLETE" if gaps or excluded_open or artifact.get("overall_status") != "PASS" or source_integrity_status != "VERIFIED" else (
        "INSUFFICIENT" if len(closed) < pivot_left + pivot_right + 1 else "COMPLETE"
    )
    return {
        "schema_version": OUTPUT_SCHEMA,
        "analysis_status": "DESCRIPTIVE_ONLY",
        "data_quality_status": data_quality,
        "source_integrity_status": source_integrity_status,
        "market": {"exchange": market.get("exchange"), "market_type": "SPOT", "symbol_native": market.get("symbol_native"), "interval": interval},
        "method": {
            "name": "confirmed local pivots with fixed-price zones",
            "pivot_left": pivot_left, "pivot_right": pivot_right, "tolerance_bps": float(tolerance_bps),
            "pivot_available_only_after_right_bars_close": True,
            "zone_bounds_are_fixed_at_creation": True,
        },
        "sample": {
            "input_candle_count": len(rows), "closed_candle_count": len(closed),
            "excluded_open_or_unconfirmed_count": excluded_open, "contiguous_segment_count": len(segments),
            "gap_count": len(gaps), "zone_count": len(zones), "event_count": len(events),
        },
        "gaps": gaps,
        "zones": [{
            **{key: value for key, value in zone.items() if key not in {"currently_intersecting", "rejection_recorded_for_episode"}},
            "center_price": str(zone["center_price"]),
            "lower_bound_price": str(zone["lower_bound_price"]),
            "upper_bound_price": str(zone["upper_bound_price"]),
            "strength_evidence": {
                "confirmed_pivot_count": zone["pivot_count"],
                "touch_count_after_availability": zone["touch_count"],
                "rejection_count_after_availability": zone["rejection_count"],
            },
        } for zone in zones],
        "events": events,
        "limitations": [
            "A pivot is emitted only after pivot_right subsequent candles have closed; its event time is the confirmation candle close.",
            "Use the event stream and available_from_ms for historical replay; final zone summaries include evidence from the entire input sample.",
            "Fixed zone bounds avoid retroactive changes to past zones; a later nearby pivot reinforces an existing active zone without moving its center.",
            "Gaps split the sample into segments; no pivot window crosses a gap and zones are not evaluated across segments.",
            "Zone touches/rejections are heuristic descriptions of OHLC ranges, not proof of resting liquidity, participant intent, or future price response.",
            "No score, threshold, ranking, investment recommendation, or trade order is produced.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--pivot-left", type=int, required=True)
    parser.add_argument("--pivot-right", type=int, required=True)
    parser.add_argument("--tolerance-bps", type=float, required=True)
    parser.add_argument("--output", default="artifacts/ohlcv-support-resistance-events.json")
    args = parser.parse_args()
    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    result = analyze_support_resistance(artifact, args.pivot_left, args.pivot_right, args.tolerance_bps)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(path), "analysis_status": result["analysis_status"],
        "data_quality_status": result["data_quality_status"], "market": result["market"],
        "zone_count": result["sample"]["zone_count"], "event_count": result["sample"]["event_count"],
        "ranking_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
