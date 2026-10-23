"""Normalize one preserved multi-exchange Spot book probe for research analysis.

The adapter never trusts authorization claims embedded in the probe. It verifies the
selected response bytes and re-evaluates internal-analysis permission against the
deployment-controlled provider authorization registry.
"""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from scripts.market_selection.capture_multi_exchange_spot_book_probe import (
    PROVIDER_IDS,
    SCHEMA_VERSION as PROBE_SCHEMA_VERSION,
    build_requests,
    extract_top_of_book,
)
from scripts.market_selection.provider_license_gate import evaluate_provider_use

OUTPUT_SCHEMA = "crypto-spot-order-book-snapshot-v1"


def normalize_multi_exchange_order_book_probe(
    artifact: dict,
    *,
    exchange: str,
    symbol: str,
    authorization_registry: dict | None = None,
) -> dict:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != PROBE_SCHEMA_VERSION:
        raise ValueError(f"expected schema_version {PROBE_SCHEMA_VERSION}")
    if not isinstance(artifact.get("records"), list):
        raise ValueError("probe.records must be a list")
    if not isinstance(exchange, str) or not exchange.strip():
        raise ValueError("exchange must be a non-empty string")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string")
    exchange_key = exchange.strip().lower()
    symbol_key = symbol.strip().upper()
    if exchange_key not in PROVIDER_IDS:
        raise ValueError(f"unsupported exchange: {exchange_key}")

    matches = [
        record for record in artifact["records"]
        if isinstance(record, dict)
        and str(record.get("exchange", "")).strip().lower() == exchange_key
        and str(record.get("symbol", "")).strip().upper() == symbol_key
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one probe record for {exchange_key}:{symbol_key}; found {len(matches)}")
    record = matches[0]
    expected_spec = next(
        (spec for spec in build_requests()
         if spec["exchange"] == exchange_key and spec["symbol"].upper() == symbol_key),
        None,
    )
    if expected_spec is None:
        raise ValueError(f"no registered probe request for {exchange_key}:{symbol_key}")
    if record.get("url") != expected_spec["url"] or record.get("asset") != expected_spec["asset"]:
        raise ValueError("selected probe record URL or asset does not match the registered request")
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        raise ValueError("selected probe record must be a successful HTTP 200 capture")
    if record.get("error_type") is not None:
        raise ValueError("selected probe record contains an error")

    encoded = record.get("response_base64")
    digest = record.get("response_sha256")
    response_bytes = record.get("response_bytes")
    if not isinstance(encoded, str) or not isinstance(digest, str):
        raise ValueError("selected probe record is missing preserved response bytes or SHA-256")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("selected probe response Base64 is invalid") from exc
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("selected probe response SHA-256 mismatch")
    if isinstance(response_bytes, bool) or not isinstance(response_bytes, int) or response_bytes != len(raw):
        raise ValueError("selected probe response byte count mismatch")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("selected probe response is not valid UTF-8 JSON") from exc
    if payload != record.get("parsed_json"):
        raise ValueError("selected probe parsed_json does not match preserved response bytes")

    bids, asks, source_timestamp = extract_top_of_book(exchange_key, payload)
    if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
        raise ValueError("selected probe response has no non-empty bids/asks")

    provider_id = PROVIDER_IDS[exchange_key]
    if not isinstance(authorization_registry, dict):
        authorization_registry = {}
    try:
        assessment = evaluate_provider_use(
            provider_id, "internal_analysis", authorization_registry.get(provider_id),
        )
    except ValueError as exc:
        raise PermissionError("trusted provider authorization record is invalid") from exc
    if assessment.get("decision") != "ALLOW":
        raise PermissionError(
            "order-book normalization blocked before analysis: "
            + ",".join(assessment.get("reason_codes") or ["PROVIDER_USE_BLOCKED"])
        )

    captured_at = record.get("captured_at_utc")
    if not isinstance(captured_at, str) or not captured_at.strip():
        raise ValueError("selected probe record captured_at_utc is required")
    return {
        "schema_version": OUTPUT_SCHEMA,
        "capture_status": "PASS",
        "provider_id": provider_id,
        "market": {
            "exchange": exchange_key,
            "market_type": "SPOT",
            "symbol_native": str(record.get("symbol")).strip(),
            "base_asset": record.get("asset"),
            "quote_asset": "USDT",
        },
        "captured_at_utc": captured_at,
        "source_timestamp_raw": source_timestamp,
        "bids": bids,
        "asks": asks,
        "provider_use_assessment": record.get("provider_use_assessment"),
        "analysis_provider_use_assessment": assessment,
        "capture_evidence": {
            "response_bytes": len(raw),
            "response_sha256": digest,
            "source_response_integrity": "VERIFIED",
            "source_record_sha256": hashlib.sha256(
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        },
        "source_capture_status": artifact.get("overall_status"),
        "orders_submitted": False,
    }
