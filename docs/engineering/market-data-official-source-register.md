# Registro de fuentes oficiales para selección de mercados spot

- **Estado:** registro inicial de fuentes y límites semánticos; no constituye una evaluación de mercados ni una aprobación de política.
- **Objetivo:** permitir rastrear cada observación hasta documentación oficial del proveedor y dejar claro qué puede y qué no puede concluirse de cada endpoint.
- **Regla:** revisar los documentos antes de cada cambio de adaptador; registrar fecha de consulta UTC, URL, versión/commit si está disponible, campos usados, hash del payload y limitaciones. Una URL oficial no prueba que una respuesta concreta se haya capturado.

## Fuentes integradas actualmente

| Proveedor / dato | Fuente oficial | Qué respalda | Qué NO demuestra |
|---|---|---|---|
| Binance Spot: reglas y metadatos del símbolo | [REST API — Exchange information](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#exchange-information) | Esquema documentado de `GET /api/v3/exchangeInfo`, identidad del símbolo y metadatos/reglas devueltos | Acceso de la cuenta/región, liquidez suficiente, frescura del libro o elegibilidad de inversión |
| Binance Spot: snapshot de profundidad | [REST API — Order book](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#order-book) | Esquema de `GET /api/v3/depth`, niveles bid/ask y `lastUpdateId` | `lastUpdateId` no es un timestamp de evento; el snapshot limitado no representa necesariamente todo el libro ni prueba frescura temporal |
| Binance: API pública de datos de mercado | [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market-data-only.md) | Endpoints públicos de datos de mercado que no requieren API key | Disponibilidad permanente, latencia end-to-end o ausencia de límites |
| Binance Spot: filtros de símbolos | [Filters](https://github.com/binance/binance-spot-api-docs/blob/master/filters.md) | Semántica de filtros del mercado, que debe consultarse para restricciones de cantidad/precio/notional aplicables | Tamaño de orden de referencia para el producto; el filtro del exchange no sustituye el requisito de uso |
| Binance Spot: comisiones | [Commission FAQ](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md) | Métodos oficiales para consultar/calcular comisiones y factores que pueden afectar el resultado | Una tasa universal fija aplicable a toda cuenta, símbolo, orden o promoción |
| Pionex: listado de símbolos | [Common Symbols API](https://www.pionex.com/docs/api-docs/trade-api/common) | `GET /api/v1/common/symbols`, parámetros de símbolo/tipo y campos documentados como timestamp, tipo, base/cotizada y habilitación | Acceso regional/de cuenta, liquidez, rentabilidad ni estado futuro del mercado |

## Semántica aplicada en el código

1. **Captura vs. calidad:** `capture_status=PASS` significa que la respuesta HTTP se recibió y se pudo parsear bajo el contrato de captura; no significa que la observación de mercado sea válida para una decisión económica.
2. **Hora de captura vs. hora de origen:** se registran por separado. No rellenar un timestamp de origen ausente con la hora local de captura.
3. **Binance REST depth:** `lastUpdateId` se trata como identificador de secuencia, no como hora de mercado. Sin evidencia temporal suficiente, `source_freshness=INDETERMINATE`.
4. **Pionex common symbols:** el campo `timestamp` del sobre se normaliza como `source_response_at_utc` después de validarse como entero en milisegundos; el estado `VALID`/`MISSING`/`INVALID` se registra explícitamente. No se copia a `source_event_at_utc`, porque es timestamp de respuesta y no timestamp de evento del libro. Si no está presente o no es interpretable, no se inventa.
5. **Comisiones:** sin respuesta oficial aplicable al símbolo/cuenta/tipo de operación y condiciones relevantes, `fees=INDETERMINATE`.
6. **Profundidad limitada:** registrar el límite solicitado y el número real de niveles; no extrapolar más allá de la profundidad observada.
7. **Tamaño de orden:** derivarlo del caso de uso documentado y contrastarlo con los filtros oficiales vigentes del símbolo. No utilizar valores predeterminados escogidos para forzar `PASS`.
8. **Estados separados:** disponibilidad, integridad de captura, frescura, liquidez, slippage, comisiones y riesgo del activo no se deben colapsar en una sola puntuación.

## Fuentes todavía no integradas al prototipo

El Issue #7 enumera OKX, Bybit, MEXC, Gate y Bitget como exchanges comparativos. Su inclusión requiere un registro separado por proveedor que cite la documentación oficial vigente de endpoints spot, semántica de datos, filtros, tarifas, límites, timestamps y restricciones geográficas aplicables. No se les atribuyen endpoints ni cobertura en este documento hasta verificar sus fuentes oficiales y añadir pruebas de contrato.

## Evidencia requerida para una evaluación reproducible

Por ejecución:
- fecha/hora UTC de consulta y captura;
- URL exacta, método y parámetros no secretos;
- estado HTTP y error si lo hubiera;
- bytes originales conservados cuando las condiciones aplicables lo permitan, SHA-256 y tamaño;
- versión de parser/código y esquema;
- campos de origen, hora de captura y semántica de cada timestamp;
- resultado de validación por dimensión y motivo de `PASS`, `FAIL`, `INDETERMINATE` o `NOT_RUN`;
- artefacto y configuración versionados;
- limitaciones y fuentes oficiales consultadas.

Una captura pública puntual no prueba estabilidad de volumen, profundidad histórica, calidad futura de API, disponibilidad regional ni rentabilidad. Esas afirmaciones requieren evidencia adicional diseñada para la pregunta concreta.
