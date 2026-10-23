# Registro preliminar de fuentes de noticias y eventos — Issue #132

- **Estado:** registro machine-readable añadido; ninguna fuente queda aprobada para ingestión automática. El adaptador SEC está implementado pero bloqueado por `TERMS_PENDING` hasta completar revisión de términos y autorización de uso.
- **Issue:** [#132](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/132)
- **Contrato de evento:** [issue-132-event-evidence-contract.md](issue-132-event-evidence-contract.md)
- **Fecha de consulta:** 2026-10-22

## Principio de selección

El registro distingue la autoridad de una fuente sobre el hecho que publica, su utilidad para detectar el evento, la disponibilidad de timestamps fiables y el derecho/posibilidad de conservar y reutilizar contenido. Una web accesible no implica permiso de reutilización, estabilidad técnica ni disponibilidad de una API. No se adopta ningún proveedor comercial de noticias en esta fase.

## Candidatos iniciales

| Fuente/categoría | Uso principal | Autoridad para el hecho | Acceso observable | Estado para el ecosistema |
|---|---|---|---|---|
| [Binance Newsroom](https://www.binance.com/en/press) | Anuncios propios, cambios de producto y listados/delistados publicados por Binance | Primaria para anuncios de Binance; no primaria para hechos de terceros | Página pública de newsroom; no se ha validado una API/RSS estable ni una licencia de archivo automatizado | Candidata para evaluación; acceso automatizado y términos pendientes |
| [SEC — Press Releases](https://www.sec.gov/newsroom/press-releases) | Acciones, comunicados y anuncios regulatorios de la SEC | Primaria para acciones/comunicados de la SEC; alcance jurisdiccional limitado | Feed oficial `https://www.sec.gov/news/pressreleases.rss` | Adaptador implementado, pero deshabilitado por `TERMS_PENDING`; no realiza red hasta aprobación de términos y autorización explícita |
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
- Estado explícito: `PROPOSED`, `TERMS_PENDING`, `APPROVED`, `SUSPENDED`, `RETIRED` o `REJECTED`.

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

Estas referencias acreditan puntos de acceso públicos, no aprobación de reutilización. El adaptador SEC está en `scripts/market_selection/capture_sec_press_releases_rss.py` y se gobierna por `scripts/market_selection/event_source_registry.py`; la entrada permanece `TERMS_PENDING`, por lo que la ejecución real está bloqueada antes de la red. Las pruebas usan respuestas sintéticas y opener simulado.

## Adaptador SEC: alcance y habilitación

- La URL RSS está fijada al endpoint oficial; el adaptador no acepta URLs arbitrarias para el feed. Los artículos individuales se limitan a hosts HTTPS `sec.gov`/`www.sec.gov`.
- El adaptador lee la respuesta hasta EOF, preserva bytes base64, tamaño, SHA-256 y headers de respuesta sin imponer un límite local de tamaño. Los errores HTTP también conservan el cuerpo completo recibido.
- Cada invocación hace como máximo una petición y no abre solicitudes paralelas. La [documentación oficial para desarrolladores de SEC](https://www.sec.gov/about/developer-resources) publica un límite de 10 solicitudes/segundo y requisitos de identificación del agente; la coordinación agregada entre procesos debe garantizarse en el despliegue, no se afirma que este módulo imponga un limitador global.
- Se requiere un User-Agent proporcionado y revisado por el operador y un timeout explícito. El código no puede determinar si SEC considera clasificado ese agente.
- La fuente solo se puede activar si se preservan los bytes de los términos revisados y su SHA-256 coincidente, se completan `reviewed_by`, `reviewed_at` y `allowed_use_cases`, y el registro de autorización del proveedor coincide con esa revisión. Aun así, la autorización de software no es dictamen legal.
- El RSS es solo una ventana de feed, no archivo histórico completo. Los titulares no resuelven entidades: promover un evento requiere captura completa del artículo, IDs estables revisados y una afirmación explícita. El conector no infiere causalidad.
