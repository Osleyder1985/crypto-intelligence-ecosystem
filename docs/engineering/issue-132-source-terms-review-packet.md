# Issue #132 — paquete de revisión de términos de fuentes externas

## Propósito y límites

Este documento convierte la revisión de condiciones de acceso y uso en una tarea reproducible y auditable. **No es una aprobación legal, no concede derechos y no cambia el estado de ninguna fuente.** Las tres fuentes del registro permanecen `TERMS_PENDING`; el capturador de feeds debe seguir bloqueando solicitudes hasta que se aprueben expresamente los usos previstos.

La revisión debe evaluar por separado, para cada proveedor y URL:

1. Condiciones de acceso automatizado y límites de frecuencia.
2. Permiso para análisis interno (`internal_analysis`).
3. Permiso para conservar de forma persistente respuestas, resúmenes, metadatos y hashes (`persistent_storage`).
4. Restricciones de redistribución, republicación, derechos de autor, retención y atribución.
5. Si la página de políticas enlazada es suficiente para la fuente concreta o si hace falta una licencia/confirmación adicional.
6. Quién revisó la evidencia, cuándo y con qué alcance aprobado.

El acceso público a una página o feed **no demuestra por sí solo** que todos esos usos estén autorizados.

## Fuentes registradas y estado

| ID de fuente | Endpoint registrado | Página de condiciones/políticas registrada | Estado |
| --- | --- | --- | --- |
| `sec_press_releases` | https://www.sec.gov/news/pressreleases.rss | https://www.sec.gov/about/developer-resources | `TERMS_PENDING` |
| `sec_press_release_archive` | https://www.sec.gov/newsroom/press-releases | https://www.sec.gov/about/developer-resources | `TERMS_PENDING` |
| `cftc_general_press_releases` | https://www.cftc.gov/RSS/RSSGP/rssgp.xml | https://www.cftc.gov/WebPolicy/index.htm | `TERMS_PENDING` |
| `cftc_press_release_archive` | https://www.cftc.gov/PressRoom/PressReleases | https://www.cftc.gov/WebPolicy/index.htm | `TERMS_PENDING` |
| `federal_reserve_press_releases` | https://www.federalreserve.gov/feeds/press_all.xml | https://www.federalreserve.gov/disclaimer.htm | `TERMS_PENDING` |
| `federal_reserve_press_release_archive` | https://www.federalreserve.gov/newsevents/pressreleases.htm | https://www.federalreserve.gov/disclaimer.htm | `TERMS_PENDING` |

Los endpoints y políticas anteriores corresponden a los seis `source_id` actualmente declarados en `scripts/market_selection/event_source_registry.py`. Si la autoridad publica una política específica para RSS, APIs o reutilización de contenido, inclúyase como evidencia adicional; no se debe asumir que una página genérica resuelve todas las cuestiones.

## Paquete de evidencia requerido por fuente

Guardar un expediente de revisión independiente para cada fuente. Como mínimo, registrar:

- `source_id`, nombre del proveedor y URL exacta revisada.
- Fecha y hora UTC de captura; URL solicitada y URL final después de redirecciones.
- Código HTTP, `Content-Type`, `Last-Modified` y `ETag` cuando estén presentes.
- User-Agent utilizado para recuperar la página de políticas.
- Bytes completos de la respuesta preservados en el expediente, cuando su conservación esté permitida; SHA-256 calculado sobre esos bytes exactos.
- Copia o referencia verificable de las condiciones vigentes, cláusulas relevantes y fecha/versión efectiva si se publica.
- Decisión separada y justificada para acceso automatizado, análisis interno, almacenamiento persistente y cualquier redistribución.
- Restricciones operativas (frecuencia, identificación, retención, atribución, límites de contenido).
- Identidad del revisor humano autorizado, fecha de revisión y evidencia de su autoridad para aprobar el uso.
- Decisión final: `APPROVED`, `TERMS_PENDING` o `REJECTED`, con razón y alcance.

No registrar secretos ni credenciales. No truncar silenciosamente una captura. Si el cuerpo no se pudo leer completo, la captura debe marcarse incompleta y no servir como prueba de revisión. Un hash demuestra integridad de los bytes capturados, no su autenticidad jurídica ni la interpretación correcta de las condiciones.

## Checklist de revisión humana

Para cada fuente, marcar cada punto como **Sí**, **No** o **No determinado**, y enlazar la evidencia concreta:

- [ ] La URL de condiciones pertenece al proveedor y corresponde al servicio/feed usado.
- [ ] Se revisaron las condiciones aplicables a acceso automatizado y sus límites.
- [ ] Se determinó si el uso propuesto de análisis interno está permitido.
- [ ] Se determinó si la persistencia de los datos concretos está permitida y durante cuánto tiempo.
- [ ] Se revisaron derechos de autor, atribución, redistribución y restricciones de contenido.
- [ ] Se documentaron conflictos entre términos, políticas, robots.txt, API terms o instrucciones específicas.
- [ ] Se registraron la captura íntegra, los metadatos y el SHA-256 verificable.
- [ ] Un revisor humano autorizado emitió una decisión explícita para cada caso de uso solicitado.
- [ ] La decisión del registro coincide exactamente con la evidencia, su hash y el alcance aprobado.

Un punto desconocido mantiene la fuente pendiente para el uso afectado. No convertir un “No determinado” en permiso por inferencia.

## Reglas de transición del registro

- `TERMS_PENDING`: estado actual y predeterminado mientras falte evidencia o revisión.
- `APPROVED`: solo después de que un revisor autorizado documente la evidencia, su SHA-256, identidad, fecha y lista explícita de casos de uso aprobados. La entrada debe conservar los bytes de términos exigidos por el validador del registro.
- `REJECTED`: cuando la revisión concluye que el uso propuesto no está permitido.
- `SUSPENDED`: cuando una autorización existente deja de ser fiable, cambia la política o aparece un conflicto que exige revisión.
- `RETIRED`: cuando se decide dejar de usar la fuente.

No se deben rellenar `reviewed_by`, `reviewed_at`, `terms_sha256` ni `allowed_use_cases` con valores ficticios para hacer pasar validaciones. Una prueba sintética puede verificar el flujo técnico, pero nunca sustituye la revisión real del proveedor.

## Pruebas y validación técnica posteriores

Una vez completada una revisión real, verificar:

1. El hash coincide con los bytes preservados y con `terms_sha256` del registro.
2. La autorización está limitada a los casos de uso expresamente aprobados.
3. La captura del feed solo se intenta para una fuente aprobada y con User-Agent identificable cuando corresponda.
4. Los errores, las respuestas incompletas y los cambios de términos no se interpretan como autorización.
5. La identidad del activo se resuelve mediante identificadores estables revisados; no solo por ticker o nombre.
6. Los eventos siguen siendo candidatos hasta verificar el hecho y su entidad.
7. La proximidad temporal con un movimiento no se presenta como causalidad.
8. La prueba de extremo a extremo usa un fixture sintético o una captura autorizada y deja constancia de cuál de las dos se ejecutó.

Comandos de contrato existentes:

```bash
python -m unittest discover -s tests/market_selection -p "test_public_event_feed.py" -v
python -m unittest discover -s tests/market_selection -p "test_external_event_evidence.py" -v
python -m unittest discover -s tests/market_selection -p "test_research_evidence_integration.py" -v
```

Estas pruebas son offline y no aprueban términos ni demuestran disponibilidad en vivo.

## Resultado actual y criterio para cerrar Issue #132

**Estado actual: pendiente de revisión humana de términos.** El flujo técnico offline de candidatos de eventos e integración en el informe ya existe, pero eso no equivale a ingestión real autorizada de SEC/CFTC/Federal Reserve. No se deben ejecutar capturas de esos feeds ni cambiar sus estados hasta que exista el expediente de revisión y una decisión autorizada.

Issue #132 puede cerrarse únicamente cuando se completen sus criterios funcionales con evidencia verificable, se documenten los límites de cobertura y se demuestre que el informe conserva la distinción entre hecho verificado, relación temporal, hipótesis y causalidad respaldada.

## 9. Comprobación preliminar de páginas oficiales — 2026-10-23

Esta comprobación documental de páginas públicas no es una revisión legal ni autoriza captura, almacenamiento o redistribución. Se registran solo hechos observables en las páginas enlazadas y las incertidumbres que quedan pendientes.

### SEC

- La página oficial de [RSS Feeds](https://www.sec.gov/about/rss-feeds) enumera feeds de comunicados, discursos, actuaciones y materiales EDGAR. La página indica que fue revisada/actualizada el 24 de junio de 2026.
- El portal oficial de [SEC Data APIs](https://data.sec.gov/) indica que el acceso automatizado debe cumplir la política de privacidad y seguridad de SEC.gov y remite a la documentación API y a las pautas de acceso justo.
- La FAQ oficial para desarrolladores sobre descargas programáticas de EDGAR menciona un máximo actual de 10 solicitudes por segundo para ese acceso programático. **No se debe trasladar automáticamente ese límite a cada feed RSS** sin confirmar qué política y límites aplican al endpoint concreto.
- La página oficial de Website Dissemination (https://www.sec.gov/about/privacy-information) afirma que la información de sec.gov es pública y puede copiarse o distribuirse sin permiso de SEC, con advertencias sobre sellos, logos y marcas. La documentación para desarrolladores (https://www.sec.gov/about/developer-resources) sigue siendo relevante para acceso automatizado. La evidencia favorece la reutilización de información oficial, pero falta documentar el tratamiento de terceros incrustados, retención de cuerpos HTML completos y condiciones específicas del RSS. Mantener TERMS_PENDING hasta que el revisor autorizado cierre esos puntos.

### CFTC

- La página oficial de [RSS](https://www.cftc.gov/RSS/index.htm), consultada el 23 de octubre de 2026, declara explícitamente: **“As of October 2026, the CFTC has temporarily disabled all RSS feeds”** para los temas enumerados, y que se volverán a habilitar más adelante.
- La [Web Policy de CFTC](https://www.cftc.gov/WebPolicy/index.htm) indica que la información gubernamental del sitio es de dominio público y puede copiarse/distribuirse con atribución adecuada; advierte que algunos documentos, imágenes u otros recursos pueden ser de terceros y estar protegidos.
- La Web Policy de CFTC indica que la información gubernamental es de dominio público con atribución, pero advierte que algunos recursos pueden ser de terceros. La página RSS confirma que los feeds están temporalmente deshabilitados en octubre de 2026. No activar solicitudes repetidas ni sustituir silenciosamente el endpoint. Mantener TERMS_PENDING y volver a comprobar disponibilidad antes de una prueba autorizada futura.

### Federal Reserve Board

- La página oficial de [RSS Feeds](https://www.federalreserve.gov/feeds/feeds.htm) enumera feeds de comunicados, discursos, datos y publicaciones; explica el uso mediante lectores/agregadores RSS. La página indica última actualización el 16 de septiembre de 2025.
- La página enlazada por el registro como política general no resuelve por sí sola, en la evidencia consultada, todos los casos de uso concretos: captura automatizada del feed, almacenamiento persistente de cuerpos completos, duración de retención, extractos y redistribución.
- El Disclaimer oficial (https://www.federalreserve.gov/disclaimer.htm) indica que, salvo indicación contraria, la información del Board es de dominio público y puede copiarse/distribuirse con atribución; los materiales identificados como pertenecientes a terceros pueden requerir permiso separado. La evidencia favorece la reutilización de información oficial, pero falta revisar contenido específico del feed, captura automatizada y retención de cuerpos HTML completos. Mantener TERMS_PENDING hasta que el revisor autorizado registre el alcance aprobado.

### Resultado consolidado

| Fuente | Hecho confirmado | Pendiente | Estado del registro |
| --- | --- | --- | --- |
| SEC | Página oficial de RSS y pautas de acceso automatizado disponibles | Alcance concreto de almacenamiento, retención y reutilización del feed registrado | `TERMS_PENDING` |
| CFTC | La página oficial indica que los feeds RSS están temporalmente deshabilitados en octubre de 2026 | Disponibilidad futura y revisión de usos permitidos | `TERMS_PENDING` |
| Federal Reserve Board | Página oficial de feeds y guía de uso mediante agregadores | Permisos concretos para captura y persistencia del contenido del feed | `TERMS_PENDING` |

**No se cambió el registro de fuentes, no se capturaron feeds y no se habilitó tráfico de red.** La conclusión es documental y preliminar; el revisor humano autorizado debe completar el checklist y registrar la evidencia de términos antes de aprobar cualquier uso.

## 10. Evidencia oficial adicional sobre reutilización de contenido — 2026-10-23

Esta sección complementa la revisión preliminar. No cambia automáticamente los estados del registro.

- **SEC:** https://www.sec.gov/about/privacy-information declara que la información de sec.gov es pública y puede copiarse/distribuirse sin permiso de SEC; la documentación de desarrolladores https://www.sec.gov/about/developer-resources sigue siendo relevante para acceso automatizado. La autorización técnica debe limitarse a contenido oficial pertinente y excluir recursos de terceros cuando no exista permiso demostrado.
- **CFTC:** https://www.cftc.gov/WebPolicy/index.htm indica que la información gubernamental es de dominio público con atribución y advierte sobre recursos de terceros. https://www.cftc.gov/RSS/index.htm confirma que los feeds están temporalmente deshabilitados en octubre de 2026.
- **Federal Reserve Board:** https://www.federalreserve.gov/disclaimer.htm declara que, salvo indicación contraria, la información del Board es de dominio público y puede copiarse/distribuirse con atribución; los materiales de terceros quedan sujetos a sus propios derechos.

La evidencia pública reduce la incertidumbre sobre copyright del contenido oficial, pero no es autorización general para almacenar indiscriminadamente todos los bytes HTML de páginas que puedan incluir contenido de terceros. El revisor debe documentar el alcance por fuente, definir si se almacenará HTML completo o contenido textual oficial extraído, revisar las condiciones de acceso automatizado y aprobar por separado los casos de uso. Hasta entonces, no cambiar el estado ni los casos de uso permitidos en el registro.


## 11. Propuesta de alcance mínimo para la primera prueba autorizada — 2026-10-23

Esta propuesta reduce el riesgo y el número de decisiones simultáneas. **No es una aprobación del propietario ni cambia el estado de ninguna fuente.** El registro de ejecución debe continuar en `TERMS_PENDING` hasta que una persona autorizada apruebe explícitamente el alcance y el paquete de evidencia cumpla el contrato del validador.

### Orden recomendado de evaluación

| Prioridad | Fuente | Evidencia oficial actual | Propuesta técnica | Bloqueo que permanece |
| --- | --- | --- | --- | --- |
| 1 | SEC — comunicados oficiales | La SEC declara que la información de sec.gov es pública y puede copiarse o redistribuirse, pide atribución y limita el uso de sellos/logos; también controla la frecuencia de acceso y no permite bots no clasificados. [Política de privacidad y difusión](https://www.sec.gov/about/privacy-information). | Evaluar primero una prueba de una sola página/comunicado oficial, con User-Agent identificable, una solicitud por invocación, contenido oficial pertinente, atribución y captura íntegra solo si se aprueba expresamente esa persistencia. | El operador debe aprobar endpoint, método de captura, tratamiento de contenido de terceros, persistencia/retención y caso de uso. No activar por defecto. |
| 2 | Federal Reserve Board — comunicados oficiales | Su disclaimer permite copiar/distribuir la información del Board salvo indicación contraria, con atribución; el contenido de terceros puede requerir permiso separado. [Disclaimer](https://www.federalreserve.gov/disclaimer.htm). | Evaluar después de SEC, para eventos macroeconómicos con fecha/hora publicada, conservando por separado publicación y captura y sin convertir la coincidencia temporal en causalidad. | Falta decisión humana específica sobre feed/archivo, contenido guardado, retención y condiciones operativas del acceso automatizado. |
| 3 | CFTC — comunicados oficiales | La Web Policy declara que la información gubernamental es de dominio público con atribución y advierte de contenido de terceros. [Web Policy](https://www.cftc.gov/WebPolicy/index.htm). El índice RSS fue reportado como temporalmente deshabilitado en octubre de 2026 en la revisión del repositorio. | No usar el RSS como primera ruta. Revalidar el estado oficial en el momento de la futura prueba; si continúa no disponible, no reintentar en bucle ni cambiar silenciosamente de endpoint. | Disponibilidad del feed/archivo y alcance autorizado por el operador. |

### Alcance mínimo propuesto para una prueba piloto

La decisión de aprobación debería declarar cada punto de forma explícita; no se deben inferir permisos no seleccionados:

- **Fuente inicial:** solo `sec_press_releases` o, si el operador prefiere otra, identificarla por su `source_id` exacto.
- **Finalidad:** `internal_analysis` para investigación de eventos de mercado; no redistribución pública ni republicación de artículos.
- **Material persistido:** declarar si se permite guardar respuesta completa, texto oficial extraído, metadatos y hashes. No tratar un hash como sustituto del contenido cuando la prueba E2E necesite verificar el artículo.
- **Retención y eliminación:** definir el periodo o regla de retención aprobada, qué se elimina y qué metadatos no textuales pueden conservarse.
- **Atribución y enlaces:** guardar fuente, URL canónica y metadatos de publicación; mostrar atribución requerida en el informe.
- **Acceso automatizado:** endpoint exacto, User-Agent revisado, frecuencia/cuota, timeout, política de redirecciones y respuesta ante errores.
- **Prueba E2E:** ejecutar solo tras aprobar la fuente; capturar índice o feed, seleccionar un candidato, obtener el artículo autorizado, verificar entidad con identificador estable, evaluar el corte temporal y producir salida factual/correlacional/causal conservadora.
- **Cobertura:** generar manifiesto de páginas/segmentos esperados, capturados, ausentes, fallidos y fuera de alcance. Nunca declarar cobertura global completa a partir de una muestra.

### Decisión pendiente del propietario

Para pasar de documentación a captura real se requiere una decisión humana explícita con esta información mínima:

1. `source_id` que se autoriza.
2. Casos de uso aprobados (`internal_analysis`, `persistent_storage` y cualquier otro que el esquema admita).
3. Tipos de contenido que pueden persistirse y su regla de retención/eliminación.
4. Confirmación de atribución, restricciones de terceros y política de acceso automatizado.
5. Identidad del revisor autorizado y fecha de decisión.

Si algún punto queda indeterminado, mantener `TERMS_PENDING` para el uso afectado. No rellenar campos de aprobación con identidades, fechas, hashes ni decisiones inventadas. La propuesta prioriza una prueba pequeña y reversible; no autoriza por sí misma la ejecución.

### Fuentes oficiales revisadas

- SEC, [Privacy and Security Policy / Website Dissemination](https://www.sec.gov/about/privacy-information): difusión pública, atribución, control de frecuencia y bots no clasificados.
- Federal Reserve Board, [Disclaimer](https://www.federalreserve.gov/disclaimer.htm): información pública del Board y excepción de materiales de terceros.
- CFTC, [Web Policy](https://www.cftc.gov/WebPolicy/index.htm): información gubernamental de dominio público con atribución y excepciones de terceros.
- CFTC, [RSS](https://www.cftc.gov/RSS/index.htm): página oficial para comprobar disponibilidad actual de feeds antes de cualquier ejecución.

La consulta de páginas oficiales sirve como evidencia documental, no como dictamen jurídico ni aprobación automática del alcance de captura y almacenamiento.

## 12. Aclaración de alcance: el piloto es una fase de validación, no el alcance final — 2026-10-23

La recomendación de comenzar por una fuente oficial **no reduce el alcance funcional del Issue #132 ni limita el producto final a SEC**. El objetivo funcional se mantiene: identificar acontecimientos potencialmente relacionados con el inicio y el fin de movimientos alcistas y bajistas de los activos investigados, contrastar evidencias de distintas clases de fuentes y preservar la distinción entre hechos, coincidencia temporal, hipótesis y causalidad respaldada.

### Alcance objetivo del ecosistema

La cobertura debe crecer por categorías pertinentes y fuentes autorizadas, según la relevancia para el activo y el periodo investigado:

- **Regulación y medidas públicas:** comunicados, resoluciones y actuaciones oficiales de organismos pertinentes.
- **Macroeconomía y política monetaria:** decisiones de bancos centrales, inflación, empleo, liquidez y publicaciones económicas con marcas temporales verificables.
- **Mercados y derivados:** datos oficiales o autorizados sobre negociación, liquidaciones, financiación, interés abierto y estructura de mercado.
- **Protocolos y redes:** anuncios de equipos oficiales, actualizaciones, incidentes, interrupciones, cambios de tokenómica, gobernanza y actividad on-chain verificable.
- **Seguridad y operación:** exploits, vulnerabilidades, interrupciones, incidentes de puentes y respuestas oficiales de los proyectos.
- **Adopción y actividad empresarial:** anuncios verificables de emisores, custodios, proveedores, integraciones y productos financieros.
- **Prensa y fuentes secundarias:** medios identificables que aporten pistas o contexto, sujetos a sus propios términos, atribución y restricciones de almacenamiento; una noticia secundaria no sustituye la verificación de la fuente primaria cuando esta exista.

Esta lista define categorías de investigación, no concede permisos de captura ni afirma que todas las fuentes ya estén integradas. Cada adaptador deberá registrar origen, hora de publicación, hora de captura, identificador estable, integridad, cobertura, condiciones aplicables y calidad de evidencia.

### Secuencia de incorporación sin convertirla en límite permanente

1. **Validación técnica inicial:** una sola fuente aprobada, para demostrar el recorrido de captura autorizado, integridad, persistencia permitida, manifiesto, deduplicación e integración con los episodios de mercado.
2. **Ampliación de fuentes oficiales:** incorporar otras fuentes pertinentes tras revisar sus condiciones, disponibilidad, límites operativos y usos autorizados.
3. **Ampliación por activo y clase de evento:** añadir fuentes primarias de proyectos, redes, mercados y seguridad según el universo de activos soportado.
4. **Cobertura secundaria y contraste cruzado:** integrar fuentes adicionales autorizadas y exigir evidencia independiente cuando la afirmación lo requiera.
5. **Evaluación continua de cobertura y calidad:** informar qué fuentes y periodos se revisaron, qué faltó, qué falló y qué conclusiones siguen siendo inciertas. No presentar una muestra como cobertura exhaustiva.

Cada fase tiene que producir criterios verificables y trazabilidad; no se debe declarar completada por calendario ni por tener CI verde únicamente.

### Separación obligatoria entre amplitud funcional y autorización

- El objetivo de producto es amplio y multifuente.
- El piloto inicial es deliberadamente pequeño para validar el recorrido técnico y operativo.
- La aprobación de una fuente no autoriza automáticamente otras fuentes ni otros usos.
- No se activa tráfico externo ni se cambia `TERMS_PENDING` sin la decisión explícita exigida por el registro.
- No se aplican límites arbitrarios de tamaño de respuesta: la captura debe preservar la respuesta completa cuando esté permitida, o declarar y documentar claramente cualquier restricción técnica u operativa real; nunca truncar silenciosamente.
- Ninguna asociación temporal basta para afirmar que una noticia causó un movimiento. El sistema debe registrar evidencia a favor, evidencia contraria, alternativas y nivel de incertidumbre.

**Conclusión:** el piloto valida una primera ruta; no redefine el objetivo del Issue #132. El criterio de éxito final es una cobertura multifuente ampliable, reproducible y auditable, dentro de las autorizaciones aplicables y con conclusiones proporcionales a la evidencia.


## 13. Política de conservación basada en normas y documentación oficial — 2026-10-23

### Regla de decisión

No se fija un número arbitrario de días para conservar el contenido. La página oficial de ISO para **ISO 15489-1:2016** describe un marco de gestión de documentos basado, entre otros elementos, en requisitos documentales identificados a partir del contexto de negocio, políticas, responsabilidades, controles y procesos de gestión. La ficha pública de ISO no establece un plazo universal de conservación aplicable a cualquier noticia o feed. Por tanto, no atribuir a ISO un plazo que no aparece en su documentación pública.

Referencias oficiales:
- ISO, [ISO 15489-1:2016 — Records management: Concepts and principles](https://www.iso.org/standard/62542.html). La ficha oficial indica que esta edición sigue vigente tras su revisión/confirmación en 2021.
- ISO/TC 46/SC 11, [Disposition of records](https://committee.iso.org/sites/tc46sc11/home/projects/published/disposition.html), que identifica ISO/TS 7538:2024 como guía sobre disposición de documentos, incluidos periodos de conservación, autoridades y destrucción.
- SEC, [Privacy and Security Policy / Website Dissemination](https://www.sec.gov/about/privacy-information), que permite copiar y redistribuir información presentada en sec.gov con las salvedades indicadas y advierte que el acceso automatizado se somete a control de frecuencia y que no se permiten bots no clasificados.
- SEC, [Developer Resources](https://www.sec.gov/about/developer-resources), que requiere acceso eficiente y descargar solo lo necesario. Estas páginas no fijan un plazo general de conservación de artículos completos para este proyecto.

### Política operativa mientras falte una regla específica aprobada

1. **No persistir contenido íntegro de una fuente externa** hasta documentar una base aplicable para esa fuente y ese tipo de contenido, las restricciones de terceros y la finalidad de conservación.
2. **No ejecutar tampoco una captura externa transitoria** mientras la fuente siga en estado TERMS_PENDING; la ausencia de persistencia no equivale a permiso para solicitar el contenido.
3. Antes de aprobar persistencia, identificar requisitos legales y contractuales aplicables, necesidad funcional, contenido mínimo necesario, propietario del dato, evento que inicia el plazo, regla de revisión, método de eliminación y excepciones de conservación justificadas.
4. Separar las reglas para contenido íntegro, texto oficial extraído, metadatos operativos, hashes y resultados derivados. No asumir que un hash permite conservar el texto ni que queda automáticamente exento de todas las obligaciones.
5. No usar “indefinido” como valor por defecto. La conservación de metadatos o hashes también debe tener una finalidad documentada y una regla de revisión/disposición.
6. Cuando la revisión oficial no determine una duración, registrar “plazo no especificado por la fuente; pendiente de análisis de requisitos aplicables”. Resolverlo mediante el análisis documentado de requisitos y la política de registros del proyecto, no inventando una cifra ni atribuyéndosela a ISO.
7. Registrar evidencia, versión/fecha de la política consultada, decisión y responsable autorizado. Revalidar la decisión si cambian los términos, la finalidad, el contenido capturado o el modo de acceso.

### Aplicación al Issue #132

- SEC, CFTC, Federal Reserve y sus entradas de archivo permanecen en estado TERMS_PENDING hasta completar la revisión por fuente.
- Para SEC, la política pública respalda la reutilización de información de sec.gov con las salvedades publicadas, pero no especifica por sí sola un plazo de conservación para este caso de uso ni autoriza automáticamente cada tipo de contenido enlazado o de terceros.
- La primera prueba E2E y el backfill real solo podrán ejecutarse cuando estén aprobados el acceso externo y los usos necesarios. No se crea una excepción para pruebas.
- La meta de producto sigue siendo multifuente. Esta regla controla la autorización y el ciclo de vida de los datos; no reduce la cobertura funcional deseada.

**Decisión resultante:** no imponer un plazo ficticio. Aplicar las condiciones oficiales de cada fuente y el proceso de gestión de registros de ISO como marco de análisis; mientras falte una decisión respaldada para una fuente/caso de uso, mantener bloqueada su captura y persistencia.


## 14. Verificación de páginas oficiales después de la autorización del propietario — 2026-10-23

Esta actualización registra únicamente lo que muestran las páginas oficiales consultadas. La autorización del propietario del proyecto permite avanzar con la revisión; no sustituye condiciones del proveedor ni permite convertir una inferencia en permiso. No se realizaron solicitudes a feeds de datos ni capturas de artículos.

### SEC — reutilización y acceso automatizado

- La FAQ oficial de SEC Webmaster declara que el contenido creado por el Gobierno en sec.gov y el contenido público de presentaciones EDGAR pueden reutilizarse; advierte que algunos elementos, como imágenes de archivo, pueden no estar libres de restricciones. Fuente: https://www.sec.gov/files/about/webmaster-faq.htm
- La misma FAQ describe un máximo de 10 solicitudes por segundo para acceso programático a EDGAR. No se extrapola ese máximo como regla específica de todos los feeds RSS: el endpoint concreto y las instrucciones aplicables deben confirmarse antes de activarlo.
- La página oficial de privacidad/diseminación de SEC debe leerse junto con los recursos para desarrolladores y las restricciones sobre contenido de terceros. Fuentes: https://www.sec.gov/about/privacy-information y https://www.sec.gov/about/developer-resources
- Resultado: existe evidencia oficial favorable a reutilizar contenido gubernamental SEC, pero todavía deben documentarse el alcance exacto por endpoint, el agente de usuario, el control agregado de solicitudes y el tratamiento de contenido de terceros y persistencia.

### CFTC — feeds temporalmente deshabilitados

- La página oficial RSS indica explícitamente que, a octubre de 2026, la CFTC ha deshabilitado temporalmente los feeds RSS enumerados y que se volverán a habilitar más adelante. Fuente: https://www.cftc.gov/RSS/index.htm
- La Web Policy oficial indica que la información gubernamental del sitio es de dominio público y puede copiarse/distribuirse con reconocimiento adecuado a la CFTC; también advierte que documentos, ilustraciones, fotografías y otros recursos aportados o licenciados por terceros pueden estar protegidos. Fuente: https://www.cftc.gov/WebPolicy/index.htm
- Resultado: no intentar el RSS deshabilitado ni hacer reintentos para sortear su indisponibilidad. El archivo HTML oficial es un origen distinto y necesita su propia validación de endpoint, alcance, acceso automatizado y persistencia. La política de copyright por sí sola no resuelve esos controles operativos.

### Federal Reserve Board — contenido propio y terceros

- El disclaimer oficial indica que, salvo indicación contraria, la información del sitio del Board es de dominio público y puede copiarse/distribuirse sin permiso, citando al Board. También establece que fotografías, gráficos u otros materiales identificados como pertenecientes a fuentes no-Board pueden requerir permiso del titular original. Fuente: https://www.federalreserve.gov/disclaimer.htm
- El índice RSS oficial describe los feeds como un mecanismo para que lectores o agregadores muestren enlaces, titulares y breves resúmenes. Fuente: https://www.federalreserve.gov/feeds/feeds.htm
- Resultado: la reutilización del contenido oficial del Board tiene soporte documental general, pero el registro debe distinguir el texto oficial de recursos de terceros, conservar la atribución y documentar endpoint, agente, límite operativo y la necesidad de persistencia antes de activar cada fuente.

### Decisiones comunes a las seis entradas

1. La evidencia de dominio público/reutilización no significa que cada elemento incrustado sea contenido gubernamental ni resuelve automáticamente la captura automatizada, la retención o la persistencia de HTML completo.
2. No se encontró en estas páginas una duración universal de retención aplicable a este proyecto. No se fija un plazo inventado: el plazo o regla debe basarse en requisitos aplicables identificados y documentados. Mientras no pueda determinarse una regla para un tipo de contenido, no se persiste ese contenido.
3. La revisión del propietario autoriza preparar y verificar el flujo de trabajo; no representa una aprobación del proveedor, una licencia de terceros ni una opinión legal.
4. Los seis source_id permanecen TERMS_PENDING; no se ha modificado el registro operativo ni se ha ejecutado captura externa o backfill.
5. Antes de un E2E real se debe preservar evidencia verificable de las páginas de política consultadas, calcular sus hashes sobre los bytes realmente preservados, completar las decisiones de uso/contenido/retención/atribución/acceso por source_id y verificar la disponibilidad actual del endpoint. No declarar exhaustividad histórica sin manifiesto de segmentos y cobertura.


## 15. Verificación de disponibilidad y alcance visible de los endpoints oficiales — 2026-10-23

Esta revisión consultó páginas públicas oficiales mediante navegación para comprobar los enlaces publicados, el estado comunicado y el alcance visible. **No equivale a una captura del adaptador del proyecto, no preserva una copia de respuesta para el registro técnico y no autoriza cambiar el estado operativo.** Los seis orígenes siguen `TERMS_PENDING`.

### SEC — feed anunciado oficialmente

- El índice oficial de RSS de SEC enumera los comunicados como uno de los feeds de materiales recientes y fue actualizado el 24 de junio de 2026: https://www.sec.gov/about/rss-feeds
- El enlace oficial de comunicados apunta a `https://www.sec.gov/news/pressreleases.rss`. El navegador de consulta no pudo representar el tipo MIME RSS (`application/rss+xml`); esto **no** demuestra que el feed esté caído ni sustituye una prueba de disponibilidad del adaptador.
- El archivo oficial de comunicados se publica por separado en https://www.sec.gov/newsroom/press-releases. El feed actual y el archivo histórico son coberturas distintas; no se puede inferir cobertura histórica completa desde el feed.
- Decisión pendiente: confirmar endpoint y acceso automatizado aplicables, agente identificable, control agregado de solicitudes, contenido de terceros, alcance de persistencia y regla de retención antes de cualquier ejecución real.

### CFTC — RSS no disponible, archivo HTML con publicaciones actuales

- La página oficial RSS mantiene el aviso: en octubre de 2026 todos los feeds RSS enumerados están temporalmente deshabilitados y se reactivarán más adelante: https://www.cftc.gov/RSS/index.htm
- La página oficial del archivo HTML sí muestra entradas recientes, incluida una publicación del 21 de octubre de 2026, y ofrece filtros por palabras clave, tipo, número de comunicado, etiqueta y año: https://www.cftc.gov/PressRoom/PressReleases
- La lista visible en la página consultada no prueba por sí sola cobertura histórica exhaustiva; los segmentos/años y los resultados de filtros deben inventariarse explícitamente. No usar el RSS deshabilitado ni intentar sortear su indisponibilidad.
- La disponibilidad visible del archivo no concede permiso automático para captura automatizada o persistencia. La entrada `cftc_press_release_archive` necesita una revisión independiente de rutas, páginas/segmentos, frecuencia, contenido guardado y retención.

### Federal Reserve Board — feed oficial y archivo por años

- El índice oficial de feeds enumera un feed de todos los comunicados y feeds por categorías: https://www.federalreserve.gov/feeds/feeds.htm
- El enlace oficial “All Press Releases” apunta a `https://www.federalreserve.gov/feeds/press_all.xml`. El navegador de consulta no pudo representar el tipo MIME XML (`text/xml`); esto no demuestra indisponibilidad. La disponibilidad real debe verificarse mediante una ejecución controlada únicamente después de completar las autorizaciones requeridas.
- El archivo oficial muestra enlaces por año desde 2006 y un enlace adicional “Archive”; la página indica que los comunicados anteriores a 2006 se encuentran en el archivo: https://www.federalreserve.gov/newsevents/pressreleases.htm
- Por tanto, el manifiesto histórico debe representar separadamente los segmentos anuales disponibles y el archivo anterior a 2006. La página principal no constituye por sí sola evidencia de que todos los comunicados históricos estén capturados.
- Decisión pendiente: distinguir el feed actual del archivo, delimitar los segmentos, documentar acceso automatizado, contenido de terceros, persistencia y retención.

### Consecuencias para la matriz

| `source_id` | Hallazgo actual | Siguiente evidencia necesaria | Estado |
|---|---|---|---|
| `sec_press_releases` | Feed anunciado por la SEC; el navegador no representó el MIME RSS | Política preservada con hash y validación autorizada del endpoint/adaptador | `TERMS_PENDING` |
| `sec_press_release_archive` | Archivo oficial separado del feed | Decisión de acceso/persistencia y manifiesto de segmentos | `TERMS_PENDING` |
| `cftc_general_press_releases` | RSS oficialmente deshabilitado temporalmente | Revalidar el aviso antes de cualquier posible activación; no solicitar el feed mientras esté deshabilitado | `TERMS_PENDING` |
| `cftc_press_release_archive` | Índice HTML oficial muestra publicaciones recientes y filtros | Revisión de alcance por segmento, acceso automatizado, persistencia y retención | `TERMS_PENDING` |
| `federal_reserve_press_releases` | Feed oficial listado; navegador no representó el MIME XML | Política preservada con hash y validación autorizada del endpoint/adaptador | `TERMS_PENDING` |
| `federal_reserve_press_release_archive` | Archivo oficial enlaza segmentos anuales y archivo anterior a 2006 | Manifiesto de cobertura por año/segmento y decisión de persistencia | `TERMS_PENDING` |

### Límite de esta revisión

No se cambió `event_source_registry.py`, no se habilitó ninguna fuente, no se ejecutó el adaptador de captura, no se persistieron artículos y no se generó un backfill. Las páginas consultadas son evidencia de descubrimiento y alcance visible; antes de aprobar un origen se deben preservar los bytes reales de las políticas pertinentes, calcular el hash sobre esos bytes, completar la decisión individual y verificar el endpoint bajo el control de acceso aprobado.

## 15. Comprobación actual de índices oficiales y disponibilidad visible — 2026-10-23

Esta comprobación se limita a páginas HTML públicas de índices y páginas de información. No se solicitaron los endpoints RSS/XML, no se descargaron comunicados y no se ejecutó el adaptador del proyecto. La disponibilidad visible de un índice HTML no equivale a aprobación de acceso automatizado ni de persistencia.

### SEC — índice de comunicados y RSS anunciado

- El índice oficial https://www.sec.gov/newsroom/press-releases mostró comunicados recientes, identificadores de publicación y paginación (1 a 25 de 6.897 elementos en la vista consultada). Esto acredita que el índice HTML está publicado y ofrece un alcance visible; no demuestra que todo el archivo histórico esté capturado ni valida el endpoint RSS.
- La página oficial https://www.sec.gov/about/rss-feeds enumera “Press Releases” entre los feeds de materiales recientes, pero esa página informativa por sí sola no valida el MIME, la respuesta actual, las redirecciones ni los límites aplicables al endpoint exacto.
- Decisión por separado: `sec_press_releases` requiere validar el feed oficial exacto; `sec_press_release_archive` requiere definir y registrar segmentos/páginas históricas. Ambos siguen `TERMS_PENDING`.

### CFTC — feed temporalmente deshabilitado; índice HTML distinto

- La página oficial RSS https://www.cftc.gov/RSS/index.htm dice expresamente: “As of October 2026, the CFTC has temporarily disabled all RSS feeds”. No intentar los feeds ni sortear la indisponibilidad mientras el aviso permanezca publicado.
- La página oficial de comunicados está enlazada desde el sitio CFTC, pero no se usa la página RSS como prueba de que el archivo HTML esté autorizado o tenga una estructura estable para captura. El archivo HTML necesita evaluación propia de endpoint, robots/política aplicable, paginación, contenido, acceso automatizado y persistencia.
- Decisión por separado: `cftc_general_press_releases` queda bloqueado por la indisponibilidad declarada del RSS; `cftc_press_release_archive` requiere revisión específica del índice HTML. Ambos siguen `TERMS_PENDING`.

### Federal Reserve Board — índice actual y segmentos históricos

- El índice oficial https://www.federalreserve.gov/newsevents/pressreleases.htm mostró comunicados de 2026 y enlaces de archivo por año desde 2006, además de un enlace “Archive”. La página indica que los comunicados anteriores a 2006 están disponibles en el archivo.
- La página oficial https://www.federalreserve.gov/feeds/feeds.htm enumera feeds de comunicados y describe RSS como enlaces, titulares y resúmenes. Esta documentación no sustituye la verificación autorizada de la respuesta XML del endpoint exacto.
- Decisión por separado: `federal_reserve_press_releases` requiere validar el feed específico; `federal_reserve_press_release_archive` debe modelar cada año/segmento y el archivo anterior a 2006 como cobertura separada. Ambos siguen `TERMS_PENDING`.

### Decisiones operativas derivadas

| `source_id` | Evidencia visible actual | Bloqueo/acción pendiente | Estado |
|---|---|---|---|
| `sec_press_releases` | Índice oficial con comunicados recientes; página oficial anuncia RSS | Verificar endpoint RSS exacto, condiciones de acceso, agente, límite agregado y alcance persistible | `TERMS_PENDING` |
| `sec_press_release_archive` | Índice HTML con paginación y años/filtros | Delimitar segmentos y generar manifiesto esperado antes de backfill autorizado | `TERMS_PENDING` |
| `cftc_general_press_releases` | Aviso oficial de feeds RSS deshabilitados temporalmente | No solicitar feed; revalidar aviso en una revisión futura antes de cualquier activación | `TERMS_PENDING` |
| `cftc_press_release_archive` | Índice HTML distinto del RSS | Revisar la página de archivo y sus condiciones de acceso como fuente independiente | `TERMS_PENDING` |
| `federal_reserve_press_releases` | Índice actual y catálogo oficial de feeds | Validar el endpoint XML exacto solo tras aprobación de alcance | `TERMS_PENDING` |
| `federal_reserve_press_release_archive` | Índice con segmentos por año y archivo anterior a 2006 | Especificar cobertura por año/segmento y verificar páginas ausentes sin afirmar exhaustividad global | `TERMS_PENDING` |

### Límite y conclusión

La consulta web de páginas públicas no constituye captura de datos de las fuentes ni reemplaza la preservación de evidencia de política exigida por la matriz. No se calcularon hashes de páginas de políticas porque no se preservaron sus bytes como artefactos; no inventar hashes a partir de resultados de búsqueda o texto extraído. No se cambió el registro operativo, no se ejecutó E2E ni backfill y no se cambió ningún estado `TERMS_PENDING`.


## 16. Control de una posible atribución incorrecta del límite SEC — 2026-10-23

La revisión de la documentación oficial detectó un punto que debe resolverse antes de activar `sec_press_releases`:

- La FAQ de SEC Webmaster menciona un máximo de 10 solicitudes por segundo para acceso programático a **EDGAR**. La documentación consultada no permite atribuir automáticamente ese mismo límite al feed RSS `https://www.sec.gov/news/pressreleases.rss`.
- La entrada actual `sec_press_releases` de `scripts/market_selection/event_source_registry.py` declara `max_requests_per_second: 10`. Aunque el origen permanece `TERMS_PENDING` y el acceso está bloqueado, ese valor no debe presentarse como una condición oficial específica del RSS sin evidencia adicional.
- Antes de aprobar la fuente, la matriz debe distinguir explícitamente: (a) límite oficial aplicable al endpoint exacto, cuando esté documentado; (b) límite interno conservador elegido por el proyecto, identificado como política propia; y (c) límite agregado efectivo del despliegue. No usar el valor de EDGAR como sustituto de los otros dos.
- No se debe activar la fuente ni aumentar la frecuencia de solicitudes a partir de esta observación. Si no se encuentra una regla específica para el RSS, documentar la incertidumbre y elegir una política operativa conservadora explícitamente etiquetada como interna, tras completar la revisión de acceso.
- Este hallazgo es documental y preventivo: no se modificó el registro operativo ni se hizo tráfico externo.

**Criterio pendiente para `sec_press_releases`:** resolver la procedencia del límite configurado, actualizar la documentación o el registro cuando corresponda, y probar el control agregado solo tras la aprobación individual de la fuente.