"""Analyze repeated public Spot quote-turnover artifacts without inventing selection thresholds."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from scripts.market_selection.provider_license_gate import evaluate_artifact_use


SCHEMA_VERSION = "multi-exchange-spot-quote-volume-v1"
OUTPUT_SCHEMA_VERSION = "quote-volume-series-analysis-v1"


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def _verify_record_integrity(record: dict, artifact_name: str) -> str:
    encoded = record.get("response_base64")
    digest = record.get("response_sha256")
    byte_count = record.get("response_bytes")
    if encoded is None:
        if record.get("capture_status") == "PASS":
            raise ValueError(f"{artifact_name}: successful record has no preserved response body")
        return "UNAVAILABLE"
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{artifact_name}: invalid response_base64") from exc
    actual_digest = hashlib.sha256(raw).hexdigest()
    if digest and actual_digest != digest:
        raise ValueError(f"{artifact_name}: SHA-256 mismatch for {record.get('exchange')}/{record.get('symbol')}")
    if byte_count is not None and len(raw) != byte_count:
        raise ValueError(f"{artifact_name}: response_bytes mismatch for {record.get('exchange')}/{record.get('symbol')}")
    if digest is None or byte_count is None:
        return "PARTIAL_METADATA"
    return "VERIFIED"


def load_artifact(path: Path) -> dict:
    raw_file = path.read_bytes()
    try:
        artifact = json.loads(raw_file.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name}: artifact is not valid UTF-8 JSON") from exc
    if not isinstance(artifact, dict) or artifact.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path.name}: expected schema_version {SCHEMA_VERSION}")
    created = artifact.get("created_at_utc")
    parse_utc(created)
    records = artifact.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{path.name}: records must be a list")
    verified_records = []
    for original in records:
        if not isinstance(original, dict):
            raise ValueError(f"{path.name}: record must be an object")
        record = dict(original)
        record["integrity_status"] = _verify_record_integrity(record, path.name)
        record["_artifact_created_at_utc"] = created
        record["_artifact_name"] = path.name
        verified_records.append(record)
    return {
        "path": path.name,
        "sha256": hashlib.sha256(raw_file).hexdigest(),
        "created_at_utc": created,
        "records": verified_records,
    }


def _is_pionex(record: dict) -> bool:
    return str(record.get("exchange", "")).strip().lower() == "pionex"


def _decimal_value(record: dict):
    # Historical artifacts may have been produced by a parser that assumed the
    # Pionex amount field was quoted in USDT. Do not trust that stale label:
    # the current official schema does not document its denomination.
    if _is_pionex(record):
        return None
    if record.get("quote_volume_status") != "VALID":
        return None
    raw = record.get("quote_volume_decimal")
    if raw is None:
        return None
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() and value >= 0 else None


def analyze_artifacts(paths) -> dict:
    loaded = [load_artifact(Path(path)) for path in paths]
    if not loaded:
        raise ValueError("at least one input artifact is required")
    for artifact in loaded:
        provider_use = evaluate_artifact_use(artifact, "internal_analysis")
        if provider_use["decision"] != "ALLOW":
            raise PermissionError("quote-volume analysis blocked before use: " + ",".join(provider_use["reason_codes"]))
    loaded.sort(key=lambda item: (parse_utc(item["created_at_utc"]), item["path"]))

    grouped = {}
    input_record_count = 0
    integrity_counts = {"VERIFIED": 0, "PARTIAL_METADATA": 0, "UNAVAILABLE": 0}
    for artifact in loaded:
        for record in artifact["records"]:
            input_record_count += 1
            integrity = record["integrity_status"]
            integrity_counts[integrity] = integrity_counts.get(integrity, 0) + 1
            key = (str(record.get("exchange", "")), str(record.get("asset", "")), str(record.get("symbol", "")))
            grouped.setdefault(key, []).append(record)

    series = []
    for (exchange, asset, symbol), records in sorted(grouped.items()):
        records.sort(key=lambda row: (parse_utc(row.get("captured_at_utc") or row["_artifact_created_at_utc"]), row["_artifact_name"]))
        valid_rows = []
        for row in records:
            value = _decimal_value(row)
            timestamp = row.get("captured_at_utc") or row["_artifact_created_at_utc"]
            parse_utc(timestamp)
            pionex = _is_pionex(row)
            row_value = {
                "artifact": row["_artifact_name"],
                "artifact_created_at_utc": row["_artifact_created_at_utc"],
                "captured_at_utc": timestamp,
                "capture_status": row.get("capture_status", "UNKNOWN"),
                "http_status": row.get("http_status"),
                "quote_volume_status": "INDETERMINATE" if pionex else row.get("quote_volume_status", "INDETERMINATE"),
                "source_reported_quote_volume_status": row.get("quote_volume_status", "INDETERMINATE"),
                "quote_volume_raw": row.get("quote_volume_raw"),
                "quote_volume_decimal": str(value) if value is not None else None,
                "quote_volume_unit": None if pionex else row.get("quote_volume_unit"),
                "source_reported_quote_volume_unit": row.get("quote_volume_unit"),
                "volume_semantics": "Pionex amount; unit/denomination not documented by the reviewed official schema" if pionex else row.get("volume_semantics"),
                "source_reported_volume_semantics": row.get("volume_semantics"),
                "comparison_eligibility_status": "INDETERMINATE_SOURCE_UNIT_UNDOCUMENTED" if pionex else "ELIGIBLE_FOR_VALIDATION",
                "source_timestamp_raw": row.get("source_timestamp_raw"),
                "response_sha256": row.get("response_sha256"),
                "integrity_status": row["integrity_status"],
                "error_type": row.get("error_type"),
                "error_message": row.get("error_message"),
            }
            valid_rows.append((row_value, value))
        values = [(item, value) for item, value in valid_rows if value is not None and item["capture_status"] == "PASS" and item["integrity_status"] == "VERIFIED"]
        units = sorted({item["quote_volume_unit"] for item, _ in values if item["quote_volume_unit"] is not None})
        semantics = sorted({item["volume_semantics"] for item, _ in values if item["volume_semantics"] is not None})
        all_semantics_present = all(item["quote_volume_unit"] is not None and item["volume_semantics"] is not None for item, _ in values)
        comparable = len(units) == 1 and len(semantics) == 1 and all_semantics_present and len(values) >= 2
        if exchange.strip().lower() == "pionex":
            comparison_status = "INDETERMINATE_SOURCE_UNIT_UNDOCUMENTED"
        elif len(values) < 2:
            comparison_status = "INSUFFICIENT_VALID_SAMPLES"
        elif len(units) != 1 or len(semantics) != 1 or not all_semantics_present:
            comparison_status = "INDETERMINATE_INCOMPATIBLE_SEMANTICS_OR_UNITS"
        else:
            comparison_status = "DESCRIPTIVE_COMPARISON_ONLY"

        deltas = []
        if comparable:
            for (previous, prev_value), (current, cur_value) in zip(values, values[1:]):
                previous_time = parse_utc(previous["captured_at_utc"])
                current_time = parse_utc(current["captured_at_utc"])
                elapsed = (current_time - previous_time).total_seconds()
                delta = None if prev_value == 0 else ((cur_value - prev_value) / prev_value) * Decimal("100")
                deltas.append({
                    "from_captured_at_utc": previous["captured_at_utc"],
                    "to_captured_at_utc": current["captured_at_utc"],
                    "elapsed_seconds": elapsed,
                    "previous_rolling_24h_turnover": str(prev_value),
                    "current_rolling_24h_turnover": str(cur_value),
                    "change_percent_between_rolling_windows": str(delta) if delta is not None else None,
                    "status": "INDETERMINATE_ZERO_BASELINE" if delta is None else "DESCRIPTIVE_ONLY",
                    "interpretation_limit": "Change between two rolling 24h ticker observations; not turnover traded during the elapsed interval.",
                })
        series.append({
            "exchange": exchange,
            "asset": asset,
            "symbol": symbol,
            "quote_currency": records[0].get("quote_currency"),
            "expected_samples": len(records),
            "valid_samples": len(values),
            "missing_or_invalid_samples": len(records) - len(values),
            "ineligible_semantic_samples": sum(1 for row in records if _is_pionex(row)),
            "coverage_ratio": str(Decimal(len(values)) / Decimal(len(records))) if records else "0",
            "quote_volume_unit_values": units,
            "volume_semantics_values": semantics,
            "comparison_status": comparison_status,
            "observations": [item for item, _ in valid_rows],
            "consecutive_deltas": deltas,
            "selection_or_ranking_performed": False,
        })

    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "analysis_status": "DESCRIPTIVE_ONLY",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "method": "Group repeated captures by exact exchange/asset/native symbol; verify preserved response bytes, hash and size; compare only valid samples with matching unit and documented field semantics. Apply the current semantic guard to Pionex independently of stale historical parser labels; Pionex amount remains ineligible until its unit is documented.",
        "input_artifacts": [{"name": item["path"], "created_at_utc": item["created_at_utc"], "sha256": item["sha256"], "record_count": len(item["records"])} for item in loaded],
        "input_record_count": input_record_count,
        "response_integrity_counts": integrity_counts,
        "series_count": len(series),
        "series": series,
        "limitations": [
            "Rolling 24h ticker changes between samples are not volume traded during the elapsed interval.",
            "Provider field semantics and rolling-window end times may differ even when units and labels match; this tool does not prove full cross-venue comparability.",
            "Pionex amount is preserved as raw evidence but is excluded from turnover comparisons, including legacy artifacts that incorrectly label it VALID/USDT, because the reviewed official schema does not document its denomination.",
            "No ranking, eligibility decision, investment recommendation, or numeric selection threshold is produced.",
            "Missing, invalid, inaccessible, or integrity-unverified observations are not converted to zero.",
            "Two or more samples do not establish long-term stability; representativeness requires a longer series, coverage analysis, and market-regime review.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", help="one or more multi-exchange-spot-quote-volume-v1 JSON artifacts")
    parser.add_argument("--output", default="artifacts/quote-volume-series-analysis.json")
    args = parser.parse_args()
    result = analyze_artifacts(args.artifacts)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "analysis_status": result["analysis_status"],
        "input_artifact_count": len(result["input_artifacts"]),
        "input_record_count": result["input_record_count"],
        "series_count": result["series_count"],
        "response_integrity_counts": result["response_integrity_counts"],
        "comparison_status_counts": {
            status: sum(1 for row in result["series"] if row["comparison_status"] == status)
            for status in sorted({row["comparison_status"] for row in result["series"]})
        },
        "selection_or_ranking_performed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
