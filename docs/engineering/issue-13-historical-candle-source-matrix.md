# Matriz de fuentes oficiales OHLCV/histórico — Issue #13

- **Estado:** investigación documental inicial; no es una decisión de proveedor ni evidencia de que todos los mercados estén accesibles.
- **Issues:** [#13 — motor de investigación cuantitativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13), [#7 — selección de mercados Spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7).
- **Propósito:** identificar fuentes oficiales de velas Spot, diferencias de esquema, paginación y límites que condicionan la reconstrucción histórica, la comparación entre venues y las pruebas anti-look-ahead.

## Matriz de fuentes

| Venue | Endpoint oficial Spot | Esquema/tiempo relevante | Límite documentado consultado | Riesgo de comparabilidad |
|---|---|---|---|---|
| Binance | [REST Kline/Candlestick](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data) — `GET /api/v3/klines`; host público sin credenciales: [Market Data Only](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md). Para rangos extensos, [archivo público oficial](https://github.com/binance/binance-public-data) con ZIP diarios/mensuales. | REST: array con open time, OHLC, volumen base/cotizado, close time, trades y campos taker; ms por defecto. Archivo Spot: timestamps en microsegundos desde 2025-01-01; interval mensual se etiqueta `1mo` en nombres de archivo. | REST `limit` máximo 1000 por petición. Archivo: ZIP por día/mes e intervalo, con `.CHECKSUM` publicado. | No mezclar REST ms con archivo µs; verificar checksum, términos del dataset, versiones/correcciones del archivo y límites exactos de ventana. |
| OKX | [API V5 — Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks) y [History Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks-history) | Array `[ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm]`; `ts` en ms; `confirm=0/1` distingue vela incompleta/completa. Para Spot, `vol` es volumen base y `volCcyQuote` es volumen en moneda cotizada; conservar también `volCcy` bruto. `after` pagina hacia velas anteriores; `1Dutc` usa apertura diaria UTC. | Endpoint reciente: hasta 1440 entradas disponibles y máximo 300 por petición; histórico: máximo 300 por petición. | Respuesta más reciente primero; respetar `confirm` y no mezclar barras UTC+8 con UTC+0. |
| Bybit | [V5 — Get Kline](https://bybit-exchange.github.io/docs/v5/market/kline) — `GET /v5/market/kline?category=spot` | Array por vela con start time, OHLC, volumen y turnover; timestamps en ms. Respuesta en orden inverso (más nueva primero). La vela actual puede no estar cerrada. | `limit` de 1 a 1000; default documentado 200. `start` y `end` son milisegundos y la respuesta se ordena de más reciente a más antigua. | Invertir/sortear por timestamp para análisis cronológico y verificar semántica de volumen/turnover bajo categoría Spot, sin reutilizar supuestos de derivados. |
| MEXC | [Spot API — Kline/Candlestick](https://mexcdevelop.github.io/apidocs/spot_v3_en/) — `GET /api/v3/klines` | Array con open time, OHLC, volumen base, close time y quote-asset volume; tiempos en ms. | `limit` máximo documentado 1000; `startTime`/`endTime` son milisegundos y las klines se identifican por `open time`. | Esquema no idéntico al de Binance; preservar los campos brutos y comprobar huecos, duplicados y límites de ventana. |
| Gate | [API v4 — Spot Candlesticks](https://www.gate.com/docs/developers/apiv4/en/spot/) — `GET /api/v4/spot/candlesticks` | Array de columnas específicas del proveedor; `from`/`to` usan Unix seconds, no ms. | Máximo 1000 puntos. `from`/`to` son segundos Unix y `limit` entra en conflicto con ambos; no enviarlos juntos. La fila documentada es `[timestamp, quote_volume, close, high, low, open, base_amount]`. | Conversión de tiempo debe ser explícita; no interpretar columnas por posición sin un parser probado contra el contrato oficial vigente. |
| Bitget | [Market Data — Get Kline/Candlestick](https://www.bitget.com/docs/catalog/market/market-data) y [History Candles](https://www.bitget.com/docs/catalog/market/market-data) — `GET /api/v3/market/candles`, `GET /api/v3/market/history-candles` | Array documentado con timestamp, OHLC, volumen base y turnover cotizado; timestamps en ms; mercado Spot según el endpoint documentado. | Reciente: hasta 1000 por página; histórico: rango máximo de 90 días por solicitud y límite de 100 por página. La documentación limita las velas históricas a `1m`, `5m`, `15m`, `1H`, `4H` y `1D`; un `endTime` que rebasa el límite de vela puede incluir una vela adicional. | No asumir cobertura histórica ilimitada; validar intervalo soportado, orden, frontera de página y posible vela adicional en límites de rango. |
| Pionex | [REST Get Klines](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines) — `GET /api/v1/market/klines` | Objeto por vela con `time` en ms, OHLC y `volume`; la OpenAPI oficial solo define `volume` como volumen total negociado y no documenta un campo de turnover cotizado separado. Por tanto, `quote_volume` debe quedar `null`/`NOT_PROVIDED_BY_SOURCE`, sin estimarlo como `volume × close`. | `endTime` es milisegundos; `limit` default 100, rango 1–500; la OpenAPI menciona un máximo de 10 000 registros recuperables. Para paginar hacia atrás, usar el timestamp de la vela más antigua como cursor y comprobar progreso. | No equiparar `volume` con turnover en USDT. La conversión usando el precio de cierre no representa necesariamente turnover realizado; si se necesita quote turnover, usar un campo fuente documentado o reconstruirlo con trades verificables. |


## Fuente adicional para historia extensa: archivo público de Binance

La documentación oficial de [Binance Public Data](https://github.com/binance/binance-public-data) confirma que el portal [data.binance.vision](https://data.binance.vision/) publica datos de mercado en archivos diarios y mensuales, incluidas velas Spot. Para historia extensa, estos archivos pueden reducir la cantidad de llamadas REST, pero tienen un contrato temporal distinto que debe tratarse explícitamente.

- La documentación indica que los timestamps de datos Spot del archivo desde **2025-01-01** están en **microsegundos**, mientras que el endpoint REST usado por el adaptador actual devuelve milisegundos por defecto. No inferir la unidad solo por el tamaño del número: registrar fuente y versión del formato.
- Los archivos de velas usan `1mo` en la ruta/nombre para el intervalo mensual; la API REST usa `1M`. Normalizar el intervalo sin perder el valor original.
- Cada ZIP tiene un archivo `.CHECKSUM` para verificación de integridad. Conservar el archivo de checksum, resultado de la verificación, ruta del dataset, fecha de descarga y SHA-256 del artefacto local.
- El repositorio oficial advierte que archivos archivados pueden actualizarse posteriormente por correcciones. Por ello, identificar cada versión por checksum y no sobrescribir un dataset ya utilizado en una evaluación.
- Consultar y registrar los [términos del dataset](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) antes de distribuir o almacenar los archivos derivados.

**Consecuencia para el motor:** REST es útil para rangos acotados y captura reciente; el archivo oficial es una fuente candidata para backtests de historia extensa. Antes de combinarlos, comprobar continuidad en las fronteras, unidades temporales, velas corregidas, campos, huecos y duplicados. La existencia del archivo no prueba que el símbolo o la ventana deseada estén completos ni que el resultado sea apto para un backtest sin controles adicionales.

## Contrato canónico propuesto para una vela

Cada vela normalizada debería conservar, además del payload/hash original:

- `venue_id`, `market_type=spot`, símbolo nativo y activos base/cotizado canónicos;
- intervalo solicitado, timestamp de apertura UTC y cierre UTC cuando la fuente lo suministre, además de los valores/unidades originales;
- OHLC decimal sin redondeo intermedio, volumen base y volumen cotizado como campos separados, con unidades explícitas;
- `is_closed` como `true`, `false` o `unknown`; nunca inferir que una vela está cerrada solo porque la API respondió 200;
- URL/endpoint, parámetros, hora de solicitud, captura UTC, código de respuesta, hash SHA-256, versión del parser y limitaciones;
- estado de calidad para timestamp inválido, vela duplicada, hueco, OHLC imposible, volumen negativo, unidad desconocida o símbolo inesperado.

La clave de deduplicación debe derivarse del venue, mercado, símbolo canónico, intervalo y open time. Si la fuente corrige una vela, conservar la nueva versión y su procedencia; no sobrescribir silenciosamente una entrada histórica sin registrar la revisión.

## Reglas de investigación histórica

1. **No mezclar unidades de tiempo.** Gate usa segundos en `from`/`to`; otros endpoints citados usan milisegundos. Mantener el valor original y una conversión UTC explícita.
2. **No usar velas abiertas para certificar señales de cierre.** OKX expone `confirm`; otros proveedores pueden requerir comparar el límite temporal de la vela con un reloj documentado o esperar a la siguiente vela. Si el cierre no puede demostrarse, marcar `unknown` y excluirla de métricas que exigen cierre confirmado.
3. **Evitar fuga de información.** Una señal en el instante (t) solo puede usar velas, eventos y datos que ya estaban disponibles en (t). No usar el high/low/close final de una vela para simular una decisión tomada antes de su cierre.
4. **No afirmar profundidad histórica a partir de OHLCV.** Las velas no reconstruyen el libro de órdenes ni trades individuales. Para slippage histórico se necesitan trades o snapshots/deltas de libro conservados durante el periodo.
5. **Validar cobertura antes de modelar.** Medir intervalos esperados/observados, huecos, duplicados, timestamps repetidos, cambios de listado, zonas horarias, límites de API y datos ausentes por venue/par.
6. **Versionar metodología y entradas.** Un backtest debe conservar el rango temporal, intervalos, reglas de exclusión, fuente y versión del dataset, parámetros, código, costes incluidos y resultados negativos.
7. **No declarar equivalencia entre campos por el nombre.** En especial, volumen base, volumen cotizado, contratos y turnover deben permanecer separados hasta que el contrato oficial de cada mercado respalde la equivalencia.

## Recomendación técnica de secuenciación

Para la primera prueba de concepto histórica, seleccionar un par Spot común solo después de confirmar identidad/disponibilidad en los venues elegidos. Empezar con un intervalo común y una ventana de prueba explícita; capturar el payload íntegro, paginar dentro de los límites oficiales y validar cobertura antes de implementar indicadores, detección de movimientos o soportes/resistencias. Mantener la primera implementación como investigación read-only: este documento no autoriza órdenes ni afirma que una estrategia sea predictiva o rentable.

## Decisiones aún no adoptadas

- Intervalos y horizonte histórico prioritarios del producto.
- Universo inicial de venues/pares con cobertura demostrada.
- Política de retención, almacenamiento permanente y presupuesto de datos.
- Reglas para excluir/usar velas incompletas, huecos y correcciones.
- Métricas de evaluación predictiva, particiones temporales y benchmarks.
- Si el producto necesitará histórico de trades/profundidad, que es distinto de OHLCV.

No se fijan umbrales de calidad, frescura, rentabilidad o cobertura sin requisitos medibles y evidencia previa.
