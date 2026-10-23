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
