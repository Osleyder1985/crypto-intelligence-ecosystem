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

## Fuentes oficiales para la prueba de fallback multi-exchange

| Proveedor / dato | Fuente oficial | Qué respalda | Qué NO demuestra |
|---|---|---|---|
| OKX Spot: libro de órdenes | [API V5 — Order book](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-order-book) | Endpoint público de libros, instrumento, niveles y timestamp de generación | Acceso garantizado desde cada región ni liquidez ejecutable |
| Bybit Spot: libro de órdenes | [V5 — Get Orderbook](https://bybit-exchange.github.io/docs/v5/market/orderbook) | `GET /v5/market/orderbook`, categoría spot, símbolo, bids/asks y campos temporales/secuencia | Profundidad completa ni ausencia de restricciones regionales |
| Coinbase Exchange: libro de órdenes | [Exchange REST API — Get product book](https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductbook) | Snapshot público de libro por producto y niveles | Equivalencia de cotización con USDT ni acceso para todas las cuentas/regiones |
| Kraken Spot: profundidad | [Spot REST API — Depth](https://docs.kraken.com/api/docs/rest-api/get-order-book/) | Endpoint público de profundidad por par | Sincronización con los otros exchanges ni suficiencia de profundidad |

La prueba inicial captura BTC, ETH y SOL, pero usa cotización USDT en OKX/Bybit y USD en Coinbase Exchange/Kraken. Por tanto, los precios no deben compararse como si fueran el mismo par cotizado sin normalizar la moneda de cotización. El resultado `PASS` solo significa que la respuesta pública pasó validación estructural básica; no aprueba comisiones, frescura bajo una política autorizada, slippage ni elegibilidad regional.

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


## Diagnóstico de acceso regional: Binance.com y Binance.US

La prueba automatizada `capture_binance_regional_rest_diagnostic.py` consulta dos servicios oficiales distintos:
- Binance.com, endpoint público de datos de mercado `https://data-api.binance.vision`, documentado en [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md).
- Binance.US, API oficial `https://api.binance.us`, documentada en [Binance.US API documentation](https://github.com/binance-us/binance-us-api-docs).

Para cada servicio registra hora del servidor, metadatos de mercado y snapshots para BTC/ETH/SOL, solicitando solo los pares BTCUSDT, ETHUSDT y SOLUSDT para evitar descargar el catálogo completo de símbolos. Conserva el estado HTTP, cuerpo de error cuando se pueda leer, SHA-256, respuesta original codificada y resumen parseado. Un símbolo inexistente se registra como `NOT_AVAILABLE`, no como captura correcta.

Esta comparación distingue accesibilidad REST pública de acceso WebSocket y elegibilidad de trading. No atribuye automáticamente un HTTP 451 a una causa concreta ni intenta eludir restricciones regionales. La ejecución debe revisarse como evidencia puntual y no como aprobación de Binance para operar.
