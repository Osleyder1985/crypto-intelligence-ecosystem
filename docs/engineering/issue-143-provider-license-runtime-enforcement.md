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

También se cierran entrypoints de transporte de bajo nivel: `request_page` de Binance OHLCV y `request_json` del diagnóstico REST regional vuelven a evaluar el gate antes de `urlopen`, incluso cuando se invocan sin sus funciones coordinadoras; `_open_public_stream` vuelve a comprobar la política justo antes de abrir el WebSocket. Los tests verifican que el transporte no se invoca al bloquear.

Los lectores `binance_public.py` y `pionex_public.py` también consultan la red directamente. Ahora exigen un registro de autorización explícito para `internal_analysis`, verifican el gate antes del transporte inyectado y antes del transporte HTTP predeterminado, y adjuntan la evaluación a las observaciones correctas. Las pruebas de tamaño grande usan registros sintéticos solo para validar la lectura íntegra; no representan autorizaciones reales.

El sondeo `capture_multi_exchange_spot_ticker_probe.py` también conserva los cuerpos de respuesta completos como evidencia base64. Por eso debe usar `persistent_storage` y la autorización por venue antes de `urlopen`; sin registros locales aprobados para el proveedor y el caso de uso, cada fila se marca `BLOCKED` y no se envía la solicitud. El comando admite `--authorization-records` (objeto JSON indexado por `provider_id`) y bloquea por defecto si no se suministra.

## Acceso privado de cuenta: Binance y Pionex

Los capturadores `capture_binance_account_commission_evidence.py` y `capture_pionex_fill_fee_evidence.py` consultan endpoints autenticados de cuenta; no son capturas de mercado público. Las claves API, por sí solas, no demuestran consentimiento para cualquier tratamiento ni autorización de licencia para cualquier uso posterior.

Se requiere una evaluación previa de `binance_spot_account_data` o `pionex_spot_account_data` con el caso `internal_analysis`. El registro aprobado debe incluir una referencia y SHA-256 de la evidencia de autorización del titular de la cuenta y confirmar que el alcance de la credencial se verificó. Sin registro, con autorización ausente/no aprobada/fuera de alcance o con alcance de credencial no verificado, el capturador debe bloquear antes de crear una petición de red. Los comandos exigen un archivo JSON local mediante `--authorization-record`; ese archivo no debe incorporarse al repositorio. La referencia de consentimiento es trazabilidad aportada por el operador, no verificación automática de identidad ni dictamen jurídico.

La evidencia de cuenta puede contener historial de operaciones y tasas individualizadas. Debe limitarse su acceso, evitar guardar respuestas privadas innecesarias y no exponer claves, firmas ni URLs firmadas en logs. Esta puerta controla la autorización del software; no reemplaza los controles de permisos mínimos de la clave API ni la revisión de términos oficiales.

## Relación con captura íntegra

No imponer un límite local arbitrario de bytes no significa que una API garantice todo el histórico imaginable. La captura debe leer cada respuesta hasta EOF, conservar el cuerpo íntegro recibido, registrar tamaño y SHA-256 y declarar cualquier truncamiento o fallo de transporte. Los límites documentados del proveedor, cuotas, ventanas históricas, paginación y fallos reales deben reflejarse como limitaciones observadas; no deben reemplazarse por un techo local inventado ni ocultarse como cobertura completa.

La integridad del cuerpo recibido y la autorización para usar los datos son controles distintos: pasar uno no implica pasar el otro.

## Inventario de entrypoints de red auditados

La revisión recursiva de los archivos Python del repositorio identificó los siguientes entrypoints de red. Los módulos analíticos, contratos, validadores de calidad y ensambladores de informes no contienen llamadas HTTP/WebSocket directas; los puntos de entrada que consumen artefactos ahora también verifican que la evidencia de captura autorice explícitamente `internal_analysis`.

| Entry point | Proveedor / transporte | Caso de uso comprobado antes de red |
|---|---|---|
| `binance_depth_transport.fetch_public_depth_snapshot` | Binance REST depth | `live_technical_test` |
| `binance_depth_transport._open_public_stream` / `capture_once` | Binance WebSocket depth | `live_technical_test` |
| `capture_binance_live_depth_evidence.clock_probe` | Binance REST server-time | `live_technical_test` |
| `capture_binance_regional_rest_diagnostic.request_json` / `capture_endpoint` | Binance global / Binance.US REST | `live_technical_test` |
| `capture_binance_spot_ohlcv.request_page` / `capture_history` | Binance Spot OHLCV | Caso declarado; registro para usos no técnicos |
| `capture_binance_spot_research` | Binance exchange metadata | Caso declarado; gate antes de `urlopen` |
| `capture_pionex_spot_ohlcv.request_page` / `capture_history` | Pionex Spot OHLCV | Caso declarado; gate antes de `urlopen` |
| `capture_binance_account_commission_evidence.capture_commission_evidence` | Binance cuenta privada | `internal_analysis` + consentimiento del titular + alcance de credencial verificado |
| `capture_pionex_fill_fee_evidence.capture` | Pionex fills de cuenta privada | `internal_analysis` + consentimiento del titular + alcance de credencial verificado |
| `capture_multi_exchange_spot_book_probe.capture_one` | Binance, OKX, Bybit, MEXC, Gate, Bitget, Pionex REST depth | `persistent_storage` por proveedor |
| `capture_multi_exchange_spot_ticker_probe.capture_one` | Los mismos siete venues, REST ticker | `persistent_storage` por proveedor |
| `capture_public_market_batch.request_capture` | Proveedores públicos declarados por configuración | Caso declarado; gate antes de `urlopen` |
| `capture_public_market_data.request_capture` | Proveedores públicos declarados por configuración | Caso declarado; gate antes de `urlopen` |
| `capture_sec_press_releases_rss.capture_sec_press_releases_rss` | SEC RSS | `internal_analysis` + `persistent_storage`, registro de fuente `APPROVED`, autorización y User-Agent antes de `urlopen` |
| `capture_sec_press_releases_rss.capture_sec_press_release_article` | Artículos enlazados por el RSS SEC | Igual que el RSS; HTTPS y host `sec.gov` allowlisted antes de `urlopen` |
| `binance_public.BinancePublicSpotReader` / `_default_http_get` | Binance REST exchangeInfo/depth | `internal_analysis` por defecto |
| `pionex_public.PionexPublicSpotReader` / `_default_http_get` | Pionex REST symbols | `internal_analysis` por defecto |


### Consumidores de artefactos y uso interno

La política se versiona como `1.2.0`. Cada evaluación autorizada incluye el hash canónico del registro de autorización y la lista explícita de casos autorizados, sin exponer secretos. `evaluate_artifact_use` rechaza artefactos antiguos sin versión/política, capturas permitidas solo como `live_technical_test`, registros sin hash o registros cuyo alcance no incluye el uso solicitado.

Los siguientes consumidores bloquean antes de analizar si el artefacto no contiene evidencia válida de autorización para `internal_analysis`:

- `research_report.build_research_report`
- `research_evidence_integration.enrich_research_report`
- `selector.evaluate_market`
- `analyze_ohlcv_risk_profile.analyze_artifact`
- `detect_ohlcv_movement_events.analyze_movement_events`
- `analyze_support_resistance.analyze_support_resistance`
- `analyze_depth_cost_curves.analyze_artifact`
- `analyze_quote_volume_series.analyze_artifacts`
- `analyze_spot_market_pareto.analyze_files`
- `analyze_minimum_common_notional_scenario.analyze_artifact`

Los cálculos matemáticos puros y helpers de parsing no abren conexiones; el control se coloca en la frontera que convierte artefactos de proveedor en análisis o decisiones. La evidencia almacenada es una comprobación de política del software, no prueba de autenticidad de documentos ni dictamen legal.

**Controles transversales:** el gate se evalúa tanto en los coordinadores como en los entrypoints de bajo nivel que abren conexiones. El conector SEC se registra como proveedor revisable, pero la fuente sigue `TERMS_PENDING` y el código bloquea antes de red hasta que se preserven/revisen los términos y se aprueben los casos de uso. Los rechazos se producen antes de `urlopen` o `websocket.create_connection`. Los usos de `live_technical_test` permitidos por la política no equivalen a licencia comercial, autorización de redistribución ni elegibilidad regional. La evidencia de un registro aprobado sigue requiriendo verificación humana de los términos oficiales y del alcance real.

