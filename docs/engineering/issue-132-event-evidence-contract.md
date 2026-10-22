# Contrato de evidencia de noticias y eventos externos — Issue #132

- **Estado:** contrato offline integrado; esta rama añade un adaptador SEC RSS/artículo, probado con respuestas sintéticas y deshabilitado hasta aprobar términos.
- **Issue:** [#132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132)
- **Dependencia de producto:** [#128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128)
- **Implementación:** `scripts/market_selection/external_event_evidence.py`
- **Pruebas:** `tests/market_selection/test_external_event_evidence.py`
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

Limitación: las URL sindicadas o redirigidas diferentes pueden representar la misma noticia y no se deduplican semánticamente en esta fase. La deduplicación entre fuentes requiere conservar ambos registros y una capa de agrupación con evidencia.

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

## 7. Pruebas implementadas

Los once tests cubren normalización de tiempo, rechazo de entidades identificadas solo por ticker, timestamps sin zona horaria, captura anterior a publicación, duplicados con conflicto, captura posterior al corte histórico, coincidencia temporal sin afirmación causal, evento fuera de ventana, ausencia de evidencia, activo no coincidente y preservación de registros de fuentes independientes.

**Estado de validación:** el contrato offline ya está en `main`; esta rama añade pruebas offline del adaptador y su gate. No se ha hecho captura real desde esta rama porque el registro de fuentes mantiene `TERMS_PENDING`. La integración con el informe `crypto-asset-research-report-v2` requiere pasar eventos promovidos explícitamente a `research_evidence_integration`; no se infiere entidad ni causalidad automáticamente. Issue #132 permanece abierto hasta completar revisión de fuente y validar una captura autorizada real.
