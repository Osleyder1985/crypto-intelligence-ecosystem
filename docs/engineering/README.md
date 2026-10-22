# Índice de ingeniería

**Estado del conjunto:** documentos versionados en `main`; su presencia en la rama principal no equivale por sí sola a aprobación formal de requisitos, decisiones normativas ni arquitectura. Los documentos marcados como borrador/propuesta siguen sujetos a decisión y trazabilidad mediante Issues/PR.

## Documentos

| Documento | Propósito | Estado |
|---|---|---|
| [Marco maestro](master-framework.md) | Visión, límites, principios, gobernanza, ciclo de vida, arquitectura lógica y decisiones pendientes | Borrador |
| [Matriz normativa](normative-matrix.md) | Referencias, estado de verificación, aplicabilidad inicial, evidencia y decisiones pendientes | Preliminar |
| [Catálogo de requisitos y trazabilidad](requirements-traceability-catalog.md) | Requisitos iniciales, NFR, mapa de objetivos y reglas de trazabilidad | Borrador |
| [Matriz de cierre de aceptación #7/#13](acceptance-closure-matrix-issues-7-13.md) | Descomposición de criterios, evidencia, método de prueba y decisiones pendientes | Propuesta de verificación |
| [Metodología de selección spot](spot-market-selection-methodology.md) | Contrato de datos, fórmulas, controles de calidad y decisión reproducible por par | Especificación propuesta |
| [Evidencia de comisiones Pionex Spot por fills — Issue #18](pionex-fill-fee-evidence.md) | Captura read-only de comisiones históricas por fill; omite IDs y cuerpo privado, marca 100 fills como potencialmente truncados | Herramienta probada; evidencia privada pendiente |
| [Política propuesta fail-closed — Issue #18](issue-18-proposed-decision-policy.md) | Semántica temporal, estados de frescura, comisiones y tamaños sin umbrales inventados | Propuesta; aprobación del producto pendiente |
| [Matriz consolidada de evidencia — Issue #18](issue-18-evidence-matrix.md) | Estado de cada criterio, enlaces a artefactos y bloqueos de cierre sin inventar umbrales | Consolidación; decisión global INDETERMINATE |
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
