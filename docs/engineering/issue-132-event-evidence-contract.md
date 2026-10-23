# Contrato de evidencia de noticias y eventos externos — Issue #132

- **Estado:** contrato offline integrado; esta rama añade un adaptador SEC RSS/artículo, probado con respuestas sintéticas y deshabilitado hasta aprobar términos.
- **Issue:** [#132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132)
- **Dependencia de producto:** [#128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128)
- **Implementación:** `scripts/market_selection/external_event_evidence.py`, `scripts/market_selection/event_source_registry.py`, `scripts/market_selection/capture_sec_press_releases_rss.py`
- **Pruebas:** `tests/market_selection/test_external_event_evidence.py`, `tests/market_selection/test_sec_press_releases_rss.py`, `tests/market_selection/test_research_evidence_integration.py`
- **Contrato de entrada:** `crypto-external-event-record-v1`
- **Contrato de evaluación:** `crypto-event-evidence-assessment-v1`

## 1. Alcance y no-objetivos

El contrato de evento valida, normaliza y relaciona de forma conservadora registros externos. El contrato base es offline y no prueba causalidad. Esta rama añade un adaptador SEC RSS/artículo; por defecto la fuente sigue `TERMS_PENDING`, por lo que no descarga nada. El adaptador preserva el feed y artículos completos cuando la fuente esté aprobada, pero requiere revisión humana de entidad antes de promover un feed item a evento.

## 2. Campos obligatorios de cada evento

| Campo | Regla |
|---|---|
| `schema_version` | Debe ser `crypto-external-event-record-v1`. |
| `event_id` | Identificador estable del registro. |
| `title`, `event_type` | No vacíos; la clasificación de evento debe mantenerse explícita. |
| `source.source_type` | Uno de `PRIMARY_OFFICIAL`, `REGULATORY`, `SECONDARY_MEDIA`, `AGGREGATOR`, `OTHER`. |
| `source.url`, `source.publisher` | URL HTTP(S) absoluta y editor/emisor identificable. |
| `published_at` | Hora de publicación ISO-8601 con zona/offset explícito. |
| `captured_at` | Hora real de captura ISO-8601 con zona/offset explícito; no debe ser anterior a la publicación declarada. |
| `entities` | Al menos un identificador estable: `coingecko_id`, `chain_contract`, `exchange_asset_id` o `project_id`. |
| `evidence` | Una o más referencias URL con la afirmación específica que respaldan. |
| `capture_method` | Procedencia de la captura (por ejemplo, nombre/versionado del adaptador o fixture). |
| `content_sha256` | Opcional; si existe, debe ser un SHA-256 hexadecimal de 64 caracteres. |

No se acepta la resolución de entidad basada solo en un ticker: los símbolos se reutilizan entre activos y redes. Para tokens, se debe conservar la red y la dirección de contrato cuando proceda; los identificadores canónicos externos deben resolverse contra un catálogo versionado. Los IDs de ejemplo en pruebas no son una fuente real.

## 3. Semántica temporal y prevención de look-ahead

- `published_at` indica la hora de publicación declarada por la fuente.
- `captured_at` registra cuándo el sistema obtuvo la evidencia. **No se deben reconstruir capturas históricas con una captura actual ni asumir que un artículo era conocido por el sistema solo porque su fecha de publicación sea antigua.**
- Una evaluación histórica con corte `evaluation_as_of` solo puede usar un evento si tanto publicación como captura son anteriores o iguales al corte.
- Si la hora de captura no existe en la fuente original, el registro no puede considerarse apto para backtesting sin evidencia independiente equivalente. No se debe rellenar con la hora de publicación.
- Todos los tiempos se normalizan a UTC, pero el valor original debe preservarse en el adaptador/artefacto de captura cuando esté disponible.
- El módulo compara la publicación con una ventana de movimiento declarada. No selecciona ni inventa ventanas de evento.

## 4. Deduplicación y conflictos

La deduplicación prioriza el ID de artículo del proveedor, cuando existe; de lo contrario, usa URL canónica (fragmento eliminado, host normalizado y barra final eliminada). No fusiona por similitud semántica de titulares. Si una misma identidad canónica tiene titulares o entidades discrepantes, el conflicto queda explícito como `CONFLICT_REQUIRES_REVIEW`, en vez de resolverlo silenciosamente.

Limitación: las URL sindicadas o redirigidas diferentes pueden representar la misma noticia y no se deduplican semánticamente en esta fase. La deduplicación entre fuentes requiere conservar ambos registros y una capa de agrupación con evidencia. Una URL canónica repetida también se marca `CONFLICT_REQUIRES_REVIEW` si cambian los campos de afirmación (`title`, `event_type`, entidades, `published_at`, referencias de evidencia) o si ambos registros incluyen hashes de contenido y estos difieren. Si uno de los hashes falta, el sistema no infiere que el contenido sea idéntico; esa ausencia queda como limitación de evidencia.

## 5. Niveles de evidencia y causalidad

La evaluación requiere que el activo objetivo se suministre con un identificador estable y que coincida exactamente con uno de los identificadores del evento. Si no coincide, el estado es `ENTITY_NOT_MATCHED`. La evaluación temporal puede producir `TEMPORALLY_ELIGIBLE`, `NOT_AVAILABLE_AS_OF` o `OUTSIDE_MOVEMENT_WINDOW`. Una coincidencia dentro de la ventana recibe únicamente `TEMPORAL_ASSOCIATION`; la salida fija `causality_claimed=false`.

La taxonomía global reservada es:

- `FACT_VERIFIED`: hecho sustentado por evidencia primaria verificable.
- `TEMPORAL_ASSOCIATION`: coincidencia temporal; no implica que el evento causara el movimiento.
- `PLAUSIBLE_HYPOTHESIS`: mecanismo plausible con evidencia incompleta y alternativas explícitas.
- `SUPPORTED_CAUSALITY`: reservado para una evaluación más estricta que compare alternativas y evidencias; esta entrega no lo asigna.
- `CAUSE_UNIDENTIFIED`: no hay base suficiente para una atribución.

La mera precedencia temporal, una nota de prensa o la correlación de precios nunca bastan por sí solas para `SUPPORTED_CAUSALITY`. Deben registrarse explicaciones alternativas, cobertura de fuentes y grado de incertidumbre.

## 6. Procedencia, licencias y límites

- Las URLs y afirmaciones de evidencia se enlazan desde el resultado.
- `content_sha256` representa el contenido original solo si el adaptador lo calcula sobre los bytes originales preservados. El hash de JSON canónico del módulo es distinto y no debe presentarse como hash del documento fuente.
- `license_notes` puede indicar `UNKNOWN`; esto significa que los términos no se han verificado, no que la reutilización esté autorizada.
- Las fuentes primarias son preferibles para confirmar anuncios propios, listados, delistados, actualizaciones e incidentes. Las fuentes regulatorias son preferibles para actos regulatorios. La prensa secundaria sirve para contexto y corroboración, no sustituye una fuente primaria cuando esta exista.
- Deben documentarse límites de acceso, licencias, condiciones de uso, retención, robots/API y cobertura antes de activar un conector en producción.
- La ausencia de resultados solo es interpretable junto con cobertura, errores, rango temporal y fuentes consultadas. Cero registros no demuestra que no ocurrió ningún evento.

## 7. Registry de fuentes y gate antes de integración

- `event_source_registry.py` mantiene el feed SEC en `TERMS_PENDING`. No se hace red hasta que los bytes de los términos y su SHA-256 coincidan, se complete la revisión y se declaren los casos de uso permitidos.
- El adaptador exige autorización independiente para `internal_analysis` y `persistent_storage`, un User-Agent proporcionado por el operador y un timeout explícito antes de abrir la conexión. El código no certifica que SEC considere clasificado el User-Agent.
- `capture_sec_press_releases_rss.py` preserva la respuesta completa hasta EOF, sin límite local de tamaño; incluye bytes base64, tamaño, SHA-256, headers y errores HTTP. Las respuestas mayores de 5 MiB y los errores de lectura parcial tienen pruebas offline.
- Los titulares no crean eventos automáticamente. La promoción requiere captura completa del artículo, mapeo de entidades con IDs estables y evidencia de mapeo preservada con hash. El registro conserva el gate del proveedor y el hash del registry.
- `research_evidence_integration.enrich_research_report` vuelve a validar cada evento: autorización para análisis y almacenamiento, fuente registrada/aprobada, hash de registry actual, host HTTPS allowlisted, editor y tipo de fuente coincidentes. Verifica base64, tamaño y SHA-256 de las capturas RSS/artículo, vuelve a parsear el RSS y comprueba que título, URL y publicación coincidan, además de verificar la evidencia del mapeo de entidades. Eventos sin estos datos quedan bloqueados.
- La evaluación temporal mantiene `causality_claimed=false`; la captura y el enlace temporal no prueban causalidad.

## 8. Pruebas implementadas

Los once tests cubren normalización de tiempo, rechazo de entidades identificadas solo por ticker, timestamps sin zona horaria, captura anterior a publicación, duplicados con conflicto, captura posterior al corte histórico, coincidencia temporal sin afirmación causal, evento fuera de ventana, ausencia de evidencia, activo no coincidente y preservación de registros de fuentes independientes.

**Estado de validación:** el contrato offline ya está en `main`; esta rama añade un adaptador SEC y gates de fuente/uso probados con respuestas sintéticas. No se ha hecho captura real porque el registro mantiene `TERMS_PENDING`. La integración con `crypto-asset-research-report-v2` acepta únicamente eventos promovidos explícitamente y vuelve a verificar autorización y registry. No se infiere entidad ni causalidad automáticamente. Issue #132 permanece abierto hasta completar revisión de fuente y validar una captura autorizada real.

## 8. Cobertura de captura por fuente en el informe

La integración admite un artefacto opcional \`event_source_coverage\` con esquema \`crypto-event-source-coverage-v1\`. Se pasa a \`enrich_research_report(..., event_source_coverage=...)\` o mediante \`--event-source-coverage <archivo.json>\`. Cada registro corresponde a una captura de una fuente registrada y conserva \`source_id\`, \`capture_status\`, \`captured_at\`, \`network_request_made\`, \`capture_truncated\`, \`feed_item_count\`, \`coverage_scope\` y \`errors\`; cuando esté disponible, también incluye \`source_registry_entry_sha256\` y \`raw_response_sha256\`.

La integración deriva estados explícitos:

- \`NOT_PROVIDED\`: no se entregó ningún registro de cobertura; no significa que la búsqueda no encontrara noticias.
- \`BLOCKED_BY_SOURCE_POLICY\`: la fuente bloqueó la captura antes de hacer red.
- \`UNAVAILABLE\`: la solicitud falló por red.
- \`PARTIAL_OR_FAILED\`: respuesta parcial, HTTP no satisfactorio, error de parseo o truncamiento.
- \`CAPTURED_NO_ITEMS_IN_RETURNED_FEED\`: captura correcta con cero entradas en el feed devuelto. Esto **no** significa ausencia de catalizadores en el archivo histórico o en otras fuentes.
- \`CAPTURED_WITH_ITEMS\`: captura correcta con entradas; cada candidato aún necesita resolver entidad y verificar el hecho.
- \`NOT_AVAILABLE_AS_OF\`: la captura ocurrió después del corte de evaluación.
- \`STALE_SOURCE_REGISTRY\`: el hash del registro usado en la captura no coincide con el registro actual.
- \`INCONSISTENT_CAPTURE_POLICY\`: los metadatos afirman éxito incompatible con la autorización/solicitud registrada.

La cobertura se limita al alcance declarado por cada proveedor; un RSS actual no es un archivo histórico completo. Los estados de cobertura no elevan un titular a evento verificado ni demuestran causalidad. Si no se suministra el artefacto de cobertura, el informe declara explícitamente \`NOT_PROVIDED\` en vez de inferir una búsqueda negativa.

## 9. Captura de artículo HTML y promoción de eventos RSS/Atom

El capturador genérico ahora ofrece \`capture_public_event_article\` y modo CLI con \`--feed-capture <feed.json> --article-candidate-id <candidate_id>\`. La captura de artículo reutiliza la autorización del proveedor y el estado del registro, verifica la integridad de los bytes del feed y que el candidato exista en el feed preservado, valida la URL HTTPS contra la allowlist y sigue redirecciones solo si el destino sigue dentro de los hosts HTTPS permitidos.

El cuerpo del artículo se lee hasta EOF, se conserva en base64 y se identifica con SHA-256 y tamaño exacto; no se aplica un límite local arbitrario de bytes. Las capturas incompletas, los errores HTTP/red y destinos fuera de la allowlist no se pueden promover. La promoción de un candidato genérico requiere ahora una captura de artículo completa, autorización para \`internal_analysis\` y \`persistent_storage\`, y una resolución de entidad revisada con ID estable y evidencia hasheada.

La integración del informe verifica de nuevo los bytes del feed y del artículo, la relación entre el candidato y la URL, el hash del cuerpo, los timestamps y el registro de fuente. El artículo capturado respalda el contenido de la afirmación; la revisión humana sigue siendo responsable de decidir si el hecho está correctamente interpretado y si se relaciona con el activo. Esto no demuestra causalidad con el movimiento de precio.

Ejemplo de captura de feed:

\`\`\`bash
python -m scripts.market_selection.capture_public_event_feed --source-id <source_id> --provider-authorization-registry <authorization.json> --user-agent "<reviewed User-Agent>" --output <feed-capture.json>
\`\`\`

Después de revisar el candidato y confirmar que la fuente está autorizada:

\`\`\`bash
python -m scripts.market_selection.capture_public_event_feed --source-id <source_id> --provider-authorization-registry <authorization.json> --user-agent "<reviewed User-Agent>" --feed-capture <feed-capture.json> --article-candidate-id <candidate_id> --output <article-capture.json>
\`\`\`

Ambos comandos deben devolver un bloqueo sin tráfico de red mientras la fuente o los usos requeridos estén pendientes. Los ejemplos son plantillas; no se ejecutaron solicitudes reales al añadir esta funcionalidad.

## 10. Ventanas temporales antes y después del movimiento

La integración acepta en cada elemento de \`events\` los parámetros opcionales \`pre_movement_window_minutes\` y \`post_movement_window_minutes\`. Ambos deben ser enteros no negativos (los booleanos no son enteros válidos para este contrato) y tienen valor predeterminado \`0\` para conservar el comportamiento anterior.

- La ventana previa permite investigar eventos publicados antes del inicio del tramo técnico.
- La ventana posterior permite incluir eventos publicados después del extremo técnico observado, cuando la disponibilidad temporal y el corte de evaluación lo permiten.
- La evaluación registra la ventana de asociación efectiva y los dos parámetros utilizados.
- Una publicación dentro de la ventana ampliada solo se clasifica como \`TEMPORAL_ASSOCIATION\`; nunca como prueba de causalidad.
- Los valores deben fijarse en una metodología versionada antes de evaluar los resultados y someterse a análisis de sensibilidad. No deben ajustarse retrospectivamente para hacer coincidir una noticia con un movimiento.
