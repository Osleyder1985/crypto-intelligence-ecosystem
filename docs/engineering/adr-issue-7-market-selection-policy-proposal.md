# ADR-07 — Política de selección de mercados Spot (propuesta)

- **Estado:** PROPUESTA NO APROBADA
- **Issue:** [#7 — selección de mercados Spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7)
- **Fecha de preparación:** 2026-10-22
- **Alcance:** metodología de investigación y ranking; no autoriza trading ni certifica rentabilidad.

## Contexto

La selección debe comparar mercados Spot con identidad de símbolo confirmada, turnover, spread, profundidad, slippage, tarifas, frescura y riesgo del activo. Un único número agregado puede ocultar incompatibilidades de unidad, libros no sincronizados, datos ausentes o una dimensión crítica deficiente.

La evidencia actual es exploratoria: cuatro capturas de turnover móvil de 24 h para BTC/ETH/SOL en siete venues y tres snapshots de libro. En cada muestra de turnover, 18/21 respuestas fueron técnicamente accesibles y 15/21 valores comparables; los tres `amount` de Pionex siguen sin unidad documentada. En los snapshots de libro, 18/21 respuestas son válidas por muestra. Bybit devolvió HTTP 403 en el runner; las capturas son secuenciales y no sincronizadas, y Binance/MEXC no aportan timestamp de evento utilizable para la profundidad. La serie de turnover abarca aproximadamente 3 h 37 min, insuficiente para derivar estabilidad de largo plazo.



## Actualización de evidencia verificada — 2026-10-22T15:57Z

- **Cuarta captura de turnover:** [workflow #39809696897](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897), [artefacto #12439416760](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809696897/artifacts/12439416760). Los 21 cuerpos se verificaron por Base64, tamaño y SHA-256; 18/21 fueron HTTP 200 y 15/21 valores comparables. Frente a la tercera muestra, los 15 cambios comparables fueron negativos (-2.76% a -15.86%) en lecturas de ventanas móviles de 24 h separadas por 2 h 1 min. No son volumen transado durante ese intervalo.
- **Tercer snapshot de libro:** [workflow #39809697313](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809697313), [artefacto #12438867580](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39809697313/artifacts/12438867580). Los 21 cuerpos se verificaron; 18/21 snapshots válidos; 6.757 s entre primera y última respuesta. Los snapshots no están sincronizados y los límites de niveles difieren por proveedor.
- Los artefactos y el análisis detallado están documentados en [observaciones de turnover](issue-7-quote-volume-observations.md) y [capturas de libro](issue-7-multi-exchange-probe.md).

**Consecuencia para el ADR:** esta evidencia refuerza la viabilidad de publicar métricas vectoriales descriptivas, pero no autoriza una clasificación definitiva. La cobertura temporal, los 403, la unidad de Pionex, la frescura absoluta de algunos libros y la falta de tamaños/umbrales aprobados mantienen los criterios 7-M01/7-M02 en estado parcial.

La fase exploratoria recomendada ya tiene una implementación en [PR #125](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/125), integrada en el commit `2206882d0a84e763ffff7cac81b01e8c827831b1`: `scripts/market_selection/analyze_spot_market_pareto.py`. Verifica los cuerpos originales y calcula una frontera por activo con cuatro dimensiones (turnover, spread y profundidad bid/ask) sin pesos ni umbrales. Sobre los artefactos de las 15:57Z produjo 15 vectores estructuralmente utilizables y excluyó seis observaciones (Bybit HTTP 403 y Pionex con unidad de turnover indeterminada). La frontera de esa captura fue BTC: Binance/MEXC; ETH: Binance/Bitget/MEXC; SOL: Binance/Bitget/MEXC.

Este resultado es un perfil de Pareto de snapshots, no una decisión de elegibilidad ni un ranking de activos. Los timestamps de origen no son uniformes, las capturas no están sincronizadas y la política de frescura no está aprobada. Por ello, **el ADR sigue como PROPUESTA NO APROBADA**; la implementación no sustituye la aprobación del propietario ni cierra el Issue #7.

## Decisión propuesta

### 1. Separar elegibilidad de ranking

Antes de comparar una métrica económica, cada observación debe pasar controles independientes:

1. **Identidad:** símbolo nativo, base, quote y mercado Spot confirmados por metadata oficial del venue.
2. **Integridad:** respuesta completa preservada, tamaño real, SHA-256 y esquema válidos; no aceptar un prefijo truncado como payload completo.
3. **Comparabilidad:** unidades, ventana, semántica del campo y mercado deben estar documentados. No equiparar volumen base con turnover cotizado. En Pionex, `amount` se preserva como dato bruto pero no se considera turnover cotizado comparable hasta documentar oficialmente su unidad.
4. **Disponibilidad objetivo:** el par exacto en Pionex debe confirmarse por separado; acceso regional o de cuenta no se infiere de un endpoint público.
5. **Frescura:** solo PASS si el tipo de timestamp permite calcular la edad con una política versionada. Sin timestamp de evento o sin unidad demostrada, usar INDETERMINATE; IDs de secuencia no son timestamps.
6. **Costes:** distinguir tarifa pública de referencia de tarifa efectiva por cuenta. Un coste neto personalizado requiere evidencia de cuenta read-only y una conversión verificable de la moneda de comisión.

Los estados son PASS, FAIL e INDETERMINATE. Un dato ausente, una respuesta 403 o una unidad desconocida nunca se convierten en cero ni en prueba de que el mercado no exista.

### 2. Presentar un vector de métricas antes de cualquier puntuación total

Para cada par elegible, exponer como mínimo:

- turnover cotizado móvil de 24 h, con semántica de proveedor y serie temporal;
- spread bid-ask en bps;
- profundidad bid y ask separadas, por banda de precio y por niveles recibidos;
- VWAP, slippage y cobertura de libro para una curva paramétrica de tamaños de orden;
- coste round-trip con supuestos y tarifas identificados;
- estabilidad histórica de turnover/spread y cobertura de la serie;
- riesgo del activo, fuentes, fecha, unidad y datos ausentes.

No combinar esos valores en una suma ponderada mientras no exista una decisión aprobada sobre pesos, normalización y compensación entre dimensiones. Como salida exploratoria, mostrar perfiles por dimensión y dominancia de Pareto; no fingir un orden total si los activos intercambian ventajas entre coste, liquidez, estabilidad y riesgo.

### 3. Umbrales explícitos, no inventados

Los límites max_spread_bps, banda de profundidad, tamaño de orden, slippage máximo, edad de snapshot, lag de fuente y tarifas deben ser parámetros de configuración versionados. Cada configuración de aceptación debe registrar estado de aprobación, referencia de aprobación, versión y dimensiones críticas. Sin esa evidencia, la decisión global permanece INDETERMINATE.

Las normas ISO consultadas no proporcionan un SLA universal de frescura de mercado ni un spread/slippage máximo aplicable a todos los activos. La documentación del exchange describe los contratos y límites de API, no una política de inversión del producto.

### 4. Tratamiento de series históricas

- El turnover de ticker es una ventana móvil de 24 h; el cambio entre dos capturas no es volumen negociado durante el tiempo entre ellas.
- Estimar estabilidad con muestras repetidas, cobertura explícita, huecos, duplicados y métricas robustas. La duración y la cobertura mínimas deben definirse antes de validar el conjunto, no después de ver el resultado.
- Comparar periodos equivalentes y distinguir cambios de mercado de cambios de proveedor, parser, universo y metodología.
- Los snapshots de libro sirven para coste instantáneo aproximado; no reconstruyen profundidad histórica.
- Mantener un conjunto temporal fuera de muestra para validar cualquier regla de ranking o predicción y registrar resultados negativos.

## Alternativas consideradas

1. **Umbrales numéricos fijos ahora:** rechazado por falta de base empírica suficiente y ausencia de un requisito comercial de tamaño/latencia.
2. **Puntuación ponderada única ahora:** rechazada porque los pesos y la capacidad de compensación entre dimensiones serían decisiones arbitrarias.
3. **Vector de métricas + gates de elegibilidad + ranking Pareto exploratorio:** recomendada como fase intermedia; conserva información y hace explícitas las incompatibilidades sin inventar umbrales.
4. **No producir ninguna comparación:** demasiado restrictivo; se puede publicar evidencia descriptiva con estado y limitaciones, sin llamarla recomendación final.

## Consecuencias

- El sistema puede comparar descriptivamente snapshots antes de disponer de una política final, pero no declarará un mercado elegible si una dimensión crítica es indeterminada.
- La UI debe separar rankings por dimensión de un eventual score global.
- Un score global solo se habilita cuando el propietario apruebe criterios, pesos, tamaño de referencia, ventanas, frescura y manejo de faltantes.
- La falta de acceso a Bybit desde CI se documenta como limitación del entorno; no se intenta eludir la restricción.
- La política no certifica cumplimiento ISO, rentabilidad, ejecución futura ni disponibilidad regional.

## Evidencia necesaria antes de cambiar el estado a aprobada

- Serie representativa de turnover y snapshots repetidos, con artefactos íntegros y cobertura cuantificada.
- Medición y tratamiento explícito de timestamps por proveedor.
- Curvas de coste y profundidad para tamaños de referencia definidos.
- Evidencia de tarifas aplicables al flujo del producto y, si se requiere coste por cuenta, evidencia privada autorizada.
- Sensibilidad del ranking a los parámetros candidatos y resultados fuera de muestra.
- Revisión y aprobación explícita del propietario registrada con fecha y versión.

**Estado final de este ADR:** propuesta documentada, no aprobada. No fija umbrales numéricos ni cierra el Issue #7.
