# Proceso de contribución

Toda decisión técnica, requisito, análisis, pregunta de ingeniería relevante, defecto o mejora que afecte al proyecto debe quedar registrada en GitHub antes de implementar cambios.

## Idioma

Los Issues, Pull Requests, revisiones, plantillas y documentos del proyecto se redactan en español. Se conservan nombres propios, identificadores de código y términos técnicos en inglés cuando sea apropiado.

## Flujo obligatorio

1. Buscar Issues existentes para evitar duplicados.
2. Crear o actualizar un Issue con situación, causa, impacto, solución propuesta, alternativas pertinentes, criterios de aceptación, riesgos y evidencias requeridas.
3. Analizar el problema y las opciones antes de modificar archivos.
4. Crear una rama de trabajo vinculada al Issue. No desarrollar directamente en `main`.
5. Implementar el cambio mínimo que satisfaga los criterios de aceptación.
6. Ejecutar las pruebas pertinentes y registrar comandos, entorno, resultados y limitaciones. Nunca declarar pruebas no ejecutadas como satisfactorias.
7. Abrir un Pull Request que explique el problema, la solución, por qué se eligió, las alternativas consideradas, los archivos afectados y la evidencia de verificación. Vincular el Issue mediante `Closes #N` cuando el PR deba cerrarlo al integrarse.
8. Revisar el cambio, resolver observaciones y comprobar las verificaciones automáticas disponibles.
9. Integrar únicamente cuando el PR haya sido analizado, verificado y probado, y exista evidencia suficiente. No integrar automáticamente por el mero hecho de abrir un PR.
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
