# Catálogo inicial de requisitos y trazabilidad

- **Estado:** borrador de trabajo; no constituye una línea base aprobada.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Convención:** los identificadores son estables; si cambia sustancialmente el significado, se retira el ID anterior y se crea uno nuevo.

## 1. Requisitos de producto (borrador)

| ID | Requisito | Prioridad inicial | Criterio de aceptación propuesto | Evidencia prevista | Estado |
|---|---|---|---|---|---|
| REQ-P-001 | El sistema permitirá iniciar una investigación bajo demanda con alcance y parámetros explícitos. | Alta | Una petición válida crea un trabajo identificable y devuelve estado/resultados o error documentado; no requiere ejecución continua 24/7. | Pruebas de API y flujo de usuario | Propuesto |
| REQ-P-002 | Los clientes consumirán una fuente central de verdad a través de contratos API versionados. | Alta | Web y móvil reciben la misma definición de datos y versión de dominio para una misma consulta; las diferencias de caché son detectables. | Pruebas de contrato e integración | Propuesto |
| REQ-P-003 | El sistema permitirá explorar activos y pares spot usando criterios reproducibles de liquidez y calidad. | Alta | Cada resultado declara exchange, par, tipo de mercado, timestamp, métricas disponibles, exclusiones y limitaciones. | Dataset de referencia y pruebas de clasificación | Propuesto |
| REQ-P-004 | Los informes distinguirán observaciones, cálculos, interpretaciones, hipótesis y recomendaciones. | Alta | Cada afirmación cuantitativa identifica método, ventana temporal, fuente y limitaciones; las hipótesis no se etiquetan como hechos. | Revisión de informes y pruebas de esquema | Propuesto |
| REQ-P-005 | Las investigaciones históricas conservarán información suficiente para reproducir el cálculo. | Alta | Se puede recuperar versión del método, parámetros, marcas temporales y referencias a entradas/datasets; cualquier dato irrecuperable se señala. | Prueba de reproducción independiente | Propuesto |
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
