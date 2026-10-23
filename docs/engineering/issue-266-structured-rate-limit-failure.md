# Fallos estructurados de coordinación del limitador — Issue #266

## Problema

El limitador SQLite debe fallar de forma cerrada si no puede reservar una cuota. Para que ese fallo sea auditable, los comandos de captura también deben persistir un artefacto JSON, en lugar de dejar únicamente una excepción sin resultado estructurado.

## Contrato de fallo

Ante `RateLimitCoordinationError`, los CLI de feed/artículo y de índice/artículo de archivo escriben un objeto con:

- `schema_version: crypto-public-event-capture-error-v1`
- `capture_status: BLOCKED_RATE_LIMIT_COORDINATION`
- `network_request_made: false`
- `reason_codes: [RATE_LIMIT_COORDINATION_FAILED]`
- `errors[0].type: RATE_LIMIT_COORDINATION`
- Un mensaje estable que no revela la ruta local de SQLite ni detalles internos.

El comando persiste el artefacto bloqueado y termina con código de salida distinto de cero. Los consumidores deben evaluar tanto el código de salida como `capture_status`; el JSON proporciona evidencia estructurada, pero no convierte el intento bloqueado en una captura correcta.

## Seguridad y alcance

- No se hace fallback a un limitador en memoria.
- No se reintenta la solicitud de red si falla la coordinación.
- La ruta de la base de datos, credenciales y excepciones internas no se incluyen en el artefacto.
- Las pruebas usan fuentes y autorizaciones sintéticas y verifican que no se invoque el acceso de red.
- Esto no autoriza fuentes ni demuestra coordinación distribuida entre varios hosts.

## Validación

La prueba `tests/market_selection/test_rate_limit_cli_failures.py` cubre los CLI de feed y archivo: error de coordinación inyectado, artefacto JSON persistido, código de razón estable, código de salida no exitoso y ausencia de llamada de red. El CLI de archivo limita el manejo del error a `capture-index` y `capture-article`; los comandos offline propagan otros errores sin clasificarlos como bloqueos del limitador.
