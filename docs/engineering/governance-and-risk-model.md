# Modelo de gobernanza, responsabilidades y riesgos

- **Estado:** propuesta para revisión; no aprobado como línea base.
- **Issues relacionados:** [#3](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/3), [#4](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/4), [#8](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/8), [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11), [#13](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13).
- **Propósito:** convertir el marco general en responsabilidades, artefactos, puertas de control y riesgos que puedan verificarse.
- **Límite:** este documento no acredita conformidad normativa, no crea controles técnicos ya implementados y no autoriza operaciones reales de trading.

## 1. Principios de autoridad y responsabilidad

1. El propietario humano conserva la autoridad final sobre alcance, prioridades, aceptación de riesgos, decisiones de arquitectura, aprobación de línea base, integración y release.
2. La IA puede asumir funciones operativas diferenciadas (análisis, implementación, QA, revisión adversarial, documentación), pero no debe describirse a sí misma como auditor independiente.
3. La misma IA que produce un cambio no constituye una segunda parte independiente que lo audita. Los controles compensatorios son criterios explícitos, pruebas reproducibles, diff revisable, revisión adversarial separada en la secuencia de trabajo y divulgación de limitaciones. Para riesgos críticos que no puedan mitigarse así, recomendar revisión externa independiente.
4. «Adelante» permite continuar el trabajo de ingeniería acordado; no equivale por sí solo a autorizar merge, despliegue, gasto, acceso a secretos, cierre de Issues ni trading real.
5. Ningún riesgo se considera aceptado por silencio. Toda excepción requiere aceptación explícita del responsable autorizado, justificación, riesgo residual y fecha o condición de revisión.
6. Los estados «propuesto», «implementado» y «verificado» son distintos. No declarar un control operativo hasta que exista implementación identificable y evidencia de ejecución.

## 2. Dominios de gobernanza y artefactos

| Dominio | Pregunta de control | Artefacto mínimo | Evidencia de revisión | Estado inicial |
|---|---|---|---|---|
| Producto y alcance | ¿Qué problema, usuarios, límites y resultados se aceptan? | Visión, casos de uso, requisitos y exclusiones | Requisitos con aceptación verificable y decisión registrada | Propuesto |
| Ingeniería y cambios | ¿Cómo se controlan requisitos, código, documentos y releases? | Issues, ramas, PR, ADR, Definition of Done y plan de reversión | Diff revisado, pruebas ejecutadas/no ejecutadas, decisión de integración | Propuesto |
| Arquitectura | ¿Qué componentes, límites, interfaces y atributos de calidad se justifican? | Vistas de arquitectura, catálogo de interfaces, ADR y modelo de amenazas | Alternativas, consecuencias, riesgos y PoC reproducibles | Propuesto |
| Datos y proveedores | ¿Qué fuente, licencia, calidad, frescura y limitaciones aplican? | Catálogo de fuentes, diccionario, linaje y política de frescura | Capturas fechadas, reconciliación, errores de calidad y términos revisados | Propuesto |
| Investigación cuantitativa | ¿Puede reconstruirse y evaluarse la conclusión sin fuga temporal? | Protocolo experimental, versiones, dataset/referencias, benchmark y registro de predicciones | Reproducción, pruebas anti-look-ahead, resultados fuera de muestra y negativos | Propuesto |
| Seguridad y privacidad | ¿Qué activos, amenazas, permisos, secretos y datos personales existen? | Inventario, modelo de amenazas, registro de riesgos y política de secretos/retención | Pruebas de acceso, revisión de dependencias y pruebas de incidentes | Propuesto |
| IA/ML | ¿Hay IA, qué valor aporta y cómo se gobierna? | Inventario de modelos, propósito, datos, evaluación, límites y monitoreo | Comparación con baseline, validación temporal, calibración y criterios de abstención | Condicional; IA no aprobada como requisito técnico |
| Operación y continuidad | ¿Cómo se observa, recupera, migra y controla el coste? | Runbooks, plan de backup/restore, observabilidad, presupuesto y salida del proveedor | Ejercicio de restauración, alerta, recuperación y coste medido | Propuesto |
| Normativa y obligaciones | ¿Qué normas/leyes aplican y por qué? | Matriz de aplicabilidad, fuentes oficiales, responsable y decisión | Referencia fechada, justificación, evidencia y revisión por cambio de alcance | Preliminar |
| UX, accesibilidad y soporte | ¿Los usuarios entienden resultados, incertidumbre y errores? | Casos de uso, criterios UX/accessibility y guías de soporte | Pruebas de tareas, dispositivos objetivo, hallazgos y correcciones | Propuesto |

## 3. Matriz de funciones operativas

Los roles siguientes describen funciones, no personas adicionales ni independencia formal. Salvo asignación expresa posterior, la asignación de responsable de cada dominio permanece pendiente.

| Función | Responsabilidad principal | Puede producir | No puede aprobar por sí sola |
|---|---|---|---|
| Propietario humano | Priorizar, resolver conflictos, aceptar riesgos, aprobar línea base e integración | Decisiones aprobadas, aceptación explícita, autorización de release | No sustituye evidencia técnica necesaria para sostener una afirmación |
| Analista de requisitos | Traducir necesidades a requisitos estables y criterios de aceptación | Catálogo, trazabilidad, escenarios, dependencias | Aprobación final de alcance o riesgo |
| Arquitectura | Comparar opciones y definir límites/interfaces | Vistas, ADR, análisis de trade-offs | Stack definitivo sin decisión autorizada |
| Implementación | Realizar el cambio mínimo trazable en la rama acordada | Código/documentación y pruebas asociadas | Integración a main ni habilitación de trading |
| QA/verificación | Ejecutar criterios y registrar resultados positivos/negativos | Reportes PASS/FAIL, defectos, reproducibilidad | Declarar auditoría independiente si comparte autoría/control |
| Revisión adversarial | Buscar fallos, supuestos, sesgos, amenazas y contraejemplos | Hallazgos priorizados y pruebas adicionales | Aceptación del riesgo residual |
| Responsable de datos | Definir procedencia, calidad, frescura, licencias y retención | Catálogo de fuentes, contratos y controles de calidad | Uso de una fuente sin verificar permisos y limitaciones |
| Responsable de riesgo/seguridad | Mantener amenazas, riesgos y mitigaciones visibles | Modelo de amenazas, registro de riesgos, recomendaciones | Aceptación de riesgos críticos sin autoridad explícita |
| Operación | Preparar despliegue, observabilidad, continuidad y recuperación | Runbooks, mediciones y pruebas de restore | Release sin cumplir la puerta de operación |

## 4. Puerta de calidad y Definition of Done propuesta

Un entregable no se considera terminado hasta que la evidencia aplicable esté registrada. Los elementos no aplicables deben justificarse; los no ejecutados se reportan como pendientes, nunca como PASS.

- [ ] Issue y objetivo trazables; alcance, exclusiones y criterios de aceptación definidos.
- [ ] Requisitos y riesgos afectados identificados; cambios de alcance documentados.
- [ ] Decisiones arquitectónicas relevantes registradas y estado de aprobación visible.
- [ ] Diff revisado; archivos afectados, migraciones y consumidores identificados.
- [ ] Pruebas elegidas según riesgo; entorno, versión, comandos, resultados y artefactos registrados.
- [ ] Pruebas fallidas, omitidas y limitaciones visibles; no se ocultan resultados negativos.
- [ ] Seguridad, privacidad, licencias, accesibilidad y observabilidad evaluadas cuando apliquen.
- [ ] Documentación y trazabilidad actualizadas; enlaces y workflows comprobados.
- [ ] Riesgos residuales, defectos abiertos, excepciones y rollback documentados.
- [ ] Revisión y autorización humana obtenidas antes de integrar o liberar.

Esta lista es una propuesta de control interno. No se presenta como transcripción ni exigencia literal de una norma ISO específica.

## 5. Registro inicial de riesgos

Los riesgos se registran inicialmente sin puntuaciones numéricas porque aún no se han acordado escalas, apetito de riesgo ni umbrales. La prioridad indicada es cualitativa y provisional; los responsables nominales están pendientes.

| ID | Riesgo / causa | Consecuencia posible | Prevención/detección propuesta | Evidencia requerida para reducirlo | Responsable | Estado |
|---|---|---|---|---|---|---|
| RISK-001 | Datos de mercado ausentes, retrasados, duplicados o con unidades incompatibles | Evaluaciones y rankings incorrectos | Validación, timestamps de evento/recepción, procedencia y estados de abstención | Fixtures conocidos, reconciliación y pruebas de datos stale | Pendiente | Abierto |
| RISK-002 | Sesgo de supervivencia, look-ahead o fuga temporal | Rendimiento histórico artificial y predicciones inválidas | Particiones temporales, protocolo previo y tests adversariales | Pruebas anti-look-ahead y reproducción fuera de muestra | Pendiente | Abierto |
| RISK-003 | Correlación temporal confundida con causalidad de noticias/eventos | Conclusiones engañosas sobre movimientos de precio | Separar hechos, hipótesis, alternativas y causalidad validada | Expedientes de evento con timestamps y evidencia contraria | Pendiente | Abierto |
| RISK-004 | Volumen declarado usado como sustituto de liquidez real | Selección de pares con spread/slippage excesivos | Libro bid/ask, trades, tamaños de referencia y comparación entre fuentes | Capturas fechadas y reglas de exclusión reproducibles | Pendiente | Abierto |
| RISK-005 | Par ausente en Pionex o restricciones de acceso/región no detectadas | Resultado no operable para el objetivo del usuario | Verificar par exacto y restricciones por separado del universo comparador | Evidencia de disponibilidad fechada por par | Pendiente | Abierto |
| RISK-006 | Ranking mezcla horizontes, universos o versiones incompatibles | Comparación falsa y decisión de inversión mal informada | Registrar universo, horizonte, metodología, pesos, exclusiones e incertidumbre | Reconstrucción histórica y pruebas de comparabilidad | Pendiente | Abierto |
| RISK-007 | Credenciales o secretos expuestos en cliente, repositorio o logs | Acceso no autorizado y pérdida de control | Secret scanning, mínimo privilegio, redacción de logs y revisión de permisos | Pruebas negativas, configuración y revisión de secretos | Pendiente | Abierto |
| RISK-008 | Dependencia de un plan gratuito, suspensión o cuotas inesperadas | Interrupción o pérdida de datos/costes imprevistos | Medir cuotas, backup/restore, alertas y plan de salida | Prueba de recuperación y modelo de costes con fuentes oficiales | Pendiente | Abierto |
| RISK-009 | Ausencia de CI en la rama base o controles no obligatorios | Cambios defectuosos sin detectar | Verificar workflows y branch rules; informar el alcance real del CI | Run de CI en el HEAD y evidencia de configuración de protección | Pendiente | Abierto |
| RISK-010 | Autoevaluación confundida con auditoría independiente | Falsa confianza en la calidad de los controles | Declarar autoría/limitaciones y solicitar revisión externa para riesgo crítico | Registro de revisión adversarial y límites declarados | Propietario para aceptación; asignación operativa pendiente | Abierto |
| RISK-011 | Referencias normativas, legales o de licencias obsoletas/mal aplicadas | Requisitos incorrectos o uso no autorizado de datos | Fuentes oficiales fechadas, aplicabilidad justificada y revisión por cambios | Matriz actualizada y registro de decisión | Pendiente | Abierto |
| RISK-012 | Recomendaciones interpretadas como garantías de rentabilidad | Daño al usuario y sobreconfianza en el sistema | Exponer horizonte, incertidumbre, cobertura, riesgos y capacidad de abstención | Pruebas de informes y revisión de lenguaje/UX | Pendiente | Abierto |
| RISK-013 | Cambios concurrentes o PR solapados | Sobrescrituras, conflictos y evidencia desactualizada | Un PR activo por objetivo, revisión de archivos y revalidación post-conflicto | Historial de PR, diff y resultados del HEAD final | Propietario/proceso; configuración por verificar | Abierto |
| RISK-014 | Alcance de trading real introducido implícitamente | Riesgo financiero, legal, operativo y de custodia | Mantener solo lectura; evaluación separada y autorización explícita | Pruebas negativas y revisión de arquitectura/configuración | Propietario para cualquier cambio de alcance | Abierto |

### Revisión del registro

Por cada riesgo, antes de aprobar una mitigación se debe completar: probabilidad e impacto según escala aprobada, exposición, tolerancia, responsable, acción, fecha/condición de revisión, evidencia de eficacia y riesgo residual. No se asignan valores ficticios. Los riesgos RISK-002, RISK-007, RISK-010 y RISK-014 deben recibir atención prioritaria antes de validar predicciones, exponer servicios, afirmar independencia de revisión o ampliar el alcance a trading.

## 6. Puertas de decisión y escalamiento

| Puerta | Pregunta | Evidencia mínima | Resultado posible |
|---|---|---|---|
| G0 — Alcance | ¿Está claro qué se construye y qué queda excluido? | Visión, requisitos, Issue y responsables | Continuar, devolver o bloquear |
| G1 — Normativa/riesgos | ¿Se han revisado aplicabilidad, amenazas y riesgos relevantes? | Matriz de aplicabilidad, registro de riesgos y decisiones | Continuar con acciones, escalar o bloquear |
| G2 — Arquitectura/PoC | ¿Las alternativas críticas se compararon con criterios fijados previamente? | ADR, PoC reproducible, coste y riesgos residuales | Recomendar opción; decisión final humana |
| G3 — Verificación | ¿Las pruebas previstas se ejecutaron en el HEAD exacto? | Comandos, entorno, logs/resultados y defectos | PASS, FAIL o BLOCKED; nunca inferido |
| G4 — Integración | ¿La revisión, CI y autorización requerida están presentes? | Diff final, revisión, estado de CI y aprobación explícita | Integrar solo con autorización |
| G5 — Operación/release | ¿Se ha demostrado seguridad, observabilidad, recuperación y rollback? | Ejercicios, runbooks, costes y riesgos residuales | Autorizar release o mantener bloqueado |

Escalamiento obligatorio: si una decisión implica pérdida de datos, exposición de secretos, uso no autorizado de datos, predicción no validada presentada como certeza, cambio de alcance a trading real o un riesgo crítico sin mitigación demostrada, detener esa ruta y elevar la decisión al propietario. Para riesgos críticos que requieran una garantía independiente, solicitar revisión externa competente.

## 7. Relación con la matriz normativa

La matriz normativa define referencias candidatas y aplicabilidad preliminar. Este documento describe controles de proyecto propuestos. Antes de asociar un control con una cláusula normativa específica, se debe comprobar la edición oficial, el texto completo legalmente disponible y el alcance. No inferir que un artefacto interno demuestra por sí solo conformidad, certificación o cumplimiento legal.

## 8. Próximas acciones para completar este modelo

1. Revisar y aprobar o corregir la asignación de autoridad y funciones.
2. Acordar escalas de probabilidad/impacto, tolerancia y quién acepta cada categoría de riesgo.
3. Verificar el estado real de branch protection, CI y permisos del repositorio.
4. Completar responsables, evidencias y decisiones de aplicabilidad normativa.
5. Convertir los riesgos prioritarios en pruebas/Issues específicos solo después de buscar trabajo abierto equivalente.
6. Revisar el documento mediante PR; mantener todos los estados como propuesta hasta autorización expresa.

## 9. Historial y limitaciones

Este documento es una propuesta documental creada para apoyar los Issues #3, #4 y #8 dentro del trabajo existente del PR #12. No prueba que los controles descritos estén implementados, que la rama principal esté protegida, que exista CI satisfactorio para cada PR, que se hayan realizado PoC o que el producto sea conforme a ISO.