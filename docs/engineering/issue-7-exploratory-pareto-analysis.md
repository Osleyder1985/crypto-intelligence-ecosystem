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

## Uso

\`\`\`bash
python -m scripts.market_selection.analyze_spot_market_pareto \\
  --quote-artifact artifacts/multi-exchange-spot-quote-volume.json \\
  --book-artifact artifacts/multi-exchange-spot-book-probe.json \\
  --output artifacts/spot-market-exploratory-pareto.json
\`\`\`

Los dos artefactos deben corresponder a capturas identificadas y preservadas. La herramienta no realiza peticiones de red, no necesita credenciales y no ejecuta órdenes.
