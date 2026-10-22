# Issue #7 — observaciones de volumen cotizado 24 h

El capturador `scripts/market_selection/capture_multi_exchange_spot_ticker_probe.py` consulta los tickers Spot públicos de Binance, OKX, Bybit, MEXC, Gate, Bitget y Pionex para BTC/USDT, ETH/USDT y SOL/USDT. Cada respuesta se conserva completa, con SHA-256, bytes, timestamp de captura y timestamp de origen cuando la fuente lo documenta. No usa credenciales ni coloca órdenes.

## Métrica y semántica

| Venue | Campo de volumen cotizado | Límite semántico |
|---|---|---|
| Binance | `quoteVolume` | Volumen del activo cotizado en la ventana móvil de 24 h. |
| OKX | `volCcy24h` | Volumen en moneda cotizada para Spot; conservar la unidad y contrato de fuente. |
| Bybit | `turnover24h` | Importe/turnover de Spot; endpoint puede ser inaccesible desde algunos entornos. |
| MEXC | `quoteVolume` | La documentación permite que sea `null`; no sustituir ausencia por cero. |
| Gate | `quote_volume` | Turnover en moneda cotizada. |
| Bitget | `turnover24h` | Turnover Spot en la moneda cotizada. |
| Pionex | `amount` | Importe total negociado de 24 h; el contrato del símbolo determina la denominación cotizada. |

## Interpretación

- El valor bruto y el contrato de cada campo se conservan. No se suman ni comparan cifras si el campo falta o su unidad no puede demostrarse.
- Un ticker móvil de 24 h es una sola observación; no demuestra estabilidad. La estabilidad exige una serie de capturas fechadas o datos de velas históricos y análisis de huecos.
- La captura se programa cada seis horas y los artefactos se retienen hasta 90 días; eso es una ventana de retención de CI, no almacenamiento histórico permanente ni garantía de disponibilidad.
- `PASS` describe recepción/parseo de una respuesta, no liquidez ejecutable ni recomendación de inversión. Los umbrales de selección quedan pendientes de decisión y evidencia.
- Un HTTP 403 se conserva como fallo de acceso; no se cambia de dominio para eludir restricciones.

## Primera captura real integrada — 2026-10-22T12:21:04Z

Workflow: [Multi-exchange Spot quote-volume probe #39777588072](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39777588072). Artefacto original: [multi-exchange-spot-quote-volume](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39777588072/artifacts/12425146770). El workflow y los tests offline terminaron en `success`; la captura de mercado fue `PARTIAL` porque Bybit devolvió HTTP 403 para los tres símbolos.

Valores capturados por el campo de turnover cotizado, expresados en USDT según la semántica documentada de cada proveedor:

| Par | Binance | OKX | Bybit | MEXC | Gate | Bitget | Pionex |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC/USDT | 1,850,653,961.12149870 | 623,948,411.148934552 | INDETERMINATE (403) | 529,563,572.28 | 1,016,564,575.3342165 | 382,658,936.756441 | 2,690,638,425.45706367 |
| ETH/USDT | 747,853,881.40297200 | 399,855,019.22415134 | INDETERMINATE (403) | 223,899,206 | 354,009,552.97876 | 153,921,805.8293 | 452,122,292.61975092 |
| SOL/USDT | 231,856,434.14443000 | 68,857,917.3333594 | INDETERMINATE (403) | 70,275,763.63 | 97,436,005.46428 | 41,066,662.7077 | 42,216,316.01379989 |

## Lectura correcta de esta muestra

- Se obtuvieron **18/21 valores de turnover válidos** y **3/21 no disponibles** por HTTP 403 de Bybit. El 403 no equivale a volumen cero ni prueba inexistencia del par.
- Las solicitudes se realizaron secuencialmente en una ventana corta; los tickers de 24 h son ventanas móviles que no terminan exactamente al mismo instante. Esta tabla es descriptiva, no un ranking aprobado.
- Gate no devolvió un timestamp de origen en el campo extraído de esta respuesta; se conserva la hora de captura y el timestamp de origen queda ausente, no inventado.
- La dispersión entre proveedores no debe interpretarse automáticamente como discrepancia de datos: las ventanas móviles, definiciones y mecanismos de agregación pueden diferir. Antes de comparar/ordenar hay que verificar la semántica de cada campo y acumular una serie temporal.
- Una captura aislada no permite calcular estabilidad de volumen en ventanas mayores. La tarea siguiente es recopilar ejecuciones periódicas, medir huecos/cobertura y contrastar las definiciones de volumen con datos históricos oficiales.
