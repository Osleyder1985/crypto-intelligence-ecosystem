# Frontera de Pareto exploratoria para mercados Spot — Issue #7

- **Herramienta:** \`scripts/market_selection/analyze_spot_market_pareto.py\`
- **Pruebas:** \`tests/market_selection/test_analyze_spot_market_pareto.py\`
- **Entrada:** un artefacto \`multi-exchange-spot-quote-volume-v1\` y otro \`multi-exchange-spot-book-probe-v1\`.
- **Salida:** \`spot-market-exploratory-pareto-v1\`; análisis descriptivo de snapshots, no ranking aprobado.

## Método

1. Verifica esquema, cantidad declarada de registros, Base64, tamaño y SHA-256. Para respuestas exitosas comprueba que el JSON parseado coincide con los bytes originales.
2. Une observaciones por exchange y activo; exige que el símbolo nativo coincida exactamente entre ticker y libro.
3. Solo calcula el vector si el turnover cotizado está \`VALID\`, su unidad \`USDT\` está documentada y el libro contiene al menos diez niveles válidos por lado.
4. Calcula cuatro dimensiones sin pesos: **maximizar** turnover móvil de 24 h, notional bid top-10 y notional ask top-10; **minimizar** spread en puntos básicos.
5. Calcula la frontera de Pareto por activo: una observación domina a otra si no es peor en ninguna dimensión y es estrictamente mejor en al menos una.
6. Conserva candidatos excluidos con razones explícitas. Pionex \`amount\` no se trata como turnover USDT mientras su unidad no esté documentada; los HTTP 403 no se convierten en cero.

## Interpretación y límites obligatorios

- \`EXPLORATORY_ONLY\` significa que hay métricas estructuralmente disponibles para visualizar la frontera; **no** significa que el mercado haya superado gates de elegibilidad.
- La decisión global permanece \`INDETERMINATE\`: no se aplican umbrales de spread, profundidad, slippage, frescura ni tamaño de orden no aprobados.
- La frescura queda \`INDETERMINATE\`. El script conserva timestamps crudos y desfase entre captura del ticker y del libro, pero no inventa una tolerancia temporal.
- Los snapshots son secuenciales, no sincronizados; los libros no representan profundidad histórica ni liquidez sostenible.
- La frontera se calcula por activo y venue. No es un ranking de activos ni una recomendación de inversión; no hay score ponderado, causalidad, predicción ni órdenes.
- Para que el producto declare elegibilidad, el propietario debe aprobar gates, ventanas, tamaños de referencia, política de frescura y tratamiento de faltantes mediante una decisión versionada.

## Resultado de referencia con capturas reales — 2026-10-22

Artefactos de entrada:
- [Turnover 24 h, workflow #39809696897 / artefacto #12439416760](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897/artifacts/12439416760), creado a las 15:57:49.948Z.
- [Libro Spot, workflow #39809697313 / artefacto #12438867580](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809697313/artifacts/12438867580), creado a las 15:57:52.682Z.

El cálculo de referencia con los cuatro objetivos descritos produjo 15 vectores utilizables (cinco venues por activo) y seis observaciones excluidas: Bybit por HTTP 403 y Pionex por unidad de turnover no documentada. Las fronteras exploratorias observadas fueron:

| Activo | Venues no dominados en esta captura | Venues dominados en esta captura |
|---|---|---|
| BTC/USDT | Binance, MEXC | Bitget, Gate, OKX |
| ETH/USDT | Binance, Bitget, MEXC | Gate, OKX |
| SOL/USDT | Binance, Bitget, MEXC | Gate, OKX |

La frontera no es un orden entre los venues listados ni una recomendación. Binance y MEXC, por ejemplo, intercambian ventajas en BTC: Binance muestra mayor turnover y spread menor en el snapshot; MEXC muestra mayor notional visible en ambos lados. Para ETH y SOL, Bitget/MEXC aportan dimensiones de profundidad que impiden que Binance los domine en todas las métricas.

El desfase entre capturas de ticker y libro para los 15 candidatos estuvo entre aproximadamente 2.388 y 3.085 ms. No se interpreta como garantía de sincronización: no existe una tolerancia temporal aprobada, y la semántica/frescura del timestamp de origen difiere por venue. La decisión global permanece \`INDETERMINATE\`, aunque el cálculo de frontera sea reproducible.

## Uso

\`\`\`bash
python -m scripts.market_selection.analyze_spot_market_pareto \\
  --quote-artifact artifacts/multi-exchange-spot-quote-volume.json \\
  --book-artifact artifacts/multi-exchange-spot-book-probe.json \\
  --output artifacts/spot-market-exploratory-pareto.json
\`\`\`

Los dos artefactos deben corresponder a capturas identificadas y preservadas. La herramienta no realiza peticiones de red, no necesita credenciales y no ejecuta órdenes.
