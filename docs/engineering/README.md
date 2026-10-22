# Índice de ingeniería

- [Contrato de evidencia fundamental y on-chain (Issue #134)](issue-134-fundamental-onchain-dictionary.md)
**Estado del conjunto:** documentos versionados en `main`; su presencia en la rama principal no equivale por sí sola a aprobación formal de requisitos, decisiones normativas ni arquitectura. Los documentos marcados como borrador/propuesta siguen sujetos a decisión y trazabilidad mediante Issues/PR.

## Documentos

| Documento | Propósito | Estado |
|---|---|---|
| [Marco maestro](master-framework.md) | Visión, límites, principios, gobernanza, ciclo de vida, arquitectura lógica y decisiones pendientes | Borrador |
| [Matriz normativa](normative-matrix.md) | Referencias, estado de verificación, aplicabilidad inicial, evidencia y decisiones pendientes | Preliminar |
| [Catálogo de requisitos y trazabilidad](requirements-traceability-catalog.md) | Requisitos iniciales, NFR, mapa de objetivos y reglas de trazabilidad | Borrador |
| [Matriz de cierre de aceptación #7/#13](acceptance-closure-matrix-issues-7-13.md) | Descomposición de criterios, evidencia, método de prueba y decisiones pendientes | Propuesta de verificación |
| [Matriz de fuentes OHLCV históricas — Issue #13](issue-13-historical-candle-source-matrix.md) | Endpoints, campos, límites, timestamps y controles anti-look-ahead para siete venues | Investigación documental; no es implementación ni aprobación de estrategia |
| [Captura histórica OHLCV Binance Spot — Issue #13](issue-13-binance-historical-ohlcv-capture.md) | Adaptador paginado, ventanas UTC, respuestas originales, hashes, detección de huecos y velas cerradas | Primera fuente implementada; solo Binance Spot |
| [Captura histórica OHLCV Pionex Spot — Issue #13](issue-13-pionex-historical-ohlcv-capture.md) | Pagina el historial disponible y conserva cuerpos íntegros; mantiene ambiguas unidad de volumen y rol temporal | Captura raw implementada; análisis cross-venue INDETERMINATE |
| [Auditoría de enforcement de licencias — Issue #143](issue-143-provider-license-runtime-enforcement.md) | Criterios verificables para bloquear usos no autorizados antes de capturas/uso de datos y distinguir permiso de integridad de captura | Hallazgo abierto; no es enforcement runtime implementado |
| [Perfil descriptivo de riesgo OHLCV — Issue #13](issue-13-ohlcv-risk-profile.md) | Retornos observados, volatilidad por vela, drawdown de cierres y controles de huecos | Descriptivo; no predice ni rankea |
| [Eventos de movimiento OHLCV — Issue #13](issue-13-ohlcv-movement-events.md) | Detección parametrizada de movimientos y anomalías de turnover sin usar velas futuras | Descriptivo; causalidad no establecida |
| [Eventos de soporte y resistencia — Issue #13](issue-13-support-resistance-events.md) | Pivotes confirmados, zonas, toques, rechazos e invalidaciones con disponibilidad temporal explícita | Heurística OHLCV; no predice reacción del precio |
| [Historial y comparación de evaluaciones — Issue #13](issue-13-evaluation-history-records.md) | Registros locales inmutables con SHA-256 y comparación conservadora de evaluaciones | Prototipo local; no sustituye persistencia central |
| [Análisis de series de turnover Spot 24 h — Issue #7](issue-7-quote-volume-series-analysis.md) | Verifica integridad y compara capturas repetidas de turnover móvil sin umbrales ni ranking | Herramienta descriptiva; requiere serie representativa |
| [Frontera de Pareto exploratoria Spot — Issue #7](issue-7-exploratory-pareto-analysis.md) | Compara turnover, spread y profundidad bid/ask por activo sin pesos ni umbrales | Exploratorio; decisión global INDETERMINATE |
| [Observaciones de volumen cotizado 24 h — Issue #7](issue-7-quote-volume-observations.md) | Capturas reales comparadas para 21 combinaciones venue/par; 15 valores por captura comparables como turnover cotizado con la semántica actual | Evidencia exploratoria; no demuestra estabilidad histórica ni constituye ranking |
| [Sondeo de libros Spot de siete exchanges — Issue #7](issue-7-multi-exchange-probe.md) | Captura read-only de BTC/ETH/SOL cotizados en USDT para Binance, OKX, Bybit, MEXC, Gate, Bitget y Pionex | Cobertura técnica parcial; no es selección de mercado ni aprobación de liquidez |
| [Metodología de selección spot](spot-market-selection-methodology.md) | Contrato de datos, fórmulas, controles de calidad y decisión reproducible por par | Especificación propuesta |
| [Evidencia de comisiones Pionex Spot por fills — Issue #18](pionex-fill-fee-evidence.md) | Captura read-only de comisiones históricas por fill; omite IDs y cuerpo privado, marca 100 fills como potencialmente truncados | Herramienta probada; evidencia privada pendiente |
| [Política fail-closed — Issue #18](issue-18-proposed-decision-policy.md) | Semántica temporal, estados de frescura, comisiones y tamaños sin umbrales inventados | Adoptada para investigación pública Spot; no habilita ejecución |
| [Matriz consolidada de evidencia — Issue #18](issue-18-evidence-matrix.md) | Evidencia, alcance adoptado y límites del modo de investigación pública | Consolidación; decisión económica INDETERMINATE cuando falten datos críticos |
| [Aplicabilidad de normas ISO — Issue #18](issue-18-data-quality-standards.md) | ISO 8601 para representación temporal e ISO/IEC 25012 para requisitos/medidas de calidad; ninguna fija un umbral universal de frescura de exchange | Nota de aplicabilidad; no certificación |
| [Fixtures de frescura en vivo — Issue #18](issue-18-live-freshness-fixtures.md) | Pruebas de PASS/FAIL/INDETERMINATE para política aprobada, timestamps ausentes/futuros y desfase de reloj | Límites solo sintéticos; no son política de producto |
| [Escenario mínimo común por filtros — Issue #18](issue-18-minimum-common-notional-scenario.md) | Calcula una referencia de frontera con filtros públicos; unidad de Pionex minAmount no documentada, por lo que el escenario queda INDETERMINATE | Hipótesis explícita; no es mínimo común verificado |
| [Mediciones observadas de frescura — Issue #18](issue-18-freshness-observations-2026-10-22.md) | Veintiún deltas Pionex de siete artefactos CI y limitaciones de inferencia | Muestra descriptiva; no aprueba umbral de producción |
| [Curvas paramétricas de coste del libro — Issue #18](issue-18-depth-cost-curves.md) | VWAP/slippage acumulado, filtros oficiales de cada símbolo y elegibilidad de tamaño explícitamente indeterminada | Análisis descriptivo; coste total pendiente |
| [Cobertura de profundidad por proveedor — Issue #18](issue-18-depth-coverage.md) | Límites oficiales de snapshots Binance/Pionex, pesos de API y cobertura parcial | Referencia oficial; captura máxima no equivale a libro completo |
| [Mediciones temporales Pionex Spot — Issue #18](issue-18-pionex-timing-measurements.md) | Deltas observados de timestamps de actualización/respuesta/captura en artefactos CI; muestra exploratoria, no umbral aprobado | Evidencia medida; política pendiente |
| [Semántica temporal Binance Spot](binance-market-data-timestamp-semantics.md) | Significado oficial de timestamps, sincronización del libro y límites para evaluar frescura | Evidencia documental; no es política aprobada |
| [Hoja de ruta](roadmap.md) | Fases, dependencias, puertas de salida, riesgos y evidencias | Propuesta |
| [Gobernanza y riesgos](governance-and-risk-model.md) | Responsabilidades, dominios de control, Definition of Done, registro inicial de riesgos y puertas de decisión | Propuesta |

## Issues relacionados

- [#3 — Gobernanza ISO/IEC](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/3)
- [#4 — Modelo de ingeniería y ciclo de vida](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/4)
- [#5 — Clientes web, Android, iOS y escritorio opcional](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/5)
- [#6 — Plataforma central de datos y API común](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/6)
- [#7 — Selección reproducible de mercados spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7)
- [#8 — Arquitectura de referencia y trazabilidad](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/8)
- [#9 — Evaluación del stack mediante criterios y PoC](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/9)
- [#10 — Evaluación de alojamiento y costes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/10)
- [#11 — Issue rector del marco maestro](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- [#13 — Evaluación histórica, ranking, análisis de eventos, liquidez y soportes/resistencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- [#18 — Frescura, comisiones y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18)

## Reglas de mantenimiento

- Cada documento debe enlazar los Issues que motivan sus cambios.
- Las decisiones aprobadas se registran con evidencia y responsable; las propuestas no se presentan como decisiones vigentes.
- Los cambios se hacen en ramas y PR; no se edita `main` directamente.
- Si una referencia normativa cambia de edición o estado, se actualiza la matriz con la fuente oficial y la fecha de consulta.
- Después de cada cambio estructural, revisar los enlaces internos y este índice.
