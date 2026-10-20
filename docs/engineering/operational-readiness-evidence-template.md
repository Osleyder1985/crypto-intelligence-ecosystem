# Plantilla de expediente de preparación operativa

- **Estado:** plantilla de ejecución; no es evidencia de que se hayan superado las pruebas.
- **Issue de seguimiento:** [#19 — Puerta de preparación operativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/19).
- **Regla:** el estado permanece **NO LISTO PARA PRODUCCIÓN** hasta que las pruebas críticas se ejecuten en un entorno identificado, se adjunten artefactos verificables y la autoridad designada acepte los riesgos residuales.

## 1. Control del expediente

| Campo | Valor requerido |
|---|---|
| Identificador del expediente | Pendiente |
| Versión/tag del producto y SHA | Pendiente |
| Entorno, región y configuración | Pendiente |
| Fecha UTC de ejecución | Pendiente |
| Responsable de ejecución | Pendiente |
| Revisor independiente de la ejecución | Pendiente |
| Autoridad que acepta riesgos residuales | Pendiente |
| Enlaces a logs y artefactos inmutables | Pendiente |
| Estado global | NOT_READY |

No registrar secretos, credenciales, datos personales innecesarios ni valores de configuración sensibles en el expediente.

## 2. Puertas obligatorias

Cada puerta debe incluir alcance, precondiciones, procedimiento reproducible, resultado esperado, resultado observado, artefacto, defectos y aprobación. No marcar una puerta como aprobada por haber redactado su plan.

| Puerta | Evidencia mínima exigida | Estado inicial |
|---|---|---|
| Integración | Suite ejecutada en entorno identificado; versiones, logs y artefactos; resultados de contratos entre componentes | NOT_RUN |
| Extremo a extremo | Flujos críticos, casos negativos y recuperación de errores; evidencia de ejecución | NOT_RUN |
| Seguridad | Modelo de amenazas revisado; dependencias y secretos; autenticación/autorización; entradas hostiles; resultados de análisis; riesgos residuales | NOT_RUN |
| Rendimiento/carga | Perfil de carga, duración, datos de prueba, umbrales aprobados antes de ejecutar, latencia y tasa de error observadas | NOT_RUN |
| Backup/restauración | Alcance de copia, procedimiento, registro de restauración, integridad comprobada y RPO/RTO aprobados cuando apliquen | NOT_RUN |
| Observabilidad/alertas | Métricas, logs y trazas; alertas disparadas de forma controlada; evidencia de recepción y diagnóstico | NOT_RUN |
| Runbooks | Procedimientos operativos probados por una persona distinta de su autor cuando sea posible | NOT_RUN |
| Rollback | Despliegue/versión de origen identificados; rollback ensayado en entorno controlado; integridad posterior validada | NOT_RUN |
| Defectos/excepciones | Lista de hallazgos, severidad, propietario, fecha objetivo y excepción aprobada cuando corresponda | NOT_RUN |

## 3. Registro por prueba

Duplicar esta sección por cada prueba ejecutada.

- **ID/nombre de prueba:**
- **Puerta relacionada:**
- **Objetivo y riesgo cubierto:**
- **Entorno y versión exactos:**
- **Precondiciones y datos de prueba:**
- **Procedimiento/comando reproducible:**
- **Criterios de aceptación aprobados antes de la ejecución:**
- **Resultado esperado:**
- **Resultado observado:**
- **Inicio/fin UTC:**
- **Logs, reportes y artefactos:**
- **Defectos abiertos y severidad:**
- **Limitaciones y desviaciones:**
- **Ejecutor y revisor:**
- **Estado:** NOT_RUN / PASS / FAIL / INDETERMINATE

## 4. Gestión de riesgos residuales

| ID | Riesgo | Severidad | Mitigación/controles | Propietario | Excepción aprobada por | Fecha de revisión | Estado |
|---|---|---|---|---|---|---|---|
| Pendiente | No se ha completado el expediente de evidencia | Alta | Mantener el producto como no listo para producción | Pendiente | Ninguna | Pendiente | Abierto |

No se aceptan riesgos críticos por silencio. Las excepciones deben identificar alcance, justificación, controles compensatorios, autoridad, fecha de expiración y condición de revisión.

## 5. Decisión de readiness

- [ ] Todas las puertas críticas tienen ejecución y artefactos verificables.
- [ ] No quedan defectos críticos/altos sin tratamiento o excepción explícita válida.
- [ ] Backup/restauración y rollback han sido ensayados y sus resultados comprobados.
- [ ] Alertas y runbooks se han probado en el entorno declarado.
- [ ] Las versiones y la configuración evaluadas corresponden al candidato que se pretende liberar.
- [ ] La autoridad designada ha revisado y aceptado por escrito los riesgos residuales.
- [ ] Existe plan de monitorización y reversión para la liberación.

**Decisión:** NOT_READY hasta que los puntos aplicables se completen con evidencia.

**Aprobador / rol:** Pendiente  
**Fecha UTC:** Pendiente  
**Versión/SHA aprobados:** Pendiente  
**Registro de decisión:** Pendiente

## 6. Límites de esta plantilla

Esta plantilla organiza la evidencia; no demuestra que las pruebas se hayan ejecutado, no sustituye una revisión de seguridad ni certifica conformidad con ISO u otra norma. La auditoría debe citar artefactos reales y conservar el estado NOT_RUN, FAIL o INDETERMINATE cuando no exista evidencia suficiente.


## 7. Validador estructural del manifiesto

Se incorpora `scripts/quality/validate_readiness_manifest.py` para validar un manifiesto JSON de evidencia antes de revisión. La prueba unitaria asociada está en `tests/quality/test_validate_readiness_manifest.py`.

Uso desde la raíz del repositorio:

```bash
python scripts/quality/validate_readiness_manifest.py ruta/al/manifiesto.json
python -m unittest discover -s tests/quality -p 'test_*.py' -v
```

El manifiesto debe incluir el identificador del expediente, versión y SHA, entorno, fecha UTC, roles responsables, las nueve puertas obligatorias y riesgos residuales. Los estados admitidos son `NOT_RUN`, `PASS`, `FAIL` e `INDETERMINATE`. Cada puerta en `PASS` requiere resultado observado, referencia de evidencia y fecha de ejecución; un riesgo crítico/alto sin excepción aprobada se rechaza.

El validador aplica reglas estructurales y fail-closed, pero no confirma que los enlaces sean accesibles o auténticos, no ejecuta pruebas de producto y no sustituye la aprobación humana. El estado del producto permanece `NOT_READY` hasta que exista evidencia operativa real revisada.
