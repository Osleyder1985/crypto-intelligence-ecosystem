# Evaluación preliminar de cobertura de requisitos

- **Estado:** evaluación documental preliminar; no constituye línea base aprobada ni auditoría técnica completa.
- **PR de trabajo:** [#271 — Plan Maestro](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/271).
- **Catálogo fuente:** [`requirements-traceability-catalog.md`](requirements-traceability-catalog.md).
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11).
- **Auditoría relacionada:** [#270](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/270).
- **Regla:** este documento evalúa cobertura documental y verificabilidad; no crea ni reemplaza identificadores `REQ-P-*` o `NFR-*`.

## 1. Alcance y método

Se contrastaron los objetivos conocidos del producto con el catálogo existente y la trazabilidad que este declara. La clasificación es una primera pasada basada en documentos y estado visible del repositorio; no equivale a revisar cada archivo, ejecutar todas las pruebas, comprobar cada proveedor ni validar resultados de mercado.

Estados utilizados:

- **Cubierto documentalmente:** hay requisito explícito y criterio de aceptación razonablemente alineado con el objetivo.
- **Parcial:** existe requisito relacionado, pero falta concretar alcance, decisión, escenario o criterio de aceptación.
- **Brecha documental aparente:** no se encontró una formulación explícita suficiente en el catálogo revisado.
- **Pendiente de evidencia técnica:** la documentación prevé la capacidad, pero no prueba que esté implementada o funcione extremo a extremo.
- **Pendiente de decisión:** el propietario debe resolver una ambigüedad de alcance antes de fijar la línea base.

## 2. Matriz de cobertura de objetivos del producto

| Objetivo del producto | IDs existentes relevantes | Evaluación documental preliminar | Brecha / comprobación necesaria |
|---|---|---|---|
| Iniciar investigaciones bajo demanda, con parámetros y estados claros | REQ-P-001, REQ-P-008, REQ-P-018 | Cubierto documentalmente | Pendiente de evidencia técnica: flujo E2E real, persistencia de estado, cancelación, errores parciales e idempotencia. |
| Identidad correcta de activo, red/contrato y par spot | REQ-P-003, REQ-P-011, REQ-P-029 | Cubierto documentalmente | Verificar resolución de símbolos ambiguos, activos envueltos, redes y discrepancias entre exchanges; no asumir que el ticker identifica por sí solo un activo. |
| Evaluar inversión a corto, medio y largo plazo | REQ-P-012, REQ-P-013, REQ-P-016, REQ-P-022 | Parcial | Falta una definición aprobable de cada horizonte y reglas de comparabilidad, invalidación, riesgo y datos mínimos por horizonte. No fijar duraciones arbitrarias sin decisión y justificación. |
| Reconstruir movimientos alcistas y bajistas y sus puntos de inicio/fin | REQ-P-023, REQ-P-024, NFR-014 | Cubierto documentalmente | Pendiente de evidencia técnica: definiciones reproducibles de episodio, confirmación temporal, pruebas anti-look-ahead y casos con pivotes revisados. |
| Identificar noticias/eventos asociados a inicio, aceleración, agotamiento o reversión | REQ-P-023, REQ-P-024, REQ-P-020 | Parcial | El catálogo advierte correctamente que asociación temporal no prueba causalidad. Faltan criterios de relevancia, fuentes elegibles/autorizadas, cobertura, hipótesis alternativas y protocolo para graduar la evidencia. |
| Detectar soportes y resistencias en varias temporalidades | REQ-P-026, NFR-013, NFR-014, NFR-016 | Cubierto documentalmente | Pendiente de evidencia técnica: comparar métodos, probar estabilidad y sensibilidad, registrar invalidación y evitar información futura en los resultados históricos. |
| Localizar liquidez/órdenes compradoras y vendedoras | REQ-P-025, REQ-P-029, NFR-003, NFR-011 | Parcial | La profundidad bid/ask y las métricas de liquidez están cubiertas, pero debe aclararse si el producto pretende mostrar únicamente liquidez observada en libros públicos o estimar zonas de concentración/posibles órdenes. Los libros visibles son instantáneas, pueden cambiar y no prueban intención ni ejecución futura. |
| Proponer ubicaciones de compra/venta para análisis spot | REQ-P-004, REQ-P-012, REQ-P-016, REQ-P-025, REQ-P-026 | Parcial | No se encontró un criterio explícito completo que conecte entrada, invalidación, objetivos/salida, costes, liquidez, riesgo y horizonte en una propuesta evaluable. Antes de ampliar el catálogo, confirmar si ya existe un Issue que cubra exactamente esta decisión; si no, documentar la brecha bajo el Issue apropiado y conservar IDs existentes. No habilitar ejecución de órdenes. |
| Análisis técnico, cuantitativo, fundamental/on-chain y riesgo según aplicabilidad | REQ-P-009, REQ-P-014, REQ-P-015, REQ-P-016 | Cubierto documentalmente | Falta verificar el inventario real de métodos/datasets y criterios por clase de activo. Los datos no aplicables o ausentes no deben convertirse silenciosamente en cero. |
| Guardar evaluaciones históricas y explicar diferencias entre ejecuciones | REQ-P-005, REQ-P-020, REQ-P-021, NFR-011 | Cubierto documentalmente | Pendiente de evidencia técnica: reproducción con referencias inmutables, separación de cambios de mercado frente a cambios de datos/método y tratamiento de datos históricos que ya no estén disponibles. |
| Clasificar criptomonedas de mejor a peor | REQ-P-022, REQ-P-012, REQ-P-017, NFR-017 | Cubierto documentalmente | Pendiente de aprobar horizonte, universo, pesos/método, comparabilidad, exclusiones, antigüedad de datos y tratamiento de incertidumbre. No publicar un ranking como universal si mezcla horizontes o datos no comparables. |
| Web, escritorio, Android e iOS con datos compartidos | REQ-P-002, REQ-P-006, REQ-P-027, REQ-P-030, REQ-P-032 | Pendiente de decisión + evidencia | REQ-P-006 nombra web, Android e iOS; REQ-P-030 trata escritorio instalado como opcional según casos de uso. Confirmar explícitamente el alcance final de escritorio y después demostrar que los clientes usan los mismos contratos y reglas de negocio. |
| Plataforma central, API versionada y políticas de frescura | REQ-P-002, REQ-P-032, NFR-003, NFR-009 | Cubierto documentalmente | Pendiente de evidencia técnica: API y almacenamiento canónicos funcionando, pruebas de contrato, autorización, caché, frescura y consistencia entre clientes. |
| Investigación reproducible, validación y prevención de sobreajuste | REQ-P-005, REQ-P-009, REQ-P-013, REQ-P-014, REQ-P-017, NFR-012, NFR-013, NFR-014 | Cubierto documentalmente | Los protocolos propuestos deben convertirse en experimentos reproducibles, con datos point-in-time, benchmarks previos y resultados negativos conservados. |
| Seguridad, privacidad, límites de operación y resiliencia | REQ-P-007, REQ-P-008, REQ-P-028, REQ-P-031, REQ-P-033, NFR-002, NFR-004, NFR-005, NFR-015 | Cubierto documentalmente | Pendiente de evidencia: modelo de amenazas, permisos efectivos, manejo de secretos, backup/restore, observabilidad y verificación de protecciones del repositorio. |
| Calidad de nivel mundial demostrable y no meramente declarada | REQ-P-017, NFR-001, NFR-006, NFR-007, NFR-010, NFR-012, NFR-017, NFR-018 | Parcial | Se requiere protocolo comparativo, competidores/referencias justificadas, datasets y versiones, métricas predefinidas, resultados repetibles y publicación de limitaciones. La etiqueta “Top Mundial” no es criterio de aceptación verificable por sí sola. |

## 3. Hallazgos concretos por requisitos existentes

### 3.1 REQ-P-023 y REQ-P-024 — episodios y eventos

Fortaleza: el catálogo requiere marcas temporales, fuentes, relevancia, alternativas, memoria de eventos y control de fuga temporal; también prohíbe inferir causalidad por mera proximidad temporal.

Trabajo pendiente:
- definir con precisión los estados de un episodio y qué datos estaban disponibles en cada instante;
- distinguir hora del evento, publicación, primera detección, captura y procesamiento;
- tratar noticias corregidas, duplicadas, sindicadas, contradictorias o publicadas después del movimiento;
- registrar hipótesis alternativas y límites de cobertura;
- verificar si la evidencia permite hablar de asociación, contribución plausible o causalidad demostrada; por defecto, no afirmar causalidad.

### 3.2 REQ-P-025 y REQ-P-026 — profundidad, órdenes y zonas técnicas

Fortaleza: existen requisitos para profundidad bid/ask, operaciones recientes, spread, desequilibrio, slippage y zonas de soporte/resistencia con invalidación e incertidumbre.

Trabajo pendiente:
- separar libro de órdenes actual, histórico de libros (si existe), operaciones ejecutadas y estimaciones derivadas;
- etiquetar exchange, par, timestamp, secuencia/cobertura y estado de frescura;
- no llamar “órdenes reales pendientes” a zonas estimadas a partir de velas o volumen;
- definir tamaños de referencia y método para estimar impacto solo tras aprobarlos;
- probar que las zonas retrospectivas no se calculan con datos posteriores a la fecha evaluada;
- describir la ubicación de compra/venta como escenario analítico condicionado, nunca como garantía ni ejecución.

### 3.3 REQ-P-012, REQ-P-016 y REQ-P-022 — conclusión, riesgo y ranking

Trabajo pendiente:
- definir cómo se separan calidad de evidencia, riesgo, puntuación del activo y oportunidad por horizonte;
- no permitir que una puntuación agregada oculte datos críticos ausentes;
- definir cuándo dos evaluaciones son comparables y cómo se trata un cambio de metodología;
- evaluar estabilidad del ranking y sensibilidad a pesos/universo;
- permitir estados indeterminado, parcial o no comparable.

### 3.4 REQ-P-006 y REQ-P-030 — alcance de clientes

Hay una ambigüedad que debe resolver el propietario: el requisito multiplataforma enumera web, Android e iOS, mientras que el requisito de estrategia trata el escritorio instalado como opcional. El Plan Maestro no debe convertir esa opción en decisión implícita. La arquitectura de datos compartida debe permanecer independiente de la decisión de cliente.

### 3.5 REQ-P-028 y REQ-P-033 — normas y terminado verificable

Fortaleza: distinguen referencias oficiales, aplicabilidad, evidencia y estado; también exigen puertas de fase y trazabilidad.

Trabajo pendiente:
- registrar la edición y el estado de cada fuente normativa al revisarla;
- diferenciar propuesta, aprobación interna, evidencia de conformidad y certificación;
- no marcar una fase como completada solo por entregar documentación o tener un workflow verde;
- registrar comandos, entorno, versión, datos de prueba, resultado, excepciones y defectos pendientes.

## 4. Revisión transversal de los 18 NFR

| Grupo | IDs | Evaluación preliminar | Evidencia que falta antes de fijar aceptación |
|---|---|---|---|
| Rendimiento, fiabilidad y resiliencia | NFR-001, NFR-002, NFR-015 | Parcial | Carga esperada, perfiles representativos, límites de servicio, escenarios de fallo y objetivos aprobados; benchmarks y recuperación reproducibles. |
| Calidad, procedencia e integridad temporal de datos | NFR-003, NFR-011, NFR-014 | Cubierto documentalmente | Umbrales por fuente/mercado justificados, fixtures, point-in-time, integridad, cobertura y pruebas de huecos/duplicados. |
| Seguridad y privacidad | NFR-004, NFR-005 | Cubierto documentalmente | Amenazas y datos reales identificados, permisos mínimos, revisión de secretos, ciclo de vida de datos y evidencias de controles. |
| Usabilidad y accesibilidad | NFR-006, NFR-018 | Parcial | Tareas críticas por plataforma, criterios de accesibilidad aplicables, usuarios/tecnologías de asistencia y resultados observados. |
| Mantenibilidad y portabilidad | NFR-007, NFR-008 | Parcial | Criterios acordados, PoC comparativas, restauración/exportación y evidencia del coste real de cambio o migración. |
| Observabilidad y coste | NFR-009, NFR-010 | Parcial | Inventario de señales operativas, alertas accionables, escenarios de carga y medición de coste con límites aprobados. |
| Calibración, robustez y calidad de ranking | NFR-012, NFR-013, NFR-017 | Cubierto documentalmente | Métricas apropiadas al objetivo, benchmarks previos, particiones temporales, sensibilidad predefinida e intervalos de incertidumbre. |
| Transparencia de límites | NFR-016 | Cubierto documentalmente | Casos de prueba explícitos de datos ausentes/conflictivos, abstención, cobertura insuficiente y resultados no comparables. |

**Conclusión NFR:** los 18 atributos están identificados, pero identificar un atributo no equivale a cumplirlo. Los umbrales de aceptación siguen pendientes donde el catálogo no define contexto, justificación y aprobación. No asignar valores arbitrarios solo para hacer que la tabla parezca completa.

## 5. Brechas prioritarias y acción recomendada

1. **Bloqueo de alcance:** resolver la definición de corto/medio/largo plazo y si escritorio instalado forma parte del alcance comprometido.
2. **Integridad de la decisión analítica:** formalizar la relación entre evidencia, puntuación, riesgo, horizonte y estado de abstención.
3. **Orden-book frente a propuesta de entrada/salida:** separar observaciones de mercado de zonas estimadas y escenarios analíticos.
4. **Eventos y causalidad:** convertir la cautela ya documentada en criterios de aceptación y pruebas de casos difíciles.
5. **E2E técnico:** comprobar con evidencia que identidad de activo, captura autorizada, análisis, informe, historial y comparación se conectan en un flujo real.
6. **NFR medibles:** aprobar umbrales por contexto y documentar el protocolo antes de ejecutar el benchmark definitivo.
7. **Trazabilidad bidireccional:** enlazar requisitos con Issues existentes, ADR, componentes, pruebas, CI y release; revisar las relaciones ya propuestas con Issues #3–#22 sin asumir que sean definitivas.
8. **Roles reales:** distinguir roles propuestos de responsables efectivamente asignados. En un proyecto de propietario único asistido por IA, registrar la limitación de independencia de revisión.

## 6. Decisiones que no deben tomarse por inferencia

- No crear IDs nuevos hasta buscar duplicados y confirmar una brecha real.
- No convertir objetivos iniciales de cobertura de exchanges en resultados alcanzados sin evidencia por exchange/par.
- No habilitar captura de nuevas fuentes ni ampliar permisos externos sin autorización.
- No habilitar ejecución de órdenes reales como consecuencia de definir ubicaciones de compra/venta.
- No declarar certificación, conformidad ISO, rentabilidad o superioridad mundial sin evidencia adecuada.
- No considerar implementado o verificado un requisito por su presencia en el catálogo o por checks documentales exitosos.

## 7. Criterios de salida de esta evaluación

La evaluación podrá elevarse a candidata para aprobación cuando:
- cada objetivo confirmado tenga requisitos existentes enlazados o una brecha explícita justificada;
- cada brecha tenga Issue rector existente o se documente por qué no existe uno equivalente;
- los criterios de aceptación críticos sean observables y reproducibles;
- los estados de requisito, implementación y verificación se mantengan separados;
- las contradicciones de alcance se resuelvan mediante decisión explícita del propietario;
- se haya comprobado la evidencia técnica del flujo E2E prioritario;
- el propietario apruebe expresamente la línea base candidata.

**Estado actual:** evaluación documental preliminar guardada para revisión en el PR #271. No es una aprobación del catálogo, no cierra Issues y no afirma que el producto esté completo.

## 8. Revisión de trazabilidad con Issues funcionales vigentes

Esta sección amplía la primera pasada documental con Issues de producto y auditoría que aparecieron después del mapa inicial del catálogo. Los enlaces indican relación de alcance, **no** prueban que un requisito esté implementado ni que todos los criterios del Issue estén satisfechos. Los estados se consultaron en GitHub durante esta revisión; volver a verificarlos antes de declarar una fase completada.

| Issue | Relación con requisitos existentes | Estado observado y conclusión documental | Evidencia pendiente / límite |
|---|---|---|---|
| [#128 — Flujo integral de investigación por activo](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) | REQ-P-001, REQ-P-004, REQ-P-005, REQ-P-008, REQ-P-012, REQ-P-020, REQ-P-021, REQ-P-023–REQ-P-027, REQ-P-032; NFR-003, NFR-011, NFR-012, NFR-014, NFR-016 | Abierto; Issue rector del flujo E2E. | Demostrar el flujo de entrada a informe e historial en una ejecución reproducible; los componentes analíticos parciales no prueban integración E2E completa. |
| [#130 — Integrar analizadores en informe E2E](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/130) | REQ-P-004, REQ-P-005, REQ-P-020, REQ-P-026; NFR-003, NFR-011, NFR-014, NFR-016 | Cerrado según el estado consultado. | El cierre de este incremento no demuestra por sí solo que estén integradas noticias, fundamentales/on-chain, metodologías aprobadas de horizonte o todo el flujo exigido por #128. Revisar su evidencia/PR si se usa como criterio de fase. |
| [#132 — Noticias y eventos como posibles detonantes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132) | REQ-P-023, REQ-P-024; NFR-011, NFR-014, NFR-016 | Abierto; contrato y pruebas descritos en el Issue, con alcance de fuentes sujeto a autorización. | Verificar cobertura real de eventos y fuentes habilitadas. La relación temporal no equivale a causalidad; no declarar que existe captura de noticias en vivo sin evidencia de fuente autorizada y ejecución real. |
| [#133 — Metodologías por horizonte](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/133) | REQ-P-009, REQ-P-012, REQ-P-013, REQ-P-014, REQ-P-016, REQ-P-022; NFR-001, NFR-012, NFR-013, NFR-017 | Abierto; decisiones metodológicas y criterios de aceptación siguen pendientes. | No inventar duraciones, pesos ni umbrales. Mantener conclusiones por horizonte como INDETERMINATE hasta que la metodología y la evidencia permitan una evaluación válida. |
| [#134 — Fuentes y métricas fundamentales/on-chain](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/134) | REQ-P-011, REQ-P-015, REQ-P-020; NFR-003, NFR-011, NFR-016 | Abierto según el Issue consultado; existe PR #217 cerrado con validaciones del contrato de observaciones. | La validación del esquema no demuestra captura de datos ni cobertura de métricas. Verificar fuente, periodo, unidades, cobertura, condiciones de uso y distinción entre no aplicable/no disponible/no accesible. |
| [#266 — Fallos estructurados del limitador](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/266) | REQ-P-008, REQ-P-018, REQ-P-020; NFR-002, NFR-009, NFR-011 | Abierto; brecha operacional concreta. | Verificar que los comandos afectados emiten artefacto JSON de bloqueo, código estable y `network_request_made: false`, y que las pruebas cubren fallo de SQLite/cuota inválida sin fallback inseguro. |
| [#270 — Auditoría integral](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/270) | REQ-P-020, REQ-P-028, REQ-P-033; NFR-004, NFR-007, NFR-009, NFR-011 | Abierto; alcance de auditoría todavía no equivale a una auditoría terminada. | Faltan línea base integral, inventario completo, evidencia de ejecución y sincronización bidireccional. La revisión asistida por IA no es independiente y no permite afirmar certificación ISO. |

### 8.1 Relaciones técnicas ya existentes que deben conservar sus límites

- [PR #177](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/177) reconstruye episodios de movimiento a partir de pivotes y reglas de precio; no demuestra por sí solo el detonante causal.
- [PR #179](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/179) enlaza evidencia de eventos suministrada con ventanas de episodios; no habilita automáticamente la captura de noticias.
- [PR #181](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/181) resume evidencia de detonantes por episodio y declara estados de ausencia de evidencia; no permite inferir que no existió un evento.
- [PR #217](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/217) valida periodos y metadatos de observaciones fundamentales/on-chain; la validación de contrato no prueba la disponibilidad ni la calidad de fuentes en vivo.

Estos PR se citan como entregas relacionadas, no como prueba suficiente de cierre de todos los requisitos asociados. Antes de elevar un requisito a `implementado` o `verificado`, registrar el PR/commit exacto, pruebas relevantes, resultado de CI y limitaciones residuales.

### 8.2 Próxima acción de trazabilidad

1. **Completado en esta iteración documental:** se amplió el catálogo maestro existente, sin crear otro catálogo, con filas de trazabilidad y revisión de cobertura para los Issues #128, #130, #132, #133, #134, #266 y #270. Las relaciones son propuestas documentales y no prueban implementación ni cierre; el validador automatizado se amplió para exigir las filas en ambas matrices y se añadieron pruebas de mutación; la ejecución de CI del nuevo HEAD sigue pendiente.
2. Para cada relación de la tabla, inspeccionar el Issue, PR/commit y pruebas reales antes de asignar estados de implementación o verificación.
3. Mantener separadas la cobertura documental, la evidencia de código, la ejecución de pruebas y la aprobación del propietario.
4. No cerrar Issues ni declarar la auditoría integral terminada por esta ampliación documental.
