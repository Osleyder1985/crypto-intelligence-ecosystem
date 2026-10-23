# Contrato de evidencia de validación fuera de muestra — Issue #133

- **Estado:** contrato estructural; no es una evaluación real ni una metodología de inversión aprobada por sí mismo.
- **Código:** `scripts/market_selection/validation_evidence_contract.py`
- **Pruebas offline:** `tests/market_selection/test_validation_evidence_contract.py`
- **Esquema:** `crypto-investment-validation-report-v1`

## Propósito

Complementa `crypto-investment-methodology-v1` y `crypto-investment-prediction-v1`. Impone una estructura mínima para que una evaluación temporal deje evidencia verificable y comparable. La metodología exacta debe estar en estado `APPROVED`; no se seleccionan umbrales, pesos, universos ni duraciones automáticamente.

## Controles estructurales

- El protocolo debe congelarse antes de la primera ventana de prueba y el informe no puede generarse antes de finalizar la última ventana fuera de muestra declarada.
- El dataset debe tener URL, SHA-256, número de muestras, cobertura temporal, definición del universo point-in-time y tratamiento explícito de activos deslistados/sesgo de supervivencia.
- Cada resultado debe corresponder exactamente a los límites de los splits pre-registrados; no se aceptan ventanas distintas introducidas después de observar resultados.
- Se exige al menos un benchmark comparable, un análisis de sensibilidad, intervalos de incertidumbre y componentes de costes con estados explícitos. Costes desconocidos no pueden representarse como cero.
- Se registra versión de código, comando reproducible, hash del entorno y artefacto de ejecución. Una revisión marcada como completada exige revisor, fecha, URL y SHA-256 de la evidencia.
- La salida contractual permanece `INDETERMINATE`; `orders_submitted=false`.

## Límite importante

El validador comprueba estructura, cronología y consistencia de los campos, no descarga ni verifica de forma independiente los artefactos enlazados, no recalcula métricas y no demuestra utilidad predictiva, calibración ni rentabilidad. Los fixtures de pruebas son sintéticos. Para satisfacer Issue #133 todavía se necesita un dataset histórico point-in-time real, un protocolo aprobado antes de ejecutar el test final, resultados reproducibles walk-forward/out-of-sample, revisión independiente y evidencia de costes, benchmarks, sensibilidad e incertidumbre.

