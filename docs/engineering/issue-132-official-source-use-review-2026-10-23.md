# Issue #132 — Revisión individual de políticas de fuentes oficiales

- Fecha de revisión técnica: 2026-10-23.
- Responsable de la revisión técnica: revisión asistida por IA para el repositorio; no constituye dictamen jurídico ni suplanta la aceptación del operador.
- Objetivo: delimitar el uso admisible por fuente y modalidad, sin trasladar permisos entre endpoints.

## Reserva Federal — archivo histórico HTML

**Fuente:** https://www.federalreserve.gov/newsevents/pressreleases.htm  
**Política:** https://www.federalreserve.gov/disclaimer.htm  
**Evidencia preservada:** artefacto de GitHub Actions `issue-132-source-policy-snapshots`, ejecución [40049674222](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40049674222), archivo `federal_reserve_disclaimer.html`, 87 235 bytes, SHA-256 `35cb213dbcdb4b34656faf7be98f277117321fcc46268f24bcd738adbdb69f88`.

La política indica que, salvo indicación contraria, la información del Board es de dominio público y puede copiarse y distribuirse sin permiso, citando al Board. Excluye o condiciona material de terceros, fotografías/gráficos identificados como ajenos, sellos/logotipos y material de sitios externos. Fuente pública: https://www.federalreserve.gov/disclaimer.htm.

### Decisión técnica de alcance

- **Candidato admisible para implementación:** metadatos bibliográficos (URL canónica, título, fecha de publicación, fecha de captura, estado HTTP, tamaño y SHA-256 de la respuesta), más texto del comunicado atribuido al Board.
- **Excluir de la persistencia de contenido:** imágenes, gráficos, logotipos/sellos, recursos externos y bloques identificados como material de terceros. Mantener URL de origen para que el lector consulte la publicación oficial.
- **No habilitar todavía la captura de archivo:** la implementación actual conserva el cuerpo HTML íntegro en `raw_response_base64`; eso no aplica la exclusión anterior. El código debe persistir una representación extraída y verificable, conservando el hash/tamaño de la respuesta completa sin conservar el HTML íntegro, antes de que esta modalidad pueda considerarse operativamente aprobada.
- **RSS de la Reserva Federal:** evaluación separada. La política de la página no se hereda automáticamente al endpoint RSS; no habilitarlo por la decisión del archivo.
- **Usos previstos para el diseño:** análisis interno y almacenamiento persistente de metadatos/texto oficial extraído con atribución. No autorizar redistribución del HTML original ni publicación del contenido completo por este registro.
- **Atribución propuesta:** “Fuente: Board of Governors of the Federal Reserve System”, junto con el enlace canónico del comunicado.
- **Estado operativo:** `TERMS_PENDING` hasta que se implemente y pruebe la persistencia de contenido limitado y se incorpore un registro de autorización compatible con el alcance.

## SEC — RSS y archivo histórico

**Política revisada:** https://www.sec.gov/about/developer-resources  
**Evidencia preservada:** la misma ejecución [40049674222](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40049674222), `sec_developer_resources.html`, 68 806 bytes, SHA-256 `b67bc3adda13b6f26c9acc3f7afad3ba4d08db20e5a7692345f5c461966a9765`.

La página documenta recursos para desarrolladores y directrices de acceso justo: solicitudes eficientes, tasa agregada no superior a 10 solicitudes por segundo y prohibición de rastreadores automatizados no clasificados. Esto no es por sí solo una licencia general de almacenamiento persistente del contenido de todas las publicaciones.

- Mantener RSS y archivo como fuentes separadas.
- Exigir User-Agent identificable y revisado, límites de solicitud, respeto de respuestas de bloqueo y alcance explícito.
- Antes de habilitar persistencia, registrar el alcance de contenido y la base de autorización específica; no inferir permiso de redistribución a partir de la página para desarrolladores.
- Estado operativo: `TERMS_PENDING`.

## CFTC — RSS y archivo histórico

**Política:** https://www.cftc.gov/WebPolicy/index.htm  
**Estado RSS:** https://www.cftc.gov/RSS/index.htm  
**Evidencia preservada:** ejecución [40049674222](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40049674222), `cftc_web_policy.html`, 47 429 bytes, SHA-256 `a5b839deafb52509bf6505d47bf86a55e79c73b236e8bed7f8c8dfa36ab6cacf`; `cftc_rss_status.html`, 32 770 bytes, SHA-256 `0ef951990ad242235c67640aeb76355d9173d1b9be8dda6d04b684c7b3110e86`.

La política de la CFTC indica que la información gubernamental de su sitio es de dominio público y puede copiarse y distribuirse con reconocimiento apropiado. También advierte que documentos, ilustraciones, fotografías u otros recursos aportados/licenciados por terceros pueden estar protegidos. El aviso de estado del RSS debe comprobarse en cada ejecución; una página de estado que indica deshabilitación no debe ser sondeada.

- Mantener RSS y archivo separados; no intentar el RSS mientras la CFTC lo declare deshabilitado.
- Para el archivo, limitar la captura persistente al texto oficial y metadatos, excluyendo recursos de terceros, sellos/logotipos y material externo.
- Registrar atribución, endpoint, política preservada y alcance de almacenamiento; la política general no autoriza por sí sola cualquier artefacto mixto.
- Estado operativo: `TERMS_PENDING` hasta implementar y probar la persistencia limitada y validar el acceso al endpoint.

## Requisitos técnicos comunes para cerrar la revisión

1. Capturar la respuesta hasta EOF sin límite local arbitrario; registrar tamaño real y SHA-256 de los bytes de respuesta.
2. Persistir por separado solo la representación textual/metadata autorizada y su hash; no persistir el HTML íntegro en las fuentes que requieran exclusión de terceros.
3. Validar redirecciones, host y ruta permitidos, HTTP 200, lectura completa, tipo de contenido, integridad de los artefactos y atribución.
4. Hacer coincidir el registro de autorización con `source_id`, URL de política, SHA-256, fecha, responsable y usos concretos.
5. Mantener `TERMS_PENDING` mientras el capturador conserve contenido más amplio que el alcance revisado. Una prueba sintética o un hash de política no son por sí solos una autorización.
6. No afirmar captura real, integración real ni backfill completo hasta ejecutar la cadena con un artículo histórico real y artefactos verificables.

## Fuentes oficiales consultadas

- Federal Reserve Board, Disclaimer: https://www.federalreserve.gov/disclaimer.htm
- SEC, Developer Resources: https://www.sec.gov/about/developer-resources
- CFTC, Web Policy: https://www.cftc.gov/WebPolicy/index.htm
- CFTC, RSS status: https://www.cftc.gov/RSS/index.htm
