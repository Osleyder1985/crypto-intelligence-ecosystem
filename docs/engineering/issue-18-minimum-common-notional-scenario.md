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
3. Calcula una cantidad auxiliar usando las restricciones publicadas que sí tienen semántica documentada y redondea al `LOT_SIZE.stepSize` de Binance para mantener una cantidad comparable. La unidad de Pionex `minAmount` no está definida inequívocamente; por eso no se utiliza para afirmar elegibilidad.
4. Cuando los mínimos conocidos permiten un cálculo, deriva la cantidad usando el menor precio top-of-book entre bid y ask de cada venue para comprobar ambos sentidos. Simula consumo de asks para compra y bids para venta hasta la cantidad calculada. Si falta profundidad, el escenario queda `INDETERMINATE`; no extrapola.
5. Añade por separado una tarifa pública de referencia por fill (Pionex 5 bps; Binance Regular User 10 bps). Calcula un coste round-trip estático orientativo solo si ambas direcciones se cubren en el snapshot.

## Resultado observado de CI

La ejecución [39727204612](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39727204612/artifacts/12404095553) capturó 12/12 registros, ejecutó el análisis dos veces y comparó ambos JSON byte a byte. Los tres escenarios de frontera quedaron estructuralmente cubiertos en el snapshot:

| Par | Cantidad base común | Notional Pionex al mejor ask | Coste Pionex (USDT / bps) | Notional Binance al mejor ask | Coste Binance (USDT / bps) |
|---|---:|---:|---:|---:|---:|
| BTC/USDT | 0,00013 BTC | 10,7603613 USDT | 0,01076166 / 10,0012 | 10,7625518 USDT | 0,02152640 / 20,0012 |
| ETH/USDT | 0,0041 ETH | 10,008674 USDT | 0,01004965 / 10,0409 | 10,008674 USDT | 0,02005831 / 20,0409 |
| SOL/USDT | 0,096 SOL | 10,09536 USDT | 0,01105488 / 10,9505 | 10,09536 USDT | 0,02114976 / 20,95 |

La columna de coste muestra USDT y, tras la barra, puntos básicos (bps) respecto al notional de compra para normalizar pequeñas diferencias de nominal. Estos costes combinan la diferencia bid/ask e impacto observados en el libro con la tarifa pública por fill (5 bps Pionex, 10 bps Binance). El round-trip supone compra y venta en el mismo snapshot estático. No incluye movimiento de precio entre fills, latencia de ejecución, descuentos de cuenta, componentes fiscales/especiales ni redondeos de comisión; no es beneficio/pérdida esperado ni una garantía de ejecución. El resultado global del artefacto sigue `INDETERMINATE`. **Corrección de interpretación:** la documentación oficial de Pionex describe `minAmount` como mínimo de la orden Spot, pero no especifica la unidad. Por eso no se puede afirmar que los tres casos satisfagan todos los mínimos Pionex: la cantidad es una referencia calculada bajo la hipótesis de que `minAmount` es notional en la moneda cotizada; `pionex_min_amount_unit_verified=false`, `pionex_minimums_satisfied=null` y `scenario_status=INDETERMINATE`. El cálculo y la cobertura del snapshot pueden pasar, sin certificar la validez de orden Pionex.

## Interpretación y límites

- Es una **referencia de frontera basada en una hipótesis explícita**, no un mínimo común verificado, un tamaño comercial típico aprobado ni una recomendación de operación.
- El esquema público Pionex usado no documenta un `stepSize` de cantidad equivalente al filtro Binance; el análisis valida sus mínimos conocidos, pero no certifica todas las reglas de precisión/aceptación de una orden Pionex.
- Las reglas Binance pueden depender del tipo de orden y precio de referencia; este escenario usa `LOT_SIZE` y el filtro de notional capturado como límite inferior de comparación, no como autorización de orden.
- El round-trip supone el mismo snapshot estático para compra y venta. No modela movimiento de precio, colas, latencia de ejecución, impacto posterior, impuestos/comisiones especiales ni moneda/redondeo de tarifa.
- Tarifas efectivas por cuenta no verificadas; las tarifas públicas son solo referencias.
- Las comisiones de retiro/red no están incluidas: esta simulación compra y vende dentro del mismo venue. Si la estrategia mueve activos entre exchanges, se debe añadir la tarifa oficial específica de moneda/red, mínimo de retiro y restricciones de depósito/retiro; no es correcto aplicar una tarifa genérica.
- Por tanto, el resultado del escenario puede ser estructuralmente calculable y aun así la decisión económica global permanece `INDETERMINATE` hasta tener política de frescura aprobada, tarifas aplicables y un tamaño/criterio de producto aprobado.
