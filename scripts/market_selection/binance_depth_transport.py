"""Bounded, read-only Binance Spot WebSocket depth capture.

Requires the optional websocket-client package for the live transport. No API
keys are used: this module reads the public Spot depth stream and REST snapshot
only. It never submits orders.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.market_selection.binance_depth_session import (
    RESYNC_REQUIRED,
    SYNCHRONIZED,
    DepthBookSession,
)

REST_BASE = "https://api.binance.com/api/v3/depth"
WS_BASE = "wss://stream.binance.com:9443/ws"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_MESSAGES = 2000
DEFAULT_MAX_RESYNC_ATTEMPTS = 3


def utc_now() -> str:
    """Return a timezone-aware UTC timestamp with millisecond precision."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def fetch_public_depth_snapshot(
    symbol: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
) -> dict[str, Any]:
    """Fetch one public REST depth snapshot; reject HTTP and malformed responses."""
    query = urlencode({"symbol": symbol.upper(), "limit": 1000})
    request = Request(
        f"{REST_BASE}?{query}",
        headers={"User-Agent": "crypto-intelligence-ecosystem-read-only/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"Binance REST snapshot returned HTTP {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"public depth snapshot request failed: {type(exc).__name__}") from exc
    if (
        not isinstance(payload, dict)
        or isinstance(payload.get("lastUpdateId"), bool)
        or not isinstance(payload.get("lastUpdateId"), int)
    ):
        raise RuntimeError("Binance REST snapshot response is malformed")
    if not isinstance(payload.get("bids"), list) or not isinstance(payload.get("asks"), list):
        raise RuntimeError("Binance REST snapshot has no bids/asks arrays")
    return payload


def _open_public_stream(symbol: str, timeout_seconds: float) -> Any:
    """Open the public stream using websocket-client, imported only for live use."""
    try:
        import websocket
    except ImportError as exc:
        raise RuntimeError(
            "live capture requires: python -m pip install -r requirements-market-data.txt"
        ) from exc
    url = f"{WS_BASE}/{symbol.lower()}@depth@100ms"
    return websocket.create_connection(url, timeout=timeout_seconds, enable_multithread=False)


def capture_once(
    symbol: str,
    *,
    websocket_factory: Callable[[str, float], Any] | None = None,
    snapshot_fetcher: Callable[[str, float], dict[str, Any]] = fetch_public_depth_snapshot,
    clock: Callable[[], str] = utc_now,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_messages: int = DEFAULT_MAX_MESSAGES,
    max_resync_attempts: int = DEFAULT_MAX_RESYNC_ATTEMPTS,
) -> dict[str, Any]:
    """Capture one synchronized book with strict message/resync bounds.

    Events are buffered before a REST snapshot. At least one event received
    after each snapshot is buffered before synchronization is attempted, so
    post-snapshot updates can bridge the snapshot update ID. A sequence gap
    discards the book and restarts the snapshot+buffer cycle.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string")
    if timeout_seconds <= 0 or max_messages < 1 or max_resync_attempts < 1:
        raise ValueError("timeout and capture bounds must be positive")
    normalized_symbol = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{2,30}", normalized_symbol):
        raise ValueError("symbol must contain only 2-30 ASCII letters or digits")
    factory = websocket_factory or _open_public_stream
    socket = factory(normalized_symbol, timeout_seconds)
    session = DepthBookSession()
    session.begin_resync(normalized_symbol)
    snapshot: dict[str, Any] | None = None
    events_after_snapshot = 0
    resync_attempts = 0
    messages = 0
    try:
        while messages < max_messages:
            raw = socket.recv()
            messages += 1
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                event = json.loads(raw)
            except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("WebSocket delivered malformed JSON") from exc
            if not isinstance(event, dict) or event.get("e") != "depthUpdate":
                continue

            received_at = clock()
            action = session.receive_event(event, received_at)
            if action.get("action") != "BUFFERED":
                if action.get("action") == "RESYNC_REQUIRED":
                    snapshot = None
                    events_after_snapshot = 0
                continue

            if snapshot is None:
                if resync_attempts >= max_resync_attempts:
                    break
                snapshot = snapshot_fetcher(normalized_symbol, timeout_seconds)
                resync_attempts += 1
                events_after_snapshot = 0
                continue

            events_after_snapshot += 1
            if events_after_snapshot < 1:
                continue
            installed = session.install_snapshot(snapshot)
            if installed["state"] == SYNCHRONIZED:
                evaluation_time = clock()
                observation = session.freshness_observation(evaluation_time)
                book = installed["book"]
                return {
                    "status": "SYNCHRONIZED",
                    "symbol": normalized_symbol,
                    "snapshot_last_update_id": book["snapshot_last_update_id"],
                    "last_applied_update_id": book["last_applied_update_id"],
                    "applied_event_count": book["applied_event_count"],
                    "source_event_at_utc": book["last_event_time_utc"],
                    "last_event_received_at_utc": book["last_received_at_utc"],
                    "evaluated_at_utc": observation["evaluation_time_utc"],
                    "bids": book["bids"],
                    "asks": book["asks"],
                    "freshness_observation": observation,
                    "messages_received": messages,
                    "snapshot_attempts": resync_attempts,
                    "read_only": True,
                    "orders_submitted": False,
                }

            if installed["state"] == RESYNC_REQUIRED:
                session.begin_resync(normalized_symbol)
                snapshot = None
                events_after_snapshot = 0

        raise RuntimeError(
            "capture did not synchronize within configured bounds "
            f"(messages={messages}, snapshot_attempts={resync_attempts})"
        )
    finally:
        try:
            socket.close()
        except Exception:
            pass


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Bounded read-only Binance Spot depth capture")
    parser.add_argument("--symbol", default="BTCUSDT", help="Spot symbol, e.g. BTCUSDT")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-messages", type=int, default=DEFAULT_MAX_MESSAGES)
    parser.add_argument("--max-resync-attempts", type=int, default=DEFAULT_MAX_RESYNC_ATTEMPTS)
    args = parser.parse_args()
    result = capture_once(
        args.symbol,
        timeout_seconds=args.timeout,
        max_messages=args.max_messages,
        max_resync_attempts=args.max_resync_attempts,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
