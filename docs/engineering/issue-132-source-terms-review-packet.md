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

| ID de fuente | Endpoint de feed | Página de condiciones/políticas registrada | Estado |
| --- | --- | --- | --- |
| `sec_press_releases` | https://www.sec.gov/news/pressreleases.rss | https://www.sec.gov/about/developer-resources | `TERMS_PENDING` |
| `cftc_general_press_releases` | https://www.cftc.gov/RSS/RSSGP/rssgp.xml | https://www.cftc.gov/sites/default/files/cftc/cftcprivacy.htm | `TERMS_PENDING` |
| `federal_reserve_press_releases` | https://www.federalreserve.gov/feeds/press_all.xml | https://www.federalreserve.gov/policies.htm | `TERMS_PENDING` |

Los enlaces son los actualmente declarados en `scripts/market_selection/event_source_registry.py`. Si la autoridad publica una política específica para RSS, APIs o reutilización de contenido, inclúyase como evidencia adicional; no se debe asumir que la página genérica registrada resuelve todas las cuestiones.

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
- Conclusión de esta revisión: se confirma que SEC publica recursos RSS y pautas de acceso automatizado; no se ha completado una decisión específica sobre análisis interno, almacenamiento persistente, retención y reutilización del contenido del feed configurado. Mantener `TERMS_PENDING`.

### CFTC

- La página oficial de [RSS](https://www.cftc.gov/RSS/index.htm), consultada el 23 de octubre de 2026, declara explícitamente: **“As of October 2026, the CFTC has temporarily disabled all RSS feeds”** para los temas enumerados, y que se volverán a habilitar más adelante.
- La [Web Policy de CFTC](https://www.cftc.gov/WebPolicy/index.htm) indica que la información gubernamental del sitio es de dominio público y puede copiarse/distribuirse con atribución adecuada; advierte que algunos documentos, imágenes u otros recursos pueden ser de terceros y estar protegidos.
- Conclusión operativa: el feed RSS registrado no debe considerarse disponible mientras la página oficial mantenga ese aviso. Esto es un problema de disponibilidad, independiente de los términos. No activar solicitudes repetidas ni sustituir silenciosamente el endpoint. Mantener `TERMS_PENDING` y volver a comprobar el aviso antes de cualquier prueba autorizada futura.

### Federal Reserve Board

- La página oficial de [RSS Feeds](https://www.federalreserve.gov/feeds/feeds.htm) enumera feeds de comunicados, discursos, datos y publicaciones; explica el uso mediante lectores/agregadores RSS. La página indica última actualización el 16 de septiembre de 2025.
- La página enlazada por el registro como política general no resuelve por sí sola, en la evidencia consultada, todos los casos de uso concretos: captura automatizada del feed, almacenamiento persistente de cuerpos completos, duración de retención, extractos y redistribución.
- Conclusión de esta revisión: se confirma la documentación oficial de feeds, pero el permiso para los casos de uso del proyecto sigue sin quedar demostrado. Mantener `TERMS_PENDING` hasta revisar la política aplicable al Board y cualquier condición específica del contenido.

### Resultado consolidado

| Fuente | Hecho confirmado | Pendiente | Estado del registro |
| --- | --- | --- | --- |
| SEC | Página oficial de RSS y pautas de acceso automatizado disponibles | Alcance concreto de almacenamiento, retención y reutilización del feed registrado | `TERMS_PENDING` |
| CFTC | La página oficial indica que los feeds RSS están temporalmente deshabilitados en octubre de 2026 | Disponibilidad futura y revisión de usos permitidos | `TERMS_PENDING` |
| Federal Reserve Board | Página oficial de feeds y guía de uso mediante agregadores | Permisos concretos para captura y persistencia del contenido del feed | `TERMS_PENDING` |

**No se cambió el registro de fuentes, no se capturaron feeds y no se habilitó tráfico de red.** La conclusión es documental y preliminar; el revisor humano autorizado debe completar el checklist y registrar la evidencia de términos antes de aprobar cualquier uso.
