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


## Autorización de alcance del propietario del proyecto — 2026-10-23

El propietario confirmó explícitamente en la conversación de trabajo que acepta el siguiente alcance propuesto para preparar la validación multifuente:

- **Fuentes solicitadas para evaluación individual:** `sec_press_releases`, `sec_press_release_archive`, `cftc_general_press_releases`, `cftc_press_release_archive`, `federal_reserve_press_releases` y `federal_reserve_press_release_archive`.
- **Finalidad del proyecto:** análisis interno de noticias/eventos como evidencia candidata para investigar movimientos de criptomonedas.
- **Autorización funcional del propietario:** el propietario autorizó avanzar con las seis fuentes y no debe volver a preguntársele por esa misma decisión. El alcance funcional solicitado incluye evaluar y usar metadatos, texto oficial y HTML completo; evaluar adjuntos y contenido de terceros; y desarrollar acceso automatizado, almacenamiento, atribución, conservación, análisis interno y backfill.
- **Aplicación por modalidad:** esa autorización permite continuar el trabajo de ingeniería y las validaciones, pero cada modalidad se habilita en ejecución solo cuando la evidencia oficial aplicable demuestra que el método de acceso y el tratamiento de datos son admisibles. No se interpretará el silencio de una política como permiso ilimitado, ni se redistribuirá contenido de terceros sin base documentada.
- **Retención:** aplicar requisitos identificados y documentados por fuente y tipo de dato; no inventar plazos ni conservar indefinidamente por defecto. Si no puede determinarse una regla aplicable, mantener bloqueada la persistencia del contenido afectado hasta resolverla.
- **Acceso automatizado:** verificar endpoint, disponibilidad, condiciones publicadas, agente identificable, límites aplicables y control agregado de solicitudes antes de habilitar tráfico. La autorización del propietario no obliga a consultar un endpoint que esté deshabilitado ni permite eludir restricciones técnicas.
- **Identidad/fecha de aprobación:** la decisión queda registrada en el comentario del Issue #132 y en el historial de esta conversación. No se atribuye una identidad legal, firma digital ni aprobación del proveedor que no haya sido verificada.

### Qué autoriza y qué no autoriza esta confirmación

Esta es una **autorización funcional expresa del propietario para avanzar con el alcance completo de las seis fuentes**, y no debe solicitarse de nuevo. No equivale a permiso concedido por SEC, CFTC o Federal Reserve, no constituye dictamen jurídico y no demuestra que cada método de acceso, persistencia o reutilización esté permitido para cada endpoint. Por ello, **no cambia por sí sola el estado operativo** de ningún origen: los seis permanecen `TERMS_PENDING` hasta documentar evidencia específica, disponibilidad y controles técnicos aplicables. La decisión del propietario está tomada; los pendientes restantes son de evidencia, disponibilidad y cumplimiento de condiciones por fuente, no una nueva solicitud de autorización al propietario.

| Fuente | Autorización funcional del propietario | Estado operativo |
|---|---|---|
| `sec_press_releases` | Autorizado avanzar con todos los usos funcionales previstos, sujetos a verificación de condiciones por modalidad | `TERMS_PENDING` |
| `sec_press_release_archive` | Autorizado avanzar con todos los usos funcionales previstos, sujetos a verificación de condiciones por modalidad | `TERMS_PENDING` |
| `cftc_general_press_releases` | Autorizado avanzar con todos los usos funcionales previstos; no consultar mientras el RSS esté deshabilitado | `TERMS_PENDING` |
| `cftc_press_release_archive` | Autorizado avanzar con todos los usos funcionales previstos, sujetos a verificación de condiciones por modalidad | `TERMS_PENDING` |
| `federal_reserve_press_releases` | Autorizado avanzar con todos los usos funcionales previstos, sujetos a verificación de condiciones por modalidad | `TERMS_PENDING` |
| `federal_reserve_press_release_archive` | Autorizado avanzar con todos los usos funcionales previstos, sujetos a verificación de condiciones por modalidad | `TERMS_PENDING` |

**Próximo paso:** ejecutar la revisión y preparación técnica por fuente sin volver a solicitar la autorización funcional ya concedida. La captura real y el backfill se habilitarán cuando la evidencia verificable confirme disponibilidad, condiciones de acceso y controles operativos para la modalidad concreta.
## Control SEC: límite publicado y clasificación del agente — 2026-10-23

La política oficial de seguridad de SEC.gov establece un máximo agregado de 10 solicitudes por segundo, sin importar cuántas máquinas originan las solicitudes, y advierte que no permite bots o herramientas automatizadas no clasificadas. Fuente: https://www.sec.gov/about/privacy-information

Consecuencias para `sec_press_releases` y `sec_press_release_archive`:
- El valor de 10 solicitudes/segundo del registro puede trazarse al techo general publicado de SEC.gov, no únicamente a la FAQ de EDGAR.
- Ese techo es un máximo, no una frecuencia objetivo. El proyecto puede usar un límite menor como control interno si queda identificado como tal.
- Antes de habilitar tráfico, debe utilizarse un User-Agent identificable y revisado, y el límite debe aplicarse de forma agregada entre procesos y máquinas que compartan la salida de red. El control local por host no basta para demostrar el límite global.
- No se modifica el estado de ninguna fuente ni se habilita tráfico con este ajuste documental. Las políticas deben preservarse en bytes verificables y calcularse su hash sobre esos bytes antes de completar el expediente técnico.

Esta precisión no modifica la autorización funcional del propietario, ya registrada arriba, y no se le volverá a solicitar para las seis fuentes enumeradas.