# Captura histórica OHLCV de Pionex Spot

**Estado:** adaptador de captura read-only. No es aún una fuente de velas semánticamente normalizada para comparaciones cruzadas.

## Fuente oficial y contrato

- [Pionex Get Klines](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines): GET /api/v1/market/klines.
- [OpenAPI oficial de Pionex](https://github.com/pionex-official/pionex-open-api/blob/main/openapi.yaml).
- Host: https://api.pionex.com; no requiere credenciales para este endpoint público.
- Intervalos oficiales: 1M, 5M, 15M, 30M, 60M, 4H, 8H, 12H, 1D. En esta API 1M significa un minuto, no el mes que representa Binance 1M.
- limit documentado: 1–500 por petición. La documentación también menciona un máximo de 10.000 registros recuperables.
- Cada vela documenta time (milisegundos), OHLC y volume ("Total trading volume"). La documentación no define explícitamente si time es apertura/cierre de la vela ni la denominación de volume.

## Implementación

scripts/market_selection/capture_pionex_spot_ohlcv.py:
- Lee cada cuerpo completo hasta EOF con un buffer de 64 KiB; no hay límite local de bytes, velas ni páginas.
- Preserva URL, timestamps de captura, estado HTTP, cuerpo Base64, tamaño, SHA-256 y JSON parseado por página.
- Pagina hacia atrás usando endTime = timestamp más antiguo observado - 1 ms; verifica progreso, registra respuestas posteriores al endTime solicitado y conserva los duplicados en el artefacto si aparecen.
- Se detiene ante página vacía, límite de historial declarado por Pionex, fallo de red/esquema, anomalía de normalización o ausencia de progreso.
- Marca overall_status=PARTIAL si la cobertura no se puede demostrar. No convierte errores en ceros ni elimina silenciosamente velas duplicadas.
- Conserva source_time_ms y volume_raw, pero deja timestamp_role_status y volume_unit_status en INDETERMINATE. No crea open_time_ms, close_time_ms, volumen base ni turnover cotizado por inferencia.

## Ejecución

    python scripts/market_selection/capture_pionex_spot_ohlcv.py \
      --symbol BTC_USDT --interval 1D \
      --output artifacts/pionex-spot-ohlcv.json

Sin start-time-ms ni end-time-ms, el adaptador intenta recorrer hacia atrás todo el historial que el endpoint permita para ese símbolo e intervalo. Los parámetros de ventana son opcionales. El workflow .github/workflows/pionex-spot-ohlcv-capture.yml ejecuta una captura de referencia para BTC_USDT/1D al integrar cambios del adaptador, y admite otras entradas por workflow_dispatch; el artefacto de Actions tiene retención finita y no equivale a persistencia central.

## Límites de análisis

Hasta que la documentación oficial especifique el rol temporal y la unidad de volumen, las velas son evidencia bruta histórica y **no se deben usar como si fueran comparables con Binance** en gaps, velas cerradas, turnover, volumen base/cotizado o análisis anti-look-ahead. La captura no prueba cobertura total más allá del límite de proveedor, no reconstruye trades/libros y no autoriza órdenes.
