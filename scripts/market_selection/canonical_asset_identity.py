"""Fail-closed canonical crypto-asset identity contract.

Market base-symbol mapping is not canonical identity. This module validates supplied,
reviewed identity evidence; it does not query registries or infer identities from tickers.
"""
from __future__ import annotations

from datetime import datetime
import re
from typing import Any
from urllib.parse import urlsplit

SCHEMA_VERSION = "crypto-canonical-asset-identity-v1"
SUPPORTED_IDENTIFIER_TYPES = {"symbol", "canonical_id", "contract_address", "name"}
SUPPORTED_ASSET_TYPES = {"NATIVE_ASSET", "TOKEN", "WRAPPED_ASSET"}
SUPPORTED_SOURCE_TYPES = {"PRIMARY_OFFICIAL", "AUTHORITATIVE_REGISTRY"}
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    raw = _text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return raw


def _sha256(value: Any, field: str) -> str:
    raw = _text(value, field)
    if not _SHA256.fullmatch(raw):
        raise ValueError(f"{field} must be a 64-character SHA-256")
    return raw.lower()


def _unresolved(requested: dict, mapping_status: str, reason: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "requested_identifier": requested,
        "asset_identity_status": "INDETERMINATE",
        "canonical_asset_identity_status": "NOT_RESOLVED",
        "market_base_asset_mapping_status": mapping_status,
        "resolution_status": "NOT_RESOLVED",
        "stable_id": None,
        "identity_evidence": None,
        "reason_codes": [reason],
    }


def resolve_asset_identity(
    requested_identifier: dict,
    market: dict,
    identity_evidence: dict | None = None,
) -> dict:
    """Resolve an explicit identifier only from reviewed, unique identity evidence.

    A matching market base ticker proves only that the selected market metadata names
    that base asset. It does not by itself establish canonical identity across networks.
    """
    if not isinstance(requested_identifier, dict):
        raise ValueError("requested_identifier must be an object")
    if not isinstance(market, dict):
        raise ValueError("market must be an object")

    identifier_type = _text(requested_identifier.get("type"), "requested_identifier.type")
    if identifier_type not in SUPPORTED_IDENTIFIER_TYPES:
        raise ValueError(f"unsupported requested identifier type: {identifier_type}")
    identifier_value = _text(requested_identifier.get("value"), "requested_identifier.value")
    requested_chain = requested_identifier.get("chain_id")
    if requested_chain is not None:
        requested_chain = _text(requested_chain, "requested_identifier.chain_id")
    requested = {"type": identifier_type, "value": identifier_value, "chain_id": requested_chain}

    market_base = market.get("base_asset") or market.get("asset_id")
    market_base = market_base.strip() if isinstance(market_base, str) and market_base.strip() else None
    if identifier_type == "symbol" and market_base:
        mapping_status = "VERIFIED" if market_base.casefold() == identifier_value.casefold() else "MISMATCH"
    else:
        mapping_status = "INDETERMINATE"

    if identity_evidence is None:
        if mapping_status == "MISMATCH":
            return {
                **_unresolved(requested, mapping_status, "REQUESTED_SYMBOL_DOES_NOT_MATCH_MARKET_BASE"),
                "canonical_asset_identity_status": "CONFLICT",
                "resolution_status": "CONFLICT",
            }
        return _unresolved(requested, mapping_status, "CANONICAL_IDENTITY_EVIDENCE_MISSING")

    evidence = identity_evidence
    if not isinstance(evidence, dict):
        raise ValueError("identity_evidence must be an object")
    if evidence.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"identity_evidence.schema_version must be {SCHEMA_VERSION}")

    stable_id = _text(evidence.get("stable_id"), "identity_evidence.stable_id")
    asset_type = _text(evidence.get("asset_type"), "identity_evidence.asset_type")
    if asset_type not in SUPPORTED_ASSET_TYPES:
        raise ValueError(f"unsupported identity_evidence.asset_type: {asset_type}")
    symbol = _text(evidence.get("symbol"), "identity_evidence.symbol")
    name = _text(evidence.get("name"), "identity_evidence.name")
    chain_id = _text(evidence.get("chain_id"), "identity_evidence.chain_id")
    contract_address = evidence.get("contract_address")
    if contract_address is not None:
        contract_address = _text(contract_address, "identity_evidence.contract_address")
    if asset_type in {"TOKEN", "WRAPPED_ASSET"} and not contract_address:
        raise ValueError("token and wrapped-asset evidence must include contract_address and chain_id")
    if asset_type == "NATIVE_ASSET" and contract_address:
        raise ValueError("native-asset evidence must not use a token contract_address")

    resolution = evidence.get("resolution")
    if not isinstance(resolution, dict):
        raise ValueError("identity_evidence.resolution must be an object")
    resolution_status = _text(resolution.get("status"), "identity_evidence.resolution.status")
    candidate_count = resolution.get("candidate_count")
    if isinstance(candidate_count, bool) or not isinstance(candidate_count, int) or candidate_count < 1:
        raise ValueError("identity_evidence.resolution.candidate_count must be a positive integer")
    review_status = _text(resolution.get("review_status"), "identity_evidence.resolution.review_status")
    reviewed_by = _text(resolution.get("reviewed_by"), "identity_evidence.resolution.reviewed_by")
    reviewed_at = _timestamp(resolution.get("reviewed_at"), "identity_evidence.resolution.reviewed_at")

    source = evidence.get("source")
    if not isinstance(source, dict):
        raise ValueError("identity_evidence.source must be an object")
    source_type = _text(source.get("source_type"), "identity_evidence.source.source_type")
    if source_type not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(f"unsupported identity source type: {source_type}")
    source_url = _text(source.get("url"), "identity_evidence.source.url")
    parsed_url = urlsplit(source_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("identity_evidence.source.url must be an absolute HTTPS URL")
    publisher = _text(source.get("publisher"), "identity_evidence.source.publisher")
    captured_at = _timestamp(source.get("captured_at"), "identity_evidence.source.captured_at")
    content_sha256 = _sha256(source.get("content_sha256"), "identity_evidence.source.content_sha256")

    sanitized_evidence = {
        "stable_id": stable_id,
        "asset_type": asset_type,
        "symbol": symbol,
        "name": name,
        "chain_id": chain_id,
        "contract_address": contract_address,
        "resolution": {
            "status": resolution_status,
            "candidate_count": candidate_count,
            "review_status": review_status,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
        },
        "source": {
            "source_type": source_type,
            "url": source_url,
            "publisher": publisher,
            "captured_at": captured_at,
            "content_sha256": content_sha256,
        },
    }

    if market_base:
        mapping_status = "VERIFIED" if market_base.casefold() == symbol.casefold() else "MISMATCH"
    else:
        mapping_status = "INDETERMINATE"

    if resolution_status != "VERIFIED_UNIQUE" or candidate_count != 1 or review_status != "APPROVED":
        return {
            "schema_version": SCHEMA_VERSION,
            "requested_identifier": requested,
            "asset_identity_status": "INDETERMINATE",
            "canonical_asset_identity_status": "NOT_RESOLVED",
            "market_base_asset_mapping_status": mapping_status,
            "resolution_status": "NOT_RESOLVED",
            "stable_id": None,
            "identity_evidence": sanitized_evidence,
            "reason_codes": ["IDENTITY_NOT_UNIQUE_OR_NOT_APPROVED"],
        }

    if mapping_status == "MISMATCH":
        return {
            "schema_version": SCHEMA_VERSION,
            "requested_identifier": requested,
            "asset_identity_status": "INDETERMINATE",
            "canonical_asset_identity_status": "CONFLICT",
            "market_base_asset_mapping_status": mapping_status,
            "resolution_status": "CONFLICT",
            "stable_id": stable_id,
            "identity_evidence": sanitized_evidence,
            "reason_codes": ["MARKET_BASE_SYMBOL_CONFLICTS_WITH_IDENTITY_EVIDENCE"],
        }

    matches = False
    if identifier_type == "symbol":
        matches = identifier_value.casefold() == symbol.casefold()
    elif identifier_type == "canonical_id":
        matches = identifier_value == stable_id
    elif identifier_type == "name":
        matches = identifier_value.casefold() == name.casefold()
    elif identifier_type == "contract_address":
        matches = bool(contract_address) and identifier_value == contract_address
        if requested_chain is None or requested_chain != chain_id:
            matches = False

    if not matches:
        return {
            "schema_version": SCHEMA_VERSION,
            "requested_identifier": requested,
            "asset_identity_status": "INDETERMINATE",
            "canonical_asset_identity_status": "CONFLICT",
            "market_base_asset_mapping_status": mapping_status,
            "resolution_status": "CONFLICT",
            "stable_id": stable_id,
            "identity_evidence": sanitized_evidence,
            "reason_codes": ["REQUESTED_IDENTIFIER_CONFLICTS_WITH_IDENTITY_EVIDENCE"],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "requested_identifier": requested,
        "asset_identity_status": "VERIFIED",
        "canonical_asset_identity_status": "VERIFIED",
        "market_base_asset_mapping_status": mapping_status,
        "resolution_status": "VERIFIED_UNIQUE",
        "stable_id": stable_id,
        "identity_evidence": sanitized_evidence,
        "reason_codes": ["UNIQUE_REVIEWED_IDENTITY_EVIDENCE_MATCH"],
    }
