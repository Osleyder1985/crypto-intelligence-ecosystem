"""Capture bounded live Binance Spot diff-depth evidence (read-only).

This command writes a reproducible artifact with event/receive/evaluation times,
snapshot synchronization results, book state, integrity digests, and measured
clock offset evidence. It does not define or approve freshness thresholds and
never submits orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.market_selection.binance_depth_transport import capture_once

TIME_URL = "https://data-api.binance.vision/api/v3/time"
DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
SCHEMA_VERSION = "binance-live-depth-evidence-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def clock_probe(timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Measure local wall-clock offset against Binance server time; do not grade it."""
    request = Request(TIME_URL, headers={"Accept": "application/json"}, method="GET")
    started_wall_ns = time.time_ns()
    started_mono_ns = time.monotonic_ns()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            chunks: list[bytes] = []
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
            status = response.status
        ended_mono_ns = time.monotonic_ns()
        ended_wall_ns = time.time_ns()
        payload = json.loads(raw.decode("utf-8"))
        server_ms = payload.get("serverTime") if isinstance(payload, dict) else None
        if status != 200 or isinstance(server_ms, bool) or not isinstance(server_ms, int):
            raise ValueError("Binance time response has unexpected status or schema")
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "status": "FAIL", "error_type": type(exc).__name__,
            "error_message": str(exc)[:240], "checked_at_utc": utc_now(),
        }

    rtt_ms = (ended_mono_ns - started_mono_ns) / 1_000_000
    local_midpoint_ms = (started_wall_ns + ended_wall_ns) / 2_000_000
    server_offset_ms = server_ms - local_midpoint_ms
    return {
        "status": "MEASURED",
        "source": TIME_URL,
        "source_server_time_ms": server_ms,
        "request_started_at_utc": datetime.fromtimestamp(started_wall_ns / 1e9, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "response_received_at_utc": datetime.fromtimestamp(ended_wall_ns / 1e9, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "round_trip_time_ms": round(rtt_ms, 3),
        "local_minus_server_offset_ms": round(-server_offset_ms, 3),
        "estimated_uncertainty_ms": round(rtt_ms / 2, 3),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
    }


def measure_clock(probes: int = 3, timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Keep every probe and select the lowest-RTT successful measurement."""
    observations = [clock_probe(timeout_seconds) for _ in range(probes)]
    successful = [item for item in observations if item.get("status") == "MEASURED"]
    if not successful:
        return {"status": "INDETERMINATE", "reason": "all server-time probes failed", "probes": observations}
    selected = min(successful, key=lambda item: item["round_trip_time_ms"])
    return {
        "status": "MEASURED" if len(successful) == probes else "PARTIAL",
        "selection_method": "lowest observed round-trip time; not a policy threshold",
        "selected_probe": selected,
        "probes": observations,
    }


def capture_symbol(symbol: str, timeout_seconds: float, max_messages: int, max_resync_attempts: int) -> dict[str, Any]:
    started_at = utc_now()
    try:
        result = capture_once(
            symbol, timeout_seconds=timeout_seconds,
            max_messages=max_messages, max_resync_attempts=max_resync_attempts,
        )
        record = {
            "status": "SYNCHRONIZED",
            "symbol": symbol,
            "capture_started_at_utc": started_at,
            "capture_completed_at_utc": utc_now(),
            **result,
        }
        record["evidence_sha256"] = sha256_json(record)
        return record
    except Exception as exc:
        record = {
            "status": "FAIL",
            "symbol": symbol,
            "capture_started_at_utc": started_at,
            "capture_completed_at_utc": utc_now(),
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:300],
            "read_only": True,
            "orders_submitted": False,
        }
        record["evidence_sha256"] = sha256_json(record)
        return record


def capture_batch(
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    *,
    timeout_seconds: float = 5.0,
    max_messages: int = 2000,
    max_resync_attempts: int = 3,
) -> dict[str, Any]:
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("symbols must be non-empty and unique")
    normalized = tuple(symbol.strip().upper() for symbol in symbols)
    if any(not symbol or not symbol.isascii() or not symbol.isalnum() for symbol in normalized):
        raise ValueError("symbols must be ASCII alphanumeric exchange symbols")
    clock_evidence = measure_clock(timeout_seconds=timeout_seconds)
    captures = [
        capture_symbol(symbol, timeout_seconds, max_messages, max_resync_attempts)
        for symbol in normalized
    ]
    successful = all(item["status"] == "SYNCHRONIZED" for item in captures)
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "scope": "public Binance Spot WebSocket diff-depth plus REST snapshot; read-only",
        "clock_evidence": clock_evidence,
        "captures": captures,
        "overall_status": "PASS" if successful and clock_evidence["status"] == "MEASURED" else "INDETERMINATE",
        "decision_status": "INDETERMINATE",
        "freshness_policy_approved": False,
        "orders_submitted": False,
        "limitations": [
            "Clock measurements are observations, not an approved clock-skew policy.",
            "No freshness PASS/FAIL is asserted without an approved policy and risk rationale.",
            "Event time, local receive time, and evaluation time are distinct fields.",
            "Hashes support integrity checking of recorded artifacts; they do not prove provider authenticity.",
            "A synchronized local book is not a guarantee of executable liquidity or fills.",
            "Fees and total execution costs are not evaluated by this capture.",
        ],
    }
    artifact["artifact_sha256"] = sha256_json(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/binance-live-depth-evidence.json")
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-messages", type=int, default=2000)
    parser.add_argument("--max-resync-attempts", type=int, default=3)
    args = parser.parse_args()
    artifact = capture_batch(
        tuple(args.symbols), timeout_seconds=args.timeout,
        max_messages=args.max_messages, max_resync_attempts=args.max_resync_attempts,
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path),
        "overall_status": artifact["overall_status"],
        "decision_status": artifact["decision_status"],
        "clock_status": artifact["clock_evidence"]["status"],
        "symbols": [{"symbol": item["symbol"], "status": item["status"]} for item in artifact["captures"]],
        "artifact_sha256": artifact["artifact_sha256"],
    }, indent=2))
    return 0 if artifact["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
