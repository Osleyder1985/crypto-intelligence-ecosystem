# Registro preliminar de fuentes de noticias y eventos — Issue #132

- **Estado:** inventario inicial de candidatos; ninguna fuente queda aprobada para ingestión automática hasta revisar acceso, términos, cobertura y captura temporal.
- **Issue:** [#132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132)
- **Contrato de evento:** [issue-132-event-evidence-contract.md](issue-132-event-evidence-contract.md)
- **Fecha de consulta:** 2026-10-22

## Principio de selección

El registro distingue la autoridad de una fuente sobre el hecho que publica, su utilidad para detectar el evento, la disponibilidad de timestamps fiables y el derecho/posibilidad de conservar y reutilizar contenido. Una web accesible no implica permiso de reutilización, estabilidad técnica ni disponibilidad de una API. No se adopta ningún proveedor comercial de noticias en esta fase.

## Candidatos iniciales

| Fuente/categoría | Uso principal | Autoridad para el hecho | Acceso observable | Estado para el ecosistema |
|---|---|---|---|---|
| [Binance Newsroom](https://www.binance.com/en/press) | Anuncios propios, cambios de producto y listados/delistados publicados por Binance | Primaria para anuncios de Binance; no primaria para hechos de terceros | Página pública de newsroom; no se ha validado una API/RSS estable ni una licencia de archivo automatizado | Candidata para evaluación; acceso automatizado y términos pendientes |
| [SEC — Press Releases](https://www.sec.gov/newsroom/press-releases) | Acciones, comunicados y anuncios regulatorios de la SEC | Primaria para acciones/comunicados de la SEC; alcance jurisdiccional limitado | Página oficial muestra un feed RSS de comunicados | Candidata para adaptador regulatorio; verificar condiciones técnicas, atribución y captura antes de habilitar |
| Comunicados oficiales de cada proyecto/protocolo | Incidentes, upgrades, gobernanza, tokenomics, unlocks y cambios de protocolo | Primaria solo respecto de lo que el propio proyecto declara | Heterogéneo: web, RSS/Atom, blog, foro, GitHub releases o canales oficiales | Requiere catálogo por proyecto, URL verificada y resolución de identidad; no se asume una interfaz común |
| Páginas oficiales de estado/incidentes de exchanges y protocolos | Caídas, interrupciones, explotación, mantenimiento y recuperación | Primaria para el estado operativo declarado por ese proveedor | Heterogéneo; formatos y retención varían | Candidata por proveedor; hay que capturar cambios de estado y hora de primera observación |
| Fuentes periodísticas secundarias | Descubrir hechos, contexto, versiones contradictorias y pistas para investigación | Secundaria; debe corroborarse con fuente primaria cuando sea posible | Depende del proveedor, API, suscripción y términos de reutilización | No seleccionar proveedor hasta evaluar licencia, cobertura, historial, timestamps y coste |
| Agregadores de noticias/sentimiento | Descubrimiento y agrupación de menciones | No deben tratarse como evidencia primaria | APIs/planes y metodologías variables | Solo como fuente auxiliar; nunca como prueba suficiente de causalidad |

## Registro de decisión por fuente

Antes de activar una fuente se debe completar y versionar al menos:

- `source_id`, propietario/editor, categoría, jurisdicción y dominios canónicos.
- URL de documentación/API y método de acceso permitido (API/RSS/webhook/archivo manual); no usar endpoints privados o no documentados.
- URL de términos/licencia, fecha de revisión, atribución requerida, derechos de retención/redistribución y estado de aprobación.
- Cobertura temporal/geográfica, activos/eventos cubiertos, límites, paginación, cuotas, latencia declarada y campos disponibles.
- Semántica de publicación, actualización, corrección y retirada; zona horaria y si el timestamp lo declara la fuente o se observa al capturar.
- Método de captura, reloj de sistema, hora de captura, hash de bytes originales cuando sea legal y técnicamente posible, y retención.
- Métricas operativas: última captura correcta, retraso observado, huecos, duplicados, errores, cambios de esquema y fecha de última revisión.
- Estado explícito: `PROPOSED`, `TERMS_PENDING`, `APPROVED`, `SUSPENDED` o `RETIRED`.

## Reglas de evidencia y cobertura

1. Un comunicado de Binance confirma lo que Binance anunció; no prueba por sí solo que un protocolo externo haya sufrido una explotación.
2. Un comunicado regulatorio se interpreta dentro de la jurisdicción, el procedimiento y el alcance exacto del documento. Una alegación, propuesta o investigación no debe convertirse en sentencia o hecho probado.
3. Una noticia secundaria puede descubrir un evento, pero debe mantener su categoría y vincular la corroboración primaria si existe.
4. Versiones contradictorias se conservan como evidencias separadas, con sus horas de publicación/captura y estados de verificación. No se sobrescribe una versión previa.
5. La falta de resultados solo significa que no se encontró evidencia en las fuentes/rango consultados. Para reportar cobertura hay que incluir fuentes consultadas, intervalo, estado de captura, paginación, errores y términos que limitaron el acceso.
6. Los timestamps históricos publicados por la fuente no sustituyen la hora de captura. Si la captura se produjo después del corte de backtest, el evento queda no disponible para ese corte.
7. La relevancia para un activo debe resolverse con IDs estables, dirección de contrato y red cuando aplique; coincidencia de ticker o palabras del titular no basta.
8. No declarar causalidad por proximidad temporal. El análisis debe considerar eventos de mercado comunes, movimientos del mercado amplio, noticias competidoras, liquidez, errores de datos y explicaciones alternativas.

## Evidencia pública consultada

- Binance, [Newsroom](https://www.binance.com/en/press): página oficial de anuncios y novedades de Binance.
- U.S. Securities and Exchange Commission, [Press Releases](https://www.sec.gov/newsroom/press-releases): página oficial de comunicados; la página anuncia disponibilidad de RSS.
- Binance Developer Documentation, [Developer Documentation](https://developers.binance.com/en/docs/introduction): la documentación oficial diferencia interfaces soportadas de comportamientos/endpoints no documentados.

Estas referencias acreditan la existencia de puntos de acceso públicos, no la aprobación de sus condiciones de reutilización ni la implementación de conectores. Los términos, las cuotas y el comportamiento real deben verificarse por separado antes de implementar cada adaptador.
