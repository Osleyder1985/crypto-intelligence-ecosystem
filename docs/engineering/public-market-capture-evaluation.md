# Evaluación reproducible de capturas públicas de mercado

## Objetivo

El evaluador `scripts/market_selection/evaluate_capture.py` procesa una captura preservada del workflow de mercado público sin consultar la red ni enviar órdenes. Verifica la integridad de los bytes guardados y calcula métricas puntuales del libro de órdenes. No emite recomendaciones de inversión.

## Ejecución local

Desde la raíz del repositorio, con Python 3:

```powershell
python scripts/market_selection/evaluate_capture.py --artifact .\public-market-capture.json --output .\market-evaluation.json
```

El artefacto debe usar `public-market-capture-v1`, tener `overall_status: PASS` e incluir exactamente un registro de cada proveedor requerido: `pionex`, `binance_exchange_info` y `binance_depth`.

Para ejecutar un escenario explícito de análisis, se puede proporcionar un archivo JSON con parámetros, por ejemplo:

No se proporciona una configuración numérica predeterminada. Para ejecutar un escenario, la configuración debe derivarse de requisitos documentados del caso de uso y restricciones oficiales del mercado. Si la fuente oficial no prescribe un límite, no se debe inventar ni presentar como requisito ISO/Binance. Los campos obligatorios ausentes deben provocar `NOT_RUN`, error de configuración o `INDETERMINATE`, según el contrato del evaluador.

Los ejemplos numéricos usados anteriormente se eligieron manualmente para probar el comportamiento del software; no procedían de ISO ni de Binance. Se retiran como recomendación. Ejecutar con `--config scenario.json` evalúa únicamente los parámetros suministrados y no convierte la configuración en política aprobada.

## Controles de integridad

Para cada respuesta original, el evaluador:
1. exige `capture_status: PASS` y HTTP 200;
2. decodifica `response_base64`;
3. recalcula y compara SHA-256;
4. compara el tamaño en bytes;
5. vuelve a analizar los bytes como JSON UTF-8;
6. compara el JSON resultante con `parsed_json`.

También verifica los identificadores exactos de mercado y sus atributos spot en las respuestas de Pionex y Binance. Rechaza registros ausentes o duplicados y libros vacíos, con niveles mal formados o valores no positivos/no finitos.

## Interpretación de estados

- `PASS`: la comprobación definida para esa dimensión se cumple con los datos disponibles.
- `FAIL`: la comprobación definida no se cumple.
- `INDETERMINATE`: la evidencia no permite concluir.
- `NOT_RUN`: no se evaluó la dimensión porque no se proporcionó el parámetro correspondiente.

La decisión global permanece `INDETERMINATE`: no existe una política de decisión aprobada dentro de este evaluador. La disponibilidad del par no prueba acceso regional o de cuenta, la integridad criptográfica no prueba autenticidad del proveedor y un snapshot no garantiza ejecución de una orden.

## Limitaciones de mercado

- La captura de profundidad utiliza un límite de 20 niveles; no demuestra la profundidad del libro completo.
- El spread es una observación puntual, no una serie histórica.
- El deslizamiento, cuando se configura, se estima consumiendo niveles del snapshot y no garantiza fills.
- `lastUpdateId` de Binance no es un timestamp del evento de mercado; la frescura respecto al origen queda `INDETERMINATE`.
- Las comisiones quedan `INDETERMINATE` hasta que se incorporen fuentes y condiciones de cuenta verificadas.
- No se envían órdenes ni se realizan solicitudes de red durante la evaluación guardada.

## Evidencia registrada

### Pruebas automatizadas

Workflow de pruebas offline [39365873626](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365873626): `completed / success`, 60 pruebas, resultado `OK`. Estas pruebas usan fixtures; la validación live E2E separada está documentada a continuación.

### Captura live de referencia

Workflow [public-market-capture, ejecución 39365509886](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365509886). Artefacto ZIP [public-market-capture](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365509886/artifacts/12238549860).

- Artefacto creado: `2026-10-20T03:40:23.226Z`.
- Esquema: `public-market-capture-v1`; estado general: `PASS`.
- ZIP SHA-256: `c4b9e4852a9b32165dc792e4a4f3b22a180f285bedfcc7cdfafebf18f0798288`.
- Pionex: `BTC_USDT`, tipo `SPOT`, habilitado en la respuesta capturada.
- Binance: `BTCUSDT`, estado `TRADING`, spot permitido en la respuesta capturada.
- Binance depth: 20 niveles bid y 20 ask; `lastUpdateId` disponible, sin timestamp de evento.

### Ejecución E2E del evaluador sobre la captura live

Workflow [market-capture-evaluation, ejecución 39366725132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39366725132), commit `6c612b9c37cb7afdae17447b0b379c69fce7eb26`: `completed / success`. El workflow descargó el artefacto live desde GitHub, verificó el SHA-256 del ZIP, ejecutó el CLI `evaluate_capture.py` dos veces sobre el mismo JSON y comparó los informes byte a byte; ambos fueron idénticos. La ejecución también comprobó explícitamente que la decisión global sigue `INDETERMINATE`, la integridad y disponibilidad spot pasan, y no hubo solicitudes de red ni órdenes durante la evaluación.

El log reporta `spread_bps = 0.0012191661445804635`, mejor bid `82023.27`, mejor ask `82023.28`, 20 niveles por lado, `source_freshness = INDETERMINATE`, `fees = INDETERMINATE`, y `depth`/`spread`/`slippage = NOT_RUN` cuando no se proporcionan parámetros de escenario. Informe y captura fuente conservados en el artefacto [live-capture-evaluation-report](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39366725132/artifacts/12238944233), SHA-256 del ZIP de informe: `785ec198cb42e74063b9122fad966c8d3772955517bdb1d75e2257e2584dd6e8` (retención de 14 días desde su creación).

### Evidencia histórica de un escenario de prueba retirado

La ejecución [39366846581](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39366846581) utilizó parámetros escogidos manualmente para ejercitar el cálculo de spread, profundidad y deslizamiento. Esos parámetros no procedían de ISO ni de Binance y se retiran como recomendación o criterio de aceptación. La ejecución demuestra únicamente que el evaluador procesó de forma determinista ese escenario de software; el estado `PASS` se refería a los valores de prueba configurados, no a una política oficial ni a idoneidad para operar.

- Profundidad mínima observada dentro de la banda de 10 bps: aproximadamente `281714.2153 USDT`.
- Compra simulada de 0,01 BTC: VWAP `82023.28 USDT`, deslizamiento estimado `0.00060958 bps`.
- Venta simulada de 0,01 BTC: deslizamiento estimado `0.00060958 bps`.
- Frescura de la fuente y comisiones siguen `INDETERMINATE`; por tanto, la decisión global continúa `INDETERMINATE`.
- Artefacto actualizado con informe base, configuración del escenario y su informe: [live-capture-evaluation-report](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39366846581/artifacts/12239721110), ZIP SHA-256 `bdaa1f8068aa12731fc7ad33ff865e43f5368fab557db813bfde4fe78feabee0`.

El resultado solo describe un snapshot de 20 niveles. La profundidad no representa el libro completo, el VWAP no garantiza ejecución y los parámetros históricos se consideran retirados; no son límites oficiales ni recomendación de inversión.

Esta prueba demuestra ejecución E2E reproducible sobre la captura archivada específica; no demuestra que las métricas predigan rentabilidad ni que los umbrales sean adecuados para operar.

## Siguiente criterio de aceptación

1. Descargar una captura conservada y verificar su SHA-256.
2. Ejecutar el CLI del evaluador contra el archivo JSON original.
3. Conservar el informe JSON resultante y registrar los hashes del artefacto fuente y del informe.
4. Repetir la evaluación con los mismos bytes y configuración; comprobar que los informes sean idénticos.
5. Mantener `decision_status: INDETERMINATE` hasta que haya criterios sustentados por fuentes oficiales o, cuando estas no fijen valores, por una justificación interna documentada con mediciones reproducibles y evaluación de riesgo.
