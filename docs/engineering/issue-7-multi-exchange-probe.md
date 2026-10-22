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

## Primera captura integrada tras PR #104 — 2026-10-22

Workflow: [Multi-exchange spot book probe #39776977998](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39776977998). Artefacto: [multi-exchange-spot-book-probe](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39776977998/artifacts/12424827345). La ejecución y sus tests offline terminaron en `success`; la captura de mercado tuvo `overall_status=PARTIAL`.

| Exchange | Capturas PASS | Observación |
|---|---:|---|
| Binance | 3/3 | HTTP 200; 100 bids y 100 asks por activo; REST depth no contiene timestamp de evento. |
| OKX | 3/3 | HTTP 200; 20 bids y 20 asks por activo; timestamp del proveedor presente. |
| Bybit | 0/3 | HTTP 403 para BTC/ETH/SOL en el runner de CI; acceso no confirmado en ese entorno. |
| MEXC | 3/3 | HTTP 200; 100 bids y 100 asks por activo; REST depth no contiene timestamp de evento. |
| Gate | 3/3 | HTTP 200; 20 bids y 20 asks por activo; `update` presente. |
| Bitget | 3/3 | HTTP 200; 100 bids y 100 asks por activo; timestamp del proveedor presente. |
| Pionex | 3/3 | HTTP 200; 100 bids y 100 asks por activo; `data.updateTime` presente. |

Resultado: **18/21 respuestas PASS**, **3/21 FAIL** por HTTP 403 de Bybit. No se cambia a un dominio alternativo ni se intenta eludir una restricción geográfica o de acceso. La respuesta 403 se trata como falta de accesibilidad en ese entorno, no como prueba de que el mercado o el exchange no existan. La captura es secuencial, no sincronizada; los precios y timestamps no deben interpretarse como una comparación simultánea ni como liquidez histórica.

Durante la revisión se detectó que el capturador conservaba el tipo y mensaje de `HTTPError` pero omitía su código HTTP en el campo `http_status`. El cambio correctivo registra `exc.code` y añade una regresión para HTTP 451; la captura anterior sigue siendo evidencia original inalterada.

## Segunda captura integrada con métricas top-of-book — 2026-10-22T13:56:45.952Z

Workflow: [Multi-exchange spot book probe #39791367596](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39791367596). Artefacto: [multi-exchange-spot-book-probe #12430663356](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39791367596/artifacts/12430663356).

### Integridad y cobertura

- El workflow terminó en `success`; la captura de mercado fue `PARTIAL`.
- Las 21 respuestas tienen cuerpo preservado, longitud coincidente y SHA-256 verificado: 21/21.
- 18/21 snapshots fueron válidos; Bybit devolvió HTTP 403 para los tres pares. La respuesta de error también se preservó y no se reemplazó por un libro vacío.
- Binance, MEXC, Bitget y Pionex devolvieron 100 niveles por lado; OKX y Gate devolvieron 20 por lado. La ventana temporal entre la primera y última respuesta fue de 4.833 s. Por tanto, no son snapshots simultáneos.
- Binance y MEXC no aportan un timestamp de evento de libro utilizable en el contrato documentado; sus identificadores de actualización no se interpretan como horas. El estado de frescura absoluta de esos snapshots es `INDETERMINATE`.

### Spread y notional visible en los primeros diez niveles

Spread en puntos básicos: `(best_ask - best_bid) / mid × 10,000`. La profundidad USDT de los primeros diez niveles es la suma de `precio × cantidad` por lado. Se informa como descriptor de la instantánea; no implica que ese notional pueda ejecutarse sin impacto ni que los niveles sigan disponibles.

| Par | Venue | Mejor bid | Mejor ask | Spread (bps) | Bid top-10 (USDT) | Ask top-10 (USDT) | Niveles recibidos por lado |
|---|---|---:|---:|---:|---:|---:|---:|
| BTC/USDT | Binance | 81,703.24 | 81,703.25 | 0.0012 | 851,334.90 | 69,622.80 | 100 |
| BTC/USDT | OKX | 81,714.80 | 81,714.90 | 0.0122 | 99,360.22 | 219,723.95 | 20 |
| BTC/USDT | MEXC | 81,699.90 | 81,699.91 | 0.0012 | 1,552,382.06 | 54,111.45 | 100 |
| BTC/USDT | Gate | 81,704.00 | 81,704.10 | 0.0122 | 36,162.30 | 17,426.66 | 20 |
| BTC/USDT | Bitget | 81,711.43 | 81,711.44 | 0.0012 | 17,343.13 | 479,937.95 | 100 |
| BTC/USDT | Pionex | 81,703.24 | 81,703.25 | 0.0012 | 2,770,565.86 | 2,259,895.32 | 100 |
| ETH/USDT | Binance | 2,411.52 | 2,411.53 | 0.0415 | 469,462.40 | 50,336.99 | 100 |
| ETH/USDT | OKX | 2,412.02 | 2,412.03 | 0.0415 | 127,833.10 | 36,836.14 | 20 |
| ETH/USDT | MEXC | 2,411.39 | 2,411.62 | 0.9538 | 219,247.11 | 105,111.06 | 100 |
| ETH/USDT | Gate | 2,411.32 | 2,411.33 | 0.0415 | 10,305.55 | 11,443.84 | 20 |
| ETH/USDT | Bitget | 2,412.37 | 2,412.38 | 0.0415 | 152,820.43 | 1,121,511.49 | 100 |
| ETH/USDT | Pionex | 2,412.07 | 2,412.08 | 0.0415 | 1,411,527.07 | 901,643.05 | 100 |
| SOL/USDT | Binance | 105.11 | 105.12 | 0.9513 | 873,300.47 | 644,471.47 | 100 |
| SOL/USDT | OKX | 105.13 | 105.14 | 0.9512 | 271,078.20 | 307,552.34 | 20 |
| SOL/USDT | MEXC | 105.10 | 105.11 | 0.9514 | 521,266.69 | 1,146,187.57 | 100 |
| SOL/USDT | Gate | 105.11 | 105.12 | 0.9513 | 62,014.51 | 31,697.34 | 20 |
| SOL/USDT | Bitget | 105.13 | 105.14 | 0.9512 | 1,379,584.31 | 2,138,460.82 | 100 |
| SOL/USDT | Pionex | 105.11 | 105.12 | 0.9513 | 1,961,205.50 | 1,589,333.23 | 100 |

### Interpretación correcta

1. En este snapshot, ETH/USDT de MEXC muestra un spread superior al de los otros venues consultados; es una observación puntual, no una conclusión sobre su spread típico ni una exclusión permanente.
2. Los notionales de los primeros diez niveles difieren mucho entre lados y venues. Eso justifica analizar compra y venta por separado; un solo número de volumen o imbalance no sustituye el coste VWAP para una cantidad definida.
3. No se puede comparar directamente el total de 20 niveles de OKX/Gate con el total de 100 niveles de otros venues. La tabla usa top-10 para igualar el número de niveles, pero el espaciado de precios y la profundidad de mercado siguen siendo distintos.
4. No se fija un tamaño de orden ni un límite de spread/slippage. Sin esos requisitos, no existe una clasificación de elegibilidad aprobada.
5. El snapshot no está sincronizado entre exchanges, y la ausencia de timestamp de evento en Binance/MEXC impide demostrar frescura absoluta. La política adoptada para investigación pública exige mantener esos casos en `INDETERMINATE` cuando la edad no se puede demostrar.
6. La captura de libro complementa el turnover 24 h, pero no aporta profundidad histórica. No puede usarse para reconstruir retrospectivamente el libro ni para afirmar rentabilidad.

Esta evidencia avanza 7-M02, pero no lo cierra: faltan series repetidas de libro, criterios de frescura y tamaño de referencia, tarifas aplicables y validación de cobertura.
