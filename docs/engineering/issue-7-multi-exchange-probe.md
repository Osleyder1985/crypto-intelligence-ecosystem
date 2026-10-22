# Issue #7 — cobertura de captura pública de libros Spot

El prototipo de sondeo abarca los siete venues del alcance inicial: Binance (referencia), OKX, Bybit, MEXC, Gate, Bitget y Pionex (mercado objetivo a verificar). Captura BTC/USDT, ETH/USDT y SOL/USDT. La finalidad es obtener evidencia técnica inicial de profundidad y top-of-book; no selecciona activos automáticamente ni emite recomendaciones.

## Fuentes oficiales consultadas el 2026-10-22

- Binance Spot depth: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#order-book — `GET /api/v3/depth`; `lastUpdateId` es secuencia, no tiempo.
- OKX API V5 books: https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-order-book — libro público y timestamp del proveedor.
- Bybit V5 orderbook: https://bybit-exchange.github.io/docs/v5/market/orderbook — categoría `spot`, bids/asks, `ts`/`cts`, update ID y secuencia.
- MEXC Spot depth: https://mexcdevelop.github.io/apidocs/spot_v3_en/#order-book — `GET /api/v3/depth`; `lastUpdateId`, bids/asks.
- Gate API v4 spot order book: https://www.gate.com/docs/developers/apiv4/en/spot/ — `GET /api/v4/spot/order_book`, `current`, `update`, bids/asks; público sin autenticación.
- Bitget Market Data order book: https://www.bitget.com/docs/catalog/market/market-data — `GET /api/v3/market/orderbook`, `category=SPOT`, `ts` en milisegundos.
- Pionex Get Depth: https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth — `GET /api/v1/market/depth`, `data.updateTime` en milisegundos y límite documentado de 1 a 1000.

## Semántica y límites

- Se preserva el payload completo, el tamaño, SHA-256 y la hora UTC de captura.
- Los timestamps de proveedor se conservan como valor crudo; no se convierten a una semántica común sin contrato.
- Binance y MEXC REST depth no aportan timestamp de evento en la respuesta documentada; `lastUpdateId` no se trata como hora.
- Los libros son snapshots tomados secuencialmente, no sincronizados entre exchanges. La diferencia temporal entre solicitudes afecta la comparación.
- Las solicitudes usan pares cotizados en USDT; esto no demuestra que los tres pares estén habilitados en Pionex ni que sean accesibles en la región/cuenta objetivo.
- La profundidad solicitada está limitada por los parámetros documentados; no equivale al libro completo.
- No se capturan credenciales, no se envían órdenes y no se emite ranking.
- `PASS` significa respuesta pública estructuralmente válida. La selección requiere además volumen histórico, estabilidad, costes, disponibilidad, riesgo del activo y reglas/umbrales aprobados.
