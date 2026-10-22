# Eventos de movimiento OHLCV — Issue #13

- **Script:** scripts/market_selection/detect_ohlcv_movement_events.py
- **Pruebas:** tests/market_selection/test_detect_ohlcv_movement_events.py
- **Entrada:** artefacto normalizado binance-spot-ohlcv-capture-v1.
- **Parámetros obligatorios:** lookback-bars, return-threshold-pct y volume-ratio-threshold.
- **Salida:** ohlcv-movement-events-v1; solo eventos descriptivos, sin ranking.

## Método causal

Por vela cerrada, calcula el retorno simple desde el cierre de la vela inmediatamente anterior y compara el turnover cotizado con la mediana de las velas cerradas previas del mismo segmento. La vela actual nunca entra en la base de su propia anomalía de volumen. Un evento queda disponible solo después del cierre de la vela que lo produce.

Los eventos describen PRICE_MOVE, VOLUME_SPIKE o ambas condiciones. El registro incluye umbrales explícitos, dirección, retorno, mediana previa, ratio de volumen, estado de la base y tiempos de disponibilidad. La atribución causal permanece NOT_ESTABLISHED: una subida con volumen no demuestra qué la causó.

## Calidad y prevención de fuga

- Verifica integridad Base64/SHA-256/tamaño de las respuestas originales.
- Excluye velas abiertas o no elegibles.
- Los huecos y velas excluidas dividen la serie; ningún retorno ni baseline de volumen cruza segmentos.
- No sustituye volumen faltante por cero ni inventa datos de un intervalo ausente.
- Los tests comprueban que añadir velas futuras no modifica eventos anteriores y que los umbrales son parámetros explícitos.

## Límites

No es un detector de noticias, causalidad ni predicción. No estima probabilidad de continuación, no fija umbrales universales, no clasifica activos y no envía órdenes. Los umbrales deben evaluarse fuera de muestra y registrarse en una configuración versionada antes de usarlos para selección.
