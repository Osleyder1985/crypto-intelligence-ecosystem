# Issue #18 — Registro de decisiones pendientes y protocolo de evidencia

**Estado:** propuesta técnica; no aprobada para producción.  
**Issue:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18  
**Alcance:** captura pública de mercado y evaluación offline. No autoriza trading ni garantiza ejecución.

## Principios no negociables

1. La hora de captura UTC y el timestamp del evento de mercado son campos distintos. Nunca inferir el segundo a partir del primero.
2. Un hash válido demuestra integridad de los bytes preservados, no frescura, veracidad económica ni aplicabilidad de una tarifa.
3. No asumir una comisión de cero si no existe evidencia oficial, vigente y aplicable a la cuenta y al tipo de operación evaluados.
4. No convertir un dato ausente, inválido, vencido o no comparable en un resultado positivo. Usar `INDETERMINATE` cuando la evidencia no permita concluir.
5. Los límites cuantitativos deben aprobarse antes de observar los resultados que se evaluarán con ellos; no ajustarlos retrospectivamente para favorecer un activo o proveedor.

## Registro de decisiones que requieren aprobación del propietario

| ID | Decisión | Evidencia necesaria | Mientras siga pendiente |
|---|---|---|---|
| D18-01 | Umbral de frescura por proveedor y tipo de dato | Semántica documentada del timestamp de origen, granularidad y limitaciones oficiales | `source_freshness=INDETERMINATE` |
| D18-02 | Tolerancia de reloj y tratamiento de timestamps futuros | Supuesto operativo explícito, fuente de sincronización y escenarios de prueba | Timestamp futuro o no interpretable no puede pasar |
| D18-03 | Tratamiento de timestamp ausente o malformado | Contrato del proveedor y fixtures reproducibles | `source_freshness=INDETERMINATE` |
| D18-04 | Fuente y aplicabilidad de comisiones | Página/API oficial, fecha de consulta, maker/taker, nivel de cuenta, mercado y condiciones | `fees=INDETERMINATE` |
| D18-05 | Antigüedad máxima aceptable de la evidencia de tarifas | Política de revalidación y detección de tarifas obsoletas | No usar tarifas obsoletas como verificadas |
| D18-06 | Escenarios y tamaños de orden de referencia | Universo de pares, tamaños/unidades, lado de operación y objetivo de comparación | No presentar coste total comparable |
| D18-07 | Tratamiento de profundidad incompleta | Límites de profundidad de cada fuente y escenarios fuera del libro observado | Coste/slippage no extrapolable; resultado indeterminado cuando afecte a la conclusión |

Este registro no fija valores de frescura, tolerancia, tamaños ni tarifas. La aprobación debe registrar responsable autorizado, fecha UTC, justificación y versión de la política.

## Contrato mínimo de evidencia de tarifas

Cada evidencia de tarifa debería identificar, cuando la fuente lo permita:

- Proveedor y mercado/par aplicable.
- URL o identificador de la fuente oficial y hora de consulta UTC.
- Tipo de operación: maker o taker; spot frente a otros productos.
- Nivel de cuenta, descuentos, token de descuento y condiciones relevantes.
- Unidad, moneda, vigencia o fecha efectiva, y respuesta original preservada con hash.
- Estado de validación: `PASS`, `FAIL` o `INDETERMINATE`, con motivo legible.

Si un atributo esencial no puede verificarse, no etiquetar la tarifa como verificada. Una tarifa publicada públicamente puede no ser la tarifa efectiva de una cuenta concreta.

## Contrato de coste total

La estimación debe declarar su alcance y supuestos e incluir, cuando sean aplicables y exista evidencia suficiente:

- Spread observado.
- Slippage estimado respecto al tamaño de orden explícito.
- Comisiones de compra/venta aplicables.
- Costes adicionales relevantes, diferenciando trading, retiro y transferencia cuando corresponda.
- Profundidad observada, límite de niveles, hora de captura y limitaciones de liquidez.

No sumar magnitudes incompatibles ni tratar un libro parcial como garantía de ejecución. Si la profundidad disponible no cubre el escenario o falta un componente material del coste, el coste total será `INDETERMINATE`.

## Matriz mínima de pruebas

| Caso | Resultado esperado |
|---|---|
| Timestamp de evento ausente | Frescura `INDETERMINATE` |
| Timestamp malformado | No pasa; `INDETERMINATE` o rechazo de entrada según el contrato |
| Timestamp futuro más allá de tolerancia aprobada | No pasa |
| Dato más antiguo que el límite aprobado | Frescura `FAIL` |
| Tarifa desconocida o no aplicable a la cuenta/mercado | Tarifas y coste total `INDETERMINATE` |
| Evidencia de tarifa obsoleta | No usar como tarifa verificada |
| Tarifa cero sin evidencia oficial aplicable | No tratar como comisión cero verificada |
| Profundidad insuficiente para el tamaño de referencia | Coste/slippage indeterminado; no extrapolar |
| Hash o bytes de captura inconsistentes | Rechazar artefacto |
| Todos los componentes tienen evidencia suficiente | Calcular solo dentro del alcance y supuestos declarados |

Los umbrales y la clasificación exacta `FAIL` frente a `INDETERMINATE` deben quedar alineados con el contrato del evaluador y aprobarse antes de cerrar el Issue.

## Condiciones de cierre del Issue #18

- [ ] Decisiones D18-01 a D18-07 aprobadas y versionadas.
- [ ] Capturador conserva por separado el timestamp de origen y el de captura, cuando estén disponibles.
- [ ] Tarifas proceden de fuentes oficiales y su aplicabilidad está documentada.
- [ ] Fixtures cubren datos ausentes, obsoletos, inválidos y profundidad insuficiente.
- [ ] Pruebas reproducibles ejecutadas en el commit identificado y resultados CI registrados.
- [ ] Un ejemplo de evidencia incompleta produce `INDETERMINATE`.
- [ ] Informe de evaluación declara versiones, configuración, límites y componentes no evaluables.

**Limitación:** este documento organiza las decisiones y pruebas pendientes. No es aprobación económica, no prueba por sí solo la implementación y no demuestra preparación para producción ni conformidad ISO.


## Hallazgo técnico verificado: contrato temporal del libro

El capturador actual consulta un snapshot REST de profundidad de Binance (/api/v3/depth). El artefacto conserva la hora local de captura, mientras que el payload de profundidad contiene lastUpdateId; el proyecto no debe interpretar ese identificador de secuencia como un timestamp. Por eso los campos source_event_at_utc, source_timestamp_field y source_timestamp_semantics quedan explícitamente vacíos y la frescura sigue siendo INDETERMINATE.

La documentación oficial de Binance describe un flujo WebSocket de diferencias de profundidad (<symbol>@depth) cuyos eventos incluyen E (event time) y los identificadores de actualización U/u. Referencia: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#diff-depth-stream. Esto identifica una vía técnica posible, pero no autoriza a asignar automáticamente E al snapshot REST existente.

### Contrato propuesto para una futura implementación

1. Verificar el contrato vigente de producción de Binance y la semántica exacta de E, U y u antes de codificarlo.
2. Construir un libro local coherente siguiendo el procedimiento oficial de sincronización entre snapshot REST y eventos WebSocket; registrar el último evento aplicado y detectar huecos/reconexiones.
3. Preservar separadamente el tiempo de recepción UTC del cliente, el timestamp del evento del proveedor, el campo de origen y su semántica documentada.
4. Marcar el libro como no confiable tras una pérdida de secuencia o reconexión hasta resincronizarlo. No inferir frescura solo porque siga llegando tráfico de red.
5. Añadir fixtures reproducibles para evento ausente/malformado, timestamp futuro, lag excesivo, secuencia perdida, reconexión y libro no sincronizado.
6. Mantener source_freshness=INDETERMINATE hasta que el contrato y los límites D18-01/D18-02 estén aprobados.

Esta alternativa requiere un capturador de libro incremental y pruebas de sincronización; no es un cambio de una sola línea en el evaluador actual. Los límites cuantitativos siguen pendientes y no se fijan en este documento.
