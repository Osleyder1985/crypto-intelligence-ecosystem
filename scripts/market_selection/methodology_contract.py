"""Versioned investment-horizon methodology and anti-look-ahead contracts.

This module validates configuration and prediction evidence. It does not choose thresholds,
train models, forecast returns, or approve a strategy.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
from urllib.parse import urlsplit

METHODOLOGY_SCHEMA = "crypto-investment-methodology-v1"
PREDICTION_SCHEMA = "crypto-investment-prediction-v1"
HORIZONS = {"short", "medium", "long"}
COST_COMPONENTS = {"fees", "spread", "slippage", "funding_or_borrow", "other"}


def parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


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


def _finite_number(value: object, field: str, *, minimum: float | None = None,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field} must be <= {maximum}")
    return float(value)


def validate_cost_component(component: object, field: str) -> dict:
    if not isinstance(component, dict):
        raise ValueError(f"{field} must be an object")
    status = _text(component.get("status"), f"{field}.status")
    allowed = {"MEASURED", "ESTIMATED", "NOT_APPLICABLE", "NOT_AVAILABLE", "NOT_APPROVED"}
    if status not in allowed:
        raise ValueError(f"{field}.status must be one of {sorted(allowed)}")
    value = component.get("basis_points")
    if status in {"MEASURED", "ESTIMATED"}:
        value = _finite_number(value, f"{field}.basis_points", minimum=0)
    elif value is not None:
        raise ValueError(f"{field}.basis_points must be null unless measured or estimated")
    if status == "NOT_APPLICABLE":
        _text(component.get("reason"), f"{field}.reason")
    return {"status": status, "basis_points": value, "reason": component.get("reason")}


def validate_methodology(methodology: object) -> dict:
    if not isinstance(methodology, dict):
        raise ValueError("methodology must be an object")
    if methodology.get("schema_version") != METHODOLOGY_SCHEMA:
        raise ValueError(f"schema_version must be {METHODOLOGY_SCHEMA}")
    methodology_id = _text(methodology.get("methodology_id"), "methodology_id")
    version = _text(methodology.get("version"), "version")
    status = _text(methodology.get("status"), "status")
    if status not in {"DRAFT", "APPROVED", "RETIRED"}:
        raise ValueError("status must be DRAFT, APPROVED, or RETIRED")
    created_at = parse_timestamp(methodology.get("created_at"), "created_at")
    approval = methodology.get("approval")
    if status == "APPROVED":
        if not isinstance(approval, dict):
            raise ValueError("APPROVED methodology requires an approval record")
        _text(approval.get("approved_by"), "approval.approved_by")
        parse_timestamp(approval.get("approved_at"), "approval.approved_at")
        _url(approval.get("evidence_url"), "approval.evidence_url")

    horizons = methodology.get("horizons")
    if not isinstance(horizons, dict) or set(horizons) != HORIZONS:
        raise ValueError("horizons must define exactly short, medium, and long")
    normalized_horizons = {}
    durations = []
    for horizon in sorted(HORIZONS):
        spec = horizons[horizon]
        if not isinstance(spec, dict):
            raise ValueError(f"horizons.{horizon} must be an object")
        seconds = _finite_number(spec.get("target_window_seconds"), f"horizons.{horizon}.target_window_seconds", minimum=1)
        target = _text(spec.get("target"), f"horizons.{horizon}.target")
        unit = _text(spec.get("target_unit"), f"horizons.{horizon}.target_unit")
        normalized_horizons[horizon] = {
            "target_window_seconds": int(seconds),
            "target": target,
            "target_unit": unit,
            "description": _text(spec.get("description"), f"horizons.{horizon}.description"),
        }
        durations.append(seconds)
    if not durations[0] < durations[1] < durations[2]:
        raise ValueError("horizon windows must be strictly ordered short < medium < long")

    target_definition = methodology.get("target_definition")
    if not isinstance(target_definition, dict):
        raise ValueError("target_definition must be an object")
    _text(target_definition.get("formula"), "target_definition.formula")
    _text(target_definition.get("price_source"), "target_definition.price_source")
    _text(target_definition.get("sampling_rule"), "target_definition.sampling_rule")
    threshold_policy = methodology.get("threshold_policy")
    if not isinstance(threshold_policy, dict):
        raise ValueError("threshold_policy must be an object")
    threshold_status = _text(threshold_policy.get("status"), "threshold_policy.status")
    if threshold_status not in {"NOT_APPROVED", "APPROVED"}:
        raise ValueError("threshold_policy.status must be NOT_APPROVED or APPROVED")
    if threshold_status == "APPROVED":
        _text(threshold_policy.get("approval_evidence"), "threshold_policy.approval_evidence")
        favorable = _finite_number(threshold_policy.get("favorable_threshold"), "favorable_threshold")
        unfavorable = _finite_number(threshold_policy.get("unfavorable_threshold"), "unfavorable_threshold")
        if favorable <= unfavorable:
            raise ValueError("favorable_threshold must be greater than unfavorable_threshold")

    validation = methodology.get("validation")
    if not isinstance(validation, dict):
        raise ValueError("validation must be an object")
    for flag in ("walk_forward", "out_of_sample", "leakage_checks"):
        if validation.get(flag) is not True:
            raise ValueError(f"validation.{flag} must be true")
    splits = validation.get("splits")
    if not isinstance(splits, list) or not splits:
        raise ValueError("validation.splits must be a non-empty list")
    normalized_splits = []
    previous_test_end = None
    for index, split in enumerate(splits):
        if not isinstance(split, dict):
            raise ValueError(f"validation.splits[{index}] must be an object")
        train_end = parse_timestamp(split.get("train_end"), f"splits[{index}].train_end")
        test_start = parse_timestamp(split.get("test_start"), f"splits[{index}].test_start")
        test_end = parse_timestamp(split.get("test_end"), f"splits[{index}].test_end")
        if not train_end < test_start < test_end:
            raise ValueError(f"validation.splits[{index}] must satisfy train_end < test_start < test_end")
        if previous_test_end is not None and test_start < previous_test_end:
            raise ValueError("validation test splits must not overlap or move backward")
        previous_test_end = test_end
        normalized_splits.append({
            "train_end": train_end.isoformat().replace("+00:00", "Z"),
            "test_start": test_start.isoformat().replace("+00:00", "Z"),
            "test_end": test_end.isoformat().replace("+00:00", "Z"),
        })

    costs = methodology.get("cost_model")
    if not isinstance(costs, dict) or set(costs) != COST_COMPONENTS:
        raise ValueError(f"cost_model must explicitly define {sorted(COST_COMPONENTS)}")
    normalized_costs = {name: validate_cost_component(costs[name], f"cost_model.{name}") for name in sorted(COST_COMPONENTS)}
    features = methodology.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("features must be a non-empty list")
    normalized_features = []
    seen_features = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ValueError(f"features[{index}] must be an object")
        feature_id = _text(feature.get("feature_id"), f"features[{index}].feature_id")
        if feature_id in seen_features:
            raise ValueError(f"duplicate feature_id: {feature_id}")
        seen_features.add(feature_id)
        normalized_features.append({
            "feature_id": feature_id,
            "source_id": _text(feature.get("source_id"), f"features[{index}].source_id"),
            "availability_timestamp_field": _text(feature.get("availability_timestamp_field"), f"features[{index}].availability_timestamp_field"),
            "transformation_version": _text(feature.get("transformation_version"), f"features[{index}].transformation_version"),
        })
    return {
        "schema_version": METHODOLOGY_SCHEMA,
        "methodology_id": methodology_id,
        "version": version,
        "status": status,
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "horizons": normalized_horizons,
        "target_definition": target_definition,
        "threshold_policy": threshold_policy,
        "validation": {**validation, "splits": normalized_splits},
        "cost_model": normalized_costs,
        "features": normalized_features,
        "decision_status": "INDETERMINATE",
        "decision_reasons": [
            "This validator checks contract integrity only; it does not validate predictive performance.",
            "A methodology must be approved and evaluated out-of-sample before its outputs can support an investment conclusion.",
        ],
    }


def validate_prediction_record(record: object, methodology: object) -> dict:
    """Validate one prediction's identity and temporal boundary against its methodology."""
    method = validate_methodology(methodology)
    if not isinstance(record, dict):
        raise ValueError("prediction record must be an object")
    if record.get("schema_version") != PREDICTION_SCHEMA:
        raise ValueError(f"schema_version must be {PREDICTION_SCHEMA}")
    if record.get("methodology_id") != method["methodology_id"] or record.get("methodology_version") != method["version"]:
        raise ValueError("prediction methodology id/version does not match validated methodology")
    asset = record.get("asset")
    if not isinstance(asset, dict):
        raise ValueError("asset must be an object")
    stable_id = _text(asset.get("stable_id"), "asset.stable_id")
    category = _text(asset.get("category"), "asset.category")
    horizon = _text(record.get("horizon"), "horizon")
    if horizon not in HORIZONS:
        raise ValueError("horizon must be short, medium, or long")
    generated = parse_timestamp(record.get("generated_at"), "generated_at")
    data_as_of = parse_timestamp(record.get("data_as_of"), "data_as_of")
    train_end = parse_timestamp(record.get("model_training_data_end"), "model_training_data_end")
    target_start = parse_timestamp(record.get("target_window_start"), "target_window_start")
    target_end = parse_timestamp(record.get("target_window_end"), "target_window_end")
    if data_as_of > generated:
        raise ValueError("data_as_of cannot be after generated_at")
    if train_end >= generated:
        raise ValueError("model_training_data_end must precede generated_at")
    if target_start <= generated:
        raise ValueError("target_window_start must be after generated_at")
    if target_end <= target_start:
        raise ValueError("target_window_end must be after target_window_start")
    required_window = method["horizons"][horizon]["target_window_seconds"]
    if (target_end - target_start).total_seconds() != required_window:
        raise ValueError("prediction target window does not match the versioned methodology horizon")
    if method["status"] != "APPROVED":
        raise ValueError("predictions cannot be validated for a non-APPROVED methodology")
    features = record.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("prediction must include feature observations")
    allowed_ids = {item["feature_id"] for item in method["features"]}
    seen = set()
    normalized_features = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ValueError(f"features[{index}] must be an object")
        feature_id = _text(feature.get("feature_id"), f"features[{index}].feature_id")
        if feature_id not in allowed_ids:
            raise ValueError(f"feature_id not declared in methodology: {feature_id}")
        if feature_id in seen:
            raise ValueError(f"duplicate prediction feature: {feature_id}")
        seen.add(feature_id)
        observed = parse_timestamp(feature.get("observed_at"), f"features[{index}].observed_at")
        captured = parse_timestamp(feature.get("captured_at"), f"features[{index}].captured_at")
        if captured > data_as_of or observed > data_as_of:
            raise ValueError(f"feature {feature_id} was not available at data_as_of")
        if captured < observed:
            raise ValueError(f"feature {feature_id} capture precedes observation")
        normalized_features.append({
            "feature_id": feature_id,
            "source_id": _text(feature.get("source_id"), f"features[{index}].source_id"),
            "observed_at": observed.isoformat().replace("+00:00", "Z"),
            "captured_at": captured.isoformat().replace("+00:00", "Z"),
        })
    output = record.get("output")
    if not isinstance(output, dict):
        raise ValueError("output must be an object")
    normalized_output = {}
    if "expected_return" in output:
        normalized_output["expected_return"] = _finite_number(output["expected_return"], "output.expected_return")
    if "probability_up" in output:
        normalized_output["probability_up"] = _finite_number(output["probability_up"], "output.probability_up", minimum=0, maximum=1)
    if not normalized_output:
        raise ValueError("output must contain expected_return and/or probability_up")
    return {
        "schema_version": PREDICTION_SCHEMA,
        "prediction_id": _text(record.get("prediction_id"), "prediction_id"),
        "methodology_id": method["methodology_id"],
        "methodology_version": method["version"],
        "asset": {"stable_id": stable_id, "category": category},
        "horizon": horizon,
        "generated_at": generated.isoformat().replace("+00:00", "Z"),
        "data_as_of": data_as_of.isoformat().replace("+00:00", "Z"),
        "model_training_data_end": train_end.isoformat().replace("+00:00", "Z"),
        "target_window_start": target_start.isoformat().replace("+00:00", "Z"),
        "target_window_end": target_end.isoformat().replace("+00:00", "Z"),
        "features": normalized_features,
        "output": normalized_output,
        "decision_status": "INDETERMINATE",
        "orders_submitted": False,
    }
