# Inventario inicial de dependencias y licencias

- **Estado:** inventario preliminar de la rama auditada; no constituye una decisión de licencia ni asesoramiento legal.
- **Issue:** [#20 — Licencia, derechos de distribución y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20).
- **Base examinada:** árbol de archivos del PR #12, HEAD fee835bc9d1cb722646ebcc2b30e76e58f1b7362; el alcance del PR #15 debe reevaluarse al preparar la línea base integrada.

## 1. Hallazgos reproducibles

- En el árbol examinado no aparece un archivo raíz LICENSE, COPYING, NOTICE, pyproject.toml, requirements.txt, Pipfile, poetry.lock, uv.lock ni package.json.
- Los módulos Python visibles de captura, selección y validación usan principalmente módulos de la biblioteca estándar en los archivos revisados; no se observó un manifiesto de dependencias Python de terceros en esta rama.
- Los workflows de GitHub Actions referencian acciones externas mediante etiquetas de versión, entre ellas actions/checkout@v4, actions/setup-python@v5 y actions/upload-artifact@v4. Deben registrarse por separado de las dependencias de ejecución del producto.
- La ausencia de un archivo de licencia explícito no significa que el contenido sea de dominio público ni que exista permiso general de reutilización o redistribución.

## 2. Inventario por componente

| Componente | Evidencia observada | Acción requerida |
|---|---|---|
| Código Python del prototipo | Sin manifiesto de paquetes detectado en el árbol del PR #12 | Confirmar el árbol integrado completo y generar inventario automatizado al incorporar nuevos paquetes |
| Biblioteca estándar de Python | Imports visibles en módulos y pruebas; versiones de Python declaradas en CI | Registrar versión/runtime objetivo y validar compatibilidad |
| GitHub Actions | checkout@v4, setup-python@v5, upload-artifact@v4 en workflows | Registrar repositorio de origen, versión/commit, licencia y política de actualización; valorar pinning por SHA |
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
