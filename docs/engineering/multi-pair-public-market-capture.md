# Captura reproducible multi-par de mercado spot

## Objetivo y alcance

`scripts/market_selection/capture_public_market_batch.py` amplía la captura de un único mercado a un universo inicial explícito de tres pares: BTC/USDT, ETH/USDT y SOL/USDT. Para cada par registra una respuesta pública de disponibilidad de Pionex, metadatos de mercado spot de Binance y profundidad de Binance limitada a 20 niveles.

El proceso es de solo lectura: no usa credenciales, no envía órdenes y no clasifica activos por potencial de inversión. El universo es un conjunto de prueba inicial, no una recomendación ni una selección aprobada de activos.

## Contrato del artefacto

Esquema: `public-market-capture-batch-v1`.

- `universe`: lista explícita de pares con símbolos exactos de Pionex y Binance y activos base/cotización.
- `records`: nueve registros esperados, tres proveedores por mercado, cada uno con URL, timestamps de captura, estado HTTP, tamaño, SHA-256, bytes originales en Base64, JSON parseado y error cuando corresponda.
- `expected_record_count` / `actual_record_count`: detectan capturas incompletas.
- `overall_status`: `PASS` solo cuando se obtienen las nueve respuestas HTTP 200 con JSON objeto válido; en caso contrario, `FAIL`.

Un registro HTTP 200 no equivale a disponibilidad del par. La interpretación de cada respuesta de mercado requiere un evaluador específico del esquema batch; este artefacto no se debe pasar al evaluador `public-market-capture-v1` de un solo par.

## Reproducibilidad y controles

Ejecutar:

```powershell
python scripts/market_selection/capture_public_market_batch.py
python -m unittest discover -s tests/market_selection -p "test_capture_public_market_batch.py" -v
```

Las pruebas son offline y sustituyen las respuestas HTTP con dobles controlados. CI ejecuta pruebas y una captura live independiente. Los artefactos se retienen 14 días.

## Límites y siguientes puertas

- Nueve solicitudes secuenciales; cada solicitud tiene timeout de 12 segundos y límite de 5 MiB. No se implementa reintento automático.
- La captura es un snapshot; no constituye una serie temporal ni acredita frescura del evento de mercado.
- La profundidad de 20 niveles no es el libro completo; el volumen 24h tampoco sustituye la profundidad ejecutable.
- La disponibilidad de Pionex no garantiza acceso por región/cuenta ni ejecución.
- Comisiones, frescura de origen, riesgo de activo, calidad histórica y rentabilidad no se evalúan aquí.
- No emitir ranking ni decisión de inversión hasta validar los esquemas por mercado, implementar evaluación batch y aprobar explícitamente criterios de elegibilidad.
- Si un proveedor falla, el artefacto se conserva para diagnóstico, pero el workflow live falla y el lote no se considera completo.

## Aceptación

1. Universo declarado y sin símbolos duplicados.
2. Tres proveedores por cada mercado; nueve registros para la configuración inicial.
3. Cada respuesta conserva bytes originales, tamaño y SHA-256.
4. Los tests offline validan matriz de solicitudes, integridad, respuesta HTTP no exitosa y contrato batch.
5. El workflow conserva el artefacto incluso si falla la captura.
