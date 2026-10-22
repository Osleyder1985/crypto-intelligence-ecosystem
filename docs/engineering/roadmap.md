# Hoja de ruta del ecosistema

- **Estado:** propuesta, sujeta a revisión y priorización.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Issue relacionado:** [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- **Regla:** una fase no se considera completada por haber escrito su documentación; requiere criterios de salida y evidencia.

## Orden propuesto

| Orden | Fase | Resultado esperado | Dependencias | Riesgo principal a controlar | Evidencia mínima | Puerta de salida | Estado |
|---:|---|---|---|---|---|---|---|
| 0 | Gobernanza y marco maestro | Marco, matriz normativa, catálogo, trazabilidad, índice, roadmap, modelo de responsabilidades, registro de riesgos y política de licencias/dependencias | Issues #1, #3, #4, #8, #11, #20 y #21; PR #12 integrado; decisiones de licencia y evaluación independiente pendientes | Documentos contradictorios, licencias incompatibles o evaluación independiente prematura | Revisión cruzada, inventario de dependencias/licencias y alcance de evaluación independiente | Revisión documental, decisión de licencia por el propietario y alcance de revisión autorizado | En preparación |
| 1 | Requisitos y riesgos del producto | Casos de uso, actores, NFR, límites, riesgos y métricas | Fase 0 | Requisitos vagos o prioridades sesgadas | Catálogo aprobado, escenarios de aceptación y registro de riesgos | Requisitos prioritarios aprobados y verificables | Pendiente |
| 2 | Investigación de mercados y fuentes | Matriz de exchanges/pares spot, identidad base/cotizada, calidad del libro, frescura, comisiones y coste total | Fase 1; Issues #7, #16, #17 y #18 | Símbolos ambiguos, libros inválidos, datos obsoletos, tarifas incompletas o coste no comparable | Capturas fechadas, procedencia/hash, validación de niveles, identidad exacta, estados de frescura/comisiones y comparativa reproducible | Método y umbrales aprobados; casos inválidos bloqueados; resultados repetibles con límites explícitos | Pendiente |
| 3 | Arquitectura y selección tecnológica | Arquitectura lógica/física inicial, ADR, comparativas y PoC | Fases 1–2; Issues #8–#10 | Lock-in, sobreingeniería o PoC no representativas | ADR, criterios fijados antes de probar, resultados brutos y análisis de costes | Alternativas probadas y decisiones autorizadas | Pendiente |
| 4 | Plataforma central de datos | Adaptadores, normalización, procedencia, calidad, persistencia y API | Fases 2–3; Issue #6 | Divergencia entre clientes, datos stale o pérdida de procedencia | Contratos API, fixtures conocidos, tests de calidad y fallos inyectados | Contratos y tests de calidad reproducibles | Pendiente |
| 5 | Motor de investigación cuantitativa | Evaluaciones históricas, comparación y ranking, detección de movimientos/eventos, memoria predictiva, análisis de libro spot y zonas de soporte/resistencia | Fases 2–4; requisitos REQ-P-004, REQ-P-005, REQ-P-009, REQ-P-012–REQ-P-017 y REQ-P-020–REQ-P-026 | Fuga temporal, falsa causalidad, ranking incomparable, datos de profundidad no históricos o costes omitidos | Datasets/versiones identificados, reconstrucción histórica, fuentes/eventos fechados, fixtures de libro/trades, pruebas anti-look-ahead y resultados fuera de muestra | Cada capacidad tiene criterios medibles, evidencia reproducible, límites de cobertura y riesgos explícitos; no implica trading real | Pendiente |
| 6 | Experiencia web y móvil | Flujos de investigación, historial, configuración y resultados en web/Android/iOS | Contratos API y requisitos de UX | Flujos inconsistentes o barreras de accesibilidad | Pruebas en dispositivos objetivo, escenarios de tareas y hallazgos de usabilidad | Pruebas funcionales, accesibilidad y usabilidad | Pendiente |
| 7 | Verificación integral y seguridad | Suite de pruebas, revisión de amenazas, rendimiento, recuperación, coste y revisión de calidad independiente cuando exista una línea base integrada | Incrementos funcionales previos; Issue #19; prerrequisitos de evidencia para #21 | Vulnerabilidades, fallos sistémicos, resultados no reproducibles o evaluación prematura | Resultados de pruebas, amenazas, defectos abiertos, riesgos residuales y revisión independiente delimitada | Criterios aprobados alcanzados o excepciones aceptadas; hallazgos críticos resueltos | Pendiente |
| 8 | Operación y release controlada | Despliegue, observabilidad, runbooks, backup/restore, rollback y evidencia de preparación de producción | Fase 7; Issue #19 | Pérdida de datos, costes inesperados, controles de seguridad incompletos o recuperación no probada | Ejercicio de restauración, alertas/diagnóstico, coste observado, rollback ensayado y riesgos residuales aceptados | Aprobación formal de preparación operativa; no basta con CI verde | Pendiente |
| 9 | Mejora continua | Métricas de producto, incidencias, feedback y nuevas prioridades | Operación controlada | Repetir errores o degradación silenciosa | Revisiones de métricas, postmortems y Issues priorizados | Ciclo de revisión y aprendizaje documentado | Pendiente |

## Qué no haremos todavía

- No empezar por una gran aplicación de código sin requisitos, arquitectura y pruebas.
- No adoptar simultáneamente varios proveedores gratuitos sin comparar límites y riesgo de continuidad.
- No entrenar modelos de IA antes de establecer una línea base y una métrica de mejora.
- No habilitar trading real ni almacenar credenciales de trading durante la fase de investigación.
- No tratar documentación o una demo como prueba de calidad de producción.

## Plan inmediato

1. **Continuar Issue #7 — selección reproducible de mercados Spot.** Ya existen sondas públicas de libros para siete exchanges y una primera captura de volumen cotizado 24 h; ampliar la evidencia temporal y la cobertura antes de elegir ganadores o cerrar el Issue.
2. **Desarrollar Issue #13 — motor de investigación cuantitativa.** Convertir capacidades requeridas (historial persistente, comparación, ranking, eventos, series multitemporales, libro y soportes/resistencias) en requisitos verificables, pruebas temporales anti-leakage y una primera línea base descriptiva.
3. **Avanzar Issue #6 — plataforma central de datos.** Definir contratos canónicos versionados, procedencia, persistencia y API común para clientes; no duplicar lógica analítica por dispositivo.
4. **Mantener Issue #19 como bloqueo de producción.** Preparar pruebas integrales, seguridad, rendimiento, restauración, alertas y rollback con evidencia ejecutada; CI verde no equivale a readiness.
5. **Resolver gobernanza pendiente en #11/#20/#21 y arquitectura en #8–#10.** Documentar propuestas y evidencias, pero reservar al propietario las decisiones legales/de producto que realmente le correspondan.
6. Mantener trazabilidad requisito → Issue → implementación → prueba → artefacto. No cerrar Issues por mera documentación ni declarar resultados que la evidencia no soporte.

## Criterio de progreso

El avance se informa por entregables aceptados y evidencia, no por número de archivos, líneas de código o tecnologías seleccionadas. Para cada entrega se reportan: estado, criterio, evidencia, defectos abiertos, riesgos residuales y próxima decisión necesaria.


## Puertas de calidad analítica adicionales

Estas puertas complementan las fases anteriores y se aplican antes de declarar fiable una capacidad de investigación. Son criterios propuestos, no evidencia de implementación.

| Puerta | Comprobación obligatoria | Evidencia mínima | No se acepta como sustituto |
|---|---|---|---|
| QD-1. Identidad y procedencia | Activos, contratos/redes, exchanges, pares, unidades y tiempos quedan identificados sin ambigüedad; conflictos y ausencias son visibles. | Catálogo canónico, fixtures, resultados de reconciliación y pruebas de calidad. | Símbolos coincidentes o volumen reportado como única prueba de identidad/calidad. |
| QD-2. Reproducibilidad histórica | Una ejecución conserva método, parámetros, datos/referencias, versiones, transformaciones y advertencias suficientes para reconstrucción. | Reproducción independiente de una muestra de ejecuciones. | Captura de pantalla o informe sin entradas y configuración. |
| QD-3. Validez temporal | Las señales históricas solo usan información disponible en el instante de emisión y los experimentos separan desarrollo, validación y prueba. | Tests anti-leakage, particiones temporales documentadas y revisión de timestamps. | Backtest con datos actuales aplicados retrospectivamente sin control point-in-time. |
| QD-4. Comparación cuantitativa | El método se compara con líneas base, costes realistas y escenarios relevantes; se conservan resultados negativos. | Protocolo fijado previamente, resultados brutos y evaluación fuera de muestra. | Un único periodo favorable o métricas elegidas después de ver resultados. |
| QD-5. Calibración y abstención | Se mide la calidad de las predicciones y el sistema puede declarar evidencia insuficiente. | Métricas de calibración/utilidad por horizonte, cobertura y casos de abstención. | Confianza verbal no calibrada o predicción presentada como certeza. |
| QD-6. Robustez y riesgo | Se examina sensibilidad a parámetros, liquidez, costes, correlaciones, cambios de régimen y escenarios adversos. | Análisis de sensibilidad y estrés reproducible. | Una puntuación única que oculta riesgo y limitaciones. |
| QD-7. Benchmark y transparencia | Las comparaciones identifican universo, periodo, versión, métricas, incertidumbre y límites, incluyendo falsos positivos. | Protocolo reproducible y reporte susceptible de revisión independiente. | Afirmaciones de «mejor del mundo» sin comparación independiente. |
| QD-8. Operación recuperable | Trabajos parciales/fallidos son explícitos; errores de proveedores, límites de API y recuperación son probados. | Pruebas de fallo, correlación de ejecución, backup/restore y runbooks cuando exista despliegue. | Demo exitosa sin pruebas de fallo o recuperación. |

## Prioridad de secuenciación revisada

1. **Primero, identidad, procedencia y calidad de datos.** Sin ello, los cálculos posteriores pueden ser precisos matemáticamente y aun así equivocados.
2. **Después, historial reproducible y contratos comunes.** No construir rankings ni memoria de eventos sobre resultados que no puedan reconstruirse.
3. **Luego, métodos descriptivos y líneas base transparentes.** Establecer resultados de referencia antes de probar modelos complejos.
4. **Después, validación predictiva y riesgo.** Añadir calibración, controles temporales, sensibilidad y abstención.
5. **En paralelo controlado, experiencia de usuario.** Probar cómo las personas entienden evidencia, incertidumbre, comparaciones y estados de trabajo.
6. **Antes de cualquier release, seguridad y operación.** Validar límites, recuperación, costes y riesgos residuales.

No se fijan fechas de calendario ni umbrales numéricos en esta revisión: dependen de los requisitos aprobados, disponibilidad de datos, coste y resultados de una línea base inicial.

## Matriz de cobertura frente a Issues #3–#10

La sección 18 del [marco maestro](master-framework.md) contiene la correspondencia Issue → requisitos → evidencia de cierre pendiente. Esta matriz evita interpretar la existencia de requisitos como cierre de una investigación técnica.

Antes de cerrar los Issues:
- **#3–#4:** verificar aplicabilidad normativa, responsables, gestión de riesgos y definición de terminado con evidencia de pruebas.
- **#5–#6:** comparar clientes con PoC y validar contratos API, frescura, permisos y consistencia.
- **#7:** ejecutar la metodología spot con capturas fechadas y publicar cobertura PASS/FAIL por exchange/par, incluida disponibilidad exacta en Pionex.
- **#8–#9:** producir vistas/ADR y ejecutar PoC con criterios fijados antes de puntuar.
- **#10:** verificar documentación oficial vigente de hosting y demostrar costes, operación desde móvil, restauración y salida del proveedor.

Todos estos resultados permanecen pendientes hasta que existan evidencias reproducibles y decisiones explícitas. No se asignan puntuaciones, costes, cobertura ni resultados de PoC por anticipado.

## Índice de requisitos por fase y prioridad

La vista ordenada y el mapeo primario de cada requisito de producto se mantienen en el [catálogo de requisitos y trazabilidad](requirements-traceability-catalog.md), sección 13. La fase primaria se usa para planificar; las dependencias cruzadas se documentan en la matriz de trazabilidad y no duplican IDs. Las prioridades son iniciales, no aprobadas. El catálogo incorpora ahora una clasificación propuesta de los NFR-001–NFR-018 por fase primaria y prioridad (sección 12); sus umbrales medibles, responsables y aceptación por el propietario siguen pendientes.

### Cobertura del motor cuantitativo

La Fase 5 incluye, como mínimo, REQ-P-004, REQ-P-005, REQ-P-009, REQ-P-012–REQ-P-017 y REQ-P-020–REQ-P-026. También depende de identidad/calidad de datos (Fase 2), plataforma central (Fase 4), control de trabajos y frescura (Fase 4) y validación integral (Fase 7). La memoria y la monitorización operativa no sustituyen la validación fuera de muestra ni las pruebas anti-look-ahead.


## Flujo E2E de investigación por activo — dependencia prioritaria

El [Issue #128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) y la [especificación de flujo](issue-128-end-to-end-asset-research.md) concretan la integración de los componentes analíticos. La fase no se declara terminada hasta que una prueba E2E demuestre entrada de activo, expediente histórico, análisis de movimientos y posibles detonantes, soportes/resistencias, evaluación independiente de corto/medio/largo plazo, persistencia y resultado reproducible.

**Puerta de salida:** evidencia archivada de tests E2E y de integración, manejo de cobertura insuficiente, anti-look-ahead, integridad de capturas, trazabilidad de fuentes, validación temporal y resultado `INDETERMINATE` cuando corresponda. La documentación por sí sola no cierra la fase.
