# Diccionario y registro de fuentes fundamentales/on-chain — Issue #134

- **Estado actualizado:** contrato/diccionario y enforcement runtime del informe integrados en `main`; fuente fundamental registrada limitada a DefiLlama offline; fuentes reales autorizadas y captura en vivo pendientes.
- **Issue:** [#134](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/134)
- **Dependencia:** [#128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) y [#130](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/130)
- **Código:** `scripts/market_selection/fundamental_onchain_contract.py` (incluye normalizador offline de TVL histórico de DefiLlama)
- **Tests:** `tests/market_selection/test_fundamental_onchain_contract.py`
- **Contratos:** `crypto-fundamental-metric-catalog-v1`, `crypto-fundamental-observation-v1`, `crypto-fundamental-assessment-v1`
- **Consulta documental:** 2026-10-22

## 1. Principios de diseño

1. Cada métrica tiene definición, unidad, categorías donde es aplicable y caveat metodológico.
2. `NOT_APPLICABLE`, `NOT_AVAILABLE`, `INACCESSIBLE`, `STALE`, `PARTIAL`, `PROVIDER_ERROR` y `CONFLICT` son estados distintos. Un dato ausente nunca se convierte en cero.
3. Cada observación conserva identidad estable del activo, fuente, URL, URL metodológica cuando exista, estado de términos, hora de publicación, hora del dato y hora de captura.
4. El corte histórico exige publicación, observación y captura no posteriores a `evaluation_as_of`. Una captura actual no demuestra disponibilidad histórica.
5. Valores discrepantes entre fuentes quedan como `CONFLICT`; no se promedian ni se selecciona un proveedor automáticamente.
6. El contrato no asigna puntuación de inversión ni ranking. La decisión permanece `INDETERMINATE` hasta metodología, cobertura y validación apropiadas.

## 2. Categorías de activos iniciales

| Categoría | Métricas especialmente relevantes | Precaución |
|---|---|---|
| `native_l1` | emisión/oferta, actividad, comisiones, concentración de validadores, seguridad | Los datos de consenso y ejecución pueden ser distintos; definir cadena y regla de conteo |
| `smart_contract_token` | oferta, contrato, distribución, actividad de la red anfitriona | No atribuir actividad de toda la cadena al token sin una metodología de atribución |
| `stablecoin` | oferta, reservas/atestaciones, redenciones, concentración, incidentes | Distinguir colateral, pasivos, derechos de redención y fecha de atestación |
| `defi_protocol_token` | oferta, desbloqueos, concentración, fees, revenue, TVL del protocolo | Fees no equivalen a revenue ni a captura de valor del token |
| `exchange_token` | oferta, desbloqueos, concentración, derechos/utilidad y riesgos del emisor | No asumir derechos económicos que no estén documentados |
| `liquid_staking` | exchange rate, concentración de operadores, seguridad del protocolo | El precio relativo al activo subyacente y los riesgos de desvinculación importan |
| `meme` | oferta, distribución, concentración, liquidez y seguridad del contrato | Actividad social no demuestra demanda sostenible ni utilidad |
| `oracle` | oferta, distribución, uso de oráculos, dependencias y seguridad | Separar uso del servicio y demanda económica del token |
| `gaming` | oferta/desbloqueos, uso de juego, actividad y seguridad | Separar usuarios, bots, transacciones y economía in-game |
| `rwa` | oferta, derechos, reservas/colateral, emisor, jurisdicción y redención | Requiere documentación jurídica y financiera específica del activo |
| `privacy` / `other` | selección por proyecto y documentación | No asumir métricas universales; el catálogo debe ampliarse con justificación |

El catálogo del código es un punto de partida versionado, no una afirmación de que todas las métricas aplican a todo proyecto. Las categorías `privacy` y `other` están reservadas para expansión; sus métricas necesitan revisión explícita.

## 3. Diccionario inicial de métricas

| ID | Unidad | Aplicabilidad | Definición / control clave |
|---|---|---|---|
| `supply.max` | token | Condicional | Máximo programado; puede no existir un máximo finito |
| `supply.circulating` | token | General | Oferta circulante con metodología de proveedor preservada |
| `supply.unlock_schedule` | token | Condicional | Liberaciones futuras con fechas y distinción entre estimadas/confirmadas |
| `distribution.holder_concentration` | fracción | Condicional | Universo de holders, exclusiones y bloque de snapshot explícitos |
| `network.active_addresses` | recuento | Condicional | Regla de actividad y ventana definidas; direcciones no equivalen a personas |
| `network.transaction_count` | recuento | Condicional | Reglas de inclusión para transacciones fallidas, internas o rollups |
| `network.fees_paid` | nativo/USD | Condicional | Fees pagadas; no confundir con revenue |
| `protocol.tvl` | USD | Condicional | Activos en contratos de un protocolo bajo metodología declarada |
| `protocol.fees` | USD | Condicional | Comisiones pagadas por usuarios en un intervalo |
| `protocol.revenue` | USD | Condicional | Parte retenida por el protocolo; no sustituir por fees brutas |
| `security.audit_status` | categórica | General | Auditor, alcance, fecha, findings y componentes revisados |
| `security.incident_history` | eventos | General | Incidentes documentados; ausencia de registros no prueba cero incidentes |
| `stablecoin.reserve_attestation` | categórica/USD | Solo stablecoin | Emisor, fecha as-of, composición, alcance y atestador |
| `staking.validator_concentration` | fracción | L1 / liquid staking | Atribución de operadores y snapshot explícitos |
| `liquid_staking.exchange_rate` | ratio | Solo liquid staking | Ratio del token líquido respecto al activo subyacente en bloque/tiempo dado |

## 4. Registro de fuentes candidatas

El registro distingue fuente primaria, agregador/indexador y proveedor de métricas. La presencia de una API pública no garantiza que sus datos tengan la definición, cobertura, licencia o disponibilidad histórica requeridas.

| Fuente | Datos potenciales | Evidencia documental / definición | Límites y decisión |
|---|---|---|---|
| [CoinGecko API](https://docs.coingecko.com/reference/introduction) | Precio/market cap, metadatos y supply | La documentación describe datos de monedas/tokens y suministro; su metodología distingue max, total y circulating supply | Candidata para datos de mercado/supply con atribución, cuotas y plan documentados. La definición puede cambiar; versionar metodología y guardar capturas. |
| [CoinGecko — metodología de supply](https://support.coingecko.com/articles/6758974979-coingecko-supply-methodology) | Max/total/circulating supply | Define categorías de oferta y reconoce diferencias como supply infinito | Fuente metodológica del proveedor, no fuente on-chain primaria para todos los activos |
| [DefiLlama API docs](https://api-docs.defillama.com/) | TVL, fees, revenue y series de protocolo | Documenta endpoints de API y condiciones de acceso; existe una capa gratuita y endpoints de plan API | Candidata para métricas de protocolo; comprobar términos, endpoint/plan, metodología y cambios de endpoint. No asumir que TVL equivale a valor del token. |
| [DefiLlama data definitions](https://defillama.com/data-definitions) | Definiciones de TVL, fees y revenue | Distingue fees totales pagadas por usuarios de revenue retenido por el protocolo | Mantener los conceptos separados y conservar fecha de consulta/metodología |
| [mempool.space REST API](https://mempool.space/docs/api/rest) | Bloques, transacciones, mempool, fees, hashrate y dificultad de Bitcoin | La documentación enumera endpoints, campos y ventanas para métricas de red | Candidata para Bitcoin; validar cuotas, cobertura histórica, precisión temporal y condiciones de uso antes de producción |
| [ethereum.org — Data and analytics](https://ethereum.org/developers/docs/data-and-analytics) | Datos de ejecución/consenso y vías de indexación | Documentación del ecosistema explica exploradores, APIs e indexadores | Guía de fuentes y arquitectura; no es un proveedor de datos único. Para cada chain/endpoint, documentar términos y método |
| RPC/nodo propio de cada red | Saldos, transferencias, bloques, eventos y estado on-chain | Evidencia directamente verificable desde el protocolo, según reglas de consenso y nodo | Mayor control y verificabilidad, pero exige infraestructura, reorg handling, finality, backfill y validación |
| Contratos oficiales / documentación del proyecto | Emisión, vesting, gobernanza, derechos del token | Fuente primaria para el código/documentación publicados por el proyecto | No es verificación independiente; contrastar con contrato desplegado, eventos y estado actual |
| Informes de auditoría y postmortems | Seguridad e incidentes | Fuente primaria del auditor/equipo respecto del informe emitido; corroborar alcance y fecha | Un audit no prueba ausencia de vulnerabilidades; preservar PDF/hash y componentes auditados |

### Condiciones de aprobación de fuente

Antes de un adaptador, registrar: `source_id`, propietario, URLs y documentación, versión del endpoint, método permitido, plan/coste/cuotas, términos/licencia y atribución, cobertura histórica, granularidad, semántica de timestamps, retrasos, paginación, límites, retención, tasa de error y fecha de revisión. Estados permitidos recomendados: `PROPOSED`, `TERMS_PENDING`, `APPROVED`, `SUSPENDED`, `RETIRED`.

## 5. Contrato de observación

Cada observación usa `crypto-fundamental-observation-v1` y contiene:

- `asset.category` y `asset.stable_id`: identidad explícita y no ambigua; para token, incluir chain/network y contract address cuando aplique.
- `metric_id`, `status`, `value`, `unit`: métrica catalogada; valores ausentes usan `null` y un estado explícito, nunca cero.
- `published_at`, `observed_at`, `captured_at`: timestamps ISO-8601 con offset explícito.
- `source.source_id`, `source.source_type`, `source.url`, `source.methodology_url`, `source.terms_status`.
- `period_start`, `period_end`, `block_height` cuando correspondan, además de notas de calidad y metadata específica del adaptador.

## 6. Limitaciones pendientes

La base inicial implementa el catálogo versionado, validación offline y pruebas sintéticas. Los PR [#161](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/161), [#162](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/162) y [#163](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/163) ya reforzaron el flujo integrado: los conflictos explícitos prevalecen sobre observaciones válidas aisladas; cada observación fundamental pasa por la puerta de autorización para `internal_analysis` y `persistent_storage`; y `source_id` debe vincularse al `provider_id` y al host/ruta HTTPS registrados. Las evaluaciones de uso quedan incluidas en el informe E2E.

**Esto no equivale a una fuente real autorizada ni a una integración en vivo.** El único binding fundamental del runtime es `defillama-free-api` → `defillama_api` → `api.llama.fi/protocol/...`; DefiLlama sigue bloqueada hasta registrar autorización escrita auténtica y aplicable. Las autorizaciones de los tests son fixtures sintéticas y no prueban derechos. El adaptador normaliza respuestas capturadas offline y requiere un vínculo token-protocolo aportado por el llamador; aún no obtiene por sí mismo evidencia independiente de ese vínculo ni crea capturas históricas reales.

Las métricas de concentración, desbloqueos, reservas/atestaciones, seguridad y auditorías todavía necesitan fuentes específicas y resolución de entidad por activo. El trabajo restante incluye fuentes reales autorizadas, captura reproducible, fixtures reales permitidas, cobertura/calidad por categoría, datos contradictorios, manejo de reorgs cuando aplique y verificación anti-look-ahead con timestamps de publicación/captura. La integración de observaciones en el informe E2E existe, pero la integración completa de #134 en el producto no se considera terminada mientras falten esas fuentes y validaciones.

Para cerrar #134 faltan adaptadores de fuentes autorizadas, capturas históricas reales reproducibles, manejo de reorgs y datos contradictorios de proveedores, controles de cobertura/calidad por categoría, validación de los vínculos activo-protocolo y pruebas anti-look-ahead con evidencia temporal verificable.


## Política explícita de frescura por métrica

La evaluación admite un mapa opcional `freshness_policy_seconds`, indexado por ID de métrica. Si se declara una edad máxima positiva, una observación `OBSERVED` más antigua que ese umbral se excluye del valor actual y se informa como `STALE`, con su ID conservado. Si coexisten observaciones antiguas y una observación vigente, se usa solo la vigente y se mantienen visibles las IDs obsoletas. La política y los IDs afectados quedan incluidos en la salida y en la cobertura.

No hay umbrales universales incorporados: el llamador debe definirlos de acuerdo con la cadencia y semántica de cada métrica. Sin una política explícita, el comportamiento anterior se conserva y no se deduce frescura solo por antigüedad.


### Uso en el informe integrado

El informe integrado expone la misma política mediante el argumento opcional `fundamental_freshness_policy_seconds`. En la CLI puede pasarse un archivo JSON con el mapa de `metric_id` a edad máxima en segundos mediante `--fundamental-freshness-policy`. El artefacto resultante conserva la política y las observaciones obsoletas; la decisión global continúa en `INDETERMINATE`.
