# Inventario inicial de fuentes oficiales para eventos externos

**Estado:** inventario técnico inicial; ninguna fuente nueva queda autorizada por este documento.  
**Fecha de revisión de endpoints:** 2026-10-23.  
**Regla de operación:** `TERMS_PENDING` bloquea la captura y el almacenamiento persistente.

## Fuentes registradas

| Fuente | Feed oficial | Política / términos consultados | Cobertura y limitaciones | Estado |
|---|---|---|---|---|
| SEC — comunicados de prensa | https://www.sec.gov/news/pressreleases.rss | https://www.sec.gov/about/developer-resources | Feed actual de materiales de prensa; no es un archivo histórico completo. La SEC exige acceso justo, identificación del agente y cumplimiento de su política de seguridad. | `TERMS_PENDING` |
| CFTC — comunicados generales | https://www.cftc.gov/RSS/RSSGP/rssgp.xml | https://www.cftc.gov/sites/default/files/cftc/cftcprivacy.htm | Comunicados regulatorios generales, no solo de cripto; útil para enforcement, derivados y regulación. El sitio advierte que parte del material de terceros puede tener restricciones. | `TERMS_PENDING` |
| Federal Reserve Board — todos los comunicados | https://www.federalreserve.gov/feeds/press_all.xml | https://www.federalreserve.gov/policies.htm | Contexto macroeconómico y monetario; no es una fuente específica de cripto ni un archivo histórico completo. Las políticas distinguen material de terceros con restricciones de reutilización. | `TERMS_PENDING` |

## Hallazgos verificables

- La SEC publica su índice oficial de RSS y documenta reglas de acceso automatizado, incluido un User-Agent identificable y límites de solicitudes. Fuentes: https://www.sec.gov/about/developer-resources y https://www.sec.gov/about/rss-feeds
- La CFTC publica un índice oficial de RSS con un feed de comunicados generales. Fuente: https://www.cftc.gov/RSS/index.htm
- La Reserva Federal publica un índice oficial de RSS con el feed de todos los comunicados. Fuente: https://www.federalreserve.gov/feeds/feeds.htm
- La existencia de un feed público no demuestra por sí sola que el uso previsto, la copia de artículos y el almacenamiento persistente estén autorizados.

## Controles pendientes antes de habilitar una fuente

1. Preservar el contenido íntegro de los términos/políticas consultados y su SHA-256.
2. Revisar el alcance concreto: análisis interno, persistencia, retención, reproducción de texto y redistribución.
3. Registrar responsable y fecha de revisión; definir User-Agent, rate limit, timeout y cobertura.
4. Añadir una autorización de proveedor coherente con la fuente y el uso solicitado.
5. Implementar y probar un adaptador de captura específico para cada fuente aprobada, con timestamps de publicación y captura separados, deduplicación y registro de errores.
6. Mantener la fuente bloqueada hasta completar esos pasos.

## Estado funcional

Este PR amplía el registro de candidatos; **no** añade adaptadores de captura para CFTC o Federal Reserve, no realiza solicitudes de red, no autoriza persistencia y no declara cobertura real de noticias. El flujo principal solo puede integrar registros de eventos preservados y previamente validados. La relación temporal con un movimiento sigue siendo evidencia contextual, no causalidad demostrada.
