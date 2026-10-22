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
| Binance Spot: evidencia de comisión de cuenta por símbolo | [Commission FAQ — `GET /api/v3/account/commission`](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md) | Tasas actuales de la cuenta para el símbolo consultado y componentes `standard`, `tax`, `special` y descuento documentados; capturador opcional `scripts/market_selection/capture_binance_account_commission_evidence.py` | No demuestra tarifa de Pionex, vigencia futura, ni coste total sin lado/tipo de orden, tamaño, profundidad y contexto de uso |
| Binance Spot: profundidad de libro | [REST API — Order book](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#order-book) | `GET /api/v3/depth`, bids/asks y `lastUpdateId` | `lastUpdateId` es un ID de secuencia, no un timestamp de evento; snapshot limitado por `limit` |
| MEXC Spot: profundidad de libro | [Spot API — Order Book](https://mexcdevelop.github.io/apidocs/spot_v3_en/#order-book) | `GET /api/v3/depth`, bids/asks y `lastUpdateId` | El ID de actualización no es una hora de evento; profundidad limitada por `limit` |
| Gate Spot: libro de órdenes | [API v4 — Get market depth information](https://www.gate.com/docs/developers/apiv4/en/spot/) | `GET /api/v4/spot/order_book`, campos `current`, `update`, bids/asks; público sin autenticación | `current` y `update` tienen semánticas distintas; snapshot limitado y accesibilidad regional deben evaluarse |
| Bitget Spot: libro de órdenes | [Market Data — Get Order Book](https://www.bitget.com/docs/catalog/market/market-data) | `GET /api/v3/market/orderbook`, categoría `SPOT`, bids/asks y `ts` en milisegundos | No demuestra profundidad completa, disponibilidad regional ni tarifa aplicable |
| Pionex Spot: profundidad de libro | [Get Depth](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth) | `GET /api/v1/market/depth`, bids/asks y `updateTime` en ms; límite documentado 1–1000 | Snapshot puntual; no demuestra acceso regional/de cuenta ni suficiencia de liquidez |
| Pionex: listado de símbolos | [Common Symbols API](https://www.pionex.com/docs/api-docs/trade-api/common) | `GET /api/v1/common/symbols`, parámetros de símbolo/tipo y campos documentados como timestamp, tipo, base/cotizada y habilitación | Acceso regional/de cuenta, liquidez, rentabilidad ni estado futuro del mercado |
| Pionex Spot: tarifas públicas de trading | [Pionex Trading Fee](https://www.pionex.com/fees) | La página pública consultada muestra Spot maker 0,050 % y taker 0,050 % como tarifa publicada general | La página indica tarifas inferiores para VIP; no demuestra el nivel ni los descuentos efectivos de una cuenta concreta, ni el coste total de una orden |

> **Nota de procedencia:** la página pública de tarifas de Pionex es dinámica. En la consulta del 2026-10-21 mostraba Spot maker 0,050 % y taker 0,050 %, a la vez que anunciaba tarifas inferiores para cuentas VIP. Registrar URL, fecha/hora UTC y copia/hash de cada consulta. No tratar esa tarifa pública como aplicable a una cuenta concreta sin verificar el nivel y las condiciones de la cuenta.

## Captura de evidencia de comisiones por cuenta

El capturador opcional de Binance Spot documentado en [`binance-account-commission-evidence.md`](binance-account-commission-evidence.md) consulta `GET /api/v3/account/commission` con una solicitud firmada y no coloca órdenes. La prueba estructural offline no requiere credenciales. Una ejecución real necesita credenciales de lectura autorizadas y un entorno permitido; nunca deben guardarse en el repositorio ni en artefactos. Hasta que exista una respuesta real, archivada y aplicable al símbolo/cuenta objetivo, la dimensión de comisiones permanece `INDETERMINATE`. La captura de Binance no resuelve tarifas de Pionex.

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

## Fuentes oficiales de tickers de 24 h para Issue #7

| Proveedor | Fuente oficial | Campo usado como turnover cotizado | Límite |
|---|---|---|---|
| Binance Spot | [REST API — 24hr ticker](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#24hr-ticker-price-change-statistics) | `quoteVolume` | Ticker móvil de 24 h; no equivale a estabilidad histórica. |
| OKX Spot | [API V5 — Get ticker](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-tickers) | `volCcy24h` | Conservar unidad y semántica Spot; no confundir con `vol24h` base. |
| Bybit Spot | [V5 — Get Tickers](https://bybit-exchange.github.io/docs/v5/market/tickers) | `turnover24h` | Respuesta puede fallar por accesibilidad del entorno; no inferir cero. |
| MEXC Spot | [Spot API — 24hr Ticker](https://mexcdevelop.github.io/apidocs/spot_v3_en/) | `quoteVolume` | La documentación muestra que el campo puede ser `null`; ausencia no es cero. |
| Gate Spot | [API v4 — Spot tickers](https://www.gate.com/docs/developers/apiv4/en/spot/) | `quote_volume` | Ticker puntual; unidad y par deben permanecer asociados. |
| Bitget Spot | [Market Data — Get Tickers](https://www.bitget.com/docs/catalog/market/market-data) | `turnover24h` | Ticker puntual; no sustituye datos de velas o serie histórica. |
| Pionex Spot | [Get 24hr Ticker](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-24hr-ticker) | `amount` | Importe negociado de 24 h; conservar símbolo/cotización y campo bruto. |

El capturador conserva respuestas originales, hashes, timestamps y valores brutos. Una captura móvil de 24 h no prueba estabilidad en ventanas mayores. Para esa conclusión se requiere una serie de observaciones fechadas con cobertura, huecos y comparabilidad evaluados.

## Estado del prototipo de sondeo multi-exchange

El prototipo captura libros públicos Spot de Binance, OKX, Bybit, MEXC, Gate, Bitget y Pionex para BTC/USDT, ETH/USDT y SOL/USDT. La cobertura está respaldada por contratos de respuesta probados offline y preservación del payload original con SHA-256. Es evidencia técnica de sondeo, no la matriz final de selección de mercados del Issue #7.

Binance y MEXC REST depth no incluyen timestamp de evento en el esquema documentado; `lastUpdateId` no es una hora. Su frescura temporal queda indeterminada por este snapshot aislado. Los snapshots se consultan secuencialmente y no están sincronizados entre venues. Faltan volumen histórico/estabilidad, costes efectivos, disponibilidad regional/cuenta, análisis de riesgo del activo y umbrales de aceptación aprobados.

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


## Endpoint oficial de streaming público de Binance

La captura sincronizada de profundidad utiliza ambos hosts de datos públicos documentados por Binance:
- REST snapshot: `https://data-api.binance.vision/api/v3/depth`.
- WebSocket market-data-only: `wss://data-stream.binance.vision:443/ws`.

Referencia oficial: [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) y [WebSocket Market Streams](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md). Binance documenta estos hosts para datos públicos de mercado; no proporcionan streams de datos de usuario. La selección del host no elude restricciones: se usa el endpoint oficial destinado a datos de mercado y se conserva la evidencia de respuesta. La sincronización solo se declara si el snapshot REST y los eventos de profundidad pasan el protocolo de secuencia existente.


## Fuentes oficiales de velas históricas OHLCV — Issue #13

| Proveedor | Fuente oficial | Semántica/limitación documentada |
|---|---|---|
| Binance Spot | [Kline/Candlestick data](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data) y [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | `GET /api/v3/klines`, campos OHLC, volumen base y quote asset volume; máximo 1000 por petición; timestamps REST en ms por defecto. |
| OKX Spot | [Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks) / [History Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks-history) | `confirm=0/1` diferencia velas incompletas/completas; hasta 300 por petición y múltiples convenciones de barra UTC+8/UTC+0. |
| Bybit Spot | [Get Kline](https://bybit-exchange.github.io/docs/v5/market/kline) | `category=spot`, timestamps ms, máximo 1000; respuesta en orden inverso y la vela actual puede estar incompleta. |
| MEXC Spot | [Kline/Candlestick Data](https://mexcdevelop.github.io/apidocs/spot_v3_en/) | `GET /api/v3/klines`, OHLC, volumen base y quote asset volume; máximo 1000. |
| Gate Spot | [Market K-line chart](https://www.gate.com/docs/developers/apiv4/en/spot/) | `GET /api/v4/spot/candlesticks`, máximo 1000; `from`/`to` en segundos y mutuamente incompatibles con `limit`. |
| Bitget Spot | [Market Data — Get Kline](https://www.bitget.com/docs/catalog/market/market-data) | `GET /api/v3/market/candles` hasta 1000; histórico separado con rango de consulta de hasta 90 días y límites de página documentados. |
| Pionex Spot | [Get Klines](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines) | `GET /api/v1/market/klines`, `time` en ms, OHLC y volumen; hasta 500 por petición, no se documenta un campo separado de quote turnover en la respuesta consultada. |

No se deben combinar las velas de estos proveedores sin normalizar intervalos, zona horaria, cierre confirmado, unidad y semántica de volumen. El histórico de velas no equivale a histórico del libro ni de trades. Ver [matriz de fuentes OHLCV](issue-13-historical-candle-source-matrix.md).
