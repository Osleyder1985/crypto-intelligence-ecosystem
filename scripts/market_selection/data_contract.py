"""Normalized, provenance-preserving market data contract (v1)."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any

CONTRACT_VERSION = "market-observation-v1"
QUALITY_STATES = {"VALID", "INVALID", "INDETERMINATE"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_timestamp(value: Any, field: str, *, allow_none: bool = False) -> datetime | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def sha256_hex(payload: bytes) -> str:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    return hashlib.sha256(payload).hexdigest()


def canonical_payload_hash(payload: Any) -> str:
    """Hash canonical JSON when original response bytes are unavailable."""
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_hex(encoded)


def validate_observation(record: Any) -> list[str]:
    """Return contract violations; an empty list means structural validity only."""
    if not isinstance(record, dict):
        return ["observation must be an object"]
    errors: list[str] = []
    required = (
        "contract_version", "observation_id", "exchange_id", "market_type",
        "symbol_native", "base_asset", "quote_asset", "source_kind",
        "source_ref", "source_timestamp_utc", "captured_at_utc",
        "payload_sha256", "parser_version", "quality_status", "limitations",
        "bids", "asks",
    )
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors
    if record["contract_version"] != CONTRACT_VERSION:
        errors.append("unsupported contract_version")
    for key in ("observation_id", "exchange_id", "symbol_native", "base_asset",
                "quote_asset", "source_kind", "source_ref", "parser_version"):
        if not isinstance(record[key], str) or not record[key].strip():
            errors.append(f"{key} must be a non-empty string")
    if record["market_type"] != "spot":
        errors.append("market_type must be 'spot'")
    if record["quality_status"] not in QUALITY_STATES:
        errors.append("quality_status is invalid")
    if not isinstance(record["limitations"], list) or not all(
        isinstance(item, str) for item in record["limitations"]
    ):
        errors.append("limitations must be a list of strings")
    digest = record["payload_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest
    ):
        errors.append("payload_sha256 must be a lowercase SHA-256 hex digest")
    try:
        parse_timestamp(record["captured_at_utc"], "captured_at_utc")
    except ValueError as exc:
        errors.append(str(exc))
    try:
        parse_timestamp(record["source_timestamp_utc"], "source_timestamp_utc", allow_none=True)
    except ValueError as exc:
        errors.append(str(exc))
    for side in ("bids", "asks"):
        levels = record[side]
        if not isinstance(levels, list) or not levels:
            errors.append(f"{side} must be a non-empty list")
            continue
        seen: set[float] = set()
        for index, level in enumerate(levels):
            if not isinstance(level, dict):
                errors.append(f"{side}[{index}] must be an object")
                continue
            price, quantity = level.get("price"), level.get("quantity")
            valid = all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) and v > 0 for v in (price, quantity))
            if not valid:
                errors.append(f"{side}[{index}] price and quantity must be finite positive numbers")
                continue
            if float(price) in seen:
                errors.append(f"{side} contains duplicate price levels")
            seen.add(float(price))
    return errors
