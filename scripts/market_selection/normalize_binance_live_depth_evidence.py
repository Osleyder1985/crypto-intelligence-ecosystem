"""Normalize preserved synchronized Binance depth evidence for the research report.

The adapter verifies artifact digests and keeps transport synchronization separate
from freshness policy and investment conclusions. It never performs network I/O.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from typing import Any

INPUT_SCHEMA = "binance-live-depth-evidence-v1"
OUTPUT_SCHEMA = "crypto-spot-order-book-snapshot-v1"


def _sha256_json(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return value.strip()


def _verify_digest(record: dict, digest_field: str, label: str) -> None:
    digest = record.get(digest_field)
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"{label} must contain a SHA-256 digest in {digest_field}")
    payload = copy.deepcopy(record)
    payload.pop(digest_field, None)
    if _sha256_json(payload) != digest.lower():
        raise ValueError(f"{label} SHA-256 digest mismatch")


def normalize_binance_live_depth_evidence(
    artifact: dict,
    *,
    symbol: str,
    quote_asset: str,
) -> dict:
    """Return a report-compatible snapshot for one symbol from a preserved artifact.

    This requires a fully passing batch and verified hashes. A synchronized book
    does not imply that any freshness threshold is approved or that liquidity is
    executable; the output explicitly preserves those limitations.
    """
    if not isinstance(artifact, dict) or artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    _verify_digest(artifact, "artifact_sha256", "live depth artifact")
    if artifact.get("overall_status") != "PASS":
        raise ValueError("live depth artifact overall_status must be PASS")
    if artifact.get("decision_status") != "INDETERMINATE":
        raise ValueError("live depth artifact must preserve INDETERMINATE decision status")
    if artifact.get("freshness_policy_approved") is not False:
        raise ValueError("live depth artifact must not claim an approved freshness policy")
    if artifact.get("orders_submitted") is not False:
        raise ValueError("live depth artifact must confirm no orders were submitted")
    clock = artifact.get("clock_evidence")
    if not isinstance(clock, dict) or clock.get("status") != "MEASURED":
        raise ValueError("live depth artifact requires measured clock evidence")

    normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
    normalized_quote = quote_asset.strip().upper() if isinstance(quote_asset, str) else ""
    if not normalized_symbol or not normalized_symbol.isascii() or not normalized_symbol.isalnum():
        raise ValueError("symbol must be a non-empty ASCII alphanumeric native market symbol")
    if not normalized_quote or not normalized_quote.isascii() or not normalized_quote.isalnum():
        raise ValueError("quote_asset must be a non-empty ASCII alphanumeric asset code")

    captures = artifact.get("captures")
    if not isinstance(captures, list) or not captures:
        raise ValueError("live depth artifact captures must be a non-empty list")
    for index, capture in enumerate(captures):
        if not isinstance(capture, dict):
            raise ValueError(f"captures[{index}] must be an object")
        _verify_digest(capture, "evidence_sha256", f"captures[{index}]")
        if capture.get("orders_submitted") is not False:
            raise ValueError(f"captures[{index}] must confirm no orders were submitted")
    matches = [item for item in captures if item.get("symbol") == normalized_symbol]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one capture for {normalized_symbol}; found {len(matches)}")
    capture = matches[0]
    if capture.get("status") != "SYNCHRONIZED" or capture.get("read_only") is not True:
        raise ValueError(f"{normalized_symbol} capture must be synchronized and read-only")

    source_event_at = _timestamp(capture.get("source_event_at_utc"), "source_event_at_utc")
    received_at = _timestamp(capture.get("last_event_received_at_utc"), "last_event_received_at_utc")
    evaluated_at = _timestamp(capture.get("evaluated_at_utc"), "evaluated_at_utc")
    started_at = _timestamp(capture.get("capture_started_at_utc"), "capture_started_at_utc")
    completed_at = _timestamp(capture.get("capture_completed_at_utc"), "capture_completed_at_utc")
    observation = capture.get("freshness_observation")
    if not isinstance(observation, dict):
        raise ValueError("freshness_observation must be an object")
    for field in ("source_timestamp_utc", "captured_at_utc", "evaluation_time_utc"):
        _timestamp(observation.get(field), f"freshness_observation.{field}")
    bids = capture.get("bids")
    asks = capture.get("asks")
    if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
        raise ValueError("synchronized capture must contain non-empty bids and asks")

    return {
        "schema_version": OUTPUT_SCHEMA,
        "capture_status": "PASS",
        "provider_id": "binance_spot_market_data",
        "market": {
            "exchange": "binance",
            "market_type": "SPOT",
            "symbol_native": normalized_symbol,
            "quote_asset": normalized_quote,
        },
        "captured_at_utc": evaluated_at,
        "bids": copy.deepcopy(bids),
        "asks": copy.deepcopy(asks),
        "source_evidence": {
            "schema_version": INPUT_SCHEMA,
            "artifact_sha256": artifact["artifact_sha256"],
            "capture_evidence_sha256": capture["evidence_sha256"],
            "source_event_at_utc": source_event_at,
            "last_event_received_at_utc": received_at,
            "capture_started_at_utc": started_at,
            "capture_completed_at_utc": completed_at,
            "evaluated_at_utc": evaluated_at,
            "freshness_observation": copy.deepcopy(observation),
            "freshness_policy_status": "NOT_APPROVED",
            "freshness_conclusion": "NOT_ASSESSED",
            "clock_evidence_status": clock["status"],
        },
        "limitations": [
            "Transport synchronization and hash verification do not establish a freshness pass.",
            "No approved freshness threshold is present; the research decision must remain INDETERMINATE.",
            "The selected quote asset is supplied by the caller and is not inferred from the native symbol.",
            "Visible orders can change or be cancelled and are not guaranteed executable liquidity.",
            "This conversion performs no network requests and submits no orders.",
        ],
        "orders_submitted": False,
    }


__all__ = ["normalize_binance_live_depth_evidence"]
