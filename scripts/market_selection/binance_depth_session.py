"""Transport-agnostic state machine for a Binance diff-depth book session.

This controller owns no sockets or clocks. The transport must call begin_resync
before buffering events, record receive timestamps at message receipt, fetch a
REST snapshot, then call install_snapshot. Disconnects and sequence gaps make
the book unavailable until a new snapshot bridges the buffered stream.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from scripts.market_selection.binance_depth_stream import (
    APPLY,
    GAP,
    IGNORE_OLD,
    classify_depth_event,
    synchronize_snapshot_with_events,
    validate_depth_event,
)

DISCONNECTED = "DISCONNECTED"
BUFFERING = "BUFFERING"
SYNCHRONIZED = "SYNCHRONIZED"
RESYNC_REQUIRED = "RESYNC_REQUIRED"


class DepthBookSession:
    """Manage the validity lifecycle of one symbol's local depth book."""

    def __init__(self) -> None:
        self.state = DISCONNECTED
        self.symbol: str | None = None
        self._buffer: list[dict[str, Any]] = []
        self._book: dict[str, Any] | None = None

    @property
    def current_book(self) -> dict[str, Any] | None:
        """Return a defensive copy only while the session is synchronized."""
        if self.state != SYNCHRONIZED or self._book is None:
            return None
        return deepcopy(self._book)

    def begin_resync(self, symbol: str) -> dict[str, Any]:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        self.symbol = symbol.upper()
        self._buffer = []
        self._book = None
        self.state = BUFFERING
        return {"state": self.state, "symbol": self.symbol}

    def receive_event(self, event: Any) -> dict[str, Any]:
        metadata = validate_depth_event(event)
        if self.state == DISCONNECTED:
            return {"state": self.state, "action": "IGNORED_NOT_STARTED"}
        if metadata["symbol"].upper() != self.symbol:
            self._invalidate()
            return {
                "state": self.state,
                "action": "RESYNC_REQUIRED",
                "reason": "event symbol does not match session symbol",
            }
        if self.state in (BUFFERING, RESYNC_REQUIRED):
            self._buffer.append(deepcopy(dict(event)))
            return {
                "state": self.state,
                "action": "BUFFERED",
                "buffered_event_count": len(self._buffer),
            }
        if self.state != SYNCHRONIZED or self._book is None:
            self._invalidate()
            return {"state": self.state, "action": "RESYNC_REQUIRED"}

        decision = classify_depth_event(self._book["last_applied_update_id"], event)
        if decision["state"] == IGNORE_OLD:
            return {"state": self.state, "action": IGNORE_OLD, "reason": decision["reason"]}
        if decision["state"] == GAP:
            self._invalidate()
            return {"state": self.state, "action": "RESYNC_REQUIRED", "reason": decision["reason"]}

        snapshot = {
            "lastUpdateId": self._book["last_applied_update_id"],
            "bids": self._book["bids"],
            "asks": self._book["asks"],
        }
        updated = synchronize_snapshot_with_events(snapshot, [event])
        if updated["status"] != SYNCHRONIZED:
            self._invalidate()
            return {
                "state": self.state,
                "action": "RESYNC_REQUIRED",
                "reason": updated["reason"],
            }
        self._book = updated
        return {
            "state": self.state,
            "action": APPLY,
            "last_applied_update_id": updated["last_applied_update_id"],
            "last_event_time_utc": updated["last_event_time_utc"],
        }

    def install_snapshot(self, snapshot: Any) -> dict[str, Any]:
        if self.state not in (BUFFERING, RESYNC_REQUIRED):
            raise RuntimeError("begin_resync must be called before installing a snapshot")
        result = synchronize_snapshot_with_events(snapshot, self._buffer)
        self._buffer = []
        if result["status"] == SYNCHRONIZED:
            self._book = result
            self.state = SYNCHRONIZED
            return {"state": self.state, "action": "BOOK_READY", "book": self.current_book}
        self._book = None
        self.state = RESYNC_REQUIRED
        return {
            "state": self.state,
            "action": "RESYNC_REQUIRED",
            "reason": result["reason"],
            "book": None,
        }

    def disconnect(self) -> dict[str, Any]:
        self._buffer = []
        self._book = None
        self.state = DISCONNECTED
        return {"state": self.state, "action": "BOOK_INVALIDATED"}

    def _invalidate(self) -> None:
        self._book = None
        self._buffer = []
        self.state = RESYNC_REQUIRED
