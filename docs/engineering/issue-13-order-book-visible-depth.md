# Profundidad visible y localización de niveles del libro — Issue #13

## Objetivo

La salida de `analyze_order_book_snapshot.py` conserva cada nivel bid/ask de la instantánea autorizada y ahora expone tres medidas derivadas para ubicar la profundidad visible sin convertirla en una señal predictiva.

- `distance_from_mid_bps`: distancia absoluta del precio del nivel respecto al punto medio bid/ask, en puntos básicos.
- `cumulative_base_quantity`: cantidad base acumulada desde el mejor precio visible hacia niveles más alejados.
- `cumulative_quote_notional`: nominal cotizado acumulado en el mismo recorrido, calculado como precio por cantidad.

Los bids se recorren de precio más alto a más bajo; los asks, de precio más bajo a más alto. En un libro válido no cruzado, ambos recorridos comienzan por los niveles más cercanos al midpoint. Los campos se serializan como decimales en texto para evitar perder precisión por redondeo binario.

## Interpretación y límites

- Son medidas de una sola instantánea; el proveedor puede limitar la profundidad visible.
- Las órdenes visibles pueden modificarse o cancelarse y no garantizan liquidez ejecutable.
- No se identifican propietarios, órdenes ocultas ni intención de participantes.
- No se calcula una recomendación, un score, una predicción ni se envían órdenes.
- El análisis sigue bloqueado si falta la autorización vigente para `internal_analysis`.

## Validación

La prueba de regresión comprueba distancias y cantidades acumuladas bid/ask con una instantánea sintética y conserva las pruebas existentes para autorización, libro cruzado, orden de niveles y captura fallida.
