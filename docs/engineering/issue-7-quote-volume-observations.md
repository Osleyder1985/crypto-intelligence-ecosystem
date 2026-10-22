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

- El valor bruto y el contrato de cada campo se conservan. El capturador exige que el símbolo nativo devuelto coincida exactamente con el solicitado y rechaza símbolos ausentes, diferentes o duplicados. No se suman ni comparan cifras si el campo falta o su unidad no puede demostrarse.
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


## Segunda observación real y comparación exploratoria — 2026-10-22

Se analizó el segundo artefacto real posterior a la integración de PR #108:

- Primera observación: [workflow #39777588072, artefacto #12425146770](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39777588072/artifacts/12425146770), creada a las 12:21:04.875Z.
- Segunda observación: [workflow #39789741314, artefacto #12431375194](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39789741314/artifacts/12431375194), creada a las 13:46:07.098Z.
- Separación entre creaciones: aproximadamente 85 minutos y 2 segundos.
- Integridad comprobada de forma local para los artefactos descargados: 21/21 respuestas de cada captura conservan un cuerpo cuya longitud coincide con `response_bytes` y cuyo SHA-256 coincide con `response_sha256`.
- Cada captura tuvo 18/21 valores de turnover válidos y 3/21 no disponibles por HTTP 403 de Bybit. No se infiere cero ni se intenta eludir el bloqueo.
- Las tablas comparan solo los 18 pares de observaciones válidas en ambas capturas. Los porcentajes son el cambio entre dos valores de ventana móvil de 24 h; **no son el volumen negociado durante esos 85 minutos**.

| Par | Exchange | Turnover 24 h anterior (USDT) | Turnover 24 h nuevo (USDT) | Cambio observado |
|---|---|---:|---:|---:|
| BTC/USDT | Binance | 1,850,653,961.12 | 1,866,250,913.92 | +0.84% |
| BTC/USDT | Bitget | 382,658,936.76 | 370,115,768.74 | -3.28% |
| BTC/USDT | Gate | 1,016,564,575.33 | 1,004,393,827.20 | -1.20% |
| BTC/USDT | MEXC | 529,563,572.28 | 534,833,981.15 | +1.00% |
| BTC/USDT | OKX | 623,948,411.15 | 617,746,577.22 | -0.99% |
| BTC/USDT | Pionex | 2,690,638,425.46 | 2,721,790,946.44 | +1.16% |
| ETH/USDT | Binance | 747,853,881.40 | 712,928,579.49 | -4.67% |
| ETH/USDT | Bitget | 153,921,805.83 | 149,272,959.09 | -3.02% |
| ETH/USDT | Gate | 354,009,552.98 | 338,245,124.18 | -4.45% |
| ETH/USDT | MEXC | 223,899,206.00 | 215,813,801.87 | -3.61% |
| ETH/USDT | OKX | 399,855,019.22 | 381,482,848.11 | -4.59% |
| ETH/USDT | Pionex | 452,122,292.62 | 436,290,676.13 | -3.50% |
| SOL/USDT | Binance | 231,856,434.14 | 225,468,242.78 | -2.76% |
| SOL/USDT | Bitget | 41,066,662.71 | 39,832,350.04 | -3.01% |
| SOL/USDT | Gate | 97,436,005.46 | 94,451,755.79 | -3.06% |
| SOL/USDT | MEXC | 70,275,763.63 | 68,490,770.27 | -2.54% |
| SOL/USDT | OKX | 68,857,917.33 | 65,787,091.46 | -4.46% |
| SOL/USDT | Pionex | 42,216,316.01 | 41,194,132.61 | -2.42% |

### Interpretación

1. En esta pareja de capturas, los seis venues accesibles muestran un descenso observado del turnover de ETH/USDT y SOL/USDT; BTC/USDT varía según venue. Eso describe dos ventanas móviles, no una causa ni un ranking estable.
2. La dispersión de los cambios entre proveedores no permite concluir cuál es el mercado más líquido: las ventanas, agregación, timestamps y semántica de campos no son necesariamente idénticos.
3. Gate no aporta timestamp de origen en estos registros; la hora de captura no sustituye a la hora del dato. Bybit continúa sin evidencia accesible desde el runner de CI.
4. Dos observaciones separadas por unos 85 minutos siguen siendo insuficientes para estimar estabilidad a largo plazo, percentiles, comportamiento en distintos regímenes o cobertura de fallos.
5. La siguiente verificación es analizar una serie con muchas observaciones programadas, medir huecos y cobertura por venue/par, validar semántica temporal y solo después definir reglas de comparabilidad y selección. No se asignan umbrales numéricos sin justificación y aprobación.

La nueva captura se ejecutó en modo público read-only. La ejecución del workflow fue `success`, pero el resultado de captura fue `PARTIAL` debido a Bybit; ambos estados deben mantenerse separados.
