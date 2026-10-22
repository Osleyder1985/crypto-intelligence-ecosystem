# Semántica temporal de los datos públicos de mercado: Binance Spot y Pionex Spot

- **Estado:** evidencia documental técnica; no es una política de frescura aprobada.
- **Issue:** [#18 — Definir política verificable de frescura, comisiones y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Fecha de consulta de las fuentes:** 2026-10-22.
- **Alcance:** endpoints públicos de mercado documentados por Binance Spot y Pionex. No extrapolar a otros productos ni a endpoints no descritos aquí.

## Binance Spot

1. **Unidad de tiempo.** La documentación general indica que los campos temporales y timestamps de respuestas JSON están expresados en milisegundos por defecto; se pueden solicitar microsegundos mediante el encabezado X-MBX-TIME-UNIT. La unidad debe registrarse junto con cada dato para evitar conversiones ambiguas.
2. **Eventos de profundidad por WebSocket.** Un evento depthUpdate contiene E (hora del evento), U (primer ID de actualización) y u (último ID de actualización). La documentación describe la continuidad por IDs: si U es mayor que el ID local más uno, se han perdido eventos y se debe descartar/reconstruir el libro. Los IDs prueban continuidad del flujo según ese protocolo; por sí solos no expresan antigüedad en segundos.
3. **Snapshot REST de profundidad.** El esquema documentado de GET /api/v3/depth incluye lastUpdateId, bids y asks, pero no un timestamp de origen. No puede calcularse la edad del snapshot a partir de esa respuesta sola. La hora local de recepción/captura es una observación distinta y no sustituye un timestamp de origen ausente.
4. **Eventos de trades.** En el stream @trade, E es la hora del evento y T la hora del trade. Son campos distintos; la evaluación debe conservar cuál utiliza y por qué.
5. **Reloj del servidor.** El endpoint de tiempo puede aportar una referencia para comparar el reloj del cliente, pero una medición de ida y vuelta introduce incertidumbre de transporte. Conservar muestras, RTT y método de cálculo; no presentar una estimación como verdad exacta.

## Pionex Spot

1. **Unidad y envoltura REST.** La documentación general REST describe el campo superior timestamp como timestamp de respuesta en milisegundos. Esto no lo convierte automáticamente en el instante en que se generó el dato de mercado incluido en data.
2. **Libro de órdenes REST.** GET /api/v1/market/depth documenta data.updateTime como timestamp de actualización en milisegundos, separado del timestamp superior de la respuesta. Para evaluar el libro, preservar ambos campos con sus nombres originales, la hora de captura UTC y la unidad.
3. **Trades REST y WebSocket.** La documentación de trades describe el campo timestamp como la hora de ejecución/fill del trade, en milisegundos. No confundir esa hora con la hora de recepción del mensaje. En los mensajes WebSocket también aparece un timestamp a nivel de mensaje; conservarlo separado del timestamp de cada trade.
4. **Límites.** La documentación consultada identifica el significado y unidad de los campos, pero no prescribe un umbral universal de edad del libro para esta decisión analítica. Tampoco demuestra la latencia real de una captura concreta.

## Implicaciones para el evaluador

- Conservar por separado, cuando estén disponibles: timestamp de origen/evento, timestamp de respuesta o envoltura, hora de recepción/captura UTC, hora de evaluación UTC, unidad temporal, endpoint/stream, símbolo e IDs de actualización.
- No sustituir timestamp de origen por la hora de captura, ni por el timestamp de la envoltura, sin una justificación específica del contrato de datos.
- Si no existe timestamp de origen interpretable para la dimensión evaluada, la frescura temporal debe quedar INDETERMINATE; no inferirla de un hash ni de una respuesta HTTP correcta.
- Si los timestamps necesarios son futuros, inválidos, carecen de unidad interpretable o son incoherentes, no declarar PASS.
- No fijar aquí un límite numérico de edad, lag o desviación de reloj. Las fuentes citadas describen campos y protocolos, pero no establecen un umbral universal para este caso de uso. Cualquier umbral interno requiere contexto de producto, mediciones reproducibles, evaluación de riesgo, responsable, versión y aprobación explícita.
- Una prueba de continuidad del libro y una prueba de frescura son dimensiones diferentes: superar una no implica superar la otra.

## Fuentes oficiales de proveedores

- [Binance Spot — General REST API Information](https://developers.binance.com/en/docs/products/spot/rest-api): unidades de timestamps y comportamiento general de API.
- [Binance Spot — WebSocket Streams](https://developers.binance.com/en/docs/products/spot/web-socket-streams): estructura de depthUpdate, campos E, U, u y sincronización del libro.
- [Binance Spot — REST API Market Data endpoints](https://developers.binance.com/en/docs/products/spot/rest-api/market-data-endpoints): esquema del snapshot de profundidad y campo lastUpdateId.
- [Pionex — REST Basic Info](https://pionex-doc.gitbook.io/apidocs/restful/general/basic): timestamp de respuesta y unidad.
- [Pionex — Get Depth](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth): updateTime del libro de órdenes.
- [Pionex — Get Trades](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-trades): timestamp de ejecución de trades.
- [Pionex — WebSocket General Info](https://pionex-doc.gitbook.io/apidocs/websocket/general-info): envoltura de mensajes, timestamp y flujo público.
- [Pionex — WebSocket Trade](https://pionex-doc.gitbook.io/apidocs/websocket/public-stream/trade): timestamp de trades transmitidos.

## Limitaciones de la evidencia

Esta nota interpreta documentación pública; no demuestra la frescura de una captura concreta ni aprueba la política de producto. Las tarifas aplicables a la cuenta, la profundidad parcial y la ausencia de un tamaño de orden aprobado siguen impidiendo calcular un coste total concluyente. El resultado global del Issue #18 debe permanecer INDETERMINATE hasta que se satisfagan sus demás criterios.
