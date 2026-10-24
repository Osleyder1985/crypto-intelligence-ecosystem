# Inventario de workflows de GitHub Actions — Issue #270

**Fecha de inspección:** 2026-10-24 UTC  
**Commit inspeccionado:** `e5f5ae47ba7169c3f12c13fb14069ddf955e88f7`  
**Método:** árbol Git recursivo fijado al commit y lectura de los 25 archivos `.github/workflows/*.yml`.  
**Alcance:** inventario estático; no sustituye la inspección de la configuración del ruleset ni demuestra que todos los workflows se ejecuten para todos los cambios.

## Resumen

- Workflows YAML encontrados: **25**.
- Los workflows contienen varios tipos de disparador: `pull_request`, `push`, `workflow_dispatch` y, en ciertos casos, `schedule`.
- Hay workflows con filtros de rutas y otros sin ellos. Los filtros deben evaluarse junto al evento, el job que emite el check y la lista de contexts requeridos; su mera presencia no prueba por sí sola un bloqueo.
- La API de GitHub devolvió **403** al intentar consultar la configuración de protección de `main` desde esta sesión. Por tanto, este inventario **no afirma haber verificado la lista vigente de contexts requeridos**. Esa lista debe contrastarse con la pantalla de administración del ruleset o con una consulta autorizada.

## Inventario de archivos y jobs

Los identificadores de job se muestran tal como aparecen bajo `jobs:`. El nombre de check visible puede ser distinto si el job define un campo `name:`.

| Archivo de workflow | Identificadores de job | Disparadores observados | Contiene `paths:` o `paths-ignore:` |
|---|---|---|---|
| `binance-live-capture-report-e2e.yml` | `offline-contract-tests`, `live-smoke-read-only` | pull_request, push, workflow_dispatch | Sí |
| `binance-live-depth-evidence.yml` | `offline-tests`, `live-capture` | pull_request, push, workflow_dispatch, schedule | No |
| `binance-regional-rest-diagnostic.yml` | `offline-tests`, `live-public-diagnostic` | push, pull_request, workflow_dispatch, schedule | Sí |
| `external-event-evidence-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `forecast-scoring-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `fundamental-onchain-contract-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `governance-validation.yml` | `validar-gobernanza` | pull_request, push, workflow_dispatch | No |
| `horizon-assessment-contract-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `issue-132-policy-snapshots.yml` | `capture-policy-pages` | workflow_dispatch, pull_request | Sí |
| `issue-18-freshness-sampling.yml` | `sample` | schedule, workflow_dispatch | No |
| `market-capture-evaluation.yml` | `scope`, `test-market-capture-evaluation` | pull_request, workflow_dispatch | No |
| `methodology-contract-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `multi-exchange-spot-book-probe.yml` | `offline-tests`, `live-public-capture` | push, pull_request, workflow_dispatch, schedule | Sí |
| `multi-exchange-spot-quote-volume-probe.yml` | `offline-tests`, `live-public-capture` | push, pull_request, workflow_dispatch, schedule | Sí |
| `multi-pair-public-market-capture.yml` | `offline-tests`, `capture-offline`, `live-capture` | pull_request, workflow_dispatch | No |
| `order-book-report-integration-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `pionex-spot-ohlcv-capture.yml` | `offline-tests`, `live-capture` | pull_request, push, workflow_dispatch | Sí |
| `provider-license-gate-tests.yml` | `provider-license-gate` | pull_request, push | Sí |
| `provider-license-runtime-integration.yml` | `runtime-enforcement` | pull_request, push | Sí |
| `public-market-capture.yml` | `scope`, `capture-public-market-data` | pull_request, workflow_dispatch | No |
| `public-market-metadata-size-tests.yml` | `large-response-regression` | pull_request, push | No |
| `report-forecast-scoring-integration-tests.yml` | `test` | pull_request, push, workflow_dispatch | Sí |
| `requirements-validation.yml` | `scope`, `validate-requirements` | pull_request, workflow_dispatch | No |
| `research-evidence-integration-tests.yml` | `research-report-and-evidence` | pull_request, push, workflow_dispatch | Sí |
| `spot-market-selection.yml` | `scope`, `spot-market-selection-tests` | pull_request, workflow_dispatch | No |

## Hallazgos y límites de la evidencia

1. **Nombre del workflow vs. nombre del check:** no deben tratarse como equivalentes. Por ejemplo, `multi-pair-public-market-capture.yml` contiene jobs cuyo nombre visible incluye “Test multi-pair capture and evaluation offline” y “Test multi-pair capture offline”; el contexto requerido depende del job y del run concreto.
2. **Workflows de captura en vivo:** algunos comparten workflow con jobs offline y en vivo. La política de CI debe comprobar que el job de red esté condicionado y separado de las pruebas offline; no se debe ejecutar una captura externa solo para satisfacer un check.
3. **Filtros de rutas:** los workflows que los contienen necesitan revisión específica de si el evento omite el workflow completo o solo un job. No se concluye un fallo sin comprobar los contexts emitidos en un PR representativo.
4. **Ruleset:** la configuración no quedó accesible por la API en esta inspección. No se modificó la protección ni se retiró ningún check obligatorio.
5. **Cobertura:** el inventario enumera los 25 archivos encontrados en el árbol de este commit. No demuestra que los tests sean suficientes ni que se hayan ejecutado todos en la rama principal.

## Próximas acciones de auditoría

- Obtener por una vía autorizada la lista vigente de contexts requeridos en `protect-main`.
- Para cada context, mapear workflow, job, evento, filtros, condiciones `if`, nombre visible y evidencia de ejecución.
- Probar la matriz con un PR documental, uno de pruebas y uno de código de captura, sin habilitar tráfico real innecesario.
- Documentar cualquier discrepancia confirmada como hallazgo con evidencia y corrección propuesta; no debilitar la protección para hacer desaparecer el bloqueo.
