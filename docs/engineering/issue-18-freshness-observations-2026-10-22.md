# Evidencia de frescura observada — Issue #18

- **Fecha de análisis:** 2026-10-22 UTC.
- **Tipo de evidencia:** mediciones observadas en artefactos CI de captura REST, no umbrales normativos.
- **Estado de decisión:** `INDETERMINATE`.
- **Alcance:** tres ejecuciones independientes; pares BTC_USDT, ETH_USDT y SOL_USDT; Pionex Spot `data.updateTime` y timestamp superior de respuesta.

## Artefactos fuente

| Run CI | Creación del artefacto (UTC) | Resultado de captura | Artefacto |
|---|---|---|---|
| 39725519816 | 2026-10-22 05:00:32.869 | 12/12 registros; PASS | [ZIP de evidencia](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39725519816/artifacts/12402698227) |
| 39725727132 | 2026-10-22 05:02:37.498 | 12/12 registros; PASS | [ZIP de evidencia](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39725727132/artifacts/12403295302) |
| 39726272598 | 2026-10-22 05:08:21.527 | 12/12 registros; PASS | [ZIP de evidencia](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39726272598/artifacts/12402498544) |

Se analizaron los archivos JSON originales `public-market-capture-batch.json` dentro de los ZIP, no solo el resumen impreso en los logs.

## Deltas medidos

`response − updateTime` = timestamp superior de respuesta Pionex menos `data.updateTime`, ambos convertidos a UTC. `captura − response` = hora UTC de captura local menos timestamp superior de respuesta.

| Run CI | Par | response − updateTime (ms) | captura − response (ms) | Niveles bid/ask Pionex |
|---|---|---:|---:|---:|
| 39725519816 | BTC_USDT | 296 | 21 | 999 / 999 |
| 39725519816 | ETH_USDT | 167 | 22 | 999 / 999 |
| 39725519816 | SOL_USDT | 393 | 13 | 1000 / 1000 |
| 39725727132 | BTC_USDT | 416 | 46 | 999 / 999 |
| 39725727132 | ETH_USDT | 211 | 47 | 999 / 999 |
| 39725727132 | SOL_USDT | 231 | 37 | 1000 / 1000 |
| 39726272598 | BTC_USDT | 232 | 20 | 999 / 999 |
| 39726272598 | ETH_USDT | 202 | 19 | 999 / 999 |
| 39726272598 | SOL_USDT | 324 | 13 | 1000 / 1000 |

Resumen descriptivo de las nueve observaciones:
- `response − updateTime`: mínimo 167 ms, máximo 416 ms.
- `captura − response`: mínimo 13 ms, máximo 47 ms.
- Las tres ejecuciones abarcan aproximadamente 7 min 49 s desde la creación del primer al tercer artefacto.

## Qué demuestra y qué no

1. Demuestra que los artefactos conservan por separado timestamp superior de respuesta, timestamp de actualización del libro y captura UTC local, y que estos campos permiten medir deltas observados.
2. No demuestra que `updateTime` equivalga a la edad de todos los niveles, ni que todos los niveles del snapshot hayan cambiado en ese instante.
3. Nueve observaciones de tres pares en un intervalo corto no estiman adecuadamente colas de latencia, degradación por carga, cortes de red, diferencias regionales ni comportamiento de producción. No son suficientes para establecer un SLA universal.
4. La captura REST de Binance usada aquí devuelve `lastUpdateId`, que es un identificador de secuencia, no un timestamp de origen. No se calcula frescura temporal absoluta a partir de él.
5. No se propone un límite numérico de frescura a partir de esta muestra. Los límites de prueba sintéticos usados en fixtures solo verifican ramas de código y no son configuración de producto.
6. Para aprobar una política interna se necesita definir el horizonte de uso y el riesgo tolerable, ampliar las mediciones en ventanas y condiciones representativas, y documentar responsable, versión y referencia de aprobación. Hasta entonces, la frescura absoluta y la decisión económica siguen `INDETERMINATE`.

## Referencias de semántica oficial

- [Binance Spot REST API — profundidad](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md): el snapshot contiene `lastUpdateId`, bids y asks; no un timestamp de evento en ese esquema.
- [Binance WebSocket streams — procedimiento para reconstruir libro](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md): la sincronización usa IDs de actualización `U`/`u` y documenta que el snapshot tiene un límite de niveles.
- [Pionex Get Depth](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth): referencia del endpoint de profundidad y su campo de actualización.

Esta evidencia es una medición técnica del comportamiento observado en los artefactos, no una declaración de conformidad ISO ni garantía de ejecución.
