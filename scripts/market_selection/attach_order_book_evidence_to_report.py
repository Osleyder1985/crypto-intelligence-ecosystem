"""Attach authorized visible Spot order-book depth to an existing research report."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.market_selection.analyze_order_book_snapshot import analyze_order_book_snapshot
from scripts.market_selection.provider_license_gate import evaluate_artifact_use, evaluate_provider_use
from scripts.market_selection.research_report import REPORT_SCHEMA

INTEGRATION_SCHEMA = "crypto-research-report-order-book-evidence-v1"


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a timezone-aware ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _json_bytes(value: object, field: str) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be JSON-serializable without non-finite numbers") from exc


def attach_order_book_evidence(
    report: object,
    snapshots: object,
    *,
    evaluation_as_of: str,
    authorization_registry: dict | None = None,
    report_bytes: bytes | None = None,
    snapshots_bytes: bytes | None = None,
) -> dict:
    """Attach read-only order-book analyses without changing investment conclusions."""
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError(f"report.schema_version must be {REPORT_SCHEMA}")
    if report.get("decision_status") != "INDETERMINATE":
        raise ValueError("only INDETERMINATE research reports can receive order-book evidence")
    if report.get("orders_submitted") is not False:
        raise ValueError("report.orders_submitted must be false")
    if "order_book_evidence" in report:
        raise ValueError("report already contains order_book_evidence; refusing to overwrite evidence")
    asset_id = report.get("requested_asset_id")
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("report.requested_asset_id must be a non-empty exchange:symbol identifier")
    cutoff = _timestamp(evaluation_as_of, "evaluation_as_of")
    if not isinstance(snapshots, list):
        raise ValueError("snapshots must be a JSON array")
    if authorization_registry is None:
        authorization_registry = {}
    if not isinstance(authorization_registry, dict):
        raise PermissionError("trusted provider authorization registry must be an object")

    for use_case in ("internal_analysis", "persistent_storage"):
        assessment = evaluate_artifact_use(report, use_case)
        if assessment.get("decision") != "ALLOW":
            raise PermissionError(
                f"report {use_case} blocked before order-book integration: "
                + ",".join(assessment.get("reason_codes") or ["PROVIDER_USE_BLOCKED"])
            )

    if report_bytes is None:
        report_bytes = _json_bytes(report, "report")
    elif not isinstance(report_bytes, bytes):
        raise ValueError("report_bytes must be bytes")
    else:
        try:
            if json.loads(report_bytes.decode("utf-8")) != report:
                raise ValueError("report_bytes do not match the supplied report object")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("report_bytes must contain the same UTF-8 JSON report") from exc

    if snapshots_bytes is None:
        snapshots_bytes = _json_bytes(snapshots, "snapshots")
    elif not isinstance(snapshots_bytes, bytes):
        raise ValueError("snapshots_bytes must be bytes")
    else:
        try:
            if json.loads(snapshots_bytes.decode("utf-8")) != snapshots:
                raise ValueError("snapshots_bytes do not match the supplied snapshots")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("snapshots_bytes must contain the same UTF-8 JSON snapshots") from exc

    analyses = []
    seen_capture_keys = set()
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            raise ValueError(f"snapshots[{index}] must be an object")
        captured_at = _timestamp(snapshot.get("captured_at_utc"), f"snapshots[{index}].captured_at_utc")
        if captured_at > cutoff:
            raise ValueError(f"snapshots[{index}] was captured after evaluation_as_of")
        market = snapshot.get("market")
        if not isinstance(market, dict):
            raise ValueError(f"snapshots[{index}].market must be an object")
        exchange = market.get("exchange")
        symbol = market.get("symbol_native")
        if not isinstance(exchange, str) or not exchange.strip() or not isinstance(symbol, str) or not symbol.strip():
            raise ValueError(f"snapshots[{index}] requires explicit exchange and native symbol")
        snapshot_asset_id = f"{exchange.strip()}:{symbol.strip()}"
        if snapshot_asset_id.casefold() != asset_id.strip().casefold():
            raise ValueError(f"snapshots[{index}] market does not match report.requested_asset_id")
        capture_key = (snapshot_asset_id.casefold(), captured_at.isoformat())
        if capture_key in seen_capture_keys:
            raise ValueError(f"duplicate order-book capture for market and timestamp at snapshots[{index}]")
        seen_capture_keys.add(capture_key)

        provider_id = snapshot.get("provider_id")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise PermissionError(f"snapshots[{index}].provider_id is required")
        try:
            storage_assessment = evaluate_provider_use(
                provider_id, "persistent_storage", authorization_registry.get(provider_id)
            )
        except ValueError as exc:
            raise PermissionError(f"snapshots[{index}] provider storage authorization is invalid") from exc
        if storage_assessment.get("decision") != "ALLOW":
            raise PermissionError(
                f"snapshots[{index}] provider storage blocked: "
                + ",".join(storage_assessment.get("reason_codes") or ["PROVIDER_USE_BLOCKED"])
            )
        analysis = analyze_order_book_snapshot(snapshot, authorization_registry)
        analyses.append({
            "analysis": analysis,
            "storage_use_assessment": storage_assessment,
        })

    enriched = dict(report)
    enriched["order_book_evidence"] = {
        "integration_schema": INTEGRATION_SCHEMA,
        "status": "ANALYZED" if analyses else "NOT_AVAILABLE",
        "evaluation_as_of": cutoff.isoformat().replace("+00:00", "Z"),
        "snapshot_count": len(analyses),
        "source_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "source_snapshots_sha256": hashlib.sha256(snapshots_bytes).hexdigest(),
        "analyses": analyses,
        "limitations": [
            "Only levels visible in each authorized snapshot are represented; hidden orders and full market depth are unknown.",
            "Visible orders can be cancelled or changed and do not guarantee executable liquidity.",
            "Snapshots are point-in-time observations, not a forecast or proof of future support/resistance.",
            "The appendix does not alter horizon conclusions or imply an order was submitted.",
        ],
    }
    enriched["decision_status"] = "INDETERMINATE"
    enriched["orders_submitted"] = False
    return enriched


def _read_json(path: Path) -> tuple[Any, bytes]:
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path} must contain valid UTF-8 JSON") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="Existing research report JSON")
    parser.add_argument("--snapshots", required=True, type=Path, help="JSON array of normalized authorized order-book snapshots")
    parser.add_argument("--authorization-registry", required=True, type=Path, help="Trusted provider authorization registry JSON")
    parser.add_argument("--evaluation-as-of", required=True, help="Historical cutoff timestamp")
    parser.add_argument("--output", required=True, type=Path, help="Output report path; existing order-book evidence is never overwritten")
    args = parser.parse_args()
    report, report_raw = _read_json(args.report)
    snapshots, snapshots_raw = _read_json(args.snapshots)
    authorization_registry, _ = _read_json(args.authorization_registry)
    enriched = attach_order_book_evidence(
        report,
        snapshots,
        evaluation_as_of=args.evaluation_as_of,
        authorization_registry=authorization_registry,
        report_bytes=report_raw,
        snapshots_bytes=snapshots_raw,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "schema_version": enriched["schema_version"],
        "order_book_evidence_status": enriched["order_book_evidence"]["status"],
        "snapshot_count": enriched["order_book_evidence"]["snapshot_count"],
        "decision_status": enriched["decision_status"],
        "orders_submitted": enriched["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
