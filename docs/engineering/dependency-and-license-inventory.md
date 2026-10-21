# Inventario inicial de dependencias y licencias

- **Estado:** inventario preliminar de la rama auditada; no constituye una decisión de licencia ni asesoramiento legal.
- **Issue:** [#20 — Licencia, derechos de distribución y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20).
- **Base examinada:** rama `main`, commit `e62c9dba84f0492e477afa144c3bbcfbbaf11422` (verificado el 2026-10-21, tras integrar el PR #35). Repetir el inventario después de cambios de dependencias y antes de una release.

## 1. Hallazgos reproducibles

- En el árbol `main` examinado no aparece un archivo raíz LICENSE, COPYING, NOTICE, pyproject.toml, requirements.txt, Pipfile, poetry.lock, uv.lock ni package.json.
- Los módulos Python visibles de captura, selección y validación usan principalmente módulos de la biblioteca estándar en los archivos revisados; no se observó un manifiesto de dependencias Python de terceros en esta rama.
- Los workflows de `main` fijan `actions/checkout` al SHA `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), `actions/setup-python` al SHA `5fda3b95a4ea91299a34e894583c3862153e4b97` (v7.0.0) y `actions/upload-artifact` al SHA `cf430e030ddbb5b0abf93d22962f4752f3646cd9`. Son dependencias de CI, separadas de las dependencias de ejecución; la versión/tag de upload-artifact debe verificarse contra la fuente oficial al actualizar el inventario.
- La ausencia de un archivo de licencia explícito no significa que el contenido sea de dominio público ni que exista permiso general de reutilización o redistribución.

## 2. Inventario por componente

| Componente | Evidencia observada | Acción requerida |
|---|---|---|
| Código Python del prototipo | Sin manifiesto de paquetes detectado en el árbol del PR #12 | Confirmar el árbol integrado completo y generar inventario automatizado al incorporar nuevos paquetes |
| Biblioteca estándar de Python | Imports visibles en módulos y pruebas; versiones de Python declaradas en CI | Registrar versión/runtime objetivo y validar compatibilidad |
| GitHub Actions | En `main`: checkout v7.0.1 y setup-python v7.0.0 mediante SHA completos; upload-artifact fijado al SHA `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | Verificar versión/tag y licencia oficial de cada SHA, registrar procedencia y mantener Dependabot habilitado |
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
