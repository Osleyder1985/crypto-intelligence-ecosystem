# Catálogo inicial de requisitos y trazabilidad

- **Estado:** borrador de trabajo; no constituye una línea base aprobada.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Issue relacionado:** [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- **Convención:** los identificadores son estables; si cambia sustancialmente el significado, se retira el ID anterior y se crea uno nuevo.

## 1. Requisitos de producto (borrador)

| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|---|
| REQ-P-001 | El sistema permitirá iniciar una investigación bajo demanda con alcance y parámetros explícitos. | Alta | Una petición válida crea un trabajo identificable y devuelve estado/resultados o error documentado; no requiere ejecución continua 24/7. | Pruebas de API y flujo de usuario | Propuesto | Rol propuesto: Product Owner |
| REQ-P-002 | Los clientes consumirán una fuente central de verdad a través de contratos API versionados. | Alta | Web y móvil reciben la misma definición de datos y versión de dominio para una misma consulta; las diferencias de caché son detectables. | Pruebas de contrato e integración | Propuesto | Rol propuesto: Líder de plataforma/API |
| REQ-P-003 | El sistema permitirá explorar activos y pares spot usando criterios reproducibles de liquidez y calidad. | Alta | Cada resultado declara exchange, par, tipo de mercado, timestamp, métricas disponibles, exclusiones y limitaciones. | Dataset de referencia y pruebas de clasificación | Propuesto | Rol propuesto: Líder de datos de mercado |
| REQ-P-004 | Los informes distinguirán observaciones, cálculos, interpretaciones, hipótesis y recomendaciones. | Alta | Cada afirmación cuantitativa identifica método, ventana temporal, fuente y limitaciones; las hipótesis no se etiquetan como hechos. | Revisión de informes y pruebas de esquema | Propuesto | Rol propuesto: Líder de investigación cuantitativa |
| REQ-P-005 | Cada investigación conservará una evaluación histórica versionada y reproducible sin sobrescribir ejecuciones anteriores. | Alta | Cada ejecución recibe un identificador único y queda enlazada con las evaluaciones anteriores; se recuperan método/versión, parámetros, marcas temporales y entradas o referencias inmutables, y se señalan los datos irrecuperables. | Prueba de reproducción y verificación de historial inmutable | Propuesto | Rol propuesto: Ingeniería de datos y reproducibilidad |
| REQ-P-006 | La interfaz soportará web, Android e iOS. | Alta | Los flujos principales definidos en requisitos de UX se completan en cada plataforma objetivo con criterios equivalentes. | Pruebas funcionales y de usabilidad por plataforma | Propuesto | Rol propuesto: Líder de experiencia multiplataforma |
| REQ-P-007 | La ejecución real de órdenes permanecerá deshabilitada hasta una decisión y evaluación separadas. | Crítica | No hay credenciales de trading ni ruta de ejecución habilitada en la versión de investigación; pruebas de configuración y revisión de secretos. | Inspección de arquitectura, secretos y pruebas negativas | Propuesto | Rol propuesto: Responsable de seguridad y riesgo |
| REQ-P-008 | El sistema informará errores, datos incompletos y fallos de proveedor sin presentar resultados parciales como completos. | Alta | Ante entradas incompletas o proveedor fallido, la respuesta identifica el fallo y marca cualquier resultado parcial. | Pruebas de fallo inyectado | Propuesto | Rol propuesto: Líder de fiabilidad de plataforma |
| REQ-P-009 | Los resultados de análisis cuantitativo incluirán costes y controles contra sesgos relevantes. | Alta | La metodología documenta comisiones, spread, deslizamiento estimado, sesgos considerados y validación fuera de muestra cuando proceda. | Informe de validación y tests | Propuesto | Rol propuesto: Líder de investigación cuantitativa |
| REQ-P-010 | La selección de stack y hosting se basará en criterios previamente definidos y evidencia comparativa. | Alta | Cada selección aprobada enlaza requisitos, pesos/umbrales acordados, alternativas, PoC, resultados, costes y riesgos residuales. | ADR y resultados reproducibles de PoC | Propuesto | Rol propuesto: Arquitectura y evaluación tecnológica |

## 2. Requisitos no funcionales (NFR) por concretar

No se fijan números arbitrarios. Los umbrales se aprobarán tras definir carga esperada, objetivos de usuario, coste disponible, amenazas y límites de proveedores.

| ID | Atributo | Métricas a definir | Prueba/evidencia requerida |
|---|---|---|---|
| NFR-001 | Rendimiento | Latencia p50/p95/p99 por operación, tiempo de investigación, throughput y consumo | Benchmark repetible con carga y datos representativos |
| NFR-002 | Fiabilidad | Tasa de error, recuperación, consistencia y comportamiento ante dependencia caída | Pruebas de fallo, reintentos y recuperación |
| NFR-003 | Calidad de datos | Frescura, cobertura, duplicados, huecos, precisión y validez de unidades | Suite de calidad con fixtures conocidos |
| NFR-004 | Seguridad | Amenazas, permisos, secretos, dependencias, exposición de API y eventos auditables | Revisión de amenazas, análisis de dependencias y pruebas de seguridad |
| NFR-005 | Privacidad | Minimización, finalidad, retención, acceso y eliminación de datos personales si los hubiera | Inventario de datos y pruebas de ciclo de vida |
| NFR-006 | Usabilidad/accesibilidad | Éxito de tareas, errores, tiempo de tarea y barreras de acceso | Pruebas con usuarios y tecnología de asistencia |
| NFR-007 | Mantenibilidad | Complejidad, modularidad, cobertura útil, tiempo de cambio y regresiones | Revisión de código, pruebas y métricas de mantenimiento |
| NFR-008 | Portabilidad | Tiempo/coste de migración, formatos abiertos y dependencia de proveedor | Ejercicio de exportación/restauración o despliegue alternativo |
| NFR-009 | Observabilidad | Cobertura de logs, métricas, trazas, alertas y correlación de trabajo | Simulación de incidente y ejercicio de diagnóstico |
| NFR-010 | Coste | Coste mensual estimado y medido por carga, almacenamiento, tráfico y proveedor | Modelo de coste y prueba de límites/consumo |

## 3. Mapa inicial de trazabilidad

| Objetivo | Requisitos asociados | Riesgo principal | Decisión/artefacto | Verificación |
|---|---|---|---|---|
| Investigación bajo demanda | REQ-P-001, REQ-P-008 | Trabajo incompleto o respuesta engañosa | Contrato de trabajo y estados | Pruebas de API, timeout y fallos |
| Datos comunes y fiables | REQ-P-002, REQ-P-003, NFR-003 | Datos divergentes, stale o mercado incorrecto | Contrato de datos y catálogo de fuentes | Tests de contrato y calidad |
| Análisis reproducible | REQ-P-004, REQ-P-005, REQ-P-009 | Sesgo, fuga temporal o resultado no reproducible | Método versionado y formato de informe | Reproducción y validación fuera de muestra |
| Uso multiplataforma | REQ-P-006, NFR-006 | Flujos inconsistentes o barreras de acceso | Prototipos, contratos API y decisiones de UI | Tests por plataforma y evaluación de usuarios |
| Seguridad y límites de operación | REQ-P-007, NFR-004, NFR-005 | Acceso indebido o trading accidental | Modelo de amenazas y separación de permisos | Pruebas negativas y revisión de configuración |
| Selección técnica sostenible | REQ-P-010, NFR-001, NFR-008, NFR-010 | Lock-in, costes ocultos o rendimiento insuficiente | ADR y PoC comparativas | Reejecución de benchmark y cálculo de coste |

## 4. Reglas de trazabilidad

- Ningún requisito aprobado queda sin propietario, prioridad, criterio de aceptación y evidencia prevista.
- Cada PR debe indicar qué IDs modifica y enlazar los Issues relevantes.
- Una prueba debe indicar qué requisito verifica, cómo se ejecuta, versión del entorno, datos de prueba y resultado.
- Las pruebas fallidas o no ejecutadas no se omiten: se documentan con impacto y decisión.
- Los requisitos sustituidos conservan enlace al reemplazo y la razón del cambio.
- Las métricas se fijan antes de observar resultados de benchmark cuando sea viable, para evitar adaptar los umbrales al resultado deseado.

## 5. Próxima revisión

Antes de aprobar esta lista:
1. Contrastar los requisitos con Issues #3–#10 y eliminar duplicidades.
2. Asignar propietario y prioridad definitiva.
3. Convertir los criterios de aceptación generales en escenarios medibles.
4. Definir modelos de datos y contratos solo después de aclarar casos de uso y fuentes.
5. Revisar implicaciones legales/regulatorias según jurisdicciones y proveedores concretos.


## 6. Requisitos ampliados para investigación de nivel avanzado

Los siguientes requisitos amplían el catálogo a partir del alcance del Issue #13. Siguen siendo propuestas: no implican que la capacidad exista ni que la metodología esté aprobada. Las métricas y umbrales numéricos se fijarán antes de evaluar resultados, con una justificación basada en el uso previsto y la evidencia disponible.

| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|---|
| REQ-P-011 | Cada dato analítico tendrá identidad canónica, procedencia, marcas temporales y estado de calidad. | Crítica | El sistema distingue activo, red/contrato cuando aplique, exchange, mercado/par y proveedor; detecta conflictos de identidad y no los resuelve silenciosamente. | Esquema versionado, catálogo de identidad, fixtures y pruebas de reconciliación | Propuesto | Rol propuesto: Gobierno y calidad de datos |
| REQ-P-012 | Los informes separarán calidad de evidencia, puntuación del activo, oportunidad por horizonte y riesgo. | Crítica | Una puntuación no oculta cobertura deficiente, incertidumbre ni incompatibilidad entre horizontes; el sistema puede abstenerse de emitir una conclusión cuando falten datos críticos. | Casos límite, pruebas de reglas de abstención y revisión de informes | Propuesto | Rol propuesto: Líder de metodología cuantitativa |
| REQ-P-013 | Las predicciones registradas serán probabilísticas, fechadas y evaluables posteriormente. | Alta | Cada predicción conserva instante de emisión, horizonte, evento/variable objetivo, probabilidad o intervalo, condiciones de invalidación, versión del método y resultado posterior; no se reescribe retroactivamente. | Registro inmutable, evaluación fuera de muestra y métricas de calibración | Propuesto | Rol propuesto: Validación de modelos |
| REQ-P-014 | Las estrategias y señales se compararán con líneas base y validación temporal fuera de muestra. | Crítica | Se documentan particiones temporales, selección del universo, costes, sesgos examinados, benchmarks y resultados negativos; ninguna métrica de prueba se usa para ajustar y certificar el mismo experimento sin separación explícita. | Protocolo experimental versionado, resultados brutos y reproducción independiente | Propuesto | Rol propuesto: Investigación cuantitativa y validación |
| REQ-P-015 | El análisis fundamental/on-chain será específico al tipo de activo y a la disponibilidad verificable de datos. | Alta | Se registran aplicabilidad, fuente, timestamp, unidad, cobertura y limitaciones para oferta/emisiones/unlocks, concentración, actividad, seguridad y métricas de protocolo cuando correspondan; datos no aplicables no se puntúan como cero. | Diccionario de métricas por categoría de activo y pruebas de ausencia/no aplicabilidad | Propuesto | Rol propuesto: Investigación fundamental/on-chain |
| REQ-P-016 | El motor de riesgo evaluará exposición a mercado, volatilidad, drawdown, correlaciones y escenarios adversos. | Alta | Cada evaluación identifica horizonte, método, ventana, supuestos, exposición relevante y limitaciones; los resultados se comparan con benchmarks y escenarios definidos previamente. | Casos de prueba, análisis de sensibilidad y pruebas de estrés reproducibles | Propuesto | Rol propuesto: Gestión de riesgo cuantitativo |
| REQ-P-017 | El producto mantendrá un benchmark de calidad analítica con protocolo reproducible. | Alta | Las comparaciones publican periodo, universo, datos, versiones, criterios, métricas y limitaciones; se incluyen fallos, falsos positivos y resultados no concluyentes, no solo casos favorables. | Protocolo de benchmark, dataset versionado y reporte reproducible | Propuesto | Rol propuesto: Verificación y benchmark analítico |
| REQ-P-018 | Los trabajos largos de investigación informarán su estado y conservarán diagnóstico de fallos. | Alta | El usuario puede distinguir en cola, en ejecución, completado, parcial, cancelado y fallido; un resultado parcial queda marcado y vinculado a errores y fuentes no disponibles. | Pruebas de estados, fallos inyectados y pruebas de integración | Propuesto | Rol propuesto: Fiabilidad de plataforma |
| REQ-P-019 | El sistema detectará degradación de fuentes, métodos y modelos a lo largo del tiempo. | Alta | Se miden frescura/cobertura de datos y cambios de rendimiento; alertas y revisiones quedan registradas sin cambiar silenciosamente versiones o umbrales. | Pruebas de datos degradados, monitorización y registro de cambios | Propuesto | Rol propuesto: Calidad de datos y observabilidad |
| REQ-P-020 | Cada conclusión relevante podrá recorrerse hacia atrás hasta su evidencia y configuración de ejecución. | Crítica | Desde una conclusión se recuperan requisito, método/versión, parámetros, fuentes, timestamps, transformaciones, advertencias, prueba de validación y aprobaciones aplicables. | Prueba de trazabilidad de extremo a extremo | Propuesto | Rol propuesto: Trazabilidad e integridad analítica |
| REQ-P-021 | El sistema comparará evaluaciones históricas del mismo activo y distinguirá cambios de mercado de cambios metodológicos o de datos. | Alta | Para dos o más ejecuciones muestra cambios absolutos/relativos en indicadores, eventos, liquidez, riesgos, puntuación y conclusión; identifica cambios debidos a método, parámetros, proveedor, cobertura o correcciones. | Pruebas con evaluaciones versionadas y casos de cambio de metodología/proveedor | Propuesto | Rol propuesto: Investigación cuantitativa |
| REQ-P-022 | El sistema generará rankings reproducibles solo con evaluaciones comparables y vigentes. | Alta | Cada ranking registra universo, exclusiones, horizonte, timestamp, metodología/pesos, penalización por datos ausentes e incertidumbre; puede reconstruirse con las versiones usadas y no mezcla horizontes incompatibles sin normalización documentada. | Reconstrucción de ranking histórico, pruebas de comparabilidad y sensibilidad a pesos | Propuesto | Rol propuesto: Ranking y metodología cuantitativa |
| REQ-P-023 | El sistema detectará candidatos a movimientos de mercado y relacionará eventos temporales con evidencia verificable. | Alta | Las reglas para inicio, aceleración, agotamiento y reversión están definidas por temporalidad; las reconstrucciones históricas solo usan información disponible entonces; noticias y eventos conservan fuente, publicación/captura, zona horaria, relevancia, alternativas y grado de evidencia, sin inferir causalidad por proximidad temporal. | Fixtures OHLCV, pruebas anti-look-ahead y expedientes reproducibles de eventos | Propuesto | Rol propuesto: Investigación de mercado y eventos |
| REQ-P-024 | El sistema mantendrá una memoria consultable de eventos y predicciones con resultados posteriores. | Alta | Cada predicción conserva timestamp, horizonte, condiciones de invalidación, método/versión y resultado observado; las recurrencias se evalúan fuera de muestra con controles de supervivencia, fuga temporal, sobreajuste y costes cuando proceda. | Registro histórico, protocolo temporal, resultados negativos y métricas de calibración | Propuesto | Rol propuesto: Validación de predicciones |
| REQ-P-025 | El sistema analizará profundidad bid/ask, operaciones recientes y métricas de liquidez de pares spot en un universo de exchanges validado. | Alta | Evaluará como objetivo inicial 15–20 exchanges, sujeto a cobertura real, acceso API, límites, comparabilidad y restricciones legales/geográficas; normaliza símbolos, unidades y timestamps; calcula spread, profundidad, desequilibrio y slippage para tamaños de referencia cuando existan datos suficientes; distingue instantáneas de históricos y documenta el inicio de captura propia. Solo lectura, sin ejecución de órdenes. | Fixtures de libro/trades, comparación de fuentes, pruebas de frescura y reporte de cobertura por exchange/par | Propuesto | Rol propuesto: Ingeniería de datos de mercado |
| REQ-P-026 | El sistema identificará zonas de soporte y resistencia con métodos documentados y varias temporalidades. | Alta | Cada zona muestra rango, método, contactos/rechazos, antigüedad, volumen asociado si existe, distancia al precio, fortaleza estimada, invalidación e incertidumbre; las señales históricas no usan información futura y no presentan la zona como garantía. | Pruebas retrospectivas anti-look-ahead, sensibilidad entre métodos y ejemplos reproducibles | Propuesto | Rol propuesto: Investigación de análisis técnico |
| REQ-P-027 | La interfaz permitirá navegar de forma coherente entre fichas de activos, evaluaciones históricas, rankings, eventos y evidencia. | Alta | Los flujos principales funcionan en web y clientes móviles objetivo; los estados de carga/error/datos insuficientes son explícitos y las visualizaciones de incertidumbre son legibles y responsivas. | Pruebas de tareas, accesibilidad, responsividad y comprensión de informes | Propuesto | Rol propuesto: UX y accesibilidad |
| REQ-P-028 | El proyecto mantendrá una evaluación de aplicabilidad normativa y gobernanza vinculada a los riesgos y procesos reales del producto. | Alta | Cada referencia identifica fuente oficial, edición/estado y fecha de consulta, alcance, aplicabilidad justificada, responsable, evidencia, estado de decisión y distinción entre control interno, conformidad evaluada, certificación y obligación legal. No se atribuyen requisitos a cláusulas no verificadas. | Matriz revisada, fuentes oficiales registradas y trazabilidad a procesos/requisitos | Propuesto | Rol propuesto: Gobernanza y aplicabilidad normativa |
| REQ-P-029 | La selección de exchanges y pares spot seguirá una metodología reproducible y explícita para el universo de comparación y el exchange objetivo. | Alta | La evaluación inicial considera Binance como referencia, OKX, Bybit, MEXC, Gate y Bitget como comparadores y verifica por separado la disponibilidad del par exacto en Pionex; toda inclusión/exclusión documenta liquidez, spread, profundidad, slippage, comisiones pertinentes, API, frescura, restricciones y datos ausentes. La cobertura objetivo de 15–20 exchanges solo se declara alcanzada con evidencia por exchange/par. | Capturas fechadas, matriz de cobertura, reglas PASS/FAIL y reproducción de una fecha histórica | Propuesto | Rol propuesto: Selección de mercados spot |
| REQ-P-030 | La estrategia de clientes se decidirá comparando web responsive/PWA, aplicaciones móviles y escritorio opcional según casos de uso y pruebas de concepto. | Alta | Se documentan tareas por plataforma, necesidades offline, notificaciones, integración local, gráficos, accesibilidad, distribución, costes y mantenimiento; iOS y Android se evalúan explícitamente y escritorio instalado solo se adopta si los requisitos lo justifican. No se fija stack antes de comparar alternativas. | Matriz ponderada, prototipos ejecutados en dispositivos objetivo y ADR revisable | Propuesto | Rol propuesto: Arquitectura de clientes |
| REQ-P-031 | La arquitectura de alojamiento y operación se seleccionará con condiciones oficiales vigentes y escenarios de coste/recuperación. | Alta | Se documentan cuotas, suspensión, almacenamiento, egreso, regiones, backups, límites de ejecución, condiciones de uso y coste para MVP/crecimiento; el despliegue, observación y recuperación se pueden operar sin laptop permanentemente disponible, con alertas de coste, exportación y procedimiento de salida. | Enlaces oficiales fechados, modelo de costes, prueba de despliegue, backup/restore y migración | Propuesto | Rol propuesto: Operación de plataforma y costes |
| REQ-P-032 | La plataforma central expondrá contratos de API versionados con controles de acceso y políticas explícitas de frescura y caché. | Alta | Para cada dominio se identifica fuente de verdad, propietario, timestamp de evento/recepción, política de frescura, tratamiento de datos obsoletos, autenticación/autorización y límites; cachés locales no se convierten en fuentes divergentes y secretos de proveedores no se exponen a clientes. | Contratos OpenAPI u otro contrato versionado, pruebas de autorización, consistencia y frescura entre clientes | Propuesto | Rol propuesto: API, seguridad y gobierno de datos |
| REQ-P-033 | Cada fase de ingeniería tendrá criterios de entrada/salida y una definición verificable de terminado basada en evidencia. | Alta | Cada entrega enlaza requisitos, riesgos, decisiones, cambios y pruebas; registra entorno/versión/comandos/resultados, controles fallidos o no ejecutados, defectos abiertos, excepciones con responsable y autorización; documentación o compilación por sí solas no satisfacen la aceptación. | Plantilla de puerta de fase, registro reproducible de pruebas y trazabilidad extremo a extremo | Propuesto | Rol propuesto: Gobernanza de ingeniería y verificación |
| REQ-P-034 | El sistema integrará una investigación de activo desde la entrada hasta un informe reproducible por horizonte. | Crítica | Una prueba E2E identifica el activo, consulta componentes analíticos existentes y entrega resultados separados para corto, medio y largo plazo, o INDETERMINATE con motivo. | Informe E2E versionado y artefactos de ejecución | Propuesto; integración pendiente | Rol propuesto: Integración de producto analítico |
| REQ-P-035 | El sistema investigará posibles detonantes de movimientos con fuentes y cronología verificables. | Alta | Cada evento relacionado conserva publicación/captura, fuente y clasificación de evidencia; no afirma causalidad por proximidad temporal. | Expediente de eventos, pruebas de fuentes contradictorias y causa desconocida | Propuesto; integración pendiente | Rol propuesto: Investigación de mercado y eventos |
| REQ-P-036 | Cada evaluación ofrecerá una tesis independiente para corto, medio y largo plazo. | Alta | Cada horizonte declara metodología/versión, escenarios, evidencia favorable/adversa, riesgos, invalidaciones y límites de confianza; sus duraciones se versionan y aprueban. | Contrato del informe y pruebas de esquema/E2E | Propuesto; metodología pendiente de aprobación | Rol propuesto: Metodología cuantitativa |
| REQ-P-037 | Las zonas de soporte y resistencia se integrarán en la evaluación con temporalidad e invalidación explícitas. | Alta | El informe enlaza zonas al método y datos de origen; las pruebas históricas demuestran ausencia de look-ahead. | Tests del analizador e informe reproducible | Parcial; integración E2E pendiente | Rol propuesto: Análisis técnico cuantitativo |
| REQ-P-038 | La captura preservará respuestas completas hasta EOF sin límite arbitrario de bytes impuesto por el proyecto. | Crítica | Las capturas registran hash, estado de terminación, paginación, errores y truncamiento; las interrupciones no se etiquetan completas y se gestionan los límites reales documentados. | Pruebas de integridad, paginación, interrupción y reanudación | Política documentada; validación integral pendiente | Rol propuesto: Ingeniería de datos de mercado |
| REQ-P-039 | El informe explicará calidad de evidencia, riesgos y abstención cuando no haya base suficiente. | Alta | Casos con datos ausentes, incompatibles o no verificables devuelven INDETERMINATE y detallan qué falta, sin puntuación positiva forzada. | Fixtures negativos y pruebas de contrato del informe | Propuesto; cobertura E2E pendiente | Rol propuesto: Calidad y verificación analítica |

## 7. NFR adicionales para fiabilidad científica y operación

| ID | Atributo | Métricas/controles a definir | Prueba/evidencia requerida |
|---|---|---|---|
| NFR-011 | Procedencia e integridad analítica | Cobertura de procedencia, referencias inmutables/hash, capacidad de reconstrucción y detección de alteraciones | Reproducción desde una ejecución registrada y prueba de integridad |
| NFR-012 | Calibración y utilidad predictiva | Brier score/log loss cuando sean aplicables, calibración por horizonte, precisión/recobrado y comparación con benchmark | Evaluación temporal fuera de muestra con intervalos de incertidumbre |
| NFR-013 | Robustez y sensibilidad | Sensibilidad a parámetros, periodos, proveedores, costes y universo elegible | Análisis de sensibilidad predefinido y repetible |
| NFR-014 | Integridad temporal | Fuga de información, look-ahead, latencia entre evento y disponibilidad de dato | Pruebas con timestamps point-in-time y casos adversariales |
| NFR-015 | Resiliencia operativa | Recuperación, errores parciales, duplicación de trabajos, pérdida de datos y comportamiento ante límites de API | Pruebas de fallo, idempotencia, backup/restore y recuperación |
| NFR-016 | Transparencia de límites | Cobertura, datos ausentes, acuerdo entre métodos, confianza y frecuencia de abstención | Casos de insuficiencia de evidencia y revisión de reportes |
| NFR-017 | Calidad de ranking | Estabilidad temporal, sensibilidad a pesos, comparabilidad y cambios de universo | Pruebas de sensibilidad y reconstrucción de rankings históricos |
| NFR-018 | Calidad de experiencia | Éxito de tareas, accesibilidad, legibilidad de incertidumbre, estado de trabajos y errores de interpretación | Pruebas moderadas con usuarios y tecnología de asistencia |
| NFR-019 | Integridad de captura | Respuestas completas hasta EOF, hashes, paginación, truncamiento, reanudación y límites reales de origen/entorno | Pruebas con respuestas grandes, paginación, EOF, interrupciones, reintentos e integridad hash |
| NFR-020 | Validez temporal de la investigación | Disponibilidad point-in-time de velas, eventos y noticias; prevención de look-ahead y sesgo de supervivencia | Pruebas adversariales temporales y evaluación fuera de muestra |
| NFR-021 | Explicabilidad y abstención analítica | Trazabilidad de conclusiones, calidad/cobertura, incertidumbre, evidencia contraria y tasa de INDETERMINATE | Revisión de informes y fixtures de evidencia insuficiente/contradictoria |

## 8. Trazabilidad ampliada

| Objetivo | Requisitos asociados | Riesgo principal | Decisión/artefacto | Verificación |
|---|---|---|---|---|
| Identidad y calidad de datos | REQ-P-002, REQ-P-003, REQ-P-011, NFR-003, NFR-011 | Mezclar activos/pares o tratar datos incompletos como fiables | Registro canónico de instrumentos, catálogo de fuentes y contrato de calidad | Reconciliación, controles de frescura y reproducción |
| Conclusiones honestas y comparables | REQ-P-004, REQ-P-012, REQ-P-020, NFR-016 | Falsa precisión o conclusión no sustentada | Esquema de informe con evidencia, incertidumbre y abstención | Casos de evidencia insuficiente y trazabilidad de extremo a extremo |
| Predicción verificable | REQ-P-013, REQ-P-014, REQ-P-017, REQ-P-019, NFR-012, NFR-013, NFR-014 | Sobreajuste, fuga temporal, deriva y selección retrospectiva | Registro de predicciones y protocolo de experimentos | Validación temporal, calibración, sensibilidad y benchmark |
| Evaluación del tipo de activo | REQ-P-015, REQ-P-016 | Métricas inaplicables, riesgos omitidos o datos no comparables | Taxonomía de activos, diccionario de métricas y motor de riesgo | Fixtures por categoría y pruebas de escenarios |
| Trabajo fiable y recuperable | REQ-P-008, REQ-P-018, REQ-P-019, NFR-015 | Resultados parciales engañosos, trabajos duplicados o fallos silenciosos | Máquina de estados, correlación de trabajos y runbooks | Fallos inyectados, idempotencia y recuperación |
| Calidad reconocible externamente | REQ-P-017, NFR-012, NFR-013, NFR-017, NFR-018 | Afirmaciones de superioridad no demostradas | Protocolo de benchmark público y métricas de producto | Reejecución independiente y publicación de resultados negativos y positivos |
| Comparación y ranking histórico | REQ-P-005, REQ-P-021, REQ-P-022, REQ-P-020, NFR-017 | Evaluaciones versionadas, ranking con universo/horizonte/pesos y trazabilidad de cambios | Comparaciones inválidas o cambios metodológicos confundidos con cambios de mercado | Reconstrucción histórica y pruebas de sensibilidad/comparabilidad |
| Detección de movimientos y memoria de eventos | REQ-P-023, REQ-P-024, REQ-P-013, REQ-P-014, NFR-014 | Series OHLCV point-in-time, registro de fuentes/eventos, predicciones fechadas y resultados posteriores | Falsa causalidad, fuga de información y sobreajuste | Pruebas anti-look-ahead, expediente de evento y evaluación fuera de muestra |
| Profundidad y liquidez spot | REQ-P-003, REQ-P-025, REQ-P-011, NFR-003, NFR-011 | Capturas de libro/trades, spread, profundidad, slippage, cobertura y frescura por exchange/par | Volumen artificial, datos no comparables o ausencia de histórico | Fixtures, reconciliación de fuentes y límites de cobertura documentados |
| Soportes/resistencias e interfaz analítica | REQ-P-026, REQ-P-027, NFR-006, NFR-016, NFR-018 | Zonas multi-temporalidad con invalidación e incertidumbre; flujos responsivos entre ficha, historial, ranking y evidencia | Señales retrospectivas engañosas o mala interpretación de incertidumbre | Pruebas temporales, tareas de usuario, accesibilidad y revisión de visualizaciones |

| Gobernanza normativa y evidencia de conformidad | REQ-P-028, REQ-P-033, NFR-004, NFR-010 | Confundir referencia normativa con obligación, certificación o control implementado | Matriz de aplicabilidad con fuente, edición, responsable, evidencia y estado | Revisión de fuentes oficiales y auditoría de trazabilidad interna |
| Selección reproducible de exchanges/pares spot | REQ-P-003, REQ-P-029, REQ-P-009, NFR-003, NFR-010 | Volumen no comparable, par no disponible o cobertura declarada sin evidencia | Universo versionado, reglas de exclusión y matriz por exchange/par | Reconstrucción fechada y pruebas de calidad de datos |
| Decisión de plataformas y stack | REQ-P-006, REQ-P-010, REQ-P-030, NFR-006, NFR-008 | Elegir plataforma sin validar casos de uso, publicación o coste | Matriz de decisión, PoC y ADR | Repetición de pruebas en dispositivos y análisis de sensibilidad de pesos |
| Hosting, operación y recuperación | REQ-P-010, REQ-P-031, NFR-002, NFR-008, NFR-009, NFR-010 | Suspensión del servicio, pérdida de datos, dependencia de laptop o costes inesperados | Modelo de costes, runbooks, backup/restore y plan de salida | Ejercicio de recuperación y comprobación de cuotas oficiales |
| API central, frescura y control de acceso | REQ-P-002, REQ-P-032, NFR-003, NFR-004, NFR-009 | Divergencia entre clientes, datos obsoletos o acceso indebido | Contratos API versionados, política de frescura y matriz de autorización | Pruebas de contrato, consistencia, permisos y datos stale |
| Ciclo de vida y terminado verificable | REQ-P-001, REQ-P-005, REQ-P-010, REQ-P-033, NFR-007 | Entregables considerados completos sin evidencia o trazabilidad | Puertas de fase, Definition of Done y registros de ejecución | Revisión de una entrega de extremo a extremo y reproducción de pruebas |

## 9. Reglas adicionales del laboratorio cuantitativo

1. Definir el objetivo, universo, horizonte, métrica principal, benchmarks y umbrales antes de ejecutar la evaluación final.
2. Mantener separados los datos disponibles en el instante de decisión y los datos conocidos posteriormente. La reconstrucción histórica debe respetar la disponibilidad temporal real.
3. Separar desarrollo, validación y prueba final por tiempo; evitar reutilizar el conjunto de prueba para optimizar parámetros.
4. Incluir comisiones, spread, slippage, restricciones de liquidez y supuestos de ejecución cuando se evalúe una estrategia negociable.
5. Comparar métodos simples y transparentes antes de justificar complejidad estadística, ML o IA.
6. Conservar resultados fallidos, hipótesis descartadas, versiones, semillas aleatorias cuando proceda y razones de cambios metodológicos.
7. Informar incertidumbre, cobertura, tamaño de muestra y escenarios en que el método deja de ser fiable.
8. No convertir una asociación histórica en explicación causal sin un diseño de investigación que permita sostener esa inferencia.

## 10. Regla de abstención y estados de evidencia

La plataforma debe poder responder «evidencia insuficiente» o «resultado no comparable». Como mínimo, la presentación distinguirá:

- **Dato observado:** recuperado de una fuente identificada, con timestamp y estado de calidad.
- **Dato derivado:** calculado a partir de entradas y una transformación versionada.
- **Interpretación:** lectura analítica apoyada en datos y método, con incertidumbre.
- **Hipótesis:** explicación que aún necesita validación.
- **Predicción:** afirmación prospectiva registrada con horizonte y criterio de evaluación.
- **Recomendación analítica:** resultado condicionado al objetivo, horizonte, riesgo y calidad de evidencia; nunca garantía de rentabilidad.

Estos estados describen el tipo de afirmación, no una escala universal de confianza. Las escalas y umbrales requieren una definición separada y validación empírica.

## 11. Próxima revisión del catálogo

- Resolver trazabilidad con Issues #3–#13 y evitar duplicar decisiones ya asignadas.
- Definir propietarios, prioridad aprobada y escenarios verificables para los requisitos críticos.
- Elaborar el modelo de datos histórico y de procedencia antes de seleccionar proveedores o implementar puntuaciones.
- Aprobar un protocolo de evaluación cuantitativa antes de comparar estrategias o modelos.
- Establecer un benchmark inicial reproducible antes de afirmar que una versión mejora a otra.
- Mantener los requisitos como propuestos hasta que el propietario apruebe la línea base.

## 12. Índice de planificación por fase y prioridad para NFR

La tabla siguiente completa la clasificación preliminar de NFR-001–NFR-021. **Fase y prioridad son propuestas de planificación, no una línea base aprobada.** La prioridad se asigna por impacto potencial si el atributo falla, dependencias de otras capacidades y alcance de la mitigación; no representa una puntuación cuantitativa de riesgo. Los umbrales numéricos quedan pendientes de requisitos de carga, coste, amenazas, datos y usuarios.

| Orden | Fase primaria | ID | Prioridad propuesta | Justificación y criterio de aceptación a concretar |
|---:|---|---|---|---|
| 1 | F0 — Gobernanza y marco maestro | NFR-004 | Crítica | Una brecha de seguridad puede exponer datos o secretos y comprometer todo el sistema. Acordar modelo de amenazas, permisos mínimos, gestión de secretos, análisis de dependencias y pruebas negativas antes de integrar clientes/proveedores. Verificar de nuevo en F7. |
| 2 | F0 — Gobernanza y marco maestro | NFR-005 | Alta | Definir finalidad, minimización, retención, acceso y eliminación antes de persistir datos personales, si los hubiera; aplicabilidad legal depende de datos y jurisdicciones reales. |
| 3 | F1 — Requisitos y riesgos del producto | NFR-001 | Alta | Fijar operaciones críticas, perfiles de carga y objetivos de latencia/throughput antes de comparar arquitectura; medir p50/p95/p99 con benchmark repetible en F7. |
| 4 | F1 — Requisitos y riesgos del producto | NFR-007 | Alta | Definir modularidad, política de pruebas, límites de complejidad y coste de cambio antes de escoger stack; verificar mediante revisión y regresiones continuas. |
| 5 | F2 — Investigación de mercados y fuentes | NFR-003 | Crítica | Datos incorrectos, stale o con unidades/identidad ambiguas invalidan el análisis posterior. Definir frescura, cobertura, huecos, duplicados y reconciliación; fijar umbrales por fuente/mercado antes de ingestión estable. |
| 6 | F2 — Investigación de mercados y fuentes | NFR-011 | Crítica | Sin procedencia e integridad no puede reconstruirse una conclusión. Definir referencias inmutables/hash, cobertura de procedencia y detección de alteraciones; reproducir una ejecución registrada. |
| 7 | F3 — Arquitectura y selección tecnológica | NFR-008 | Alta | El riesgo de lock-in o pérdida de portabilidad afecta la continuidad y el coste. Comparar formatos abiertos, exportación, restauración y despliegue alternativo en PoC. |
| 8 | F3 — Arquitectura y selección tecnológica | NFR-010 | Alta | El coste debe quedar acotado antes de elegir proveedores. Definir escenarios de carga, almacenamiento, tráfico, cuotas, alertas y coste máximo aceptable; contrastar estimación con medición. |
| 9 | F4 — Plataforma central de datos | NFR-002 | Alta | La plataforma necesita consistencia y degradación controlada ante fallos de proveedores. Definir disponibilidad/recuperación requeridas según uso y probar reintentos, timeout, recuperación y consistencia. |
| 10 | F4 — Plataforma central de datos | NFR-009 | Alta | Los fallos no son gestionables sin logs, métricas, trazas y correlación. Definir cobertura de telemetría y alertas para ingestión, API y trabajos; demostrar diagnóstico en un incidente simulado. |
| 11 | F4 — Plataforma central de datos | NFR-015 | Alta | Los trabajos duplicados, pérdida de datos o límites de API pueden generar resultados falsos o pérdida de historial. Definir idempotencia, recuperación, comportamiento parcial y backup/restore; probar fallos. |
| 12 | F5 — Motor de investigación cuantitativa | NFR-012 | Crítica | Las predicciones no deben presentarse como útiles sin evaluación y calibración. Definir métricas apropiadas por objetivo/horizonte, benchmarks e incertidumbre; evaluar fuera de muestra. |
| 13 | F5 — Motor de investigación cuantitativa | NFR-014 | Crítica | La fuga temporal puede invalidar retrospectivamente cualquier señal. Definir reglas point-in-time y disponibilidad real de datos; ejecutar pruebas anti-look-ahead y casos adversariales. |
| 14 | F5 — Motor de investigación cuantitativa | NFR-016 | Crítica | El sistema debe exponer datos ausentes, cobertura y casos en que no puede concluir. Definir estados de evidencia/abstención y revisar casos límite para evitar falsa precisión. |
| 15 | F5 — Motor de investigación cuantitativa | NFR-013 | Alta | La sensibilidad a parámetros, periodos, proveedores, costes y universo puede revelar sobreajuste. Fijar protocolo antes de ejecutar y conservar resultados de escenarios predefinidos. |
| 16 | F5 — Motor de investigación cuantitativa | NFR-017 | Alta | Rankings inestables o incomparables inducen decisiones engañosas. Definir pruebas de sensibilidad a pesos/universo, estabilidad temporal y reconstrucción histórica. |
| 17 | F6 — Experiencia web y móvil | NFR-006 | Alta | Una interfaz no utilizable o inaccesible puede hacer que se interpreten mal datos y riesgos. Definir tareas, tasa de éxito, errores, accesibilidad y tecnología de asistencia; evaluar en plataformas objetivo. |
| 18 | F6 — Experiencia web y móvil | NFR-018 | Alta | La comprensión de incertidumbre, errores y estados de trabajo es crítica para evitar malas interpretaciones. Definir tareas moderadas, criterios de comprensión y pruebas de accesibilidad/responsividad. |
| 19 | F6 — Experiencia web y móvil | NFR-019 | Alta | La integridad de captura debe ser verificable para que el análisis no se base en respuestas silenciosamente truncadas; probar EOF, hash, paginación, interrupción y reanudación. |
| 20 | F6 — Experiencia web y móvil | NFR-020 | Alta | Evitar que la investigación histórica use datos futuros; exigir disponibilidad point-in-time y pruebas anti-look-ahead/sesgo de supervivencia. |
| 21 | F6 — Experiencia web y móvil | NFR-021 | Alta | Cada conclusión debe enlazar evidencia y declarar incertidumbre; los casos insuficientes/contradictorios deben permitir abstención explícita. |

## 13. Índice de planificación por fase y prioridad

Esta vista es el **orden de planificación propuesto** de los requisitos de producto. La asignación es primaria (una fase de referencia por requisito) para ordenar el trabajo; no impide dependencias ni verificaciones transversales. Las prioridades siguen siendo iniciales y requieren aprobación. Los identificadores originales no se renumeran.

| Orden | Fase de referencia | ID | Prioridad inicial | Tema |
|---:|---|---|---|---|
| 1 | F0 — Gobernanza y marco maestro | REQ-P-007 | Crítica | Límite de seguridad: sin trading real |
| 2 | F0 — Gobernanza y marco maestro | REQ-P-028 | Alta | Gobernanza y aplicabilidad normativa |
| 3 | F0 — Gobernanza y marco maestro | REQ-P-033 | Alta | Puertas de fase y Definition of Done |
| 4 | F2 — Investigación de mercados y fuentes | REQ-P-011 | Crítica | Identidad y procedencia de datos |
| 5 | F2 — Investigación de mercados y fuentes | REQ-P-003 | Alta | Universo de activos y pares spot |
| 6 | F2 — Investigación de mercados y fuentes | REQ-P-029 | Alta | Selección reproducible de exchanges/pares |
| 7 | F3 — Arquitectura y selección tecnológica | REQ-P-010 | Alta | Selección de stack y hosting |
| 8 | F3 — Arquitectura y selección tecnológica | REQ-P-030 | Alta | Decisión de plataformas cliente |
| 9 | F3 — Arquitectura y selección tecnológica | REQ-P-031 | Alta | Hosting, costes y recuperación |
| 10 | F4 — Plataforma central de datos | REQ-P-002 | Alta | API central y contratos comunes |
| 11 | F4 — Plataforma central de datos | REQ-P-008 | Alta | Errores y resultados parciales |
| 12 | F4 — Plataforma central de datos | REQ-P-018 | Alta | Estados y diagnóstico de trabajos |
| 13 | F4 — Plataforma central de datos | REQ-P-032 | Alta | API, acceso, frescura y caché |
| 14 | F5 — Motor de investigación cuantitativa | REQ-P-012 | Crítica | Calidad de evidencia y abstención |
| 15 | F5 — Motor de investigación cuantitativa | REQ-P-014 | Crítica | Validación temporal fuera de muestra |
| 16 | F5 — Motor de investigación cuantitativa | REQ-P-020 | Crítica | Trazabilidad de conclusiones |
| 17 | F5 — Motor de investigación cuantitativa | REQ-P-034 | Crítica | Integrar los componentes existentes en un flujo E2E desde la identidad del activo hasta el informe por horizonte. |
| 18 | F5 — Motor de investigación cuantitativa | REQ-P-004 | Alta | Informes y evidencia analítica |
| 19 | F5 — Motor de investigación cuantitativa | REQ-P-005 | Alta | Historial reproducible |
| 20 | F5 — Motor de investigación cuantitativa | REQ-P-009 | Alta | Costes y sesgos cuantitativos |
| 21 | F5 — Motor de investigación cuantitativa | REQ-P-013 | Alta | Registro de predicciones |
| 22 | F5 — Motor de investigación cuantitativa | REQ-P-015 | Alta | Análisis fundamental/on-chain por activo |
| 23 | F5 — Motor de investigación cuantitativa | REQ-P-016 | Alta | Motor de riesgo y escenarios |
| 24 | F5 — Motor de investigación cuantitativa | REQ-P-017 | Alta | Benchmark analítico reproducible |
| 25 | F5 — Motor de investigación cuantitativa | REQ-P-021 | Alta | Comparación histórica |
| 26 | F5 — Motor de investigación cuantitativa | REQ-P-022 | Alta | Rankings comparables |
| 27 | F5 — Motor de investigación cuantitativa | REQ-P-023 | Alta | Movimientos de mercado y eventos |
| 28 | F5 — Motor de investigación cuantitativa | REQ-P-024 | Alta | Memoria de eventos y predicciones |
| 29 | F5 — Motor de investigación cuantitativa | REQ-P-025 | Alta | Profundidad y liquidez spot |
| 30 | F5 — Motor de investigación cuantitativa | REQ-P-026 | Alta | Soportes y resistencias |
| 31 | F5 — Motor de investigación cuantitativa | REQ-P-035 | Alta | Investigar detonantes con fuentes verificables y distinguir hechos, correlación, hipótesis y causa desconocida. |
| 32 | F5 — Motor de investigación cuantitativa | REQ-P-036 | Alta | Evaluar por separado corto, medio y largo plazo con escenarios, riesgos e invalidaciones versionados. |
| 33 | F5 — Motor de investigación cuantitativa | REQ-P-037 | Alta | Integrar soportes/resistencias con temporalidad, método e invalidación sin look-ahead. |
| 34 | F6 — Experiencia web y móvil | REQ-P-001 | Alta | Inicio y control del trabajo de investigación |
| 35 | F6 — Experiencia web y móvil | REQ-P-006 | Alta | Clientes web y móviles |
| 36 | F6 — Experiencia web y móvil | REQ-P-027 | Alta | Navegación analítica y experiencia |
| 37 | F8 — Operación y release controlada | REQ-P-038 | Crítica | Preservar capturas completas, registrar integridad y distinguir capturas completas de interrumpidas. |
| 38 | F8 — Operación y release controlada | REQ-P-019 | Alta | Monitorización de degradación |
| 39 | F8 — Operación y release controlada | REQ-P-039 | Alta | Exponer calidad de evidencia y abstenerse cuando falten datos esenciales. |

## 14. Matriz de trazabilidad entre Issues y requisitos

Esta matriz propone la cobertura documental de los Issues de arquitectura y requisitos. **No declara que los Issues estén resueltos ni que los requisitos estén implementados.** La asignación se basa en el alcance y los criterios de aceptación documentados en cada Issue; el responsable del proyecto debe confirmar la cobertura antes de aprobar la línea base. Un requisito puede vincularse a más de un Issue cuando exista una dependencia real.

| Issue | Alcance de trazabilidad | Requisitos de producto vinculados | NFR vinculados | Estado de la relación |
|---|---|---|---|---|
| [#3 — Gobernanza ISO/IEC](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/3) | Aplicabilidad normativa, gobernanza y límites de conformidad | REQ-P-028, REQ-P-033 | NFR-004, NFR-005 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#4 — Ingeniería de software](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/4) | Ciclo de vida, validación, experimentación, calidad y puertas de entrega | REQ-P-001, REQ-P-004, REQ-P-005, REQ-P-007, REQ-P-008, REQ-P-009, REQ-P-010, REQ-P-014, REQ-P-017, REQ-P-018, REQ-P-019, REQ-P-020, REQ-P-033 | NFR-001, NFR-002, NFR-007, NFR-009, NFR-011, NFR-012, NFR-013, NFR-014, NFR-015, NFR-016, NFR-017 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#5 — Clientes multiplataforma](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/5) | Web/PWA, Android, iOS y escritorio opcional según evidencia | REQ-P-006, REQ-P-027, REQ-P-030 | NFR-006, NFR-018 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#6 — Plataforma central de datos y API](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/6) | Fuente de verdad, contratos API, identidad, frescura, resiliencia y trabajos | REQ-P-002, REQ-P-008, REQ-P-011, REQ-P-018, REQ-P-019, REQ-P-032 | NFR-002, NFR-003, NFR-004, NFR-009, NFR-011, NFR-015 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#7 — Selección de mercados spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7) | Universo reproducible de exchanges/pares, liquidez y restricciones spot | REQ-P-003, REQ-P-011, REQ-P-025, REQ-P-029 | NFR-003, NFR-010, NFR-011 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#8 — Arquitectura y trazabilidad](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/8) | Arquitectura de referencia, decisiones, evidencia y trazabilidad normativa | REQ-P-002, REQ-P-004, REQ-P-010, REQ-P-020, REQ-P-028, REQ-P-032, REQ-P-033 | NFR-007, NFR-008, NFR-011 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#9 — Selección del stack tecnológico](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/9) | Criterios ponderados, pruebas de concepto, rendimiento, portabilidad y coste | REQ-P-010, REQ-P-030, REQ-P-031 | NFR-001, NFR-007, NFR-008, NFR-010 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#10 — Alojamiento y costes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/10) | Hosting, cuotas, recuperación, operación móvil y salida del proveedor | REQ-P-001, REQ-P-010, REQ-P-031, REQ-P-032 | NFR-001, NFR-002, NFR-008, NFR-009, NFR-010, NFR-015 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#11 — Marco maestro](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11) | Integración del marco, riesgos, hoja de ruta y Definition of Done | REQ-P-028, REQ-P-033 | NFR-007, NFR-011 | Propuesta; Issue rector, no sustituye la trazabilidad específica de los Issues subordinados |
| [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13) | Historial, comparaciones, ranking, eventos, liquidez, predicciones y niveles técnicos | REQ-P-004, REQ-P-005, REQ-P-009, REQ-P-012, REQ-P-013, REQ-P-014, REQ-P-015, REQ-P-016, REQ-P-017, REQ-P-018, REQ-P-019, REQ-P-020, REQ-P-021, REQ-P-022, REQ-P-023, REQ-P-024, REQ-P-025, REQ-P-026, REQ-P-027, REQ-P-029 | NFR-003, NFR-011, NFR-012, NFR-013, NFR-014, NFR-016, NFR-017, NFR-018 | Propuesta; confirmar contra criterios de aceptación del Issue |
| [#128 — Flujo integral de investigación por activo](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) | Integración E2E de identidad, historia, eventos/detonantes, horizontes, soportes/resistencias e informe con abstención | REQ-P-034, REQ-P-035, REQ-P-036, REQ-P-037, REQ-P-038, REQ-P-039 | NFR-019, NFR-020, NFR-021 | Requisitos especificados; implementación y evidencia E2E pendientes |
| [#16 — Calidad del libro de órdenes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/16) | Validación estructural del libro: orden, duplicados, lados vacíos, niveles inválidos y estados cruzado/bloqueado | REQ-P-025, REQ-P-029 | NFR-003, NFR-011 | Propuesta; confirmar criterios y política de libro bloqueado |
| [#17 — Identidad de mercado spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/17) | Identidad del par mediante símbolo, activo base/cotizado y estado spot específico del proveedor | REQ-P-025, REQ-P-029 | NFR-003, NFR-011 | Propuesta; confirmar cobertura de Binance y Pionex |
| [#18 — Frescura y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18) | Timestamps de origen/captura, política de frescura, tarifas y coste total con incertidumbre explícita | REQ-P-009, REQ-P-025, REQ-P-029, REQ-P-032 | NFR-003, NFR-011 | Propuesta; umbrales y evidencia económica pendientes |
| [#19 — Preparación operativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/19) | Puerta preproducción: pruebas integrales, seguridad, rendimiento, observabilidad, restauración y rollback | REQ-P-001, REQ-P-007, REQ-P-010, REQ-P-032, REQ-P-033 | NFR-001, NFR-002, NFR-007, NFR-009, NFR-015 | Propuesta; ejecución integral no demostrada |
| [#20 — Licencia y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20) | Decisión de distribución, licencia del proyecto, revisión de licencias de dependencias y avisos | REQ-P-028, REQ-P-033 | NFR-004, NFR-005 | Propuesta; requiere decisión explícita del propietario |
| [#21 — Evaluación independiente](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/21) | Alcance de evaluación externa, expediente de evidencia y distinción entre control interno, conformidad y certificación | REQ-P-028, REQ-P-033 | NFR-007, NFR-011 | Propuesta; no existe evaluación independiente completada |
| [#22 — Alineación de checks obligatorios](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/22) | Correspondencia entre checks requeridos por protect-main y contextos reales emitidos por workflows en todos los PR | REQ-P-028, REQ-P-033 | NFR-007, NFR-011 | Propuesta; discrepancia de contextos pendiente de resolver |

### Criterios de cierre de trazabilidad

- Cada requisito definido debe estar vinculado a, al menos, un Issue de alcance; una mención en el Issue rector no sustituye la relación específica cuando exista un Issue especializado.
- Todo ID mencionado en esta matriz debe existir en el catálogo y todo ID del catálogo debe aparecer en una fila de trazabilidad.
- La relación Issue–requisito es una hipótesis revisable: al aprobar un requisito se debe conservar evidencia de la revisión de los criterios de aceptación y evitar duplicar requisitos con distinto ID.
- Esta matriz no equivale a una matriz completa de cumplimiento normativo ni a evidencia de implementación; esas trazabilidades requieren artefactos y verificaciones propios.

Los valores de la columna **Responsable** son roles funcionales propuestos, no personas designadas ni asignaciones aprobadas. La asignación nominal, disponibilidad, autoridad de decisión y sustitución deben confirmarse por el propietario del proyecto antes de aprobar la línea base.

## 15. Revisión de cobertura contra criterios de aceptación de Issues

La revisión se realizó comparando las descripciones y criterios de aceptación vigentes de los Issues enlazados con los requisitos, NFR y artefactos citados en este catálogo. Es una revisión documental interna, no una revisión independiente. Las filas siguientes registran cobertura y brechas observadas; no marcan Issues como resueltos.

Para el desglose operativo de los criterios originales de los Issues #7 y #13, véase la [matriz de cierre verificable](acceptance-closure-matrix-issues-7-13.md), que vincula cada criterio con evidencia mínima, método de verificación y decisiones/umbrales pendientes. Para la definición de campos, fórmulas y estados de decisión spot, véase también la [metodología reproducible de selección spot](spot-market-selection-methodology.md); sus umbrales siguen pendientes de aprobación.

| Issue | Cobertura documental observada | Brecha o acción pendiente frente a criterios de aceptación | Evaluación documental |
|---|---|---|---|
| [#3 — Gobernanza ISO/IEC](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/3) | REQ-P-028 y la matriz normativa distinguen aplicabilidad, estado de edición, evidencia y conformidad/certificación. | Completar justificación norma por norma con referencias oficiales actualizadas; formalizar responsables de gobernanza, datos, riesgos, IA y operación; enlazar artefactos y puertas de entrada/salida por proceso. La matriz sigue preliminar y no acredita implementación. | Parcial |
| [#4 — Ingeniería de software](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/4) | Marco maestro, roadmap, REQ-P-009, REQ-P-014, REQ-P-017, REQ-P-020 y REQ-P-033 describen ciclo de vida, experimentación, trazabilidad y evidencia. | Falta asignar responsables por requisito/disciplina y definir la estrategia verificable de validación de señales/backtests con herramientas, datos, comandos y criterios PASS/FAIL aprobados. | Parcial |
| [#5 — Multiplataforma](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/5) | REQ-P-006, REQ-P-027 y REQ-P-030 incluyen web, Android, iOS y comparación de alternativas. | Faltan matriz de casos de uso por plataforma, comparativa de coste/mantenimiento, límites PWA/offline/notificaciones, pruebas de concepto y ADR aprobada. | Parcial |
| [#6 — Plataforma central de datos y API](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/6) | REQ-P-002, REQ-P-011, REQ-P-032 y NFR-003 cubren fuente de verdad, identidad, procedencia, contratos y frescura. | Faltan catálogo de dominios/propietarios, contratos API concretos, modelo de autenticación/autorización, políticas de caché y pruebas de consistencia entre clientes. | Parcial |
| [#7 — Selección spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7) | REQ-P-003, REQ-P-025, REQ-P-029 y NFR-003 cubren liquidez, universo, API y calidad de datos. | Faltan umbrales aprobados de spread/profundidad/slippage/volumen, tamaños de orden de referencia, capturas fechadas, disponibilidad comprobada de pares Pionex y reglas PASS/FAIL reproducibles. | Parcial |
| [#8 — Arquitectura y trazabilidad](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/8) | Marco maestro, matriz normativa, REQ-P-020, REQ-P-028 y REQ-P-033 documentan principios, arquitectura lógica y evidencia. | Faltan vistas arquitectónicas completas, ADR con alternativas/consecuencias, vínculo riesgo-componente-prueba y confirmación de las ediciones normativas desde fichas oficiales para cada decisión aprobada. | Parcial |
| [#9 — Stack tecnológico](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/9) | REQ-P-010 y REQ-P-030/031 establecen selección basada en criterios, PoC, costes y riesgos. | No hay PoC documentadas con entorno, versiones, comandos y resultados; falta matriz ponderada aprobada, ADR revisable y riesgos residuales. El stack no está seleccionado. | Brecha de evidencia |
| [#10 — Hosting y costes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/10) | REQ-P-031 y NFR-002/008/009/010/015 definen objetivos de costes, portabilidad, observabilidad y recuperación. | Faltan consultas de documentación oficial vigente de proveedores, límites/cuotas, modelo de costes, despliegue de prueba, backup/restore, alertas y ejercicio de migración. | Brecha de evidencia |
| [#11 — Marco maestro](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11) | Se dispone de marco, matriz normativa, catálogo, roadmap y modelo de gobernanza/riesgos. | La línea base no está aprobada; faltan responsables, prioridades acordadas, criterios de salida medibles y verificación de que cada norma/decisión está respaldada por evidencia vigente. | Parcial |
| [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13) | REQ-P-004/005/009/012–027/029 cubren historial, ranking, eventos, predicciones, liquidez y zonas técnicas. | Las tablas contienen roles funcionales propuestos para los 33 requisitos de producto; no son personas nominadas ni asignaciones aprobadas. Faltan responsables nominados, umbrales de UX/rendimiento, protocolo temporal y criterios de aceptación cuantitativos aprobados; la matriz normativa de controles aún no es evidencia de implementación. | Parcial; responsable pendiente |
| [#128 — Flujo integral de investigación por activo](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) | Se han especificado flujo E2E, tres horizontes, investigación de detonantes, zonas técnicas, integridad de captura y abstención. | Falta auditar la implementación real y aportar prueba E2E reproducible, artefactos de salida, validación temporal y trazabilidad requisito-código-prueba. La PR documental no prueba capacidad implementada. | Especificación propuesta; verificación pendiente |
| [#16 — Calidad del libro de órdenes](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/16) | REQ-P-025/029 y NFR-003/011 relacionan calidad de datos, métricas y reproducibilidad. | El PR #15 añade validaciones y pruebas para orden, duplicados y libro cruzado; falta definir y probar explícitamente el tratamiento del libro bloqueado (best_bid == best_ask) y enlazar la evidencia CI definitiva para todos los criterios del Issue. | Parcial; cierre pendiente |
| [#17 — Identidad de mercado spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/17) | REQ-P-025/029 y NFR-003/011 relacionan identidad del par y calidad de datos. | El PR #15 valida baseAsset/quoteAsset en Binance; falta demostrar el contrato equivalente de Pionex, campos ausentes, quote incorrecto, símbolos duplicados y estados no spot/no negociables con pruebas y evidencia CI. | Parcial; cierre pendiente |
| [#18 — Frescura y coste total](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18) | REQ-P-009/025/029/032 y NFR-003/011 vinculan métricas, procedencia y calidad de datos. | Frescura y tarifas permanecen INDETERMINATE; faltan política y umbrales aprobados, fuentes oficiales de tarifas, escenarios de coste y fixtures de datos stale/ausentes y profundidad insuficiente. | Brecha de evidencia |
| [#19 — Preparación operativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/19) | REQ-P-001/007/010/032/033 y NFR-001/002/007/009/015 relacionan ciclo de vida, resiliencia y operación. | No se ha demostrado un expediente integral de pruebas E2E, carga, amenazas, observabilidad, backup/restore ni rollback en entorno identificado. Mantener “no listo para producción”. | Brecha de evidencia; bloqueante antes de producción |
| [#20 — Licencia y dependencias](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/20) | REQ-P-028/033 y NFR-004/005 relacionan gobernanza, obligaciones y gestión normativa. | Falta decisión del propietario sobre modelo de distribución/licencia, inventario y revisión de licencias de dependencias y avisos necesarios. No seleccionar una licencia sin decisión explícita. | Decisión pendiente |
| [#21 — Evaluación independiente](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/21) | REQ-P-028/033 y NFR-007/011 relacionan gobernanza, trazabilidad y evidencia. | Falta definir alcance/criterios, preparar el expediente y decidir si se contrata evaluación independiente. La auditoría documental actual no equivale a conformidad ISO ni certificación. | Decisión y evidencia pendientes |
| [#22 — Alineación de checks obligatorios](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/22) | REQ-P-028/033 y NFR-007/011 relacionan gobernanza de cambios, evidencia y trazabilidad. | La lista requerida del ruleset no coincide con los contextos visibles en todos los PR; hay nombres alternativos y workflows con filtros de rutas. Falta confirmar la mergeabilidad y asegurar que cada check obligatorio se emita consistentemente sin debilitar las puertas. | Brecha de gobernanza; validación pendiente |

### Acciones necesarias para cerrar las brechas

1. Asignar responsables por requisito sin inferir que el autor del documento es automáticamente su responsable de producto o verificación.
2. Convertir los criterios aún cualitativos en umbrales aprobados con método de medición, conjunto de datos, entorno y regla PASS/FAIL.
3. Producir PoC, ADR, capturas de fuentes y pruebas de recuperación donde los Issues lo exigen; una propuesta documental no satisface esos criterios.
4. Revisar de nuevo la matriz cuando se incorporen evidencias y actualizar estado solo con enlaces verificables.

