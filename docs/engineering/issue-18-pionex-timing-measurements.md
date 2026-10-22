# Medición de timestamps de profundidad Pionex Spot

- **Estado:** evidencia empírica exploratoria; no es una política de frescura aprobada.
- **Issue:** [#18 — Frescura, comisiones y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Fecha de análisis:** 2026-10-22 UTC.
- **Fuente semántica oficial:** [Pionex Get Depth](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-depth).
- **Alcance:** dos capturas puntuales de BTC_USDT, ETH_USDT y SOL_USDT, 20 niveles bid/ask por snapshot.

## Método

La documentación oficial de Pionex describe `data.updateTime` como timestamp de actualización del libro en milisegundos, mientras el campo superior `timestamp` describe la respuesta REST. La captura también registra `captured_at_utc` con el reloj del runner. Se calculan, sin imponer umbrales:

- `response_minus_book_update_ms = source_response_at_utc - source_market_update_at_utc`.
- `capture_minus_book_update_ms = captured_at_utc - source_market_update_at_utc`.
- `capture_minus_response_ms = captured_at_utc - source_response_at_utc`.

La primera diferencia compara dos timestamps del proveedor. Las otras dos combinan el reloj del proveedor con el reloj local y pueden verse afectadas por su desviación. Un delta no negativo no prueba por sí solo que los datos sean suficientemente recientes para el uso del producto.

## Observaciones conservadas

| Ejecución de GitHub Actions | Mercado | Respuesta − actualización | Captura local − actualización | Captura − respuesta | Niveles bid/ask |
|---|---|---:|---:|---:|---:|
| [39724912224](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39724912224) | BTC_USDT | 238 ms | 313 ms | 75 ms | 20 / 20 |
| [39724912224](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39724912224) | ETH_USDT | 311 ms | 385 ms | 74 ms | 20 / 20 |
| [39724912224](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39724912224) | SOL_USDT | 194 ms | 289 ms | 95 ms | 20 / 20 |
| [39725001609](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39725001609) | BTC_USDT | 204 ms | 252 ms | 48 ms | 20 / 20 |
| [39725001609](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39725001609) | ETH_USDT | 145 ms | 193 ms | 48 ms | 20 / 20 |
| [39725001609](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39725001609) | SOL_USDT | 134 ms | 188 ms | 54 ms | 20 / 20 |

Para estas seis observaciones, los rangos fueron: respuesta−actualización **134–311 ms**, captura−actualización **188–385 ms**, captura−respuesta **48–95 ms**. Son rangos descriptivos de una muestra pequeña, no percentiles ni estimaciones de latencia de cola. No deben extrapolarse a otros símbolos, regiones, horas, cargas o endpoints.

## Limitaciones y tratamiento

- Los dos artefactos contienen snapshots puntuales; no son una serie continua ni un histórico de profundidad.
- La profundidad se solicitó con `limit=20`; por tanto, cada snapshot es parcial y no demuestra que una orden de cualquier tamaño sea ejecutable.
- El tiempo de captura local no sustituye al timestamp de origen. La comparación con el reloj local requiere medir y conservar su incertidumbre.
- La documentación pública no prescribe un umbral universal de edad para este caso de uso. No se crea un umbral a partir de estas seis observaciones.
- El evaluador puede publicar los deltas observados como métricas; `source_freshness` sigue `INDETERMINATE` hasta que exista una política aprobada previamente, mediciones representativas y evidencia de sincronización de reloj.
- Estas medidas no determinan las comisiones aplicables ni el coste total de ejecución.

