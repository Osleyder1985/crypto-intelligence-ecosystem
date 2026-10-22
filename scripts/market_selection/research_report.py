"""Assemble existing descriptive OHLCV analyses into a conservative research report.

This is an offline integration step, not a forecast or investment recommendation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.market_selection.analyze_ohlcv_risk_profile import analyze_artifact
from scripts.market_selection.analyze_support_resistance import analyze_support_resistance
from scripts.market_selection.detect_ohlcv_movement_events import analyze_movement_events
try:
    from scripts.market_selection.canonical_asset_identity import resolve_asset_identity
except ModuleNotFoundError:
    from canonical_asset_identity import resolve_asset_identity
try:
    from scripts.market_selection.provider_license_gate import evaluate_artifact_use
except ModuleNotFoundError:
    from provider_license_gate import evaluate_artifact_use

INPUT_SCHEMA = "binance-spot-ohlcv-capture-v1"
REPORT_SCHEMA = "crypto-asset-research-report-v2"
HORIZONS = ("short", "medium", "long")


def _require_object(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_config(config: dict) -> dict:
    config = _require_object(config, "config")
    methodology_id = _require_text(config.get("methodology_id"), "config.methodology_id")
    methodology_version = _require_text(config.get("methodology_version"), "config.methodology_version")
    movement = _require_object(config.get("movement"), "config.movement")
    support_resistance = _require_object(config.get("support_resistance"), "config.support_resistance")

    required_movement = ("lookback_bars", "return_threshold_pct", "volume_ratio_threshold")
    required_sr = ("pivot_left", "pivot_right", "tolerance_bps")
    for key in required_movement:
        if key not in movement:
            raise ValueError(f"config.movement.{key} is required")
    for key in required_sr:
        if key not in support_resistance:
            raise ValueError(f"config.support_resistance.{key} is required")

    return {
        "methodology_id": methodology_id,
        "methodology_version": methodology_version,
        "movement": {
            "lookback_bars": movement["lookback_bars"],
            "return_threshold_pct": movement["return_threshold_pct"],
            "volume_ratio_threshold": movement["volume_ratio_threshold"],
        },
        "support_resistance": {
            "pivot_left": support_resistance["pivot_left"],
            "pivot_right": support_resistance["pivot_right"],
            "tolerance_bps": support_resistance["tolerance_bps"],
        },
    }


def build_research_report(
    artifact: dict,
    config: dict,
    requested_asset_id: str,
    source_bytes: bytes | None = None,
    *,
    requested_identifier_type: str = "symbol",
    requested_chain_id: str | None = None,
    identity_evidence: dict | None = None,
) -> dict:
    """Build a deterministic report from one preserved normalized Spot OHLCV artifact.

    If source_bytes are provided, provenance hashes the exact file bytes. Otherwise,
    the function hashes canonical JSON and labels that weaker provenance basis.
    """
    artifact = _require_object(artifact, "artifact")
    if artifact.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"artifact.schema_version must be {INPUT_SCHEMA}")
    market = _require_object(artifact.get("market"), "artifact.market")
    if market.get("market_type") != "SPOT":
        raise ValueError("artifact.market.market_type must be SPOT")
    exchange = _require_text(market.get("exchange"), "artifact.market.exchange")
    symbol = _require_text(market.get("symbol_native"), "artifact.market.symbol_native")
    interval = _require_text(market.get("interval"), "artifact.market.interval")
    requested_asset_id = _require_text(requested_asset_id, "requested_asset_id")
    normalized_asset = requested_asset_id
    config = _validate_config(config)
    identity_resolution = resolve_asset_identity(
        {"type": requested_identifier_type, "value": normalized_asset, "chain_id": requested_chain_id},
        market,
        identity_evidence,
    )
    if identity_resolution["canonical_asset_identity_status"] == "CONFLICT" or identity_resolution["market_base_asset_mapping_status"] == "MISMATCH":
        raise ValueError("canonical asset identity evidence conflicts with the requested identifier or market base")
    identity_status = identity_resolution["asset_identity_status"]

    downstream_use = evaluate_artifact_use(artifact, "internal_analysis")
    if downstream_use["decision"] != "ALLOW":
        raise PermissionError("research report blocked before analysis: " + ",".join(downstream_use["reason_codes"]))

    if source_bytes is None:
        source_bytes = (
            json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            .encode("utf-8")
        )
        hash_basis = "CANONICAL_JSON_SERIALIZATION"
    else:
        if not isinstance(source_bytes, bytes):
            raise ValueError("source_bytes must be bytes when provided")
        try:
            decoded_source = json.loads(source_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("source_bytes must contain the same UTF-8 JSON artifact") from exc
        if decoded_source != artifact:
            raise ValueError("source_bytes do not match the supplied artifact object")
        hash_basis = "RAW_SOURCE_FILE_BYTES"

    risk = analyze_artifact(artifact)
    movement = analyze_movement_events(
        artifact,
        config["movement"]["lookback_bars"],
        config["movement"]["return_threshold_pct"],
        config["movement"]["volume_ratio_threshold"],
    )
    support_resistance = analyze_support_resistance(
        artifact,
        config["support_resistance"]["pivot_left"],
        config["support_resistance"]["pivot_right"],
        config["support_resistance"]["tolerance_bps"],
    )

    source_integrity = {
        "sha256": _sha256(source_bytes),
        "bytes": len(source_bytes),
        "hash_basis": hash_basis,
        "page_integrity_status": {
            "risk_profile": risk.get("source_integrity_status"),
            "movement_events": movement.get("source_integrity_status"),
            "support_resistance": support_resistance.get("source_integrity_status"),
        },
    }
    input_capture_status = artifact.get("overall_status")
    analysis_quality = {
        "capture_status": input_capture_status if input_capture_status in {"PASS", "PARTIAL"} else "INDETERMINATE",
        "canonical_asset_identity": identity_resolution["canonical_asset_identity_status"],
        "risk_profile": risk.get("data_quality_status", "INDETERMINATE"),
        "movement_events": movement.get("data_quality_status", "INDETERMINATE"),
        "support_resistance": support_resistance.get("data_quality_status", "INDETERMINATE"),
    }
    quality_complete = (
        input_capture_status == "PASS"
        and identity_status == "VERIFIED"
        and all(value in {"COMPLETE", "PASS", "VERIFIED"} for key, value in analysis_quality.items() if key != "capture_status")
        and all(value == "VERIFIED" for value in source_integrity["page_integrity_status"].values())
    )

    horizons = {
        horizon: {
            "status": "INDETERMINATE",
            "conclusion": "INDETERMINATE",
            "reason_codes": [
                "HORIZON_METHODOLOGY_NOT_APPROVED",
                "EXTERNAL_EVENT_SOURCES_NOT_INTEGRATED",
                "FUNDAMENTAL_AND_ONCHAIN_COVERAGE_NOT_INTEGRATED",
            ],
            "reason": (
                "The current integration provides descriptive OHLCV analytics only. "
                "It has no approved horizon-specific methodology or integrated event, "
                "fundamental and on-chain evidence; no investment conclusion is emitted."
            ),
        }
        for horizon in HORIZONS
    }

    return {
        "schema_version": REPORT_SCHEMA,
        "report_status": "TECHNICAL_BASELINE_ASSEMBLED" if quality_complete else "PARTIAL",
        "decision_status": "INDETERMINATE",
        "requested_asset_id": normalized_asset,
        "requested_identifier_type": requested_identifier_type,
        "asset_identity_status": identity_status,
        "canonical_asset_identity_status": identity_resolution["canonical_asset_identity_status"],
        "market_base_asset_mapping_status": identity_resolution["market_base_asset_mapping_status"],
        "canonical_asset_identity": identity_resolution,
        "asset_identity_scope": (
            "Reviewed unique canonical identity evidence linked to market base asset."
            if identity_status == "VERIFIED"
            else "Market base symbol only; canonical identity is unresolved."
        ),
        "market": {
            "exchange": exchange,
            "market_type": "SPOT",
            "symbol_native": symbol,
            "base_asset": market.get("base_asset"),
            "interval": interval,
        },
        "methodology": config,
        "source_artifact": {
            "schema_version": artifact["schema_version"],
            "capture_status": input_capture_status,
            "provider_use_assessment": artifact.get("provider_use_assessment"),
            "downstream_use_assessment": downstream_use,
            **source_integrity,
        },
        "data_quality": {
            "status": "COMPLETE" if quality_complete else "INCOMPLETE_OR_UNVERIFIED",
            "dimensions": analysis_quality,
        },
        "descriptive_analyses": {
            "risk_profile": risk,
            "movement_events": movement,
            "support_resistance": support_resistance,
        },
        "horizons": horizons,
        "event_causal_assessment": {
            "status": "NOT_AVAILABLE",
            "reason": "No external news/event source connector is integrated in this increment.",
            "causality_claimed": False,
        },
        "limitations": [
            "This report combines descriptive module outputs; it is not a validated investment recommendation.",
            "The three horizons remain INDETERMINATE until horizon-specific methods and evidence coverage are approved.",
            "No news, regulatory-event, project-announcement, fundamental or on-chain connector is called.",
            "No ranking, forecast probability, expected return or guarantee of profitability is produced.",
            "A verified source hash proves byte integrity, not source authority or analytical validity.",
            "No order is submitted and no trading credentials are used.",
        ],
        "orders_submitted": False,
        "network_requests_made": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-id", required=True, help="Identifier value to evaluate; declare its type with --asset-id-type")
    parser.add_argument("--asset-id-type", choices=("symbol", "canonical_id", "contract_address", "name"), default="symbol")
    parser.add_argument("--asset-chain-id", help="Required when --asset-id-type=contract_address")
    parser.add_argument("--identity-evidence", type=Path, help="Reviewed crypto-canonical-asset-identity-v1 JSON; without it canonical identity remains unresolved")
    parser.add_argument("--artifact", required=True, type=Path, help="Preserved normalized Spot OHLCV JSON")
    parser.add_argument("--config", required=True, type=Path, help="Versioned JSON with explicit analysis parameters")
    parser.add_argument("--output", required=True, type=Path, help="Path to the research report JSON")
    args = parser.parse_args()

    raw = args.artifact.read_bytes()
    artifact = json.loads(raw.decode("utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    identity_evidence = json.loads(args.identity_evidence.read_text(encoding="utf-8")) if args.identity_evidence else None
    report = build_research_report(
        artifact, config, args.asset_id, raw,
        requested_identifier_type=args.asset_id_type,
        requested_chain_id=args.asset_chain_id,
        identity_evidence=identity_evidence,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "schema_version": report["schema_version"],
        "report_status": report["report_status"],
        "decision_status": report["decision_status"],
        "asset_identity_status": report["asset_identity_status"],
        "canonical_asset_identity_status": report["canonical_asset_identity_status"],
        "market_base_asset_mapping_status": report["market_base_asset_mapping_status"],
        "horizons": {key: value["status"] for key, value in report["horizons"].items()},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
