"""Transport-agnostic state machine for a Binance diff-depth book session.

This controller owns no sockets or clocks. The transport must call begin_resync
before buffering events, record receive timestamps at message receipt, fetch a
REST snapshot, then call install_snapshot. Disconnects and sequence gaps make
the book unavailable until a new snapshot bridges the buffered stream.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from scripts.market_selection.binance_depth_stream import (
    APPLY,
    GAP,
    IGNORE_OLD,
    classify_depth_event,
    synchronize_snapshot_with_events,
    validate_depth_event,
    freshness_observation_from_sync,
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

    def receive_event(self, event: Any, received_at_utc: Any) -> dict[str, Any]:
        metadata = validate_depth_event(event)
        received_at = self._normalize_utc_timestamp(received_at_utc, "received_at_utc")
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
            self._buffer.append({
                "event": deepcopy(dict(event)),
                "received_at_utc": received_at,
            })
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
        updated["last_received_at_utc"] = received_at
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
        buffered = self._buffer
        result = synchronize_snapshot_with_events(
            snapshot, [item["event"] for item in buffered]
        )
        self._buffer = []
        if result["status"] == SYNCHRONIZED:
            last_id = result["snapshot_last_update_id"]
            last_received_at = None
            for item in buffered:
                decision = classify_depth_event(last_id, item["event"])
                if decision["state"] == IGNORE_OLD:
                    continue
                if decision["state"] == GAP:
                    self._book = None
                    self.state = RESYNC_REQUIRED
                    return {
                        "state": self.state,
                        "action": "RESYNC_REQUIRED",
                        "reason": "buffered event sequence changed during timestamp attribution",
                        "book": None,
                    }
                last_id = decision["final_update_id"]
                last_received_at = item["received_at_utc"]
            if last_received_at is None:
                self._book = None
                self.state = RESYNC_REQUIRED
                return {
                    "state": self.state,
                    "action": "RESYNC_REQUIRED",
                    "reason": "no applied event has a receive timestamp",
                    "book": None,
                }
            result["last_received_at_utc"] = last_received_at
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

    def freshness_observation(self, evaluation_time_utc: Any) -> dict[str, str]:
        if self.state != SYNCHRONIZED or self._book is None:
            raise ValueError("freshness requires a SYNCHRONIZED book")
        received_at = self._book.get("last_received_at_utc")
        return freshness_observation_from_sync(
            self._book, received_at, evaluation_time_utc
        )

    @staticmethod
    def _normalize_utc_timestamp(value: Any, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be an explicit ISO-8601 timestamp")
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(f"{field} must include a UTC offset")
        return parsed.astimezone(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")

    def _invalidate(self) -> None:
        self._book = None
        self._buffer = []
        self.state = RESYNC_REQUIRED
