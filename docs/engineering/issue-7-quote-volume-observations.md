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
| Pionex | `amount` | La OpenAPI oficial lo describe como importe negociado de 24 h, pero no fija inequívocamente la unidad/denominación. Conservar el valor bruto; su comparabilidad como turnover cotizado queda `INDETERMINATE`. |

## Interpretación

- El valor bruto y el contrato de cada campo se conservan. El capturador exige que el símbolo nativo devuelto coincida exactamente con el solicitado y rechaza símbolos ausentes, diferentes o duplicados. No se suman ni comparan cifras si el campo falta o su unidad no puede demostrarse. Para Pionex, `amount` queda `INDETERMINATE` como turnover USDT hasta que una fuente oficial documente inequívocamente la unidad.
- Un ticker móvil de 24 h es una sola observación; no demuestra estabilidad. La estabilidad exige una serie de capturas fechadas o datos de velas históricos y análisis de huecos.
- La captura se programa cada seis horas y los artefactos se retienen hasta 90 días; eso es una ventana de retención de CI, no almacenamiento histórico permanente ni garantía de disponibilidad.
- `PASS` describe recepción/parseo de una respuesta, no liquidez ejecutable ni recomendación de inversión. Los umbrales de selección quedan pendientes de decisión y evidencia.
- Un HTTP 403 se conserva como fallo de acceso; no se cambia de dominio para eludir restricciones.

## Primera captura real integrada — 2026-10-22T12:21:04Z

Workflow: [Multi-exchange Spot quote-volume probe #39777588072](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39777588072). Artefacto original: [multi-exchange-spot-quote-volume](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39777588072/artifacts/12425146770). El workflow y los tests offline terminaron en `success`; la captura de mercado fue `PARTIAL` porque Bybit devolvió HTTP 403 para los tres símbolos.

Los valores se expresan en USDT solo cuando la semántica oficial del campo lo respalda. En Pionex se conserva el `amount` bruto, pero se marca `INDETERMINATE` porque la OpenAPI pública no define inequívocamente su unidad; no usarlo para comparar o rankear turnover:

| Par | Binance | OKX | Bybit | MEXC | Gate | Bitget | Pionex |
|---|---:|---:|---:|---:|---:|---:|---|
| BTC/USDT | 1,850,653,961.12149870 | 623,948,411.148934552 | INDETERMINATE (403) | 529,563,572.28 | 1,016,564,575.3342165 | 382,658,936.756441 | INDETERMINATE (amount=2,690,638,425.45706367; unidad no documentada) |
| ETH/USDT | 747,853,881.40297200 | 399,855,019.22415134 | INDETERMINATE (403) | 223,899,206 | 354,009,552.97876 | 153,921,805.8293 | INDETERMINATE (amount=452,122,292.61975092; unidad no documentada) |
| SOL/USDT | 231,856,434.14443000 | 68,857,917.3333594 | INDETERMINATE (403) | 70,275,763.63 | 97,436,005.46428 | 41,066,662.7077 | INDETERMINATE (amount=42,216,316.01379989; unidad no documentada) |

## Lectura correcta de esta muestra

- Se obtuvieron 21 respuestas preservadas: 18/21 fueron técnicamente accesibles y 3/21 devolvieron HTTP 403 de Bybit. Solo 15/21 valores se consideran comparables como turnover cotizado; los 3 `amount` de Pionex se conservan en bruto pero su unidad queda `INDETERMINATE`. El 403 no equivale a volumen cero ni prueba inexistencia del par.
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
- Cada captura tuvo 18/21 respuestas técnicamente accesibles y 3/21 HTTP 403 de Bybit; solo 15/21 valores se consideran comparables como turnover cotizado, porque los tres `amount` de Pionex tienen unidad `INDETERMINATE`. No se infiere cero ni se intenta eludir el bloqueo.
- Las tablas comparan solo los 18 pares de observaciones válidas en ambas capturas. Los porcentajes son el cambio entre dos valores de ventana móvil de 24 h; **no son el volumen negociado durante esos 85 minutos**.

| Par | Exchange | Turnover 24 h anterior (USDT) | Turnover 24 h nuevo (USDT) | Cambio observado |
|---|---|---:|---:|---:|
| BTC/USDT | Binance | 1,850,653,961.12 | 1,866,250,913.92 | +0.84% |
| BTC/USDT | Bitget | 382,658,936.76 | 370,115,768.74 | -3.28% |
| BTC/USDT | Gate | 1,016,564,575.33 | 1,004,393,827.20 | -1.20% |
| BTC/USDT | MEXC | 529,563,572.28 | 534,833,981.15 | +1.00% |
| BTC/USDT | OKX | 623,948,411.15 | 617,746,577.22 | -0.99% |
| SOL/USDT | 231,856,434.14443000 | 68,857,917.3333594 | INDETERMINATE (403) | 70,275,763.63 | 97,436,005.46428 | 41,066,662.7077 | INDETERMINATE (amount=42,216,316.01379989; unidad no documentada) |
| ETH/USDT | Binance | 747,853,881.40 | 712,928,579.49 | -4.67% |
| ETH/USDT | Bitget | 153,921,805.83 | 149,272,959.09 | -3.02% |
| ETH/USDT | Gate | 354,009,552.98 | 338,245,124.18 | -4.45% |
| ETH/USDT | MEXC | 223,899,206.00 | 215,813,801.87 | -3.61% |
| ETH/USDT | OKX | 399,855,019.22 | 381,482,848.11 | -4.59% |
| BTC/USDT | Pionex | INDETERMINATE (amount=2,690,638,425.46; unidad no documentada) | INDETERMINATE (amount=2,721,790,946.44; unidad no documentada) | INDETERMINATE (unidad no documentada) |
| SOL/USDT | Binance | 231,856,434.14 | 225,468,242.78 | -2.76% |
| SOL/USDT | Bitget | 41,066,662.71 | 39,832,350.04 | -3.01% |
| SOL/USDT | Gate | 97,436,005.46 | 94,451,755.79 | -3.06% |
| SOL/USDT | MEXC | 70,275,763.63 | 68,490,770.27 | -2.54% |
| SOL/USDT | OKX | 68,857,917.33 | 65,787,091.46 | -4.46% |
| ETH/USDT | Pionex | INDETERMINATE (amount=452,122,292.62; unidad no documentada) | INDETERMINATE (amount=436,290,676.13; unidad no documentada) | INDETERMINATE (unidad no documentada) |

### Interpretación

1. En esta pareja de capturas, los seis venues accesibles muestran un descenso observado del turnover de ETH/USDT y SOL/USDT; BTC/USDT varía según venue. Eso describe dos ventanas móviles, no una causa ni un ranking estable.
2. La dispersión de los cambios entre proveedores no permite concluir cuál es el mercado más líquido: las ventanas, agregación, timestamps y semántica de campos no son necesariamente idénticos.
3. Gate no aporta timestamp de origen en estos registros; la hora de captura no sustituye a la hora del dato. Bybit continúa sin evidencia accesible desde el runner de CI.
4. Dos observaciones separadas por unos 85 minutos siguen siendo insuficientes para estimar estabilidad a largo plazo, percentiles, comportamiento en distintos regímenes o cobertura de fallos.
5. La siguiente verificación es analizar una serie con muchas observaciones programadas, medir huecos y cobertura por venue/par, validar semántica temporal y solo después definir reglas de comparabilidad y selección. No se asignan umbrales numéricos sin justificación y aprobación.

La nueva captura se ejecutó en modo público read-only. La ejecución del workflow fue `success`, pero el resultado de captura fue `PARTIAL` debido a Bybit; ambos estados deben mantenerse separados.

## Tercera observación real — 2026-10-22T13:56:45.057Z

- Workflow: [Multi-exchange Spot quote-volume probe #39791367609](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39791367609).
- Artefacto: [multi-exchange-spot-quote-volume #12430313812](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39791367609/artifacts/12430313812).
- Estado del workflow: `success`; estado de la captura: `PARTIAL`.
- 21/21 respuestas conservadas; bytes y SHA-256 coinciden en todas. 18/21 respuestas fueron técnicamente accesibles; 15/21 valores son comparables como turnover cotizado. Bybit devuelve HTTP 403 en BTC/ETH/SOL y los tres `amount` de Pionex quedan `INDETERMINATE` por unidad no documentada.
- Separación desde la segunda observación: 10 min 37.959 s. Separación entre primera y tercera: 1 h 35 min 40.182 s.

### Cambios observados entre la segunda y tercera captura

Los porcentajes comparan dos lecturas de ventanas móviles de 24 horas. No representan el volumen negociado durante los 10 min 37.959 s transcurridos.

| Par | Exchange | Turnover 24 h anterior (USDT) | Turnover 24 h nuevo (USDT) | Cambio observado |
|---|---|---:|---:|---:|
| BTC/USDT | Binance | 1,866,250,913.92 | 1,894,194,478.79 | +1.50% |
| BTC/USDT | Bitget | 370,115,768.74 | 367,958,461.40 | -0.58% |
| BTC/USDT | Gate | 1,004,393,827.20 | 1,006,859,674.29 | +0.25% |
| BTC/USDT | MEXC | 534,833,981.15 | 539,650,671.74 | +0.90% |
| BTC/USDT | OKX | 617,746,577.22 | 623,257,465.60 | +0.89% |
| SOL/USDT | Pionex | INDETERMINATE (amount=42,216,316.01; unidad no documentada) | INDETERMINATE (amount=41,194,132.61; unidad no documentada) | INDETERMINATE (unidad no documentada) |
| ETH/USDT | Binance | 712,928,579.49 | 714,293,662.26 | +0.19% |
| ETH/USDT | Bitget | 149,272,959.09 | 148,897,115.47 | -0.25% |
| ETH/USDT | Gate | 338,245,124.18 | 336,352,911.84 | -0.56% |
| ETH/USDT | MEXC | 215,813,801.87 | 216,224,559.26 | +0.19% |
| ETH/USDT | OKX | 381,482,848.11 | 381,918,873.52 | +0.11% |
| BTC/USDT | Pionex | INDETERMINATE (amount=2,721,790,946.44; unidad no documentada) | INDETERMINATE (amount=2,758,275,000.95; unidad no documentada) | INDETERMINATE (unidad no documentada) |
| SOL/USDT | Binance | 225,468,242.78 | 226,662,914.69 | +0.53% |
| SOL/USDT | Bitget | 39,832,350.04 | 39,664,546.12 | -0.42% |
| SOL/USDT | Gate | 94,451,755.79 | 94,061,729.94 | -0.41% |
| SOL/USDT | MEXC | 68,490,770.27 | 68,753,171.45 | +0.38% |
| SOL/USDT | OKX | 65,787,091.46 | 65,701,707.62 | -0.13% |
| ETH/USDT | Pionex | INDETERMINATE (amount=436,290,676.13; unidad no documentada) | INDETERMINATE (amount=437,497,730.64; unidad no documentada) | INDETERMINATE (unidad no documentada) |

### Qué permite concluir la tercera captura

1. Se mantienen 18/21 respuestas técnicamente accesibles, pero solo 15/21 valores comparables como turnover cotizado; Bybit continúa sin evidencia accesible desde este runner y los valores brutos de Pionex no son comparables hasta demostrar su unidad.
2. Entre la segunda y tercera muestra, los cambios de BTC varían por venue; ETH presenta variaciones pequeñas y mixtas; SOL también presenta cambios mixtos. No es una clasificación de liquidez.
3. Tres observaciones en menos de dos horas no constituyen una muestra representativa de estabilidad de 24 h ni de regímenes de mercado. No permiten estimar percentiles robustos, colas, comportamiento semanal ni estabilidad de largo plazo.
4. La diferencia de timestamps y las semánticas de campo siguen limitando la comparación entre venues. Gate no aporta timestamp de origen en los registros capturados; se conserva como ausente.
5. Los artefactos conservan respuestas completas y hashes verificables, pero GitHub Actions tiene retención finita. La serie debe analizarse antes de expirar y almacenarse conforme a una política de retención aprobada.

Esta tercera observación aumenta la trazabilidad de la muestra, pero **no cierra 7-M01**: sigue faltando una serie suficientemente larga y un criterio de estabilidad aprobado.


## Cuarta observación real — 2026-10-22T15:57:49.948Z

- Workflow: [Multi-exchange Spot quote-volume probe #39809696897](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897).
- Artefacto: [multi-exchange-spot-quote-volume #12439416760](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897/artifacts/12439416760).
- SHA-256 del JSON descargado: `d1fa980c4c1c97837c0b5928e3362ba482ada4e97204dd36dd5a5bfd1aad6ba0`; tamaño: 41.054 bytes.
- Estado del workflow: `success`; estado de la captura: `PARTIAL`.
- Integridad verificada: 21/21 respuestas decodifican desde Base64 y coinciden con el tamaño y SHA-256 registrados. 18/21 respuestas HTTP 200; 15/21 valores comparables como turnover cotizado.
- Separación desde la tercera observación: 2 h 1 min 4.891 s. Desde la primera observación, aproximadamente 3 h 36 min 46 s; sigue siendo una muestra corta frente a una evaluación de estabilidad de varios días o regímenes.

### Cambios observados entre la tercera y cuarta captura

Los porcentajes comparan dos lecturas del turnover móvil de 24 horas. **No representan el volumen negociado durante las dos horas transcurridas.** Los cambios solo se calculan para los cinco venues cuyo campo tiene unidad cotizada documentada y respuesta válida; Bybit y Pionex quedan fuera.

| Par | Exchange | Turnover 24 h anterior (USDT) | Turnover 24 h nuevo (USDT) | Cambio observado |
|---|---|---:|---:|---:|
| BTC/USDT | Binance | 1,894,194,478.79 | 1,738,168,583.78 | -8.24% |
| ETH/USDT | Binance | 714,293,662.26 | 629,903,782.33 | -11.81% |
| SOL/USDT | Binance | 226,662,914.69 | 207,660,538.47 | -8.38% |
| BTC/USDT | Bitget | 367,958,461.40 | 309,602,000.39 | -15.86% |
| ETH/USDT | Bitget | 148,897,115.47 | 138,683,839.45 | -6.86% |
| SOL/USDT | Bitget | 39,664,546.12 | 38,571,599.71 | -2.76% |
| BTC/USDT | Gate | 1,006,859,674.29 | 864,411,423.67 | -14.15% |
| ETH/USDT | Gate | 336,352,911.84 | 301,079,754.95 | -10.49% |
| SOL/USDT | Gate | 94,061,729.94 | 85,388,044.70 | -9.22% |
| BTC/USDT | MEXC | 539,650,671.74 | 498,525,142.05 | -7.62% |
| ETH/USDT | MEXC | 216,224,559.26 | 192,797,718.45 | -10.83% |
| SOL/USDT | MEXC | 68,753,171.45 | 63,807,757.48 | -7.19% |
| BTC/USDT | OKX | 623,257,465.60 | 553,133,704.06 | -11.25% |
| ETH/USDT | OKX | 381,918,873.52 | 341,049,260.83 | -10.70% |
| SOL/USDT | OKX | 65,701,707.62 | 58,268,645.36 | -11.31% |

### Valores que siguen sin ser comparables

| Par | Bybit | Pionex `amount` anterior | Pionex `amount` nuevo | Estado |
|---|---|---:|---:|---|
| BTC/USDT | HTTP 403 | 2,758,275,000.95 | 2,550,095,364.92 | `INDETERMINATE`: unidad no documentada |
| ETH/USDT | HTTP 403 | 437,497,730.64 | 397,969,446.83 | `INDETERMINATE`: unidad no documentada |
| SOL/USDT | HTTP 403 | 41,249,150.76 | 38,441,086.35 | `INDETERMINATE`: unidad no documentada |

### Interpretación de la cuarta observación

1. Los 15 deltas comparables son negativos en esta pareja de capturas; el rango observado es -2.76% a -15.86%. Eso describe el cambio entre dos ventanas móviles de 24 h y no permite inferir por sí solo la actividad transada en el intervalo, la causa del cambio ni la liquidez ejecutable.
2. El turnover móvil cambia también porque las operaciones antiguas salen de la ventana de 24 horas. Las definiciones, la agregación y los tiempos de captura pueden diferir por proveedor.
3. Bybit continúa devolviendo HTTP 403 desde el runner; no se intenta eludir esa restricción. Los tres valores Pionex se preservan, pero su unidad no se da por demostrada.
4. Cuatro capturas en unas 3 h 37 min mejoran la evidencia descriptiva, pero no demuestran estabilidad diaria/semanal ni permiten cerrar 7-M01. El muestreo programado cada seis horas debe acumular una serie más larga; la retención de CI no equivale a almacenamiento permanente.
