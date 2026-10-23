"""Immutable, content-addressed evaluation records and conservative evaluation comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


SCHEMA_VERSION = "crypto-evaluation-record-v1"
COMPARISON_SCHEMA_VERSION = "crypto-evaluation-comparison-v1"


def _reject_constant(value):
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=_reject_constant)


def _validate_json(value, path="value"):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string object key")
            _validate_json(item, f"{path}.{key}")
        return
    raise ValueError(f"{path} contains a non-JSON value: {type(value).__name__}")


def _require_text(manifest: dict, key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _validate_market_metadata(manifest: dict, asset_id: str, market_id: str):
    metadata = manifest.get("market_metadata")
    if metadata is None:
        return None
    if not isinstance(metadata, dict) or not metadata:
        raise ValueError("market_metadata must be a non-empty JSON object when provided")
    allowed = {"base_asset_id", "quote_asset_id", "market_type"}
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        raise ValueError(f"market_metadata contains unsupported fields: {', '.join(unknown)}")
    normalized = {}
    for key in allowed:
        value = metadata.get(key)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"market_metadata.{key} must be a non-empty string")
            normalized[key] = value.strip()
    if not normalized:
        raise ValueError("market_metadata must declare at least one supported field")
    base_asset = normalized.get("base_asset_id")
    if base_asset is not None and base_asset != asset_id:
        raise ValueError("market_metadata.base_asset_id must match asset_id")
    parts = market_id.split(":")
    if len(parts) == 3:
        pair, market_type = parts[1], parts[2]
        if normalized.get("market_type") is not None and normalized["market_type"] != market_type:
            raise ValueError("market_metadata.market_type must match market_id")
        # Only validate pair components when the market ID uses an explicit separator.
        separators = ("-", "/", "_")
        separator = next((item for item in separators if item in pair), None)
        if separator is not None:
            pair_parts = pair.split(separator)
            if len(pair_parts) == 2 and all(pair_parts):
                if base_asset is not None and pair_parts[0] != base_asset:
                    raise ValueError("market_metadata.base_asset_id must match the delimited market pair")
                quote_asset = normalized.get("quote_asset_id")
                if quote_asset is not None and pair_parts[1] != quote_asset:
                    raise ValueError("market_metadata.quote_asset_id must match the delimited market pair")
    return normalized


def _validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("generated_at_utc must be an ISO-8601 timestamp with timezone")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("generated_at_utc must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_optional_timestamp(value, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone or null")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def build_evaluation_record(manifest: dict, archive_dir: str | Path, output_dir: str | Path) -> dict:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    _validate_json(manifest, "manifest")
    required = ("asset_id", "market_id", "horizon", "methodology_id", "methodology_version", "code_version")
    values = {key: _require_text(manifest, key) for key in required}
    market_metadata = _validate_market_metadata(manifest, values["asset_id"], values["market_id"])
    parameters = manifest.get("parameters")
    results = manifest.get("results")
    quality = manifest.get("quality")
    sources = manifest.get("source_artifacts")
    if not isinstance(parameters, dict) or not isinstance(results, dict) or not isinstance(quality, dict):
        raise ValueError("parameters, results and quality must be JSON objects")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source_artifacts must be a non-empty array")
    generated = _validate_timestamp(manifest.get("generated_at_utc") or datetime.now(timezone.utc).isoformat())
    archive_root = Path(archive_dir)
    archived_sources = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"source_artifacts[{index}] must be an object")
        source_path = source.get("path")
        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError(f"source_artifacts[{index}].path is required")
        window_start = _validate_optional_timestamp(
            source.get("window_start_utc"), f"source_artifacts[{index}].window_start_utc"
        )
        window_end = _validate_optional_timestamp(
            source.get("window_end_utc"), f"source_artifacts[{index}].window_end_utc"
        )
        if window_start is not None and window_end is not None and window_start > window_end:
            raise ValueError(f"source_artifacts[{index}] window_start_utc must not be after window_end_utc")
        raw = Path(source_path).read_bytes()
        digest = _sha256(raw)
        relative = Path("sha256") / f"{digest}.bin"
        destination = archive_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            existing = destination.read_bytes()
            if _sha256(existing) != digest or existing != raw:
                raise ValueError(f"content-addressed archive collision for {digest}")
        else:
            _write_exclusive(destination, raw)
        item = {
            "source": _require_text(source, "source"),
            "endpoint": _require_text(source, "endpoint"),
            "window_start_utc": window_start,
            "window_end_utc": window_end,
            "quality_status": _require_text(source, "quality_status"),
            "sha256": digest,
            "bytes": len(raw),
            "archive_relative_path": relative.as_posix(),
        }
        archived_sources.append(item)
    body = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "asset_id": values["asset_id"],
        "market_id": values["market_id"],
        **({"market_metadata": market_metadata} if market_metadata is not None else {}),
        "horizon": values["horizon"],
        "methodology": {
            "id": values["methodology_id"],
            "version": values["methodology_version"],
            "parameters": parameters,
        },
        "implementation": {
            "code_version": values["code_version"],
            "git_sha": manifest.get("git_sha"),
        },
        "source_artifacts": archived_sources,
        "quality": quality,
        "results": results,
        "uncertainty": manifest.get("uncertainty", []),
        "warnings": manifest.get("warnings", []),
        "previous_evaluation_id": manifest.get("previous_evaluation_id"),
        "orders_submitted": False,
        "persistence_mode": "LOCAL_CONTENT_ADDRESSED_ARCHIVE",
    }
    _validate_json(body, "record")
    evaluation_id = _sha256(_json_bytes(body))
    record = {**body, "evaluation_id": evaluation_id}
    record["record_sha256"] = _sha256(_json_bytes(record))
    output_path = Path(output_dir) / f"{evaluation_id}.json"
    _write_exclusive(output_path, (_json_bytes(record) + b"\n"))
    return record


def verify_evaluation_record(record_path: str | Path, archive_dir: str | Path | None = None) -> dict:
    errors = []
    try:
        record = _read_json(record_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"valid": False, "errors": [f"record_read_error: {type(exc).__name__}: {exc}"], "record": None}
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA_VERSION:
        return {"valid": False, "errors": ["unsupported_schema_version"], "record": record if isinstance(record, dict) else None}
    body = {key: value for key, value in record.items() if key not in ("evaluation_id", "record_sha256")}
    expected_id = _sha256(_json_bytes(body))
    if record.get("evaluation_id") != expected_id:
        errors.append("evaluation_id_mismatch")
    without_record_hash = {key: value for key, value in record.items() if key != "record_sha256"}
    if record.get("record_sha256") != _sha256(_json_bytes(without_record_hash)):
        errors.append("record_sha256_mismatch")
    if archive_dir is not None:
        root = Path(archive_dir)
        for source in record.get("source_artifacts", []):
            relative = source.get("archive_relative_path")
            if not isinstance(relative, str):
                errors.append("source_archive_path_missing")
                continue
            path = root / relative
            try:
                raw = path.read_bytes()
            except OSError:
                errors.append(f"source_archive_missing:{relative}")
                continue
            if len(raw) != source.get("bytes") or _sha256(raw) != source.get("sha256"):
                errors.append(f"source_archive_integrity_mismatch:{relative}")
    return {"valid": not errors, "errors": errors, "record": record}


def _flatten_numeric(value, prefix=""):
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            result.update(_flatten_numeric(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]"
            result.update(_flatten_numeric(item, path))
    elif isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            return result
        if number.is_finite():
            result[prefix] = number
    return result


def compare_evaluation_records(old: dict, new: dict) -> dict:
    if old.get("schema_version") != SCHEMA_VERSION or new.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("both inputs must use the supported evaluation record schema")
    scope_fields = ("asset_id", "market_id", "market_metadata", "horizon")
    scope_compatible = all(old.get(key) == new.get(key) for key in scope_fields)
    methodology_changed = old.get("methodology") != new.get("methodology")
    implementation_changed = old.get("implementation") != new.get("implementation")
    old_sources = old.get("source_artifacts", [])
    new_sources = new.get("source_artifacts", [])
    source_signature = lambda rows: sorted((x.get("source"), x.get("endpoint")) for x in rows)
    source_set_changed = source_signature(old_sources) != source_signature(new_sources)
    old_quality, new_quality = old.get("quality"), new.get("quality")
    quality_changed = old_quality != new_quality
    old_hashes = sorted(x.get("sha256") for x in old_sources)
    new_hashes = sorted(x.get("sha256") for x in new_sources)
    input_data_changed = old_hashes != new_hashes
    old_metrics = _flatten_numeric(old.get("results", {}))
    new_metrics = _flatten_numeric(new.get("results", {}))
    metric_deltas = []
    for key in sorted(set(old_metrics) & set(new_metrics)):
        before, after = old_metrics[key], new_metrics[key]
        delta = after - before
        metric_deltas.append({
            "metric": key, "old": str(before), "new": str(after), "absolute_delta": str(delta),
            "relative_delta_pct": str(delta / before * Decimal(100)) if before != 0 else None,
            "old_zero_baseline": before == 0,
        })
    results_payload_changed = old.get("results") != new.get("results")
    if not scope_compatible:
        attribution = "INCOMPATIBLE_SCOPE"
    elif methodology_changed or implementation_changed or source_set_changed or quality_changed:
        attribution = "MIXED_OR_INCOMPATIBLE_CAUSES"
    elif input_data_changed and results_payload_changed:
        attribution = "COMPARABLE_OBSERVED_CHANGE_CANDIDATE"
    elif not input_data_changed and results_payload_changed:
        attribution = "INCONSISTENT_RESULTS_FOR_IDENTICAL_INPUT_HASHES"
    elif input_data_changed:
        attribution = "INPUTS_CHANGED_NO_RESULT_CHANGE"
    else:
        attribution = "NO_OBSERVED_CHANGE"
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "old_evaluation_id": old.get("evaluation_id"),
        "new_evaluation_id": new.get("evaluation_id"),
        "scope_compatible": scope_compatible,
        "methodology_changed": methodology_changed,
        "implementation_changed": implementation_changed,
        "source_set_changed": source_set_changed,
        "quality_changed": quality_changed,
        "input_data_changed": input_data_changed,
        "results_payload_changed": results_payload_changed,
        "numeric_metric_deltas": metric_deltas,
        "attribution_status": attribution,
        "interpretation": "Observed differences are not causal attribution or a prediction; comparable status only means scope, methodology, implementation, source set and declared quality match.",
        "orders_submitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--manifest", required=True)
    create.add_argument("--archive-dir", required=True)
    create.add_argument("--output-dir", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--record", required=True)
    verify.add_argument("--archive-dir")
    compare = sub.add_parser("compare")
    compare.add_argument("--old", required=True)
    compare.add_argument("--new", required=True)
    compare.add_argument("--old-archive-dir")
    compare.add_argument("--new-archive-dir")
    compare.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "create":
        record = build_evaluation_record(_read_json(args.manifest), args.archive_dir, args.output_dir)
        print(json.dumps({"evaluation_id": record["evaluation_id"], "record_sha256": record["record_sha256"], "orders_submitted": False}, indent=2))
        return 0
    if args.command == "verify":
        result = verify_evaluation_record(args.record, args.archive_dir)
        print(json.dumps({"valid": result["valid"], "errors": result["errors"]}, indent=2))
        return 0 if result["valid"] else 1
    old_result = verify_evaluation_record(args.old, args.old_archive_dir)
    new_result = verify_evaluation_record(args.new, args.new_archive_dir)
    if not old_result["valid"] or not new_result["valid"]:
        raise SystemExit(json.dumps({"error": "record verification failed", "old_errors": old_result["errors"], "new_errors": new_result["errors"]}))
    comparison = compare_evaluation_records(old_result["record"], new_result["record"])
    _write_exclusive(Path(args.output), (_json_bytes(comparison) + b"\n"))
    print(json.dumps({"output": args.output, "attribution_status": comparison["attribution_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
