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
| Acceso automatizado | Endpoint oficial, agente identificable, límite de solicitudes, timeout, redirecciones permitidas y controles agregados entre procesos |
| Integridad | SHA-256, tamaño, fecha/hora UTC de captura, código HTTP y bytes originales cuando la retención esté autorizada |
| Retirada/corrección | Cómo se registra una corrección, retirada, restricción nueva o solicitud de eliminación |
| Responsable y evidencia | Identidad del responsable, fecha UTC, URL de política revisada, copia preservada de la política y SHA-256 |
| Decisión final | `APPROVED`, `TERMS_PENDING`, `SUSPENDED` o `REJECTED`, con justificación y alcance exactos |

No usar una casilla genérica de “términos revisados” como sustituto de las decisiones sobre contenido, retención y finalidad.

## Inventario de orígenes pendientes

| `source_id` | Contenido/alcance | Observaciones para la revisión | Estado actual |
|---|---|---|---|
| `sec_press_releases` | Feed RSS actual | Confirmar el agente y el control agregado de solicitudes; el RSS no representa el archivo completo. Separar metadatos, texto oficial y HTML completo. | `TERMS_PENDING` |
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

## Condiciones técnicas antes de activar una fuente

1. La entrada del registro, el registro de autorización del proveedor y la evidencia de política deben coincidir en `source_id`, finalidad y alcance.
2. La captura debe fallar cerrada antes de la red cuando el origen o cualquiera de los usos requeridos no esté aprobado.
3. La allowlist de host y rutas debe ser específica para cada feed/archivo; validar también cada redirección.
4. El control de frecuencia debe ser agregado entre procesos y máquinas. Un límite por invocación no es por sí solo un limitador global.
5. El informe debe diferenciar `BLOCKED_BY_SOURCE_POLICY`, `UNAVAILABLE`, `PARTIAL_OR_FAILED` y una captura correcta sin entradas. Ninguno de estos estados permite afirmar que no ocurrió un evento.
6. Solo después de documentar la decisión se podrá planificar una prueba real de alcance reducido. Preservar la solicitud, la respuesta, los hashes, las decisiones de identidad y la cobertura obtenida, sin afirmar exhaustividad más allá del alcance declarado.

## Criterio de cierre de esta preparación

La matriz documental puede considerarse preparada cuando está versionada. **Issue #132 no se considera terminado** hasta que exista una decisión de uso por cada fuente que se vaya a activar, una prueba E2E con evidencia real autorizada y un manifiesto de backfill reproducible. Las fuentes que no tengan autorización permanecen deshabilitadas; no es necesario activarlas todas para cerrar el trabajo funcional si se delimita y verifica un alcance autorizado suficiente.
