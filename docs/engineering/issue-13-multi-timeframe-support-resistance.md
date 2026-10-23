# Análisis multi-temporal de soportes y resistencias — Issue #13

## Propósito

El módulo `analyze_multi_timeframe_support_resistance.py` ejecuta el analizador causal existente sobre varios artefactos OHLCV Spot de un mismo exchange y símbolo. Cada artefacto mantiene su intervalo, calidad, integridad, método, zonas y stream de eventos propios.

## Contrato de entrada

JSON con `schema_version=multi-timeframe-support-resistance-input-v1` y un array no vacío `artifacts` de capturas normalizadas existentes. Cada captura debe pasar sus controles actuales de autorización de uso del proveedor, integridad y calidad. El usuario debe indicar `pivot_left`, `pivot_right` y `tolerance_bps`; no hay umbrales ocultos.

## Comportamiento y controles

- Rechaza mezclas de exchange, tipo de mercado o símbolo nativo, y rechaza intervalos duplicados.
- Conserva las zonas y eventos por temporalidad sin fusionar precios ni conteos.
- Declara explícitamente `cross_timeframe_confluence=NOT_COMPUTED`; no infiere confluencia a partir de un agregado arbitrario.
- Resume la calidad como completa solo si todas las temporalidades son completas; una temporalidad incompleta hace que el resultado global sea incompleto.
- No cambia el algoritmo de pivotes ni su prevención de look-ahead: la disponibilidad de cada pivote depende del cierre de las velas derechas en su propio intervalo.

## Uso

```bash
python -m scripts.market_selection.analyze_multi_timeframe_support_resistance \
  --input artifacts/multi-timeframe-input.json \
  --pivot-left 2 --pivot-right 2 --tolerance-bps 75 \
  --output artifacts/multi-timeframe-support-resistance.json
```

## Límites

Este módulo organiza resultados independientes; no calcula todavía confluencia entre temporalidades ni un score de fortaleza combinado. Las zonas describen estructura OHLCV y no demuestran órdenes resting, reacción futura ni recomendación de inversión. Las entradas pueden cubrir ventanas diferentes, por lo que el informe debe comparar sus coberturas antes de interpretar diferencias.
