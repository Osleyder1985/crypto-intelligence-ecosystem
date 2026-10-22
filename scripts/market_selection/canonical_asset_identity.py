"""Fail-closed stable crypto-asset identity contract (offline; no provider calls).

Ticker symbols are labels, not canonical identities. This module accepts an explicit
chain namespace/reference plus asset namespace/reference and source evidence.
"""
from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import urlsplit

SCHEMA_VERSION = "crypto-canonical-asset-identity-v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _timestamp(value: object, field: str) -> str:
    raw = _text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return raw


def assess_canonical_asset_identity(record: dict) -> dict:
    """Validate identity evidence; never resolve an asset from ticker/name alone."""
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")

    ticker = record.get("ticker")
    if ticker is not None:
        ticker = _text(ticker, "ticker").upper()

    # Missing chain/asset coordinates are a legitimate unresolved state, not an error
    # and must never be silently filled from the ticker or market symbol.
    required_identity = ("chain_namespace", "chain_reference", "asset_namespace", "asset_reference")
    missing = [key for key in required_identity if not isinstance(record.get(key), str) or not record[key].strip()]
    if missing:
        return {
            "schema_version": "crypto-canonical-asset-identity-assessment-v1",
            "identity_status": "NOT_RESOLVED",
            "canonical_asset_id": None,
            "ticker": ticker,
            "reason_codes": ["CANONICAL_ID_COMPONENTS_MISSING"],
            "missing_components": missing,
            "evidence_status": "NOT_ASSESSED",
        }

    chain_namespace = _text(record["chain_namespace"], "chain_namespace").lower()
    chain_reference = _text(record["chain_reference"], "chain_reference")
    asset_namespace = _text(record["asset_namespace"], "asset_namespace").lower()
    asset_reference = _text(record["asset_reference"], "asset_reference")
    if not _TOKEN.fullmatch(chain_namespace):
        raise ValueError("chain_namespace has invalid syntax")
    if not _TOKEN.fullmatch(asset_namespace):
        raise ValueError("asset_namespace has invalid syntax")
    if any(ch.isspace() for ch in chain_reference + asset_reference):
        raise ValueError("chain_reference and asset_reference must not contain whitespace")

    provider = _text(record.get("provider"), "provider")
    source_url = _text(record.get("source_url"), "source_url")
    parsed_url = urlsplit(source_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("source_url must be an absolute HTTPS URL")
    evidence_sha256 = _text(record.get("evidence_sha256"), "evidence_sha256").lower()
    if not _SHA256.fullmatch(evidence_sha256):
        raise ValueError("evidence_sha256 must be 64 hexadecimal characters")
    captured_at = _timestamp(record.get("captured_at"), "captured_at")
    observed_at = _timestamp(record.get("observed_at"), "observed_at")

    canonical_id = f"{chain_namespace}:{chain_reference}/{asset_namespace}:{asset_reference}"
    return {
        "schema_version": "crypto-canonical-asset-identity-assessment-v1",
        "identity_status": "RESOLVED",
        "canonical_asset_id": canonical_id,
        "ticker": ticker,
        "reason_codes": [],
        "missing_components": [],
        "evidence_status": "PRESENT",
        "evidence": {
            "provider": provider,
            "source_url": source_url,
            "evidence_sha256": evidence_sha256,
            "captured_at": captured_at,
            "observed_at": observed_at,
        },
        "identity_basis": "EXPLICIT_CHAIN_AND_ASSET_COORDINATES",
        "ticker_used_as_identity": False,
    }
