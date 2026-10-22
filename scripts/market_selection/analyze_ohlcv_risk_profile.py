"""Compute descriptive OHLCV risk metrics without ranking assets or filling missing candles."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

INPUT_SCHEMA = "binance-spot-ohlcv-capture-v1"
OUTPUT_SCHEMA = "ohlcv-descriptive-risk-profile-v1"
FIXED_INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}


def _decimal(value, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a decimal value") from exc
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    return number


def next_open_time(open_time_ms: int, interval: str) -> int:
    if interval in FIXED_INTERVAL_MS:
        return open_time_ms + FIXED_INTERVAL_MS[interval]
    if interval != "1M":
        raise ValueError(f"unsupported interval: {interval}")
    current = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
    if current.day != 1 or current.hour or current.minute or current.second or current.microsecond:
        raise ValueError("monthly candle open must be first day of UTC month")
    year, month = current.year, current.month + 1
    if month == 13:
        year, month = year + 1, 1
    return int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)


def _timestamp_ms(value, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer millisecond timestamp")
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be an integer millisecond timestamp") from exc
    if result < 0 or str(result) != str(value):
        raise ValueError(f"{field} must be a non-negative integer millisecond timestamp")
    return result


def analyze_artifact(artifact: dict, periods_per_year: int | None = None) -> dict:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    market = artifact.get("market")
    if not isinstance(market, dict) or market.get("market_type") != "SPOT":
        raise ValueError("market.market_type must be SPOT")
    symbol = market.get("symbol_native")
    interval = market.get("interval")
    if not isinstance(symbol, str) or not symbol or not isinstance(interval, str):
        raise ValueError("native symbol and interval are required")
    if periods_per_year is not None and (isinstance(periods_per_year, bool) or periods_per_year <= 0):
        raise ValueError("periods_per_year must be a positive integer when supplied")
    candles = artifact.get("candles")
    if not isinstance(candles, list):
        raise ValueError("candles must be a list")

    closed = []
    excluded_open = 0
    previous_seen = None
    for index, candle in enumerate(candles):
        if not isinstance(candle, dict):
            raise ValueError(f"candles[{index}] must be an object")
        opened = _timestamp_ms(candle.get("open_time_ms"), f"candles[{index}].open_time_ms")
        if previous_seen is not None and opened <= previous_seen:
            raise ValueError("candles must be strictly increasing by open_time_ms with no duplicates")
        previous_seen = opened
        close_time = _timestamp_ms(candle.get("close_time_ms"), f"candles[{index}].close_time_ms")
        if close_time < opened:
            raise ValueError("candle close time precedes open time")
        is_closed = candle.get("closed_at_capture") is True and candle.get("eligible_for_closed_candle_analysis") is True
        if not is_closed:
            excluded_open += 1
            continue
        close = _decimal(candle.get("close"), f"candles[{index}].close")
        if close <= 0:
            raise ValueError("closed candle close price must be positive")
        quote_volume = _decimal(candle.get("quote_volume"), f"candles[{index}].quote_volume")
        base_volume = _decimal(candle.get("base_volume"), f"candles[{index}].base_volume")
        if quote_volume < 0 or base_volume < 0:
            raise ValueError("candle volumes must be non-negative")
        closed.append({
            "open_time_ms": opened, "close_time_ms": close_time, "close": close,
            "quote_volume": quote_volume, "base_volume": base_volume,
        })

    gaps = []
    returns = []
    simple_returns = []
    skipped_gap_returns = 0
    for previous, current in zip(closed, closed[1:]):
        expected = next_open_time(previous["open_time_ms"], interval)
        if current["open_time_ms"] != expected:
            gaps.append({
                "previous_open_time_ms": previous["open_time_ms"],
                "expected_next_open_time_ms": expected,
                "observed_next_open_time_ms": current["open_time_ms"],
                "missing_interval_count": None,
                "status": "GAP",
            })
            skipped_gap_returns += 1
            continue
        simple = (current["close"] / previous["close"]) - Decimal(1)
        log_return = math.log(float(current["close"] / previous["close"]))
        simple_returns.append(float(simple))
        returns.append(log_return)

    if len(closed) >= 2:
        first_close = closed[0]["close"]
        last_close = closed[-1]["close"]
        period_return_pct = float((last_close / first_close - Decimal(1)) * Decimal(100))
        running_peak = closed[0]["close"]
        max_drawdown = Decimal(0)
        for candle in closed:
            running_peak = max(running_peak, candle["close"])
            drawdown = candle["close"] / running_peak - Decimal(1)
            max_drawdown = min(max_drawdown, drawdown)
        max_drawdown_pct = float(max_drawdown * Decimal(100))
    else:
        period_return_pct = None
        max_drawdown_pct = None

    log_std = statistics.stdev(returns) if len(returns) >= 2 else None
    simple_std = statistics.stdev(simple_returns) if len(simple_returns) >= 2 else None
    annualized_log_vol = log_std * math.sqrt(periods_per_year) if log_std is not None and periods_per_year else None
    data_quality = "INSUFFICIENT" if len(closed) < 2 else ("INCOMPLETE" if gaps or excluded_open else "COMPLETE")
    quote_volumes = [float(c["quote_volume"]) for c in closed]
    base_volumes = [float(c["base_volume"]) for c in closed]
    losses = [r for r in simple_returns if r < 0]
    gains = [r for r in simple_returns if r > 0]

    return {
        "schema_version": OUTPUT_SCHEMA,
        "analysis_status": "DESCRIPTIVE_ONLY",
        "data_quality_status": data_quality,
        "market": {"exchange": market.get("exchange"), "market_type": "SPOT", "symbol_native": symbol, "interval": interval},
        "source_artifact": {
            "schema_version": artifact.get("schema_version"),
            "overall_status": artifact.get("overall_status"),
            "source": artifact.get("source"),
            "window": artifact.get("window"),
        },
        "sample": {
            "input_candle_count": len(candles),
            "closed_candle_count": len(closed),
            "excluded_open_or_unconfirmed_count": excluded_open,
            "consecutive_interval_return_count": len(returns),
            "returns_skipped_across_gaps": skipped_gap_returns,
            "gap_count": len(gaps),
            "first_open_time_ms": closed[0]["open_time_ms"] if closed else None,
            "last_open_time_ms": closed[-1]["open_time_ms"] if closed else None,
        },
        "metrics": {
            "observed_period_return_pct": period_return_pct,
            "maximum_observed_close_to_close_drawdown_pct": max_drawdown_pct,
            "sample_standard_deviation_log_return_per_bar": log_std,
            "sample_standard_deviation_simple_return_per_bar": simple_std,
            "annualized_log_volatility": annualized_log_vol,
            "annualization_periods_per_year": periods_per_year,
            "mean_quote_volume_per_closed_candle": statistics.mean(quote_volumes) if quote_volumes else None,
            "mean_base_volume_per_closed_candle": statistics.mean(base_volumes) if base_volumes else None,
            "largest_observed_single_bar_loss_pct": min(losses) * 100 if losses else None,
            "largest_observed_single_bar_gain_pct": max(gains) * 100 if gains else None,
            "positive_consecutive_bar_fraction": sum(1 for r in simple_returns if r > 0) / len(simple_returns) if simple_returns else None,
            "negative_consecutive_bar_fraction": sum(1 for r in simple_returns if r < 0) / len(simple_returns) if simple_returns else None,
        },
        "gaps": gaps,
        "limitations": [
            "Metrics are descriptive for the captured closed-candle sample; they are not a forecast or investment recommendation.",
            "Volatility is per-bar unless periods_per_year is explicitly supplied; no hidden annualization convention is assumed.",
            "Returns across missing intervals are skipped rather than treated as single-bar returns.",
            "Maximum drawdown is computed from observed candle closes, not intrabar highs/lows; gaps can hide unobserved paths and drawdowns.",
            "Quote/base volumes retain their source fields and units; they are not interchangeable.",
            "No token-holder concentration, unlock schedule, order-book history, fee-adjusted execution cost, or fundamental risk is inferred from OHLCV alone.",
            "No ranking, pass/fail eligibility, numeric risk threshold, or trade order is produced.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, help="normalized binance-spot-ohlcv-capture-v1 JSON")
    parser.add_argument("--output", default="artifacts/ohlcv-descriptive-risk-profile.json")
    parser.add_argument("--periods-per-year", type=int, default=None,
                        help="optional explicit annualization factor; omitted means per-bar volatility only")
    args = parser.parse_args()
    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    result = analyze_artifact(artifact, args.periods_per_year)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "analysis_status": result["analysis_status"],
        "data_quality_status": result["data_quality_status"],
        "market": result["market"],
        "closed_candle_count": result["sample"]["closed_candle_count"],
        "gap_count": result["sample"]["gap_count"],
        "ranking_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
