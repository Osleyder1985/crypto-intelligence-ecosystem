# Plan Maestro Top Mundial del Crypto Intelligence Ecosystem

- **Estado:** propuesta para revisión; no aprobado hasta decisión explícita del propietario.
- **Versión del documento:** 1.0.0
- **Idioma:** español; nombres de archivos, directorios, código e identificadores técnicos en inglés.
- **Issue rector:** [#11 — Definir el marco maestro de ingeniería, gobernanza y hoja de ruta](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11).
- **Auditoría de referencia:** [#270 — Auditoría integral de documentación, código, arquitectura y ciclo de vida](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/270).
- **Alcance:** producto de inteligencia e investigación cripto; el MVP es de investigación y no ejecuta órdenes reales.
- **Principio de honestidad:** este plan define objetivos y evidencia requerida. No afirma que las capacidades estén implementadas, que exista conformidad ISO, que se haya probado rentabilidad ni que el producto sea actualmente Top Mundial.

## 1. Visión y resultado esperado

Construir un ecosistema de investigación de criptoactivos que permita al usuario seleccionar un activo y obtener una evaluación reproducible, explicable y actualizable a corto, medio y largo plazo. La evaluación debe integrar datos de mercado, episodios alcistas y bajistas, noticias y eventos autorizados, soportes y resistencias, libro de órdenes y liquidez, evidencia fundamental/on-chain disponible, riesgos, escenarios y niveles de interés para investigación spot.

El producto debe guardar las evaluaciones históricas, comparar sus cambios, explicar qué evidencia cambió y clasificar los activos mediante una metodología publicada. Todas las interfaces autorizadas deben consumir los mismos contratos y datos centrales, evitando cálculos contradictorios entre plataformas.

“Top Mundial” es una aspiración que solo podrá declararse con benchmarks reproducibles frente a alternativas pertinentes, resultados observables, limitaciones transparentes y evaluación externa apropiada. No es un estado que se obtiene por adoptar una arquitectura, una norma o una tecnología específica.

## 2. Objetivos de producto

1. **Integridad de datos:** procedencia, integridad, temporalidad, frescura, cobertura, calidad y limitaciones explícitas.
2. **Análisis de movimientos:** detectar y reconstruir episodios alcistas, bajistas y laterales, sus límites y la evidencia asociada.
3. **Investigación de catalizadores:** relacionar noticias/eventos con episodios sin confundir correlación temporal con causalidad demostrada.
4. **Análisis técnico:** identificar zonas de soporte/resistencia por temporalidad, con método, vigencia, confluencia e invalidación.
5. **Microestructura:** examinar spread, profundidad visible, desequilibrio, concentración de órdenes y coste/deslizamiento estimado con limitaciones.
6. **Evaluación por horizonte:** producir escenarios y riesgos diferenciados para corto, medio y largo plazo, sin promesas de rentabilidad.
7. **Memoria de investigación:** almacenar versiones inmutables de evaluaciones, datos y metodología para comparaciones reproducibles.
8. **Ranking:** comparar activos con criterios explícitos, fecha de corte, cobertura, incertidumbre y explicación de posiciones.
9. **Producto integrado:** experiencia consistente en web, escritorio, Android e iOS; orden de implementación sujeto a requisitos, viabilidad y decisiones aprobadas.
10. **Confianza y gobernanza:** seguridad, control de fuentes, auditabilidad, pruebas, gestión de riesgos, operación recuperable y cambios controlados.

## 3. Alcance y exclusiones

### Incluido

- Investigación spot como caso inicial.
- Precios, OHLCV, mercados y profundidad según cobertura real del proveedor.
- Noticias y eventos solo desde fuentes con autorización y condiciones de uso revisadas.
- Datos fundamentales/on-chain cuando exista fuente adecuada, autorización y evidencia de calidad.
- Análisis estadístico y modelos predictivos solo si aportan valor demostrado frente a métodos de referencia.
- Reportes, evaluación histórica, comparación y ranking.
- API y almacenamiento compartidos; clientes multiplataforma por fases.
- Observabilidad, seguridad, auditoría, documentación, CI/CD y recuperación.

### Excluido hasta aprobación expresa

- Envío o ejecución de órdenes reales, custodia de fondos y acceso a claves privadas.
- Afirmaciones de causalidad cuando solo exista asociación temporal.
- Garantías de rentabilidad, precisión o éxito de señales.
- Activación de proveedores con términos, permisos o condiciones no verificados.
- Incorporación de una tecnología (por ejemplo, microservicios, Kubernetes, blockchain o ML complejo) sin requisito, análisis comparativo y decisión aprobada.
- Declarar certificación o conformidad ISO sin el proceso de evaluación y evidencia que corresponda.

## 4. Principios no negociables

1. **Evidencia antes que afirmaciones:** cada conclusión relevante debe señalar datos, fuentes, fecha de corte, método, incertidumbre y limitaciones.
2. **Fail closed:** si faltan permisos, datos esenciales, integridad o coordinación segura, bloquear la captura o conclusión afectada y registrar claramente el motivo.
3. **Sin límites arbitrarios de captura:** no truncar respuestas por un límite local arbitrario. Aplicar límites técnicos justificados, paginación, streaming, almacenamiento incremental y manejo documentado de cuotas; respetar límites reales del proveedor y capacidad operativa.
4. **Reproducibilidad:** conservar las versiones de datos, código, configuración y metodología necesarias para reconstruir una evaluación, dentro de las condiciones de retención y licencias.
5. **Temporalidad correcta:** timestamps normalizados y originales cuando proceda, zonas horarias explícitas, orden de eventos, controles anti-leakage y no-look-ahead.
6. **No confundir niveles con órdenes ejecutables:** el libro visible es una fotografía parcial y cambiante; los niveles analíticos no son instrucciones de inversión ni garantizan ejecución.
7. **Autorización humana:** el propietario aprueba decisiones de producto, habilitación de fuentes sensibles, cambios de riesgo y cualquier ampliación a operaciones reales.
8. **Cambios auditables:** cada problema accionable tiene Issue; cada solución técnica/documental se propone en un PR vinculado; no crear duplicados.
9. **Protección de main:** no integrar cambios sin checks requeridos satisfactorios, revisión disponible y autorización explícita del propietario. Una revisión de IA no se presenta como revisión independiente.
10. **Transparencia normativa:** distinguir norma publicada, borrador en desarrollo, guía, alineación interna, evaluación de conformidad y certificación.

## 5. Arquitectura objetivo, pendiente de ADR

La arquitectura se diseña a partir de requisitos y pruebas de concepto; los elementos siguientes son capacidades lógicas deseadas, no una decisión anticipada sobre lenguaje, framework, base de datos o topología.

- **Clientes:** web, escritorio, Android e iOS.
- **API de producto:** identidad/autorización, selección de activos, ejecución de evaluaciones, consulta de resultados e historial.
- **Orquestación de investigación:** planifica tareas, registra estados, cancelación, reintentos y fallos.
- **Adaptadores de proveedores:** conectores aislados para precios, OHLCV, libro de órdenes, noticias, macro, derivados y datos fundamentales/on-chain, cada uno con estado de autorización y capacidades declaradas.
- **Capa de datos:** datos brutos o evidencia conservada conforme a licencias; datos normalizados; catálogo de procedencia y calidad; resultados derivados versionados.
- **Motores analíticos:** episodios, soportes/resistencias, microestructura, eventos/catalizadores, análisis por horizonte y ranking.
- **Registro de evaluaciones:** entradas, versiones de método/modelo, resultados, incertidumbre, riesgos y comparaciones.
- **Gobernanza y observabilidad:** auditoría, métricas, trazas, logs, control de permisos, inventario de dependencias y estado de proveedores.

### Decisiones de arquitectura obligatorias (ADR)

Antes de fijar el stack se deben comparar opciones según requisitos medibles: compatibilidad con Windows y dispositivos móviles, coste total, operación desde Cuba/España según disponibilidad de servicios, rendimiento en el hardware objetivo, mantenibilidad por un propietario con asistencia de IA, seguridad, portabilidad, licencias, disponibilidad de herramientas y facilidad de prueba/recuperación. Cada ADR registra opciones, criterios, evidencia, consecuencias, decisión, fecha y autoridad aprobadora.

## 6. Modelo de datos y contrato de una evaluación

Toda evaluación versionada debería registrar, cuando aplique:

- identificador único, activo, mercado/par, proveedor y fecha/hora de solicitud;
- instante de corte de datos, intervalos cubiertos, cobertura faltante y frescura;
- identificadores o hashes de fuentes/artefactos, licencia/permiso y procedencia;
- versión de código, configuración, método y modelo;
- episodios alcistas/bajistas/laterales y pivotes usados;
- eventos relacionados con enlaces a evidencia, tiempo de publicación/hecho, relevancia, confianza y clasificación explícita de asociación versus causalidad;
- zonas técnicas con temporalidad, método, confluencia, edad, invalidación y datos que las respaldan;
- libro de órdenes: instante, spread, profundidad observada, rango cubierto, desequilibrio y estimación de coste/deslizamiento con supuestos;
- factores fundamentales/on-chain disponibles y sus limitaciones;
- escenarios por horizonte, evidencia favorable/contraria, riesgos, incertidumbre y condiciones de invalidación;
- estado de calidad: válido, parcial, obsoleto, bloqueado o fallido, con razón;
- resultados históricos y posteriores cuando estén disponibles, sin sobrescribir la evaluación original.

Los campos definitivos se establecerán mediante contratos versionados y ADR; no se considerará que esta lista ya esté implementada.

## 7. Hoja de ruta por fases y puertas de salida

Las fases se cierran por evidencia y dependencias, no por fechas arbitrarias. Se permite trabajar en paralelo únicamente cuando no se comprometa la línea base ni se creen cambios duplicados.

### Fase 0 — Gobernanza, línea base y definición de éxito

**Objetivo:** convertir el estado actual en una línea base verificable y una única hoja de ruta gobernada.

Entregables:
- inventario completo del repositorio, archivos, módulos, tests, workflows, dependencias y documentos;
- auditoría con hallazgos confirmados, sospechas y aspectos no verificables claramente separados;
- catálogo de requisitos funcionales/no funcionales con identificadores y criterios de aceptación;
- matriz de aplicabilidad normativa con edición/estado verificados en fuente oficial;
- mapa de Issues existentes, dependencias y duplicados;
- métricas base de calidad, pruebas y producto, sin inventar valores.

Puerta de salida:
- línea base de commit registrada;
- cada área y requisito tiene estado y evidencia;
- prioridades y dependencias aceptadas por el propietario;
- ninguna supuesta capacidad se presenta como completa sin pruebas.

### Fase 1 — Contratos, arquitectura y decisiones técnicas

**Objetivo:** definir límites y contratos que permitan integrar módulos sin acoplamiento accidental.

Entregables:
- diagramas de contexto, contenedores/componentes y flujos de datos;
- ADR comparativos para stack, persistencia, API, autenticación, ejecución de trabajos, clientes y despliegue;
- contratos versionados de activos, observaciones, episodios, zonas, eventos, libro de órdenes y evaluaciones;
- modelo de amenazas y registro de riesgos;
- estrategia de migración, compatibilidad, errores, idempotencia y versionado.

Puerta de salida:
- ADR críticos aprobados;
- contratos con pruebas de esquema y ejemplos válidos/invalidos;
- riesgos arquitectónicos de mayor impacto mitigados o aceptados formalmente.

### Fase 2 — Ingesta de datos confiable

**Objetivo:** obtener datos con procedencia y cobertura conocidas.

Entregables:
- matriz de proveedores, mercados, endpoints, términos, permisos, cuotas y cobertura;
- adaptadores aislados con paginación/streaming donde corresponda, reintentos limitados, timeouts justificados y rate limiting coordinado;
- preservación de respuestas completas dentro de las condiciones del proveedor, checksums cuando sean útiles, normalización y validación;
- detección de huecos, duplicados, timestamps incorrectos, datos futuros y divergencias;
- pruebas con fixtures deterministas y pruebas de integración solo cuando estén autorizadas.

Puerta de salida:
- cada fuente activa tiene permiso y alcance registrados;
- pruebas cubren fallos, respuestas parciales, cuotas, datos inválidos y recuperación;
- se informa cobertura real; los datos ausentes nunca se inventan.

### Fase 3 — Persistencia e historial reproducible

**Objetivo:** mantener el linaje entre observaciones, métodos y evaluaciones.

Entregables:
- persistencia de observaciones normalizadas, artefactos y evaluaciones versionadas;
- migraciones, políticas de retención/borrado compatibles con licencias y obligaciones aplicables;
- recuperación tras fallo, backup y restauración probada;
- consulta de historial y comparación entre evaluaciones;
- manifiesto de reproducibilidad por ejecución.

Puerta de salida:
- una evaluación histórica puede reconstruirse hasta donde permitan los datos/licencias conservados;
- cambios de esquema y metodología quedan versionados;
- restauración demostrada en entorno de prueba.

### Fase 4 — Núcleo de análisis de mercado

**Objetivo:** consolidar análisis técnico y microestructura como evidencia verificable.

Entregables:
- episodios de tendencia y movimientos laterales por temporalidad;
- soportes/resistencias con método, confluencia, vigencia e invalidación;
- análisis del libro visible, profundidad, spread, desequilibrio y coste estimado;
- pruebas de invariantes, casos límite, datos faltantes y cambios de régimen;
- informes que distingan observación, cálculo, hipótesis y conclusión.

Puerta de salida:
- resultados reproducibles con fixtures y datasets identificados;
- pruebas anti-look-ahead y de temporalidad satisfactorias;
- limitaciones de la instantánea del libro y de los niveles declaradas explícitamente.

### Fase 5 — Eventos, noticias y explicación de movimientos

**Objetivo:** investigar posibles catalizadores del inicio y fin de movimientos.

Entregables:
- fuentes autorizadas con reglas de captura, archivo y atribución;
- normalización de noticias/eventos, deduplicación, publicación vs. hora del hecho y entidades afectadas;
- enlace auditable entre eventos y episodios, con ventanas y método documentados;
- clasificación entre asociación temporal, evidencia corroborante, hipótesis y causalidad demostrada;
- cobertura de eventos ausentes y razones de incertidumbre.

Puerta de salida:
- un analista puede seguir desde cada afirmación hasta las fuentes;
- pruebas cubren eventos tardíos, duplicados, zonas horarias, fuentes contradictorias y ausencia de evidencia;
- no se declara causalidad solo por proximidad temporal.

### Fase 6 — Evaluación por horizontes y ranking

**Objetivo:** comparar escenarios a corto, medio y largo plazo con incertidumbre y validación.

Entregables:
- definición explícita de cada horizonte y de las etiquetas/objetivos evaluados;
- baselines simples antes de modelos complejos;
- protocolo de backtesting y walk-forward que evite leakage, sesgo de supervivencia y selección retrospectiva;
- costes, spreads, deslizamiento, comisiones y supuestos incorporados cuando corresponda;
- calibración de probabilidades si se publican probabilidades; intervalos/uncertidumbre cuando sean defendibles;
- evaluación posterior prospectiva, registro de errores y degradación;
- ranking versionado con criterios, cobertura, fecha de corte y sensibilidad a datos faltantes.

Puerta de salida:
- rendimiento y limitaciones comparados con baselines en muestras no utilizadas para desarrollo;
- ningún resultado se presenta como garantía;
- metodología, datasets, costes y criterios de exclusión están documentados;
- el ranking puede explicarse y reproducirse.

### Fase 7 — API y experiencia multiplataforma

**Objetivo:** hacer accesible la misma inteligencia mediante interfaces coherentes.

Entregables:
- API documentada con autenticación, autorización, validación, límites y versionado;
- interfaz de investigación con selección de activo, temporalidad, fuentes, episodios, zonas, liquidez, eventos, escenarios e historial;
- clientes web, escritorio, Android e iOS implementados en el orden aprobado según viabilidad;
- accesibilidad, localización, estados vacíos, fallos de red y visualización de incertidumbre;
- pruebas de contrato, integración y E2E sobre flujos reales.

Puerta de salida:
- todas las plataformas consultan la misma fuente de verdad;
- los flujos prioritarios pasan pruebas E2E;
- la UI nunca oculta datos obsoletos, parciales o bloqueados;
- la experiencia se evalúa con usuarios y problemas observados registrados.

### Fase 8 — Seguridad, operación y preparación para producción

**Objetivo:** demostrar operación mantenible y recuperable.

Entregables:
- modelo de amenazas actualizado, permisos mínimos, gestión de secretos y controles de acceso;
- inventario de dependencias/SBOM, escaneo de vulnerabilidades y licencias;
- CI/CD con pruebas relevantes, artefactos trazables y control de cambios;
- métricas, logs estructurados, alertas, runbooks, backups, restauración y rollback;
- gestión de incidentes, retención, privacidad y respuesta ante fallo de proveedor;
- pruebas de rendimiento basadas en cargas y objetivos justificados.

Puerta de salida:
- se demuestra despliegue y rollback en entorno no productivo;
- restauración, alertas y procedimientos de incidentes se ensayan;
- defectos críticos de seguridad o integridad bloquean release;
- los objetivos de servicio son acordados y medidos, no inventados.

### Fase 9 — Validación competitiva y mejora continua

**Objetivo:** demostrar fortalezas relativas y evitar proclamar superioridad sin datos.

Entregables:
- selección documentada de plataformas y métodos de referencia pertinentes;
- benchmark repetible con datasets, fechas, metodología y limitaciones publicados;
- comparación de cobertura, calidad, latencia, explicabilidad, experiencia, reproducibilidad y coste;
- revisión de resultados con evaluador externo competente cuando sea viable;
- ciclo de retroalimentación de errores, incidentes, cambios de mercado y versiones de modelos.

Puerta de salida:
- ventajas competitivas concretas respaldadas por evidencia;
- resultados negativos y limitaciones reportados;
- declaración “Top Mundial” solo si se define un ámbito comparativo, se aportan pruebas reproducibles y se evita una afirmación universal no demostrable.

## 8. Calidad, verificación y criterios de puntuación

Cada área se evalúa mediante una rúbrica común de 0 a 10, con evidencias adjuntas. La rúbrica se formalizará y aprobará antes de usar puntuaciones para decisiones de release.

- **0–2:** ausente o solo idea sin evidencia.
- **3–4:** prototipo parcial; integración o verificación insuficiente.
- **5–6:** funcionalidad sustancial, pero con brechas conocidas o validación incompleta.
- **7–8:** integrada y probada en escenarios relevantes; riesgos residuales controlados y documentados.
- **9:** robusta, reproducible y con evidencia operacional amplia; quedan mejoras menores no críticas.
- **10:** todos los criterios aprobados, evidencia completa y vigente, sin defectos críticos conocidos, pruebas repetibles y validación independiente cuando el criterio requiera independencia.

Estas bandas son una propuesta de gobernanza, no una escala ISO. Un 10/10 no significa ausencia metafísica de defectos: significa que se cumplieron los criterios previamente definidos y que los límites residuales son conocidos y aceptados. Si falta evidencia, la puntuación debe ser “no demostrada” o provisional, no 10.

## 9. Indicadores que deben medirse

Los objetivos numéricos se fijan después de levantar una línea base y justificar el nivel requerido.

- **Datos:** cobertura por activo/mercado/temporalidad, frescura, porcentaje de registros rechazados, huecos, duplicados y fallos de captura.
- **Eventos:** porcentaje de episodios con evidencia autorizada disponible, duplicados, conflictos de fuente y afirmaciones no verificables.
- **Análisis:** reproducibilidad, estabilidad de zonas, errores por horizonte, desempeño frente a baselines y sensibilidad a costes.
- **Predicción:** métricas adecuadas al objetivo, calibración cuando aplique, resultados fuera de muestra y seguimiento prospectivo.
- **Producto:** tasa de éxito de flujos E2E, errores visibles, accesibilidad evaluada, latencia medida y satisfacción/usabilidad observada.
- **Ingeniería:** defectos por severidad, regresiones, resultados CI, cobertura de requisitos críticos, deuda técnica y antigüedad de hallazgos.
- **Operación/seguridad:** incidentes, tiempo de detección/recuperación medido, restauraciones probadas, vulnerabilidades y dependencias no resueltas.
- **Competitividad:** diferencias reproducibles frente a referencias, coste por análisis y calidad comparativa.

No usar cobertura de líneas como sustituto de cobertura de requisitos, ni una única métrica predictiva como prueba de valor financiero.

## 10. Verificación mínima por cambio

Cada PR debe incluir según corresponda:

1. Issue de origen y descripción del problema, causa y solución.
2. Alcance exacto, archivos afectados y consecuencias.
3. Requisitos/contratos que cambian y compatibilidad.
4. Pruebas añadidas o actualizadas y comandos realmente ejecutados.
5. Evidencia de CI del commit revisado; no reutilizar resultados de otra revisión/commit.
6. Riesgos, permisos de proveedor y datos sintéticos vs. reales claramente distinguidos.
7. Documentación, changelog/índice y trazabilidad actualizados.
8. Plan de rollback o mitigación para cambios operativos.
9. Revisión crítica que no se presente como independiente si la realizó la misma IA que preparó el cambio.
10. Autorización explícita antes de integrar a `main`.

## 11. Gobierno de Issues y Pull Requests

- Mantener un Issue rector por problema o requisito y enlazarlo desde los trabajos derivados.
- Antes de crear un Issue o PR, buscar duplicados y reutilizar el existente si cubre el mismo resultado.
- Títulos, descripciones, comentarios de revisión y documentación del proyecto en español, salvo términos técnicos necesarios.
- Nombres de código, archivos y directorios en inglés.
- Issues describen situación/problema, causa, solución propuesta, dependencias y criterios de aceptación.
- PRs explican qué cambia, por qué es la mejor solución evaluada, pruebas, riesgos y evidencia.
- Mantener cambios pequeños y coherentes; no mezclar rediseños no relacionados.
- No cerrar un Issue por escribir documentación: cerrarlo cuando su criterio de aceptación esté verificado.
- No fusionar por el mero hecho de que el PR sea mergeable; comprobar checks, revisión, autorización y riesgos.

## 12. Gobernanza normativa

La selección de normas se mantiene en una matriz viva, verificada en fuentes oficiales en el momento de cada revisión. Como mínimo, evaluar aplicabilidad de:
- ISO/IEC/IEEE 12207 para procesos del ciclo de vida del software;
- ISO/IEC/IEEE 15288 si el alcance de ingeniería de sistemas lo requiere;
- ISO/IEC/IEEE 42010 para descripción arquitectónica;
- ISO/IEC 25010 para calidad del producto;
- ISO/IEC 27001 y controles pertinentes para gestión de seguridad;
- ISO 31000 para gestión de riesgos;
- ISO 9241-210 y requisitos aplicables de accesibilidad/usabilidad;
- ISO/IEC 42001 e ISO/IEC 23894 si el uso y gobernanza de IA justifican su aplicabilidad;
- normas de documentación, prueba, seguridad, privacidad y calidad adicionales solo tras verificar su estado, alcance y pertinencia.

Registrar referencia, edición, estado oficial, propósito, decisión de aplicabilidad, requisitos/controles derivados, artefactos, pruebas, responsable y fecha de revisión. No inventar cláusulas, no tratar borradores como normas publicadas y no declarar certificación por el mero uso de una matriz.

## 13. Riesgos principales y respuesta

| Riesgo | Respuesta obligatoria |
|---|---|
| Datos incompletos o proveedor bloqueado | Estado parcial/bloqueado visible, fuentes alternativas solo tras evaluación y autorización, sin rellenar datos inventados. |
| Noticias interpretadas como causa | Clasificación explícita de evidencia y lenguaje calibrado; causalidad requiere metodología y evidencia adicional. |
| Sobreajuste o leakage | Baselines, particiones temporales, walk-forward, muestras no usadas y revisión de sesgos. |
| Liquidez efímera o libro parcial | Marcar instantánea, cobertura y límites; no asumir que órdenes visibles permanecerán o ejecutarán. |
| Dependencia de un solo proveedor | Diseñar adaptadores y evaluar alternativas por cobertura, licencia, calidad, coste y disponibilidad. |
| Alcance demasiado grande para un propietario | Entregas pequeñas, automatización, priorización por riesgo y decisiones explícitas de aplazamiento. |
| Arquitectura sobredimensionada | ADR y pruebas de concepto; adoptar la solución más simple que satisfaga requisitos demostrados. |
| Vulnerabilidades/licencias | SBOM, revisión de dependencias, escaneo, actualización controlada y evidencia de autorización. |
| Fallo de almacenamiento o pérdida histórica | Backups, restauración ensayada, integridad y política de retención documentada. |
| Reivindicaciones de “Top Mundial” sin sustento | Benchmark repetible, límites declarados y revisión independiente cuando corresponda. |

## 14. Registro de decisiones pendientes

No se consideran aprobadas hasta registrar ADR o aprobación explícita:

- stack definitivo de API, backend y clientes;
- tecnología de persistencia y estrategia de datos históricos;
- hosting, despliegue, identidad y operación;
- proveedores y fuentes autorizadas por clase de datos;
- definición operativa de corto/medio/largo plazo;
- metodología y métricas del ranking;
- umbrales de calidad, rendimiento, disponibilidad y frescura;
- orden definitivo de clientes web, escritorio, Android e iOS;
- alcance de cualquier evaluación/certificación externa;
- eventual habilitación de operaciones reales (fuera del MVP actual).

## 15. Próximos pasos concretos

1. Vincular este plan con el Issue #11 y el informe de auditoría #270; resolver cualquier contradicción con documentos maestros existentes antes de declarar este documento rector.
2. Completar la auditoría real del árbol completo y actualizar la línea base de cada hallazgo.
3. Mapear las fases y entregables a Issues existentes; no crear Issues duplicados.
4. Confirmar dependencias y orden de trabajo con el propietario, comenzando por las brechas que bloquean la integración E2E, la integridad de datos y la verificación.
5. Elaborar ADRs solo cuando la evidencia disponible permita comparar opciones.
6. Entregar cada remediación mediante PR pequeño, con pruebas y criterios de aceptación verificables.
7. Revisar el plan tras cada puerta de fase y al cambiar requisitos, proveedores, normas o riesgos.

## 16. Condiciones para declarar el plan completado

El plan se considera implantado —no simplemente escrito— cuando:
- todos los requisitos aprobados están trazados a implementación, pruebas y evidencia;
- las fases aplicables han superado sus puertas de salida;
- la ruta E2E prioritaria funciona y sus fallos son observables y recuperables;
- las evaluaciones e historiales son reproducibles con las limitaciones documentadas;
- la seguridad, las licencias, la operación y la gobernanza tienen evidencia actualizada;
- las aplicaciones comprometidas consumen contratos y datos compartidos;
- las métricas se reportan junto con metodología y limitaciones;
- la comparación competitiva respalda las ventajas que se afirmen;
- el propietario aprueba el estado y las limitaciones residuales;
- cualquier afirmación de conformidad o evaluación independiente dispone de evidencia apropiada.

**Estado de salida actual:** propuesta de plan para revisión. La aprobación de este documento no cierra brechas técnicas ni autoriza por sí sola cambios de arquitectura, activación de proveedores, despliegue o ejecución de órdenes.


## 17. Reconciliación obligatoria con el catálogo de requisitos existente

La inspección del repositorio `main` encontró un catálogo preexistente en [`docs/engineering/requirements-traceability-catalog.md`](../../docs/engineering/requirements-traceability-catalog.md). Por tanto, **no se debe crear un segundo catálogo paralelo ni reemplazar el existente sin reconciliación**.

### Evidencia documental observada

- El catálogo existente identifica 33 requisitos de producto (`REQ-P-001` a `REQ-P-033`).
- Identifica 18 atributos no funcionales (`NFR-001` a `NFR-018`), con métricas por concretar.
- Incluye un mapa de trazabilidad, reglas de abstención, priorización preliminar por fases y una revisión documental de cobertura de Issues.
- El propio documento se declara borrador y no línea base aprobada.
- La sección 15 registra brechas para los Issues #3–#11 y #13, además de #16–#22, entre ellas responsables aún no nominados, criterios cuantitativos pendientes, PoC/ADR no demostradas, contratos API por concretar y evidencia operativa pendiente.

La lectura del documento demuestra que ya existe un punto de partida sustancial; **no demuestra que los 33 requisitos estén completos, aprobados, implementados o verificados**. Los roles propuestos tampoco equivalen a responsables humanos nominados.

### Procedimiento de consolidación

1. Conservar los identificadores `REQ-P-*` y `NFR-*` cuando el significado sea equivalente; no reasignar IDs para ocultar duplicados.
2. Contrastar cada objetivo del Plan Maestro con los requisitos existentes y marcar la relación como cubierto, parcial, ausente, contradictorio o pendiente de evidencia.
3. Revisar los Issues y documentos maestros relacionados antes de proponer requisitos nuevos. Si ya existe un requisito equivalente, ampliar su criterio de aceptación o trazabilidad en vez de crear otro.
4. Separar requisitos de producto, calidad, seguridad, datos, operación, gobernanza, restricciones y decisiones pendientes.
5. Convertir los criterios vagos en escenarios verificables. Los umbrales numéricos se fijan únicamente con justificación, línea base, contexto de uso y aprobación; no se inventan.
6. Registrar propietario/rol de decisión y verificación. En un proyecto de propietario único asistido por IA, documentar el conflicto de funciones y no presentar la revisión de la misma IA como independiente.
7. Enlazar cada requisito con objetivo, Issue, riesgo, ADR, componente, prueba, ejecución CI y evidencia de release cuando aplique.
8. Mantener los estados separados: propuesto, aprobado, implementado, verificado, bloqueado, retirado. No inferir implementación a partir de documentación ni verificación a partir de la existencia de tests.
9. Documentar toda contradicción y resolverla mediante decisión trazable del propietario antes de fijar la línea base.
10. Publicar una matriz de brechas revisada en PR y solicitar aprobación explícita; no fusionar ni cerrar Issues por la mera creación del catálogo.

### Orden de trabajo para la siguiente iteración

1. **Primero:** revisar la matriz existente de Issues #3–#22 y sus dependencias para no duplicar trabajo; actualizar su estado solo con evidencia actual.
2. **Segundo:** contrastar los objetivos funcionales completos —episodios alcistas/bajistas y catalizadores, soportes/resistencias, libro y liquidez, análisis por horizontes, historial, comparación y ranking— con los 33 requisitos.
3. **Tercero:** revisar cobertura no funcional más allá de las 10 métricas iniciales: el catálogo contiene `NFR-001`–`NFR-018`, por lo que deben inspeccionarse todos sus campos, criterios y trazabilidad, no asumir que solo existen los diez primeros.
4. **Cuarto:** identificar contradicciones, huecos y criterios de aceptación no verificables, citando ruta, sección o Issue exacto.
5. **Quinto:** producir una línea base candidata con matriz de cobertura bidireccional y decisiones pendientes claramente separadas.
6. **Sexto:** someterla a revisión del propietario. Hasta esa aprobación, los requisitos siguen siendo una propuesta.

### Condición de salida

Esta actividad no se considera completada hasta que cada objetivo aprobado tenga uno o más requisitos inequívocos, cada requisito tenga criterio de aceptación verificable y trazabilidad, las brechas estén registradas, no queden duplicados/contradicciones sin resolver y el propietario apruebe expresamente la línea base. Este cierre documental no equivale a implementar o validar el producto.
