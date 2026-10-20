#!/usr/bin/env python3
"""Validate requirements-catalogue structure and traceability deterministically."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs" / "engineering" / "requirements-traceability-catalog.md"
ENGINEERING_DIR = ROOT / "docs" / "engineering"
CLOSURE_MATRIX = ENGINEERING_DIR / "acceptance-closure-matrix-issues-7-13.md"
SPOT_METHOD = ENGINEERING_DIR / "spot-market-selection-methodology.md"
PRIORITY_RANK = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}
PRODUCT_ID = re.compile(r"REQ-P-\d{3}")
NFR_ID = re.compile(r"NFR-\d{3}")
INDEX_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*F(\d+)\s+—[^|]*\|\s*"
    r"((?:REQ-P|NFR)-\d{3})\s*\|\s*(Crítica|Alta|Media|Baja)\s*\|"
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def validate_index(
    section: str,
    expected_ids: set[str],
    prefix: str,
    source_priorities: dict[str, str] | None = None,
) -> list[str]:
    errors: list[str] = []
    rows: list[tuple[int, int, str, str]] = []
    for line in section.splitlines():
        match = INDEX_ROW.match(line)
        if match:
            ordinal, phase, requirement_id, priority = match.groups()
            if not requirement_id.startswith(prefix):
                errors.append(f"{prefix} index contains wrong ID family: {requirement_id}")
            rows.append((int(ordinal), int(phase), requirement_id, priority))

    ids = [row[2] for row in rows]
    if not rows:
        return [f"{prefix} index has no parseable rows"]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"{prefix} index has duplicate IDs: {', '.join(duplicates)}")
    missing, extra = sorted(expected_ids - set(ids)), sorted(set(ids) - expected_ids)
    if missing:
        errors.append(f"{prefix} index is missing: {', '.join(missing)}")
    if extra:
        errors.append(f"{prefix} index has undefined IDs: {', '.join(extra)}")

    for position, row in enumerate(rows, start=1):
        if row[0] != position:
            errors.append(f"{prefix} index ordinal {row[0]} should be {position}")

    for previous, current in zip(rows, rows[1:]):
        _, p_phase, p_id, p_priority = previous
        _, c_phase, c_id, c_priority = current
        if c_phase < p_phase:
            errors.append(f"{prefix} index phase decreases: {p_id} before {c_id}")
        elif c_phase == p_phase:
            if PRIORITY_RANK[c_priority] < PRIORITY_RANK[p_priority]:
                errors.append(f"{prefix} priority order is invalid: {p_id} before {c_id}")
            elif c_priority == p_priority and c_id < p_id:
                errors.append(f"{prefix} ID tie-break order is invalid: {p_id} before {c_id}")

    if source_priorities is not None:
        for _, _, requirement_id, priority in rows:
            expected = source_priorities.get(requirement_id)
            if expected and priority != expected:
                errors.append(
                    f"{requirement_id} priority differs: catalogue={expected}, index={priority}"
                )
    return errors


def validate_catalog(content: str) -> list[str]:
    errors: list[str] = []
    product_rows: dict[str, tuple[int, str]] = {}
    nfr_rows: dict[str, int] = {}

    for line_no, line in enumerate(content.splitlines(), start=1):
        if not line.startswith("|"):
            continue
        row = cells(line)
        if not row:
            continue
        if PRODUCT_ID.fullmatch(row[0]):
            requirement_id = row[0]
            if requirement_id in product_rows:
                errors.append(f"duplicate product requirement {requirement_id} at line {line_no}")
                continue
            if len(row) < 7:
                errors.append(f"{requirement_id} row has {len(row)} cells; expected at least 7 including responsible role")
                continue
            fields = {
                "description": row[1],
                "priority": row[2],
                "acceptance": row[3],
                "evidence": row[4],
                "status": row[5],
                "responsible role": row[6],
            }
            for name, value in fields.items():
                if not value:
                    errors.append(f"{requirement_id} has empty {name} at line {line_no}")
            if row[2] not in PRIORITY_RANK:
                errors.append(f"{requirement_id} has invalid priority {row[2]!r}")
            if row[6] == "Por asignar":
                errors.append(f"{requirement_id} has no proposed responsible role at line {line_no}")
            product_rows[requirement_id] = (line_no, row[2])
        elif NFR_ID.fullmatch(row[0]):
            requirement_id = row[0]
            if requirement_id in nfr_rows:
                errors.append(f"duplicate NFR definition {requirement_id} at line {line_no}")
                continue
            if len(row) < 4:
                errors.append(f"{requirement_id} row has {len(row)} cells; expected at least 4")
                continue
            if not all(row[1:4]):
                errors.append(f"{requirement_id} has an empty required NFR field at line {line_no}")
            nfr_rows[requirement_id] = line_no

    required_owner_header = "| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado | Responsable |"
    if content.count(required_owner_header) != 2:
        errors.append("expected owner column in both product-requirement tables")

    if len(product_rows) != 33:
        errors.append(f"expected 33 product requirements; found {len(product_rows)}")
    if len(nfr_rows) != 18:
        errors.append(f"expected 18 NFR definitions; found {len(nfr_rows)}")

    defined = set(product_rows) | set(nfr_rows)
    for match in re.finditer(r"\b(?:REQ-P|NFR)-\d{3}\b", content):
        requirement_id = match.group(0)
        if requirement_id not in defined:
            line_no = content.count("\n", 0, match.start()) + 1
            errors.append(f"undefined requirement reference {requirement_id} at line {line_no}")

    nfr_start = content.find("## 12. Índice de planificación por fase y prioridad para NFR")
    product_start = content.find("## 13. Índice de planificación por fase y prioridad")
    if nfr_start < 0 or product_start < 0 or nfr_start >= product_start:
        errors.append("expected NFR index section 12 before product index section 13")
    else:
        errors.extend(validate_index(content[nfr_start:product_start], set(nfr_rows), "NFR"))
        errors.extend(
            validate_index(
                content[product_start:],
                set(product_rows),
                "REQ-P",
                {key: value[1] for key, value in product_rows.items()},
            )
        )

    section_numbers = [
        int(match.group(1))
        for line in content.splitlines()
        if (match := re.match(r"^## (\d+)\.", line))
    ]
    if section_numbers != list(range(1, len(section_numbers) + 1)):
        errors.append(f"top-level section numbering is not sequential: {section_numbers}")
    return errors


def validate_issue_traceability(content: str) -> list[str]:
    errors: list[str] = []
    heading = "## 14. Matriz de trazabilidad entre Issues y requisitos"
    start = content.find(heading)
    if start < 0:
        return ["missing section 14: Issue-to-requirement traceability matrix"]

    next_heading = "## 15. Revisión de cobertura contra criterios de aceptación de Issues"
    end = content.find(next_heading, start + len(heading))
    section = content[start:end] if end >= 0 else content[start:]
    defined = set(re.findall(r"(?<!\w)(?:REQ-P|NFR)-\d{3}(?!\w)", content[:start]))
    mapped: set[str] = set()
    issues_found: set[int] = set()
    for line_no, line in enumerate(section.splitlines(), start=1):
        if not line.startswith("|"):
            continue
        row = cells(line)
        if not row:
            continue
        issue_match = re.match(r"\[#(\d+)\b", row[0])
        if not issue_match:
            continue
        issues_found.add(int(issue_match.group(1)))
        ids = set(re.findall(r"(?<!\w)(?:REQ-P|NFR)-\d{3}(?!\w)", line))
        unknown = sorted(ids - defined)
        if unknown:
            errors.append(
                f"Issue traceability row references undefined IDs: {', '.join(unknown)}"
            )
        mapped.update(ids)

    required_issues = {3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 17, 18, 19, 20, 21, 22}
    missing_issues = sorted(required_issues - issues_found)
    if missing_issues:
        errors.append(
            "Issue traceability matrix is missing rows for: "
            + ", ".join(f"#{number}" for number in missing_issues)
        )
    missing_ids = sorted(defined - mapped)
    if missing_ids:
        errors.append(
            "requirements are not linked to any Issue: " + ", ".join(missing_ids)
        )
    return errors


def validate_issue_acceptance_review(content: str) -> list[str]:
    heading = "## 15. Revisión de cobertura contra criterios de aceptación de Issues"
    start = content.find(heading)
    if start < 0:
        return ["missing section 15: Issue acceptance-criteria review"]

    section = content[start:]
    found: set[int] = set()
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        row = cells(line)
        if not row:
            continue
        match = re.match(r"\[#(\d+)\b", row[0])
        if match:
            found.add(int(match.group(1)))

    required = {3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 17, 18, 19, 20, 21}
    missing = sorted(required - found)
    if missing:
        return [
            "Issue acceptance-criteria review is missing rows for: "
            + ", ".join(f"#{number}" for number in missing)
        ]
    return []



def validate_acceptance_closure_matrix(content: str) -> list[str]:
    """Ensure criterion-level coverage for the acceptance matrix of Issues #7 and #13."""
    errors: list[str] = []
    for heading in (
        "# Matriz de cierre verificable de criterios de aceptación — Issues #7 y #13",
        "## 1. Issue #7 — Selección reproducible de exchanges y pares spot",
        "## 2. Issue #13 — Cobertura de criterios de aceptación",
        "## 3. Descomposición funcional del Issue #13 para diseñar pruebas",
        "## 4. Contrato de evidencia para cada prueba",
        "## 5. Decisiones necesarias antes de declarar cierre",
    ):
        if heading not in content:
            errors.append(f"acceptance closure matrix is missing heading: {heading}")

    required_ids = (
        [f"7-M{i:02d}" for i in range(1, 9)]
        + [f"7-D{i:02d}" for i in range(1, 7)]
        + [f"13-C{i:02d}" for i in range(1, 13)]
        + [f"RF-{i:02d}" for i in range(1, 10)]
    )
    lines = content.splitlines()
    for criterion_id in required_ids:
        matches = [
            line for line in lines
            if line.startswith("| " + criterion_id + " |")
            or line.startswith("| " + criterion_id + " ")
        ]
        if not matches:
            errors.append(f"acceptance closure matrix is missing criterion: {criterion_id}")
        elif len(matches) > 1:
            errors.append(f"acceptance closure matrix duplicates criterion: {criterion_id}")
    return errors



def validate_spot_methodology(content: str) -> list[str]:
    """Guard the minimum operational contract of the spot-selection specification."""
    errors: list[str] = []
    required_headings = (
        "# Metodología reproducible para seleccionar mercados spot",
        "## 3. Entidades y claves de datos",
        "## 4. Contrato mínimo de captura",
        "## 5. Métricas y definiciones",
        "### 5.1 Volumen spot",
        "### 5.2 Spread bid-ask",
        "### 5.3 Profundidad",
        "### 5.4 Slippage estimado por tamaño de orden",
        "### 5.5 Comisiones",
        "### 5.6 Disponibilidad exacta del par en Pionex",
        "## 6. Controles de calidad de datos",
        "## 7. Motor de decisión: sin umbrales implícitos",
        "## 8. Resultado de evaluación esperado",
        "## 9. Plan de validación y criterios de aceptación",
        "## 10. Decisiones pendientes",
    )
    for heading in required_headings:
        if heading not in content:
            errors.append(f"spot methodology is missing heading: {heading}")

    required_tokens = (
        "PASS",
        "FAIL",
        "INDETERMINATE",
        "NOT_APPLICABLE",
        "NOT_RUN",
        "payload_hash",
        "parser_version",
        "source_timestamp",
        "captured_at_utc",
        "\\text{spread}_{bps}",
        "\\text{slippage}_{bps}",
        "Los valores faltantes en esta configuración",
    )
    for token in required_tokens:
        if token not in content:
            errors.append(f"spot methodology is missing required contract token: {token}")
    return errors


def validate_relative_links() -> list[str]:
    errors: list[str] = []
    for markdown_path in sorted(ENGINEERING_DIR.glob("*.md")):
        content = markdown_path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(content):
            target = match.group(1).strip()
            if not target or target.startswith(
                ("#", "https://", "http://", "mailto:", "tel:", "data:")
            ):
                continue
            path_part = target.split("#", 1)[0].split("?", 1)[0]
            if not path_part:
                continue
            resolved = (markdown_path.parent / path_part).resolve()
            if not resolved.exists():
                line_no = content.count("\n", 0, match.start()) + 1
                errors.append(
                    f"broken relative link {markdown_path.relative_to(ROOT)}:{line_no}: {target}"
                )
    return errors


def main() -> int:
    if not CATALOG.is_file():
        print(f"FAIL: catalogue not found: {CATALOG}", file=sys.stderr)
        return 2
    catalog_content = CATALOG.read_text(encoding="utf-8")
    errors = validate_catalog(catalog_content)
    errors.extend(validate_issue_traceability(catalog_content))
    errors.extend(validate_issue_acceptance_review(catalog_content))
    if not CLOSURE_MATRIX.is_file():
        errors.append(f"acceptance closure matrix not found: {CLOSURE_MATRIX}")
    else:
        errors.extend(validate_acceptance_closure_matrix(CLOSURE_MATRIX.read_text(encoding="utf-8")))
    if not SPOT_METHOD.is_file():
        errors.append(f"spot methodology not found: {SPOT_METHOD}")
    else:
        errors.extend(validate_spot_methodology(SPOT_METHOD.read_text(encoding="utf-8")))
    errors.extend(validate_relative_links())
    if errors:
        print("FAIL: requirements documentation validation")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "PASS: 33 product requirements, 18 NFRs, both indexes, requirement references, "
        "section numbering, and relative engineering links are consistent."
    )
    print(
        "NOTE: this check does not approve priorities, validate acceptance thresholds, "
        "test product behavior, or establish ISO conformity."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
