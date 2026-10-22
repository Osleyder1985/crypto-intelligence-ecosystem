# Captura histórica OHLCV Spot de Binance — Issue #13

- **Script:** `scripts/market_selection/capture_binance_spot_ohlcv.py`
- **Pruebas offline:** `tests/market_selection/test_capture_binance_spot_ohlcv.py`
- **Fuente oficial:** [Binance Spot REST — Kline/Candlestick Data](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data); host público de datos: `https://data-api.binance.vision`.
- **Estado:** primer adaptador de captura implementado en rama de trabajo; no es todavía una plataforma histórica multiexchange ni evidencia de análisis rentable.

## Contrato

La CLI exige símbolo nativo, intervalo y una ventana UTC en milisegundos. La ventana es semiabierta `[start, end)), y ambos extremos deben alinearse con límites de vela. Esto evita ambigüedad sobre la vela final y permite comprobar la secuencia esperada.

```bash
python -m scripts.market_selection.capture_binance_spot_ohlcv \
  --symbol BTCUSDT --interval 1h \
  --start-time-ms 1792454400000 --end-time-ms 1792540800000 \
  --output artifacts/binance-spot-ohlcv.json
```

El adaptador pagina usando el límite oficial de 1000 velas por petición; ese límite es de la API por petición, no un límite total de bytes ni de velas de la herramienta. Conserva cada respuesta original en Base64 con SHA-256, tamaño, HTTP, URL y hora UTC de captura; normaliza OHLC, volumen base/cotizado, trades y campos taker sin descartar la fila original.

## Controles de calidad y sesgo temporal

- Rechaza esquema inválido, valores no finitos, OHLC incoherente, volúmenes negativos, respuesta fuera de ventana y duplicados entre páginas.
- Calcula la secuencia esperada para detectar huecos y devuelve `PARTIAL` si falta alguna vela o falla una página.
- Marca si la vela ya estaba cerrada al capturarla; la vela en curso no es elegible para análisis de velas cerradas.
- No completa huecos por interpolación, no convierte faltantes en cero y no afirma que un historial capturado hoy contenga libro de órdenes histórico.
- La salida es un artefacto reproducible de datos; no detecta por sí misma movimientos, causalidad, soportes/resistencias ni predice precios.

## Límites pendientes

Este PR cubre Binance Spot. Las otras fuentes del registro OHLCV requieren adaptadores independientes porque difieren en esquemas, paginación, unidades temporales y límites. Antes de comparar venues hay que normalizar sin perder el dato bruto, verificar velas cerradas, cobertura, intervalos, timezone y licencia/condiciones. La selección del universo y la evaluación predictiva siguen pendientes.
