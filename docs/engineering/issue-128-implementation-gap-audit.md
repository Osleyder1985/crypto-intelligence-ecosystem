# Auditoría de brechas de implementación — objetivo integral de Issue #128

- **Fecha de revisión:** 2026-10-22.
- **Línea base inspeccionada:** `main` en `6aef5146c2cb58633383ec3bc995dae89a11df89`.
- **Estado:** auditoría documental del árbol de código, scripts y pruebas disponibles; no equivale a ejecutar una auditoría de seguridad ni a validar la calidad económica de las señales.
- **Issue rector:** [#128 — Flujo integral de investigación por activo](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128).
- **Regla de evidencia:** la existencia de un script o de pruebas unitarias demuestra solo el alcance que esas pruebas ejercitan; no demuestra integración de producto, calidad predictiva ni preparación para producción.

## 1. Conclusión ejecutiva

La línea base contiene componentes analíticos reutilizables para datos públicos Spot: captura histórica OHLCV de Binance, perfil descriptivo de riesgo, detección de movimientos de precio/volumen, zonas de soporte/resistencia, evaluación de capturas de liquidez y registros locales de evaluación con hashes.

**No se ha encontrado en el árbol inspeccionado un flujo de aplicación/API o interfaz de usuario que conecte esos componentes a partir de una consulta de activo.** Tampoco se ha identificado un conector implementado de noticias/eventos externos ni un motor integrado que produzca, para un activo arbitrario, tres evaluaciones de horizonte y un informe final. La evaluación existente de mercado público está orientada a un escenario Spot fijo y devuelve `INDETERMINATE` cuando no hay política aprobada; no es una recomendación de inversión.

Por tanto, el estado global del objetivo de Issue #128 es **PARCIAL EN COMPONENTES, NO IMPLEMENTADO COMO FLUJO E2E DEMOSTRADO**.

## 2. Evidencia observada en el repositorio

| Capacidad | Evidencia en `main` | Estado de auditoría | Límite demostrado |
|---|---|---|---|
| Captura histórica OHLCV | `scripts/market_selection/capture_binance_spot_ohlcv.py`; `tests/market_selection/test_capture_binance_spot_ohlcv.py` | Parcial, existe prototipo | Adaptador Binance Spot. Lee cuerpos completos por bloques hasta EOF y preserva bytes/hash; paginación limitada por el contrato del endpoint. No demuestra proveedor histórico universal ni captura de todas las clases de datos. |
| Perfil de riesgo OHLCV | `scripts/market_selection/analyze_ohlcv_risk_profile.py`; pruebas asociadas | Parcial, descriptivo | Métricas derivadas de velas y calidad de serie. No estima por sí solo riesgo fundamental, on-chain, causalidad, ni rentabilidad esperada. |
| Detección de movimientos | `scripts/market_selection/detect_ohlcv_movement_events.py`; `tests/market_selection/test_detect_ohlcv_movement_events.py` | Parcial, descriptivo | Detecta eventos parametrizados de retorno y volumen sobre velas cerradas. La atribución causal queda `NOT_ESTABLISHED`; no busca noticias ni identifica causas externas. |
| Soporte/resistencia | `scripts/market_selection/analyze_support_resistance.py`; `tests/market_selection/test_analyze_support_resistance.py` | Parcial, heurístico | Detecta pivotes y zonas con parámetros explícitos, confirma pivotes tras velas posteriores y conserva tiempos de disponibilidad. No garantiza reacción del precio ni está integrado en un informe completo por horizonte. |
| Evaluación de captura pública | `scripts/market_selection/evaluate_capture.py`; pruebas de captura/evaluación | Parcial, escenario específico | Evalúa un artefacto de mercado de referencia con identidad Spot Binance/Pionex, spread, profundidad y slippage parametrizados. Declara límites del snapshot y devuelve `INDETERMINATE` sin política aprobada. No evalúa el atractivo de inversión de un activo arbitrario. |
| Historial de evaluaciones | `scripts/market_selection/evaluation_record.py`; `tests/market_selection/test_evaluation_record.py` | Parcial, persistencia local | Registros content-addressed e integridad SHA-256 en filesystem local. No demuestra base de datos central, multiusuario, API, retención, backup/restore o historial de producto operado. |
| Integridad de respuestas | Capturadores públicos, verificadores de hash y `.github/workflows/public-market-metadata-size-tests.yml` | Parcial por adaptador | Hay preservación de cuerpos y pruebas de regresión de respuestas grandes. Se requiere verificar cada adaptador y paginación; no asumir que todos los conectores comparten las mismas garantías. |
| Noticias y detonantes externos | No se identificó conector de noticias/eventos en el árbol de scripts inspeccionado | Brecha | No hay evidencia de ingesta, deduplicación, procedencia, publicación/captura, resolución de entidad ni enlace temporal a movimientos. |
| Fundamentales y on-chain | No se identificó motor/adaptador de análisis fundamental/on-chain | Brecha | No se deben inferir tokenomics, concentración, actividad de red, desbloqueos o métricas de protocolo a partir de OHLCV. |
| Evaluación corto/medio/largo | Los registros permiten un campo `horizon`; no se encontró orquestador de tres horizontes | Brecha de integración | Un campo de horizonte no equivale a metodología aprobada ni a tres resultados independientes comparables. |
| Informe de investigación por activo | No se identificó generador integrado de informe E2E ni frontend/API de producto en el árbol de código inspeccionado | Brecha de producto | Los scripts producen artefactos técnicos separados; no existe evidencia de un flujo de usuario completo ni de un contrato de informe integral. |
| Validación predictiva integrada | Hay pruebas anti-look-ahead locales para eventos y zonas, y documentación sobre evaluación temporal | Parcial | No se ha demostrado un protocolo completo de predicción por horizonte, benchmark, walk-forward, costes, calibración y resultados out-of-sample para el producto. |
| Pruebas end-to-end | Los tests inspeccionados son pruebas unitarias/funcionales de módulos | Brecha | No se encontró una prueba que parta de un identificador de activo y produzca el informe integral con fuentes, tres horizontes, eventos y riesgos. |

## 3. Requisitos existentes que deben reutilizarse

No duplicar ni reemplazar los componentes actuales sin demostrar una razón técnica. El trabajo de integración debe reutilizar y versionar, según corresponda:

- Captura OHLCV y artefactos originales con integridad verificable.
- Contratos de mercado/activo y controles de calidad de datos.
- Detección descriptiva de eventos de precio/volumen.
- Análisis de soportes/resistencias basado en pivotes causales.
- Perfil descriptivo de riesgo y cálculos de liquidez de libros observados.
- Registro local inmutable y comparación conservadora de evaluaciones.
- Estados `PASS`, `FAIL`, `INDETERMINATE` y `NOT_RUN` donde el contrato existente los utilice.

Antes de generalizar un componente, deben revisarse sus esquemas de entrada/salida, limitaciones y pruebas; no asumir compatibilidad solo por compartir JSON.

## 4. Brechas prioritarias

### P0 — Contrato de la investigación integral

Definir esquema versionado de solicitud y resultado: identidad canónica del activo, mercados, intervalo histórico, cobertura, fuentes, parámetros/metodología, tres horizontes, riesgos, eventos, soportes/resistencias, advertencias y referencias de evidencia. Las conclusiones deben tener estados explícitos y permitir abstención.

**Aceptación:** validación de esquema, ejemplos positivos/negativos y prueba de compatibilidad del contrato.

### P1 — Orquestador E2E

Crear un servicio/CLI de investigación que coordine identidad, captura, validación de datos, análisis existentes, investigación de eventos, evaluaciones por horizonte y generación del informe. Debe guardar estado de cada etapa y devolver resultado parcial claramente marcado o error; no declarar éxito integral si una etapa crítica falló.

**Aceptación:** prueba E2E desde activo de entrada hasta informe, con artefactos y versiones registradas.

### P2 — Fuentes de noticias y eventos

Diseñar registro de fuentes permitidas y conectores verificables para noticias, anuncios oficiales, listados/delistados, incidentes, regulación y eventos de protocolo según cobertura. Preservar fuente original, publicación, captura, zona horaria, entidades, relación con el activo, fiabilidad y duplicados. Diferenciar hechos, correlación, hipótesis y causa desconocida.

**Aceptación:** pruebas con noticia anterior/posterior, publicación tardía, fuentes contradictorias, falso positivo y causa desconocida. No declarar causalidad solo por proximidad temporal.

### P3 — Metodología de horizontes

Definir y versionar la duración y la metodología de corto/medio/largo plazo, sin fijar valores arbitrarios. Para cada horizonte, generar escenarios, evidencia favorable/adversa, riesgos, niveles técnicos, invalidaciones y limitaciones. Mantener separadas calidad de evidencia, riesgo, oportunidad y cualquier puntuación compuesta.

**Aceptación:** configuración versionada, pruebas de contrato, sensibilidad y casos donde los horizontes discrepen o devuelvan `INDETERMINATE`.

### P4 — Fundamentales/on-chain y cobertura

Evaluar qué métricas son aplicables por tipo de activo y cuáles tienen fuentes fiables. Implementar solo conectores con procedencia y licencias/condiciones revisadas. Diferenciar no aplicable, no disponible, no accesible, incompleto y error.

**Aceptación:** diccionario de métricas por categoría, pruebas de unidades/cobertura y ausencia de inferencias silenciosas.

### P5 — Persistencia, API e interfaz

La persistencia local actual es una prueba de concepto. Diseñar la fuente central de verdad, contratos API, identidad de trabajos, historial inmutable, autorización, retención, recuperación y experiencia de usuario después de decidir arquitectura. No declarar que web/móvil existe basándose en scripts Python.

**Aceptación:** pruebas de contrato/integración, comparación de historial y recorrido de usuario; seguridad, backup/restore y observabilidad sujetos a Issue #19.

### P6 — Validación temporal y evidencia de desempeño

Acordar objetivos predictivos, benchmarks y protocolo antes de evaluar señales. Aplicar separación temporal, walk-forward/out-of-sample, controles de leakage/survivorship/data snooping, costes pertinentes y calibración. Conservar resultados negativos y condiciones de invalidez.

**Aceptación:** protocolo y resultados reproducibles, con datos, versión, métricas, intervalos de incertidumbre y limitaciones.

## 5. Matriz requisito → implementación → prueba

| Requisito | Código actual reutilizable | Brecha de integración | Prueba requerida |
|---|---|---|---|
| REQ-P-034 — investigación E2E | Captura OHLCV, evaluadores y registro local | No hay orquestador ni salida integral demostrada | E2E desde entrada de activo hasta informe |
| REQ-P-035 — detonantes con evidencia | Detector descriptivo de movimientos | Falta ingesta y correlación de noticias/eventos | Fuentes temporales, contradicciones y causa desconocida |
| REQ-P-036 — tres horizontes | Registro admite campo `horizon` | Falta metodología versionada y agregador de horizontes | Tres informes separados con escenarios e invalidaciones |
| REQ-P-037 — soportes/resistencias | Analizador de pivotes y pruebas anti-look-ahead | Falta incluir resultados en informe integrado | Test de contrato y E2E |
| REQ-P-038 — captura completa | Capturadores y hashes por fuente | Verificar todos los adaptadores, paginación y reanudación | Respuestas grandes, interrupción, hash y EOF |
| REQ-P-039 — abstención | Estados conservadores en evaluadores de captura | Falta propagar el estado hasta el informe de activo | Datos insuficientes producen `INDETERMINATE` |
| NFR-019 — integridad | SHA-256 y bytes preservados en varios módulos | Cobertura uniforme de todos los conectores por verificar | Regresión por adaptador |
| NFR-020 — validez temporal | Pruebas anti-look-ahead de eventos y zonas | Falta validación temporal integrada para noticias y horizontes | Pruebas point-in-time y walk-forward |
| NFR-021 — explicabilidad | Metadatos de calidad y límites en artefactos existentes | Falta contrato único que enlace cada conclusión con evidencia | Validación de informe y referencias de evidencia |

## 6. Criterios de cierre de esta auditoría

- [ ] Revisar esta matriz contra el código y las pruebas del commit que se vaya a integrar.
- [ ] Cada estado de implementación enlaza archivo, prueba ejecutada y resultado; la ausencia de evidencia se mantiene como brecha.
- [ ] El contrato E2E y los esquemas de artefactos están versionados.
- [ ] El orquestador integra los componentes sin alterar su semántica ni ocultar fallos parciales.
- [ ] Las fuentes de noticias/eventos tienen procedencia temporal y política de evidencia.
- [ ] Cada horizonte usa metodología aprobada/versionada y puede abstenerse.
- [ ] La prueba E2E produce informe, fuentes, datos, logs y hashes reproducibles.
- [ ] La validación fuera de muestra y las puertas de seguridad/operación están documentadas antes de declarar producción.

**Conclusión:** el trabajo debe pasar de prototipos analíticos separados a un producto integrado y validado. No se requiere reemplazar lo que ya funciona; se requiere conectar los componentes, cubrir las fuentes que faltan, formalizar las metodologías y demostrar el resultado con pruebas reproducibles.
