# Hoja de ruta del ecosistema

- **Estado:** propuesta, sujeta a revisión y priorización.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Issue relacionado:** [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- **Regla:** una fase no se considera completada por haber escrito su documentación; requiere criterios de salida y evidencia.

## Orden propuesto

| Orden | Fase | Resultado esperado | Dependencias | Riesgo principal a controlar | Evidencia mínima | Puerta de salida | Estado |
|---:|---|---|---|---|---|---|---|
| 0 | Gobernanza y marco maestro | Marco, matriz normativa, catálogo, trazabilidad, índice y roadmap revisables | Issues #1, #3, #4, #8 y #11; PR #2 pendiente de revisión | Documentos contradictorios o decisiones implícitas | Revisión cruzada de documentos, enlaces y estados de decisión | Revisión documental y autorización del propietario | En preparación |
| 1 | Requisitos y riesgos del producto | Casos de uso, actores, NFR, límites, riesgos y métricas | Fase 0 | Requisitos vagos o prioridades sesgadas | Catálogo aprobado, escenarios de aceptación y registro de riesgos | Requisitos prioritarios aprobados y verificables | Pendiente |
| 2 | Investigación de mercados y fuentes | Matriz de exchanges/pares spot, licencias, cobertura, calidad y coste | Fase 1; Issue #7 | Volumen artificial, datos incompletos, restricciones geográficas o coste oculto | Capturas fechadas, metodología versionada, datos de prueba y comparativa reproducible | Método de selección aprobado y resultados repetibles | Pendiente |
| 3 | Arquitectura y selección tecnológica | Arquitectura lógica/física inicial, ADR, comparativas y PoC | Fases 1–2; Issues #8–#10 | Lock-in, sobreingeniería o PoC no representativas | ADR, criterios fijados antes de probar, resultados brutos y análisis de costes | Alternativas probadas y decisiones autorizadas | Pendiente |
| 4 | Plataforma central de datos | Adaptadores, normalización, procedencia, calidad, persistencia y API | Fases 2–3; Issue #6 | Divergencia entre clientes, datos stale o pérdida de procedencia | Contratos API, fixtures conocidos, tests de calidad y fallos inyectados | Contratos y tests de calidad reproducibles | Pendiente |
| 5 | Motor de investigación cuantitativa | Evaluaciones históricas, comparación y ranking, detección de movimientos/eventos, memoria predictiva, análisis de libro spot y zonas de soporte/resistencia | Fases 2–4; requisitos REQ-P-005 y REQ-P-021–REQ-P-027 | Fuga temporal, falsa causalidad, ranking incomparable, datos de profundidad no históricos o costes omitidos | Datasets/versiones identificados, reconstrucción histórica, fuentes/eventos fechados, fixtures de libro/trades, pruebas anti-look-ahead y resultados fuera de muestra | Cada capacidad tiene criterios medibles, evidencia reproducible, límites de cobertura y riesgos explícitos; no implica trading real | Pendiente |
| 6 | Experiencia web y móvil | Flujos de investigación, historial, configuración y resultados en web/Android/iOS | Contratos API y requisitos de UX | Flujos inconsistentes o barreras de accesibilidad | Pruebas en dispositivos objetivo, escenarios de tareas y hallazgos de usabilidad | Pruebas funcionales, accesibilidad y usabilidad | Pendiente |
| 7 | Verificación integral y seguridad | Suite de pruebas, revisión de amenazas, rendimiento, recuperación y coste | Incrementos funcionales previos | Vulnerabilidades, fallos sistémicos o umbrales no definidos | Resultados de pruebas, amenazas, defectos abiertos y riesgos residuales | Criterios aprobados alcanzados o excepciones aceptadas | Pendiente |
| 8 | Operación y release controlada | Despliegue, observabilidad, runbooks, backup/restore y rollback | Fase 7 | Pérdida de datos, costes inesperados o recuperación no probada | Ejercicio de restauración, alerta/diagnóstico, coste observado y rollback ensayado | Aprobación de preparación operativa | Pendiente |
| 9 | Mejora continua | Métricas de producto, incidencias, feedback y nuevas prioridades | Operación controlada | Repetir errores o degradación silenciosa | Revisiones de métricas, postmortems y Issues priorizados | Ciclo de revisión y aprendizaje documentado | Pendiente |

## Qué no haremos todavía

- No empezar por una gran aplicación de código sin requisitos, arquitectura y pruebas.
- No adoptar simultáneamente varios proveedores gratuitos sin comparar límites y riesgo de continuidad.
- No entrenar modelos de IA antes de establecer una línea base y una métrica de mejora.
- No habilitar trading real ni almacenar credenciales de trading durante la fase de investigación.
- No tratar documentación o una demo como prueba de calidad de producción.

## Plan inmediato

1. Revisar el borrador de marco maestro, la matriz normativa, el catálogo y este roadmap.
2. Contrastar el catálogo inicial con Issues #3–#10; registrar contradicciones o decisiones nuevas como Issues.
3. Completar la trazabilidad de los requisitos prioritarios y definir criterios medibles.
4. Obtener la aprobación explícita de la línea base documental.
5. Solo entonces comenzar la especificación de requisitos detallada y las PoC técnicas que correspondan.

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
