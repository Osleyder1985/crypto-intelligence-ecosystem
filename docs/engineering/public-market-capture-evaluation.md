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

```json
{
  "max_spread_bps": 5,
  "depth_band_bps": 10,
  "min_depth_quote": 10000,
  "order_size_base": 0.01,
  "max_slippage_bps": 10
}
```

Estos valores son ilustrativos; no son umbrales aprobados para operar. Ejecutar con `--config scenario.json` evalúa ese escenario, pero no convierte la configuración en política aprobada.

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

Workflow [market-capture-evaluation, ejecución 39365873626](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365873626): estado `completed / success`; el log registró 60 pruebas y resultado `OK`. Estas pruebas son offline y usan fixtures, por lo que no deben describirse como una ejecución end-to-end del evaluador sobre la captura live.

### Captura live de referencia

Workflow [public-market-capture, ejecución 39365509886](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365509886). Artefacto ZIP [public-market-capture](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365509886/artifacts/12238549860).

- Artefacto creado: `2026-10-20T03:40:23.226Z`.
- Esquema: `public-market-capture-v1`; estado general: `PASS`.
- ZIP SHA-256: `c4b9e4852a9b32165dc792e4a4f3b22a180f285bedfcc7cdfafebf18f0798288`.
- Pionex: `BTC_USDT`, tipo `SPOT`, habilitado en la respuesta capturada.
- Binance: `BTCUSDT`, estado `TRADING`, spot permitido en la respuesta capturada.
- Binance depth: 20 niveles bid y 20 ask; `lastUpdateId` disponible, sin timestamp de evento.

Una comprobación independiente de los bytes descargados confirmó los hashes, los tamaños, la coincidencia entre JSON preservado e interpretado, y reprodujo un spread aproximado de `0.001219 bps` para ese snapshot. Esta comprobación independiente no sustituye a registrar una ejecución del CLI del evaluador sobre ese artefacto; esa ejecución debe hacerse y conservarse como evidencia separada antes de declarar el flujo E2E completado.

## Siguiente criterio de aceptación

1. Descargar una captura conservada y verificar su SHA-256.
2. Ejecutar el CLI del evaluador contra el archivo JSON original.
3. Conservar el informe JSON resultante y registrar los hashes del artefacto fuente y del informe.
4. Repetir la evaluación con los mismos bytes y configuración; comprobar que los informes sean idénticos.
5. Mantener `decision_status: INDETERMINATE` hasta aprobar explícitamente una política y sus umbrales.
