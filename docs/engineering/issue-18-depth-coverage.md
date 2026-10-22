# Cobertura de profundidad pública — Binance Spot y Pionex Spot

- **Estado:** decisión de captura basada en límites documentados del proveedor; no es una garantía de liquidez ni una política de coste aprobada.
- **Issue:** [#18](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Fecha de consulta:** 2026-10-22 UTC.

## Límites oficiales y parámetros de captura

| Proveedor | Endpoint | Límite usado por el capturador | Límite documentado | Peso documentado / efecto |
|---|---|---:|---:|---|
| Binance Spot | `GET /api/v3/depth` | 5000 niveles | Máximo 5000 | Peso de solicitud 250 para límites 1001–5000 |
| Pionex Spot | `GET /api/v1/market/depth` | 1000 niveles | Rango 1–1000 | La documentación consultada indica peso 1 |

Fuentes oficiales:
- [Binance Spot REST API — Order book](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md)
- [Pionex Get Depth](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth)

## Por qué no se interpreta como “libro completo”

Los límites anteriores son los máximos que permiten esos endpoints, no un máximo de bytes impuesto por el proyecto. Se conserva el cuerpo completo que devuelve el proveedor sin truncarlo por tamaño. Aun así, una respuesta limitada por el parámetro `limit` es un snapshot parcial: no representa niveles más allá del límite, cambios posteriores ni un histórico de profundidad.

Binance documenta `lastUpdateId` como identificador secuencial del snapshot, no como timestamp de evento. Pionex documenta `data.updateTime` en milisegundos; debe conservarse separado del timestamp superior de respuesta y de la captura local. La frescura no se declara `PASS` solo por recibir más niveles o tener un timestamp válido.

## Controles de implementación

- Guardar el parámetro solicitado y el número real de niveles bid/ask recibidos.
- Conservar los bytes completos, SHA-256 y JSON parseado.
- Si el proveedor devuelve menos niveles que los disponibles, no afirmar que el límite se alcanzó; registrar la cantidad observada.
- Aplicar los pesos y límites de tasa documentados; respetar respuestas 429/418 y `Retry-After`, sin reintentos agresivos.
- No extrapolar slippage más allá de la profundidad recibida. Si una orden de referencia supera el libro observado, cantidad no cubierta y slippage completo quedan indeterminados.
- No fijar tamaños de orden ni umbrales de frescura a partir de la profundidad observada.

