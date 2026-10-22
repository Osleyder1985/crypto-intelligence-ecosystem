"""Detect descriptive price/turnover events using only closed candles and prior-window baselines."""
from __future__ import annotations

try:
    from scripts.market_selection.provider_license_gate import evaluate_artifact_use
except ModuleNotFoundError:
    from provider_license_gate import evaluate_artifact_use

import argparse
import base64
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

INPUT_SCHEMA = "binance-spot-ohlcv-capture-v1"
OUTPUT_SCHEMA = "ohlcv-movement-events-v1"
INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}


def verify_pages(artifact):
    pages = artifact.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("source artifact must contain a non-empty pages list")
    statuses = []
    for i, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(f"pages[{i}] must be an object")
        encoded = page.get("response_base64")
        if encoded is None:
            if page.get("capture_status") == "PASS":
                raise ValueError(f"pages[{i}] successful capture has no preserved body")
            statuses.append("UNAVAILABLE")
            continue
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"pages[{i}] has invalid Base64 body") from exc
        if page.get("response_bytes") is not None and len(raw) != page["response_bytes"]:
            raise ValueError(f"pages[{i}] response size mismatch")
        digest = page.get("response_sha256")
        if digest is not None and hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"pages[{i}] SHA-256 mismatch")
        statuses.append("VERIFIED" if digest is not None and page.get("response_bytes") is not None else "PARTIAL_METADATA")
    return "VERIFIED" if all(s == "VERIFIED" for s in statuses) else ("PARTIAL" if "VERIFIED" in statuses else "UNVERIFIED")


def dec(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def next_open(open_ms, interval):
    if interval in INTERVAL_MS:
        return open_ms + INTERVAL_MS[interval]
    if interval != "1M":
        raise ValueError(f"unsupported interval: {interval}")
    current = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc)
    if current.day != 1 or current.hour or current.minute or current.second or current.microsecond:
        raise ValueError("monthly candle must open at UTC month boundary")
    year, month = current.year, current.month + 1
    if month == 13:
        year, month = year + 1, 1
    return int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)


def analyze_movement_events(artifact, lookback_bars, return_threshold_pct, volume_ratio_threshold):
    if not isinstance(artifact, dict) or artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    provider_use = evaluate_artifact_use(artifact, "internal_analysis")
    if provider_use["decision"] != "ALLOW":
        raise PermissionError("OHLCV movement analysis blocked before use: " + ",".join(provider_use["reason_codes"]))
    integrity = verify_pages(artifact)
    market = artifact.get("market")
    if not isinstance(market, dict) or market.get("market_type") != "SPOT":
        raise ValueError("market.market_type must be SPOT")
    interval = market.get("interval")
    if not isinstance(interval, str) or not interval:
        raise ValueError("market.interval is required")
    if isinstance(lookback_bars, bool) or not isinstance(lookback_bars, int) or lookback_bars < 2:
        raise ValueError("lookback_bars must be an integer >= 2")
    if isinstance(return_threshold_pct, bool) or not math.isfinite(return_threshold_pct) or return_threshold_pct <= 0:
        raise ValueError("return_threshold_pct must be finite and positive")
    if isinstance(volume_ratio_threshold, bool) or not math.isfinite(volume_ratio_threshold) or volume_ratio_threshold <= 1:
        raise ValueError("volume_ratio_threshold must be finite and greater than 1")
    rows = artifact.get("candles")
    if not isinstance(rows, list):
        raise ValueError("candles must be a list")

    closed = []
    excluded = 0
    previous_open = None
    force_new_segment = False
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"candles[{i}] must be an object")
        open_ms = int(row.get("open_time_ms"))
        if previous_open is not None and open_ms <= previous_open:
            raise ValueError("candles must be strictly increasing by open_time_ms with no duplicates")
        previous_open = open_ms
        if row.get("closed_at_capture") is not True or row.get("eligible_for_closed_candle_analysis") is not True:
            excluded += 1
            force_new_segment = True
            continue
        close_ms = int(row.get("close_time_ms"))
        if close_ms != next_open(open_ms, interval) - 1:
            raise ValueError(f"candles[{i}] close time does not match interval boundary")
        op = dec(row.get("open"), f"candles[{i}].open")
        high = dec(row.get("high"), f"candles[{i}].high")
        low = dec(row.get("low"), f"candles[{i}].low")
        close = dec(row.get("close"), f"candles[{i}].close")
        quote_volume = dec(row.get("quote_volume"), f"candles[{i}].quote_volume")
        if min(op, high, low, close) <= 0 or high < max(op, close, low) or low > min(op, close, high):
            raise ValueError("candle OHLC envelope must be positive and internally consistent")
        if quote_volume < 0:
            raise ValueError("quote volume must be non-negative")
        gap_before = force_new_segment or (closed and open_ms != next_open(closed[-1]["open_time_ms"], interval))
        closed.append({
            "open_time_ms": open_ms, "close_time_ms": close_ms,
            "close": close, "quote_volume": quote_volume,
            "segment_break_before": bool(gap_before),
        })
        force_new_segment = False

    segments = []
    current = []
    for row in closed:
        if row["segment_break_before"] and current:
            segments.append(current)
            current = []
        current.append(row)
    if current:
        segments.append(current)

    events = []
    gap_count = sum(1 for row in closed if row["segment_break_before"])
    for segment_index, segment in enumerate(segments):
        for i in range(1, len(segment)):
            current = segment[i]
            previous = segment[i - 1]
            if current["open_time_ms"] != next_open(previous["open_time_ms"], interval):
                continue
            simple_return = (current["close"] / previous["close"] - Decimal(1)) * Decimal(100)
            price_move = abs(float(simple_return)) >= return_threshold_pct
            baseline = [float(row["quote_volume"]) for row in segment[max(0, i - lookback_bars):i]]
            volume_ratio = None
            volume_spike = False
            volume_status = "INSUFFICIENT_BASELINE" if len(baseline) < lookback_bars else "VALID"
            if len(baseline) == lookback_bars:
                median_volume = statistics.median(baseline)
                if median_volume <= 0:
                    volume_status = "INDETERMINATE_ZERO_BASELINE"
                else:
                    volume_ratio = float(current["quote_volume"]) / median_volume
                    volume_spike = volume_ratio >= volume_ratio_threshold
            if not price_move and not volume_spike:
                continue
            if price_move and volume_spike:
                event_type = "PRICE_MOVE_AND_VOLUME_SPIKE"
            elif price_move:
                event_type = "PRICE_MOVE"
            else:
                event_type = "VOLUME_SPIKE"
            events.append({
                "event_type": event_type,
                "event_time_ms": current["close_time_ms"],
                "available_from_ms": current["close_time_ms"] + 1,
                "source_candle_open_time_ms": current["open_time_ms"],
                "segment_index": segment_index,
                "direction": "UP" if simple_return > 0 else ("DOWN" if simple_return < 0 else "FLAT"),
                "simple_return_pct": float(simple_return),
                "price_move_threshold_pct": return_threshold_pct,
                "price_move_threshold_met": price_move,
                "quote_volume": str(current["quote_volume"]),
                "prior_window_quote_volume_median": statistics.median(baseline) if len(baseline) == lookback_bars else None,
                "quote_volume_ratio_to_prior_median": volume_ratio,
                "volume_ratio_threshold": volume_ratio_threshold,
                "volume_spike_threshold_met": volume_spike,
                "volume_baseline_status": volume_status,
                "lookback_bars": lookback_bars,
                "lookahead_bars": 0,
                "causal_attribution": "NOT_ESTABLISHED",
            })

    if len(closed) < 2:
        quality = "INSUFFICIENT"
    elif excluded or gap_count or artifact.get("overall_status") != "PASS" or integrity != "VERIFIED":
        quality = "INCOMPLETE"
    else:
        quality = "COMPLETE"
    return {
        "schema_version": OUTPUT_SCHEMA,
        "analysis_status": "DESCRIPTIVE_ONLY",
        "data_quality_status": quality,
        "source_integrity_status": integrity,
        "market": {"exchange": market.get("exchange"), "market_type": "SPOT", "symbol_native": market.get("symbol_native"), "interval": interval},
        "method": {
            "lookback_bars": lookback_bars,
            "return_threshold_pct": return_threshold_pct,
            "volume_ratio_threshold": volume_ratio_threshold,
            "baseline_uses_only_prior_closed_bars": True,
            "lookahead_bars": 0,
        },
        "sample": {
            "input_candle_count": len(rows), "closed_candle_count": len(closed),
            "excluded_open_or_unconfirmed_count": excluded, "contiguous_segment_count": len(segments),
            "gap_or_segment_break_count": gap_count, "event_count": len(events),
        },
        "events": events,
        "limitations": [
            "Events describe price/turnover conditions only; no news or causal attribution is inferred.",
            "Thresholds are explicit parameters, not universal or approved investment thresholds.",
            "Volume baseline uses only prior closed candles in the same contiguous segment.",
            "No return or volume baseline crosses a gap or an excluded open candle.",
            "No ranking, forecast, eligibility decision, probability, or order is produced.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--lookback-bars", type=int, required=True)
    parser.add_argument("--return-threshold-pct", type=float, required=True)
    parser.add_argument("--volume-ratio-threshold", type=float, required=True)
    parser.add_argument("--output", default="artifacts/ohlcv-movement-events.json")
    args = parser.parse_args()
    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    result = analyze_movement_events(artifact, args.lookback_bars, args.return_threshold_pct, args.volume_ratio_threshold)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(path), "analysis_status": result["analysis_status"],
        "data_quality_status": result["data_quality_status"], "market": result["market"],
        "event_count": result["sample"]["event_count"], "ranking_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
