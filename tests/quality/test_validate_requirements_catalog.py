"""Mutation tests for the requirements-catalogue validator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "quality"))

import validate_requirements_catalog as validator  # noqa: E402


class RequirementsCatalogueValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = validator.CATALOG.read_text(encoding="utf-8")
        cls.matrix = validator.CLOSURE_MATRIX.read_text(encoding="utf-8")
        cls.spot_method = validator.SPOT_METHOD.read_text(encoding="utf-8")

    def test_current_catalogue_is_consistent(self) -> None:
        self.assertEqual(validator.validate_catalog(self.content), [])
        self.assertEqual(validator.validate_issue_traceability(self.content), [])


    def test_acceptance_closure_matrix_has_required_criteria(self) -> None:
        self.assertEqual(validator.validate_acceptance_closure_matrix(self.matrix), [])

    def test_missing_spot_acceptance_criterion_fails(self) -> None:
        row = next(
            line for line in self.matrix.splitlines()
            if line.startswith("| 7-M03 |")
        )
        mutated = self.matrix.replace(row + "\n", "", 1)
        errors = validator.validate_acceptance_closure_matrix(mutated)
        self.assertTrue(
            any("missing criterion: 7-M03" in error for error in errors),
            errors,
        )


    def test_spot_methodology_has_required_operational_contract(self) -> None:
        self.assertEqual(validator.validate_spot_methodology(self.spot_method), [])

    def test_missing_slippage_formula_fails(self) -> None:
        mutated = self.spot_method.replace("\\text{slippage}_{bps}", "")
        errors = validator.validate_spot_methodology(mutated)
        self.assertTrue(
            any("missing required contract token" in error and "slippage" in error for error in errors),
            errors,
        )

    def test_missing_product_index_entry_fails(self) -> None:
        heading = "## 13. Índice de planificación por fase y prioridad"
        start = self.content.index(heading)
        prefix, index = self.content[:start], self.content[start:]
        target = "| 1 | F0 — Gobernanza y marco maestro | REQ-P-007 | Crítica |"
        self.assertIn(target, index)
        mutated = prefix + index.replace(target, "", 1)
        errors = validator.validate_catalog(mutated)
        self.assertTrue(any("REQ-P-007" in error and "missing" in error for error in errors), errors)

    def test_duplicate_product_definition_fails(self) -> None:
        line = next(
            row for row in self.content.splitlines()
            if row.startswith("| REQ-P-001 |")
        )
        mutated = self.content.replace(line, line + "\n" + line, 1)
        errors = validator.validate_catalog(mutated)
        self.assertTrue(any("duplicate product requirement REQ-P-001" in error for error in errors), errors)

    def test_catalogue_index_priority_mismatch_fails(self) -> None:
        line = next(
            row for row in self.content.splitlines()
            if row.startswith("| REQ-P-001 |")
        )
        cells = validator.cells(line)
        cells[2] = "Media"
        changed = "| " + " | ".join(cells) + " |"
        mutated = self.content.replace(line, changed, 1)
        errors = validator.validate_catalog(mutated)
        self.assertTrue(any("REQ-P-001 priority differs" in error for error in errors), errors)

    def test_missing_responsible_role_fails(self) -> None:
        line = next(
            row for row in self.content.splitlines()
            if row.startswith("| REQ-P-001 |")
        )
        row = validator.cells(line)
        self.assertEqual(len(row), 7)
        row[6] = ""
        mutated_row = "| " + " | ".join(row) + " |"
        mutated = self.content.replace(line, mutated_row, 1)
        errors = validator.validate_catalog(mutated)
        self.assertTrue(
            any("REQ-P-001 has empty responsible role" in error for error in errors),
            errors,
        )

    def test_missing_issue_acceptance_review_row_fails(self) -> None:
        heading = "## 15. Revisión de cobertura contra criterios de aceptación de Issues"
        start = self.content.index(heading)
        prefix, review = self.content[:start], self.content[start:]
        row = next(line for line in review.splitlines() if line.startswith("| [#10 —"))
        mutated = prefix + review.replace(row + "\n", "", 1)
        errors = validator.validate_issue_acceptance_review(mutated)
        self.assertTrue(
            any("missing rows for" in error and "#10" in error for error in errors),
            errors,
        )

    def test_unmapped_requirement_fails(self) -> None:
        heading = "## 14. Matriz de trazabilidad entre Issues y requisitos"
        start = self.content.index(heading)
        prefix, matrix = self.content[:start], self.content[start:]
        target = "| [#5 — Clientes multiplataforma](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/5) | Web/PWA, Android, iOS y escritorio opcional según evidencia | REQ-P-006, REQ-P-027, REQ-P-030 | NFR-006, NFR-018 | Propuesta; confirmar contra criterios de aceptación del Issue |"
        self.assertIn(target, matrix)
        mutated_matrix = matrix.replace("REQ-P-006, ", "")
        mutated_matrix = mutated_matrix.replace("REQ-P-006", "")
        mutated = prefix + mutated_matrix
        errors = validator.validate_issue_traceability(mutated)
        self.assertTrue(any("REQ-P-006" in error and "not linked" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
