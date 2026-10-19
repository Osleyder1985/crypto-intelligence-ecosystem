# Gobernanza del desarrollo

## Propósito

Mantener trazabilidad entre cada necesidad del proyecto, su análisis, la solución propuesta, los cambios implementados, las pruebas ejecutadas y la decisión de integración.

## Registro de trabajo

Se debe abrir o actualizar un Issue antes de iniciar cualquier cambio sustancial. Esto incluye requisitos, defectos, decisiones de arquitectura, análisis de proveedores o datos, cambios de metodología, riesgos, tareas de investigación y preguntas cuya respuesta afecte al diseño o al alcance.

Las conversaciones pueden ayudar a explorar alternativas, pero las conclusiones relevantes deben trasladarse al Issue correspondiente. Antes de crear uno nuevo, buscar si ya existe un Issue equivalente.

Todo Issue debe explicar:
- Situación o problema.
- Causa o fundamento basado en evidencia disponible.
- Impacto y alcance.
- Solución propuesta.
- Alternativas consideradas o pendientes de investigar.
- Criterios de aceptación comprobables.
- Riesgos y dependencias.
- Evidencia disponible y evidencia pendiente.

## Cambios y Pull Requests

Todo cambio debe desarrollarse en una rama de trabajo y presentarse mediante Pull Request. El PR debe enlazar el Issue, explicar la solución y por qué se considera preferible, describir los archivos afectados y registrar las pruebas ejecutadas con resultados reproducibles.

No se debe integrar un PR hasta que:
1. Se haya revisado el alcance y la solución.
2. Los criterios de aceptación estén cubiertos.
3. Las pruebas pertinentes se hayan ejecutado y sus resultados estén documentados.
4. Los controles automáticos disponibles estén satisfactorios o las excepciones hayan sido evaluadas y aprobadas explícitamente.
5. Los riesgos y las limitaciones conocidas estén documentados.
6. No queden observaciones bloqueantes.

No se debe afirmar que una prueba, auditoría, certificación o protección está completada sin evidencia verificable.

## Regla para main

`main` representa la línea estable del proyecto. No se deben realizar cambios de desarrollo directamente en esa rama. La política esperada es exigir Pull Request y verificaciones antes de integrar.

La protección efectiva de la rama se configura en GitHub, fuera del contenido versionado. Un archivo en el repositorio no basta para activar una regla. El estado de la configuración debe comprobarse y documentarse. Si el plan de GitHub no permite exigir una revisión independiente, debe registrarse esa limitación y no simular una aprobación independiente.

## Idioma

La comunicación del proyecto —Issues, PR, revisiones, documentación y registros de decisiones— se mantiene en español. Se conservan en inglés nombres propios, nombres de bibliotecas, identificadores, comandos y términos técnicos cuando traducirlos reduzca la precisión.

## Evidencia y reproducibilidad

Cuando una afirmación dependa de una prueba, se debe registrar:
- Qué se comprobó.
- Qué versión del código y qué entorno se utilizaron.
- Qué comando o procedimiento se ejecutó.
- Qué resultado se observó.
- Dónde se conserva la evidencia.
- Qué no se pudo comprobar y por qué.

Para análisis cuantitativos o de modelos se deben registrar también la versión de los datos, el período, los parámetros, los costes considerados y el método de validación.

## Estado de esta política

Este documento define el proceso esperado. Su existencia no demuestra que la protección de `main`, las reglas de revisión o los controles de integración estén activos en GitHub. Esos controles deben configurarse y verificarse por separado.
