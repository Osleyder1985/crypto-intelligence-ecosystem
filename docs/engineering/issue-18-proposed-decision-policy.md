# Política adoptada de frescura y coste — Issue #18

- **Estado:** ADOPTADA COMO POLÍTICA BASE DEL MODO DE INVESTIGACIÓN PÚBLICA SPOT.
- **Alcance:** análisis comparativo público y reproducible; no evalúa rentabilidad personalizada de una cuenta ni autoriza ejecución.
- **Fecha:** 2026-10-22 UTC.
- **Ámbito:** comparación analítica de mercados Spot con datos públicos. No habilita ejecución de órdenes.
- **Regla de gobierno:** no inventar umbrales ni atribuirlos a ISO, Binance o Pionex cuando sus fuentes no los prescriben.

## 1. Frescura y semántica temporal

### Captura de timestamps

- Conservar por separado: timestamp de evento/actualización de origen, timestamp de respuesta del proveedor, inicio de petición, captura local UTC, unidad original, endpoint, símbolo y SHA-256 de la respuesta.
- Normalizar milisegundos/microsegundos solo después de identificar explícitamente la unidad. No comparar timestamps con unidades diferentes.
- Medir y conservar RTT y la incertidumbre del reloj local. La hora de recepción no equivale al tiempo del evento de mercado.
- Pionex Spot depth expone `data.updateTime` y un timestamp superior de respuesta. Los 21 deltas observados en esta muestra corta (response−updateTime: 161–416 ms; captura−response: 13–114 ms) son descriptivos, no un SLA.
- Binance Spot REST depth expone `lastUpdateId`, que es un ID de secuencia, no un timestamp de evento. Por sí solo no permite calcular edad temporal absoluta. Si se necesita frescura temporal de Binance, usar snapshot REST sincronizado con eventos WebSocket documentados y conservar `E`, `U`, `u` y la evidencia de sincronización.

### Estados

- **PASS:** solo si hay timestamp de origen semánticamente definido, timestamp válido, reloj con incertidumbre conocida, sincronización de libro válida cuando corresponda, y el intervalo de edad medido queda dentro de un límite aprobado por el producto.
- **FAIL:** solo si los datos son demostrablemente obsoletos bajo ese límite aprobado, teniendo en cuenta la incertidumbre del reloj.
- **INDETERMINATE:** timestamp ausente/malformado/futuro, unidad no identificada, sincronización rota, incertidumbre de reloj desconocida, intervalo que cruza el límite, límite no aprobado o fuente REST sin timestamp de evento suficiente.
- **No existe valor predeterminado numérico.** `max_age_ms` debe permanecer sin configurar hasta que el producto defina horizonte operativo y riesgo tolerable. Los límites de fixtures son sintéticos y solo prueban ramas de código.

## 2. Comisiones y coste

- Para investigación comparativa pública, mostrar maker/taker de la tarifa base pública por venue con URL oficial, fecha de consulta, nivel de referencia y condiciones. No presentarlas como la tarifa efectiva del usuario.
- Si el resultado debe representar una cuenta concreta, exigir evidencia privada autorizada: Binance `GET /api/v3/account/commission`; Pionex, fills históricos con `fee`/`feeCoin` como evidencia retrospectiva, sin tratarlos como garantía de la próxima operación.
- Si la comisión se paga en un activo distinto del activo cotizado, no convertirla sin un precio de conversión verificable y con timestamp; en caso contrario, coste total `INDETERMINATE`.
- Incluir coste de retiro/red solo cuando el flujo de producto transfiera activos entre exchanges; en ese caso, exigir moneda, red, mínimo y tarifa oficial vigentes.
- Coste visible por fill = desviación VWAP frente al mid (spread e impacto incluidos) + comisión de referencia o efectiva aplicable. Para round-trip, sumar los dos lados y ambas comisiones. Una simulación de snapshot estático no garantiza que los dos lados sigan disponibles.

## 3. Tamaño de escenario

- No fijar un nominal típico sin requisito del producto.
- Publicar curvas acumuladas de todos los niveles devueltos para compra y venta; indicar profundidad visible y el límite del snapshot.
- El escenario de frontera por mínimos públicos es solo auxiliar. La unidad de Pionex `minAmount` no está definida inequívocamente por el esquema público, por lo que no se usa para declarar una orden admisible. Preservar los campos literalmente y mantener `order_size_eligibility=INDETERMINATE`.
- Solo un tipo de orden y tamaño definidos permiten comprobar filtros aplicables y calcular un escenario de coste concreto.

## 4. Regla de decisión global

La decisión económica global solo podrá ser distinta de `INDETERMINATE` cuando todos los datos críticos del escenario elegido estén disponibles: frescura demostrable según política aprobada, tarifa aplicable al modo de análisis, profundidad suficiente, filtros del tipo/tamaño de orden, y costes de transferencia cuando correspondan. Un resultado PASS técnico no equivale a una oportunidad rentable ni a una orden autorizada.

## 5. Fuentes oficiales

- [ISO 8601-1:2019](https://www.iso.org/standard/70907.html), revisada/confirmada en 2024, y [enmienda 1:2022](https://www.iso.org/standard/81801.html): representación/intercambio de fechas y horas; no prescribe un SLA de frescura para estos exchanges. El borrador ISO/CD 8601-1 en desarrollo no se trata como norma publicada vigente.
- [ISO/IEC 25012:2008](https://www.iso.org/standard/35736.html), confirmada por ISO en 2025: modelo general de calidad de datos; no fija un umbral universal de frescura para este producto.
- [Binance Spot REST API](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md): profundidad REST y `lastUpdateId`.
- [Binance WebSocket streams](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md): timestamps de eventos e IDs para sincronizar el libro.
- [Binance Commission FAQ](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md): consulta de comisiones por símbolo.
- [Pionex common symbols](https://www.pionex.com/docs/api-docs/trade-api/common): campos de restricciones públicas de símbolo.
- [Pionex depth endpoint](https://www.pionex.com/docs/api-docs/trade-api/market): timestamp de respuesta y `data.updateTime`.
- [Pionex authentication](https://www.pionex.com/docs/api-docs/trade-api/general-info/authentication): firma y permisos read-only.

## Aprobación pendiente

Esta es una propuesta de política fail-closed, no una aprobación. Para aprobarla, el responsable del producto debe confirmar que el alcance es comparación pública Spot y decidir si la evaluación debe representar tarifas base públicas o costes personalizados por cuenta. Si se requiere un límite de frescura numérico o un tamaño típico, debe definirse y justificarse antes de evaluar el resultado; no se inferirá de esta muestra.
