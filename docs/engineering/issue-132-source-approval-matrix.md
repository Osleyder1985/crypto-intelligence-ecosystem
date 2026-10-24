# Matriz de decisión de uso por fuente — Issue #132

- **Estado:** plantilla de decisión; no constituye autorización ni dictamen jurídico.
- **Fecha de preparación:** 2026-10-23.
- **Issue relacionado:** [#132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132).
- **Registro técnico:** [event_source_registry.py](../../scripts/market_selection/event_source_registry.py).
- **Políticas revisadas:** [SEC](https://www.sec.gov/about/privacy-information), [SEC Developer Resources](https://www.sec.gov/about/developer-resources), [CFTC Web Policy](https://www.cftc.gov/WebPolicy/index.htm), [Federal Reserve Disclaimer](https://www.federalreserve.gov/disclaimer.htm).

## Propósito

Convertir la revisión de políticas en una decisión operativa explícita y auditable. Que un sitio permita reutilizar determinada información oficial no significa que todo elemento embebido sea reutilizable, que cualquier método de acceso automatizado esté permitido o que se haya aprobado la retención indefinida de respuestas completas.

**Regla por defecto:** si una decisión requerida no está documentada, el origen permanece `TERMS_PENDING`, no se realiza tráfico y el informe debe reflejar el bloqueo como limitación de cobertura.

## Decisiones requeridas por origen

Completar un registro independiente para cada `source_id`, tanto para feeds como para índices de archivo. La aprobación de un feed no aprueba automáticamente su archivo HTML ni viceversa.

| Decisión | Valores que deben quedar documentados |
|---|---|
| Finalidad | `internal_analysis`; otras finalidades deben identificarse y justificarse por separado |
| Contenido capturado | Metadatos mínimos; texto del comunicado oficial; HTML completo; recursos adjuntos; cada categoría se decide separadamente |
| Contenido de terceros | Excluido, aislado sin persistencia o autorizado con evidencia específica; no asumir autorización por estar alojado en el dominio oficial |
| Persistencia | Qué campos y bytes se guardan, por qué son necesarios y por cuánto tiempo |
| Reproducción y distribución | No distribuir contenido fuente salvo que exista autorización documentada para ello |
| Atribución | Formato de atribución y enlace de origen que acompañarán a cada registro |
| Acceso automatizado | Endpoint oficial, agente identificable, límite de solicitudes, timeout, redirecciones permitidas y controles agregados entre procesos y límites de topología |
| Integridad | SHA-256, tamaño, fecha/hora UTC de captura, código HTTP y bytes originales cuando la retención esté autorizada |
| Retirada/corrección | Cómo se registra una corrección, retirada, restricción nueva o solicitud de eliminación |
| Responsable y evidencia | Identidad del responsable, fecha UTC, URL de política revisada, copia preservada de la política y SHA-256 |
| Decisión final | `APPROVED`, `TERMS_PENDING`, `SUSPENDED` o `REJECTED`, con justificación y alcance exactos |

No usar una casilla genérica de “términos revisados” como sustituto de las decisiones sobre contenido, retención y finalidad.

## Inventario de orígenes pendientes

| `source_id` | Contenido/alcance | Observaciones para la revisión | Estado actual |
|---|---|---|---|
| `sec_press_releases` | Feed RSS actual | Confirmar el agente y el control agregado de solicitudes; documentar si todas las invocaciones compartirán el mismo ledger local. El RSS no representa el archivo completo. Separar metadatos, texto oficial y HTML completo. | `TERMS_PENDING` |
| `sec_press_release_archive` | Índice histórico SEC | Limitar rutas al prefijo permitido; registrar cada página/segmento y no tratar recursos de terceros como contenido oficial. | `TERMS_PENDING` |
| `cftc_general_press_releases` | Feed RSS actual | Verificar disponibilidad del endpoint antes de planificar captura; no asumir que el RSS está operativo. | `TERMS_PENDING` |
| `cftc_press_release_archive` | Índice histórico CFTC | Capturar únicamente páginas oficiales dentro de la allowlist; excluir la sección de cobertura mediática del adaptador de comunicados. | `TERMS_PENDING` |
| `federal_reserve_press_releases` | Feed RSS actual | Diferenciar comunicados del Board y materiales de terceros; el feed macroeconómico no es una fuente cripto exhaustiva. | `TERMS_PENDING` |
| `federal_reserve_press_release_archive` | Índice histórico del Board | Registrar segmentos/años por separado; distinguir contenido del Board de fotografías, gráficos u otros recursos de terceros. | `TERMS_PENDING` |

Los estados anteriores reflejan el registro de código consultado el 2026-10-23; no significan que se haya solicitado o concedido autorización externa.

## Registro de decisión — copiar y completar por fuente

```yaml
source_id: "<id exacto del registro>"
decision: "TERMS_PENDING"
decision_at: null
reviewed_by: null
policy_urls:
  - "<URL oficial revisada>"
policy_snapshot_sha256: null
allowed_use_cases: []
allowed_content:
  metadata: null
  official_text: null
  full_html: null
  attachments: null
third_party_content:
  handling: null
  evidence: null
retention:
  stored_fields: []
  duration: null
  deletion_or_recheck_rule: null
attribution:
  required: null
  format: null
automated_access:
  approved_endpoint: null
  user_agent: null
  max_aggregate_requests_per_second: null
  timeout_seconds: null
  redirect_policy: null
limitations: []
decision_rationale: null
```

Los campos `null`, las listas vacías y los valores de ejemplo no son autorizaciones. No copiar el registro a producción ni cambiar el estado a `APPROVED` hasta que las decisiones estén completas y la evidencia de política esté preservada y validada.

## Validación obligatoria del alcance aprobado

El estado APPROVED del registro técnico exige un objeto approval_scope completo, además del hash y los bytes de la política revisada. Debe declarar explícitamente:

- decisiones booleanas separadas para metadatos, texto oficial, HTML completo y adjuntos;
- tratamiento del contenido de terceros y evidencia cuando se autorice;
- campos persistidos, duración de retención y regla de eliminación/revisión;
- atribución requerida y formato;
- endpoint HTTPS cuyo host pertenezca a la lista permitida, agente de usuario, límite agregado por segundo no superior al límite del registro, timeout positivo y política de redirecciones;
- limitaciones conocidas y justificación de la decisión.

Las pruebas usan únicamente una decisión sintética marcada como fixture. No modifica ni autoriza ninguna de las fuentes reales pendientes. Esta validación comprueba que la decisión está estructuralmente completa; no sustituye una revisión de términos ni garantiza que la decisión sea jurídicamente correcta.

## Condiciones técnicas antes de activar una fuente

1. La entrada del registro, el registro de autorización del proveedor y la evidencia de política deben coincidir en `source_id`, finalidad y alcance.
2. La captura debe fallar cerrada antes de la red cuando el origen o cualquiera de los usos requeridos no esté aprobado.
3. La allowlist de host y rutas debe ser específica para cada feed/archivo; validar también cada redirección.
4. El control de frecuencia debe ser agregado en la topología real de despliegue. La implementación actual coordina procesos del mismo usuario y host que comparten una base SQLite; no coordina varios hosts ni usuarios con bases distintas. Si la fuente se captura desde varios hosts, se debe aportar un coordinador compartido antes de activar ese despliegue. Un límite por invocación no es por sí solo un limitador agregado.
5. El informe debe diferenciar `BLOCKED_BY_SOURCE_POLICY`, `UNAVAILABLE`, `PARTIAL_OR_FAILED` y una captura correcta sin entradas. Ninguno de estos estados permite afirmar que no ocurrió un evento.
6. Solo después de documentar la decisión se podrá planificar una prueba real de alcance reducido. Preservar la solicitud, la respuesta, los hashes, las decisiones de identidad y la cobertura obtenida, sin afirmar exhaustividad más allá del alcance declarado.

## Criterio de cierre de esta preparación

La matriz documental puede considerarse preparada cuando está versionada. **Issue #132 no se considera terminado** hasta que exista una decisión de uso por cada fuente que se vaya a activar, una prueba E2E con evidencia real autorizada y un manifiesto de backfill reproducible. Las fuentes que no tengan autorización permanecen deshabilitadas; no es necesario activarlas todas para cerrar el trabajo funcional si se delimita y verifica un alcance autorizado suficiente.


## 2026-10-24 — resultado verificable de captura de páginas de política

El workflow [Capturar evidencia de políticas oficiales — Issue 132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40045854045) terminó correctamente. El artefacto `issue-132-source-policy-snapshots` contiene los siete cuerpos de respuesta y `manifest.json`; el ZIP fue descargado y se recalculó SHA-256 sobre cada cuerpo, coincidiendo en los siete casos con el manifiesto.

| ID de evidencia | HTTP | Bytes | SHA-256 |
|---|---:|---:|---|
| `sec_website_dissemination` | 200 | 90776 | `56d226ad907d9b431ed17d353cd03b709d324daa2040a19fe34503deeb0a8b74` |
| `sec_developer_resources` | 200 | 68809 | `dd9db5c0ae91a46cb72d79e36c7a6317fc03aacabf4a2d27a54da62bfd5432f6` |
| `sec_rss_feeds` | 200 | 65725 | `0e8f0348f2f138442121db635a6111f1074d748663dbbbc0a8620eea7c95df7f` |
| `cftc_web_policy` | 200 | 47429 | `a0a6faaeeac3ecfb7a81dfe83f145231966454590bede365d5873d64292d5f6d` |
| `cftc_rss_status` | 200 | 32770 | `2cdf6b74d28b883962b94cf0d0009c7b8b929075874c79ff87ced72231586a6d` |
| `federal_reserve_disclaimer` | 200 | 87235 | `8c60de635af28464eeed9bd339313502f1da29b9f3376d9739426ee5351c2f86` |
| `federal_reserve_rss_feeds` | 200 | 92134 | `4f0aa870b1d6837fba1a2d8beb8bf493fb7386b7eed7dbf5dfa618aa8d5579a8` |

El artefacto es temporal y tiene retención de siete días; esta tabla permite comprobar integridad, pero no sustituye la preservación durable que se exija para el expediente final. No se ha cambiado ningún estado de autorización.

### Lectura operativa preliminar de la evidencia

- **SEC:** la página de diseminación declara que la información presentada en sec.gov es pública y puede copiarse/distribuirse sin permiso de SEC, con cita apropiada. La documentación para desarrolladores fija un máximo total de 10 solicitudes por segundo para acceso a SEC.gov y advierte que no permite bots no clasificados. El registro debe exigir User-Agent identificable y un limitador conservador compartido; no extrapolar sin revisión adicional el límite a servicios o dominios distintos.
- **CFTC:** la Web Policy declara que la información gubernamental es de dominio público y puede copiarse con atribución, y advierte sobre recursos protegidos de terceros. La página RSS capturada dice que todos los feeds están temporalmente deshabilitados en octubre de 2026. No intentar el feed deshabilitado; evaluar el archivo HTML como origen separado y confirmar sus condiciones antes de capturarlo.
- **Federal Reserve Board:** el disclaimer indica que la información del Board, salvo indicación contraria, es de dominio público y puede copiarse/distribuirse con atribución; fotos, gráficos y materiales identificados como pertenecientes a terceros requieren tratamiento separado. La página RSS explica el uso de lectores/agregadores, pero eso por sí solo no resuelve retención automatizada ilimitada ni el tratamiento de todos los recursos enlazados.

**Conclusión de esta revisión técnica:** la evidencia observada apoya la reutilización de contenido oficial en términos generales en las tres instituciones, con condiciones específicas de acceso y atribución. No equivale a aprobación global de HTML completo, adjuntos, contenido de terceros, retención indefinida o backfill ilimitado. Esas decisiones deben quedar acotadas en `approval_scope` por cada `source_id` antes de activar la modalidad correspondiente. Los estados permanecen `TERMS_PENDING`.


## Alcance funcional multifuente y estado operativo

El objetivo funcional es evaluar las seis fuentes registradas como candidatas para investigar noticias y eventos relacionados con movimientos del mercado cripto. Ese alcance no debe reducirse a un piloto único por defecto. La priorización de implementación puede organizar el trabajo, pero no limita el alcance final solicitado.

La autorización para continuar el desarrollo no debe confundirse con una autorización específica para acceder, capturar, persistir o redistribuir contenido de una fuente concreta. No se atribuirá al propietario una aprobación individual de SEC, CFTC o Federal Reserve que no haya declarado expresamente. La decisión de activar cada modalidad se documenta por fuente con evidencia oficial, disponibilidad y controles técnicos verificables.

- Mantener cada origen en `TERMS_PENDING` mientras falten las condiciones operativas documentadas para su modalidad.
- No consultar los feeds de CFTC mientras el aviso oficial indique que están deshabilitados; el archivo HTML es un origen separado.
- No inferir permiso para conservar indefinidamente HTML, adjuntos o contenido de terceros a partir de una política general de reutilización.
- No inferir causalidad entre un evento y un movimiento de precio solo por proximidad temporal.
