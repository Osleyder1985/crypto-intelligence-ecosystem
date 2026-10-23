"""Deterministic scoring of matured point-in-time return forecasts.

This module scores forecasts against outcomes only after the target window has
closed and the outcome was observed. It does not infer trading profitability,
calibrate probabilities, or approve a methodology.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean

SCORING_SCHEMA = "crypto-investment-forecast-scoring-v1"
HORIZONS = {"short", "medium", "long"}
DECISION_MODES = {"ASSESS", "ABSTAIN"}


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a timezone-aware ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a timezone-aware ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _direction(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def score_forecast_records(records: object) -> dict:
    """Score a single compatible cohort; reject mixed asset/horizon/methodology cohorts.

    Each record contains a forecast and its matured outcome. ABSTAIN records are
    counted but excluded from forecast error metrics. Zero-return outcomes are
    excluded from directional accuracy and reported separately as direction ties.
    """
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list")

    normalized = []
    cohort = None
    seen_ids = set()
    for index, record in enumerate(records):
        field = f"records[{index}]"
        if not isinstance(record, dict):
            raise ValueError(f"{field} must be an object")
        prediction_id = _text(record.get("prediction_id"), f"{field}.prediction_id")
        if prediction_id in seen_ids:
            raise ValueError(f"duplicate prediction_id: {prediction_id}")
        seen_ids.add(prediction_id)
        asset_id = _text(record.get("asset_id"), f"{field}.asset_id")
        methodology_id = _text(record.get("methodology_id"), f"{field}.methodology_id")
        methodology_version = _text(record.get("methodology_version"), f"{field}.methodology_version")
        horizon = _text(record.get("horizon"), f"{field}.horizon")
        if horizon not in HORIZONS:
            raise ValueError(f"{field}.horizon must be short, medium, or long")
        cohort_key = (asset_id, methodology_id, methodology_version, horizon)
        if cohort is None:
            cohort = cohort_key
        elif cohort != cohort_key:
            raise ValueError("records must share asset, methodology id/version, and horizon")

        issued_at = _timestamp(record.get("issued_at"), f"{field}.issued_at")
        target_start = _timestamp(record.get("target_window_start"), f"{field}.target_window_start")
        target_end = _timestamp(record.get("target_window_end"), f"{field}.target_window_end")
        outcome_observed_at = _timestamp(record.get("outcome_observed_at"), f"{field}.outcome_observed_at")
        if not issued_at < target_start < target_end:
            raise ValueError(f"{field} requires issued_at < target_window_start < target_window_end")
        if outcome_observed_at < target_end:
            raise ValueError(f"{field}.outcome_observed_at cannot precede target_window_end")

        decision_mode = _text(record.get("decision_mode"), f"{field}.decision_mode")
        if decision_mode not in DECISION_MODES:
            raise ValueError(f"{field}.decision_mode must be ASSESS or ABSTAIN")
        actual_return = _number(record.get("actual_return"), f"{field}.actual_return")
        benchmark_return = _number(record.get("benchmark_return"), f"{field}.benchmark_return")
        forecast_return = record.get("forecast_return")
        if decision_mode == "ASSESS":
            forecast_return = _number(forecast_return, f"{field}.forecast_return")
        elif forecast_return is not None:
            raise ValueError(f"{field}.forecast_return must be null when decision_mode is ABSTAIN")
        normalized.append({
            "prediction_id": prediction_id,
            "decision_mode": decision_mode,
            "forecast_return": forecast_return,
            "actual_return": actual_return,
            "benchmark_return": benchmark_return,
        })

    assessed = [item for item in normalized if item["decision_mode"] == "ASSESS"]
    abstained = len(normalized) - len(assessed)
    if not assessed:
        metrics = None
        benchmark_metrics = None
        paired_benchmark = 0
    else:
        errors = [item["forecast_return"] - item["actual_return"] for item in assessed]
        squared_errors = [error * error for error in errors]
        direction_rows = [
            item for item in assessed
            if _direction(item["actual_return"]) != 0
        ]
        metrics = {
            "mae": mean(abs(error) for error in errors),
            "rmse": math.sqrt(mean(squared_errors)),
            "directional_accuracy": (
                sum(_direction(item["forecast_return"]) == _direction(item["actual_return"]) for item in direction_rows)
                / len(direction_rows) if direction_rows else None
            ),
            "directional_sample_count": len(direction_rows),
            "zero_actual_return_count": len(assessed) - len(direction_rows),
        }
        benchmark_errors = [item["benchmark_return"] - item["actual_return"] for item in assessed]
        benchmark_metrics = {
            "mae": mean(abs(error) for error in benchmark_errors),
            "rmse": math.sqrt(mean(error * error for error in benchmark_errors)),
            "directional_accuracy": (
                sum(_direction(item["benchmark_return"]) == _direction(item["actual_return"]) for item in direction_rows)
                / len(direction_rows) if direction_rows else None
            ),
            "directional_sample_count": len(direction_rows),
        }
        paired_benchmark = len(assessed)

    return {
        "schema_version": SCORING_SCHEMA,
        "cohort": {
            "asset_id": cohort[0],
            "methodology_id": cohort[1],
            "methodology_version": cohort[2],
            "horizon": cohort[3],
        },
        "sample_count": len(normalized),
        "assessed_count": len(assessed),
        "abstained_count": abstained,
        "coverage": len(assessed) / len(normalized),
        "scored_prediction_ids": [item["prediction_id"] for item in assessed],
        "metrics": metrics,
        "benchmark_id": "provided_per_record_benchmark",
        "benchmark_sample_count": paired_benchmark,
        "benchmark_metrics": benchmark_metrics,
        "interpretation": (
            "Descriptive forecast error only. Metrics do not establish statistical significance, "
            "calibration, causality, strategy profitability, or future performance. "
            "Benchmark comparison is paired on assessed records; abstention coverage must be considered."
        ),
        "decision_status": "INDETERMINATE",
        "orders_submitted": False,
    }
