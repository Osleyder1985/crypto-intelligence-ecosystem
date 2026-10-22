# Auditoría de enforcement de licencias de proveedores — Issue #143

**Estado:** hallazgo abierto; no equivale a una aprobación legal ni a un control runtime implementado.

## Hallazgo verificado

La PR [#142](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/142) introduce un evaluador de política en `scripts/market_selection/provider_license_gate.py`. En la versión de esa PR revisada durante esta auditoría, el evaluador se prueba de forma aislada, pero no se invoca desde el flujo de captura `capture_binance_spot_research.py` ni desde el orquestador del informe. El flujo mantiene `license_review_status = REQUIRES_PRODUCT_SPECIFIC_REVIEW` como etiqueta, sin una decisión efectiva previa a la petición.

Por tanto, las pruebas unitarias del evaluador no demuestran que una captura, retención, presentación o exportación prohibida se bloquee en runtime. El hallazgo se registra en [Issue #143](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/143).

## Criterios de cierre

1. Cada operación declara proveedor y caso de uso específico antes de acceder a los datos o utilizarlos.
2. Una decisión `BLOCK` termina el flujo antes de cualquier petición de red o uso restringido; no basta con anotar una advertencia en el informe.
3. La evidencia de ejecución registra proveedor, caso de uso, decisión, códigos de motivo, versión de política y referencia/hash de autorización, sin incluir secretos.
4. Las pruebas de integración simulan el transporte y demuestran que autorizaciones ausentes, inválidas, caducadas o fuera de alcance no generan solicitudes.
5. Las pruebas positivas demuestran que una autorización permite únicamente el alcance explícito que cubre.
6. El registro de autorización debe verificarse contra el acuerdo o los términos oficiales aplicables. Un hash y una URL almacenados prueban trazabilidad del documento presentado, no la autenticidad del permiso ni la existencia de derechos.
7. Los workflows obligatorios deben pasar sobre la cabeza de la rama basada en el `main` vigente; resultados de un SHA anterior no prueban la integración actual.

## Baseline de uso por proveedor

- **Binance Spot:** una prueba técnica read-only no es autorización general para explotación comercial, retención o redistribución.
- **DefiLlama:** mantener bloqueado el uso sujeto a permiso hasta que exista autorización escrita verificable que cubra la actividad concreta.
- **CoinGecko:** verificar plan, alcance, atribución, política de caché/retención y derechos específicos de redistribución antes de habilitar cada caso de uso.
- **Proveedor desconocido:** bloquear por defecto hasta revisión y registro explícitos.

Estas reglas son controles de ingeniería y no sustituyen una revisión legal específica del contrato, jurisdicción, producto y modalidad de uso.

## Captura multi-exchange y almacenamiento persistente

`capture_multi_exchange_spot_book_probe.py` guarda el payload público íntegro como evidencia base64 y, por tanto, su caso de uso es `persistent_storage`, no solo una prueba técnica en vivo. La captura ahora evalúa el gate por venue antes de crear una solicitud: Binance, OKX, Bybit, MEXC, Gate, Bitget y Pionex. Sin autorización aprobada para el proveedor y el caso de uso, la fila queda `BLOCKED` y no se llama a `urlopen`. Las autorizaciones se suministran localmente con `--authorization-records`, como objeto JSON indexado por `provider_id`; sin archivo, el comportamiento predeterminado es bloquear. Los registros de prueba no equivalen a permisos reales.

El sondeo `capture_multi_exchange_spot_ticker_probe.py` también conserva los cuerpos de respuesta completos como evidencia base64. Por eso debe usar `persistent_storage` y la autorización por venue antes de `urlopen`; sin registros locales aprobados para el proveedor y el caso de uso, cada fila se marca `BLOCKED` y no se envía la solicitud. El comando admite `--authorization-records` (objeto JSON indexado por `provider_id`) y bloquea por defecto si no se suministra.

## Acceso privado de cuenta: Binance y Pionex

Los capturadores `capture_binance_account_commission_evidence.py` y `capture_pionex_fill_fee_evidence.py` consultan endpoints autenticados de cuenta; no son capturas de mercado público. Las claves API, por sí solas, no demuestran consentimiento para cualquier tratamiento ni autorización de licencia para cualquier uso posterior.

Se requiere una evaluación previa de `binance_spot_account_data` o `pionex_spot_account_data` con el caso `internal_analysis`. El registro aprobado debe incluir una referencia y SHA-256 de la evidencia de autorización del titular de la cuenta y confirmar que el alcance de la credencial se verificó. Sin registro, con autorización ausente/no aprobada/fuera de alcance o con alcance de credencial no verificado, el capturador debe bloquear antes de crear una petición de red. Los comandos exigen un archivo JSON local mediante `--authorization-record`; ese archivo no debe incorporarse al repositorio. La referencia de consentimiento es trazabilidad aportada por el operador, no verificación automática de identidad ni dictamen jurídico.

La evidencia de cuenta puede contener historial de operaciones y tasas individualizadas. Debe limitarse su acceso, evitar guardar respuestas privadas innecesarias y no exponer claves, firmas ni URLs firmadas en logs. Esta puerta controla la autorización del software; no reemplaza los controles de permisos mínimos de la clave API ni la revisión de términos oficiales.

## Relación con captura íntegra

No imponer un límite local arbitrario de bytes no significa que una API garantice todo el histórico imaginable. La captura debe leer cada respuesta hasta EOF, conservar el cuerpo íntegro recibido, registrar tamaño y SHA-256 y declarar cualquier truncamiento o fallo de transporte. Los límites documentados del proveedor, cuotas, ventanas históricas, paginación y fallos reales deben reflejarse como limitaciones observadas; no deben reemplazarse por un techo local inventado ni ocultarse como cobertura completa.

La integridad del cuerpo recibido y la autorización para usar los datos son controles distintos: pasar uno no implica pasar el otro.
