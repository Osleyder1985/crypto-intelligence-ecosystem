"""Cross-process request pacing for approved external-event sources.

The SQLite ledger is shared by invocations running as the same OS user on the same
host. Coordination failures are fail-closed: callers must not make the request.
"""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import time


class RateLimitCoordinationError(RuntimeError):
    """Raised when the shared request-pacing ledger cannot safely coordinate."""


def _default_database_path() -> Path:
    configured = os.environ.get("CRYPTO_EVENT_RATE_LIMIT_DB")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".crypto-intelligence" / "event-rate-limit.sqlite3"


def wait_for_rate_slot(
    source_id: str,
    requests_per_second: float,
    database_path: str | os.PathLike[str] | None = None,
    *,
    sleep=time.sleep,
    clock=time.time,
) -> None:
    """Reserve a serialized slot in a persistent SQLite ledger, then wait for it.

    A transaction reserves the next slot before sleeping, so concurrent processes
    cannot all observe the same previous timestamp and proceed together. The
    database is deliberately shared across CLI invocations, not stored in process
    memory. If the ledger cannot be used, this function raises and callers must
    abort the network operation.
    """
    if not isinstance(source_id, str) or not source_id.strip():
        raise RateLimitCoordinationError("source_id must be a non-empty string")
    if isinstance(requests_per_second, bool) or not isinstance(requests_per_second, (int, float)):
        raise RateLimitCoordinationError("requests_per_second must be a positive number")
    if requests_per_second <= 0:
        raise RateLimitCoordinationError("requests_per_second must be a positive number")

    path = Path(database_path).expanduser() if database_path is not None else _default_database_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(path), timeout=10.0, isolation_level=None) as connection:
            connection.execute("PRAGMA busy_timeout = 10000")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS request_slots ("
                "source_id TEXT PRIMARY KEY, next_allowed_epoch REAL NOT NULL)"
            )
            connection.execute("BEGIN IMMEDIATE")
            now = float(clock())
            row = connection.execute(
                "SELECT next_allowed_epoch FROM request_slots WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            reserved_at = max(now, float(row[0]) if row else now)
            next_allowed = reserved_at + (1.0 / float(requests_per_second))
            connection.execute(
                "INSERT INTO request_slots(source_id, next_allowed_epoch) VALUES (?, ?) "
                "ON CONFLICT(source_id) DO UPDATE SET next_allowed_epoch = excluded.next_allowed_epoch",
                (source_id, next_allowed),
            )
            connection.execute("COMMIT")
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        raise RateLimitCoordinationError(
            "shared rate-limit ledger unavailable; network request blocked"
        ) from exc

    delay = reserved_at - float(clock())
    if delay > 0:
        sleep(delay)
