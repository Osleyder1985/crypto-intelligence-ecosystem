# Integración de scoring de pronósticos al informe — Issue #133

- **Componente:** `scripts/market_selection/attach_forecast_scoring_to_report.py`
- **Pruebas offline:** `tests/market_selection/test_attach_forecast_scoring_to_report.py`
- **Esquema de apéndice:** `crypto-research-report-forecast-evaluation-integration-v1`
- **Entrada:** informe `crypto-asset-research-report-v2` y registros maduros `crypto-investment-forecast-scoring-v1`.

## Comportamiento

La herramienta agrega un apéndice `forecast_evaluation` a un informe existente sin cambiar las conclusiones de los horizontes ni el estado global. Exige que el `asset_id` de todos los registros coincida exactamente con `requested_asset_id` del informe, conserva SHA-256 de los bytes originales del informe y de los registros, y rechaza un informe que ya contenga el apéndice para no sobrescribir evidencia.

El scoring se limita a cohortes compatibles (activo, metodología/versión y horizonte únicos), con outcomes ya maduros. Se conserva `decision_status=INDETERMINATE` y `orders_submitted=false`. El CLI no hace solicitudes de red ni envía órdenes.

## Ejemplo

```bash
python -m scripts.market_selection.attach_forecast_scoring_to_report \
  --report artifacts/crypto-asset-research-report.json \
  --records artifacts/matured-forecast-records.json \
  --output artifacts/crypto-asset-research-report-scored.json
```

El archivo de registros debe ser un array JSON que cumpla el contrato de `forecast_scoring.py`. El reporte original y el archivo de registros se conservan; la salida se escribe en una ruta aparte.

## Limitaciones

La integración no cambia los estados `INDETERMINATE` del informe, no prueba la veracidad de los resultados enlazados ni verifica por sí misma que la metodología esté aprobada. Se debe validar la procedencia y aprobación de los pronósticos antes de usar los resultados. Las pruebas son sintéticas y no demuestran capacidad predictiva ni rentabilidad.
