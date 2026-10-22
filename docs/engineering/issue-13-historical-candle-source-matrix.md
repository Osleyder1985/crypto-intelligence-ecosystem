# Matriz de fuentes oficiales OHLCV/histórico — Issue #13

- **Estado:** investigación documental inicial; no es una decisión de proveedor ni evidencia de que todos los mercados estén accesibles.
- **Issues:** [#13 — motor de investigación cuantitativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13), [#7 — selección de mercados Spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7).
- **Propósito:** identificar fuentes oficiales de velas Spot, diferencias de esquema, paginación y límites que condicionan la reconstrucción histórica, la comparación entre venues y las pruebas anti-look-ahead.

## Matriz de fuentes

| Venue | Endpoint oficial Spot | Esquema/tiempo relevante | Límite documentado consultado | Riesgo de comparabilidad |
|---|---|---|---|---|
| Binance | [REST Kline/Candlestick](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data) — `GET /api/v3/klines`; endpoint público también listado en [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | Array con open time, OHLC, volumen base, close time, quote-asset volume, conteo de trades y campos taker. Timestamps REST en ms por defecto. | `limit` máximo documentado 1000 por petición. | Klines se identifican por open time; conservar quote volume bruto y no confundirlo con volumen base. |
| OKX | [API V5 — Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks) y [History Candlesticks](https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks-history) | Array `[ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm]`; `ts` en ms; `confirm=0/1) distingue vela incompleta/completa. Para Spot, la documentación diferencia volumen base de cantidad en moneda cotizada. | Endpoint reciente: hasta 1440 entradas disponibles y máximo 300 por petición; histórico: máximo 300 por petición. | Orden y paginación por `after`/`before`; respetar el campo de confirmación y no mezclar barras UTC+8 con UTC+0. |
| Bybit | [V5 — Get Kline](https://bybit-exchange.github.io/docs/v5/market/kline) — `GET /v5/market/kline?category=spot` | Array por vela con start time, OHLC, volumen y turnover; timestamps en ms. Respuesta en orden inverso (más nueva primero). La vela actual puede no estar cerrada. | `limit` de 1 a 1000; default documentado 200. | Invertir/sortear por timestamp para análisis cronológico y verificar semántica de volumen/turnover bajo categoría Spot, sin reutilizar supuestos de derivados. |
| MEXC | [Spot API — Kline/Candlestick](https://mexcdevelop.github.io/apidocs/spot_v3_en/) — `GET /api/v3/klines` | Array con open time, OHLC, volumen base, close time y quote-asset volume; tiempos en ms. | `limit` máximo documentado 1000. | Esquema no idéntico al de Binance; preservar los campos brutos y comprobar huecos, duplicados y límites de ventana. |
| Gate | [API v4 — Spot Candlesticks](https://www.gate.com/docs/developers/apiv4/en/spot/) — `GET /api/v4/spot/candlesticks` | Array de columnas específicas del proveedor; `from`/`to` usan Unix seconds, no ms. | Máximo 1000 puntos. `limit` entra en conflicto con `from`/`to`; usar la modalidad de consulta documentada, no combinarlos. | Conversión de tiempo debe ser explícita; no interpretar columnas por posición sin un parser probado contra el contrato oficial vigente. |
| Bitget | [Market Data — Get Kline/Candlestick](https://www.bitget.com/docs/catalog/market/market-data) y [History Candles](https://www.bitget.com/docs/catalog/market/market-data) — `GET /api/v3/market/candles`, `GET /api/v3/market/history-candles` | Array documentado con timestamp, OHLC, volumen base y turnover cotizado; timestamps en ms. `category=SPOT). | Reciente: hasta 1000; histórico: consulta máxima de 90 días por rango y límite por página de hasta 100 según la documentación consultada. | No asumir cobertura histórica ilimitada; validar intervalo soportado, orden, frontera de página y posible vela adicional en límites de rango. |
| Pionex | [REST Get Klines](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines) — `GET /api/v1/market/klines` | Objeto por vela con `time` en ms, OHLC y `volume`; la respuesta pública documentada no incluye un campo de turnover cotizado separado. | `limit` default 100, rango 1–500; documentación menciona un límite máximo de 10 000 registros recuperables. | No equiparar `volume` con turnover en USDT. La conversión usando el precio de cierre no representa necesariamente turnover realizado; si se necesita quote turnover, usar un campo fuente documentado o reconstruirlo con trades verificables. |

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
