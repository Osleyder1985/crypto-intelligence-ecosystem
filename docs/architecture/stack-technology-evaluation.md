# Evaluación del stack tecnológico (Issue #9)

**Estado:** evaluación documental inicial; decisión final condicionada a PoC ejecutables.  
**Fecha de corte:** 2026-10-24.  
**Alcance:** clientes web, Android/iOS, API central, almacenamiento histórico, procesamiento asíncrono, calidad/seguridad y operación.  
**No constituye** una certificación ISO, una prueba de rendimiento ni una validación de producción.

## 1. Requisitos que condicionan la selección

1. Clientes web, Android e iOS comparten contratos y resultados canónicos; escritorio solo si un requisito posterior lo justifica.
2. El cliente no contiene claves de proveedores ni reglas analíticas canónicas.
3. API versionada y documentada con OpenAPI; validación de contratos automatizada.
4. Persistencia de observaciones y evaluaciones históricas con procedencia, timestamps, versión metodológica y reproducibilidad.
5. Captura externa pública en modo read-only; ninguna orden real de trading.
6. Ejecución bajo demanda, abstención explícita ante datos insuficientes y manejo visible de errores/obsolescencia.
7. El diseño inicial debe poder ejecutarse y probarse localmente en Windows con recursos limitados; no introducir infraestructura distribuida sin evidencia de necesidad.

## 2. Matriz de decisión: criterios y pesos de trabajo

Los pesos son una propuesta de evaluación que suma 100%; deben aprobarse antes de puntuar. Las puntuaciones permanecen **N/E (no evaluadas)** hasta ejecutar PoC comparables. No se asigna un ganador ficticio.

| Dominio | Peso | Evidencia/medición requerida |
|---|---:|---|
| Adecuación funcional y contratos compartidos | 20% | Casos de uso, contrato OpenAPI, validación cliente-servidor |
| Mantenibilidad y reutilización multiplataforma | 15% | Duplicación real, estructura, experiencia de desarrollo |
| Gráficos y manejo de series de mercado | 15% | OHLCV, zoom/pan, volumen y carga de datos reproducible |
| Seguridad y privacidad | 15% | Dependencias, permisos, secretos, logs, límites de confianza |
| Persistencia histórica y consultas | 10% | Escritura/lectura, integridad temporal, consulta por activo/horizonte |
| Pruebas y CI reproducibles | 10% | Tests repetibles desde entorno limpio y artefactos de resultados |
| Recursos locales y experiencia de build | 5% | Versiones, tiempo de build, memoria y tamaño de artefacto |
| Coste operativo/licencias/soporte | 5% | Licencias, mantenimiento, soporte y servicios requeridos |
| Incertidumbre y reversibilidad | 5% | Riesgo de bloqueo, migración y condición de reconsideración |

### Regla de puntuación

- Escala propuesta: 1 (insuficiente), 2 (débil), 3 (aceptable), 4 (fuerte), 5 (muy fuerte).
- Cada puntuación debe enlazar a evidencia reproducible y anotar incertidumbre.
- Resultado ponderado = suma de (peso × puntuación / 5); no calcularlo mientras existan dominios críticos N/E.
- Sensibilidad: recalcular al variar cada peso ±20% y documentar si cambia la alternativa ganadora.
- Umbral de aceptación y reglas para N/E deben aprobarse antes de examinar resultados; no inventar umbrales tras ver la salida.

## 3. Alternativas a probar

| Capa | Candidatos | Riesgo que decide la PoC |
|---|---|---|
| Web | TypeScript + React/Next.js; alternativa React/Vite si SSR no es requisito | Complejidad de despliegue frente a necesidad real de SSR |
| Móvil | Flutter; React Native; Android nativo Kotlin como referencia | Gráficos, accesibilidad, integración, pruebas y coste de mantener iOS |
| API | Python + FastAPI; alternativa Python + Django REST Framework | Contratos, validación, latencia y complejidad de servicio |
| Datos | PostgreSQL sin extensión especializada inicialmente | Consultas históricas, índices, particionado y retención con volumen representativo |
| Tareas asíncronas | Proceso/worker simple y persistente antes de añadir broker | Reintentos, idempotencia, recuperación y observabilidad |
| Streaming/caché/objetos | Diferir hasta demostrar requisito | Carga, latencia, tamaño, coste y necesidad de retención binaria |
| Contratos | OpenAPI + validación y generación de tipos/clientes cuando aporte valor | Detección de incompatibilidades y deriva entre clientes |
| Calidad | pytest u otras herramientas adecuadas a cada lenguaje; análisis estático y escaneo de dependencias | Repetibilidad, cobertura de comportamiento crítico y falsos positivos |

## 4. Plan de PoC reproducibles (obligatorio antes de decisión final)

Todas las alternativas comparadas deben usar el mismo caso de uso, dataset de prueba versionado y criterios fijados previamente.

### PoC-A: contrato API
- Definir un contrato mínimo versionado para buscar un activo y obtener una evaluación fechada.
- Incluir estados de datos insuficientes, timeout, error del proveedor y resultado obsoleto.
- Validar ejemplos válidos e inválidos, compatibilidad y errores de esquema.
- Registrar comandos, versiones, salida y hashes de artefactos.

### PoC-B: persistencia histórica
- Guardar dos evaluaciones de un mismo activo sin sobrescribir la anterior.
- Consultar por activo, horizonte y fecha; verificar orden temporal, procedencia y versión metodológica.
- Registrar plan de consulta y tiempos solo con dataset y entorno descritos; no extrapolar resultados.

### PoC-C: cliente multiplataforma y gráficos
- Implementar la misma pantalla de búsqueda/ficha en las alternativas móviles consideradas.
- Renderizar el mismo fixture OHLCV, con volumen, zoom/desplazamiento y estados vacíos/error.
- Probar escalado de texto, lector de pantalla, movimiento reducido y orientación/tamaño de pantalla.
- En React Native/Flutter, registrar versiones y comandos de build en Windows; Android nativo sirve como referencia, no como decisión automática.

### PoC-D: tarea asíncrona
- Ejecutar una tarea de investigación con clave de idempotencia, reintento acotado y estados persistidos.
- Demostrar que un fallo de red no se convierte en captura válida ni duplica efectos.
- Verificar recuperación tras terminar el proceso y visibilidad del fallo.

### PoC-E: CI y seguridad
- Ejecutar pruebas desde un entorno limpio, análisis estático y revisión de dependencias.
- No imprimir secretos ni datos sensibles en logs.
- Conservar artefactos de resultados y versión exacta de herramientas.
- Un workflow verde solo acredita los checks ejecutados; no acredita rendimiento, conformidad ISO ni preparación para producción.

## 5. Diseño de límites recomendado para validar

- **Clientes:** presentación, accesibilidad, estado local no canónico y visualización; sin claves de proveedores ni lógica analítica duplicada.
- **API de producto:** autenticación/autorización, validación de contratos, versionado, límites de solicitud y respuestas de error consistentes.
- **Servicios de dominio:** identidad de activos/mercados, evaluación, metodología versionada, ranking y evidencia temporal.
- **Adaptadores de fuentes:** conectores aislados con permisos, límites, trazabilidad, procedencia y manejo de fallos específicos.
- **Persistencia:** PostgreSQL candidato inicial para metadatos, evaluaciones y observaciones normalizadas; validar el patrón temporal antes de extensiones especializadas.
- **Worker:** inicialmente proceso sencillo con estado persistido e idempotencia; introducir broker/caché/streaming solo con evidencia de carga o latencia.
- **CI y observabilidad:** pruebas, auditoría de cambios, logs estructurados sin secretos, métricas de fallos y artefactos reproducibles.

## 6. Registro de evidencia actual y brechas

- README de main describe clientes web, Android e iOS conectados a una plataforma central y prohíbe inferir preparación para producción sin evidencia integral.
- El comentario previo en Issue #9 registró que no se encontraron en la raíz los marcadores habituales de una aplicación Android/Flutter/React Native; tampoco acreditó una compilación móvil.
- El comentario de auditoría asociado a Issue #270 calificó provisionalmente la selección tecnológica en 3/10 por ausencia de PoC comparativas y benchmarks verificables.
- La rama de trabajo debe completar PoC, actualizar esta matriz con evidencias reales y registrar el ADR final. Hasta entonces, el stack definitivo queda **pendiente**, no aprobado.

## 7. Condiciones de cierre del Issue #9

- [ ] Matriz con puntuaciones respaldadas por evidencia y análisis de sensibilidad.
- [ ] PoC ejecutables para API, cliente/gráficos, persistencia y tareas asíncronas.
- [ ] Comandos, versiones, entorno, resultados y fallos reproducibles.
- [ ] ADR final con alternativa seleccionada, consecuencias, riesgos y condiciones de revisión.
- [ ] CI relevante verde y PR revisado; ningún cambio directo a main.
- [ ] Los resultados no afirman conformidad ISO/certificación ni rendimiento no medido.

**Conclusión actual:** la arquitectura lógica y el protocolo de evaluación quedan definidos, pero cerrar el Issue como completado antes de las PoC sería una afirmación no respaldada.


## 8. CI observada para el PR #301 (2026-10-24)

Se consultaron las ejecuciones asociadas al commit `569e9712d6e5fa5c94dc6a0b4545f3bd3f5935fd`. Dos workflows finalizaron con los jobs observados en PASS:

| Workflow | Run ID | Job | Resultado observado | Alcance real |
|---|---:|---|---|---|
| Reproducible market capture evaluation | 40056223784 | Test offline capture evaluation | PASS | Pruebas unitarias existentes, fixture sintético determinista y comparación de salidas; no compara stacks de aplicación |
| Requirements traceability validation | 40056223782 | Validate requirements catalogue and traceability | PASS | Validador del catálogo de requisitos y trazabilidad; no demuestra que las PoC de este Issue estén ejecutadas |

En ambas ejecuciones, el job de detección de alcance también terminó correctamente. Esto significa que los workflows existentes se ejecutaron, pero **no** constituye PASS de PoC de FastAPI/alternativas, clientes móviles, gráficos, PostgreSQL o procesamiento asíncrono. Tampoco demuestra que todos los checks del PR estén terminados ni que el stack esté aprobado.

- Run 40056223784: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056223784
- Run 40056223782: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056223782
- PR: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/301


## 9. Artefacto adicional: contrato API preliminar

Se añadió `docs/architecture/stack-poc-openapi.yaml` con un contrato OpenAPI 3.1.0 provisional para:
- búsqueda del catálogo canónico de activos;
- consulta de evaluaciones históricas inmutables por activo/horizonte;
- solicitud de evaluación bajo demanda con clave de idempotencia;
- consulta del estado de procesamiento y estados explícitos `failed`/`indeterminate`.

El servidor `example.invalid` es deliberadamente un marcador de posición, no un endpoint operativo. El contrato todavía requiere validación con un parser OpenAPI, pruebas de contrato y revisión de autenticación/autorización antes de considerarse válido o implementado. La existencia del YAML no acredita una API funcionando.

## 10. Diagrama de límites propuesto

```mermaid
flowchart LR
  Web[Web client] --> API[Versioned product API]
  Android[Android client] --> API
  IOS[iOS client] --> API
  API --> Domain[Canonical domain and evaluation service]
  Domain --> DB[(PostgreSQL candidate)]
  Domain --> Queue[Persisted task state / worker]
  Queue --> Sources[Read-only source adapters]
  Sources --> Evidence[Evidence and provenance store]
  Evidence --> DB
  Domain --> Results[Immutable evaluation records]
  Results --> DB
```

Este diagrama expresa límites propuestos, no infraestructura desplegada. La elección concreta de worker, persistencia de evidencia y almacenamiento de objetos queda pendiente de PoC y requisitos de retención.

## 11. Estado actualizado de aceptación

- [x] Criterios y pesos de evaluación documentados como propuesta (sin puntuaciones inventadas).
- [x] ADR provisional con alternativas, riesgos y condiciones de revisión.
- [x] Contrato OpenAPI inicial y diagrama lógico propuestos.
- [x] Dos workflows existentes observados en PASS, con sus límites documentados.
- [x] Validación automática de sintaxis/estructura OpenAPI 3.1.0 con `openapi-spec-validator` (run 40056998001 PASS).
- [x] PoC API FastAPI/SQLite: búsqueda, Bearer auth configurable, idempotencia, errores y consulta de historial (run 40056917356 PASS).
- [x] PoC PostgreSQL 16: orden histórico y bloqueo de UPDATE/DELETE (run 40056885420 PASS).
- [x] Worker secuencial PoC: procesa una solicitud persistida y devuelve `indeterminate` cuando no hay motor analítico (test incluido en run 40056998071 PASS).
- [ ] Pruebas de contrato cliente-servidor; el validador OpenAPI por sí solo no las sustituye.
- [ ] Worker con concurrencia, reintentos y recuperación demostrada tras interrupción.
- [ ] PoC comparativas de cliente móvil/gráficos (Flutter, React Native y referencia nativa) y web.
- [ ] Medición representativa de persistencia/consultas, seguridad/licencias y recursos de build.
- [ ] Matriz puntuada con resultados medidos y análisis de sensibilidad.
- [ ] ADR definitivo ratificado y revisión del PR.


## 12. CI específico del contrato OpenAPI

Se añadió `.github/workflows/issue-9-openapi-contract.yml`. En el commit `b64ce55e49c4271ad7702697e43a08c0b599c5c8` se sustituyó la validación artesanal por el validador de especificaciones OpenAPI `openapi-spec-validator==0.7.2`, con Python 3.12 y las acciones de checkout/setup-python fijadas a SHA completos.

Comando configurado en CI:

```bash
python -m pip install --disable-pip-version-check openapi-spec-validator==0.7.2
openapi-spec-validator docs/architecture/stack-poc-openapi.yaml
```

**Estado de ejecución:** no confirmado. La consulta de ejecuciones asociadas a ese commit y los estados combinados no devolvió resultados; por tanto, no se registra PASS hasta que GitHub Actions publique un resultado verificable. Incluso con el validador OpenAPI en PASS, seguirán pendientes las pruebas de contrato cliente-servidor y las PoC comparativas de API, persistencia histórica, cliente/gráficos y tareas asíncronas.

## 13. PoC ejecutable de API, historial e idempotencia

Se añadieron `scripts/stack_poc/research_api.py`, `tests/stack_poc/test_research_api.py` y el workflow `.github/workflows/issue-9-stack-poc.yml`. La PoC usa FastAPI con SQLite para poder ejecutar pruebas sin un servicio de base de datos local; **SQLite es únicamente una ayuda de prueba y no valida PostgreSQL ni sustituye la PoC de persistencia requerida**.

Comportamientos que cubren las pruebas automatizadas:
- búsqueda del catálogo de activos y forma de respuesta vacía;
- autenticación Bearer configurable, sin credencial predeterminada; el servicio falla cerrado si no se configura el secreto;
- solicitud bajo demanda con clave de idempotencia, repetición del mismo payload y conflicto HTTP 409 cuando la clave se reutiliza con otro payload;
- errores 404 para activo/solicitud inexistente;
- persistencia de dos evaluaciones históricas con metodología distinta, orden temporal y filtro por horizonte.

El workflow instala versiones fijadas de FastAPI y HTTPX y ejecuta `unittest` en Python 3.12. **Resultado CI observado:** el run [40056765545](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056765545) ejecutó el job `api-history-idempotency` con conclusión `success` y los tests terminaron en `success`. En un run posterior, [40056876572](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056876572), la suite falló porque el workflow SQLite descubrió también `test_postgres_history.py` sin instalar `psycopg`. Se corrigió el workflow para ejecutar solo `test_research_api.py`. La ejecución corregida [40056917356](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056917356) terminó con el job `api-history-idempotency` en `success`, incluidos los tests. El fallo anterior se conserva como evidencia de la corrección y no se oculta. La implementación no ejecuta análisis real ni worker asíncrono: las solicitudes permanecen `queued` en esta PoC. Tampoco implementa autorización por roles, migraciones, PostgreSQL, límites operativos ni pruebas de concurrencia; estos son riesgos/alcances pendientes.

## 14. PoC de persistencia PostgreSQL

Se añadió `scripts/stack_poc/postgres_schema.sql`, una prueba de integración `tests/stack_poc/test_postgres_history.py` y el workflow `.github/workflows/issue-9-postgres-poc.yml`. El workflow levanta PostgreSQL 16 como servicio efímero, instala `psycopg[binary]==3.2.6` y ejecuta pruebas con Python 3.12.

La PoC verifica:
- escritura de evaluaciones distintas para el mismo activo, con horizonte y versión metodológica;
- orden de consulta por timestamp descendente;
- rechazo explícito de `UPDATE` y `DELETE` sobre el historial mediante trigger de PostgreSQL.

**Resultado CI observado:** los runs [40056876625](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056876625) y [40056885420](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056885420) completaron el job `postgres-history` con conclusión `success`, incluidos inicialización del servicio PostgreSQL, instalación de psycopg y ejecución de las pruebas. Es una prueba de esquema/retención de historial, no un benchmark representativo, una migración de producción ni una validación de recuperación/backup. El worker persistente y la idempotencia transaccional todavía requieren PoC separada.

## 15. Worker persistente de PoC y abstención explícita

Se añadió `scripts/stack_poc/research_worker.py` y una prueba que solicita dos horizontes, procesa una tarea pendiente una sola vez, verifica que una segunda ejecución no duplique el resultado y consulta el estado persistido. Cuando el motor analítico no está integrado, el worker registra resultados `indeterminate` con la limitación `analysis_engine_not_integrated`; no inventa una evaluación de inversión.

La respuesta de `GET /v1/evaluation-requests/{request_id}` y el contrato OpenAPI se ajustaron para devolver una lista de evaluaciones por horizonte. El workflow API run [40056998071](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056998071) ejecutó el paso de tests con conclusión `success`; el job estaba terminando la limpieza cuando se verificó. El workflow OpenAPI run [40056998001](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40056998001) completó el paso de validación con `success`.

**Límite restante:** este worker PoC procesa una tarea en una transacción SQLite y demuestra persistencia/idempotencia secuencial. No acredita concurrencia entre múltiples workers, recuperación tras caída a mitad de ejecución, reintentos temporizados ni integración con fuentes/analizador real. Esos casos requieren pruebas específicas antes de considerar completa la PoC asíncrona.


## 16. Verificación adicional del worker: concurrencia y rollback transaccional

Se añadieron `tests/stack_poc/test_worker_reliability.py` y un paso dedicado en `.github/workflows/issue-9-stack-poc.yml`. El run [40057212197](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40057212197) completó con `success` los pasos `Run API, history and idempotency PoC tests` y `Run worker concurrency and transaction-recovery tests`. La validación OpenAPI del mismo HEAD también pasó en el run [40057212129](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40057212129).

Casos añadidos:
- ocho workers concurrentes compiten por doce solicitudes persistidas; cada solicitud se procesa una vez, quedan 24 evaluaciones para dos horizontes por solicitud y no aparecen duplicados por clave `(request_id, horizon)`;
- una transacción que cambia temporalmente una solicitud a `running` se revierte antes del commit; se comprueba que la solicitud sigue `queued`, un worker la procesa después y una segunda ejecución no crea resultados adicionales.

**Alcance preciso:** esto prueba concurrencia de procesos/hilos contra la misma base SQLite y recuperación tras rollback de transacción. No equivale a matar un proceso en medio de operaciones externas, recuperación distribuida, reintentos con backoff, leasing/visibilidad de cola ni garantía de entrega exactamente-una-vez entre sistemas. Como el worker no llama a proveedores ni al motor analítico, no prueba reintentos de red ni recuperación de una evaluación real. El run PostgreSQL del mismo commit debe verificarse por separado antes de registrar PASS actualizado.

## 17. Estado de cierre actualizado

- [x] PoC de concurrencia local con múltiples workers y solicitudes persistidas.
- [x] Prueba de rollback transaccional y reprocesamiento secuencial sin duplicar resultados.
- [x] CI del worker reliability: run 40057212197, ambos pasos de test en success.
- [x] Validación OpenAPI en el HEAD de esta ampliación: run 40057212129, success.
- [ ] Recuperación ante terminación forzada del proceso y fallos entre sistemas externos.
- [ ] Pruebas contractuales ejecutando cliente generado o cliente HTTP frente al servidor real de la PoC.
- [ ] Comparativa móvil/gráficos y web reproducible en un entorno con toolchains instalados.
- [ ] Benchmarks comparables de API/persistencia/build, revisión de licencias y seguridad.
- [ ] Matriz final puntuada con mediciones y análisis de sensibilidad; ADR definitivo.
- [ ] Verificación final de todos los checks del PR y revisión antes de merge.

No se considera completado el Issue #9 hasta cerrar las condiciones pendientes con evidencia verificable.


## 18. Herramienta de sensibilidad con puerta de evidencia

Se añadió `scripts/stack_poc/sensitivity_analysis.py` y `tests/stack_poc/test_sensitivity_analysis.py`. La herramienta exige que cada alternativa tenga puntuación entera 1–5 y referencia de evidencia no vacía para **cada** criterio, y que los pesos sumen 100. Si falta cualquier dato, devuelve `status=incomplete`, una lista de ausencias y no calcula ranking (código de salida 2). Si la matriz está completa, calcula puntuación ponderada y cambia cada peso individualmente ±20%, renormaliza el total y registra si cambia el orden.

Los tests cubren bloqueo por datos ausentes, ranking/sensibilidad con datos sintéticos de test y validación de pesos. Los candidatos sintéticos del test solo prueban el algoritmo; no son puntuaciones de Flutter, React Native ni de ninguna tecnología real. La matriz real permanece N/E hasta adjuntar evidencia comparativa. El workflow de PoC incluye ahora esta suite.


## 18. Medición de geometría web disponible (2026-10-24)

La PoC de referencia ejecutó sus tres tests de geometría y un microbenchmark en el runner GitHub Actions del workflow [40058440405](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058440405), commit `5554cb2be65cb9b55f663d3234a8bf259616561b`. Registro durable: `docs/architecture/evidence/issue-9-web-geometry-linux-ci-40058440405.json`.

- Entorno: Linux hosted runner, Node.js v22.23.3, AMD EPYC 9V74, 4 vCPU, RAM reportada 16,766,414,848 bytes.
- Fixture: 12 velas sintéticas, SHA-256 `0265cfa5e4d4e6673476bc7db84ed98d43147409172a00deda958bd82823f63d`.
- Geometría JavaScript: 100 iteraciones de calentamiento y 1.000 medidas; mínimo 0.001512 ms, mediana 0.002433 ms, p95 0.004987 ms, máximo 0.419061 ms.
- RSS: 51,630,080 bytes antes y 55,463,936 bytes después. Son dos muestras de RSS, no memoria pico.
- Tests: 3 PASS, 0 FAIL.

**Interpretación:** esto solo mide el cálculo geométrico de velas, no renderizado DOM, GPU, memoria pico, arranque ni preparación visible del gráfico. Es una sola ejecución de CI, no un conjunto de tres builds y no debe compararse con Windows local o con Flutter/React Native. Por ello no se asigna aún puntuación de rendimiento al stack web.

## 19. Flutter Android PoC: medición en curso

La rama `feat/issue-9-flutter-chart-reference` contiene una PoC Flutter que dibuja el mismo fixture canónico con `CustomPainter`, volumen y tabla de datos. El workflow [40058442391](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058442391) comprobó la igualdad byte a byte del fixture; en la última consulta la instalación de Flutter seguía en curso, por lo que no se declaran todavía tests ni builds PASS. El workflow está diseñado para ejecutar tests de widgets y tres builds Android limpios, registrar tiempo, RSS máximo del proceso y tamaño APK; después deben conservarse los resultados y comparar solo las medidas compatibles.


## 20. Python PoC dependency/security/licence review (2026-10-24)

The dependency audit workflow completed successfully in [run 40058494463](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058494463): `pip check` passed, `pip-audit` reported no known vulnerabilities for the pinned Python PoC requirements/advisory data available to the run, and the direct/transitive licence inventory was uploaded as [artifact 12546825286](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058494463/artifacts/12546825286). Manual checks for rows whose installed metadata said `UNKNOWN` are recorded in `docs/architecture/evidence/issue-9-python-dependency-license-review.md`.

This is a completed review for the current **Python PoC environment**, not for the final product. Psycopg 3 declares LGPL-3.0-only, so packaging/distribution implications require a deployment-specific review. The future Flutter/Dart/Android, React/Node and iOS toolchains/dependency graphs remain unaudited until their candidate implementations and locks exist. A clean advisory scan does not establish absence of all vulnerabilities.

## 21. Matrix scoring and sensitivity status

The sensitivity-analysis implementation exists and is tested to reject any candidate with missing scores or evidence references. However, the real candidate matrix still has critical dimensions without measured Flutter, React Native, web-browser and local-Windows evidence. **Do not produce a winner or mark the matrix complete yet.** A synthetic unit test of the sensitivity algorithm is not a sensitivity result for actual stack candidates. Once comparable evidence is available, score each criterion with an evidence link, run the ±20% one-weight-at-a-time scenarios, and record ranking stability before the ADR is ratified.


## 22. Repeticiones independientes del microbenchmark web (2026-10-24)

La segunda ejecución del workflow [40058638191](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058638191) completó 3 procesos Node independientes; cada proceso hizo 100 calentamientos y 1.000 observaciones. Registro durable: `docs/architecture/evidence/issue-9-web-geometry-linux-ci-40058638191.json`.

| Proceso | Mediana (ms) | p95 (ms) | RSS antes (bytes) | RSS después (bytes) |
|---:|---:|---:|---:|---:|
| 1 | 0.001663 | 0.003435 | 51,240,960 | 55,762,944 |
| 2 | 0.001652 | 0.003505 | 51,232,768 | 55,754,752 |
| 3 | 0.002985 | 0.003796 | 51,412,992 | 55,672,832 |

Mediana de las tres medianas: **0.001663 ms**; rango de medianas: **0.001652–0.002985 ms**. Entorno: Linux hosted runner, Node v22.23.3, AMD EPYC 9V45, 4 vCPU, RAM reportada 16,766,414,848 bytes. Fixture SHA-256: `0265cfa5e4d4e6673476bc7db84ed98d43147409172a00deda958bd82823f63d`. Los 3 tests geométricos terminaron PASS.

La repetición independiente mejora la reproducibilidad de la microoperación, pero no equivale a tres builds limpios ni mide la pantalla renderizada. El RSS sigue siendo muestreo antes/después, no pico. No usar esta cifra para clasificar el stack frente a Flutter/React Native ni para inferir experiencia real de usuario.


## 23. Windows-hosted geometry cross-check and fixture line endings (2026-10-24)

The Windows measurement script initially exposed that Git's CRLF checkout changed the raw SHA-256 of the canonical JSON fixture even though the parsed JSON was identical. Added `.gitattributes` to force LF for canonical fixture JSON and the web benchmark inputs. The next Windows workflow run confirmed the same raw fixture SHA-256 as Linux: `0265cfa5e4d4e6673476bc7db84ed98d43147409172a00deda958bd82823f63d`.

| Environment / evidence | Node | Fixture SHA-256 | Median geometry time | p95 | RSS before → after |
|---|---|---|---:|---:|---:|
| Hosted Linux, [run 40058638191](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058638191) | 22.23.3 | `0265cfa5e4d4e6673476bc7db84ed98d43147409172a00deda958bd82823f63d` | 0.001663 ms (median of 3 process medians) | 0.003796 ms (max of process p95s) | ~51–55 MB per process |
| Hosted Windows Server 2025, [run 40059988216](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059988216) | 22.23.4 | same | 0.0032 ms | 0.0076 ms | 35,377,152 → 39,354,368 bytes |

These runs validate cross-platform fixture integrity and the measurement script, not a cross-OS performance ranking. They use different hosted machines/OS runtimes, and the Windows run is not the user's Windows 11 PC. Both measure Node geometry only, not browser rendering or on-screen chart readiness. The Windows result is preserved in `docs/architecture/evidence/issue-9-web-geometry-windows-ci-40059988216.json`.


## 24. Trazabilidad normativa oficial para la evaluación (2026-10-24)

La matriz y el protocolo se alinean con estos modelos oficiales como referencia de evaluación; no se afirma certificación ni conformidad completa del producto.

| Norma oficial | Estado consultado | Aplicación en Issue #9 | Límite explícito |
|---|---|---|---|
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) — modelo de calidad del producto | Edición 2 publicada en 2023; reemplaza ISO/IEC 25010:2011 | Trazar adecuación funcional, eficiencia de rendimiento, compatibilidad, capacidad de interacción, fiabilidad, seguridad, mantenibilidad, flexibilidad y seguridad operacional según aplique | El modelo no aporta por sí solo puntuaciones de candidatos ni umbrales universales |
| [ISO/IEC 25023:2016](https://www.iso.org/standard/35747.html) — medición de calidad del producto | La página oficial indica que sigue vigente tras revisión, pero está en proceso de revisión y muestra ISO/IEC DIS 25000-23.2 en desarrollo | Definir medidas operacionales, método de captura, entorno, repeticiones y registro de resultados | La norma no establece rangos universales para calificar medidas; los criterios deben basarse en necesidades y categoría del sistema |
| [ISO/IEC/IEEE 12207:2026](https://www.iso.org/es/contents/data/standard/09/02/90219.html) — procesos del ciclo de vida del software | Edición 2 publicada en abril de 2026; la edición 2017 figura retirada en la página oficial | Gobernanza de requisitos, diseño, construcción, verificación, operación, mantenimiento y control de cambios del proceso de selección | No sustituye la planificación real ni demuestra que un proceso se haya ejecutado correctamente |
| [ISO/IEC 27001:2022](https://committee.iso.org/es/norma/27001) — sistema de gestión de seguridad de la información | Edición 3 publicada en 2022, con Amendment 1:2024 | Enmarcar la identificación de riesgos, tratamiento de dependencias, gestión de secretos, control de cambios y evidencia de revisión | No certifica la PoC ni sustituye el análisis técnico de vulnerabilidades/licencias |

### Regla de uso

1. Se conserva la evidencia de fuente y edición consultada; si ISO publica una nueva edición o borrador, se vuelve a verificar el estado antes de actualizar el criterio.
2. Los tiempos, memoria, tamaño de artefactos y resultados de seguridad se reportan como observaciones reproducibles, no como “cumple/no cumple ISO” por un número inventado.
3. Los pesos de la matriz son decisiones del producto, no pesos prescritos por ISO. La escala 1–5 requiere evidencia y justificación explícita.
4. Una auditoría de dependencias o una compilación verde no equivale a conformidad normativa ni certificación.


## 25. Web chart browser smoke test (2026-10-24)

The web PoC now exposes accessible buttons for zoom in/out and pan left/right, while retaining the textual OHLCV table. Chromium smoke test passed in [run 40060309796](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40060309796): it loaded the 12-candle canonical fixture, verified 12 table rows, exercised zoom to 125%, panned right and left, returned to 100%, and observed no page errors. The three-process Node geometry microbenchmark in the same run reported per-process medians 0.003307, 0.003266 and 0.003327 ms; median-of-medians 0.003307 ms. p95 observations were 0.007203, 0.007133 and 0.007163 ms.

This is a browser smoke test and geometry microbenchmark, not a full performance profile: it does not measure real-device rendering, frame time, GPU, memory peak, network latency or chart-ready time. Playwright is CI-only tooling and is not a web-client runtime dependency.


## 26. Mobile PoC repeated-build evidence available at this checkpoint (2026-10-24)

### Flutter Android (Debug + Release)

[Run 40059925721](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059925721) passed on Ubuntu 24.04.5, AMD EPYC 7763, 4 vCPU, 16.77 GB RAM, Flutter 3.47.5 stable, Node 22.23.3 and Temurin JDK 17.0.20.1. Debug clean-build times were 163.34 / 19.42 / 18.74 s (median 19.42 s, range 18.74–163.34 s), incremental Debug 4.50 s, Debug APK 150,302,356 bytes. Release build was 57.13 s and Release APK 45,445,816 bytes. Maximum RSS observations were 281,224 / 116,092 / 108,880 KB for clean builds, 102,080 KB incremental and 124,632 KB Release. Full record: `docs/architecture/evidence/issue-9-flutter-android-ci-40059925721.md`.

### React Native iOS (Debug)

[Run 40059801779](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801779) passed on macOS 26 ARM64, Apple M1 virtual, 3 cores, 7 GB RAM, Xcode 26.6 and Node 22.23.4. Debug clean-build times were 64.51 / 39.76 / 40.60 s (median 40.60 s, range 39.76–64.51 s), Debug rebuild after JS timestamp touch 13.86 s (not treated as JS-bundle incremental because Debug may skip bundling), Debug app bundle 163,404 KB. Maximum RSS observations: 205,275,136 / 214,040,576 / 212,500,480 bytes; peak memory footprint observations: 123,276,096 / 123,292,480 / 121,801,600 bytes. Full record: `docs/architecture/evidence/issue-9-react-native-ios-repeated-builds-40059801779.md`.

### Comparability and missing cells

These Android and iOS measurements are not compared against one another. Android Release/Debug can be compared only with React Native Android Release/Debug measured on the same runner image; iOS Debug/Release can be compared only with React Native iOS Debug/Release on the same macOS image. The current repeated React Native Android build/release workflow, the Release incremental JS rebuilds, and the current Flutter iOS Debug/Release workflow are still pending. The earlier React Native Android result is one build only and cannot substitute for its three-run summary.

The measurements support the feasibility of both Flutter and bare React Native, but do not yet justify a weighted winner. Real-device chart readiness, interaction latency, memory under a running chart, physical-device accessibility, and the target Windows PC report remain N/E. Do not ratify ADR-0001 or close Issue #9 at this checkpoint.


## 27. Parciales con cobertura de evidencia (2026-10-24)

El script `scripts/stack_poc/sensitivity_analysis.py` ahora devuelve `partial_scores` cuando faltan datos: criterios puntuados, criterios ausentes, porcentaje de peso cubierto y un subtotal normalizado sobre los criterios con evidencia. En estado `incomplete`, la salida sigue teniendo `ranking=[]` y `sensitivity=[]`. Los subtotales parciales son diagnósticos y no se pueden comparar entre candidatos con distinta cobertura; no sustituyen la matriz completa ni autorizan ratificar ADR-0001. Se añadió un test que verifica este comportamiento.


## 28. Puntuación parcial con evidencia y sensibilidad de subconjunto (2026-10-24)

El input reproducible está en `docs/architecture/evidence/issue-9-partial-score-input.json`; el workflow genera el JSON de salida como artefacto y comprueba que, al faltar criterios, no se produce ranking final ni sensibilidad completa. La cobertura de pesos y subtotales diagnósticos en este checkpoint es:

| Alternativa | Criterios con puntuación/evidencia | Peso cubierto | Subtotal normalizado parcial | Interpretación |
|---|---|---:|---:|---|
| Web React/Vite + API compartida | Gráficos 4, persistencia 3, pruebas/CI 4 | 35% | 74.2857/100 | Diagnóstico parcial; seguridad, build/recursos, mantenibilidad, contratos cliente y coste/licencias siguen N/E |
| Flutter + API compartida | Gráficos 4, persistencia 3, pruebas/CI 4 | 35% | 74.2857/100 | Diagnóstico parcial; iOS Debug/Release actualizado y revisión de licencias siguen pendientes |
| React Native bare + API compartida | Gráficos 3, seguridad 3, persistencia 3, pruebas/CI 3 | 50% | 60/100 | Diagnóstico parcial; build Android Release repetido, UI nativa automatizada y revisión legal de licencias siguen pendientes |
| Kotlin Android + cliente iOS separado | Persistencia 3 | 10% | 60/100 | No comparable; no hay PoC de cliente Kotlin ni cliente iOS separado |

Estos subtotales **no son una clasificación de stacks**: las coberturas difieren y varias puntuaciones son provisionales. El criterio de contratos cliente/API queda N/E porque las pantallas PoC todavía no consumen el API real. Los scores están respaldados por los runs referenciados en el input JSON.

Para una sensibilidad acotada, se tomó solo el subconjunto con evidencia para Web, Flutter y React Native: gráficos/series, persistencia histórica común y pruebas/CI. Los pesos originales 15:10:10 se normalizaron a 42.8571:28.5714:28.5714. Con scores (Web 4/3/4, Flutter 4/3/4, React Native 3/3/3), el subtotal de este subconjunto es Web=Flutter 74.2857 y React Native 60. El script recalcula cada peso ±20% (seis escenarios) y la ordenación de este subconjunto no cambia: Web y Flutter empatados por encima de React Native. Este resultado no incluye seis criterios, no incluye Kotlin y **no ratifica un ganador final**. El input de sensibilidad reproducible está en `docs/architecture/evidence/issue-9-subset-sensitivity-input.json`; el workflow debe terminar y preservar el artefacto antes de considerar este resultado verificado.


## 29. Comparación observada de builds Android Release (2026-10-24)

Los dos resultados siguientes se ejecutaron en la misma clase de runner Ubuntu 24.04 / imagen `20261012.334`, AMD EPYC 7763, 4 vCPU, 16.77 GB RAM, Node 22.23.3 y Temurin JDK 17.0.20.1. Son instancias separadas; cada registro conserva su propio estado de caché.

| Stack | Build Release | Artefacto Release | Debug limpio: mediana | Artefacto Debug | Evidencia |
|---|---:|---:|---:|---:|---|
| Flutter 3.47.5 | 57.13 s | 45,445,816 bytes | 19.42 s (3 runs; rango 18.74–163.34 s) | 150,302,356 bytes | `issue-9-flutter-android-ci-40059925721.md` |
| React Native bare 0.88.0 | 124.23 s | 55,447,309 bytes | 70.62 s (3 runs; rango 67.66–147.40 s) | 125,271,411 bytes | `issue-9-react-native-android-repeated-builds-40059801811.md` |

En estas observaciones, Flutter Release compiló aproximadamente un 54.0% más rápido y produjo un APK aproximadamente un 18.0% más pequeño que React Native Release. Esto es una comparación de artefactos de PoC en la misma clase de host, no una conclusión global: el incremental Release tras editar el JavaScript aún está pendiente en React Native, las firmas son de prueba/no producción y no se midieron arranque ni memoria del proceso ejecutándose. Los tamaños Debug no deben usarse como sustituto de los Release.

### iOS — Debug disponible, Release todavía no comparable

Flutter iOS Debug: mediana 23.43 s, rango 22.49–40.14 s, app 97,276 KB; Release 29.56 s / 14,560 KB (code signing disabled). React Native iOS Debug: mediana 40.60 s, rango 39.76–64.51 s, app 163,404 KB. La Release de React Native y su recompilación incremental después de editar `App.js` siguen pendientes; por ello no se declara un ganador iOS todavía.


## 30. Corrección de escala de puntuación en sensibilidad (2026-10-24)

La primera salida del subconjunto de sensibilidad reveló que `score_out_of_100` estaba serializando valores normalizados entre 0 y 1, pese al nombre del campo. Se corrigió el cálculo para devolver la escala 0–100, se añadió una aserción unitaria (`70/100` para el caso de prueba) y el workflow ahora valida explícitamente `74.2857, 74.2857, 60.0` en el subconjunto diagnóstico. El artefacto previo de [run 40061223306](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061223306) queda supersedido; usar únicamente el nuevo artefacto tras esta corrección. La clasificación sigue siendo parcial y no ratifica ADR-0001.

## 31. Repeticiones móviles y auditoría de dependencias — actualización 2026-10-24

Los registros detallados más recientes están en [evidencia móvil y dependencias](evidence/issue-9-mobile-build-and-dependency-evidence-400616.md). Sustituyen como observaciones de build a las ejecuciones anteriores para los commits indicados, sin convertir la muestra CI en una clasificación final.

| PoC | Tres builds Debug (s) | Incremental (s) | Release build (s) | Release artifact | Seguridad/licencias |
|---|---|---:|---:|---|---|
| Flutter 3.47.5 Android | 161.49 / 19.18 / 18.28 | 7.75 | 55.85 | APK 45,445,816 bytes | Widget tests y fixture PASS; inventario Dart/Gradle generado, revisión completa de licencias/avisos aún pendiente |
| React Native bare 0.88.0 Android | 152.53 / 70.36 / 67.85 | 15.65 (Release tras editar JS) | 123.33 | APK 55,447,313 bytes | `npm audit` 0 vulnerabilidades reportadas; inventario 803 entradas sin `UNKNOWN`; revisar CC-BY-4.0, BlueOak-1.0.0 y avisos de paquetes deprecados |

Los tiempos reflejan el efecto de cachés entre ejecuciones y no deben leerse como una prueba A/B controlada; se conservan todas las observaciones y no solo la mediana. El workflow de comparación en el mismo emulador Android debe terminar para aportar arranque, visibilidad de UI y PSS/RSS de las aplicaciones en ejecución.

La primera auditoría Python sí pasó `pip-audit` y `pip check`, pero 16 de 42 etiquetas de licencia fueron `UNKNOWN`. Se actualizó el workflow para combinar metadata/clasificadores y preservar ficheros de licencia/aviso; esa nueva salida debe revisarse antes de declarar completa la revisión legal.

**iOS:** las medidas anteriores se excluyen de la comparación directa porque Flutter construía para `iphoneos` y React Native para Simulator. Los workflows se corrigieron para usar iOS Simulator ARM64 en ambos; el nuevo par de ejecuciones debe terminar y sus logs confirmarse antes de puntuar build, memoria o tamaño iOS.

**Decisión:** todavía no se ratifica ADR-0001 ni se cierra Issue #9. Las celdas de ejecución en el Windows 11 del usuario, UI en dispositivo físico, accesibilidad móvil, revisión legal de todos los avisos, API/persistencia bajo carga representativa y sensibilidad de la matriz completa permanecen N/E o pendientes de evidencia.


## 32. Web PoC browser verification — 2026-10-24

The latest [web chart workflow run 40063297746](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063297746) passed all steps on the current evaluation branch. Playwright 1.64.1/Chromium 156 ran the same synthetic 12-candle fixture three times; all three browser smoke tests passed. Measured chart-ready samples: 128.745, 173.772 and 121.467 ms. Three fresh Node processes measured geometry-only median times of 0.003226, 0.003296 and 0.003226 ms (aggregate median-of-medians 0.003226 ms). These are different measurements: browser chart-ready includes the tested page rendering path; the geometry microbenchmark excludes DOM/layout/GPU and must not be treated as user-visible latency. Full evidence and limits: `docs/architecture/evidence/issue-9-web-browser-benchmark-40063297746.md`.

The browser tooling audit reported zero npm vulnerabilities. The workflow logs nevertheless include upstream Node deprecation warnings for `punycode` and `url.parse()`, and a Node 20 deprecation warning for pinned GitHub Actions. Record these as maintenance follow-ups; they are not npm audit vulnerabilities. Mobile same-emulator runtime measurement, updated iOS comparisons, full licence-obligation review and the user's own Windows 11 benchmark remain pending. This evidence does not change the provisional ranking or authorize ADR ratification.


## 33. Windows-hosted capture script validation — 2026-10-24

[Run 40063297774](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063297774) passed PowerShell parsing and environment/web geometry capture. The host was Windows Server 2025 Datacenter, AMD EPYC 7763, 4 logical CPUs, ~17.17 GB RAM, Node 22.23.4 and JDK 17.0.20.1; Flutter was not installed, so the workflow explicitly skipped Flutter builds. On the canonical 12-candle fixture, Windows-hosted Node geometry median was 0.0033 ms, p95 0.0088 ms; RSS before/after was 35,315,712 / 39,587,840 bytes (two samples, not peak). Evidence: `docs/architecture/evidence/issue-9-windows-hosted-script-validation-40063297774.md`. This is a hosted Windows Server baseline, not the user's Windows 11 PC; local Android builds, process-tree peak memory and artifact size remain N/E until the script runs on the target PC.


## 34. Python dependency security and licence triage — 2026-10-24

The latest [dependency audit run 40063600439](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063600439) passed `pip check`, `pip-audit` (no known vulnerabilities reported at scan time), licence inventory generation and four unit tests for conservative licence triage. The inventory contains 42 installed Python distributions. The triage identified licence expressions from version-bound captured text for 15 packages; 14 had aligned metadata/classifier values, 2 metadata-only, and 7 classifier-only. Four remain manual-review-required, and three of those lack captured licence text in the installed distribution. The fourth, `typing_extensions 4.16.0`, has a bundled Python licence-history file without an unambiguous package-level SPDX expression. Evidence, official package metadata links, and artifact ID 12548740668: `docs/architecture/evidence/issue-9-python-license-review-40063600439.md`.

The report also found no separate NOTICE file/text for 39 packages. This is not by itself proof of a violation; obligations depend on the applicable licence text and distribution model. Therefore the security scan is PASS but licence review is only PARTIAL. ADR-0001 must remain provisional until the four manual-review items and distribution obligations are resolved. The new tests prevent version-specific licence overrides from being silently reused after a dependency upgrade.


## 35. Flutter repeated Android/iOS builds — 2026-10-24

The latest Flutter Android [run 40063244382](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244382) and iOS [run 40063244341](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244341) both passed. Android on Ubuntu 24.04.5 / Intel Xeon Platinum 8573C / 4 vCPU / 16.77 GB / Flutter 3.47.5: clean Debug 178.59 / 17.70 / 17.14 s (cold-build outlier retained), incremental Debug 8.77 s, Release 52.52 s / 45,445,816-byte APK. Clean Debug APKs were 150,302,356 bytes; post-source-edit artifact was 165,199,496 bytes. Clean Debug peak RSS values: 292,380 / 113,952 / 120,344 KB; incremental 106,772 KB; Release 125,040 KB.

On macOS / virtual Apple M1 / 3 cores / 7 GB, Flutter iOS Simulator Debug clean builds took 81 / 57 / 40 s with 142,300 KB app bundle; incremental Debug took 21 s. Device-target Release (code signing disabled) took 44 s and produced a 14,560 KB app bundle. Full memory values and artifact references are in `docs/architecture/evidence/issue-9-flutter-repeated-builds-40063244382-40063244341.md`. These metrics are hosted CI observations; do not compare Android with iOS or substitute them for local Windows performance. Android/iOS SDK licensing and production signing remain separate deployment checks.


## 36. React Native iOS repeated builds — 2026-10-24

The updated [React Native iOS workflow 40063271628](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271628) passed. On macOS / virtual Apple M1 / 3 cores / 7 GB / Xcode 26.6, Simulator Debug builds took 85 / 39 / 34 s with 82,492 KB app bundle; device-target Release (code signing disabled) took 76 s / 22,420 KB, and the incremental Release build after JS edit took 23 s (post-edit bundle 21,400 KB). Max RSS and peak memory footprint are recorded in `docs/architecture/evidence/issue-9-react-native-ios-repeated-builds-40063271628.md`. The 804-entry licence inventory has zero UNKNOWN labels and one UNLICENSED entry for the private PoC app; CC-BY-4.0 and BlueOak-1.0.0 expressions still need obligation/notice review.

The Flutter and React Native device-target Release artifacts were built in separate workflow runs on the same class of macOS runner (virtual Apple M1, 3 cores, 7 GB, Xcode 26.6), but not on the same machine or with controlled cache state. Their observed artifact sizes (14,560 KB Flutter; 22,420 KB React Native) are recorded separately; **do not use the 44 s vs 76 s build times as a scored head-to-head result**. The common-emulator workflow is the planned same-runner comparison for Android; iOS build-time differences remain diagnostic until a controlled repeated A/B run is defined. The React Native workflow did not measure incremental Simulator Debug; do not fill that cell by inference. Runtime on physical devices, accessibility, local Windows build, and legal obligation review remain outstanding.


## 37. React Native Android repeated builds — 2026-10-24

The updated [React Native Android workflow 40063271581](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271581) passed. On Ubuntu 24.04 / AMD EPYC 7763 / 4 vCPU / 16.77 GB / Node 22.23.3 / Temurin JDK 17.0.20.1, clean Debug builds took 156.13 / 70.88 / 68.90 s (cold run retained), incremental Release after JS edit 17.19 s, and Release 128.24 s / APK 55,447,309 bytes. Debug APKs were each 125,271,411 bytes. Peak RSS: Debug 116,276 / 96,612 / 99,116 KB; Release 100,632 KB; incremental Release 103,112 KB. `npm audit --audit-level=high` reported zero vulnerabilities and the 804-entry licence inventory had zero UNKNOWN labels. Full record: `docs/architecture/evidence/issue-9-react-native-android-repeated-builds-40063271581.md`.

The Flutter and React Native standalone builds ran on Ubuntu 24.04 / 4 vCPU / ~16.77 GB, but on different virtual CPU models (Intel Xeon Platinum 8573C vs AMD EPYC 7763) and separate machines. Their artifact sizes (45,445,816 bytes Flutter; 55,447,309 bytes React Native) are useful recorded observations; **the 52.52 s vs 128.24 s build times are not a valid scored head-to-head comparison** under the no-mixed-machine rule. Use the shared-runner three-client workflow for comparative build/runtime scoring once it passes. The common-emulator runtime benchmark remains pending.


## 38. Native Kotlin Android reference PoC — 2026-10-24

The new native Android reference uses Kotlin 2.1.20, Android Gradle Plugin 8.10.1, compile/target SDK 36, and a custom Canvas renderer (candles + volume), horizontal panning, zoom buttons, accessible labels, and a text table. It consumes the exact canonical synthetic OHLCV fixture and has no market-data connection or third-party chart library. Build evidence: [run 40064396892](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40064396892), artifact ID 12548796271, report `docs/architecture/evidence/issue-9-kotlin-android-build-40064396892.md`.

On Ubuntu 24.04 / AMD EPYC 9V45 / 4 vCPU / 16.77 GB / Temurin JDK 17.0.20.1, clean Debug builds took 22.84 / 12.13 / 11.98 s, incremental Debug 5.74 s, Release 25.92 s; Debug APK 839,249 bytes and Release APK 638,316 bytes. These are standalone measurements on a third CPU model, so they must not be ranked against the separate Flutter/RN times. The same-runner shared-emulator workflow is being extended to install all three apps, verify visible title and fixture content, and measure launch wait plus PSS/RSS. Gradle warned that `kotlinOptions` is deprecated and Gradle 10 compatibility needs review; the Release APK uses debug-key signing only for emulator installation.

The app runtime dependency graph contains Kotlin stdlib 2.1.20 and JetBrains annotations 13.0; the build plugin graph is preserved separately and still requires build-tool licence review. This Kotlin PoC is Android-only; it does not remove the need for a separate iOS implementation if Kotlin Multiplatform/native is selected.
