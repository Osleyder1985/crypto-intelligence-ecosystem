# Propuesta de política de frescura, comisiones y coste total

- **Issue:** [#18 — Política verificable de frescura, comisiones y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18)
- **Estado:** propuesta técnica para decisión; no aprobada.
- **Fase:** 2 — Investigación de mercados y fuentes.
- **Prioridad:** P1.
- **Regla de seguridad analítica:** mientras falte una decisión o evidencia esencial, el resultado económico permanece `INDETERMINATE`; no se sustituye la ausencia por cero ni se infiere frescura a partir de la hora de captura.

## 1. Objetivo y alcance

Establecer un contrato auditable para determinar si los datos son suficientemente recientes para una evaluación definida y si existe evidencia suficiente para calcular un coste de operación estimado. Esta política no garantiza que una orden vaya a ejecutarse al precio calculado y no habilita envío de órdenes.

## 2. Modelo de tiempo y procedencia

Cada registro de datos debe conservar, cuando esté disponible:

| Campo | Regla |
|---|---|
| `provider`, `endpoint`, `market_id` | Identificar proveedor, recurso y mercado canónico. |
| `captured_at_utc` | Hora local de captura normalizada a UTC, generada por el capturador. |
| `source_event_at_utc` | Timestamp del evento del proveedor, solo si existe y su semántica está documentada. |
| `source_timestamp_field` | Nombre exacto del campo original o `null`. |
| `source_timestamp_semantics` | Documentación de qué representa el timestamp: evento, publicación, actualización del libro u otro. |
| `clock_source` / `clock_sync_status` | Evidencia de la fuente de reloj y del estado de sincronización del entorno, si está disponible. |
| `raw_payload_sha256` | Hash del payload original preservado, cuando sea posible. |
| `parser_version` / `schema_version` | Versiones necesarias para reproducir el parseo y la evaluación. |

No se debe renombrar la hora de captura como hora del evento. Si el proveedor no ofrece timestamp de origen, la frescura del evento no puede certificarse a partir del timestamp de captura por sí solo.

## 3. Cálculo de antigüedad

Cuando exista un timestamp de origen con semántica verificada:

`age_seconds = captured_at_utc - source_event_at_utc`

Antes de evaluar antigüedad, validar formato, zona horaria, parseo y coherencia temporal. Un timestamp futuro respecto de la captura debe quedar como `INDETERMINATE` y generar una razón diagnóstica; no se debe convertir silenciosamente la antigüedad a cero.

Cuando no exista timestamp de origen, el resultado de frescura es `INDETERMINATE`, salvo que una política específica para ese endpoint haya sido aprobada por el responsable y documente una fuente alternativa de evidencia. La hora de captura sigue registrándose por separado.

## 4. Parámetros que requieren decisión autorizada

No asignar valores numéricos hasta que el propietario apruebe la política. La decisión debe registrar valor, unidad, alcance, racional, responsable y fecha.

| Parámetro | Ámbito de decisión | Estado |
|---|---|---|
| Edad máxima admisible | Por proveedor y tipo de dato (ticker, trades, libro, metadatos) | Pendiente de aprobación |
| Tolerancia de desfase del reloj | Por entorno/capturador y método de sincronización | Pendiente de aprobación |
| Timestamp ausente o inválido | Política de abstención y excepciones explícitas por endpoint | Pendiente de aprobación |
| Timestamp futuro | Tratamiento y condiciones de investigación | Propuesta: `INDETERMINATE` |
| Ventana de captura para comparar fuentes | Por tipo de dato y propósito de comparación | Pendiente de aprobación |
| Profundidad mínima utilizable | Por tamaño/escenario de orden; respetar niveles realmente capturados | Pendiente de aprobación |

No aprobar un umbral después de observar el resultado que pretende clasificar. Los umbrales deben quedar versionados antes de la evaluación y no deben ajustarse retroactivamente para convertir un resultado en PASS.

## 5. Evidencia de comisiones

Cada tarifa utilizada debe incluir:

- Proveedor y URL/documento oficial de origen.
- Fecha y hora de consulta UTC y fecha de vigencia indicada por el proveedor, si se publica.
- Mercado, activo y tipo de operación al que se aplica.
- Tipo de tarifa (maker/taker), nivel de cuenta, descuentos y condiciones que afecten a la cuenta objetivo.
- Unidad, moneda de cobro, precisión y método de cálculo.
- Hash o copia preservada permitida por los términos de la fuente; si no se puede preservar el contenido, registrar metadatos y limitación.
- Estado de verificación, versión del parser y fecha de próxima revisión definida por la política aprobada.

No usar una tarifa genérica del exchange como si estuviera confirmada para la cuenta del usuario. Si no se puede verificar el nivel de cuenta o las condiciones aplicables, las comisiones y el coste total quedan `INDETERMINATE`.

## 6. Contrato de coste total estimado

Para cada escenario explícito, el expediente debe separar como mínimo:

1. Valor nocional de referencia y tamaño de orden, con moneda/unidad.
2. Spread observado en el snapshot.
3. Slippage estimado para el tamaño y lado indicados, identificando niveles disponibles y cualquier insuficiencia de profundidad.
4. Tarifa maker/taker aplicable y evidencia que la sustenta.
5. Otros costes aplicables al escenario (por ejemplo, retiro, conversión o red) solo cuando formen parte del propósito de comparación y existan fuentes verificables.
6. Componentes excluidos, supuestos, redondeos y limitaciones.
7. Versión de la fórmula, configuración aprobada, resultado y estado por dimensión.

No sumar componentes incompatibles ni presentar costes de trading como coste completo si faltan componentes esenciales para el escenario. El resultado es una estimación del snapshot, no una garantía de precio ni una recomendación de inversión.

## 7. Estados de decisión

- **PASS:** evidencia suficiente, política aprobada y vigente, todos los componentes obligatorios válidos para el escenario declarado.
- **FAIL:** evidencia válida demuestra incumplimiento de un criterio aprobado.
- **INDETERMINATE:** falta fuente, timestamp, tarifa aplicable, parámetro aprobado, profundidad suficiente u otra evidencia esencial.
- **NOT_RUN:** el cálculo no se ejecutó.

Una dimensión PASS no convierte la decisión económica completa en PASS. Si frescura o tarifas son esenciales para el escenario y están indeterminadas, la decisión total permanece `INDETERMINATE`.

## 8. Matriz mínima de pruebas

| Caso | Resultado esperado |
|---|---|
| Timestamp de evento ausente | Frescura `INDETERMINATE`; razón explícita |
| Timestamp inválido o zona horaria ambigua | Frescura `INDETERMINATE` |
| Timestamp futuro respecto a la captura | Frescura `INDETERMINATE`; diagnóstico |
| Timestamp antiguo frente a un umbral previamente aprobado | `FAIL` en frescura |
| Timestamp dentro del umbral previamente aprobado | Puede ser `PASS` en frescura, si las demás validaciones pasan |
| Tarifa no disponible o no oficial | Comisiones `INDETERMINATE` |
| Tarifa oficial pero nivel de cuenta no confirmado | Comisiones `INDETERMINATE` |
| Tarifa fuera de vigencia según la política aprobada | Comisiones `INDETERMINATE` hasta verificación actualizada |
| Profundidad insuficiente para el tamaño definido | Slippage/coste `INDETERMINATE` |
| Solo existe spread; faltan tarifas | Spread puede evaluarse por separado; coste total `INDETERMINATE` |
| Mismos artefactos y configuración/versiones | Evaluación reproducible, salvo fuentes externas no preservadas documentadas |

Las pruebas que dependen de umbrales se deben parametrizar con fixtures y valores de prueba aislados; los valores de los tests no constituyen política de producción.

## 9. Decisiones necesarias para aprobar

- [ ] Confirmar proveedores y endpoints dentro del alcance inicial.
- [ ] Revisar semántica oficial de timestamps por endpoint y documentar los casos sin timestamp.
- [ ] Aprobar edades máximas por tipo de dato y tolerancia de reloj.
- [ ] Aprobar tratamiento de datos ausentes, inválidos y futuros.
- [ ] Definir escenarios y tamaños de orden, monedas/unidades y componentes de coste relevantes.
- [ ] Definir cómo se verifica el nivel de cuenta y la vigencia de las tarifas oficiales.
- [ ] Aprobar la política de retención de artefactos y limitaciones de redistribución.
- [ ] Identificar quién aprueba la política y registrar fecha/versión.
- [ ] Ejecutar la suite de pruebas y adjuntar artefactos reproducibles tras la aprobación.

## 10. Límites

Este documento no declara que los parámetros estén aprobados, que los datos actuales sean frescos, que las tarifas de una cuenta estén verificadas, que un mercado sea económicamente apto, ni que el producto esté listo para producción. No envía solicitudes de trading ni órdenes. El cierre de la Issue #18 requiere decisión autorizada, implementación, pruebas y evidencia reproducible.
