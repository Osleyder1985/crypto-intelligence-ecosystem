# Captura y evaluación reproducible multi-par de mercado spot

## Objetivo y alcance

`scripts/market_selection/capture_public_market_batch.py` captura tres pares explícitos: BTC/USDT, ETH/USDT y SOL/USDT. Por par guarda respuestas públicas de Pionex y Binance, incluida profundidad Binance limitada a 20 niveles. `scripts/market_selection/evaluate_capture_batch.py` verifica la integridad de los bytes y evalúa cada mercado sin solicitudes de red ni órdenes.

El universo es una prueba técnica inicial, no un ranking ni una recomendación de inversión. No usa credenciales y no puede operar.

## Contrato de captura

Esquema: `public-market-capture-batch-v1`. El artefacto incluye universo, nueve registros (tres proveedores por mercado), URL, timestamps, estado HTTP, tamaño, SHA-256, bytes originales Base64, JSON parseado y errores. `overall_status: PASS` solo indica que las nueve respuestas son HTTP 200 con JSON objeto válido; no certifica disponibilidad semántica.

## Contrato de evaluación

Esquema de salida: `public-market-batch-evaluation-v1`. Verifica hash, longitud y consistencia del JSON original, rechaza proveedores ausentes o duplicados, comprueba campos de disponibilidad spot y calcula spread. Con parámetros explícitos calcula profundidad en banda y deslizamiento estimado por VWAP, por par.

Configuración ilustrativa no aprobada:

```json
{
  "max_spread_bps": 5,
  "depth_band_bps": 10,
  "min_depth_quote": 10000,
  "order_size_base": 0.01,
  "max_slippage_bps": 10
}
```

Los umbrales no se aprueban por aparecer en un JSON. La decisión global permanece `INDETERMINATE`; no hay ranking ni decisión de inversión aprobada.

## Ejecución

```powershell
python scripts/market_selection/capture_public_market_batch.py
python -m unittest discover -s tests/market_selection -p "test_*batch.py" -v
python scripts/market_selection/evaluate_capture_batch.py --artifact .\artifacts\public-market-capture-batch.json --output .\artifacts\batch-evaluation.json
```

CI ejecuta pruebas offline y captura pública live. Evalúa dos veces la misma captura, con y sin escenario ilustrativo, y compara los informes byte a byte. Los artefactos se retienen 14 días.

## Estados y límites

- `PASS` solo aplica a una dimensión y a la evidencia disponible; no es señal de compra.
- `FAIL` indica que una comprobación explícita no se cumple.
- `INDETERMINATE` indica evidencia insuficiente.
- `NOT_RUN` indica que no se proporcionó el parámetro necesario.

La frescura del evento y las comisiones permanecen `INDETERMINATE`. Veinte niveles no son el libro completo; un snapshot no garantiza fills; disponibilidad no prueba acceso regional o de cuenta. Riesgo de activo, histórico de liquidez, comisiones oficiales, series temporales y rentabilidad quedan fuera. No se envían órdenes.

## Aceptación

1. Universo explícito y sin símbolos duplicados.
2. Nueve respuestas y combinación única mercado/proveedor.
3. Integridad de bytes antes de calcular métricas.
4. Pruebas offline de captura y evaluación.
5. Dos ejecuciones con inputs idénticos producen informes idénticos.
6. Decisión global `INDETERMINATE`; sin órdenes ni red durante la evaluación.
