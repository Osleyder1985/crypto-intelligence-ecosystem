"""Reproducibly evaluate a preserved public-market capture artifact.

This module never performs network requests or submits orders. It verifies the
stored raw response bytes before deriving snapshot-only spot liquidity metrics.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from selector import depth_quote, estimate_slippage_bps, spread_bps

VALID_STATES = {"PASS", "FAIL", "INDETERMINATE", "NOT_RUN"}


def _finite_positive(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return number


def _record_by_provider(artifact: dict[str, Any], provider: str) -> dict[str, Any]:
    records = artifact.get("records")
    if not isinstance(records, list):
        raise ValueError("artifact records must be a list")
    matches = [item for item in records if isinstance(item, dict) and item.get("provider") == provider]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one record for provider {provider}")
    return matches[0]


def _verified_payload(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        raise ValueError(f"{record.get('provider')} capture is not a successful HTTP 200 record")
    encoded = record.get("response_base64")
    digest = record.get("response_sha256")
    byte_count = record.get("response_bytes")
    if not isinstance(encoded, str) or not isinstance(digest, str):
        raise ValueError(f"{record.get('provider')} raw response bytes or digest are missing")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError(f"{record.get('provider')} response_base64 is invalid") from exc
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"{record.get('provider')} raw response SHA-256 mismatch")
    if isinstance(byte_count, bool) or byte_count != len(raw):
        raise ValueError(f"{record.get('provider')} response byte count mismatch")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{record.get('provider')} raw response is not UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{record.get('provider')} raw response must be a JSON object")
    if record.get("parsed_json") != parsed:
        raise ValueError(f"{record.get('provider')} parsed_json does not match preserved raw bytes")
    return parsed


def _levels(raw_levels: Any, field: str) -> list[dict[str, float]]:
    if not isinstance(raw_levels, list) or not raw_levels:
        raise ValueError(f"{field} must be a non-empty list")
    result = []
    for index, level in enumerate(raw_levels):
        if not isinstance(level, list) or len(level) < 2:
            raise ValueError(f"{field}[{index}] must contain price and quantity")
        result.append({
            "price": _finite_positive(level[0], f"{field}[{index}].price"),
            "quantity": _finite_positive(level[1], f"{field}[{index}].quantity"),
        })
    return result


def evaluate_capture(artifact: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a saved capture deterministically; config contains explicit scenario inputs."""
    config = {} if config is None else config
    if not isinstance(artifact, dict):
        raise ValueError("artifact must be a JSON object")
    if artifact.get("schema_version") != "public-market-capture-v1":
        raise ValueError("unsupported capture schema_version")
    if artifact.get("overall_status") != "PASS":
        raise ValueError("capture artifact overall_status is not PASS")

    pionex_record = _record_by_provider(artifact, "pionex")
    exchange_record = _record_by_provider(artifact, "binance_exchange_info")
    depth_record = _record_by_provider(artifact, "binance_depth")
    pionex = _verified_payload(pionex_record)
    exchange = _verified_payload(exchange_record)
    depth = _verified_payload(depth_record)

    pionex_data = pionex.get("data")
    symbols = pionex_data.get("symbols") if isinstance(pionex_data, dict) else None
    pionex_matches = [x for x in symbols or [] if isinstance(x, dict) and x.get("symbol") == "BTC_USDT"]
    exact_pionex = (
        len(pionex_matches) == 1
        and pionex_matches[0].get("type") == "SPOT"
        and pionex_matches[0].get("baseCurrency") == "BTC"
        and pionex_matches[0].get("quoteCurrency") == "USDT"
        and pionex_matches[0].get("enable") is True
    )
    exchange_matches = [
        x for x in exchange.get("symbols", [])
        if isinstance(x, dict) and x.get("symbol") == "BTCUSDT"
    ]
    exact_binance = (
        len(exchange_matches) == 1
        and exchange_matches[0].get("status") == "TRADING"
        and exchange_matches[0].get("isSpotTradingAllowed") is True
        and exchange_matches[0].get("baseAsset") == "BTC"
        and exchange_matches[0].get("quoteAsset") == "USDT"
    )
    bids = _levels(depth.get("bids"), "bids")
    asks = _levels(depth.get("asks"), "asks")
    # Sort before calculations; the source should be ordered, but calculations
    # remain deterministic if a valid payload's levels are not ordered.
    bids.sort(key=lambda item: item["price"], reverse=True)
    asks.sort(key=lambda item: item["price"])
    best_bid, best_ask = bids[0]["price"], asks[0]["price"]
    spread = spread_bps(best_bid, best_ask)
    mid = (best_bid + best_ask) / 2.0

    metrics: dict[str, Any] = {
        "symbol": "BTC_USDT",
        "market_type": "spot",
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid,
        "spread_bps": spread,
        "bid_levels_received": len(bids),
        "ask_levels_received": len(asks),
        "depth_snapshot_truncated_or_complete": "unknown",
        "depth_limitations": [
            "A 20-level API response is a bounded snapshot, not proof of full-book depth.",
            "Snapshot VWAP estimates do not guarantee executable fills or account-specific costs.",
            "Binance lastUpdateId is not an event timestamp; source freshness is indeterminate.",
        ],
    }
    statuses = {
        "capture_integrity": "PASS",
        "pionex_availability": "PASS" if exact_pionex else "FAIL",
        "binance_spot_market": "PASS" if exact_binance else "FAIL",
        "spread": "NOT_RUN",
        "depth": "NOT_RUN",
        "slippage": "NOT_RUN",
        "source_freshness": "INDETERMINATE",
        "fees": "INDETERMINATE",
    }

    band = config.get("depth_band_bps")
    if band is not None:
        band_value = _finite_nonnegative(band, "depth_band_bps")
        bid_depth = depth_quote(bids, mid, band_value, "bids")
        ask_depth = depth_quote(asks, mid, band_value, "asks")
        metrics["depth_band_bps"] = band_value
        metrics["bid_depth_quote"] = bid_depth
        metrics["ask_depth_quote"] = ask_depth
        metrics["min_side_depth_quote"] = min(bid_depth, ask_depth)
        min_depth = config.get("min_depth_quote")
        if min_depth is not None:
            threshold = _finite_nonnegative(min_depth, "min_depth_quote")
            statuses["depth"] = "PASS" if min(bid_depth, ask_depth) >= threshold else "FAIL"
            metrics["min_depth_quote_threshold"] = threshold

    max_spread = config.get("max_spread_bps")
    if max_spread is not None:
        threshold = _finite_nonnegative(max_spread, "max_spread_bps")
        statuses["spread"] = "PASS" if spread <= threshold else "FAIL"
        metrics["max_spread_bps_threshold"] = threshold

    order_size = config.get("order_size_base")
    max_slippage = config.get("max_slippage_bps")
    if order_size is not None:
        size = _finite_positive(order_size, "order_size_base")
        buy = estimate_slippage_bps(asks, mid, size, "asks")
        sell = estimate_slippage_bps(bids, mid, size, "bids")
        metrics["order_size_base"] = size
        metrics["buy_execution"] = buy
        metrics["sell_execution"] = sell
        if max_slippage is not None:
            threshold = _finite_nonnegative(max_slippage, "max_slippage_bps")
            metrics["max_slippage_bps_threshold"] = threshold
            slippages = (buy["slippage_bps"], sell["slippage_bps"])
            if any(value is None for value in slippages):
                statuses["slippage"] = "INDETERMINATE"
            else:
                statuses["slippage"] = "PASS" if max(slippages) <= threshold else "FAIL"

    return {
        "schema_version": "public-market-evaluation-v1",
        "source_artifact_schema": artifact["schema_version"],
        "source_created_at_utc": artifact.get("created_at_utc"),
        "evaluation_mode": "deterministic_saved_artifact_read_only",
        "dimension_status": statuses,
        "metrics": metrics,
        "decision_status": "INDETERMINATE",
        "decision_reason": (
            "No approved decision policy or human-approved thresholds were supplied; "
            "metrics do not constitute an investment recommendation."
        ),
        "orders_submitted": False,
        "network_requests_made": False,
    }


def _finite_nonnegative(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be a finite non-negative number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite non-negative number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path, help="Preserved public-market-capture.json")
    parser.add_argument("--config", type=Path, help="Optional JSON with explicit scenario thresholds and order size")
    parser.add_argument("--output", type=Path, help="Optional path for evaluation JSON; defaults to stdout")
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
    result = evaluate_capture(artifact, config)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
