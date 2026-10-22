# Eventos descriptivos de soportes y resistencias — Issue #13

- **Script:** scripts/market_selection/analyze_support_resistance.py
- **Pruebas:** tests/market_selection/test_analyze_support_resistance.py
- **Entrada:** artefacto normalizado binance-spot-ohlcv-capture-v1.
- **Parámetros obligatorios:** pivot-left, pivot-right y tolerance-bps. No hay valores por defecto ocultos.
- **Salida:** ohlcv-support-resistance-events-v1; no produce score, ranking ni recomendación.

## Método causal

Un pivote local se reconoce solo cuando se han cerrado pivot-right velas posteriores. El evento de pivote se registra en el cierre de la vela de confirmación, y la zona queda disponible desde el siguiente milisegundo. Por eso el precio histórico del pivote no puede utilizarse como si hubiera sido conocido antes de la confirmación.

Cada pivote crea una zona de soporte (mínimo local) o resistencia (máximo local). Las zonas conservan sus límites originales; un pivote posterior dentro de la tolerancia puede reforzar la zona sin mover retroactivamente su centro. El stream registra creación, refuerzo, toque, rechazo e invalidación. La fuerza se describe con conteos observados (pivotes, toques y rechazos), no con una puntuación ponderada arbitraria.

## Calidad y prevención de look-ahead

- Verifica los hashes y tamaños de los cuerpos originales preservados.
- Excluye velas abiertas o no elegibles.
- Rechaza OHLC imposible, timestamps duplicados/desordenados y cierres fuera de la frontera del intervalo.
- Divide la serie en segmentos cuando hay huecos; ninguna ventana de pivote ni actualización de zona cruza un hueco.
- Los tests verifican que añadir velas futuras no modifica eventos cuyo tiempo ya ocurrió.
- La zona se invalida si un cierre confirmado cruza su límite exterior; los eventos conservan la hora de cierre de la vela que provoca el cambio.

## Límites

Las zonas son una heurística de precios OHLCV, no una reconstrucción de órdenes resting ni prueba de que el precio vaya a reaccionar. Los límites dependen de parámetros explícitos; deben validarse fuera de muestra y por temporalidad. No se asignan umbrales de fuerza, probabilidad o rentabilidad. No se envían órdenes.
