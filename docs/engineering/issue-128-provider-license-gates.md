# Puertas de aprobación de fuentes externas — Issue #128

- **Consulta documental:** 2026-10-22
- **Estado:** evaluación documental preliminar; ninguna fuente queda autorizada automáticamente para uso comercial o redistribución.
- **Objetivo:** impedir que una API técnicamente accesible se trate como una fuente legalmente aprobada para un producto web/móvil con informes persistentes.

## Decisiones de integración

| Fuente | Evidencia oficial revisada | Restricción relevante | Decisión para el ecosistema |
|---|---|---|---|
| Binance Spot public market-data API | [Documentación oficial REST](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md) y [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | La documentación confirma endpoints públicos sin autenticación para datos de mercado; eso demuestra disponibilidad técnica, no por sí solo el alcance de los derechos comerciales, la retención o la redistribución del dato en un producto. | **HABILITADA SOLO PARA PRUEBAS TÉCNICAS DE SOLO LECTURA EN ESTA PR**. Antes de producción comercial, persistencia de largo plazo, exportación o redistribución, revisar y registrar las condiciones aplicables al producto y jurisdicción. |
| DefiLlama API gratuita | [Documentación oficial de API](https://api-docs.defillama.com/) y [Términos de uso](https://defillama.com/terms) | Los términos permiten usar la API pública oficial, pero restringen el uso comercial, copia, republicación y explotación de datos sin consentimiento previo por escrito; no se debe asumir que un producto comercial puede retener o mostrar libremente datos. | **NO APROBADA para ingestión persistente/comercial** hasta obtener y registrar autorización escrita aplicable al producto y a la retención/distribución prevista. Solo mantener el adaptador offline para fixtures/capturas ya autorizadas. |
| CoinGecko API | [Términos de API](https://www.coingecko.com/en/api_terms), [planes y licencias](https://www.coingecko.com/en/api/pricing), [guía de licencias actualizada](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses) | La documentación vigente distingue uso comercial en planes de pago, atribución pública, restricciones de redistribución/sublicencia y obligaciones de almacenamiento/actualización/eliminación. El acceso gratuito no debe interpretarse como licencia comercial universal. | **CANDIDATA CONDICIONADA** a elegir plan/licencia compatible, implementar atribución y retención permitida, y resolver por escrito cualquier caso de redistribución o entrega de datos reutilizables a usuarios. |
| Datos oficiales de protocolo/cadena | Documentación oficial específica del proyecto o red, más términos del endpoint/explorador utilizado | La disponibilidad pública no elimina condiciones de uso, límites operativos ni problemas de semántica, indexación, reorgs o atribución. Cada red y proveedor requiere análisis individual. | **CANDIDATA POR FUENTE**: aprobar por endpoint y campo, no como una categoría genérica. Preservar bloque/altura, hora de observación/captura, metodología y estado de finalización cuando proceda. |
| Fuentes oficiales de noticias, emisores y reguladores | Sitio/documentación oficial de cada emisor o regulador; condiciones del feed/API específico | Una página pública no garantiza permiso para scraping automatizado, republicación de contenido íntegro o almacenamiento indefinido. Fechas de publicación y captura deben distinguirse. | Preferir feeds/API oficiales documentados. Registrar licencia, atribución, límites, retención y evidencia primaria antes de habilitar captura automática. |

## Puerta obligatoria antes de habilitar un conector

Cada proveedor/endpoint debe tener un registro versionado con:

1. URL y documentación oficial consultada, fecha de consulta y responsable de revisión.
2. Tipo de licencia/plan aplicable y evidencia de aceptación o autorización escrita cuando sea necesaria.
3. Uso permitido: cálculo interno, visualización al usuario, informes, almacenamiento histórico, exportación y redistribución; cada permiso debe ser explícito.
4. Atribución exigida, límites de llamadas, costes, política de caché/retención y eliminación al terminar el acceso.
5. Esquema, semántica de cada campo, timestamps, cobertura histórica, tratamiento de correcciones y límites de integridad.
6. Pruebas con respuestas capturadas y hashes; estados de error, ausencia, obsolescencia, conflicto y truncamiento.
7. Aprobación de gobernanza antes de que el conector se habilite en producción.

## Regla de seguridad de producto

No inferir permiso comercial a partir de que un endpoint responda HTTP 200, de que exista una API gratuita, de que los datos sean visibles en una web, ni de que un proveedor ofrezca un plan de pago. La licencia debe cubrir el uso real del ecosistema: investigación interna, informes, clientes web/móvil, persistencia, descarga/exportación y cualquier redistribución prevista.

## Consecuencia inmediata

- DefiLlama queda bloqueada como fuente automática persistente/comercial hasta autorización escrita aplicable.
- CoinGecko queda como candidata condicionada a un plan/licencia, atribución y reglas de almacenamiento/redistribución compatibles.
- Los contratos de eventos y fundamentales/on-chain siguen offline. La PR #139 añade una captura técnica de solo lectura para Binance Spot; no implica autorización comercial ni habilita distribución de datos.
- Las conclusiones del informe continúan en `INDETERMINATE` si falta evidencia permitida, suficiente o temporalmente válida.

Esta nota es una revisión documental técnica, no asesoramiento jurídico. Los términos pueden cambiar y deben revalidarse antes de habilitar cada conector.
