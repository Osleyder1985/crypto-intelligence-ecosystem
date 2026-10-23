# Contrato de metodología por horizonte y validación temporal — Issue #133

- **Estado:** contrato de validación inicial en rama de trabajo; no es metodología de inversión aprobada.
- **Issue:** [#133](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/133)
- **Dependencias:** [#128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128), [#130](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/130), [#134](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/134)
- **Código:** `scripts/market_selection/methodology_contract.py`
- **Tests:** `tests/market_selection/test_methodology_contract.py`
- **Contratos:** `crypto-investment-methodology-v1`, `crypto-investment-prediction-v1`
- **Consulta:** 2026-10-22

## 1. Principio de configuración explícita

No existe en este contrato una definición universal de corto, medio y largo plazo ni un umbral universal de rentabilidad. Cada versión debe declarar la duración de sus tres horizontes, objetivo, unidad, fórmula, fuente de precios y regla de muestreo. Las duraciones deben estar ordenadas estrictamente `short < medium < long`, pero sus valores los debe aprobar la metodología del producto con evidencia y validación, no el validador.

La política de umbrales empieza en `NOT_APPROVED`. El contrato no asigna defaults de rentabilidad, probabilidad, score o tolerancia al riesgo.

## 2. Campos de metodología requeridos

- ID y versión inmutables; estado `DRAFT`, `APPROVED` o `RETIRED`.
- Definición de cada horizonte: duración en segundos, objetivo, unidad y descripción.
- Definición del target: fórmula, fuente de precio y regla de muestreo.
- Política de umbrales con estado explícito. Si se marca aprobada, requiere evidencia y límites coherentes.
- Protocolo de validación con walk-forward, test fuera de muestra y controles anti-leakage obligatorios.
- Splits temporales con `train_end < test_start < test_end` y ventanas de test no solapadas.
- Modelo de costes explícito: fees, spread, slippage, funding/borrow y otros costes. Cada componente debe ser medido, estimado, no aplicable con justificación, no disponible o no aprobado. Un coste desconocido no se convierte en cero.
- Registro de features con fuente, campo temporal de disponibilidad y versión de transformación.

## 3. Contrato de predicción y prevención de leakage

Cada registro `crypto-investment-prediction-v1` conserva identidad estable del activo, versión exacta de metodología, horizonte, instante de generación, corte de datos, fin de datos de entrenamiento, ventana objetivo, features y salida.

Reglas aplicadas:
- `data_as_of <= generated_at`.
- `model_training_data_end <= data_as_of` y siempre anterior a `generated_at`.
- `target_window_start > generated_at`; el final debe ser posterior al inicio y la duración debe coincidir con la versión de horizonte.
- Cada feature debe estar declarada en la metodología, con el mismo source ID y versión de transformación.
- Tanto `observed_at` como `captured_at` de cada feature deben ser anteriores o iguales a `data_as_of`.
- No se valida un registro de predicción contra metodología `DRAFT` o `RETIRED`.
- Las probabilidades deben estar entre 0 y 1.
- La salida de validación sigue `INDETERMINATE` y `orders_submitted=false`; validar el formato no valida la capacidad predictiva.

## 4. Qué todavía no demuestra

Esta implementación no entrena modelos, no determina qué factores predicen rendimientos, no estima la calidad predictiva, no calibra probabilidades, no valida benchmarks ni costes reales, y no autoriza una estrategia. Las pruebas sintéticas demuestran controles del contrato, no rentabilidad ni robustez. Antes de aprobar una metodología se necesitan datasets point-in-time, universo con supervivientes y activos desaparecidos, benchmarks, costes aplicables, evaluación walk-forward/out-of-sample, calibración, intervalos de incertidumbre, análisis de régimen y registro inmutable de predicciones/resultados.

## 5. Pruebas

Los tests cubren versiones/horizontes, orden temporal, costes desconocidos, aprobación explícita, splits de validación, identidad de features, transformación versionada, corte de disponibilidad, ventanas objetivo y probabilidades inválidas. El workflow dedicado debe ejecutarse sobre el head actual antes de declarar el cambio validado.

## 6.1 Control adicional para probabilidades

Una predicción que incluya `output.probability_up` debe adjuntar `output.probability_calibration`: estado `VALIDATED`, método, métrica (Brier score, log loss o ECE), puntuación, intervalo de evaluación, número de muestras, URL y SHA-256 de la evidencia, revisor y fecha de revisión. La revisión y el intervalo de evaluación deben ser anteriores o iguales a la emisión de la predicción; un hash mal formado o una calibración futura se rechazan.

Este gate mejora la trazabilidad y evita que una probabilidad desnuda pase el contrato. **No verifica de forma independiente la veracidad del expediente ni demuestra que el modelo esté bien calibrado**: esa validación exige revisar la evidencia y reproducir la evaluación out-of-sample. El resultado del contrato continúa siendo `INDETERMINATE`, sin recomendación ni órdenes.
