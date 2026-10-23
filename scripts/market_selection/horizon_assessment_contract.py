"""Independent short/medium/long horizon assessment contract.

This module validates evidence separation and temporal availability. It does not
score assets, choose factors, infer causality, or make investment recommendations.
"""
from __future__ import annotations

from scripts.market_selection.methodology_contract import parse_timestamp

ASSESSMENT_SCHEMA = "crypto-investment-horizon-assessment-v1"
HORIZONS = ("short", "medium", "long")
FACTOR_CATEGORIES = {"MARKET_STRUCTURE", "PRICE_VOLUME", "LIQUIDITY", "EXTERNAL_EVENT", "FUNDAMENTAL", "ON_CHAIN", "MACRO", "OTHER"}
FACTOR_DECISIONS = {"INCLUDED", "EXCLUDED"}
DIMENSION_STATUSES = {"SUPPORTED", "LIMITED", "INSUFFICIENT", "CONFLICTING", "INDETERMINATE"}
SCENARIOS = {"FAVORABLE", "BASE", "ADVERSE"}


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _dimension(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    status = _text(value.get("status"), f"{field}.status")
    if status not in DIMENSION_STATUSES:
        raise ValueError(f"{field}.status must be one of {sorted(DIMENSION_STATUSES)}")
    return {
        "status": status,
        "rationale": _text(value.get("rationale"), f"{field}.rationale"),
        "evidence_refs": _string_list(value.get("evidence_refs"), f"{field}.evidence_refs"),
    }


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    result = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{field}[{index}]"))
    if len(set(result)) != len(result):
        raise ValueError(f"{field} must not contain duplicates")
    return result


def validate_horizon_assessment(record: object) -> dict:
    """Validate separate horizon conclusions, factor provenance, scenarios and abstention."""
    if not isinstance(record, dict):
        raise ValueError("assessment must be an object")
    if record.get("schema_version") != ASSESSMENT_SCHEMA:
        raise ValueError(f"schema_version must be {ASSESSMENT_SCHEMA}")
    assessment_id = _text(record.get("assessment_id"), "assessment_id")
    methodology_id = _text(record.get("methodology_id"), "methodology_id")
    methodology_version = _text(record.get("methodology_version"), "methodology_version")
    asset_id = _text(record.get("asset_id"), "asset_id")
    generated_at = parse_timestamp(record.get("generated_at"), "generated_at")
    data_as_of = parse_timestamp(record.get("data_as_of"), "data_as_of")
    if data_as_of > generated_at:
        raise ValueError("data_as_of cannot be after generated_at")

    assessments = record.get("horizons")
    if not isinstance(assessments, dict) or set(assessments) != set(HORIZONS):
        raise ValueError("horizons must define exactly short, medium, and long")
    normalized = {}
    for horizon in HORIZONS:
        item = assessments[horizon]
        field = f"horizons.{horizon}"
        if not isinstance(item, dict):
            raise ValueError(f"{field} must be an object")
        conclusion = _text(item.get("conclusion"), f"{field}.conclusion")
        if conclusion not in {"FAVORABLE", "BASE", "ADVERSE", "INDETERMINATE"}:
            raise ValueError(f"{field}.conclusion is invalid")
        abstention = _text(item.get("decision_mode"), f"{field}.decision_mode")
        if abstention not in {"ASSESS", "ABSTAIN"}:
            raise ValueError(f"{field}.decision_mode must be ASSESS or ABSTAIN")
        abstention_reasons = item.get("abstention_reasons", [])
        if not isinstance(abstention_reasons, list) or any(not isinstance(x, str) or not x.strip() for x in abstention_reasons):
            raise ValueError(f"{field}.abstention_reasons must be a list of non-empty strings")
        if abstention == "ABSTAIN":
            if not abstention_reasons:
                raise ValueError(f"{field}.abstention_reasons required when abstaining")
            if conclusion != "INDETERMINATE":
                raise ValueError(f"{field}.conclusion must be INDETERMINATE when abstaining")
        elif abstention_reasons:
            raise ValueError(f"{field}.abstention_reasons must be empty when decision_mode is ASSESS")

        dimensions = {}
        for dimension_name in ("evidence_quality", "asset_risk", "horizon_opportunity", "confidence"):
            dimensions[dimension_name] = _dimension(item.get(dimension_name), f"{field}.{dimension_name}")

        factors = item.get("factors")
        if not isinstance(factors, list) or not factors:
            raise ValueError(f"{field}.factors must be a non-empty list, including exclusions")
        normalized_factors = []
        seen = set()
        for index, factor in enumerate(factors):
            ffield = f"{field}.factors[{index}]"
            if not isinstance(factor, dict):
                raise ValueError(f"{ffield} must be an object")
            factor_id = _text(factor.get("factor_id"), f"{ffield}.factor_id")
            if factor_id in seen:
                raise ValueError(f"{field} contains duplicate factor_id: {factor_id}")
            seen.add(factor_id)
            category = _text(factor.get("category"), f"{ffield}.category")
            if category not in FACTOR_CATEGORIES:
                raise ValueError(f"{ffield}.category is invalid")
            decision = _text(factor.get("decision"), f"{ffield}.decision")
            if decision not in FACTOR_DECISIONS:
                raise ValueError(f"{ffield}.decision must be INCLUDED or EXCLUDED")
            observed_at = parse_timestamp(factor.get("observed_at"), f"{ffield}.observed_at")
            captured_at = parse_timestamp(factor.get("captured_at"), f"{ffield}.captured_at")
            if observed_at > data_as_of or captured_at > data_as_of:
                raise ValueError(f"{ffield} was not available at data_as_of")
            if captured_at < observed_at:
                raise ValueError(f"{ffield}.captured_at cannot precede observed_at")
            normalized_factors.append({
                "factor_id": factor_id,
                "category": category,
                "decision": decision,
                "rationale": _text(factor.get("rationale"), f"{ffield}.rationale"),
                "source_id": _text(factor.get("source_id"), f"{ffield}.source_id"),
                "transformation_version": _text(factor.get("transformation_version"), f"{ffield}.transformation_version"),
                "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
                "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
            })

        scenarios = item.get("scenarios")
        if not isinstance(scenarios, dict) or set(scenarios) != SCENARIOS:
            raise ValueError(f"{field}.scenarios must define FAVORABLE, BASE, and ADVERSE")
        normalized_scenarios = {}
        for scenario_name in ("FAVORABLE", "BASE", "ADVERSE"):
            scenario = scenarios[scenario_name]
            sfield = f"{field}.scenarios.{scenario_name}"
            if not isinstance(scenario, dict):
                raise ValueError(f"{sfield} must be an object")
            normalized_scenarios[scenario_name] = {
                "conditions": _string_list(scenario.get("conditions"), f"{sfield}.conditions"),
                "invalidation_rules": _string_list(scenario.get("invalidation_rules"), f"{sfield}.invalidation_rules"),
            }
        normalized[horizon] = {
            "conclusion": conclusion,
            "decision_mode": abstention,
            "abstention_reasons": [x.strip() for x in abstention_reasons],
            **dimensions,
            "factors": normalized_factors,
            "scenarios": normalized_scenarios,
        }

    return {
        "schema_version": ASSESSMENT_SCHEMA,
        "assessment_id": assessment_id,
        "methodology_id": methodology_id,
        "methodology_version": methodology_version,
        "asset_id": asset_id,
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "data_as_of": data_as_of.isoformat().replace("+00:00", "Z"),
        "horizons": normalized,
        "aggregation": "NONE",
        "decision_status": "INDETERMINATE",
        "orders_submitted": False,
        "interpretation": "Contract validity does not establish predictive utility, causal attribution, calibration, or profitability.",
    }
