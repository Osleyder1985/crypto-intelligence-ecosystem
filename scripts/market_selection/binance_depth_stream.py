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


def _snapshot_levels(value: Any, field: str) -> dict[Decimal, Decimal]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"snapshot {field} must be a non-empty list")
    levels: dict[Decimal, Decimal] = {}
    for index, level in enumerate(value):
        if not isinstance(level, list) or len(level) != 2:
            raise ValueError(f"snapshot {field}[{index}] must contain price and quantity")
        price_raw, quantity_raw = level
        try:
            price, quantity = Decimal(str(price_raw)), Decimal(str(quantity_raw))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"snapshot {field}[{index}] contains an invalid decimal") from exc
        if not price.is_finite() or price <= 0 or not quantity.is_finite() or quantity <= 0:
            raise ValueError(f"snapshot {field}[{index}] price and quantity must be finite and positive")
        if price in levels:
            raise ValueError(f"snapshot {field} contains duplicate price levels")
        levels[price] = quantity
    return levels


def _apply_levels(book: dict[Decimal, Decimal], updates: list[list[Any]]) -> None:
    for price_raw, quantity_raw in updates:
        price, quantity = Decimal(str(price_raw)), Decimal(str(quantity_raw))
        if quantity == 0:
            book.pop(price, None)
        else:
            book[price] = quantity


def _serialize_levels(book: dict[Decimal, Decimal], side: str) -> list[list[str]]:
    prices = sorted(book, reverse=(side == "bids"))
    return [[format(price, "f"), format(book[price], "f")] for price in prices]


def synchronize_snapshot_with_events(snapshot: Any, buffered_events: Any) -> dict[str, Any]:
    """Build a locally consistent snapshot book from buffered diff-depth events.

    The function is deterministic and network-free. It returns no usable book if
    no event bridges the snapshot update ID or if any sequence gap is detected.
    It does not keep a live socket open; the caller must continue classifying each
    subsequent event and discard/rebuild the book on GAP.
    """
    if not isinstance(snapshot, Mapping):
        raise ValueError("snapshot must be an object")
    snapshot_id = _update_id(snapshot.get("lastUpdateId"), "snapshot.lastUpdateId")
    if not isinstance(buffered_events, list):
        raise ValueError("buffered_events must be a list")
    bids = _snapshot_levels(snapshot.get("bids"), "bids")
    asks = _snapshot_levels(snapshot.get("asks"), "asks")
    if max(bids) >= min(asks):
        raise ValueError("snapshot order book must not be locked or crossed")

    applied = 0
    last_id = snapshot_id
    last_event_time_utc = None
    expected_symbol = None
    for event in buffered_events:
        metadata = validate_depth_event(event)
        if expected_symbol is None:
            expected_symbol = metadata["symbol"]
        elif metadata["symbol"] != expected_symbol:
            raise ValueError("buffered depth events must all use the same symbol")
        decision = classify_depth_event(last_id, event)
        if decision["state"] == IGNORE_OLD:
            continue
        if decision["state"] == GAP:
            return {
                "status": "RESYNC_REQUIRED",
                "reason": decision["reason"],
                "snapshot_last_update_id": snapshot_id,
                "last_applied_update_id": last_id,
                "applied_event_count": applied,
                "last_event_time_utc": last_event_time_utc,
                "bids": None,
                "asks": None,
            }
        _apply_levels(bids, event["b"])
        _apply_levels(asks, event["a"])
        last_id = decision["final_update_id"]
        last_event_time_utc = decision["event_time_utc"]
        applied += 1

    if applied == 0:
        return {
            "status": "INDETERMINATE",
            "reason": "no buffered event bridged the snapshot update ID",
            "snapshot_last_update_id": snapshot_id,
            "last_applied_update_id": last_id,
            "applied_event_count": 0,
            "last_event_time_utc": None,
            "bids": None,
            "asks": None,
        }
    return {
        "status": "SYNCHRONIZED",
        "reason": "snapshot bridged and buffered events applied without sequence gaps",
        "snapshot_last_update_id": snapshot_id,
        "last_applied_update_id": last_id,
        "applied_event_count": applied,
        "last_event_time_utc": last_event_time_utc,
        "bids": _serialize_levels(bids, "bids"),
        "asks": _serialize_levels(asks, "asks"),
    }
