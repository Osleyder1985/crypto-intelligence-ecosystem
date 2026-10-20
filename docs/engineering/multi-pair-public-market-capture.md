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


## Evidencia E2E registrada

Workflow [39367485108](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39367485108), commit `702afe229d40c8ca2d33e7a053f296994c055d9d`: `completed / success`. En la misma ejecución pasaron las pruebas offline de captura/evaluación y la captura pública live de nueve respuestas; el evaluador procesó los tres pares dos veces, tanto sin parámetros como con escenario ilustrativo, y comparó los informes byte a byte.

- Los nueve registros devolvieron HTTP 200 y JSON válido.
- Para los tres pares, la integridad de captura, disponibilidad spot de Pionex y estado spot de Binance resultaron `PASS` en esta captura.
- En el escenario ilustrativo (banda 10 bps, orden de 0,01 unidades base, máximos de spread y slippage de 5/10 bps), las dimensiones spread, profundidad y slippage pasaron para los tres snapshots.
- Spread observado: BTC/USDT ≈ 0,001217 bps; ETH/USDT ≈ 0,041426 bps; SOL/USDT ≈ 0,949623 bps.
- Profundidad mínima por lado dentro de 10 bps: BTC ≈ 260.689 USDT; ETH ≈ 76.071 USDT; SOL ≈ 884.717 USDT.
- Slippage estimado para orden de 0,01 unidades base: BTC ≈ 0,000609 bps; ETH ≈ 0,020713 bps; SOL ≈ 0,474811 bps.
- Frescura de origen y comisiones permanecen `INDETERMINATE`; la decisión global sigue `INDETERMINATE`. Estos valores describen snapshots de Binance, no garantizan ejecución ni demuestran rentabilidad.
- Artefacto con captura e informes: [public-market-capture-batch](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39367485108/artifacts/12239772976), SHA-256 del ZIP `53a888a93bc24b6d799a5bba085d0df2d9bd7a2a13120a7c2f31e5a5608bcaaf`, retención hasta 2026-11-03.

## Aceptación

1. Universo explícito y sin símbolos duplicados.
2. Nueve respuestas y combinación única mercado/proveedor.
3. Integridad de bytes antes de calcular métricas.
4. Pruebas offline de captura y evaluación.
5. Dos ejecuciones con inputs idénticos producen informes idénticos.
6. Decisión global `INDETERMINATE`; sin órdenes ni red durante la evaluación.
