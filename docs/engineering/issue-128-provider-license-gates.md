# Puertas de aprobación de fuentes externas — Issue #128

- **Consulta documental:** 2026-10-22
- **Estado:** evaluación documental preliminar; ninguna fuente queda autorizada automáticamente para uso comercial o redistribución.
- **Objetivo:** impedir que una API técnicamente accesible se trate como una fuente legalmente aprobada para un producto web/móvil con informes persistentes.

## Decisiones de integración

| Fuente | Evidencia oficial revisada | Restricción relevante | Decisión para el ecosistema |
|---|---|---|---|
| Binance Spot public market-data API | [Documentación oficial REST](https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md) y [Market Data Only URLs](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) | La documentación confirma endpoints públicos sin autenticación para datos de mercado; eso demuestra disponibilidad técnica, no por sí solo el alcance de los derechos comerciales, la retención o la redistribución del dato en un producto. | **HABILITADA SOLO PARA PRUEBAS TÉCNICAS DE SOLO LECTURA EN ESTA PR**. Antes de producción comercial, persistencia de largo plazo, exportación o redistribución, revisar y registrar las condiciones aplicables al producto y jurisdicción. |
| DefiLlama API gratuita | [Documentación oficial de API](https://api-docs.defillama.com/) y [Términos de uso vigentes](https://enterprise.defillama.com/terms), efectivos desde 24-06-2025 | La cláusula 7 limita el uso general a fines personales/no comerciales; la cláusula 8 prohíbe copia, republicación, explotación comercial sin consentimiento previo por escrito y el uso de robots/spiders. El acceso a la API pública oficial no equivale a autorización para automatizar captura comercial, retención o redistribución. | **BLOQUEADA para conector automático persistente/comercial** hasta obtener autorización escrita que cubra específicamente el producto, automatización, retención histórica, visualización y exportación. No activar el endpoint de producción por defecto. |
| CoinGecko API | [Términos de API](https://www.coingecko.com/en/api_terms), [planes y licencias](https://www.coingecko.com/en/api/pricing), [guía de licencias actualizada 19-10-2026](https://support.coingecko.com/articles/1043089972-what-are-the-differences-between-commercial-and-custom-licenses) | La guía oficial actualizada indica que los planes de pago incluyen uso comercial estándar con atribución; cachés de visualización deben refrescarse al menos cada 24 horas, los datos almacenados deben protegerse y eliminarse al terminar el acceso. La licencia estándar no incluye redistribución/sindicación, reventa de API ni datos reutilizables por usuarios; esos casos requieren licencia personalizada. El plan Demo/gratuito no concede por sí solo derechos comerciales. | **CANDIDATA CONDICIONADA; NO ACTIVAR AÚN**. Requiere seleccionar plan pagado, implementar atribución, política de refresh/cifrado/borrado y obtener confirmación/licencia adicional si el producto expone datos reutilizables, históricos descargables o redistribución. Hasta entonces, solo fixtures offline y capturas cuya retención esté autorizada. |
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

- DefiLlama queda bloqueada para captura automatizada persistente/comercial hasta autorización escrita; los términos vigentes incluyen una restricción explícita sobre robots/spiders.
- CoinGecko queda como candidata condicionada a un plan de pago, atribución, refresh de caché al menos cada 24 horas, cifrado y borrado al terminar la suscripción; redistribución o datos reutilizables requieren derechos adicionales.
- Los contratos de eventos y fundamentales/on-chain siguen offline. La PR #139 añade una captura técnica de solo lectura para Binance Spot; no implica autorización comercial ni habilita distribución de datos.
- Las conclusiones del informe continúan en `INDETERMINATE` si falta evidencia permitida, suficiente o temporalmente válida.

Esta nota se revalidó el 22-10-2026 contra la guía oficial de licencias de CoinGecko actualizada el 19-10-2026 y los términos de DefiLlama efectivos el 24-06-2025. Es una revisión documental técnica, no asesoramiento jurídico. Los términos pueden cambiar y deben revalidarse antes de habilitar cada conector.
