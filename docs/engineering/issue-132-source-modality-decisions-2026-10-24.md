# Decisiones de uso por fuente y modalidad — Issue #132

- **Fecha de evaluación:** 2026-10-24.
- **Alcance:** las seis entradas actuales del registro `event_source_registry.py`.
- **Tipo de decisión:** decisión operativa conservadora basada en la evidencia de política preservada; no es asesoría legal ni una autorización concedida por el proveedor.
- **Regla aplicada:** no se declara permitido un uso si la evidencia no resuelve ese uso concreto. Los estados de runtime permanecen `TERMS_PENDING` hasta que el expediente exigido por el registro esté completo y sea consistente.

## 1. Decisión ejecutiva

Las páginas oficiales verificadas permiten concluir, con límites, que el contenido gubernamental/oficial puede reutilizarse con atribución en los términos generales publicados por SEC, CFTC y Federal Reserve Board. **No permiten convertir automáticamente esa conclusión en permiso operativo para cualquier captura automatizada, persistencia de respuestas completas, HTML íntegro, adjuntos o materiales de terceros.**

Por tanto, para las seis fuentes, la decisión actual es:

- **No habilitar captura de red ni backfill en producción todavía.** Falta un expediente operativo completo y coincidente con el esquema `approval_scope` del repositorio.
- **Contenido oficial:** reutilización con atribución es respaldada en términos generales por las políticas capturadas, pero su ingestión automatizada persistente queda pendiente de resolver las condiciones del endpoint y la retención exacta.
- **Metadatos mínimos (URL, título, fecha de publicación, identificador de feed y hash del registro):** modalidad candidata preferida para la primera activación; no se activa hasta que se complete el registro por fuente y se confirme el acceso automatizado.
- **Texto oficial completo, HTML completo y adjuntos:** no aprobados para persistencia en esta decisión. Requieren una justificación y una decisión de alcance separadas; excluir contenido de terceros salvo evidencia de permiso.
- **Contenido de terceros:** excluirlo de captura/persistencia salvo permiso específico verificable.
- **Redistribución/republicación:** no aprobada por el proyecto. Enlaces y atribución no equivalen a permiso de redistribuir todo el cuerpo.
- **Retención indefinida:** no aprobada. No se inventa un plazo: la duración debe definirse expresamente antes de habilitar persistencia.

Estos son veredictos operativos conservadores, no afirmaciones de que el proveedor prohíba esos usos. La diferencia es importante: **“no aprobado por este expediente” no significa “ilegal” ni “prohibido por el proveedor”.**

## 2. Matriz transversal de modalidades

| Modalidad | Decisión operativa actual | Evidencia / razón | Condición para reconsiderar |
|---|---|---|---|
| Lectura automatizada de feed RSS | **BLOQUEADA hasta revisión del endpoint** | Política general no resuelve todas las condiciones del endpoint; CFTC RSS figura deshabilitado en octubre de 2026 | Confirmar disponibilidad, política aplicable al endpoint, User-Agent, cuota agregada y autorización registrada |
| Lectura automatizada de índice HTML histórico | **BLOQUEADA hasta revisión del endpoint** | Cada archivo es una fuente independiente de su feed y tiene paginación/cobertura propia | Validar host/ruta, acceso automatizado, redirecciones, frecuencia y segmentos de alcance |
| Almacenamiento de metadatos mínimos | **CANDIDATA; no habilitada** | Menor exposición que almacenar el cuerpo completo, pero la persistencia aún debe declararse y aprobarse en el registro | Enumerar campos, finalidad, duración y regla de eliminación/revisión; hash de política y autorización coincidentes |
| Almacenamiento del texto oficial íntegro | **NO APROBADO en el alcance actual** | Las políticas respaldan reutilización general del contenido oficial, pero el expediente no delimita aún captura y retención de texto completo por endpoint | Decisión específica documentada, atribución y retención definida |
| Almacenamiento de HTML completo | **NO APROBADO** | El HTML puede contener material de terceros, scripts, imágenes, marcas y otros recursos cuyo régimen no se deduce de la política general | Revisión de contenido, exclusiones y justificación de bytes completos; permiso aplicable cuando corresponda |
| Descarga/almacenamiento de adjuntos | **NO APROBADO** | No se ha verificado individualmente titularidad/licencia de cada adjunto | Permiso verificable por recurso o exclusión estricta |
| Contenido de terceros incrustado o enlazado | **EXCLUIDO por defecto** | Las tres instituciones advierten que ciertos materiales pueden pertenecer a terceros | Evidencia específica de permiso; no basta con que el recurso esté alojado/enlazado en el dominio oficial |
| Análisis interno de hechos oficiales | **CONDICIONAL; no habilitado por runtime** | El uso general de información oficial está respaldado, pero debe ligarse a la fuente/endpoint y al contenido realmente capturado | Aprobar `internal_analysis` para esa entrada y documentar atribución, contenido y acceso |
| Persistencia para investigación histórica | **PENDIENTE; no habilitada** | Necesita campos, duración y eliminación/revisión explícitos; no hay autorización para retención indefinida | Aprobar `persistent_storage` y reglas de retención concretas |
| Redistribución de cuerpos o adjuntos | **NO APROBADA** | El proyecto no cuenta con autorización específica para republicar el corpus | Evaluación independiente de derechos y licencia aplicable |
| Backfill histórico | **BLOQUEADO** | No debe iniciarse sin alcance aprobado y acceso válido; el feed actual no equivale a archivo completo | Activar únicamente segmentos permitidos, con manifiesto de páginas esperadas/capturadas/ausentes y hashes |

## 3. Decisión individual por fuente

### 3.1 SEC — RSS de comunicados

- **ID:** `sec_press_releases`
- **Endpoint registrado:** https://www.sec.gov/news/pressreleases.rss
- **Política de acceso:** https://www.sec.gov/about/developer-resources
- **Evidencia general de reutilización:** https://www.sec.gov/about/privacy-information
- **Decisión:** `TERMS_PENDING`; no realizar solicitudes desde el adaptador.
- **Metadatos mínimos:** candidata, no activada.
- **Texto oficial:** reutilización general respaldada con atribución, pero la ingestión/persistencia de este feed no queda activada hasta resolver las condiciones del endpoint.
- **HTML completo y adjuntos:** no aprobados; excluir material de terceros.
- **Automatización:** usar agente identificable y limitador agregado. La documentación SEC capturada indica un máximo de 10 solicitudes por segundo para SEC.gov y restricciones sobre bots/herramientas automatizadas no clasificadas. No asumir que ese máximo autoriza al proyecto ni trasladarlo sin revisión a cualquier servicio. El limitador de despliegue debe coordinar todos los procesos que compartan la cuota.
- **Retención:** sin duración aprobada; prohibido inferir retención indefinida.
- **Condición para activar:** aclarar aplicabilidad de la política de automatización al endpoint RSS, completar agente/limitador/topología, aprobar campos y duración de persistencia y generar registro de autorización con hashes coincidentes.

### 3.2 SEC — archivo HTML histórico de comunicados

- **ID:** `sec_press_release_archive`
- **Endpoint registrado:** https://www.sec.gov/newsroom/press-releases
- **Política de acceso:** https://www.sec.gov/about/developer-resources
- **Decisión:** `TERMS_PENDING`; no realizar solicitudes desde el adaptador.
- **Metadatos mínimos:** candidata, no activada.
- **Texto oficial:** reutilización general respaldada con atribución, pendiente de alcance de captura automatizada y retención para esta modalidad.
- **HTML completo y adjuntos:** no aprobados; excluir recursos de terceros.
- **Automatización/cobertura:** limitarse a prefijos permitidos; cada página, año y paginación debe registrarse por separado. No afirmar exhaustividad del archivo por capturar una página.
- **Retención:** sin duración aprobada.
- **Condición para activar:** expediente de autorización independiente del RSS, alcance de páginas y paginación, cuota agregada, retención, atribución y validación de redirecciones.

### 3.3 CFTC — RSS general de comunicados

- **ID:** `cftc_general_press_releases`
- **Endpoint registrado:** https://www.cftc.gov/RSS/RSSGP/rssgp.xml
- **Política:** https://www.cftc.gov/WebPolicy/index.htm
- **Estado observado:** la página oficial https://www.cftc.gov/RSS/index.htm indicaba en octubre de 2026 que todos los feeds RSS estaban temporalmente deshabilitados.
- **Decisión:** `TERMS_PENDING` y **sin solicitudes de sondeo/reintentos mientras siga vigente el aviso oficial de deshabilitación**.
- **Metadatos, texto, HTML, adjuntos y retención:** no habilitados para esta modalidad.
- **Razón:** además de la decisión de copyright/atribución, el endpoint no está disponible según el aviso oficial capturado. No se debe interpretar una falla o un feed vacío como ausencia de eventos.
- **Condición para reconsiderar:** comprobar que el aviso oficial cambió y que el endpoint está disponible; luego completar el expediente específico del feed. No heredar automáticamente aprobación desde el archivo HTML.

### 3.4 CFTC — archivo HTML histórico de comunicados

- **ID:** `cftc_press_release_archive`
- **Endpoint registrado:** https://www.cftc.gov/PressRoom/PressReleases
- **Política:** https://www.cftc.gov/WebPolicy/index.htm
- **Decisión:** `TERMS_PENDING`; no realizar solicitudes desde el adaptador.
- **Contenido oficial:** la política CFTC indica que información gubernamental puede copiarse con atribución; esto no elimina las excepciones de terceros ni aprueba por sí solo toda modalidad de captura persistente.
- **Metadatos mínimos:** candidata, no activada.
- **HTML completo, adjuntos y terceros:** no aprobados; excluir terceros.
- **Automatización/cobertura:** archivo HTML independiente del RSS deshabilitado. Solo prefijos/rutas permitidos; capturar y manifestar páginas por segmento, sin declarar exhaustividad global.
- **Retención:** sin duración aprobada.
- **Condición para activar:** expediente específico para HTML, endpoint disponible, cuota agregada interna conservadora, atribución, campos/duración de retención y reglas de retirada/corrección.

### 3.5 Federal Reserve Board — RSS de comunicados

- **ID:** `federal_reserve_press_releases`
- **Endpoint registrado:** https://www.federalreserve.gov/feeds/press_all.xml
- **Política:** https://www.federalreserve.gov/disclaimer.htm
- **Índice RSS oficial:** https://www.federalreserve.gov/feeds/feeds.htm
- **Decisión:** `TERMS_PENDING`; no realizar solicitudes desde el adaptador.
- **Contenido del Board:** el disclaimer permite, salvo indicación contraria, copiar/distribuir información del Board con atribución; no equivale a autorización global de persistencia automatizada de cada respuesta o recurso enlazado.
- **Metadatos mínimos:** candidata, no activada.
- **Texto oficial:** uso general con atribución respaldado, pero persistencia de feed pendiente.
- **HTML completo, adjuntos y materiales de terceros:** no aprobados; excluir terceros salvo permiso comprobado.
- **Retención:** sin duración aprobada.
- **Condición para activar:** definir campos/duración, confirmar alcance de automatización para el feed, agente, cuota, atribución y registro de autorización coincidente.

### 3.6 Federal Reserve Board — archivo HTML histórico

- **ID:** `federal_reserve_press_release_archive`
- **Endpoint registrado:** https://www.federalreserve.gov/newsevents/pressreleases.htm
- **Política:** https://www.federalreserve.gov/disclaimer.htm
- **Decisión:** `TERMS_PENDING`; no realizar solicitudes desde el adaptador.
- **Contenido oficial:** reutilización general con atribución respaldada, sujeta a indicaciones contrarias y exclusión de material de terceros.
- **Metadatos mínimos:** candidata, no activada.
- **HTML completo, adjuntos y terceros:** no aprobados.
- **Automatización/cobertura:** archivo por año/segmento; cada página capturada necesita su propio URL, timestamp, bytes y SHA-256. No asumir que el índice cubre todo el histórico.
- **Retención:** sin duración aprobada.
- **Condición para activar:** expediente independiente del RSS, segmentación histórica declarada, política de redirecciones, atribución, retención y autorización estructurada.

## 4. Campos de retención que deben definirse antes de habilitar persistencia

No se establece aquí una duración arbitraria. El expediente operativo debe decidir, por fuente:

1. Qué metadatos se conservan (por ejemplo, identificador de fuente, URL, título, fecha de publicación, hora UTC de captura, código HTTP, tamaño, hash, estado y referencia a evidencia).
2. Si se conserva el texto oficial, y si el contenido original completo se almacena solo temporalmente para verificación.
3. La duración concreta para cada categoría y su justificación funcional.
4. El evento que inicia la retención (captura, publicación, revisión o última verificación).
5. La regla de eliminación o revisión cuando expiren los términos, se retire/corrija el contenido o se detecte material de terceros.
6. Si las copias de respaldo, artefactos de CI y exportaciones quedan sujetas a la misma política.
7. Cómo se demuestra la eliminación/revisión sin conservar indebidamente el contenido que debía eliminarse.

Hasta que esos campos estén definidos, `persistent_storage` debe permanecer sin aprobar. Un hash o un enlace no sustituyen una política de retención, y guardar bytes en un artefacto temporal no equivale a autorización para conservarlos indefinidamente.

## 5. Controles técnicos mínimos antes de activar una fuente

- El registro, la política preservada y la autorización del proveedor deben coincidir en `source_id`, URL de términos, hash, casos de uso y alcance.
- No rellenar `reviewed_by`, `reviewed_at`, hash de términos o evidencia con datos ficticios.
- No cambiar a `APPROVED` únicamente porque una política general permita reutilizar información oficial.
- Fallar cerrado antes de la red si fuente, uso, User-Agent, autorización, host o alcance no cumplen.
- Coordinar las cuotas entre todos los procesos/hosts que compartan el proveedor; un limitador SQLite local no coordina hosts con bases separadas.
- Respetar los endpoints deshabilitados y no convertir DNS, timeout, 403, 429, HTTP 5xx o respuesta parcial en una captura válida.
- Registrar atribución y procedencia; no redistribuir contenido fuente por defecto.
- Separar captura, verificación factual, resolución de entidad, asociación temporal y conclusión causal.

## 6. Evidencia preservada y limitaciones

El workflow de políticas [run 40045854045](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40045854045) obtuvo HTTP 200 para siete páginas oficiales y se verificaron los tamaños/SHA-256 de sus cuerpos contra el manifiesto. Los detalles y hashes se registran en `issue-132-source-approval-matrix.md`.

Esto prueba la integridad de las capturas de política en ese artefacto; no prueba permiso legal para cualquier modalidad, disponibilidad actual de feeds, captura de noticias, retención permanente ni backfill histórico. El artefacto original tenía retención temporal de siete días.

## 7. Criterio de salida

Esta matriz **completa las decisiones operativas conservadoras para las seis fuentes y las modalidades solicitadas**, pero no habilita ninguna fuente. El estado de runtime permanece pendiente deliberadamente.

Para aprobar una entrada concreta hacen falta, como mínimo, una revisión autorizada con identidad/fecha reales, bytes y hash de la política, `approval_scope` completo (contenido, terceros, retención, atribución, acceso, limitaciones), autorización del proveedor coincidente y validación del adaptador. Tras esa aprobación se puede realizar una captura real de alcance acotado y documentar su resultado. No se debe cerrar el Issue #132 hasta que exista evidencia E2E real autorizada y un manifiesto reproducible del backfill declarado.
