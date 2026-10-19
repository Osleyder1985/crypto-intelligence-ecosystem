# Matriz de aplicabilidad normativa

- **Estado:** preliminar; pendiente de aprobación.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Issue relacionado:** [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- **Fecha de consulta de fichas oficiales:** 2026-10-19.

Esta matriz es una evaluación inicial de aplicabilidad, no una declaración de conformidad. Debe actualizarse cuando cambie el alcance y antes de usarla como criterio formal de auditoría. La norma completa puede contener requisitos adicionales que no se reproducen aquí.

| Referencia | Estado/edición verificados | Aplicabilidad inicial | Uso propuesto | Artefactos/evidencia a producir | Estado de decisión |
|---|---|---|---|---|---|
| ISO/IEC/IEEE 12207 | 2026, publicada; edición 2017 retirada | Alta | Estructurar procesos del ciclo de vida del software desde concepción hasta retirada, con iteraciones | Ciclo de vida, procesos, puertas, registros de verificación/validación, gestión de cambios | Propuesta |
| ISO/IEC 25010 | 2023, publicada | Alta | Derivar atributos de calidad y convertirlos en requisitos medibles | Catálogo NFR, métricas, estrategia de pruebas y resultados | Propuesta |
| ISO/IEC 27001 | 2022, publicada; enmienda 1:2024 sobre cambios climáticos | Condicional, según el alcance del sistema de gestión y objetivos de negocio | Usar como referencia para gestión sistemática de riesgos de seguridad; valorar más adelante si se pretende certificar una organización/alcance | Inventario de activos, riesgos, controles aplicables, tratamiento y evidencias de gestión | Pendiente |
| ISO 31000 | 2018, confirmada en 2023 y marcada por ISO para revisión | Alta como guía de gestión de riesgos | Estructurar identificación, análisis, tratamiento, seguimiento y comunicación de riesgos | Registro de riesgos, responsables, tratamiento, riesgo residual y revisión | Propuesta |
| ISO/IEC/IEEE 15289 | 2019, edición 4; ficha oficial consultada indica confirmación en 2025 y revisión en curso para posible revisión futura | Alta para gestión de información documental del ciclo de vida | Definir propósito y contenido de los artefactos documentales; no prescribe por sí sola una estructura universal de carpetas o medio de almacenamiento | Índice documental, plantillas, control de estado, trazabilidad, responsables y registros | Propuesta; aplicabilidad detallada pendiente |
| ISO/IEC/IEEE 15288 | Edición y estado deben verificarse en ficha oficial antes de fijar la línea base | Potencialmente alta para el sistema completo, más allá del software | Complementar 12207 si el análisis de sistema, operación, servicios externos y clientes requiere procesos de ciclo de vida de sistemas | Mapa de sistema, interfaces, ciclo de vida y responsabilidades | Pendiente de verificación |
| ISO/IEC/IEEE 42010 | 2022, edición 2, publicada | Potencial; alta para documentar la arquitectura de referencia | Estructurar la descripción de arquitectura, interesados, preocupaciones, puntos de vista y vistas; no prescribe un formato o medio único de registro | Descripción de arquitectura, vistas y decisiones arquitectónicas | Propuesta; aplicabilidad detallada pendiente |
| ISO 9241-210 | Edición y estado deben verificarse en ficha oficial antes de fijar la línea base | Alta para la UX de web y móvil | Incorporar diseño centrado en las personas, investigación de usuarios y evaluación iterativa | Perfiles/tareas, prototipos, hallazgos de pruebas de usabilidad y cambios | Pendiente de verificación |
| Norma de accesibilidad web/móvil pertinente | Debe identificarse la referencia y edición aplicables al producto y jurisdicción | Alta como objetivo de producto; obligación legal por determinar | Definir criterios de accesibilidad verificables para navegación, formularios, contraste, lector de pantalla y estados | Especificación de accesibilidad, auditorías y pruebas con tecnología de asistencia | Pendiente |
| ISO/IEC 42001 | Edición/estado deben verificarse antes de incluirla como referencia aprobada | Solo si se define un sistema de gestión de IA con alcance real | Evaluar gobernanza de IA si el producto incorpora IA de forma material y se justifica por riesgos/objetivos | Inventario de sistemas de IA, evaluación de riesgos y gobernanza | Condicional |
| ISO/IEC 23894 | Edición/estado deben verificarse antes de incluirla como referencia aprobada | Solo si se adopta IA/ML | Orientar gestión de riesgos específicos de IA, complementaria a la gestión general | Riesgos del modelo, datos, validación, supervisión y seguimiento | Condicional |

## Fuentes oficiales consultadas

1. [ISO/IEC/IEEE 12207:2026 — ficha oficial ISO](https://www.iso.org/standard/90219.html). La ficha indica publicación en abril de 2026 y retirada de la edición 2017.
2. [ISO/IEC 25010:2023 — ficha oficial ISO](https://www.iso.org/standard/78176.html). Define un modelo de calidad de producto con características y subcaracterísticas.
3. [ISO/IEC 27001:2022 — ficha oficial](https://committee.iso.org/standard/27001).
4. [ISO/IEC 27001:2022/Amd 1:2024 — ficha oficial](https://www.iso.org/standard/88435.html).
5. [ISO 31000:2018 — ficha oficial ISO](https://www.iso.org/standard/31000). La ficha señala que la edición permanece vigente y está marcada para revisión; la norma es guía y no se usa para certificación.

## Reglas para aprobar una referencia

Antes de pasar cualquier fila a “aprobada”:
1. Abrir y registrar la ficha oficial vigente de ISO/IEC/IEEE u organismo normativo responsable.
2. Registrar título exacto, edición, fecha, estado, enmiendas y sustituciones.
3. Identificar requisitos aplicables al producto y distinguirlos de recomendaciones o controles voluntarios.
4. Justificar inclusión/exclusión, coste, responsables y artefactos que demostrarán aplicación.
5. Evitar copiar texto protegido de la norma; registrar referencias de cláusula solo si se dispone legalmente de la norma.
6. Definir quién revisará la matriz y qué evento obliga a actualizarla.

**No conformidad automática:** no se debe declarar cumplimiento, certificación ni auditoría satisfactoria a partir de esta matriz. La implementación y la evidencia aún deben producirse y revisarse.


## Trazabilidad normativa con los requisitos analíticos ampliados

Esta sección propone asociaciones de control para orientar el diseño y la evidencia. No equivale a una evaluación formal de conformidad; las cláusulas específicas solo se deben asignar tras verificar legalmente la edición completa aplicable y su alcance.

| Área de control | Requisitos relacionados | Evidencia de producto prevista | Estado |
|---|---|---|---|
| Ciclo de vida y gestión de requisitos | REQ-P-001, REQ-P-005, REQ-P-010, REQ-P-020 | IDs estables, decisiones registradas, trazabilidad requisito-diseño-prueba-release y control de cambios | Propuesta; cláusulas pendientes |
| Calidad de producto y experiencia | REQ-P-004, REQ-P-006, REQ-P-008, REQ-P-018; NFR-001, NFR-006, NFR-016, NFR-018 | Criterios de calidad medibles, pruebas de tareas, accesibilidad, rendimiento, estados de error e incertidumbre | Propuesta; métricas por acordar |
| Seguridad y resiliencia | REQ-P-007, REQ-P-018, REQ-P-019; NFR-004, NFR-005, NFR-015 | Modelo de amenazas, control de acceso, gestión de secretos, registro seguro, pruebas de recuperación y riesgos residuales | Propuesta; aplicabilidad por evaluar |
| Gestión de riesgos | REQ-P-012, REQ-P-016, REQ-P-019; NFR-013, NFR-015, NFR-016 | Registro de riesgos, escenarios, sensibilidad, tratamiento, responsable y riesgo residual | Propuesta; no implica certificación |
| Procedencia e integridad de datos | REQ-P-011, REQ-P-020; NFR-003, NFR-011, NFR-014 | Catálogo de fuentes, timestamps point-in-time, control de unidades, referencias/hash y reproducción de ejecución | Propuesta; diseño pendiente |
| Validación cuantitativa y transparencia | REQ-P-013, REQ-P-014, REQ-P-017, REQ-P-019; NFR-012, NFR-013, NFR-017 | Protocolo predefinido, benchmark, evaluación temporal, calibración, sensibilidad y conservación de resultados negativos | Control interno propuesto; no atribuirlo como exigencia textual de una norma sin verificarla |
| Historial y comparación de evaluaciones | REQ-P-005, REQ-P-020, REQ-P-021 | Identificadores de ejecución, referencias inmutables, comparación de versiones y distinción entre cambios de mercado, método y datos | Control interno propuesto; pruebas de reconstrucción pendientes |
| Ranking reproducible de activos | REQ-P-022; NFR-017, NFR-016 | Universo elegible, exclusiones, horizonte, pesos, comparabilidad, incertidumbre y reconstrucción histórica | Control interno propuesto; protocolo y umbrales pendientes |
| Detección de movimientos y memoria de eventos | REQ-P-023, REQ-P-024; REQ-P-013, REQ-P-014; NFR-014 | Evidencia fechada, timestamps de publicación/captura, explicaciones alternativas, predicciones y evaluación fuera de muestra | Control interno propuesto; no implica causalidad ni capacidad predictiva demostrada |
| Profundidad y liquidez de mercado spot | REQ-P-003, REQ-P-025, REQ-P-011; NFR-003, NFR-011 | Capturas de libro/trades, cobertura por exchange/par, spread, profundidad, slippage, frescura y límites del histórico | Control interno propuesto; cobertura real por proveedor pendiente de validar |
| Soportes/resistencias y experiencia analítica | REQ-P-026, REQ-P-027; NFR-006, NFR-016, NFR-018 | Métodos multi-temporalidad, invalidación, incertidumbre, accesibilidad y pruebas de tareas | Control interno propuesto; métricas y validación empírica pendientes |

### Regla de uso

- No asociar una práctica a una cláusula normativa específica sin verificar la fuente oficial y el texto aplicable.
- Distinguir requisitos normativos, buenas prácticas voluntarias y controles de producto definidos por el equipo.
- Cada control aprobado debe tener responsable, riesgo que trata, artefacto, método de verificación y evidencia retenida.
- Revisar aplicabilidad y obligaciones legales por jurisdicción, proveedor y tipo de dato antes de publicar el servicio.
- No declarar conformidad, certificación o auditoría satisfactoria por el mero hecho de mantener esta matriz.

## Convención documental y de nombres del repositorio (propuesta)

Las normas citadas no se interpretan como una obligación universal de nombrar carpetas, archivos, variables o funciones en inglés. ISO/IEC/IEEE 15289 aborda el propósito y contenido de los elementos de información del ciclo de vida, pero no prescribe un formato único de almacenamiento o una política universal de idioma para nombres de archivo. ISO/IEC/IEEE 42010 establece requisitos para describir la arquitectura, pero no impone un formato de archivo concreto. Por tanto, la convención siguiente es una decisión de ingeniería del proyecto que deberá aprobarse y controlarse como tal, no una cita literal de ISO.

- Rutas técnicas, nombres de módulos, scripts, workflows, pruebas, símbolos de código y contratos de API: inglés, ASCII cuando sea viable, minúsculas y separación por guiones bajos o guiones según la tecnología; cada área fijará una única convención.
- Contenido explicativo de documentación, Issues, Pull Requests y decisiones: español, conservando los identificadores normativos, términos de dominio, nombres propios y nombres oficiales de tecnologías.
- Identificadores de requisitos, riesgos, decisiones y pruebas: estables, únicos y no dependientes del idioma; por ejemplo, `REQ-001`, `RISK-001`, `ADR-001` y `TEST-001`.
- Los nombres de rutas se cambiarán solo mediante PR, con inventario de referencias, actualización de enlaces y validación de workflows/scripts; no se renombrarán archivos aislados sin actualizar sus consumidores.
- Esta convención se considera propuesta hasta que el propietario del proyecto la apruebe. La coherencia y la trazabilidad son los criterios de aceptación; el idioma inglés no se presentará como exigencia de ISO.

## Referencias normativas adicionales verificadas

- **ISO/IEC/IEEE 12207:2026**, edición publicada en abril de 2026, es la edición vigente localizada; la ficha oficial indica que 12207:2017 fue retirada. Debe usarse la edición 2026 al fijar la línea base normativa, tras evaluar aplicabilidad.
- **ISO/IEC/IEEE 15289:2019**, edición 4, publicada y confirmada en 2025 según la ficha oficial consultada; la ficha también señala que está en revisión para posible revisión futura. Su alcance cubre el propósito y contenido de los elementos de información del ciclo de vida, pero no define por sí sola una estructura universal de carpetas ni un formato de almacenamiento.
- **ISO/IEC/IEEE 42010:2022**, edición 2, publicada; especifica requisitos para la estructura y expresión de descripciones de arquitectura, incluidos marcos, puntos de vista y modelos. No prescribe un formato o medio único para registrar la descripción.

Fuentes oficiales:
1. [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html).
2. [ISO/IEC/IEEE 15289:2019](https://www.iso.org/standard/74909.html).
3. [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html).


