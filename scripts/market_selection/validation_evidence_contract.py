"""Evidence contract for reproducible out-of-sample methodology validation.

This validates report structure and chronology, not the truth of linked artifacts or
the predictive quality of a strategy. A valid report remains INDETERMINATE until
its evidence is independently reviewed.
"""
from __future__ import annotations

import math
from urllib.parse import urlsplit

from scripts.market_selection.methodology_contract import (
    COST_COMPONENTS,
    parse_timestamp,
    validate_cost_component,
    validate_methodology,
)

VALIDATION_REPORT_SCHEMA = "crypto-investment-validation-report-v1"
_SHA256_HEX = set("0123456789abcdef")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _url(value: object, field: str) -> str:
    raw = _text(value, field)
    parsed = urlsplit(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    return raw


def _sha256(value: object, field: str) -> str:
    raw = _text(value, field).lower()
    if len(raw) != 64 or any(char not in _SHA256_HEX for char in raw):
        raise ValueError(f"{field} must be a 64-character hexadecimal SHA-256")
    return raw


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _metrics(value: object, field: str) -> dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a non-empty object of numeric metrics")
    result = {}
    for key, number in value.items():
        name = _text(key, f"{field} metric name")
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError(f"{field}.{name} must be a finite number")
        result[name] = float(number)
    return result


def validate_validation_report(report: object, methodology: object) -> dict:
    """Validate report completeness against the exact approved methodology version."""
    method = validate_methodology(methodology)
    if method["status"] != "APPROVED":
        raise ValueError("validation report requires an APPROVED methodology")
    if not isinstance(report, dict):
        raise ValueError("validation report must be an object")
    if report.get("schema_version") != VALIDATION_REPORT_SCHEMA:
        raise ValueError(f"schema_version must be {VALIDATION_REPORT_SCHEMA}")
    if report.get("methodology_id") != method["methodology_id"] or report.get("methodology_version") != method["version"]:
        raise ValueError("validation report methodology id/version does not match approved methodology")

    report_id = _text(report.get("report_id"), "report_id")
    generated_at = parse_timestamp(report.get("generated_at"), "generated_at")
    frozen_at = parse_timestamp(report.get("protocol_frozen_at"), "protocol_frozen_at")

    splits = method["validation"]["splits"]
    first_test_start = parse_timestamp(splits[0]["test_start"], "methodology first test_start")
    last_test_end = parse_timestamp(splits[-1]["test_end"], "methodology last test_end")
    if frozen_at >= first_test_start:
        raise ValueError("protocol_frozen_at must precede the first out-of-sample test window")
    if generated_at < last_test_end:
        raise ValueError("generated_at must be at or after the final out-of-sample test window")

    dataset = report.get("dataset")
    if not isinstance(dataset, dict):
        raise ValueError("dataset must be an object")
    dataset_url = _url(dataset.get("artifact_url"), "dataset.artifact_url")
    dataset_hash = _sha256(dataset.get("sha256"), "dataset.sha256")
    sample_count = _positive_int(dataset.get("sample_count"), "dataset.sample_count")
    dataset_start = parse_timestamp(dataset.get("window_start"), "dataset.window_start")
    dataset_end = parse_timestamp(dataset.get("window_end"), "dataset.window_end")
    if dataset_start >= dataset_end:
        raise ValueError("dataset window_start must precede window_end")
    if dataset_start > first_test_start or dataset_end < last_test_end:
        raise ValueError("dataset time coverage must include all declared out-of-sample test windows")
    if dataset.get("point_in_time") is not True:
        raise ValueError("dataset.point_in_time must be true")
    _text(dataset.get("universe_definition"), "dataset.universe_definition")
    delisted_policy = _text(dataset.get("delisted_asset_policy"), "dataset.delisted_asset_policy")
    if delisted_policy not in {"INCLUDED", "EXCLUDED_WITH_BIAS_DISCLOSURE", "NOT_APPLICABLE"}:
        raise ValueError("dataset.delisted_asset_policy must disclose survivorship treatment")

    results = report.get("split_results")
    if not isinstance(results, list) or len(results) != len(splits):
        raise ValueError("split_results must contain exactly one result for each methodology validation split")
    normalized_results = []
    observed_metric_names = set()
    for index, (result, split) in enumerate(zip(results, splits)):
        field = f"split_results[{index}]"
        if not isinstance(result, dict):
            raise ValueError(f"{field} must be an object")
        if result.get("split_index") != index:
            raise ValueError(f"{field}.split_index must match its ordered methodology split")
        start = parse_timestamp(result.get("test_start"), f"{field}.test_start")
        end = parse_timestamp(result.get("test_end"), f"{field}.test_end")
        if start != parse_timestamp(split["test_start"], "methodology test_start") or end != parse_timestamp(split["test_end"], "methodology test_end"):
            raise ValueError(f"{field} test window must match the pre-registered methodology split")
        metrics = _metrics(result.get("metrics"), f"{field}.metrics")
        observed_metric_names.update(metrics)
        normalized_results.append({
            "split_index": index,
            "test_start": start.isoformat().replace("+00:00", "Z"),
            "test_end": end.isoformat().replace("+00:00", "Z"),
            "sample_count": _positive_int(result.get("sample_count"), f"{field}.sample_count"),
            "metrics": metrics,
        })

    baselines = report.get("baseline_results")
    if not isinstance(baselines, list) or not baselines:
        raise ValueError("baseline_results must include at least one explicit benchmark")
    normalized_baselines = []
    for index, baseline in enumerate(baselines):
        field = f"baseline_results[{index}]"
        if not isinstance(baseline, dict):
            raise ValueError(f"{field} must be an object")
        metrics = _metrics(baseline.get("metrics"), f"{field}.metrics")
        if not (set(metrics) & observed_metric_names):
            raise ValueError(f"{field} must report at least one metric comparable to the tested method")
        normalized_baselines.append({
            "benchmark_id": _text(baseline.get("benchmark_id"), f"{field}.benchmark_id"),
            "description": _text(baseline.get("description"), f"{field}.description"),
            "metrics": metrics,
        })

    costs = report.get("realized_cost_model")
    if not isinstance(costs, dict) or set(costs) != COST_COMPONENTS:
        raise ValueError(f"realized_cost_model must explicitly define {sorted(COST_COMPONENTS)}")
    normalized_costs = {}
    for name in sorted(COST_COMPONENTS):
        cost = validate_cost_component(costs[name], f"realized_cost_model.{name}")
        if cost["status"] == "NOT_APPROVED":
            raise ValueError(f"realized_cost_model.{name} cannot remain NOT_APPROVED in a validation report")
        normalized_costs[name] = cost

    sensitivity = report.get("sensitivity_analysis")
    if not isinstance(sensitivity, list) or not sensitivity:
        raise ValueError("sensitivity_analysis must include at least one documented scenario")
    normalized_sensitivity = []
    for index, scenario in enumerate(sensitivity):
        field = f"sensitivity_analysis[{index}]"
        if not isinstance(scenario, dict):
            raise ValueError(f"{field} must be an object")
        metrics = _metrics(scenario.get("metrics"), f"{field}.metrics")
        if not (set(metrics) & observed_metric_names):
            raise ValueError(f"{field} must report at least one metric comparable to the tested method")
        normalized_sensitivity.append({
            "scenario_id": _text(scenario.get("scenario_id"), f"{field}.scenario_id"),
            "description": _text(scenario.get("description"), f"{field}.description"),
            "metrics": metrics,
        })

    uncertainty = report.get("uncertainty")
    if not isinstance(uncertainty, dict):
        raise ValueError("uncertainty must be an object")
    uncertainty_method = _text(uncertainty.get("method"), "uncertainty.method")
    confidence_level = uncertainty.get("confidence_level")
    if isinstance(confidence_level, bool) or not isinstance(confidence_level, (int, float)) or not math.isfinite(confidence_level) or not 0 < confidence_level < 1:
        raise ValueError("uncertainty.confidence_level must be strictly between 0 and 1")
    intervals = uncertainty.get("intervals")
    if not isinstance(intervals, list) or not intervals:
        raise ValueError("uncertainty.intervals must contain at least one interval")
    normalized_intervals = []
    for index, interval in enumerate(intervals):
        field = f"uncertainty.intervals[{index}]"
        if not isinstance(interval, dict):
            raise ValueError(f"{field} must be an object")
        metric = _text(interval.get("metric"), f"{field}.metric")
        lower = interval.get("lower")
        upper = interval.get("upper")
        for label, number in (("lower", lower), ("upper", upper)):
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
                raise ValueError(f"{field}.{label} must be a finite number")
        if lower > upper:
            raise ValueError(f"{field}.lower cannot exceed upper")
        normalized_intervals.append({
            "metric": metric,
            "lower": float(lower),
            "upper": float(upper),
            "sample_count": _positive_int(interval.get("sample_count"), f"{field}.sample_count"),
        })

    reproducibility = report.get("reproducibility")
    if not isinstance(reproducibility, dict):
        raise ValueError("reproducibility must be an object")
    code_version = _text(reproducibility.get("code_version"), "reproducibility.code_version")
    command = _text(reproducibility.get("command"), "reproducibility.command")
    environment_hash = _sha256(reproducibility.get("environment_sha256"), "reproducibility.environment_sha256")
    execution_url = _url(reproducibility.get("execution_artifact_url"), "reproducibility.execution_artifact_url")

    review = report.get("review")
    if not isinstance(review, dict):
        raise ValueError("review must be an object")
    review_status = _text(review.get("status"), "review.status")
    if review_status not in {"PENDING", "REVIEWED"}:
        raise ValueError("review.status must be PENDING or REVIEWED")
    normalized_review = {"status": review_status}
    if review_status == "REVIEWED":
        reviewer = _text(review.get("reviewed_by"), "review.reviewed_by")
        reviewed_at = parse_timestamp(review.get("reviewed_at"), "review.reviewed_at")
        if reviewed_at < generated_at:
            raise ValueError("review.reviewed_at cannot precede report generation")
        normalized_review.update({
            "reviewed_by": reviewer,
            "reviewed_at": reviewed_at.isoformat().replace("+00:00", "Z"),
            "evidence_url": _url(review.get("evidence_url"), "review.evidence_url"),
            "evidence_sha256": _sha256(review.get("evidence_sha256"), "review.evidence_sha256"),
        })

    return {
        "schema_version": VALIDATION_REPORT_SCHEMA,
        "report_id": report_id,
        "methodology_id": method["methodology_id"],
        "methodology_version": method["version"],
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "protocol_frozen_at": frozen_at.isoformat().replace("+00:00", "Z"),
        "dataset": {
            "artifact_url": dataset_url,
            "sha256": dataset_hash,
            "sample_count": sample_count,
            "window_start": dataset_start.isoformat().replace("+00:00", "Z"),
            "window_end": dataset_end.isoformat().replace("+00:00", "Z"),
            "point_in_time": True,
            "universe_definition": dataset["universe_definition"].strip(),
            "delisted_asset_policy": delisted_policy,
        },
        "split_results": normalized_results,
        "baseline_results": normalized_baselines,
        "realized_cost_model": normalized_costs,
        "sensitivity_analysis": normalized_sensitivity,
        "uncertainty": {
            "method": uncertainty_method,
            "confidence_level": float(confidence_level),
            "intervals": normalized_intervals,
        },
        "reproducibility": {
            "code_version": code_version,
            "command": command,
            "environment_sha256": environment_hash,
            "execution_artifact_url": execution_url,
        },
        "review": normalized_review,
        "decision_status": "INDETERMINATE",
        "interpretation": "Contract validity is not independent verification of artifacts, calibration, predictive utility, or profitability.",
        "orders_submitted": False,
    }
