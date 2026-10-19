# Catálogo inicial de requisitos y trazabilidad

- **Estado:** borrador de trabajo; no constituye una línea base aprobada.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Issue relacionado:** [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- **Convención:** los identificadores son estables; si cambia sustancialmente el significado, se retira el ID anterior y se crea uno nuevo.

## 1. Requisitos de producto (borrador)

| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado |
|---|---|---|---|---|---|
| REQ-P-001 | El sistema permitirá iniciar una investigación bajo demanda con alcance y parámetros explícitos. | Alta | Una petición válida crea un trabajo identificable y devuelve estado/resultados o error documentado; no requiere ejecución continua 24/7. | Pruebas de API y flujo de usuario | Propuesto |
| REQ-P-002 | Los clientes consumirán una fuente central de verdad a través de contratos API versionados. | Alta | Web y móvil reciben la misma definición de datos y versión de dominio para una misma consulta; las diferencias de caché son detectables. | Pruebas de contrato e integración | Propuesto |
| REQ-P-003 | El sistema permitirá explorar activos y pares spot usando criterios reproducibles de liquidez y calidad. | Alta | Cada resultado declara exchange, par, tipo de mercado, timestamp, métricas disponibles, exclusiones y limitaciones. | Dataset de referencia y pruebas de clasificación | Propuesto |
| REQ-P-004 | Los informes distinguirán observaciones, cálculos, interpretaciones, hipótesis y recomendaciones. | Alta | Cada afirmación cuantitativa identifica método, ventana temporal, fuente y limitaciones; las hipótesis no se etiquetan como hechos. | Revisión de informes y pruebas de esquema | Propuesto |
| REQ-P-005 | Cada investigación conservará una evaluación histórica versionada y reproducible sin sobrescribir ejecuciones anteriores. | Alta | Cada ejecución recibe un identificador único y queda enlazada con las evaluaciones anteriores; se recuperan método/versión, parámetros, marcas temporales y entradas o referencias inmutables, y se señalan los datos irrecuperables. | Prueba de reproducción y verificación de historial inmutable | Propuesto |
| REQ-P-006 | La interfaz soportará web, Android e iOS. | Alta | Los flujos principales definidos en requisitos de UX se completan en cada plataforma objetivo con criterios equivalentes. | Pruebas funcionales y de usabilidad por plataforma | Propuesto |
| REQ-P-007 | La ejecución real de órdenes permanecerá deshabilitada hasta una decisión y evaluación separadas. | Crítica | No hay credenciales de trading ni ruta de ejecución habilitada en la versión de investigación; pruebas de configuración y revisión de secretos. | Inspección de arquitectura, secretos y pruebas negativas | Propuesto |
| REQ-P-008 | El sistema informará errores, datos incompletos y fallos de proveedor sin presentar resultados parciales como completos. | Alta | Ante entradas incompletas o proveedor fallido, la respuesta identifica el fallo y marca cualquier resultado parcial. | Pruebas de fallo inyectado | Propuesto |
| REQ-P-009 | Los resultados de análisis cuantitativo incluirán costes y controles contra sesgos relevantes. | Alta | La metodología documenta comisiones, spread, deslizamiento estimado, sesgos considerados y validación fuera de muestra cuando proceda. | Informe de validación y tests | Propuesto |
| REQ-P-010 | La selección de stack y hosting se basará en criterios previamente definidos y evidencia comparativa. | Alta | Cada selección aprobada enlaza requisitos, pesos/umbrales acordados, alternativas, PoC, resultados, costes y riesgos residuales. | ADR y resultados reproducibles de PoC | Propuesto |

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

| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado |
|---|---|---|---|---|---|
| REQ-P-011 | Cada dato analítico tendrá identidad canónica, procedencia, marcas temporales y estado de calidad. | Crítica | El sistema distingue activo, red/contrato cuando aplique, exchange, mercado/par y proveedor; detecta conflictos de identidad y no los resuelve silenciosamente. | Esquema versionado, catálogo de identidad, fixtures y pruebas de reconciliación | Propuesto |
| REQ-P-012 | Los informes separarán calidad de evidencia, puntuación del activo, oportunidad por horizonte y riesgo. | Crítica | Una puntuación no oculta cobertura deficiente, incertidumbre ni incompatibilidad entre horizontes; el sistema puede abstenerse de emitir una conclusión cuando falten datos críticos. | Casos límite, pruebas de reglas de abstención y revisión de informes | Propuesto |
| REQ-P-013 | Las predicciones registradas serán probabilísticas, fechadas y evaluables posteriormente. | Alta | Cada predicción conserva instante de emisión, horizonte, evento/variable objetivo, probabilidad o intervalo, condiciones de invalidación, versión del método y resultado posterior; no se reescribe retroactivamente. | Registro inmutable, evaluación fuera de muestra y métricas de calibración | Propuesto |
| REQ-P-014 | Las estrategias y señales se compararán con líneas base y validación temporal fuera de muestra. | Crítica | Se documentan particiones temporales, selección del universo, costes, sesgos examinados, benchmarks y resultados negativos; ninguna métrica de prueba se usa para ajustar y certificar el mismo experimento sin separación explícita. | Protocolo experimental versionado, resultados brutos y reproducción independiente | Propuesto |
| REQ-P-015 | El análisis fundamental/on-chain será específico al tipo de activo y a la disponibilidad verificable de datos. | Alta | Se registran aplicabilidad, fuente, timestamp, unidad, cobertura y limitaciones para oferta/emisiones/unlocks, concentración, actividad, seguridad y métricas de protocolo cuando correspondan; datos no aplicables no se puntúan como cero. | Diccionario de métricas por categoría de activo y pruebas de ausencia/no aplicabilidad | Propuesto |
| REQ-P-016 | El motor de riesgo evaluará exposición a mercado, volatilidad, drawdown, correlaciones y escenarios adversos. | Alta | Cada evaluación identifica horizonte, método, ventana, supuestos, exposición relevante y limitaciones; los resultados se comparan con benchmarks y escenarios definidos previamente. | Casos de prueba, análisis de sensibilidad y pruebas de estrés reproducibles | Propuesto |
| REQ-P-017 | El producto mantendrá un benchmark de calidad analítica con protocolo reproducible. | Alta | Las comparaciones publican periodo, universo, datos, versiones, criterios, métricas y limitaciones; se incluyen fallos, falsos positivos y resultados no concluyentes, no solo casos favorables. | Protocolo de benchmark, dataset versionado y reporte reproducible | Propuesto |
| REQ-P-018 | Los trabajos largos de investigación informarán su estado y conservarán diagnóstico de fallos. | Alta | El usuario puede distinguir en cola, en ejecución, completado, parcial, cancelado y fallido; un resultado parcial queda marcado y vinculado a errores y fuentes no disponibles. | Pruebas de estados, fallos inyectados y pruebas de integración | Propuesto |
| REQ-P-019 | El sistema detectará degradación de fuentes, métodos y modelos a lo largo del tiempo. | Alta | Se miden frescura/cobertura de datos y cambios de rendimiento; alertas y revisiones quedan registradas sin cambiar silenciosamente versiones o umbrales. | Pruebas de datos degradados, monitorización y registro de cambios | Propuesto |
| REQ-P-020 | Cada conclusión relevante podrá recorrerse hacia atrás hasta su evidencia y configuración de ejecución. | Crítica | Desde una conclusión se recuperan requisito, método/versión, parámetros, fuentes, timestamps, transformaciones, advertencias, prueba de validación y aprobaciones aplicables. | Prueba de trazabilidad de extremo a extremo | Propuesto |
| REQ-P-021 | El sistema comparará evaluaciones históricas del mismo activo y distinguirá cambios de mercado de cambios metodológicos o de datos. | Alta | Para dos o más ejecuciones muestra cambios absolutos/relativos en indicadores, eventos, liquidez, riesgos, puntuación y conclusión; identifica cambios debidos a método, parámetros, proveedor, cobertura o correcciones. | Pruebas con evaluaciones versionadas y casos de cambio de metodología/proveedor | Propuesto |
| REQ-P-022 | El sistema generará rankings reproducibles solo con evaluaciones comparables y vigentes. | Alta | Cada ranking registra universo, exclusiones, horizonte, timestamp, metodología/pesos, penalización por datos ausentes e incertidumbre; puede reconstruirse con las versiones usadas y no mezcla horizontes incompatibles sin normalización documentada. | Reconstrucción de ranking histórico, pruebas de comparabilidad y sensibilidad a pesos | Propuesto |
| REQ-P-023 | El sistema detectará candidatos a movimientos de mercado y relacionará eventos temporales con evidencia verificable. | Alta | Las reglas para inicio, aceleración, agotamiento y reversión están definidas por temporalidad; las reconstrucciones históricas solo usan información disponible entonces; noticias y eventos conservan fuente, publicación/captura, zona horaria, relevancia, alternativas y grado de evidencia, sin inferir causalidad por proximidad temporal. | Fixtures OHLCV, pruebas anti-look-ahead y expedientes reproducibles de eventos | Propuesto |
| REQ-P-024 | El sistema mantendrá una memoria consultable de eventos y predicciones con resultados posteriores. | Alta | Cada predicción conserva timestamp, horizonte, condiciones de invalidación, método/versión y resultado observado; las recurrencias se evalúan fuera de muestra con controles de supervivencia, fuga temporal, sobreajuste y costes cuando proceda. | Registro histórico, protocolo temporal, resultados negativos y métricas de calibración | Propuesto |
| REQ-P-025 | El sistema analizará profundidad bid/ask, operaciones recientes y métricas de liquidez de pares spot en un universo de exchanges validado. | Alta | Evaluará como objetivo inicial 15–20 exchanges, sujeto a cobertura real, acceso API, límites, comparabilidad y restricciones legales/geográficas; normaliza símbolos, unidades y timestamps; calcula spread, profundidad, desequilibrio y slippage para tamaños de referencia cuando existan datos suficientes; distingue instantáneas de históricos y documenta el inicio de captura propia. Solo lectura, sin ejecución de órdenes. | Fixtures de libro/trades, comparación de fuentes, pruebas de frescura y reporte de cobertura por exchange/par | Propuesto |
| REQ-P-026 | El sistema identificará zonas de soporte y resistencia con métodos documentados y varias temporalidades. | Alta | Cada zona muestra rango, método, contactos/rechazos, antigüedad, volumen asociado si existe, distancia al precio, fortaleza estimada, invalidación e incertidumbre; las señales históricas no usan información futura y no presentan la zona como garantía. | Pruebas retrospectivas anti-look-ahead, sensibilidad entre métodos y ejemplos reproducibles | Propuesto |
| REQ-P-027 | La interfaz permitirá navegar de forma coherente entre fichas de activos, evaluaciones históricas, rankings, eventos y evidencia. | Alta | Los flujos principales funcionan en web y clientes móviles objetivo; los estados de carga/error/datos insuficientes son explícitos y las visualizaciones de incertidumbre son legibles y responsivas. | Pruebas de tareas, accesibilidad, responsividad y comprensión de informes | Propuesto |

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
