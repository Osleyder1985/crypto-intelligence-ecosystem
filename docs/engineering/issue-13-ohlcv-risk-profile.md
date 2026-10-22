# Perfil descriptivo de riesgo OHLCV — Issue #13

- **Script:** scripts/market_selection/analyze_ohlcv_risk_profile.py
- **Pruebas:** tests/market_selection/test_analyze_ohlcv_risk_profile.py
- **Entrada:** artefacto normalizado binance-spot-ohlcv-capture-v1.
- **Salida:** ohlcv-descriptive-risk-profile-v1; no genera ranking ni recomendación.

## Métricas

Calcula retorno observado del periodo, máximo drawdown close-to-close observado, desviación estándar por vela de log-returns y retornos simples, mayor pérdida/ganancia observada por intervalo consecutivo y volúmenes medios por vela cerrada. La volatilidad anualizada se omite por defecto; solo se calcula si el usuario suministra explícitamente periods_per_year. No se oculta una convención de anualización.

## Protección contra sesgo temporal y datos ausentes

- Solo usa velas que estén marcadas como cerradas y elegibles para análisis de velas cerradas.
- Rechaza timestamps duplicados o desordenados, precios de cierre no positivos y volúmenes negativos/no finitos.
- Detecta huecos comparando el siguiente open time esperado para el intervalo.
- Omite el retorno por vela cuando hay un hueco entre cierres; no interpreta un cambio de varias velas como un retorno de una sola vela.
- No interpola huecos ni convierte valores ausentes en cero.
- El drawdown se calcula solo con cierres observados; no es un máximo drawdown intrabar y puede subestimar rutas no observadas si existen huecos.

## Límites

Es una base descriptiva, no un modelo predictivo. No estima concentración de holders, tokenomics, unlocks, calidad del proyecto, profundidad histórica, coste de ejecución ni riesgo regulatorio. Esos dominios necesitan fuentes específicas. No establece umbrales, no decide elegibilidad, no genera score global y no envía órdenes.
