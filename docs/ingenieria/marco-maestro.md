# Marco maestro de ingeniería del ecosistema

- **Estado:** propuesta para revisión; no aprobado como línea base.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Versión documental:** 0.1.0-draft
- **Rama:** `docs/issue-11-marco-maestro`
- **Idioma de trabajo:** español; se conservan los nombres técnicos normalizados.
- **Última revisión de fuentes normativas:** 2026-10-19.

## 1. Propósito

Establecer un sistema de ingeniería que permita especificar, construir, verificar, operar y mejorar un ecosistema de inteligencia para criptoactivos. La calidad se demostrará con requisitos medibles, decisiones justificadas, evidencia reproducible y revisiones documentadas; no con declaraciones de intención ni con la mera mención de normas.

Este documento es una propuesta inicial. No acredita conformidad con ninguna norma, no equivale a una auditoría y no sustituye el texto íntegro de normas protegidas por derechos de autor.

## 2. Visión de producto

Construir una plataforma de investigación de criptoactivos que permita al usuario iniciar análisis bajo demanda y obtener resultados explicables, trazables y reproducibles. Los clientes previstos son web, Android e iOS; escritorio queda como alternativa por justificar mediante requisitos y coste total.

La plataforma debe compartir una fuente central de verdad y una API versionada. Los clientes pueden usar caché local para experiencia de usuario, pero no deben mantener universos de datos o reglas de negocio divergentes.

### Capacidades objetivo sujetas a requisitos y validación

1. Exploración de mercados y pares **spot** con controles de liquidez, calidad de datos y disponibilidad.
2. Investigación bajo demanda de activos, eventos, noticias y contexto de mercado.
3. Análisis cuantitativo con metodología, parámetros, ventana temporal, costes y limitaciones visibles.
4. Informes que separen hechos observados, datos derivados, interpretación, hipótesis y recomendaciones.
5. Historial reproducible de investigaciones, fuentes, versiones de algoritmos y resultados.
6. Experiencia multiplataforma accesible, segura y coherente.
7. Gestión de riesgos, privacidad, observabilidad, recuperación y mejora continua.

Estas capacidades son objetivos de producto, no funcionalidades ya implementadas.

## 3. Límites explícitos

- **Fuera de alcance por ahora:** envío o ejecución real de órdenes, custodia de fondos, gestión de claves de trading y promesas de rentabilidad.
- No se presupone que una IA/ML sea necesaria. Se evaluará únicamente si aporta valor medible frente a una línea base no basada en IA.
- No se fija todavía lenguaje, framework, base de datos, nube, proveedor de mercado ni topología de despliegue.
- No se considerará que un activo es una oportunidad solo por tener un precio nominal bajo.
- No se presentará una predicción como certeza ni un backtest como garantía de resultados futuros.
- El uso de datos, noticias, servicios de terceros y datos personales debe respetar sus licencias, condiciones y obligaciones aplicables.
- No se afirmará que la rama principal está protegida hasta comprobar la configuración efectiva de GitHub.

## 4. Principios de ingeniería

1. **Evidencia antes que afirmaciones:** toda conclusión importante identifica fuente, instante de captura, cobertura, método y limitaciones.
2. **Trazabilidad bidireccional:** objetivos ↔ requisitos ↔ riesgos ↔ decisiones ↔ componentes ↔ pruebas ↔ releases.
3. **Reproducibilidad:** fijar versiones, parámetros, periodos, datos de entrada o sus referencias, zona horaria y semilla aleatoria cuando proceda.
4. **Calidad medible:** convertir atributos como exactitud, rendimiento, seguridad, disponibilidad, mantenibilidad y usabilidad en criterios verificables.
5. **Seguridad y privacidad desde el diseño:** minimizar datos y privilegios; proteger secretos; registrar acciones relevantes sin exponer credenciales.
6. **Iteración controlada:** entregar incrementos pequeños, revisables y reversibles, con puertas de aceptación.
7. **Simplicidad evolutiva:** preferir la arquitectura más sencilla que cumpla los requisitos; separar módulos con contratos claros y no adoptar microservicios sin evidencia.
8. **Transparencia epistemológica:** distinguir observación, cálculo, inferencia, hipótesis y recomendación.
9. **Neutralidad tecnológica:** seleccionar soluciones mediante criterios ponderados, prototipos comparables y coste total.
10. **Autorización humana:** ninguna integración a `main` ni activación de trading real sin autorización explícita.

## 5. Modelo de gobierno y estados

Cada trabajo relevante debe tener un Issue antes de cambiar documentación o código. Los cambios se implementan en una rama y se proponen mediante Pull Request enlazado al Issue.

Estados de decisión:
- **Propuesta:** existe una opción formulada, sin evidencia suficiente.
- **Pendiente de aprobación:** existe análisis y evidencia inicial, pero falta decisión explícita.
- **Aprobada:** el responsable autorizado acepta la decisión y sus consecuencias.
- **Implementada:** el cambio está en una rama o versión identificada.
- **Verificada:** se ejecutaron los controles definidos y se conservaron sus resultados.
- **Retirada:** una decisión anterior dejó de aplicarse; debe conservarse su historial y motivo.

Estados de requisito: borrador, en revisión, aprobado, implementado, verificado, bloqueado, sustituido. No se debe marcar un requisito como verificado solo porque el código compila.

### Flujo de cambio obligatorio

1. Crear o actualizar un Issue con objetivo, problema, alternativas, riesgos y criterios de aceptación.
2. Analizar requisitos, impactos, dependencias y aplicabilidad normativa.
3. Registrar decisiones técnicas relevantes como ADR (Architecture Decision Record) cuando corresponda.
4. Crear rama con nombre descriptivo y referencia al Issue.
5. Implementar el cambio mínimo suficiente y añadir pruebas/evidencias.
6. Abrir PR en borrador si la solución aún necesita madurar; enlazar el Issue y describir pruebas ejecutadas y no ejecutadas.
7. Revisar diff, criterios, seguridad, regresiones, documentación y resultados reproducibles.
8. Integrar solo tras revisión y autorización explícita del propietario del proyecto.
9. Registrar versión, cambios, limitaciones conocidas y plan de reversión cuando proceda.

La documentación de gobernanza propuesta en PR #2 no se considera integrada ni activa en `main` mientras ese PR permanezca sin integrar.

## 6. Ciclo de vida y puertas de decisión

El ciclo es iterativo e incremental; las fases no obligan a una cascada rígida. Una iteración puede volver a una fase anterior si aparece nueva evidencia.

| Fase | Trabajo principal | Entregables mínimos | Puerta de salida |
|---|---|---|---|
| G0. Gobierno y alcance | Propósito, límites, roles, repositorio y control de cambios | Marco maestro, mapa de Issues, registro de decisiones | Alcance y reglas revisados; pendientes identificados |
| G1. Requisitos y riesgos | Necesidades, casos de uso, NFR, riesgos, obligaciones | Catálogo de requisitos, matriz de riesgos, criterios medibles | Requisitos críticos con propietario y aceptación definida |
| G2. Arquitectura y selección | Opciones, atributos de calidad, ADR, prototipos | Vistas de arquitectura, comparativas, resultados de PoC | Decisiones justificadas y aprobadas; riesgos críticos tratados |
| G3. Plataforma de datos | Ingesta, normalización, procedencia, frescura y calidad | Contratos de datos, catálogo de fuentes, pruebas de calidad | Datos trazables, errores y datos ausentes detectables |
| G4. Motor de investigación | Universo spot, análisis, eventos, cálculo cuantitativo | Métodos versionados, informes, pruebas y datasets de validación | Resultados reproducibles y limitaciones expuestas |
| G5. Clientes multiplataforma | Flujos de investigación web y móvil; escritorio solo si se justifica | Prototipos, pruebas de usabilidad/accesibilidad, contratos API | Flujos principales validados en dispositivos objetivo |
| G6. Verificación integral | Seguridad, rendimiento, recuperación, calidad y regresión | Informes de prueba, defectos, evidencias y riesgos residuales | Umbrales aprobados alcanzados o excepciones autorizadas |
| G7. Operación controlada | Despliegue, observabilidad, soporte, costes y recuperación | Runbooks, alertas, backups/restore probados, plan de rollback | Preparación operativa demostrada y aprobación de release |
| G8. Evolución | Métricas reales, incidentes, feedback y cambios de mercado | Revisiones, nuevas Issues, planes de mejora | Priorización y aprendizaje documentados |

Cada puerta requiere una decisión explícita: aceptar, rechazar o devolver con acciones. Las excepciones deben tener responsable, justificación, riesgo residual, vencimiento y mecanismo de seguimiento.

## 7. Arquitectura lógica inicial — no aprobada

Se propone evaluar, sin prejuzgar el stack:

- **Clientes:** web, Android, iOS y, si se justifica, escritorio.
- **API central versionada:** autenticación/autorización, contratos y límites de uso.
- **Módulos de dominio:** universo de mercado, investigaciones, informes, fuentes/eventos, usuarios y auditoría.
- **Servicios de datos:** adaptadores de proveedores, normalización, calidad, procedencia, almacenamiento y caché.
- **Motor de análisis:** cálculos deterministas, validación estadística y experimentos reproducibles.
- **Operación transversal:** configuración, secretos, observabilidad, seguridad, CI, despliegue y recuperación.

La arquitectura inicial podrá ser un monolito modular si satisface los atributos de calidad. La división en servicios se decide con métricas de carga, aislamiento, despliegue, fiabilidad y coste, no por preferencia estética.

## 8. Datos de mercado y validez cuantitativa

Cada observación relevante debe conservar, cuando el proveedor lo permita: proveedor, instrumento/mercado, símbolo original y normalizado, tipo de mercado, timestamp del evento, timestamp de recepción, zona horaria, unidad, periodo, método de extracción, versión del adaptador y estado de calidad.

Controles mínimos a diseñar y probar:
- frescura y retraso de actualización;
- cobertura temporal y huecos;
- duplicados, orden temporal y valores imposibles;
- consistencia de símbolo, cotización y mercado spot;
- precisión decimal, unidades y conversión;
- disponibilidad del par en el exchange objetivo;
- volumen real frente a métricas derivadas y riesgo de datos inflados;
- spread, profundidad, deslizamiento estimado y comisiones cuando se evalúe liquidez;
- tratamiento explícito de datos ausentes y fallos del proveedor.

Las estrategias se validarán contra una línea base, incluyendo comisiones, spread, deslizamiento, sesgo de supervivencia, look-ahead bias, selección retrospectiva, particiones temporales y pruebas fuera de muestra. Los resultados deben incluir incertidumbre y escenarios adversos; un backtest positivo no demuestra rentabilidad futura.

## 9. Seguridad, privacidad y operación

La especificación de seguridad deberá identificar activos, amenazas, límites de confianza, datos sensibles, permisos y riesgos de terceros. Como mínimo, se evaluarán autenticación, autorización, gestión de secretos, dependencias vulnerables, cifrado en tránsito, registros sin secretos, limitación de solicitudes, protección de API, retención de datos, copias de seguridad y restauración.

No se aceptará una promesa de alta disponibilidad basada solo en un plan gratuito. Cada proveedor de hosting se evaluará por límites, suspensión, almacenamiento, transferencia, costes al escalar, región, seguridad, backups, observabilidad, portabilidad y estrategia de salida.

## 10. Selección tecnológica

No se aprueba aún ninguna tecnología. La comparación debe incluir al menos:
- ajuste a requisitos funcionales y atributos de calidad;
- rendimiento medido con carga representativa;
- facilidad de desarrollo y pruebas desde los dispositivos disponibles;
- madurez, mantenimiento, seguridad y ecosistema;
- compatibilidad con web, Android e iOS;
- coste total, límites de planes gratuitos y coste de salida;
- portabilidad, lock-in y disponibilidad de personal;
- resultados de PoC reproducibles y limitaciones.

Las puntuaciones, pesos y umbrales se acuerdan antes de ejecutar las comparativas para reducir el sesgo de confirmación. Una prueba no ejecutada se marca como pendiente; no se inventan resultados.

## 11. Referencias normativas preliminares

La matriz detallada se mantiene en [matriz de aplicabilidad normativa](matriz-normativa.md). Las fichas oficiales consultadas a 2026-10-19 incluyen:
- ISO/IEC/IEEE 12207:2026: marco de procesos del ciclo de vida del software. [Ficha oficial](https://www.iso.org/standard/90219.html).
- ISO/IEC 25010:2023: modelo de calidad de producto. [Ficha oficial](https://www.iso.org/standard/78176.html).
- ISO/IEC 27001:2022 y Enmienda 1:2024: requisitos del sistema de gestión de seguridad de la información. [Ficha oficial de la norma](https://committee.iso.org/standard/27001) y [enmienda](https://www.iso.org/standard/88435.html).
- ISO 31000:2018: directrices de gestión de riesgos; la ficha oficial indica que sigue vigente y está destinada a revisión. No es una norma certificable. [Ficha oficial](https://www.iso.org/standard/31000).

Las referencias de sistemas, arquitectura, experiencia de usuario, accesibilidad e IA quedan sujetas a verificación adicional de edición, estado y aplicabilidad antes de ser incluidas como base normativa aprobada.

## 12. Criterios de calidad del propio marco

El marco no estará listo para aprobar hasta que:
- los documentos estén vinculados a Issues y no contradigan decisiones existentes;
- las decisiones propuestas estén diferenciadas de las aprobadas;
- cada fase tenga entregables, criterios de salida, riesgos y evidencias;
- los requisitos tengan IDs únicos y criterios verificables;
- la matriz normativa incluya fuente oficial, estado de verificación y artefactos asociados;
- se defina cómo conservar y reproducir evidencias;
- se revisen consistencia, enlaces internos, ortografía y alcance;
- se enumeren explícitamente las cuestiones que siguen pendientes de decisión.

## 13. Registro inicial de decisiones pendientes

| ID | Decisión | Estado | Evidencia necesaria |
|---|---|---|---|
| DEC-001 | Stack de backend y motor analítico | Pendiente | Requisitos, comparativa y PoC |
| DEC-002 | Framework de cliente web | Pendiente | Flujos, accesibilidad, rendimiento y PoC |
| DEC-003 | Tecnología móvil para Android/iOS | Pendiente | Prototipo en dispositivos y coste de mantenimiento |
| DEC-004 | Base de datos y estrategia de persistencia | Pendiente | Modelo de datos, integridad, carga y recuperación |
| DEC-005 | Proveedores de datos de mercado/noticias | Pendiente | Cobertura, licencias, calidad, coste y disponibilidad geográfica |
| DEC-006 | Hosting y despliegue | Pendiente | PoC, límites, coste total, seguridad, backup/restore y portabilidad |
| DEC-007 | Uso de IA/ML | Pendiente | Comparación con línea base y métrica de valor incremental |
| DEC-008 | Aplicabilidad formal de cada norma | Pendiente | Revisión de alcance, requisitos y coste de mantenimiento |
| DEC-009 | Incorporación de trading real | Fuera de alcance; requiere decisión explícita | Análisis separado legal, operativo, de seguridad y de riesgo |

## 14. Mantenimiento del marco

Cada modificación se propone mediante Issue y PR. La revisión del marco se activa cuando cambien el alcance, los riesgos críticos, el modelo de datos, la arquitectura, una obligación aplicable, la fuente normativa o los objetivos de calidad. Las decisiones retiradas no se borran: se conserva su historial y se enlaza la sustitución.

## 15. Descargo de alcance

Este marco es una propuesta de ingeniería y calidad de producto. No constituye asesoramiento financiero, promesa de resultados, certificación ISO, auditoría independiente ni confirmación de que los controles descritos ya estén implementados.
