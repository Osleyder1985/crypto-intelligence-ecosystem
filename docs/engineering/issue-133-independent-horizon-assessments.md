# Contrato de evaluaciones independientes por horizonte — Issue #133

- **Esquema:** `crypto-investment-horizon-assessment-v1`
- **Implementación:** `scripts/market_selection/horizon_assessment_contract.py`
- **Pruebas offline:** `tests/market_selection/test_horizon_assessment_contract.py`
- **Estado:** contrato estructural; no es un modelo validado ni una recomendación de inversión.

## Propósito

Este contrato cierra una brecha entre validar una metodología/predicción y expresar una evaluación interpretable por horizonte. Exige evaluaciones separadas para `short`, `medium` y `long`; pueden discrepar y no se convierten en una puntuación agregada.

## Campos y controles

Cada horizonte debe contener por separado:

- **Calidad de evidencia**, **riesgo del activo**, **oportunidad del horizonte** y **confianza**. Cada dimensión requiere estado explícito, justificación y referencias de evidencia.
- Factores incluidos y excluidos, con categoría, decisión, razón, fuente, versión de transformación, instante observado y capturado. Las observaciones y capturas no pueden ser posteriores a `data_as_of`.
- Escenarios `FAVORABLE`, `BASE` y `ADVERSE`, cada uno con condiciones y reglas explícitas de invalidación.
- Modo de decisión `ASSESS` o `ABSTAIN`. Abstenerse exige motivos y conclusión `INDETERMINATE`.

Los estados de dimensión son descriptivos del expediente, no puntuaciones numéricas. No hay pesos ni score compuesto implícito. Los factores no verificables pueden registrarse como excluidos; no deben convertirse en evidencia positiva.

## Límites

El validador comprueba campos y cronología, pero no verifica por sí mismo las fuentes, la relevancia económica de cada factor, la exactitud de escenarios ni el desempeño predictivo. La salida global permanece `INDETERMINATE` y `orders_submitted=false`. El contrato no sustituye el protocolo congelado, el dataset point-in-time, la evaluación walk-forward/out-of-sample, los benchmarks, los costes, la sensibilidad, la incertidumbre ni la revisión independiente requeridos por #133.
