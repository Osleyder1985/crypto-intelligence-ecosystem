# Hoja de ruta del ecosistema

- **Estado:** propuesta, sujeta a revisión y priorización.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Regla:** una fase no se considera completada por haber escrito su documentación; requiere criterios de salida y evidencia.

## Orden propuesto

| Orden | Fase | Resultado esperado | Dependencias | Riesgo principal a controlar | Evidencia mínima | Puerta de salida | Estado |
|---:|---|---|---|---|---|---|---|
| 0 | Gobernanza y marco maestro | Marco, matriz normativa, catálogo, trazabilidad, índice y roadmap revisables | Issues #1, #3, #4, #8 y #11; PR #2 pendiente de revisión | Documentos contradictorios o decisiones implícitas | Revisión cruzada de documentos, enlaces y estados de decisión | Revisión documental y autorización del propietario | En preparación |
| 1 | Requisitos y riesgos del producto | Casos de uso, actores, NFR, límites, riesgos y métricas | Fase 0 | Requisitos vagos o prioridades sesgadas | Catálogo aprobado, escenarios de aceptación y registro de riesgos | Requisitos prioritarios aprobados y verificables | Pendiente |
| 2 | Investigación de mercados y fuentes | Matriz de exchanges/pares spot, licencias, cobertura, calidad y coste | Fase 1; Issue #7 | Volumen artificial, datos incompletos, restricciones geográficas o coste oculto | Capturas fechadas, metodología versionada, datos de prueba y comparativa reproducible | Método de selección aprobado y resultados repetibles | Pendiente |
| 3 | Arquitectura y selección tecnológica | Arquitectura lógica/física inicial, ADR, comparativas y PoC | Fases 1–2; Issues #8–#10 | Lock-in, sobreingeniería o PoC no representativas | ADR, criterios fijados antes de probar, resultados brutos y análisis de costes | Alternativas probadas y decisiones autorizadas | Pendiente |
| 4 | Plataforma central de datos | Adaptadores, normalización, procedencia, calidad, persistencia y API | Fases 2–3; Issue #6 | Divergencia entre clientes, datos stale o pérdida de procedencia | Contratos API, fixtures conocidos, tests de calidad y fallos inyectados | Contratos y tests de calidad reproducibles | Pendiente |
| 5 | Motor de investigación cuantitativa | Métodos versionados, informes, validación estadística y backtesting controlado | Fases 2–4 | Sesgo retrospectivo, look-ahead, sobreajuste o costes omitidos | Datasets/versiones identificados, partición temporal, costes y resultados fuera de muestra | Validación temporal, costes, sesgos y limitaciones documentados | Pendiente |
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
