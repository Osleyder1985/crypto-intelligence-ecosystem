# Hoja de ruta del ecosistema

- **Estado:** propuesta, sujeta a revisión y priorización.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Regla:** una fase no se considera completada por haber escrito su documentación; requiere criterios de salida y evidencia.

## Orden propuesto

| Orden | Fase | Resultado esperado | Dependencias | Puerta de salida | Estado |
|---:|---|---|---|---|---|
| 0 | Gobernanza y marco maestro | Marco, matriz normativa, catálogo de requisitos, trazabilidad y roadmap revisables | Issues #1, #3, #4, #8 y #11; PR #2 pendiente de revisión | Revisión documental y autorización del propietario | En preparación |
| 1 | Requisitos y riesgos del producto | Casos de uso, actores, NFR, límites de alcance, riesgos y métricas | Fase 0 | Requisitos prioritarios aprobados y verificables | Pendiente |
| 2 | Investigación de mercados y fuentes | Matriz de exchanges/pares spot, licencias, cobertura, calidad y coste | Fase 1; Issue #7 | Método de selección aprobado y resultados repetibles | Pendiente |
| 3 | Arquitectura y selección tecnológica | Arquitectura lógica/física inicial, ADR, comparativas y PoC | Fases 1–2; Issues #8–#10 | Alternativas probadas y decisiones autorizadas | Pendiente |
| 4 | Plataforma central de datos | Adaptadores, normalización, procedencia, calidad, persistencia y API | Fases 2–3; Issue #6 | Contratos y tests de calidad reproducibles | Pendiente |
| 5 | Motor de investigación cuantitativa | Métodos versionados, informes, validación estadística y backtesting controlado | Fases 2–4 | Validación temporal, costes, sesgos y limitaciones documentados | Pendiente |
| 6 | Experiencia web y móvil | Flujos de investigación, historial, configuración y resultados en web/Android/iOS | Contratos API y requisitos de UX | Pruebas funcionales, accesibilidad y usabilidad | Pendiente |
| 7 | Verificación integral y seguridad | Suite de pruebas, revisión de amenazas, rendimiento, recuperación y coste | Incrementos funcionales previos | Criterios aprobados alcanzados o excepciones aceptadas | Pendiente |
| 8 | Operación y release controlada | Despliegue, observabilidad, runbooks, backup/restore y rollback | Fase 7 | Aprobación de preparación operativa | Pendiente |
| 9 | Mejora continua | Métricas de producto, incidencias, feedback y nuevas prioridades | Operación controlada | Ciclo de revisión y aprendizaje funcionando | Pendiente |

## Qué no haremos todavía

- No empezar por una gran aplicación monolítica de código sin requisitos, arquitectura y pruebas.
- No adoptar simultáneamente varios proveedores gratuitos sin comparar límites y riesgo de continuidad.
- No entrenar modelos de IA antes de establecer una línea base y una métrica de mejora.
- No habilitar trading real ni almacenar credenciales de trading durante la fase de investigación.
- No tratar documentación o una demo como prueba de calidad de producción.

## Plan inmediato

1. Revisar el borrador de marco maestro y la matriz normativa.
2. Contrastar el catálogo inicial con Issues #3–#10; registrar contradicciones o decisiones nuevas como Issues.
3. Completar la trazabilidad de los requisitos prioritarios y definir criterios medibles.
4. Obtener la aprobación explícita de la línea base documental.
5. Solo entonces comenzar la especificación de requisitos detallada y las PoC técnicas que correspondan.

## Criterio de progreso

El avance se informa por entregables aceptados y evidencia, no por número de archivos, líneas de código o tecnologías seleccionadas. Para cada entrega se reportan: estado, criterio, evidencia, defectos abiertos, riesgos residuales y próxima decisión necesaria.
