"""Pure validation helpers for Binance Spot diff-depth events.

This module does not open sockets, fetch snapshots, mutate an order book, or
claim freshness. A caller must implement the documented snapshot+buffer
synchronization protocol and must invalidate its local book after a sequence gap.

Protocol reference:
https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#diff-depth-stream
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

APPLY = "APPLY"
IGNORE_OLD = "IGNORE_OLD"
GAP = "GAP"


def _update_id(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _validate_levels(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    for index, level in enumerate(value):
        if not isinstance(level, list) or len(level) != 2:
            raise ValueError(f"{field}[{index}] must contain price and quantity")
        price_raw, quantity_raw = level
        if not isinstance(price_raw, (str, int, float)) or isinstance(price_raw, bool):
            raise ValueError(f"{field}[{index}] price must be numeric")
        if not isinstance(quantity_raw, (str, int, float)) or isinstance(quantity_raw, bool):
            raise ValueError(f"{field}[{index}] quantity must be numeric")
        try:
            price, quantity = Decimal(str(price_raw)), Decimal(str(quantity_raw))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field}[{index}] contains an invalid decimal") from exc
        if not price.is_finite() or price <= 0:
            raise ValueError(f"{field}[{index}] price must be finite and positive")
        # Zero quantity is valid in a diff-depth event and means delete the level.
        if not quantity.is_finite() or quantity < 0:
            raise ValueError(f"{field}[{index}] quantity must be finite and non-negative")


def validate_depth_event(event: Any) -> dict[str, Any]:
    """Validate a raw depthUpdate event and return normalized sequence metadata."""
    if not isinstance(event, Mapping):
        raise ValueError("depth event must be an object")
    if event.get("e") != "depthUpdate":
        raise ValueError("event type must be depthUpdate")
    event_time_ms = _update_id(event.get("E"), "E")
    first_update_id = _update_id(event.get("U"), "U")
    final_update_id = _update_id(event.get("u"), "u")
    if first_update_id > final_update_id:
        raise ValueError("U must be less than or equal to u")
    symbol = event.get("s")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("s must be a non-empty symbol")
    _validate_levels(event.get("b"), "b")
    _validate_levels(event.get("a"), "a")
    try:
        event_time = datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("E must be a representable Unix timestamp in milliseconds") from exc
    return {
        "symbol": symbol,
        "event_time_ms": event_time_ms,
        "event_time_utc": event_time.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "first_update_id": first_update_id,
        "final_update_id": final_update_id,
    }


def classify_depth_event(last_applied_update_id: Any, event: Any) -> dict[str, Any]:
    """Classify a diff event relative to a snapshot/local book update ID.

    APPLY means the sequence interval overlaps the next required ID; it does not
    mean the caller has applied the price changes or proven the book is fresh.
    GAP means the local book must be discarded and re-synchronized.
    """
    last_id = _update_id(last_applied_update_id, "last_applied_update_id")
    metadata = validate_depth_event(event)
    first_id = metadata["first_update_id"]
    final_id = metadata["final_update_id"]
    if final_id <= last_id:
        state, reason = IGNORE_OLD, "event final update ID is already applied"
    elif first_id > last_id + 1:
        state, reason = GAP, "event starts after the next required update ID"
    else:
        state, reason = APPLY, "event covers the next required update ID"
    return {"state": state, "reason": reason, **metadata}
