# Captura Binance Spot → informe de investigación E2E (Issue #128)

## Alcance

El comando `scripts.market_selection.capture_binance_spot_research` conecta los dos bloques existentes: captura OHLCV real de solo lectura y composición del informe `crypto-asset-research-report-v1`.

Usa únicamente endpoints públicos documentados de Binance Spot:
- `GET /api/v3/exchangeInfo?symbol=...` en `https://data-api.binance.vision`, para resolver `baseAsset`, `quoteAsset`, estado y permiso spot del símbolo nativo exacto.
- `GET /api/v3/klines` en el mismo host, a través del capturador existente, para el intervalo UTC solicitado.

Referencia oficial: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md y https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md.

## Uso

```bash
python -m scripts.market_selection.capture_binance_spot_research \
  --symbol BTCUSDT \
  --base-asset-ticker BTC \
  --interval 1h \
  --start-time-ms 1792540800000 \
  --end-time-ms 1792562400000 \
  --config configs/technical-descriptive-baseline.json \
  --capture-output artifacts/binance-spot-capture.json \
  --report-output artifacts/crypto-asset-research-report.json
```

Los timestamps son ejemplos de sintaxis: antes de una ejecución real, calcular límites UTC alineados al intervalo. La ventana es semiabierta `[start, end)`; no se deben usar los valores de ejemplo como ventana actual.

## Evidencia y garantías

- Preserva cuerpo completo de exchangeInfo en Base64, número exacto de bytes, SHA-256, URL y timestamps de solicitud/captura.
- Reutiliza la captura OHLCV que preserva cuerpo de cada página, hash, tamaño, normalización, huecos y duplicados.
- No impone un máximo local de bytes; sigue leyendo cada respuesta hasta EOF. Los límites operativos del proveedor, límites de página y ventanas temporales solicitadas se documentan por separado.
- No deduce la identidad a partir de dividir el ticker; utiliza `baseAsset` devuelto por exchangeInfo para el par exacto.
- El ticker base no equivale a un identificador global canónico de token. El informe marca `market_base_asset_mapping_status=VERIFIED`, pero mantiene `asset_identity_status=INDETERMINATE`, `canonical_asset_identity_status=NOT_RESOLVED` y calidad `INCOMPLETE_OR_UNVERIFIED` hasta resolver un identificador estable cross-provider. Mapeos entre activos envueltos, cadenas y proveedores siguen sin resolverse.
- Registra `license_review_status=REQUIRES_PRODUCT_SPECIFIC_REVIEW`. Documentación de endpoint no implica una licencia comercial general; evaluar condiciones aplicables antes de persistencia/redistribución comercial.
- No usa credenciales, no accede a cuentas privadas, no coloca órdenes.
- La decisión y los horizontes corto/medio/largo permanecen `INDETERMINATE`; captura real no es evidencia de rentabilidad ni un pronóstico.

## Validación

El workflow ejecuta tests offline con respuestas simuladas para validar preservación íntegra, hash/tamaño, resolución exacta de símbolo, rechazo de mercados no operables y abstención. Un workflow_dispatch separado ejecuta una prueba pequeña de solo lectura contra Binance real y genera artefactos efímeros de CI; ese smoke test no equivale a aprobación comercial ni a evaluación predictiva.

## Limitaciones

No integra noticias, fundamentales/on-chain ni una licencia de datos comerciales. No realiza selección automática de un par cuando un activo tiene múltiples pares. El usuario/componente llamador debe especificar el símbolo nativo exacto y un `base-asset-ticker` igual al `baseAsset` resuelto. No se acepta un ID global pretendiendo que el ticker lo representa. La cobertura real del intervalo puede ser `PARTIAL`; no se ocultan velas faltantes.
