# Inventario inicial de dependencias y licencias

- **Estado:** inventario preliminar; no constituye una decisión de licencia ni asesoramiento legal.
- **Issue:** [#20 — Licencia, derechos de distribución y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20).
- **Base examinada:** `main`, commit `9aed74a44aa6ee20eba8878205027666e0568491` (2026-10-21). Repetir antes de una release.

## 1. Hallazgos reproducibles

- El árbol integrado contiene `requirements-market-data.txt`, que fija `websocket-client==1.8.0` para el transporte público WebSocket de Binance. Es una dependencia opcional: el módulo la importa al abrir el socket en vivo; las pruebas offline pueden inyectar un transporte simulado.
- La presencia del pin no prueba por sí sola que la dependencia se haya instalado, ejecutado en vivo, revisado por vulnerabilidades o aprobado para distribución.
- El inventario consultado no identifica un archivo raíz `LICENSE` o `COPYING`. La ausencia de licencia explícita no convierte el código en dominio público ni otorga permisos generales de reutilización o redistribución.
- Los workflows de GitHub Actions son dependencias de CI distintas de las dependencias de ejecución. Sus versiones, SHAs, licencias y procedencia deben revisarse contra las fuentes oficiales al mantener el inventario.
- Los módulos revisados de captura y selección usan ampliamente la biblioteca estándar de Python. Esta observación no equivale a un análisis automatizado exhaustivo de todas las dependencias transitivas.

## 2. Inventario por componente

| Componente | Evidencia observada | Acción requerida |
|---|---|---|
| Código Python del prototipo | Módulos de captura, selección, evaluación y pruebas en `main` | Mantener inventario actualizado y revisar dependencias nuevas |
| Biblioteca estándar de Python | Imports en los módulos revisados y runtime declarado en CI | Documentar runtime objetivo y comprobar compatibilidad |
| Transporte público WebSocket | `requirements-market-data.txt` fija `websocket-client==1.8.0`; el transporte no usa credenciales ni envía órdenes | Verificar licencia y procedencia oficiales, mantenimiento, avisos y vulnerabilidades antes de distribuir |
| GitHub Actions | Workflows con acciones fijadas por SHA | Verificar versión/tag y licencia de cada acción desde la fuente oficial; mantener actualizaciones controladas |
| Documentación y contenido | No se ha identificado licencia raíz explícita en la línea base examinada | Decidir derechos de código, documentación, marcas, contribuciones y artefactos |
| Dependencias transitivas | No se adjunta aquí un SBOM ni un resultado de escaneo completo | Generar inventario reproducible en el entorno de release |

## 3. Puertas pendientes

- [ ] Decidir explícitamente el modelo de distribución: propietario, código abierto u otro.
- [ ] Evaluar licencias candidatas y solicitar asesoramiento legal cuando corresponda.
- [ ] Confirmar que la decisión cubre código, documentación, marcas, contribuciones y artefactos/capturas externas.
- [ ] Verificar la licencia y procedencia de `websocket-client==1.8.0` en la fuente oficial y conservar evidencia fechada.
- [ ] Revisar licencias, avisos, versiones y procedencia de las acciones de CI.
- [ ] Incorporar SBOM o inventario automatizado y política de actualización/alertas apropiada.
- [ ] Añadir licencia y avisos solo después de una decisión aprobada, mediante PR revisable.
- [ ] Registrar responsable, justificación y fecha de aprobación.

## 4. Restricciones

No se elige una licencia por inferencia ni se supone que el proyecto deba ser de código abierto. Este documento describe evidencia observada en una línea base concreta; no certifica exhaustividad, seguridad legal ni preparación para release.
