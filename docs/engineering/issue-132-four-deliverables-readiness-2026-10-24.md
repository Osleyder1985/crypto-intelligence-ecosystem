# Issue #132 — Expediente de cierre de cuatro entregables

- Fecha de corte: 2026-10-24.
- Estado: **abierto; no declarar completado** mientras no existan captura real autorizada, integración E2E ejecutada y manifiesto de backfill real reproducible.
- Alcance: evidencia de eventos externos para investigación cripto. Este documento registra resultados comprobables y bloqueos; no convierte una política general en permiso para almacenar contenido no cubierto.

## Entregable 1 — Revisión de fuente y modalidad

**Resultado comprobado:** el workflow [captura de políticas](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40049674222) publicó el artefacto `issue-132-source-policy-snapshots`, con cinco respuestas HTTP 200 preservadas en `issue-132-source-policy-snapshots.zip`. El artefacto es evidencia de políticas, no captura de artículos ni autorización de uso.

**Decisión operativa:** ninguna de las seis entradas puede pasar a `APPROVED` por inferencia. La política de Federal Reserve permite copiar y distribuir información del Board salvo indicación contraria, con atribución; no resuelve automáticamente la captura y persistencia de HTML íntegro, material de terceros, adjuntos, condiciones del endpoint, ni duración de retención. La entrada CFTC RSS debe permanecer sin sondeos mientras siga vigente el aviso oficial de deshabilitación.

**Acción necesaria antes de activar cada fuente:** preservar la política específica con bytes íntegros y SHA-256 coincidente; documentar endpoint y alcance exactos, User-Agent, límite agregado, redirecciones, campos almacenados, atribución, exclusión de terceros y duración/regla de eliminación. No reutilizar la aprobación de RSS para el archivo HTML ni viceversa.

## Entregable 2 — Captura histórica real

**Estado: pendiente.** No se ha acreditado una captura de artículo ejecutada por `capture_public_event_archive.py` con autorización válida. La página histórica de Federal Reserve del 24 de septiembre de 2026 es un candidato de investigación, no evidencia de que el repositorio lo haya capturado. No se debe saltar el control fail-closed para generar un artefacto artificialmente válido.

La captura que permita cerrar este punto debe preservar índice y artículo por separado, URL final, hora UTC de captura, código HTTP, bytes completos sin límite local arbitrario, hash SHA-256 y referencia al expediente de autorización que permitió la solicitud.

## Entregable 3 — Integración end-to-end

**Implementación existente, ejecución real pendiente.** Los contratos de evento, resolución de entidad, asociación temporal, promoción de candidato e integración de evidencia están implementados y tienen pruebas offline. Las pruebas sintéticas no prueban una integración con un artículo histórico real.

La prueba de cierre debe ejecutar, con artefactos encadenados: índice → selección verificable del candidato → artículo preservado → resolución con identificador estable del activo → evaluación temporal contra un episodio real → informe integrado. La salida debe diferenciar hecho verificado, asociación temporal, hipótesis, causalidad respaldada y causa no identificada; no puede inferir activo solo por ticker ni declarar causalidad por proximidad.

## Entregable 4 — Backfill y manifiesto reproducible

**Herramienta disponible; ejecución real pendiente.** La CLI de cobertura puede emitir manifiestos por partición/página y enumerar ausencias dentro del alcance declarado. Aún no hay evidencia de un backfill real que demuestre la captura histórica y la cobertura del corpus seleccionado.

Para cerrar, el manifiesto debe registrar `source_id`, `scope_id`, definición del alcance, particiones esperadas, páginas esperadas/capturadas/ausentes, referencias a artefactos y hashes, timestamps UTC, errores y estado `COMPLETE_FOR_DECLARED_SCOPE` solo si se satisface íntegramente ese alcance. Nunca declarar exhaustividad global a partir de una página o feed actual.

## CI y cambio de cobertura

El PR [#292](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/292) corrige el filtro `push.paths` para ejecutar las pruebas cuando cambie `capture_public_event_feed.py`. Su workflow de pruebas terminó en éxito: [run #177](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40050655862). También finalizaron en éxito los workflows consultados de trazabilidad y gobernanza en el mismo commit. El estado combinado de commits no expone checks de estado tradicionales; esto no equivale por sí solo a una verificación exhaustiva de todas las reglas requeridas de protección de rama. No se declara el PR fusionado.

## Condición de cierre

Issue #132 permanece abierto hasta adjuntar evidencia reproducible de los cuatro entregables. Si la autorización de una modalidad sigue sin estar sustentada, debe informarse como bloqueada y no sustituirse por fixtures sintéticos, contenido copiado manualmente ni una excepción al control de autorización.
