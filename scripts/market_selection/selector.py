"""Read-only spot market selector prototype; no exchange/API integration."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

VALID_STATES = {"PASS", "FAIL", "INDETERMINATE", "NOT_APPLICABLE", "NOT_RUN"}
REQUIRED_CONFIG = (
    "max_spread_bps",
    "depth_band_bps",
    "min_depth_quote",
    "order_size_base",
    "max_slippage_bps",
    "critical_dimensions",
    "config_approval_status",
    "config_version",
    "config_approval_ref",
    "max_snapshot_age_seconds",
    "max_source_lag_seconds",
    "maker_fee_bps",
    "taker_fee_bps",
)
DIMENSIONS = ("market_type", "spread", "depth", "slippage", "availability", "freshness", "fees")


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive(value: Any) -> bool:
    return _number(value) and value > 0


def _levels(value: Any, side: str) -> list[tuple[float, float]]:
    """Validate levels represented as {price, quantity}; return price-sorted levels."""
    if not isinstance(value, list) or not value:
        raise ValueError(f"{side} order book must be a non-empty list")
    result: list[tuple[float, float]] = []
    for index, level in enumerate(value):
        if not isinstance(level, dict) or not _positive(level.get("price")) or not _positive(level.get("quantity")):
            raise ValueError(f"{side}[{index}] requires finite positive price and quantity")
        result.append((float(level["price"]), float(level["quantity"])))
    prices = [price for price, _ in result]
    if len(prices) != len(set(prices)):
        raise ValueError(f"{side} order book contains duplicate price levels")
    return sorted(result, key=lambda item: item[0], reverse=(side == "bids"))


def spread_bps(best_bid: float, best_ask: float) -> float:
    """Return quoted spread in basis points; reject invalid or crossed books."""
    if not _positive(best_bid) or not _positive(best_ask):
        raise ValueError("best bid and ask must be finite and positive")
    if best_bid > best_ask:
        raise ValueError("crossed order book: best bid exceeds best ask")
    mid = (best_bid + best_ask) / 2.0
    return (best_ask - best_bid) / mid * 10_000.0


def depth_quote(levels: list[dict[str, Any]], mid: float, band_bps: float, side: str) -> float:
    """Sum quote notional within a symmetric mid-price band."""
    if not _positive(mid) or not _number(band_bps) or band_bps < 0:
        raise ValueError("mid must be positive and band_bps must be finite and non-negative")
    parsed = _levels(levels, side)
    lower = mid * (1.0 - band_bps / 10_000.0)
    upper = mid * (1.0 + band_bps / 10_000.0)
    total = sum(price * quantity for price, quantity in parsed if lower <= price <= upper)
    if not math.isfinite(total):
        raise ValueError("computed depth is non-finite")
    return total


def estimate_slippage_bps(
    levels: list[dict[str, Any]], mid: float, order_size_base: float, side: str
) -> dict[str, float | None]:
    """Estimate snapshot VWAP slippage for a base-quantity order; never assume uncovered fills."""
    if not _positive(mid) or not _positive(order_size_base):
        raise ValueError("mid and order_size_base must be finite and positive")
    if side not in {"asks", "bids"}:
        raise ValueError("side must be 'asks' (buy) or 'bids' (sell)")
    parsed = _levels(levels, side)
    remaining = float(order_size_base)
    filled = 0.0
    notional = 0.0
    for price, quantity in parsed:
        take = min(remaining, quantity)
        filled += take
        notional += take * price
        remaining -= take
        if remaining <= 1e-12:
            break
    vwap = notional / filled if filled > 0 else None
    if remaining > 1e-12 or vwap is None:
        return {
            "requested_base": float(order_size_base),
            "filled_base": filled,
            "uncovered_base": max(remaining, 0.0),
            "vwap": vwap,
            "slippage_bps": None,
        }
    if side == "asks":
        slippage = (vwap / mid - 1.0) * 10_000.0
    else:
        slippage = (1.0 - vwap / mid) * 10_000.0
    return {
        "requested_base": float(order_size_base),
        "filled_base": filled,
        "uncovered_base": 0.0,
        "vwap": vwap,
        "slippage_bps": max(slippage, 0.0),
    }



def _timestamp(value: Any, field: str) -> datetime:
    """Parse an ISO-8601 timestamp and require an explicit timezone."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit timezone")
    return parsed


def evaluate_freshness(observation: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Check source-to-capture lag and capture age against explicit configured limits."""
    required = ("source_timestamp_utc", "captured_at_utc", "evaluation_time_utc")
    if any(not observation.get(key) for key in required):
        raise ValueError("source_timestamp_utc, captured_at_utc and evaluation_time_utc are required")
    max_age = config.get("max_snapshot_age_seconds")
    max_lag = config.get("max_source_lag_seconds")
    if not _number(max_age) or max_age < 0 or not _number(max_lag) or max_lag < 0:
        raise ValueError("freshness limits must be finite and non-negative")
    source = _timestamp(observation["source_timestamp_utc"], "source_timestamp_utc")
    captured = _timestamp(observation["captured_at_utc"], "captured_at_utc")
    evaluated = _timestamp(observation["evaluation_time_utc"], "evaluation_time_utc")
    source_lag = (captured - source).total_seconds()
    snapshot_age = (evaluated - captured).total_seconds()
    if source_lag < 0 or snapshot_age < 0:
        raise ValueError("timestamps are inconsistent or lie in the future")
    return {"source_lag_seconds": source_lag, "snapshot_age_seconds": snapshot_age,
            "status": "PASS" if source_lag <= max_lag and snapshot_age <= max_age else "FAIL"}

def evaluate_market(observation: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one synthetic/normalized snapshot. Missing thresholds never default silently."""
    if not isinstance(observation, dict) or not isinstance(config, dict):
        raise TypeError("observation and config must be dictionaries")

    missing_config = [key for key in REQUIRED_CONFIG if key not in config or config[key] is None]
    states: dict[str, str] = {dimension: "NOT_RUN" for dimension in DIMENSIONS}
    metrics: dict[str, Any] = {}
    reasons: list[str] = []

    market_type = observation.get("market_type")
    if market_type != "spot":
        states["market_type"] = "FAIL" if market_type is not None else "INDETERMINATE"
        reasons.append("market_type must be explicitly 'spot'")
        return _result(states, metrics, reasons, "FAIL" if states["market_type"] == "FAIL" else "INDETERMINATE")

    states["market_type"] = "PASS"
    if missing_config:
        reasons.append("missing required configuration: " + ", ".join(missing_config))

    try:
        bids = _levels(observation.get("bids"), "bids")
        asks = _levels(observation.get("asks"), "asks")
        bid, ask = bids[0][0], asks[0][0]
        spread = spread_bps(bid, ask)
        mid = (bid + ask) / 2.0
        metrics["mid"] = mid
        metrics["spread_bps"] = spread
        if bid > ask:
            raise ValueError("crossed order book")
        if "max_spread_bps" in config and _number(config["max_spread_bps"]) and config["max_spread_bps"] >= 0:
            states["spread"] = "PASS" if spread <= config["max_spread_bps"] else "FAIL"
        else:
            states["spread"] = "INDETERMINATE"
            reasons.append("max_spread_bps is missing or invalid")
        if "depth_band_bps" in config and _number(config["depth_band_bps"]) and config["depth_band_bps"] >= 0:
            depth_bid = depth_quote(observation["bids"], mid, config["depth_band_bps"], "bids")
            depth_ask = depth_quote(observation["asks"], mid, config["depth_band_bps"], "asks")
            metrics["depth_bid_quote"] = depth_bid
            metrics["depth_ask_quote"] = depth_ask
            if _positive(config.get("min_depth_quote")):
                states["depth"] = "PASS" if min(depth_bid, depth_ask) >= config["min_depth_quote"] else "FAIL"
            else:
                states["depth"] = "INDETERMINATE"
                reasons.append("min_depth_quote is missing or invalid")
        else:
            states["depth"] = "INDETERMINATE"
            reasons.append("depth_band_bps is missing or invalid")
        if _positive(config.get("order_size_base")):
            buy = estimate_slippage_bps(observation["asks"], mid, config["order_size_base"], "asks")
            sell = estimate_slippage_bps(observation["bids"], mid, config["order_size_base"], "bids")
            metrics["buy_execution"] = buy
            metrics["sell_execution"] = sell
            max_slippage = config.get("max_slippage_bps")
            if buy["slippage_bps"] is None or sell["slippage_bps"] is None:
                states["slippage"] = "INDETERMINATE"
                reasons.append("order book does not cover the full configured order size")
            elif _number(max_slippage) and max_slippage >= 0:
                states["slippage"] = "PASS" if max(buy["slippage_bps"], sell["slippage_bps"]) <= max_slippage else "FAIL"
            else:
                states["slippage"] = "INDETERMINATE"
                reasons.append("max_slippage_bps is missing or invalid")
        else:
            states["slippage"] = "INDETERMINATE"
            reasons.append("order_size_base is missing or invalid")
    except (KeyError, TypeError, ValueError) as exc:
        for dimension in ("spread", "depth", "slippage"):
            states[dimension] = "INDETERMINATE"
        reasons.append(f"order book invalid or incomplete: {exc}")

    try:
        freshness = evaluate_freshness(observation, config)
        metrics["freshness"] = freshness
        states["freshness"] = freshness["status"]
        if freshness["status"] == "FAIL":
            reasons.append("snapshot freshness/source-lag limits exceeded")
    except (KeyError, TypeError, ValueError) as exc:
        states["freshness"] = "INDETERMINATE"
        reasons.append(f"freshness cannot be established: {exc}")

    maker_fee = config.get("maker_fee_bps")
    taker_fee = config.get("taker_fee_bps")
    if _number(maker_fee) and maker_fee >= 0 and _number(taker_fee) and taker_fee >= 0:
        metrics["fees"] = {"maker_fee_bps_per_side": float(maker_fee),
                            "taker_fee_bps_per_side": float(taker_fee),
                            "taker_round_trip_fee_bps": float(taker_fee) * 2.0,
                            "note": "Fee estimate only; excludes withdrawal/network fees and account-specific discounts unless configured separately."}
        states["fees"] = "PASS"
    else:
        states["fees"] = "INDETERMINATE"
        reasons.append("maker_fee_bps and taker_fee_bps must be explicitly configured as finite non-negative values")


    availability = observation.get("availability_status")
    if availability == "confirmed":
        states["availability"] = "PASS"
    elif availability == "unavailable":
        states["availability"] = "FAIL"
        reasons.append("target-platform pair availability is confirmed unavailable")
    else:
        states["availability"] = "INDETERMINATE"
        reasons.append("target-platform pair availability is not confirmed")

    if missing_config:
        reasons.append("global decision blocked until required configuration is complete")
    critical = config.get("critical_dimensions")
    valid_critical = isinstance(critical, list) and bool(critical) and all(
        isinstance(item, str) and item in states for item in critical
    )
    approval_valid = (
        config.get("config_approval_status") == "approved"
        and isinstance(config.get("config_version"), str)
        and bool(config["config_version"].strip())
        and isinstance(config.get("config_approval_ref"), str)
        and bool(config["config_approval_ref"].strip())
    )
    if not approval_valid:
        reasons.append("configuration approval status/version/reference is missing or not approved")
        decision = "INDETERMINATE"
    elif not valid_critical:
        reasons.append("critical_dimensions must be an approved non-empty list of known dimensions")
        decision = "INDETERMINATE"
    elif missing_config or any(states[key] in {"INDETERMINATE", "NOT_RUN"} for key in critical):
        decision = "INDETERMINATE"
    elif any(states[key] == "FAIL" for key in critical):
        decision = "FAIL"
    else:
        decision = "PASS"
    return _result(states, metrics, reasons, decision)


def _result(states: dict[str, str], metrics: dict[str, Any], reasons: list[str], decision: str) -> dict[str, Any]:
    return {
        "decision_status": decision,
        "dimension_status": states,
        "metrics": metrics,
        "decision_reasons": reasons,
        "execution_mode": "read_only",
        "live_data_used": False,
        "orders_submitted": False,
    }
