# Integración multi-temporal de soportes/resistencias en el informe — Issue #128

El CLI `research_report.py` acepta el argumento opcional `--multi-timeframe-support-resistance-artifacts`, un JSON con el esquema `multi-timeframe-support-resistance-input-v1` y un array `artifacts` de capturas OHLCV Spot previamente preservadas y autorizadas.

El informe incorpora el resultado en `descriptive_analyses.support_resistance_multi_timeframe`. El conjunto de entradas debe referirse al mismo exchange, símbolo nativo y mercado Spot del artefacto principal. Cada entrada vuelve a pasar los controles de autorización e integridad del analizador de soportes/resistencias.

Ejemplo de entrada:

```json
{
  "schema_version": "multi-timeframe-support-resistance-input-v1",
  "artifacts": [
    { "schema_version": "binance-spot-ohlcv-capture-v1" }
  ]
}
```

El ejemplo solo ilustra el envoltorio; cada objeto debe ser una captura completa válida, no un objeto parcial como el fragmento de ejemplo. Los resultados se conservan por intervalo y el informe declara `cross_timeframe_confluence=NOT_COMPUTED`. No se genera una puntuación combinada, recomendación ni orden. Si no se proporciona el argumento, el informe devuelve `status=NOT_PROVIDED` para esta sección.

Pruebas de integración: incorporación al informe y rechazo de un símbolo incompatible.
