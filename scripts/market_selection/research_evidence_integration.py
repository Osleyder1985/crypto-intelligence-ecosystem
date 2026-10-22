"""Join validated event, fundamental/on-chain, and methodology evidence into a report.

This is an offline integration layer. It does not fetch sources, train/evaluate models,
approve methodology, infer causality, or issue investment recommendations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.market_selection.external_event_evidence import assess_temporal_association, validate_event
from scripts.market_selection.fundamental_onchain_contract import evaluate_observations
from scripts.market_selection.methodology_contract import validate_methodology
from scripts.market_selection.provider_license_gate import evaluate_artifact_use

REPORT_SCHEMA = "crypto-asset-research-report-v2"
BUNDLE_SCHEMA = "crypto-research-evidence-bundle-v1"


def _object(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp with offset")
    return value.strip()


def enrich_research_report(
    report: dict,
    *,
    events: list[dict],
    observations: list[dict],
    methodology: dict,
    asset: dict,
    evaluation_as_of: str,
) -> dict:
    """Validate and attach supplied evidence while retaining fail-closed decision states.

    Each event item is an object with an `event` record and a declared `movement_window`
    containing `start` and `end`. Capture/publication timestamps are validated by the
    source-neutral event contract. Observations and methodology use their own versioned
    contracts. The function never upgrades INDETERMINATE to a favorable/unfavorable decision.
    """
    report = _object(report, "report")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError(f"report.schema_version must be {REPORT_SCHEMA}")
    provider_use = evaluate_artifact_use(report, "internal_analysis")
    if provider_use["decision"] != "ALLOW":
        raise PermissionError("evidence integration blocked before use: " + ",".join(provider_use["reason_codes"]))
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    asset = _object(asset, "asset")
    stable_id = asset.get("stable_id")
    category = asset.get("category")
    if not isinstance(stable_id, str) or not stable_id.strip():
        raise ValueError("asset.stable_id must be a non-empty stable identifier")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("asset.category must be non-empty")
    cutoff = _timestamp(evaluation_as_of, "evaluation_as_of")

    validated_methodology = validate_methodology(methodology)
    event_assessments = []
    seen_event_ids = set()
    for index, item in enumerate(events):
        item = _object(item, f"events[{index}]")
        event = validate_event(item.get("event"))
        event_id = event["event_id"]
        if event_id in seen_event_ids:
            raise ValueError(f"duplicate event_id in evidence bundle: {event_id}")
        seen_event_ids.add(event_id)
        window = _object(item.get("movement_window"), f"events[{index}].movement_window")
        assessment = assess_temporal_association(
            event,
            movement_start=_timestamp(window.get("start"), f"events[{index}].movement_window.start"),
            movement_end=_timestamp(window.get("end"), f"events[{index}].movement_window.end"),
            evaluation_as_of=cutoff,
            target_entity=item.get("target_entity") or {},
        )
        event_assessments.append(assessment)

    fundamental = evaluate_observations(
        observations,
        asset={"stable_id": stable_id.strip(), "category": category.strip()},
        evaluation_as_of=cutoff,
    )

    horizons = report.get("horizons")
    if not isinstance(horizons, dict) or set(horizons) != {"short", "medium", "long"}:
        raise ValueError("report.horizons must define exactly short, medium, and long")
    output = dict(report)
    output["external_event_evidence"] = {
        "schema_version": "crypto-event-evidence-assessment-v1",
        "status": "ASSESSED" if event_assessments else "NOT_AVAILABLE",
        "event_count": len(event_assessments),
        "assessments": event_assessments,
        "causality_claimed": False,
        "interpretation": "Temporal association is not proof of causality; event absence does not prove no catalyst existed.",
    }
    output["fundamental_onchain_assessment"] = fundamental
    output["downstream_use_assessment"] = provider_use
    output["methodology_assessment"] = {
        "schema_version": validated_methodology["schema_version"],
        "methodology_id": validated_methodology["methodology_id"],
        "version": validated_methodology["version"],
        "status": validated_methodology["status"],
        "horizons": validated_methodology["horizons"],
        "threshold_policy_status": validated_methodology["threshold_policy"]["status"],
        "cost_components": validated_methodology["cost_model"],
        "contract_valid": True,
        "predictive_performance_validated": False,
        "investment_methodology_approved": validated_methodology["status"] == "APPROVED",
    }
    output["evidence_bundle"] = {
        "schema_version": BUNDLE_SCHEMA,
        "asset": {"stable_id": stable_id.strip(), "category": category.strip()},
        "evaluation_as_of": cutoff,
        "events_supplied": len(events),
        "fundamental_observations_supplied": len(observations),
    }
    output["decision_status"] = "INDETERMINATE"
    for horizon in ("short", "medium", "long"):
        output["horizons"][horizon] = dict(output["horizons"][horizon])
        output["horizons"][horizon]["status"] = "INDETERMINATE"
        output["horizons"][horizon]["conclusion"] = "INDETERMINATE"
        reasons = list(output["horizons"][horizon].get("reason_codes", []))
        for reason in ("PREDICTIVE_PERFORMANCE_NOT_VALIDATED", "EVIDENCE_INTEGRATION_IS_NOT_AN_INVESTMENT_SIGNAL"):
            if reason not in reasons:
                reasons.append(reason)
        output["horizons"][horizon]["reason_codes"] = reasons
    output["limitations"] = list(output.get("limitations", []))
    output["limitations"].append(
        "External events and fundamental/on-chain observations are contract-validated supplied inputs; this command does not fetch sources or prove their authority, completeness, licensing, or predictive value."
    )
    output["limitations"].append(
        "Methodology contract validity is not a backtest result; no predictive performance, calibrated confidence, or investment recommendation is claimed."
    )
    output["network_requests_made"] = False
    output["orders_submitted"] = False
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="Existing crypto-asset-research-report-v1 JSON")
    parser.add_argument("--events", required=True, type=Path, help="JSON array of event records with movement windows")
    parser.add_argument("--observations", required=True, type=Path, help="JSON array of fundamental/on-chain observations")
    parser.add_argument("--methodology", required=True, type=Path, help="Versioned crypto-investment-methodology-v1 JSON")
    parser.add_argument("--asset-stable-id", required=True)
    parser.add_argument("--asset-category", required=True)
    parser.add_argument("--evaluation-as-of", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    events = json.loads(args.events.read_text(encoding="utf-8"))
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    methodology = json.loads(args.methodology.read_text(encoding="utf-8"))
    enriched = enrich_research_report(
        report,
        events=events,
        observations=observations,
        methodology=methodology,
        asset={"stable_id": args.asset_stable_id, "category": args.asset_category},
        evaluation_as_of=args.evaluation_as_of,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "schema_version": enriched["schema_version"],
        "decision_status": enriched["decision_status"],
        "event_count": enriched["external_event_evidence"]["event_count"],
        "observed_fundamental_metrics": enriched["fundamental_onchain_assessment"]["coverage"]["observed_metric_count"],
        "predictive_performance_validated": enriched["methodology_assessment"]["predictive_performance_validated"],
        "orders_submitted": enriched["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
