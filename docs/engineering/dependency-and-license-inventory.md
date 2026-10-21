# Inventario inicial de dependencias y licencias

- **Estado:** inventario preliminar de la rama auditada; no constituye una decisión de licencia ni asesoramiento legal.
- **Issue:** [#20 — Licencia, derechos de distribución y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20).
- **Base examinada:** instantánea de la rama de la PR #12 revisada el 2026-10-20; repetir el inventario después de integrar cambios adicionales y antes de una release.

## 1. Hallazgos reproducibles

- En el árbol examinado no aparece un archivo raíz LICENSE, COPYING, NOTICE, pyproject.toml, requirements.txt, Pipfile, poetry.lock, uv.lock ni package.json.
- Los módulos Python visibles de captura, selección y validación usan principalmente módulos de la biblioteca estándar en los archivos revisados; no se observó un manifiesto de dependencias Python de terceros en esta rama.
- Los workflows de GitHub Actions de esta rama fijan `actions/checkout` a `11bd71901bbe5b1630ceea73d27597364c9af683` (v4.2.2), `actions/setup-python` a `a26af69be951a213d495a4c3e4e4022e16d87065` (v5.6.0) y `actions/upload-artifact` a `ea165f8d65b6e75b540449e92b4886f43607fa02` (v4.6.2). Son dependencias de CI y deben inventariarse por separado de las dependencias de ejecución del producto.
- La ausencia de un archivo de licencia explícito no significa que el contenido sea de dominio público ni que exista permiso general de reutilización o redistribución.

## 2. Inventario por componente

| Componente | Evidencia observada | Acción requerida |
|---|---|---|
| Código Python del prototipo | Sin manifiesto de paquetes detectado en el árbol del PR #12 | Confirmar el árbol integrado completo y generar inventario automatizado al incorporar nuevos paquetes |
| Biblioteca estándar de Python | Imports visibles en módulos y pruebas; versiones de Python declaradas en CI | Registrar versión/runtime objetivo y validar compatibilidad |
| GitHub Actions | Los workflows auditados fijan checkout v4.2.2, setup-python v5.6.0 y upload-artifact v4.6.2 mediante SHA completos | Registrar repositorio de origen, SHA/versión, licencia y política de actualización; verificar los SHA al actualizar y mantener Dependabot habilitado |
| Documentación y contenido | No se encontró licencia raíz explícita en el árbol auditado | Decidir derechos de código, documentación, marcas, capturas y contribuciones |
| Dependencias de ramas aún no integradas | El alcance y los archivos pueden diferir de esta instantánea | Repetir inventario en la línea base candidata a release |

## 3. Puertas pendientes

- [ ] Decidir explícitamente el modelo de distribución: propietario, código abierto u otro.
- [ ] Evaluar licencias candidatas y obtener asesoramiento legal cuando corresponda.
- [ ] Confirmar que la decisión cubre código, documentación, marcas, contribuciones y artefactos/capturas externas.
- [ ] Revisar licencias, avisos y procedencia de acciones de CI y de cualquier dependencia futura.
- [ ] Incorporar un inventario automatizado de dependencias y una política de actualización/alertas apropiada.
- [ ] Añadir el archivo de licencia y avisos solo después de la decisión aprobada, mediante PR revisable.
- [ ] Registrar responsable, justificación y fecha de aprobación.

## 4. Restricciones

No se elige una licencia por inferencia ni se supone que una licencia de código abierto sea el objetivo correcto. Este inventario describe la evidencia disponible en una rama concreta; no certifica exhaustividad del repositorio integrado ni sustituye revisión legal.
