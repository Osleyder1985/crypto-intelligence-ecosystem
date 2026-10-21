# Issue #19 — Expediente de evidencia de preparación operativa

**Estado:** plan de ejecución; no es evidencia de pruebas ejecutadas ni aprobación de producción.  
**Issue:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/19

## Regla de decisión

La preparación operativa permanece `NOT_READY` hasta que cada puerta crítica tenga un resultado reproducible asociado a un commit, versión y entorno identificados. Un workflow verde de pruebas unitarias no sustituye pruebas integrales, restauración, observabilidad o rollback.

No ejecutar pruebas destructivas en producción. Cualquier umbral de aceptación, RPO/RTO, severidad o excepción requiere aprobación explícita antes de ejecutar el ensayo.

## Registro de puertas

| ID | Puerta | Evidencia mínima requerida | Estado inicial |
|---|---|---|---|
| OP-01 | Alcance y entorno | Diagrama de componentes, versión desplegada, configuración saneada, dependencias y límites del entorno | NOT_RUN |
| OP-02 | Integración / extremo a extremo | Casos de uso y fallos críticos definidos antes de ejecutar; logs y resultados completos; commit exacto | NOT_RUN |
| OP-03 | Modelo de amenazas | Activos, límites de confianza, actores, superficies, mitigaciones, riesgos residuales y propietario de cada riesgo | NOT_RUN |
| OP-04 | Rendimiento | Perfil de carga, duración, concurrencia, dataset, métricas y umbrales aprobados previamente | NOT_RUN |
| OP-05 | Backup / restauración | Backup identificado, procedimiento, integridad comprobada, restauración en entorno aislado, tiempos medidos y evidencia | NOT_RUN |
| OP-06 | Observabilidad y alertas | Señales críticas, umbrales aprobados, alertas disparadas deliberadamente, recepción confirmada y runbook asociado | NOT_RUN |
| OP-07 | Rollback | Versión origen/destino, disparador, pasos, verificación posterior y evidencia de recuperación en entorno controlado | NOT_RUN |
| OP-08 | Riesgos y liberación | Defectos abiertos, excepciones, severidades, aceptación por responsable autorizado y decisión de release | NOT_RUN |

## Registro obligatorio por ensayo

Cada ensayo debe conservar:

- ID de puerta y caso de prueba; objetivo y criterio de aceptación aprobados antes de ejecutarlo.
- Commit SHA, versión de artefactos, versión de dependencias y configuración no secreta.
- Identificador del entorno, fecha/hora UTC de inicio y fin, ejecutor y prerequisitos.
- Comando/procedimiento reproducible, resultado esperado y resultado observado.
- Logs, métricas y artefactos preservados con hash cuando sea viable.
- Defectos creados, impacto, severidad, mitigación y enlace a la corrección.
- Estado final: `PASS`, `FAIL`, `INDETERMINATE` o `NOT_RUN`; evidencia enlazada y justificación.

No registrar secretos, tokens, claves privadas, datos personales innecesarios ni credenciales en los artefactos.

## Criterios para asignar estado

- `PASS`: se ejecutó el ensayo en el entorno identificado y toda la evidencia requerida satisface el criterio previamente aprobado.
- `FAIL`: se ejecutó y no cumplió el criterio, o se demostró una condición de fallo.
- `INDETERMINATE`: evidencia incompleta, entorno no identificable, resultados no reproducibles o criterio no aprobado.
- `NOT_RUN`: todavía no se ha ejecutado.

Un plan escrito, un workflow de CI verde o una simulación no realizada no pueden etiquetarse como `PASS`.

## Dependencias de aprobación

Antes de ensayar, el responsable del proyecto debe aprobar los criterios de aceptación, severidades y umbrales de rendimiento; RPO/RTO si aplican; alcance de restauración; disparadores de rollback; y riesgos residuales aceptables. No se inventan valores por defecto en este plan.

## Condición de cierre

Issue #19 no se cierra hasta que OP-01–OP-08 tengan evidencia revisable, las puertas críticas estén en `PASS`, los defectos y excepciones estén registrados y exista una decisión explícita de release por una autoridad identificada. Si faltan pruebas críticas, mantener `NOT_READY`.

**Limitación:** este documento estructura el expediente y no demuestra que ningún ensayo se haya ejecutado. No constituye declaración de preparación para producción, conformidad ISO ni certificación.
