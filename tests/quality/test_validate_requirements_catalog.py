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

    def test_current_catalogue_is_consistent(self) -> None:
        self.assertEqual(validator.validate_catalog(self.content), [])
        self.assertEqual(validator.validate_issue_traceability(self.content), [])

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

    def test_unmapped_requirement_fails(self) -> None:
        heading = "## 14. Matriz de trazabilidad entre Issues y requisitos"
        start = self.content.index(heading)
        prefix, matrix = self.content[:start], self.content[start:]
        target = "| [#5 — Clientes multiplataforma](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/5) | Web/PWA, Android, iOS y escritorio opcional según evidencia | REQ-P-006, REQ-P-027, REQ-P-030 | NFR-006, NFR-018 | Propuesta; confirmar contra criterios de aceptación del Issue |"
        self.assertIn(target, matrix)
        mutated = prefix + matrix.replace(target, target.replace("REQ-P-006, ", ""), 1)
        errors = validator.validate_issue_traceability(mutated)
        self.assertTrue(any("REQ-P-006" in error and "not linked" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
