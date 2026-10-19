# Matriz de aplicabilidad normativa

- **Estado:** preliminar; pendiente de aprobación.
- **Issue rector:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11)
- **Fecha de consulta de fichas oficiales:** 2026-10-19.

Esta matriz es una evaluación inicial de aplicabilidad, no una declaración de conformidad. Debe actualizarse cuando cambie el alcance y antes de usarla como criterio formal de auditoría. La norma completa puede contener requisitos adicionales que no se reproducen aquí.

| Referencia | Estado/edición verificados | Aplicabilidad inicial | Uso propuesto | Artefactos/evidencia a producir | Estado de decisión |
|---|---|---|---|---|---|
| ISO/IEC/IEEE 12207 | 2026, publicada; edición 2017 retirada | Alta | Estructurar procesos del ciclo de vida del software desde concepción hasta retirada, con iteraciones | Ciclo de vida, procesos, puertas, registros de verificación/validación, gestión de cambios | Propuesta |
| ISO/IEC 25010 | 2023, publicada | Alta | Derivar atributos de calidad y convertirlos en requisitos medibles | Catálogo NFR, métricas, estrategia de pruebas y resultados | Propuesta |
| ISO/IEC 27001 | 2022, publicada; enmienda 1:2024 sobre cambios climáticos | Condicional, según el alcance del sistema de gestión y objetivos de negocio | Usar como referencia para gestión sistemática de riesgos de seguridad; valorar más adelante si se pretende certificar una organización/alcance | Inventario de activos, riesgos, controles aplicables, tratamiento y evidencias de gestión | Pendiente |
| ISO 31000 | 2018, confirmada en 2023 y marcada por ISO para revisión | Alta como guía de gestión de riesgos | Estructurar identificación, análisis, tratamiento, seguimiento y comunicación de riesgos | Registro de riesgos, responsables, tratamiento, riesgo residual y revisión | Propuesta |
| ISO/IEC/IEEE 15288 | Edición y estado deben verificarse en ficha oficial antes de fijar la línea base | Potencialmente alta para el sistema completo, más allá del software | Complementar 12207 si el análisis de sistema, operación, servicios externos y clientes requiere procesos de ciclo de vida de sistemas | Mapa de sistema, interfaces, ciclo de vida y responsabilidades | Pendiente de verificación |
| ISO/IEC/IEEE 42010 | Edición y estado deben verificarse en ficha oficial antes de fijar la línea base | Potencial | Estructurar descripción de arquitectura, stakeholders, concerns, viewpoints y views | Descripción de arquitectura, vistas y decisiones arquitectónicas | Pendiente de verificación |
| ISO 9241-210 | Edición y estado deben verificarse en ficha oficial antes de fijar la línea base | Alta para la UX de web y móvil | Incorporar diseño centrado en las personas, investigación de usuarios y evaluación iterativa | Perfiles/tareas, prototipos, hallazgos de pruebas de usabilidad y cambios | Pendiente de verificación |
| Norma de accesibilidad web/móvil pertinente | Debe identificarse la referencia y edición aplicables al producto y jurisdicción | Alta como objetivo de producto; obligación legal por determinar | Definir criterios de accesibilidad verificables para navegación, formularios, contraste, lector de pantalla y estados | Especificación de accesibilidad, auditorías y pruebas con tecnología de asistencia | Pendiente |
| ISO/IEC 42001 | Edición/estado deben verificarse antes de incluirla como referencia aprobada | Solo si se define un sistema de gestión de IA con alcance real | Evaluar gobernanza de IA si el producto incorpora IA de forma material y se justifica por riesgos/objetivos | Inventario de sistemas de IA, evaluación de riesgos y gobernanza | Condicional |
| ISO/IEC 23894 | Edición/estado deben verificarse antes de incluirla como referencia aprobada | Solo si se adopta IA/ML | Orientar gestión de riesgos específicos de IA, complementaria a la gestión general | Riesgos del modelo, datos, validación, supervisión y seguimiento | Condicional |

## Fuentes oficiales consultadas

1. [ISO/IEC/IEEE 12207:2026 — ficha oficial ISO](https://www.iso.org/standard/90219.html). La ficha indica publicación en abril de 2026 y retirada de la edición 2017.
2. [ISO/IEC 25010:2023 — ficha oficial ISO](https://www.iso.org/standard/78176.html). Define un modelo de calidad de producto con características y subcaracterísticas.
3. [ISO/IEC 27001:2022 — ficha oficial](https://committee.iso.org/standard/27001).
4. [ISO/IEC 27001:2022/Amd 1:2024 — ficha oficial](https://www.iso.org/standard/88435.html).
5. [ISO 31000:2018 — ficha oficial ISO](https://www.iso.org/standard/65694.html). La ficha señala que la edición permanece vigente y está marcada para revisión; la norma es guía y no se usa para certificación.

## Reglas para aprobar una referencia

Antes de pasar cualquier fila a “aprobada”:
1. Abrir y registrar la ficha oficial vigente de ISO/IEC/IEEE u organismo normativo responsable.
2. Registrar título exacto, edición, fecha, estado, enmiendas y sustituciones.
3. Identificar requisitos aplicables al producto y distinguirlos de recomendaciones o controles voluntarios.
4. Justificar inclusión/exclusión, coste, responsables y artefactos que demostrarán aplicación.
5. Evitar copiar texto protegido de la norma; registrar referencias de cláusula solo si se dispone legalmente de la norma.
6. Definir quién revisará la matriz y qué evento obliga a actualizarla.

**No conformidad automática:** no se debe declarar cumplimiento, certificación ni auditoría satisfactoria a partir de esta matriz. La implementación y la evidencia aún deben producirse y revisarse.
