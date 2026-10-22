# Escenario de frontera por mínimo común de notional — Issue #18

- **Script:** `scripts/market_selection/analyze_minimum_common_notional_scenario.py`.
- **Salida CI:** `artifacts/minimum-common-notional-1.json`.
- **Decisión global:** `INDETERMINATE`; no autoriza ejecución.

## Por qué existe este escenario

Los requisitos de los Issues #7/#13 piden tamaños de referencia basados en requisitos y restricciones oficiales, pero no especifican el tamaño comercial típico del producto. Este análisis no inventa ese tamaño. Construye un escenario auxiliar de frontera: la cantidad base común mínima derivable de los mínimos públicos de ambos venues para cada par, redondeada al incremento de cantidad del filtro Binance `LOT_SIZE` capturado.

Fuentes oficiales:
- [Pionex Market Data — símbolos](https://pionex-doc.gitbook.io/apidocs/restful/common/market-data): el esquema distingue `minAmount` (mínimo de orden Spot) y `minTradeSize` (cantidad mínima de orden límite).
- [Binance Spot filters](https://github.com/binance/binance-spot-api-docs/blob/master/filters.md): `LOT_SIZE` define mínimo, máximo e incremento de cantidad; `NOTIONAL`/`MIN_NOTIONAL` define mínimos de notional y su aplicabilidad por tipo de orden.

## Método

1. Verifica HTTP 200, bytes preservados, SHA-256 y que el JSON parseado coincide con la respuesta original para metadata y libros.
2. Extrae el símbolo Pionex y los filtros Binance del mismo artefacto, no de cifras hardcodeadas por par.
3. Calcula el mínimo base que satisface los mínimos de notional/cantidad conocidos de ambos venues, usando el mejor ask de cada snapshot, y redondea hacia arriba al `LOT_SIZE.stepSize` de Binance para mantener una cantidad común comparable.
4. Deriva la cantidad usando el menor precio top-of-book entre bid y ask de cada venue para asegurar que el mínimo de notional se cumple en ambos sentidos. Simula consumo de asks para compra y bids para venta hasta la cantidad calculada. Si falta profundidad, el escenario queda `INDETERMINATE`; no extrapola.
5. Añade por separado una tarifa pública de referencia por fill (Pionex 5 bps; Binance Regular User 10 bps). Calcula un coste round-trip estático orientativo solo si ambas direcciones se cubren en el snapshot.

## Interpretación y límites

- Es un **escenario mínimo de restricciones**, no un tamaño comercial típico aprobado ni una recomendación de operación.
- El esquema público Pionex usado no documenta un `stepSize` de cantidad equivalente al filtro Binance; el análisis valida sus mínimos conocidos, pero no certifica todas las reglas de precisión/aceptación de una orden Pionex.
- Las reglas Binance pueden depender del tipo de orden y precio de referencia; este escenario usa `LOT_SIZE` y el filtro de notional capturado como límite inferior de comparación, no como autorización de orden.
- El round-trip supone el mismo snapshot estático para compra y venta. No modela movimiento de precio, colas, latencia de ejecución, impacto posterior, impuestos/comisiones especiales ni moneda/redondeo de tarifa.
- Tarifas efectivas por cuenta no verificadas; las tarifas públicas son solo referencias.
- Por tanto, el resultado del escenario puede ser estructuralmente calculable y aun así la decisión económica global permanece `INDETERMINATE` hasta tener política de frescura aprobada, tarifas aplicables y un tamaño/criterio de producto aprobado.
