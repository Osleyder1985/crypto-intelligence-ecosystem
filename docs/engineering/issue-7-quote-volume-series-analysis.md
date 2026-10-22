# Análisis de series de turnover Spot 24 h — Issue #7

- **Herramienta:** `scripts/market_selection/analyze_quote_volume_series.py`
- **Pruebas:** `tests/market_selection/test_analyze_quote_volume_series.py`
- **Entrada:** uno o más artefactos `multi-exchange-spot-quote-volume-v1` descargados de ejecuciones del workflow público.
- **Salida:** JSON determinista respecto a los datos de entrada, salvo el campo informativo `created_at_utc`; no clasifica ni recomienda activos.

## Qué calcula

1. Comprueba el esquema y la fecha UTC de cada artefacto.
2. Verifica para cada respuesta preservada la decodificación Base64, el SHA-256 y el número de bytes.
3. Agrupa por exchange, activo y símbolo nativo exacto.
4. Informa cobertura y observaciones válidas, inválidas o ausentes sin convertir valores faltantes en cero.
5. Calcula el cambio porcentual entre observaciones consecutivas válidas solo si coinciden unidad y semántica declarada del campo.
6. Aplica una regla semántica vigente para Pionex: conserva amount y cualquier etiqueta declarada por capturadores antiguos, pero fuerza su elegibilidad comparativa a INDETERMINATE hasta que una fuente oficial documente la unidad.
7. Conserva los timestamps de origen como valores originales; no los sustituye por la hora de captura.

## Interpretación

El dato del ticker es turnover de una ventana móvil de 24 horas. La diferencia entre dos capturas **no** equivale al volumen negociado durante el tiempo transcurrido. Los proveedores pueden cerrar sus ventanas en instantes distintos o aplicar contratos de campo diferentes. El análisis es descriptivo, no un ranking y no demuestra estabilidad de largo plazo.

No establece umbrales de selección, no mide por sí solo liquidez ejecutable y no convierte el turnover en recomendación de inversión. Una serie suficientemente larga y representativa, controles de huecos/cobertura y una política aprobada siguen siendo necesarios para evaluar estabilidad. Los artefactos históricos de Pionex que etiquetaban amount como VALID/USDT no se aceptan como comparables: el analizador conserva esa etiqueta como metadato de origen, pero no la trata como evidencia de unidad.



## Evidencia live de la serie — 2026-10-22

La cuarta captura integrada se generó en [workflow #39809696897](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897), artefacto [#12439416760](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897/artifacts/12439416760). El JSON descargado mide 41.054 bytes y su SHA-256 es `d1fa980c4c1c97837c0b5928e3362ba482ada4e97204dd36dd5a5bfd1aad6ba0`. Los 21 cuerpos de respuesta superaron la verificación de Base64, tamaño y SHA-256. La captura fue `PARTIAL`: 18/21 respuestas HTTP 200, 15/21 valores comparables; Bybit respondió HTTP 403 y Pionex `amount` sigue `INDETERMINATE`.

La comparación reproducible con la tercera captura, separada por 2 h 1 min 4.891 s, muestra cambios de -2.76% a -15.86% para los 15 valores comparables. Son diferencias entre ventanas móviles de 24 h, no el volumen negociado en esas dos horas. Cuatro capturas en aproximadamente 3 h 37 min siguen siendo insuficientes para estimar estabilidad a largo plazo, percentiles robustos o distintos regímenes de mercado. Los valores completos y deltas por par/venue están en [issue-7-quote-volume-observations.md](issue-7-quote-volume-observations.md).

## Ejemplo

```bash
python -m scripts.market_selection.analyze_quote_volume_series \
  artifacts/capture-1.json artifacts/capture-2.json \
  --output artifacts/quote-volume-series-analysis.json
```

Los artefactos de GitHub Actions tienen retención finita; para analizar una serie deben descargarse antes de expirar y entregarse como entradas explícitas. Esta herramienta no consulta endpoints externos ni necesita credenciales.
