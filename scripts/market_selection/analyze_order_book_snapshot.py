"""Analyze one preserved, authorized normalized Spot order-book snapshot.

This is descriptive only: it measures visible depth and does not infer hidden orders,
future price reactions, or executable liquidity.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import math
from typing import Any

from scripts.market_selection.provider_license_gate import evaluate_provider_use

INPUT_SCHEMA = "crypto-spot-order-book-snapshot-v1"
OUTPUT_SCHEMA = "crypto-spot-order-book-analysis-v1"


def _positive(value: Any, field: str, *, allow_zero: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a decimal number") from exc
    if not number.is_finite() or (number < 0 if allow_zero else number <= 0):
        requirement = "finite and non-negative" if allow_zero else "finite and positive"
        raise ValueError(f"{field} must be {requirement}")
    return number


def _levels(value: Any, field: str, *, descending: bool) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    result = []
    previous = None
    for index, row in enumerate(value):
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            raise ValueError(f"{field}[{index}] must contain price and quantity")
        price = _positive(row[0], f"{field}[{index}].price")
        quantity = _positive(row[1], f"{field}[{index}].quantity", allow_zero=True)
        if quantity == 0:
            raise ValueError(f"{field}[{index}].quantity must be positive")
        if previous is not None and ((descending and price > previous) or (not descending and price < previous)):
            raise ValueError(f"{field} must be sorted by price")
        previous = price
        result.append({"price": str(price), "quantity": str(quantity), "notional": str(price * quantity)})
    return result


def _annotate_depth(levels: list[dict[str, str]], midpoint: Decimal) -> list[dict[str, str]]:
    cumulative_quantity = Decimal(0)
    cumulative_notional = Decimal(0)
    annotated = []
    for row in levels:
        price = Decimal(row["price"])
        quantity = Decimal(row["quantity"])
        notional = Decimal(row["notional"])
        cumulative_quantity += quantity
        cumulative_notional += notional
        distance_bps = abs(price - midpoint) / midpoint * Decimal(10_000)
        if not distance_bps.is_finite():
            raise ValueError("depth distance exceeds the supported finite numeric range")
        annotated.append({
            **row,
            "distance_from_mid_bps": str(distance_bps.quantize(Decimal("0.000001"))),
            "cumulative_base_quantity": str(cumulative_quantity),
            "cumulative_quote_notional": str(cumulative_notional),
        })
    return annotated


def analyze_order_book_snapshot(artifact: dict, authorization_registry: dict | None = None) -> dict:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    if artifact.get("capture_status") != "PASS":
        raise ValueError("order-book capture_status must be PASS")
    if not isinstance(authorization_registry, dict):
        authorization_registry = {}
    provider_id = artifact.get("provider_id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise PermissionError("order-book provider_id is required for trusted authorization lookup")
    try:
        provider_use = evaluate_provider_use(
            provider_id, "internal_analysis", authorization_registry.get(provider_id),
        )
    except ValueError as exc:
        raise PermissionError("order-book provider authorization record is invalid") from exc
    if provider_use["decision"] != "ALLOW":
        raise PermissionError("order-book analysis blocked before use: " + ",".join(provider_use["reason_codes"]))

    market = artifact.get("market")
    if not isinstance(market, dict):
        raise ValueError("market must be an object")
    exchange = market.get("exchange")
    symbol = market.get("symbol_native")
    if not isinstance(exchange, str) or not exchange.strip():
        raise ValueError("market.exchange is required")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("market.symbol_native is required")
    captured_at = artifact.get("captured_at_utc")
    if not isinstance(captured_at, str) or not captured_at.strip():
        raise ValueError("captured_at_utc is required")
    try:
        parsed_capture_time = datetime.fromisoformat(captured_at.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("captured_at_utc must be ISO-8601 with timezone") from exc
    if parsed_capture_time.tzinfo is None or parsed_capture_time.utcoffset() is None:
        raise ValueError("captured_at_utc must include a timezone")

    bids = _levels(artifact.get("bids"), "bids", descending=True)
    asks = _levels(artifact.get("asks"), "asks", descending=False)
    best_bid = Decimal(bids[0]["price"])
    best_ask = Decimal(asks[0]["price"])
    if best_bid >= best_ask:
        raise ValueError("crossed or locked book is invalid for this snapshot")
    midpoint = (best_bid + best_ask) / Decimal(2)
    spread = best_ask - best_bid
    bids = _annotate_depth(bids, midpoint)
    asks = _annotate_depth(asks, midpoint)
    bid_notional = sum((Decimal(row["notional"]) for row in bids), Decimal(0))
    ask_notional = sum((Decimal(row["notional"]) for row in asks), Decimal(0))
    total_notional = bid_notional + ask_notional
    imbalance = ((bid_notional - ask_notional) / total_notional) if total_notional else None
    spread_bps = float(spread / midpoint * Decimal(10000))
    if not math.isfinite(spread_bps):
        raise ValueError("spread_bps exceeds the supported finite numeric range")

    return {
        "schema_version": OUTPUT_SCHEMA,
        "status": "DESCRIPTIVE_SNAPSHOT",
        "market": {"exchange": exchange.strip(), "symbol_native": symbol.strip(),
                   "quote_asset": market.get("quote_asset")},
        "captured_at_utc": captured_at,
        "provider_use_assessment": provider_use,
        "book": {
            "bids_count": len(bids), "asks_count": len(asks),
            "best_bid": str(best_bid), "best_ask": str(best_ask),
            "mid_price": str(midpoint), "spread_absolute": str(spread),
            "spread_bps": spread_bps,
            "visible_bid_base_quantity": str(sum((Decimal(row["quantity"]) for row in bids), Decimal(0))),
            "visible_ask_base_quantity": str(sum((Decimal(row["quantity"]) for row in asks), Decimal(0))),
            "visible_bid_quote_notional": str(bid_notional),
            "visible_ask_quote_notional": str(ask_notional),
            "visible_notional_imbalance": float(imbalance) if imbalance is not None else None,
            "bids": bids, "asks": asks,
        },
        "limitations": [
            "Only levels present in this snapshot are measured; provider depth limits may truncate the book.",
            "Visible orders can be modified or cancelled and are not guaranteed executable liquidity.",
            "This snapshot does not reveal hidden orders or the full cross-exchange market.",
            "Notional imbalance is descriptive and is not a directional prediction.",
            "No order is submitted.",
        ],
        "orders_submitted": False,
    }
