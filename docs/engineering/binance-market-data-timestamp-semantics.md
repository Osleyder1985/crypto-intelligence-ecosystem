# Semántica temporal de Binance Spot para la evaluación de frescura

- **Estado:** evidencia documental técnica; no es una política de frescura aprobada.
- **Issue:** [#18 — Definir política verificable de frescura, comisiones y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Fecha de consulta de las fuentes:** 2026-10-22.
- **Alcance:** Binance Spot API pública. No extrapolar estas conclusiones a Pionex u otros proveedores.

## Semántica documentada oficialmente

1. **Unidad de tiempo.** La documentación general de Binance Spot indica que los campos temporales y timestamps de las respuestas JSON están expresados en milisegundos por defecto; se puede solicitar microsegundos mediante el encabezado X-MBX-TIME-UNIT. La unidad debe registrarse junto con el dato para evitar conversiones ambiguas.
2. **Eventos de profundidad por WebSocket.** Un evento depthUpdate contiene E (hora del evento), U (primer ID de actualización) y u (último ID de actualización). La documentación describe la continuidad por IDs: si U es mayor que el ID local más uno, se han perdido eventos y se debe descartar/reconstruir el libro. Los IDs prueban continuidad del flujo según ese protocolo; por sí solos no expresan antigüedad en segundos.
3. **Snapshot REST de profundidad.** La respuesta de GET /api/v3/depth incluye lastUpdateId, bids y asks; no contiene un timestamp de origen del snapshot en su esquema documentado. Por tanto, no puede calcularse una edad de snapshot a partir de esa respuesta sola. La hora local de recepción/captura es una observación distinta y no debe sustituir a un timestamp de origen ausente.
4. **Eventos de trades.** En el stream @trade, E es la hora del evento y T es la hora del trade. Son campos con semánticas distintas; la evaluación debe conservar cuál de ellos usa y por qué. No asumir que el timestamp de evento equivale a la hora de captura del cliente.
5. **Tiempo del servidor.** El endpoint de tiempo del servidor puede aportar una referencia de reloj para comparar con el reloj del cliente, pero una medición de ida y vuelta introduce incertidumbre de transporte. Conservar muestras, RTT y método de cálculo; no presentar una estimación como verdad exacta.

## Implicaciones para el evaluador

- Conservar por separado, cuando estén disponibles: timestamp de origen/evento, hora de recepción/captura UTC, hora de evaluación UTC, unidad temporal, endpoint/stream, símbolo, IDs de actualización y evidencia de sincronización.
- Si la fuente no entrega timestamp de origen para el dato, marcar la frescura temporal como INDETERMINATE; no inferirla de la hora de captura ni del hash.
- Si los timestamps necesarios son futuros, inválidos, carecen de zona/unidad interpretable o son incoherentes, no declarar PASS.
- No fijar aquí un límite numérico de edad, lag o desviación de reloj. Las fuentes citadas describen campos y protocolo, pero no establecen un umbral universal de frescura para este caso de uso. Cualquier umbral interno requiere contexto de producto, mediciones reproducibles, evaluación de riesgo, responsable, versión y aprobación explícita.
- Una prueba de continuidad del libro y una prueba de frescura son dimensiones diferentes: superar una no implica superar la otra.

## Fuentes oficiales

- [Binance Spot — General REST API Information](https://developers.binance.com/en/docs/products/spot/rest-api): unidades de timestamps, endpoints y comportamiento general de API.
- [Binance Spot — WebSocket Streams](https://developers.binance.com/en/docs/products/spot/web-socket-streams): estructura de depthUpdate, campos E, U, u y procedimiento de sincronización del libro.
- [Binance Spot — REST API Market Data endpoints](https://developers.binance.com/en/docs/products/spot/rest-api/market-data-endpoints): esquema del snapshot de profundidad y campo lastUpdateId.
- [Binance Spot — WebSocket API: Time](https://developers.binance.com/en/docs/products/spot/web-socket-api/general-api-information): referencia del reloj del servidor, cuando aplique.

## Limitaciones de la evidencia

Esta nota interpreta documentación pública; no demuestra la frescura de una captura concreta ni aprueba la política de producto. La semántica de timestamps de Pionex sigue pendiente de verificación con su documentación oficial específica. Las tasas de comisión, la profundidad parcial y la ausencia de un tamaño de orden aprobado siguen impidiendo calcular un coste total concluyente. El resultado global del Issue #18 debe permanecer INDETERMINATE hasta que se satisfagan sus demás criterios.
