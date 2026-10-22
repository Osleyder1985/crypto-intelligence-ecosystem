# Curvas paramétricas de coste de libro — Issue #18

- **Estado:** análisis descriptivo; no selecciona tamaño comercial ni autoriza ejecución.
- **Issue:** [#18](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Script:** `scripts/market_selection/analyze_depth_cost_curves.py`.
- **Salida CI:** `artifacts/depth-cost-curves-1.json`, comparada byte a byte con una segunda ejecución para probar determinismo.

## Método

El script verifica para cada libro el HTTP 200, Base64, longitud de bytes, SHA-256 y equivalencia del JSON parseado con el cuerpo preservado. Luego recorre todos los niveles recibidos y genera, por venue, dos curvas:

- Compra consumiendo asks, acumulando cantidad base y coste cotizado, con VWAP acumulado y slippage frente al mid del snapshot.
- Venta consumiendo bids, acumulando cantidad base y producto cotizado, con VWAP acumulado y slippage frente al mismo mid.

Cada punto corresponde a consumir desde el mejor precio hasta ese nivel real. Por tanto, el tamaño base se deriva del libro capturado, no de un importe comercial inventado. La salida conserva el número de niveles realmente recibidos, mejores precios, spread y profundidad cotizada visible. Los snapshots de Binance y Pionex se analizan por separado.

## Referencia pública de comisión (no efectiva de cuenta)

Cada punto incluye `slippage_plus_public_fee_reference_bps_per_fill`, una suma ilustrativa de slippage frente al mid y una tarifa pública de referencia por un solo fill:
- Pionex Spot: 0,050% maker/taker (5 bps), [tarifas oficiales](https://www.pionex.com/es/fees).
- Binance Spot, Regular User: 0,100% maker/taker (10 bps), [tarifas oficiales](https://www.binance.com/es-LA/fee/trading).

La salida conserva `effective_account_fee_verified=false`. El overlay no aplica VIP, descuentos BNB, promociones de símbolo, componentes fiscales/especiales, moneda de comisión ni redondeos. No es un coste total round-trip y no se debe interpretar como tarifa efectiva del usuario. Se ofrece solo como escenario público de referencia para que el impacto de usar una tarifa base sea visible.

## Restricciones oficiales de símbolo preservadas

La curva también conserva restricciones de los metadatos oficiales de cada mercado:
- Pionex `GET /api/v1/common/symbols`: identidad Spot, enable, precisión, `minAmount`, `minTradeSize`, `maxTradeSize`, `minTradeDumping`, `maxTradeDumping`, `buyCeiling` y `sellFloor`, cuando estén presentes. La documentación distingue límites de orden limit de campos de dumping para venta market.
- Binance `GET /api/v3/exchangeInfo`: identidad, estado, permiso Spot y lista completa de filtros de símbolo, incluidos `PRICE_FILTER`, `LOT_SIZE`, `MARKET_LOT_SIZE`, `MIN_NOTIONAL`/`NOTIONAL` cuando existan.

Fuentes oficiales: [Pionex Market Data / common symbols](https://pionex-doc.gitbook.io/apidocs/restful/common/market-data) y [Binance Spot REST API](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md).

El estado de captura de restricciones puede ser `PASS` si los metadatos se validan; eso **no** significa que una orden sea elegible. `order_size_eligibility` permanece `INDETERMINATE` mientras el producto no defina tamaño y tipo de orden, y mientras no se comprueben los filtros relevantes para ese tipo.

## Interpretación

- `slippage_bps_vs_mid` es una medida de desviación del VWAP acumulado frente al mid del snapshot; incluye el efecto del spread y el impacto de los niveles consumidos. No es una garantía de precio de ejecución.
- `visible_depth_quote` suma precio × cantidad de todos los niveles recibidos. No es liquidez garantizada ni prueba que el libro se mantenga hasta la orden.
- La curva base de slippage no incluye comisiones; la salida agrega aparte un overlay de tarifa pública de referencia por fill. El coste total efectivo sigue indeterminado hasta integrar evidencia aplicable a la cuenta/símbolo.
- Las capturas entre venues son secuenciales, no se declara que estén sincronizadas.
- El script no escoge un tamaño único, no crea un umbral de aprobación y no envía órdenes; el resultado global es `INDETERMINATE`.

## Reproducción

El workflow `Multi-pair public market capture (read-only)` captura el máximo de profundidad documentado, genera las curvas dos veces y exige que los dos JSON sean idénticos. El artefacto de CI incluye la captura original y la curva derivada para poder verificar los cálculos sin volver a consultar la red.
