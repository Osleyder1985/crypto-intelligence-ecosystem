# Puntuación reproducible de pronósticos maduros — Issue #133

- **Esquema de salida:** `crypto-investment-forecast-scoring-v1`
- **Código:** `scripts/market_selection/forecast_scoring.py`
- **Pruebas offline:** `tests/market_selection/test_forecast_scoring.py`
- **Estado:** calculadora descriptiva; no es una metodología aprobada ni una estrategia de trading.

## Uso

`score_forecast_records(records)` recibe registros ya emitidos y vinculados a sus resultados maduros. Una cohorte debe corresponder a un único activo, ID/versión de metodología y horizonte. La función rechaza IDs de predicción duplicados, retornos no finitos, marcas temporales sin zona horaria y resultados que se declaren observados antes del cierre de su ventana objetivo.

## Métricas

Para pronósticos con `decision_mode=ASSESS` calcula MAE, RMSE y exactitud direccional. El benchmark suministrado por registro se compara sobre las mismas predicciones evaluadas. Los resultados cuyo retorno observado es exactamente cero se excluyen del denominador direccional y se cuentan por separado. Los registros `ABSTAIN` no entran en los errores, pero sí en el total y el cálculo de cobertura; abstenerse no desaparece de la evaluación.

No se calculan probabilidades, calibración, significación estadística ni P&L neto. La calculadora no elige umbrales ni juzga si una mejora es material. El resultado siempre conserva `decision_status=INDETERMINATE` y `orders_submitted=false`.

## Límites y requisitos antes de producción

- El scoring sólo es válido cuando los registros de pronóstico han pasado `crypto-investment-prediction-v1` contra la versión de metodología aprobada y los resultados se han unido mediante una regla de target pre-registrada.
- La comprobación de timestamps impide puntuar un resultado inmaduro; no valida la procedencia de datos ni corrige sesgos del dataset.
- Las pruebas son sintéticas. No demuestran rendimiento real, generalización, causalidad ni rentabilidad.
- Para cerrar Issue #133 siguen siendo necesarios datos históricos point-in-time reales, protocolo congelado antes del test final, ejecución walk-forward/out-of-sample reproducible, benchmarks, costes pertinentes, sensibilidad, incertidumbre y revisión independiente.
