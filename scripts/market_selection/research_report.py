"""Assemble existing descriptive OHLCV analyses into a conservative research report.

This is an offline integration step, not a forecast or investment recommendation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.market_selection.analyze_ohlcv_risk_profile import analyze_artifact
from scripts.market_selection.analyze_support_resistance import analyze_support_resistance
from scripts.market_selection.build_movement_episodes import build_movement_episodes
from scripts.market_selection.detect_ohlcv_movement_events import analyze_movement_events
from scripts.market_selection.analyze_order_book_snapshot import analyze_order_book_snapshot
from scripts.market_selection.normalize_order_book_probe import normalize_multi_exchange_order_book_probe
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


def _utc_timestamp_ms(value: Any) -> int | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return int(parsed.timestamp() * 1000)


def _measure_candle_freshness(artifact: dict) -> dict:
    """Measure age at capture without inventing a fresh/stale threshold."""
    candles = artifact.get("candles")
    if not isinstance(candles, list):
        return {
            "status": "INDETERMINATE",
            "reason_code": "CANDLE_LIST_MISSING",
            "freshness_policy_status": "NOT_APPROVED",
            "freshness_conclusion": "NOT_ASSESSED",
            "age_ms_at_capture": None,
            "latest_closed_candle_close_time_ms": None,
            "latest_closed_candle_captured_at_utc": None,
        }
    eligible = [
        candle for candle in candles
        if isinstance(candle, dict)
        and candle.get("closed_at_capture") is True
        and candle.get("eligible_for_closed_candle_analysis") is True
        and isinstance(candle.get("close_time_ms"), int)
        and not isinstance(candle.get("close_time_ms"), bool)
    ]
    if not eligible:
        return {
            "status": "INDETERMINATE",
            "reason_code": "NO_CLOSED_CANDLE_ELIGIBLE_AT_CAPTURE",
            "freshness_policy_status": "NOT_APPROVED",
            "freshness_conclusion": "NOT_ASSESSED",
            "age_ms_at_capture": None,
            "latest_closed_candle_close_time_ms": None,
            "latest_closed_candle_captured_at_utc": None,
        }
    latest = max(eligible, key=lambda candle: candle["close_time_ms"])
    captured_at = latest.get("captured_at_utc")
    captured_at_ms = _utc_timestamp_ms(captured_at)
    close_time_ms = latest["close_time_ms"]
    if captured_at_ms is None:
        status = "INDETERMINATE"
        reason = "CANDLE_CAPTURE_TIMESTAMP_MISSING_OR_INVALID"
        age_ms = None
    elif captured_at_ms < close_time_ms:
        status = "INVALID"
        reason = "CAPTURE_TIMESTAMP_PRECEDES_CANDLE_CLOSE"
        age_ms = None
    else:
        status = "MEASURED"
        reason = "AGE_MEASURED_NO_APPROVED_FRESHNESS_THRESHOLD"
        age_ms = captured_at_ms - close_time_ms
    return {
        "status": status,
        "reason_code": reason,
        "freshness_policy_status": "NOT_APPROVED",
        "freshness_conclusion": "NOT_ASSESSED",
        "age_ms_at_capture": age_ms,
        "latest_closed_candle_close_time_ms": close_time_ms,
        "latest_closed_candle_captured_at_utc": captured_at,
        "measurement_basis": "capture timestamp minus latest eligible closed candle close time",
    }


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

    # Fail closed on malformed methodology values before any analyzer consumes them.
    # bool is deliberately rejected even though Python treats it as an int.
    for key in ("lookback_bars",):
        value = movement[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"config.movement.{key} must be a positive integer")

    for key in ("pivot_left", "pivot_right"):
        value = support_resistance[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"config.support_resistance.{key} must be a positive integer")

    for key in ("return_threshold_pct", "volume_ratio_threshold"):
        value = movement[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"config.movement.{key} must be a finite number greater than zero")

    tolerance_bps = support_resistance["tolerance_bps"]
    if (isinstance(tolerance_bps, bool) or not isinstance(tolerance_bps, (int, float))
            or not math.isfinite(tolerance_bps) or not 0 <= tolerance_bps <= 10_000):
        raise ValueError("config.support_resistance.tolerance_bps must be a finite number from 0 to 10000")

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
    order_book_artifact: dict | None = None,
    order_book_authorization_registry: dict | None = None,
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
    movement_episodes = build_movement_episodes(support_resistance)
    order_book_analysis = None
    if order_book_artifact is not None:
        order_book_analysis = analyze_order_book_snapshot(order_book_artifact, order_book_authorization_registry)
        order_market = order_book_analysis["market"]
        if order_market["exchange"].lower() != exchange.lower() or order_market["symbol_native"].upper() != symbol.upper():
            raise ValueError("order-book artifact exchange and symbol must match the OHLCV report market")

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
    freshness_observation = _measure_candle_freshness(artifact)
    candles = artifact.get("candles")
    captured_payload_count = len(candles) if isinstance(candles, list) else None
    requested_count = artifact.get("requested_open_candle_count")
    declared_captured_count = artifact.get("captured_candle_count")
    missing_open_times = artifact.get("missing_open_time_ms")
    unexpected_open_times = artifact.get("unexpected_open_time_ms")
    count_fields_valid = (
        isinstance(requested_count, int) and not isinstance(requested_count, bool) and requested_count > 0
        and isinstance(declared_captured_count, int) and not isinstance(declared_captured_count, bool)
        and declared_captured_count >= 0
        and isinstance(captured_payload_count, int)
        and isinstance(missing_open_times, list)
        and isinstance(unexpected_open_times, list)
    )
    declared_count_matches_payload = (
        count_fields_valid and declared_captured_count == captured_payload_count
    )
    coverage_ratio = (
        captured_payload_count / requested_count
        if count_fields_valid and requested_count > 0
        else None
    )
    if not count_fields_valid:
        coverage_status = "INDETERMINATE"
    elif (
        input_capture_status == "PASS"
        and declared_count_matches_payload
        and declared_captured_count == requested_count
        and not missing_open_times
        and not unexpected_open_times
    ):
        coverage_status = "COMPLETE"
    else:
        coverage_status = "PARTIAL"
    historical_coverage = {
        "status": coverage_status,
        "requested_candle_count": requested_count if count_fields_valid else None,
        "captured_candle_count": captured_payload_count,
        "declared_captured_candle_count": declared_captured_count if count_fields_valid else None,
        "declared_count_matches_payload": declared_count_matches_payload,
        "coverage_ratio": coverage_ratio,
        "missing_open_time_ms": missing_open_times if isinstance(missing_open_times, list) else None,
        "unexpected_open_time_ms": unexpected_open_times if isinstance(unexpected_open_times, list) else None,
        "basis": "capture artifact counts and explicit open-time gap lists",
    }
    analysis_quality = {
        "capture_status": input_capture_status if input_capture_status in {"PASS", "PARTIAL"} else "INDETERMINATE",
        "historical_coverage": coverage_status,
        "canonical_asset_identity": identity_resolution["canonical_asset_identity_status"],
        "risk_profile": risk.get("data_quality_status", "INDETERMINATE"),
        "movement_events": movement.get("data_quality_status", "INDETERMINATE"),
        "support_resistance": support_resistance.get("data_quality_status", "INDETERMINATE"),
    }
    quality_complete = (
        input_capture_status == "PASS"
        and coverage_status == "COMPLETE"
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
            "quote_asset": market.get("quote_asset"),
            "symbol_status_at_capture": market.get("symbol_status_at_capture"),
            "is_spot_trading_allowed_at_capture": market.get("is_spot_trading_allowed_at_capture"),
            "market_resolution": market.get("market_resolution"),
            "interval": interval,
        },
        "methodology": config,
        "source_artifact": {
            "schema_version": artifact["schema_version"],
            "capture_status": input_capture_status,
            "historical_coverage": historical_coverage,
            "freshness_observation": freshness_observation,
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
            "movement_episodes": movement_episodes,
            "order_book": order_book_analysis if order_book_analysis is not None else {
                "status": "NOT_PROVIDED",
                "reason": "No authorized normalized order-book snapshot was supplied.",
            },
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
            "Movement episodes are reconstructed from confirmed pivots; their turning-point timestamps are retrospective estimates and no news/event causality is inferred.",
            "No news, regulatory-event, project-announcement, fundamental or on-chain connector is called.",
            "Order-book analysis is included only when a matching authorized snapshot is supplied; snapshots are not full or persistent market depth.",
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
    parser.add_argument("--order-book-artifact", type=Path, help="Optional normalized crypto-spot-order-book-snapshot-v1 JSON matching the selected exchange and symbol")
    parser.add_argument("--provider-authorization-registry", type=Path, help="Deployment-controlled provider authorization registry JSON; never use user-supplied authorization records")
    parser.add_argument("--multi-exchange-order-book-probe", type=Path, help="Optional preserved multi-exchange-spot-book-probe-v1 JSON to normalize and analyze")
    parser.add_argument("--order-book-exchange", help="Exchange key for selecting exactly one record from the multi-exchange probe")
    parser.add_argument("--order-book-symbol", help="Native symbol for selecting exactly one record from the multi-exchange probe")
    parser.add_argument("--output", required=True, type=Path, help="Path to the research report JSON")
    args = parser.parse_args()

    raw = args.artifact.read_bytes()
    artifact = json.loads(raw.decode("utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    identity_evidence = json.loads(args.identity_evidence.read_text(encoding="utf-8")) if args.identity_evidence else None
    order_book_artifact = json.loads(args.order_book_artifact.read_text(encoding="utf-8")) if args.order_book_artifact else None
    authorization_registry = json.loads(args.provider_authorization_registry.read_text(encoding="utf-8")) if args.provider_authorization_registry else None
    if args.multi_exchange_order_book_probe:
        if order_book_artifact is not None:
            parser.error("choose either --order-book-artifact or --multi-exchange-order-book-probe, not both")
        if not args.order_book_exchange or not args.order_book_symbol:
            parser.error("--multi-exchange-order-book-probe requires --order-book-exchange and --order-book-symbol")
        probe = json.loads(args.multi_exchange_order_book_probe.read_text(encoding="utf-8"))
        order_book_artifact = normalize_multi_exchange_order_book_probe(
            probe, exchange=args.order_book_exchange, symbol=args.order_book_symbol,
            authorization_registry=authorization_registry,
        )
    elif args.order_book_exchange or args.order_book_symbol:
        parser.error("--order-book-exchange and --order-book-symbol require --multi-exchange-order-book-probe")
    report = build_research_report(
        artifact, config, args.asset_id, raw,
        requested_identifier_type=args.asset_id_type,
        requested_chain_id=args.asset_chain_id,
        identity_evidence=identity_evidence,
        order_book_artifact=order_book_artifact,
        order_book_authorization_registry=authorization_registry,
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
