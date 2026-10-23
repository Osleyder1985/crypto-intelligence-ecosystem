# Integración de evaluaciones independientes por horizonte en el informe — Issue #133

- **Estado:** integración estructural; no es recomendación de inversión ni evidencia de capacidad predictiva.
- **Esquema del apéndice:** `crypto-research-report-horizon-assessment-integration-v1`
- **Entrada:** informe `crypto-asset-research-report-v2` y evaluación `crypto-investment-horizon-assessment-v1`.
- **Implementación:** `scripts/market_selection/attach_horizon_assessment_to_report.py`
- **Pruebas:** `tests/market_selection/test_attach_horizon_assessment_to_report.py`

## Comportamiento

La herramienta valida el contrato de la evaluación, exige coincidencia exacta entre `assessment.asset_id` y `report.requested_asset_id`, y requiere una metodología `APPROVED` cuyo identificador y versión coincidan con la evaluación. Adjunta evaluaciones separadas para corto, medio y largo plazo, incluidas dimensiones de calidad de evidencia, riesgo, oportunidad y confianza, factores incluidos/excluidos y escenarios con reglas de invalidación.

Se conservan los bytes originales de informe, evaluación y metodología mediante SHA-256. Si se proporcionan bytes de origen, deben decodificar como UTF-8 JSON y corresponder exactamente con los objetos recibidos. No se permite sobrescribir un apéndice existente.

## Controles conservadores

- No agrega los horizontes ni calcula una puntuación compuesta.
- No modifica las conclusiones base del informe.
- Mantiene `decision_status=INDETERMINATE` y `orders_submitted=false`.
- Rechaza factores observados o capturados después de `data_as_of`.
- Las salidas favorables/adversas son conclusiones registradas en el apéndice, no una autorización de inversión.
- El estado `APPROVED` y la evidencia de aprobación son datos declarados por el expediente; el adaptador no autentica de forma independiente al aprobador ni el enlace de aprobación.
- La validez del contrato no demuestra que las fuentes sean auténticas, que los factores tengan relevancia económica ni que una predicción funcione fuera de muestra.

## Uso

```bash
python -m scripts.market_selection.attach_horizon_assessment_to_report \
  --report artifacts/crypto-asset-research-report.json \
  --assessment artifacts/horizon-assessment.json \
  --methodology configs/approved-methodology.json \
  --output artifacts/crypto-asset-research-report-with-horizons.json
```

El informe de entrada permanece intacto y la salida se escribe en una ruta separada. La herramienta no solicita datos de red ni envía órdenes.
