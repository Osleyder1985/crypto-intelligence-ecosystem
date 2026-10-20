# Proceso de contribución

Toda decisión técnica, requisito, análisis, pregunta de ingeniería relevante, defecto o mejora que afecte al proyecto debe quedar registrada en GitHub antes de implementar cambios.

## Idioma

Los Issues, Pull Requests, revisiones, plantillas y documentos del proyecto se redactan en español. Se conservan nombres propios, identificadores de código y términos técnicos en inglés cuando sea apropiado.

## Modelo operativo: propietario e inteligencia artificial

El proyecto opera con un único propietario humano y asistencia de inteligencia artificial. La IA asume las funciones operativas de ingeniería que resulten aplicables: análisis de requisitos, arquitectura, implementación, revisión técnica, pruebas, QA, análisis de seguridad, revisión normativa, documentación, trazabilidad y preparación de propuestas de integración.

El propietario del proyecto establece objetivos y prioridades, puede intervenir o recomendar cambios en cualquier momento y conserva la autoridad final para aceptar decisiones estratégicas y autorizar la integración en `main`. La IA no debe interpretar la ausencia de comentarios como autorización para fusionar, publicar, desplegar ni activar operaciones financieras.

La separación de roles es funcional, no una afirmación de independencia organizativa. Cuando la IA revise trabajo que ella misma produjo, debe identificar ese hecho y compensar el riesgo mediante pruebas automatizadas, criterios de aceptación explícitos, inspección del diff, verificaciones reproducibles, análisis adversarial y declaración de limitaciones. No debe describir esa revisión como auditoría independiente ni como certificación externa.

## Flujo obligatorio

1. Buscar Issues existentes para evitar duplicados.
2. Crear o actualizar un Issue con situación, causa, impacto, solución propuesta, alternativas pertinentes, criterios de aceptación, riesgos y evidencias requeridas.
3. Analizar el problema y las opciones antes de modificar archivos.
4. Crear una rama de trabajo vinculada al Issue. No desarrollar directamente en `main`.
5. Implementar el cambio mínimo que satisfaga los criterios de aceptación.
6. Ejecutar las pruebas pertinentes y registrar comandos, entorno, resultados y limitaciones. Nunca declarar pruebas no ejecutadas como satisfactorias.
7. Abrir un Pull Request que explique el problema, la solución, por qué se eligió, las alternativas consideradas, los archivos afectados y la evidencia de verificación. Vincular el Issue mediante `Closes #N` cuando el PR deba cerrarlo al integrarse.
8. La IA realiza una revisión crítica del cambio, resuelve observaciones y comprueba las verificaciones automáticas disponibles; explicita los controles que no puede ejecutar o verificar.
9. Presentar al propietario un resumen de decisión con alcance, evidencia, riesgos residuales, limitaciones y recomendación. Integrar únicamente tras autorización explícita del propietario; no integrar automáticamente por el mero hecho de abrir un PR.
10. Comprobar que el resultado integrado corresponde al cambio revisado y actualizar la documentación si procede.

## Convención de ramas

Usar nombres descriptivos y prefijos coherentes:

- `feat/<issue>-<resumen>`: funcionalidad.
- `fix/<issue>-<resumen>`: corrección.
- `docs/<issue>-<resumen>`: documentación.
- `test/<issue>-<resumen>`: pruebas.
- `process/<issue>-<resumen>`: proceso de ingeniería.

Ejemplo: `process/1-github-governance`.

## Convención de commits

Usar mensajes breves y descriptivos. Se recomienda el formato:

`tipo: descripción en español`

Tipos habituales: `docs`, `feat`, `fix`, `test`, `refactor`, `build`, `ci`.

## Criterio para aceptar un Pull Request

El PR debe estar vinculado a un Issue, describir la solución y su justificación, aportar evidencia verificable de las pruebas pertinentes, declarar las pruebas no ejecutadas y limitaciones conocidas, y no introducir cambios ajenos al alcance aprobado.

## Protección de main

La regla de protección debe configurarse y comprobarse en los ajustes de GitHub. Este documento y los archivos del repositorio describen el proceso, pero no activan por sí mismos la protección del servidor. Mientras no se confirme la configuración efectiva, debe tratarse como una tarea pendiente y evitar cambios directos a `main`.

## Verificación automática de gobernanza

El workflow `.github/workflows/governance-validation.yml` ejecuta `scripts/quality/check_governance.py` en cada Pull Request y en los pushes a `main`. Comprueba la presencia de los documentos obligatorios y contratos textuales mínimos de gobernanza. Es un control inicial de documentación, no una prueba del producto ni una validación semántica completa de YAML.

Antes de exigir este control como estado obligatorio para integrar, se debe abrir el PR, esperar a que GitHub ejecute el workflow y confirmar el nombre exacto del check. Después, el propietario debe configurar en Settings → Rules (o Branches) una regla aplicable a `main` que exija Pull Request y el check `validar-gobernanza`; debe impedir force-push y eliminación de la rama. La exigencia de aprobación se configura solo según las capacidades disponibles y sin fingir una revisión independiente cuando no exista otro revisor autorizado.

La protección no queda activa por crear este workflow. Hasta verificar la regla en GitHub, el estado se mantiene como pendiente.

## Convención de nombres y estructura

Esta convención es una decisión de ingeniería del proyecto para favorecer consistencia, interoperabilidad y mantenimiento; no se atribuye como una obligación universal impuesta por ISO/IEC.

- Rutas técnicas, nombres de scripts, workflows, pruebas, módulos, variables, funciones, clases y contratos de API: inglés, con una convención uniforme por tecnología.
- Contenido explicativo de documentación, Issues, Pull Requests y registros de decisiones: español. Se conservan identificadores, nombres oficiales y términos técnicos cuando sea necesario para la precisión.
- Identificadores de requisitos, riesgos, decisiones y pruebas deben ser estables y únicos, por ejemplo `REQ-001`, `RISK-001`, `ADR-001` y `TEST-001`.
- Cualquier cambio de rutas debe actualizar en el mismo PR todos los enlaces, referencias de workflows, scripts, configuración y documentación afectados.
- Antes de renombrar, se inspeccionan las referencias y se ejecutan los controles disponibles. No se cambia una ruta técnica en aislamiento.
- La estructura y el contenido documental se gestionan con trazabilidad, control de cambios, estado de aprobación y evidencia de verificación. La aplicabilidad normativa concreta se mantiene en la matriz normativa; no se afirma conformidad por adoptar esta convención.
