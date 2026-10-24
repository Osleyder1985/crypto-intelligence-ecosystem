# Issue #132 — Alcance de datos de mercado para asociación temporal

## Objetivo

Vincular un evento regulatorio real con episodios técnicos observados en velas históricas, sin inferir causalidad ni convertir el resultado en recomendación de inversión.

## Fuente y alcance

- **Proveedor:** Binance Spot, únicamente datos públicos de mercado.
- **Endpoint documentado:** `https://data-api.binance.vision/api/v3/klines`.
- **Documentación oficial:** https://developers.binance.com/en/docs/products/spot/rest-api
- **Evidencia exacta registrada:** “For APIs that only send public market data, please use the base endpoint https://data-api.binance.vision.”
- **SHA-256 del extracto UTF-8:** `7b98e2a2961eceab65592628930600a9c6681651637031ba9fae6dc4604a6cc1` (hash del extracto almacenado, no de la página completa).
- **Captura automatizada de la documentación:** el endpoint devolvió HTTP 202 en el runner; el manifiesto registra `AUTOMATION_CHALLENGE` y revisión manual pendiente. El cuerpo del desafío no se acepta ni se conserva como texto de política. No se afirma que exista un snapshot íntegro de la página Binance.
- **Casos de uso del proyecto:** análisis interno y persistencia de informes derivados. No se autoriza redistribución de datos OHLCV sin procesar ni ejecución de operaciones.
- **Persistencia:** el payload de velas y las respuestas HTTP permanecen solo en memoria durante el análisis. El informe derivado conserva endpoint, ventana solicitada, timestamps, códigos HTTP, tamaños y hashes de respuesta, configuración, episodios y evaluación temporal; no guarda las filas de velas ni sus cuerpos base64.
- **Límite jurídico:** la documentación identifica el endpoint público; no se interpreta como una licencia general de redistribución ni como dictamen jurídico. El registro es una decisión técnica del proyecto, con alcance restringido.

## Ventana histórica y método

Para el evento CFTC del 29 de mayo de 2026 se captura BTCUSDT en intervalo de una hora desde 14 días naturales antes hasta 14 días naturales después de la fecha publicada. El intervalo simétrico sirve para inspección retrospectiva de swings próximos; no es una ventana causal validada ni un horizonte de inversión.

La segmentación de pivotes usa `configs/technical-descriptive-baseline.json`, cuyo estado es experimental/no aprobado. El resultado se conserva como descripción exploratoria y no se utiliza para señales, predicciones ni decisiones de compra/venta.

## Controles temporales

- El evento se relaciona mediante `coingecko_id=bitcoin`, no solo por el ticker.
- La fecha de publicación de la nota CFTC tiene precisión de día, no hora exacta.
- La captura del artículo se realizó después del movimiento histórico; el contrato temporal debe marcarlo como no disponible en el corte histórico del episodio, aunque pueda describir la relación retrospectiva entre la fecha publicada y el swing.
- Los estados `TEMPORAL_ASSOCIATION`, `NOT_AVAILABLE_AT_DECISION_TIME` u otros resultados no implican causalidad.
- `causality_claimed=false` es obligatorio.

## Revisión y límites

La autorización del archivo histórico de CFTC no se hereda al endpoint de datos de mercado, y la autorización de datos de mercado no se hereda a RSS ni a otras fuentes. Cada proveedor, endpoint, uso y modalidad se evalúa por separado. El RSS de CFTC no se consulta mientras su aviso oficial indique que está deshabilitado.
