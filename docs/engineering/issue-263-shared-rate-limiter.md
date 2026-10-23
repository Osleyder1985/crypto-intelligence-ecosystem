# Limitador agregado de solicitudes — Issue #263

## Propósito

Las capturas autorizadas de feeds, índices de archivo y artículos deben coordinar el ritmo de solicitudes entre invocaciones concurrentes ejecutadas en el mismo host y bajo el mismo usuario del sistema operativo. Un bloqueo de memoria de un único proceso no cumple ese requisito.

## Implementación

`scripts/market_selection/shared_request_rate_limiter.py` reserva cada turno en una base SQLite compartida. La transacción `BEGIN IMMEDIATE` serializa las reservas concurrentes y persiste el siguiente instante permitido por `source_id`. La reserva se confirma antes de esperar, por lo que dos invocaciones no pueden leer simultáneamente el mismo turno disponible.

El limitador se aplica a los cuatro puntos de captura de `capture_public_event_feed.py`: feed, índice de archivo, artículo enlazado y artículo de archivo.

## Ubicación y alcance

- Ubicación predeterminada: `~/.crypto-intelligence/event-rate-limit.sqlite3`.
- Puede configurarse otra ruta mediante `CRYPTO_EVENT_RATE_LIMIT_DB`.
- La base debe ser compartida por las invocaciones del mismo usuario en el mismo host.
- **No es un limitador distribuido entre varios hosts ni entre usuarios del sistema con directorios distintos.** Si el despliegue necesita esa topología, deberá proporcionar un almacén de coordinación compartido y auditable antes de activar captura concurrente.
- Los registros de turnos persisten entre ejecuciones; la cuota se separa por `source_id`.

## Comportamiento ante errores

Si no se puede crear, abrir o actualizar el ledger, o si la cuota no es válida, se lanza `RateLimitCoordinationError` y la ejecución se detiene antes de enviar la solicitud. No se debe añadir un fallback al limitador en memoria, porque reintroduciría el fallo que se pretende corregir.

## Validación

Las pruebas usan una base SQLite temporal y un reloj/suspensión sintéticos. Cubren persistencia entre invocaciones, reservas concurrentes, límites inválidos y fallo cerrado cuando la coordinación no está disponible. No generan tráfico externo ni cambian la autorización de ninguna fuente.

## Límites conocidos

El ledger coordina procesos locales que comparten ruta de base de datos; no sustituye la revisión de términos ni demuestra autorización de contenido o persistencia. Los límites de fuente se deben derivar de la configuración revisada y de las condiciones aplicables, no de valores inventados.