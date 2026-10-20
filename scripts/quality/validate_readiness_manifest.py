#!/usr/bin/env python3
"""Validate an operational-readiness evidence manifest without claiming readiness.

This checks evidence completeness and fail-closed decision rules only. It does not
execute integration, security, backup/restore, monitoring, or rollback tests.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REQUIRED_GATES = {
    "integration",
    "end_to_end",
    "security",
    "performance",
    "backup_restore",
    "observability_alerting",
    "runbooks",
    "rollback",
    "defects_exceptions",
}
VALID_STATUSES = {"NOT_RUN", "PASS", "FAIL", "INDETERMINATE"}
REQUIRED_TOP_LEVEL = {
    "case_id", "product_version", "product_sha", "environment",
    "executed_at_utc", "executor", "independent_reviewer",
    "risk_acceptance_authority", "gates", "residual_risks",
}


def _nonempty(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not any(token in value.strip().lower() for token in (
            "pending", "pendiente", "unknown", "desconocido", "n/a"
        ))
    )


def validate_manifest(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["La raíz del manifiesto debe ser un objeto JSON."]

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        return [f"Falta el campo obligatorio: {key}" for key in missing]

    for key in ("case_id", "product_version", "product_sha", "environment", "executor"):
        if not _nonempty(data.get(key)):
            errors.append(f"{key}: debe contener un valor concreto.")

    timestamp = data.get("executed_at_utc")
    if not _nonempty(timestamp):
        errors.append("executed_at_utc: debe ser una fecha ISO 8601 UTC terminada en Z.")
    else:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if not timestamp.endswith("Z") or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
                raise ValueError("not UTC Z")
        except (ValueError, TypeError, AttributeError):
            errors.append("executed_at_utc: formato inválido; use ISO 8601 UTC terminado en Z.")

    for key in ("independent_reviewer", "risk_acceptance_authority"):
        if not _nonempty(data.get(key)):
            errors.append(f"{key}: debe identificar un responsable/rol o indicar una excepción documentada.")

    gates = data.get("gates")
    if not isinstance(gates, list):
        errors.append("gates: debe ser una lista.")
        gates = []

    seen: set[str] = set()
    for index, gate in enumerate(gates):
        prefix = f"gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{prefix}: debe ser un objeto.")
            continue
        gate_id = gate.get("id")
        if not isinstance(gate_id, str) or gate_id not in REQUIRED_GATES:
            errors.append(f"{prefix}.id: puerta desconocida o inválida.")
            continue
        if gate_id in seen:
            errors.append(f"Puerta duplicada: {gate_id}.")
        seen.add(gate_id)

        status = gate.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{gate_id}.status: debe ser uno de {', '.join(sorted(VALID_STATUSES))}.")
            continue
        if status == "PASS":
            if not _nonempty(gate.get("observed_result")):
                errors.append(f"{gate_id}: PASS requiere observed_result concreto.")
            evidence = gate.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(_nonempty(item) for item in evidence):
                errors.append(f"{gate_id}: PASS requiere al menos una referencia de evidencia verificable.")
            if not _nonempty(gate.get("executed_at_utc")):
                errors.append(f"{gate_id}: PASS requiere executed_at_utc.")
        elif status in {"FAIL", "INDETERMINATE"} and not _nonempty(gate.get("reason")):
            errors.append(f"{gate_id}: {status} requiere explicar el motivo.")

    missing_gates = sorted(REQUIRED_GATES - seen)
    for gate_id in missing_gates:
        errors.append(f"Falta la puerta obligatoria: {gate_id}.")

    risks = data.get("residual_risks")
    if not isinstance(risks, list):
        errors.append("residual_risks: debe ser una lista.")
        risks = []
    for index, risk in enumerate(risks):
        if not isinstance(risk, dict):
            errors.append(f"residual_risks[{index}]: debe ser un objeto.")
            continue
        severity = risk.get("severity")
        normalized_severity = severity.strip().lower() if isinstance(severity, str) else ""
        high_risk = normalized_severity in {"critical", "high", "crítica", "critica", "alta"}
        if high_risk:
            approved = risk.get("status") == "approved_exception"
            exception_complete = all(
                _nonempty(risk.get(field))
                for field in ("approved_by", "justification", "expires_at_utc")
            )
            if not approved or not exception_complete:
                errors.append(
                    f"Riesgo residual crítico/alto sin excepción aprobada completa "
                    f"(status, approved_by, justification y expires_at_utc): índice {index}."
                )
            else:
                try:
                    expiry = datetime.fromisoformat(
                        risk["expires_at_utc"].replace("Z", "+00:00")
                    )
                    if not risk["expires_at_utc"].endswith("Z") or expiry.utcoffset() is None or expiry.utcoffset().total_seconds() != 0:
                        raise ValueError("not UTC Z")
                except (ValueError, TypeError, AttributeError):
                    errors.append(
                        f"Riesgo residual crítico/alto: expires_at_utc debe ser ISO 8601 UTC terminado en Z: índice {index}."
                    )

    declared = data.get("decision")
    all_pass = len(seen) == len(REQUIRED_GATES) and all(
        isinstance(g, dict) and g.get("id") in REQUIRED_GATES and g.get("status") == "PASS"
        for g in gates
    )
    if declared == "READY" and (errors or not all_pass):
        errors.append("decision=READY no permitido: hay errores o puertas que no están todas en PASS.")
    if declared not in {"NOT_READY", "READY"}:
        errors.append("decision: debe ser NOT_READY o READY.")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Uso: python scripts/quality/validate_readiness_manifest.py <manifiesto.json>", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: no se pudo leer el manifiesto: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(data)
    if errors:
        print("FAIL: manifiesto de readiness incompleto o incoherente.")
        for error in errors:
            print(f"- {error}")
        print("La validación del manifiesto no ejecuta pruebas operativas ni certifica el producto.")
        return 1
    print(f"PASS: estructura y reglas del manifiesto válidas (decisión declarada: {data['decision']}).")
    print("LÍMITE: no verifica externamente los artefactos ni demuestra por sí sola la preparación para producción.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
