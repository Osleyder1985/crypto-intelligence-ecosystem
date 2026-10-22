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
