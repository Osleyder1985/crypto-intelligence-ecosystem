"""Attach descriptive matured-forecast scoring to an existing research report."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.market_selection.forecast_scoring import score_forecast_records
from scripts.market_selection.research_report import REPORT_SCHEMA

INTEGRATION_SCHEMA = "crypto-research-report-forecast-evaluation-integration-v1"


def attach_forecast_scoring(report: object, records: object, *, report_bytes: bytes | None = None,
                            records_bytes: bytes | None = None) -> dict:
    """Add a scoring appendix without changing horizon conclusions or report decisions."""
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError(f"report.schema_version must be {REPORT_SCHEMA}")
    asset_id = report.get("requested_asset_id")
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("report.requested_asset_id must be a non-empty string")
    if report.get("decision_status") != "INDETERMINATE":
        raise ValueError("only INDETERMINATE research reports can receive descriptive forecast scoring")
    if report.get("orders_submitted") is not False:
        raise ValueError("report.orders_submitted must be false")
    if "forecast_evaluation" in report:
        raise ValueError("report already contains forecast_evaluation; refusing to overwrite evidence")
    if report_bytes is None:
        report_bytes = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    elif not isinstance(report_bytes, bytes):
        raise ValueError("report_bytes must be bytes")
    else:
        try:
            if json.loads(report_bytes.decode("utf-8")) != report:
                raise ValueError("report_bytes do not match the supplied report object")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("report_bytes must contain the same UTF-8 JSON report") from exc
    if records_bytes is None:
        records_bytes = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    elif not isinstance(records_bytes, bytes):
        raise ValueError("records_bytes must be bytes")
    else:
        try:
            if json.loads(records_bytes.decode("utf-8")) != records:
                raise ValueError("records_bytes do not match the supplied records")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("records_bytes must contain the same UTF-8 JSON records") from exc

    scored = score_forecast_records(records)
    cohort_asset_id = scored["cohort"]["asset_id"]
    if cohort_asset_id != asset_id.strip():
        raise ValueError("forecast scoring cohort asset_id must exactly match report.requested_asset_id")

    enriched = dict(report)
    enriched["forecast_evaluation"] = {
        "integration_schema": INTEGRATION_SCHEMA,
        "status": "DESCRIPTIVE_SCORING_ATTACHED",
        "source_records_sha256": hashlib.sha256(records_bytes).hexdigest(),
        "source_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "scoring": scored,
        "interpretation": (
            "This appendix reports descriptive forecast error only. It does not alter the report's "
            "horizon conclusions, decision_status, or order-submission state."
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
    parser.add_argument("--records", required=True, type=Path, help="JSON array of matured forecast/outcome records")
    parser.add_argument("--output", required=True, type=Path, help="Output report path; existing forecast evidence is never overwritten")
    args = parser.parse_args()
    report, report_raw = _read_json(args.report)
    records, records_raw = _read_json(args.records)
    enriched = attach_forecast_scoring(report, records, report_bytes=report_raw, records_bytes=records_raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "schema_version": enriched["schema_version"],
        "forecast_evaluation_status": enriched["forecast_evaluation"]["status"],
        "decision_status": enriched["decision_status"],
        "orders_submitted": enriched["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
