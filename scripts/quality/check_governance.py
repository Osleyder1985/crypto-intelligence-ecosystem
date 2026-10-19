#!/usr/bin/env python3
"""Validaciones mínimas y deterministas del contrato documental de gobernanza.

Este control no sustituye revisión humana, pruebas de producto ni configuración
de protección de ramas. Solo comprueba invariantes explícitos del repositorio.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "CONTRIBUTING.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/01-requisito-mejora.yml",
    ".github/ISSUE_TEMPLATE/02-defecto.yml",
    "docs/gobernanza/flujo-de-trabajo.md",
)

REQUIRED_TEXT = {
    "CONTRIBUTING.md": (
        "antes de implementar cambios",
        "Pull Request",
        "Protección de main",
        "no activan por sí mismos la protección",
    ),
    ".github/PULL_REQUEST_TEMPLATE.md": (
        "Issue relacionado",
        "Justificación de la solución",
        "Verificación y pruebas",
        "Riesgos y compatibilidad",
        "no se afirma que se ejecutaron pruebas",
    ),
    "docs/gobernanza/flujo-de-trabajo.md": (
        "Criterios de aceptación",
        "protección efectiva",
        "Evidencia y reproducibilidad",
        "No se debe integrar un PR hasta que",
    ),
    ".github/ISSUE_TEMPLATE/01-requisito-mejora.yml": (
        'name: "Requisito o mejora"',
        "Criterios de aceptación",
        "Evidencia disponible y pendiente",
    ),
    ".github/ISSUE_TEMPLATE/02-defecto.yml": (
        'name: "Defecto"',
        "Pasos para reproducir",
        "Criterios de aceptación",
    ),
}

def main() -> int:
    errors = []
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"Falta el archivo obligatorio: {relative}")

    for relative, phrases in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase.casefold() not in content.casefold():
                errors.append(f"{relative}: falta el contrato textual {phrase!r}")

    if errors:
        print("FALLO: contrato documental de gobernanza incumplido.")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS: {len(REQUIRED_FILES)} archivos de gobernanza presentes.")
    print("PASS: contratos documentales obligatorios encontrados.")
    print("LIMITACIÓN: no comprueba reglas de rama del servidor ni sustituye revisión humana.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
