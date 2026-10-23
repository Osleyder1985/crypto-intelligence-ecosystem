"""Attach validated, independent horizon assessments to an existing research report."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.market_selection.horizon_assessment_contract import (
    ASSESSMENT_SCHEMA,
    validate_horizon_assessment,
)
from scripts.market_selection.research_report import REPORT_SCHEMA

INTEGRATION_SCHEMA = "crypto-research-report-horizon-assessment-integration-v1"


def attach_horizon_assessment(
    report: object,
    assessment: object,
    *,
    report_bytes: bytes | None = None,
    assessment_bytes: bytes | None = None,
) -> dict:
    """Attach a validated assessment without overwriting the report's baseline conclusions."""
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError(f"report.schema_version must be {REPORT_SCHEMA}")
    asset_id = report.get("requested_asset_id")
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("report.requested_asset_id must be a non-empty string")
    if report.get("decision_status") != "INDETERMINATE":
        raise ValueError("only INDETERMINATE research reports can receive a horizon assessment")
    if report.get("orders_submitted") is not False:
        raise ValueError("report.orders_submitted must be false")
    if "horizon_assessment" in report:
        raise ValueError("report already contains horizon_assessment; refusing to overwrite evidence")

    if report_bytes is None:
        report_bytes = json.dumps(
            report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    elif not isinstance(report_bytes, bytes):
        raise ValueError("report_bytes must be bytes")
    else:
        try:
            if json.loads(report_bytes.decode("utf-8")) != report:
                raise ValueError("report_bytes do not match the supplied report object")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("report_bytes must contain the same UTF-8 JSON report") from exc

    if assessment_bytes is None:
        assessment_bytes = json.dumps(
            assessment, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    elif not isinstance(assessment_bytes, bytes):
        raise ValueError("assessment_bytes must be bytes")
    else:
        try:
            if json.loads(assessment_bytes.decode("utf-8")) != assessment:
                raise ValueError("assessment_bytes do not match the supplied assessment object")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("assessment_bytes must contain the same UTF-8 JSON assessment") from exc

    validated = validate_horizon_assessment(assessment)
    if validated["schema_version"] != ASSESSMENT_SCHEMA:
        raise ValueError(f"assessment.schema_version must be {ASSESSMENT_SCHEMA}")
    if validated["asset_id"] != asset_id.strip():
        raise ValueError("assessment.asset_id must exactly match report.requested_asset_id")

    enriched = dict(report)
    enriched["horizon_assessment"] = {
        "integration_schema": INTEGRATION_SCHEMA,
        "status": "VALIDATED_ASSESSMENT_ATTACHED",
        "source_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "source_assessment_sha256": hashlib.sha256(assessment_bytes).hexdigest(),
        "assessment": validated,
        "interpretation": (
            "This appendix preserves independent horizon assessments without aggregating them "
            "or replacing the report's baseline horizon statuses, decision_status, or order state. "
            "Contract validation does not establish predictive utility or investment suitability."
        ),
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
    parser.add_argument("--report", required=True, type=Path, help="Existing crypto-asset-research-report-v2 JSON")
    parser.add_argument("--assessment", required=True, type=Path, help="JSON assessment with separate short/medium/long horizons")
    parser.add_argument("--output", required=True, type=Path, help="Output path; existing assessment evidence is never overwritten")
    args = parser.parse_args()
    report, report_raw = _read_json(args.report)
    assessment, assessment_raw = _read_json(args.assessment)
    enriched = attach_horizon_assessment(
        report, assessment, report_bytes=report_raw, assessment_bytes=assessment_raw
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "schema_version": enriched["schema_version"],
        "horizon_assessment_status": enriched["horizon_assessment"]["status"],
        "decision_status": enriched["decision_status"],
        "orders_submitted": enriched["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
