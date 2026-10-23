"""Versioned fundamental/on-chain metric contracts and fail-closed evidence evaluation.

This module validates supplied observations offline. It does not fetch data or imply that a
metric is universally comparable across assets, chains, protocols, or providers.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from urllib.parse import urlsplit

CATALOG_SCHEMA = "crypto-fundamental-metric-catalog-v1"
OBSERVATION_SCHEMA = "crypto-fundamental-observation-v1"
ASSESSMENT_SCHEMA = "crypto-fundamental-assessment-v1"

METRIC_CATALOG = {
    "supply.max": {
        "unit": "token",
        "categories": ["native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "meme", "oracle", "gaming", "rwa"],
        "applicability": "CONDITIONAL",
        "definition": "Protocol-defined maximum supply, if a meaningful finite maximum exists.",
        "caveat": "An unbounded or governance-adjustable supply is not zero and may have no meaningful maximum.",
        "source_classes": ["protocol_docs", "onchain", "market_data_provider"],
    },
    "supply.circulating": {
        "unit": "token",
        "categories": ["native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "meme", "oracle", "gaming", "rwa"],
        "applicability": "APPLICABLE",
        "definition": "Provider-defined circulating supply at a stated observation time.",
        "caveat": "Methodologies differ on treasury, locked, bridged, burned, and vesting balances; preserve provider methodology.",
        "source_classes": ["onchain", "protocol_docs", "market_data_provider"],
    },
    "supply.unlock_schedule": {
        "unit": "token",
        "categories": ["smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "meme", "oracle", "gaming", "rwa"],
        "applicability": "CONDITIONAL",
        "definition": "Future scheduled token releases with a dated schedule and source.",
        "caveat": "Schedules may change; distinguish scheduled, estimated, and confirmed unlocks.",
        "source_classes": ["protocol_docs", "vesting_contract", "specialist_provider"],
    },
    "distribution.holder_concentration": {
        "unit": "fraction",
        "categories": ["native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "meme", "oracle", "gaming", "rwa"],
        "applicability": "CONDITIONAL",
        "definition": "Concentration metric with explicit holder universe, exclusions, and snapshot block.",
        "caveat": "Addresses are not necessarily beneficial owners; exchange, bridge, burn, vesting and contract addresses can distort concentration.",
        "source_classes": ["onchain", "specialist_provider"],
    },
    "network.active_addresses": {
        "unit": "address_count",
        "categories": ["native_l1", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Active addresses over a specified chain, activity rule, and time window.",
        "caveat": "Addresses are not people; contract and account abstraction models affect comparability.",
        "source_classes": ["node_rpc", "indexer", "specialist_provider"],
    },
    "network.transaction_count": {
        "unit": "transaction_count",
        "categories": ["native_l1", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Transactions counted under a stated chain and inclusion rule over a defined interval.",
        "caveat": "Transactions, internal calls, rollup batches and failed transactions may be counted differently.",
        "source_classes": ["node_rpc", "indexer", "explorer"],
    },
    "network.fees_paid": {
        "unit": "native_or_usd",
        "categories": ["native_l1", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Fees paid for activity, with unit, conversion source, interval, and chain specified.",
        "caveat": "Fees paid by users are not equivalent to protocol revenue or token-holder value capture.",
        "source_classes": ["node_rpc", "indexer", "explorer", "specialist_provider"],
    },
    "protocol.tvl": {
        "unit": "usd",
        "categories": ["defi_protocol_token", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Value of assets held in a specifically identified protocol under a declared methodology.",
        "caveat": "TVL is protocol-level, may be double-counted across composable protocols, and is not automatically token value.",
        "source_classes": ["protocol_contracts", "specialist_provider"],
    },
    "protocol.fees": {
        "unit": "usd",
        "categories": ["defi_protocol_token", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Fees paid by users to use a named protocol over a stated interval.",
        "caveat": "Gross user fees are distinct from protocol revenue and token-holder distributions.",
        "source_classes": ["protocol_contracts", "specialist_provider"],
    },
    "protocol.revenue": {
        "unit": "usd",
        "categories": ["defi_protocol_token", "smart_contract_token"],
        "applicability": "CONDITIONAL",
        "definition": "Protocol-retained fees/revenue under a declared methodology and interval.",
        "caveat": "Must not be substituted with gross fees or token emissions.",
        "source_classes": ["protocol_contracts", "specialist_provider"],
    },
    "security.audit_status": {
        "unit": "categorical",
        "categories": ["native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "oracle", "gaming", "rwa"],
        "applicability": "APPLICABLE",
        "definition": "Evidence of a named audit/security review, scope, date, auditor, and findings.",
        "caveat": "An audit is not proof of safety; absence of evidence is not proof that no audit exists.",
        "source_classes": ["auditor_report", "protocol_docs"],
    },
    "security.incident_history": {
        "unit": "event_count_or_records",
        "categories": ["native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token", "exchange_token", "oracle", "gaming", "rwa"],
        "applicability": "APPLICABLE",
        "definition": "Documented security incidents with affected component, date, impact, and source.",
        "caveat": "Counts require a declared period and source coverage; incomplete records cannot establish zero incidents.",
        "source_classes": ["incident_postmortem", "security_advisory", "reputable_media"],
    },
    "stablecoin.reserve_attestation": {
        "unit": "categorical_or_usd",
        "categories": ["stablecoin"],
        "applicability": "APPLICABLE",
        "definition": "Reserve/attestation evidence with as-of date, scope, issuer, auditor/attestor and asset breakdown.",
        "caveat": "An attestation is not necessarily a full audit; reserve composition, liabilities and redemption rights matter.",
        "source_classes": ["issuer_report", "auditor_report", "regulatory_filing"],
    },
    "staking.validator_concentration": {
        "unit": "fraction",
        "categories": ["native_l1", "liquid_staking"],
        "applicability": "CONDITIONAL",
        "definition": "Share of stake/validators under a defined entity attribution and snapshot.",
        "caveat": "Validator addresses and operators may not map one-to-one; attribution is uncertain.",
        "source_classes": ["consensus_api", "node_rpc", "specialist_provider"],
    },
    "liquid_staking.exchange_rate": {
        "unit": "ratio",
        "categories": ["liquid_staking"],
        "applicability": "APPLICABLE",
        "definition": "Exchange rate between the liquid staking token and its underlying asset at a stated block/time.",
        "caveat": "Do not compare with USD price without the underlying asset conversion and depeg context.",
        "source_classes": ["protocol_contracts", "onchain"],
    },
}

VALID_STATUSES = {
    "OBSERVED", "NOT_APPLICABLE", "NOT_AVAILABLE", "INACCESSIBLE",
    "STALE", "PARTIAL", "PROVIDER_ERROR", "CONFLICT",
}


def parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return result.astimezone(timezone.utc)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _http_url(value: object, field: str) -> str:
    url = _string(value, field)
    parsed = urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    return url


def validate_observation(item: object) -> dict:
    if not isinstance(item, dict):
        raise ValueError("observation must be an object")
    if item.get("schema_version") != OBSERVATION_SCHEMA:
        raise ValueError(f"schema_version must be {OBSERVATION_SCHEMA}")
    metric_id = _string(item.get("metric_id"), "metric_id")
    if metric_id not in METRIC_CATALOG:
        raise ValueError(f"unknown metric_id: {metric_id}")
    asset = item.get("asset")
    if not isinstance(asset, dict):
        raise ValueError("asset must be an object")
    category = _string(asset.get("category"), "asset.category")
    asset_id = _string(asset.get("stable_id"), "asset.stable_id")
    if category not in {"native_l1", "smart_contract_token", "stablecoin", "defi_protocol_token",
                        "exchange_token", "meme", "oracle", "gaming", "rwa", "liquid_staking",
                        "privacy", "gaming", "other"}:
        raise ValueError("asset.category is not in the versioned category vocabulary")
    metric = METRIC_CATALOG[metric_id]
    status = _string(item.get("status"), "status")
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    value = item.get("value")
    unit = _string(item.get("unit"), "unit")
    if status == "OBSERVED":
        if value is None:
            raise ValueError("OBSERVED requires a value; use an explicit non-observed status for missing data")
        if unit != metric["unit"]:
            raise ValueError(f"unit must match catalog unit {metric['unit']}")
        categorical_units = {"categorical", "categorical_or_usd", "event_count_or_records"}
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError("value must be a finite number or a categorical string")
        if isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError("numeric value must be finite")
        if unit in categorical_units and not isinstance(value, str):
            raise ValueError("categorical metric values must be strings")
        if unit not in categorical_units and not isinstance(value, (int, float)):
            raise ValueError("quantitative metric values must be numeric")
        if isinstance(value, str) and not value.strip():
            raise ValueError("categorical value must be non-empty")
        if unit == "fraction" and not 0 <= value <= 1:
            raise ValueError("fraction values must be between 0 and 1")
        if category not in metric["categories"]:
            raise ValueError(f"metric {metric_id} is not defined as applicable for category {category}")
    else:
        if value is not None:
            raise ValueError(f"{status} observations must use value=null, never a fabricated zero")
        if status == "NOT_APPLICABLE" and category in metric["categories"] and not _string(
            item.get("applicability_override_reason"), "applicability_override_reason"
        ):
            raise ValueError(f"{metric_id} is listed for category {category}; NOT_APPLICABLE requires a documented applicability_override_reason")
    source = item.get("source")
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    source_id = _string(source.get("source_id"), "source.source_id")
    source_type = _string(source.get("source_type"), "source.source_type")
    source_url = _http_url(source.get("url"), "source.url")
    methodology_url = source.get("methodology_url")
    if methodology_url is not None:
        methodology_url = _http_url(methodology_url, "source.methodology_url")
    raw_published_at = item.get("published_at")
    publication_time_status = item.get(
        "publication_time_status", "KNOWN" if raw_published_at is not None else "UNKNOWN"
    )
    if publication_time_status not in {"KNOWN", "UNKNOWN", "NOT_PROVIDED"}:
        raise ValueError("publication_time_status must be KNOWN, UNKNOWN, or NOT_PROVIDED")
    if publication_time_status == "KNOWN":
        published_at = parse_timestamp(raw_published_at, "published_at")
    else:
        if raw_published_at is not None:
            raise ValueError("published_at must be null when publication_time_status is not KNOWN")
        published_at = None
    observed_at = parse_timestamp(item.get("observed_at"), "observed_at")
    captured_at = parse_timestamp(item.get("captured_at"), "captured_at")
    if captured_at < observed_at:
        raise ValueError("captured_at cannot precede observed_at")
    if published_at is not None and published_at > captured_at:
        raise ValueError("published_at cannot be after captured_at")
    return {
        "schema_version": OBSERVATION_SCHEMA,
        "observation_id": _string(item.get("observation_id"), "observation_id"),
        "asset": {"category": category, "stable_id": asset_id},
        "metric_id": metric_id,
        "status": status,
        "value": value,
        "unit": unit,
        "period_start": item.get("period_start"),
        "period_end": item.get("period_end"),
        "block_height": item.get("block_height"),
        "published_at": published_at.isoformat().replace("+00:00", "Z") if published_at else None,
        "publication_time_status": publication_time_status,
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
        "source": {
            "source_id": source_id,
            "source_type": source_type,
            "url": source_url,
            "methodology_url": methodology_url,
            "terms_status": _string(source.get("terms_status", "UNKNOWN"), "source.terms_status"),
        },
        "quality_notes": item.get("quality_notes", ""),
        "applicability_override_reason": item.get("applicability_override_reason"),
        "metadata": item.get("metadata", {}) if isinstance(item.get("metadata", {}), dict) else {},
    }


def evaluate_observations(observations: list[dict], *, asset: dict, evaluation_as_of: str) -> dict:
    """Evaluate a single stable asset and cutoff; conflicts are not silently resolved."""
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    if not isinstance(asset, dict):
        raise ValueError("asset must be an object")
    target_category = _string(asset.get("category"), "asset.category")
    target_id = _string(asset.get("stable_id"), "asset.stable_id")
    cutoff = parse_timestamp(evaluation_as_of, "evaluation_as_of")
    validated = [validate_observation(o) for o in observations]
    groups: dict[str, list[dict]] = {}
    rejected_future = []
    for obs in validated:
        if obs["asset"]["stable_id"].casefold() != target_id.casefold() or obs["asset"]["category"] != target_category:
            raise ValueError("all observations must match the exact target stable_id and category")
        time_fields = ("observed_at", "captured_at")
        if obs["published_at"] is not None:
            time_fields = ("published_at",) + time_fields
        if any(parse_timestamp(obs[field], field) > cutoff for field in time_fields):
            rejected_future.append(obs["observation_id"])
            continue
        groups.setdefault(obs["metric_id"], []).append(obs)

    metrics = {}
    for metric_id, definition in METRIC_CATALOG.items():
        applicable = target_category in definition["categories"]
        entries = groups.get(metric_id, [])
        observed = [e for e in entries if e["status"] == "OBSERVED"]
        explicit_statuses = {e["status"] for e in entries}
        if "CONFLICT" in explicit_statuses:
            # An explicit source conflict cannot be erased by another source's observed value.
            status, value = "CONFLICT", None
        elif len(observed) > 1:
            values = {(type(e["value"]).__name__, json.dumps(e["value"], sort_keys=True)) for e in observed}
            if len(values) > 1:
                status, value = "CONFLICT", None
            else:
                # Multiple sources agree on the value; retain all source evidence.
                status, value = "OBSERVED", observed[0]["value"]
        elif len(observed) == 1:
            status, value = "OBSERVED", observed[0]["value"]
        elif entries:
            # Preserve the most conservative explicit missing-data state; never coerce to zero.
            priority = ["PROVIDER_ERROR", "INACCESSIBLE", "PARTIAL", "STALE", "NOT_AVAILABLE", "NOT_APPLICABLE"]
            status = next((s for s in priority if s in explicit_statuses), "NOT_AVAILABLE")
            value = None
        elif not applicable:
            status, value = "NOT_APPLICABLE", None
        else:
            status, value = "NOT_AVAILABLE", None
        metrics[metric_id] = {
            "status": status,
            "value": value,
            "unit": definition["unit"],
            "applicable_to_category": applicable,
            "observation_ids": [e["observation_id"] for e in entries],
            "source_ids": sorted({e["source"]["source_id"] for e in entries}),
            "definition": definition["definition"],
            "caveat": definition["caveat"],
        }
    available = sum(1 for x in metrics.values() if x["status"] == "OBSERVED")
    applicable_count = sum(1 for x in metrics.values() if x["applicable_to_category"])
    return {
        "schema_version": ASSESSMENT_SCHEMA,
        "asset": {"category": target_category, "stable_id": target_id},
        "evaluation_as_of": cutoff.isoformat().replace("+00:00", "Z"),
        "decision_status": "INDETERMINATE",
        "coverage": {
            "catalog_metric_count": len(METRIC_CATALOG),
            "applicable_metric_count": applicable_count,
            "observed_metric_count": available,
            "applicable_coverage_ratio": available / applicable_count if applicable_count else None,
            "rejected_after_cutoff_observation_ids": rejected_future,
        },
        "metrics": metrics,
        "interpretation": "No investment conclusion is computed by this contract; coverage, methodology, comparability and validation are prerequisites.",
    }


def adapt_defillama_protocol_tvl(
    payload: object,
    *,
    protocol_slug: str,
    asset_category: str,
    asset_stable_id: str,
    captured_at: str,
    mapping_evidence_url: str,
    terms_status: str = "REVIEW_PENDING",
) -> list[dict]:
    """Normalize a captured DefiLlama protocol response into protocol-TVL observations.

    This is an offline adapter for a previously captured response, not a network client.
    The caller must provide evidence linking the asset to the protocol; TVL is protocol-level,
    not a direct measure of token value or token-holder revenue.
    """
    import re
    from datetime import timedelta

    slug = _string(protocol_slug, "protocol_slug")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ValueError("protocol_slug must be a normalized lowercase slug")
    category = _string(asset_category, "asset_category")
    stable_id = _string(asset_stable_id, "asset_stable_id")
    if category not in METRIC_CATALOG["protocol.tvl"]["categories"]:
        raise ValueError("protocol TVL cannot be attributed to this asset category")
    captured = parse_timestamp(captured_at, "captured_at")
    mapping_url = _http_url(mapping_evidence_url, "mapping_evidence_url")
    if not isinstance(payload, dict) or not isinstance(payload.get("tvl"), list):
        raise ValueError("DefiLlama protocol payload must contain a tvl list")
    points = {}
    for index, point in enumerate(payload["tvl"]):
        if not isinstance(point, dict):
            raise ValueError(f"tvl[{index}] must be an object")
        date = point.get("date")
        value = point.get("totalLiquidityUSD")
        if isinstance(date, bool) or not isinstance(date, (int, float)) or not math.isfinite(date):
            raise ValueError(f"tvl[{index}].date must be a finite Unix timestamp in seconds")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"tvl[{index}].totalLiquidityUSD must be a finite non-negative number")
        observed = datetime.fromtimestamp(date, tz=timezone.utc)
        if observed > captured:
            raise ValueError("DefiLlama TVL sample timestamp cannot be after capture time")
        timestamp = int(date)
        if timestamp in points and points[timestamp] != value:
            raise ValueError("conflicting DefiLlama TVL values for the same timestamp")
        points[timestamp] = value

    source_url = f"https://api.llama.fi/protocol/{slug}"
    methodology_url = "https://defillama.com/data-definitions"
    output = []
    for timestamp, value in sorted(points.items()):
        observed = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        output.append({
            "schema_version": OBSERVATION_SCHEMA,
            "observation_id": f"defillama:{slug}:tvl:{timestamp}",
            "asset": {"category": category, "stable_id": stable_id},
            "metric_id": "protocol.tvl",
            "status": "OBSERVED",
            "value": float(value),
            "unit": "usd",
            "period_start": None,
            "period_end": observed,
            "block_height": None,
            "published_at": None,
            "publication_time_status": "UNKNOWN",
            "observed_at": observed,
            "captured_at": captured.isoformat().replace("+00:00", "Z"),
            "source": {
                "source_id": "defillama-free-api",
                "source_type": "aggregator",
                "url": source_url,
                "methodology_url": methodology_url,
                "terms_status": terms_status,
            },
            "quality_notes": (
                "Protocol-level TVL from a captured response; source publication time is unknown. "
                "TVL is not token value or token-holder revenue."
            ),
            "metadata": {
                "protocol_slug": slug,
                "mapping_evidence_url": mapping_url,
                "mapping_status": "CALLER_SUPPLIED_REQUIRES_REVIEW",
                "api_response_schema": "DefiLlama protocol endpoint; historical tvl array",
            },
        })
    return output


def canonical_sha256(value: object) -> str:
    """Hash canonical JSON, not original provider bytes."""
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
