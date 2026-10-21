# Issue #18 — Propuesta de política de frescura, comisiones y coste total

- **Estado:** PROPUESTA PARA DECISIÓN DEL PROPIETARIO; no aprobada y no aplicable como criterio PASS.
- **Issue:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18
- **Línea base de trabajo:** `main`; el valor de esta propuesta es separar las decisiones pendientes de la implementación ya probada.
- **Modo operativo:** lectura pública solamente. No autoriza órdenes, trading, producción ni recomendaciones de inversión.

## 1. Regla de seguridad no negociable

Hasta que el propietario apruebe una versión fechada de esta política, el evaluador debe mantener la decisión global `INDETERMINATE`. Los valores de esta propuesta no deben interpretarse como umbrales aprobados. Un `PASS` dimensional solo indica que una dimensión satisface una regla aprobada y no garantiza ejecución ni convierte el resultado global en aprobado.

## 2. Frescura: dimensiones que no deben confundirse

| Campo | Significado | Fuente de evidencia | Regla |
|---|---|---|---|
| `source_event_at_utc` | Tiempo de evento declarado por el proveedor | Evento Binance Diff Depth `E`, convertido desde epoch milliseconds a UTC | No sustituir por la hora de captura ni por `lastUpdateId` |
| `received_at_utc` | Momento en que el cliente recibió el evento | Reloj local UTC en recepción | Registrar por evento; un valor aislado no prueba continuidad |
| `captured_at_utc` | Momento de persistencia del artefacto | Reloj local UTC | Solo acredita cuándo se guardó la evidencia |
| `evaluation_time_utc` | Momento en que se calculó el resultado | Reloj local UTC | Debe ser posterior o igual a los tiempos usados; si no, abstenerse |
| `clock_skew_estimate_ms` | Diferencia estimada entre reloj del cliente y del proveedor | Comprobación de tiempo del sistema y fuente de tiempo documentada | Si no puede estimarse con evidencia suficiente, la comparación de edad de evento queda indeterminada |

La sincronización del libro (secuencia `U/u`, snapshot y ausencia de huecos) es una condición de integridad, no una medida de frescura temporal. La edad de evento, la edad desde recepción y la continuidad de la sesión son dimensiones distintas.

## 3. Base normativa y decisiones de diseño

**No se atribuyen umbrales numéricos a ISO ni a Binance si sus fuentes oficiales no los establecen.** La versión anterior de esta propuesta incluía 2.000 ms, 1.000 ms, 24 horas y tamaños de 10/100/1.000 USDT como sugerencias internas sin respaldo normativo documentado. Se retiran como valores recomendados.

### Fuentes oficiales aplicables

- **ISO/IEC 25010:2023 — modelo de calidad del producto:** https://www.iso.org/standard/78176.html. Proporciona características y un marco para especificar, medir y evaluar calidad y criterios de aceptación; no prescribe un SLA universal de frescura de libros de Binance ni importes de órdenes para este proyecto.
- **ISO/IEC 27001:2022 — sistema de gestión de seguridad de la información:** https://www.iso.org/standard/27001. Aporta un marco de gestión de riesgos y controles de seguridad; no fija tolerancias de latencia de mercado ni caducidad universal de tarifas.
- **Documentación oficial de Binance Spot API y streams:** https://github.com/binance/binance-spot-api-docs. En `web-socket-streams.md`, Binance documenta para Diff. Depth Stream el tiempo de evento `E`, los identificadores `U/u`, y las velocidades de actualización publicadas (1.000 ms o 100 ms para los streams JSON descritos). Estas velocidades describen la publicación/actualización del stream, no una garantía de latencia extremo a extremo, edad máxima del dato en el cliente ni umbral de aceptación del ecosistema.
- **Comisiones oficiales de Binance Spot:** https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md y endpoint documentado `GET /api/v3/account/commission`. La respuesta de tarifas debe obtenerse para el símbolo y la cuenta relevantes; `POST /api/v3/order/test` con `computeCommissionRates` puede aportar estimación específica de los parámetros de una orden de prueba. Una consulta pública genérica no equivale necesariamente a la tarifa real de la cuenta.
- **Tarifas públicas de Pionex Spot:** https://www.pionex.com/fees. En la consulta del 2026-10-21 la página mostraba maker 0,050 % y taker 0,050 % para Spot y señalaba tarifas inferiores para VIP. Es una referencia pública general y dinámica, no prueba la tarifa efectiva de una cuenta concreta; debe archivarse la página consultada y verificarse la aplicabilidad al nivel de cuenta.

### Registro de requisitos y decisiones

| ID | Requisito verificable | Evidencia y criterio | Si falta evidencia |
|---|---|---|---|
| D18-01 | Identificar tiempo de evento, recepción y evaluación por separado | Payload oficial de Binance y reloj de recepción local; conservar los valores originales y su unidad | Frescura `INDETERMINATE` |
| D18-02 | Validar integridad temporal del reloj utilizado | Documentar fuente, método de sincronización y medición de incertidumbre/desfase; el límite de aceptación debe derivarse del contexto de uso y pruebas, no atribuirse a ISO/Binance | Frescura `INDETERMINATE` si no se puede demostrar la validez temporal |
| D18-03 | Aplicar correctamente el protocolo de libro local | Seguir el procedimiento oficial de snapshot + eventos, IDs `U/u`, descartes y detección de huecos | Libro no sincronizado o `RESYNC_REQUIRED`: no evaluar como libro válido |
| D18-04 | Definir el requisito operativo de frescura para el caso de uso | Medir latencia y edad con capturas representativas, distribución/percentiles, condiciones de red, comportamiento ante desconexión y riesgo del uso; registrar fuente y justificación de cualquier umbral interno | No declarar `PASS` hasta que exista criterio aprobado y evidencia suficiente |
| D18-05 | Calcular coste para tamaños relevantes al producto | Los tamaños deben venir de requisitos del producto/usuario y restricciones oficiales del símbolo (`exchangeInfo` filters), no de importes arbitrarios | Escenario no definido: coste comparativo `INDETERMINATE` |
| D18-06 | Obtener comisión aplicable al símbolo y tipo de orden | Endpoint oficial de comisión por cuenta/símbolo o respuesta `computeCommissionRates` para los parámetros evaluados; registrar descuentos, componentes y errores | Comisiones `INDETERMINATE` |
| D18-10 | Tratar tarifas públicas de Pionex sin asumir nivel VIP | Captura fechada de la página oficial de tarifas; verificar nivel/condiciones de la cuenta si se pretende estimar coste individual | La tarifa publicada general sirve como referencia, pero la comisión aplicable a la cuenta sigue `INDETERMINATE` si su nivel/condiciones no se verifican |
| D18-07 | No extrapolar más allá de la profundidad observada | Mostrar cantidad solicitada, cantidad cubierta y remanente; no afirmar ejecutabilidad total si el libro capturado no cubre la orden | Coste total `INDETERMINATE` para la orden completa |
| D18-08 | Rechazar timestamps ausentes, inválidos o inconsistentes | Pruebas de límites derivadas del contrato temporal y política aprobada; conservar error original | `INDETERMINATE`, sin corregir silenciosamente |
| D18-09 | Comparar costes homogéneos | Mismo mercado/unidad, tipo de ejecución, tamaño, ventana temporal, componentes de tarifa y supuestos declarados | No agregar; comparación `INDETERMINATE` |

### Cómo se fijará cualquier umbral interno

Un umbral que no venga prescrito por una fuente oficial solo podrá proponerse tras:
1. definir el contexto de uso y el daño potencial de datos atrasados;
2. recopilar mediciones reproducibles bajo condiciones representativas;
3. documentar método, muestra, distribución y limitaciones;
4. justificar el valor de aceptación respecto al riesgo y los objetivos del producto;
5. versionar y aprobar el criterio, con trazabilidad a evidencia y pruebas.

Esto es una decisión de ingeniería y gestión de riesgo del proyecto, no un requisito numérico de ISO ni un SLA de Binance. Hasta que exista esa base, no se inventará un valor de aceptación: el estado será `INDETERMINATE`.
## 4. Evidencia de tarifas por ejecución

Para cada fuente oficial y mercado evaluado, el artefacto debe conservar:

- proveedor, mercado spot, endpoint o URL oficial y fecha/hora de consulta UTC;
- payload original o copia permitida por los términos del proveedor, hash SHA-256 y versión del parser;
- maker/taker, nivel de cuenta, descuentos, activo de comisión y condiciones de elegibilidad;
- si la tarifa es pública genérica o confirmada para la cuenta real; no presentarlas como equivalentes;
- tarifa de retiro, activo y red únicamente si el escenario incluye retiro; no mezclarla con la comisión de trading;
- errores, autenticación requerida, límites y campos ausentes, sin persistir credenciales ni secretos.

Una configuración `maker_fee_bps=0` o `taker_fee_bps=0` no es evidencia de tarifa cero. Si el proveedor no permite confirmar el nivel de cuenta aplicable sin autenticación, la dimensión permanece indeterminada hasta que el propietario suministre evidencia permitida y saneada o apruebe explícitamente un escenario genérico claramente rotulado.

## 5. Composición del coste

Para cada escenario de compra/venta, informar separadamente:

1. spread observado en el snapshot válido;
2. slippage estimado del tamaño solicitado y cantidad no cubierta;
3. comisión maker/taker elegida según el tipo de ejecución supuesto;
4. descuento/activo de pago y conversión usada, si aplica;
5. tarifa de retiro/red solo si forma parte del escenario;
6. tiempo de fuente, recepción, evaluación, identificador de sesión, secuencia del libro y limitaciones.

No presentar la suma como coste garantizado de ejecución. Latencia, cambios del libro, órdenes parciales, impacto fuera de la profundidad capturada, límites de cuenta y condiciones reales pueden alterar el coste.

## 6. Criterios de abstención obligatoria

El resultado económico global debe seguir `INDETERMINATE` si ocurre cualquiera de estas condiciones:

- política sin aprobar o configuración sin identificador/versión aprobados;
- timestamp de evento, recepción o evaluación ausente, inválido o temporalmente inconsistente;
- calidad del reloj insuficiente o ausencia de un criterio interno justificado y aprobado para interpretar la frescura;
- sesión no sincronizada, desconexión, hueco de secuencia o evento inválido;
- tarifa desconocida, vencida, no oficial o no aplicable al nivel de cuenta/escenario;
- libro truncado o insuficiente para cubrir el tamaño requerido por el escenario de producto;
- unidad, mercado, horizonte o definición de coste no comparable.

Un resultado `PASS` en integridad de captura no levanta ninguno de estos bloqueos.

## 7. Pruebas automatizadas requeridas

La suite debe incluir y preservar casos para:

- timestamp de evento ausente, malformado, futuro y obsoleto;
- calidad temporal del reloj insuficiente, incluyendo pruebas de los límites definidos por una política justificada y aprobada (sin inventar límites normativos);
- evento fresco pero recepción/captura vieja y el caso inverso;
- sesión desconectada, secuencia con hueco y libro sincronizado con evento fresco;
- tarifa ausente, error de endpoint, nivel de cuenta/símbolo incompatible y tarifa configurada a cero sin evidencia oficial;
- profundidad insuficiente para los tamaños de orden definidos por requisitos del producto y filtros oficiales del símbolo, incluyendo cantidad no cubierta;
- moneda/unidad no comparable y retiro no aplicable;
- repetición de la evaluación sobre el mismo artefacto/configuración, con resultado idéntico.

Las pruebas con reloj simulado validan la lógica, no sustituyen evidencia de una sesión real. La ejecución en vivo debe ser explícita, acotada, de solo lectura y guardar artefacto saneado, SHA de código, configuración, hora UTC y limitaciones.

## 7.1 Trazabilidad de las fuentes

Las fuentes oficiales determinan el formato y comportamiento documentado de la API, el mecanismo de obtención de tarifas y el marco de calidad/gestión. No se debe inferir de ellas una garantía que no expresan. Antes de usar una URL como evidencia, registrar fecha/hora de consulta UTC, versión/revisión del documento cuando esté disponible, endpoint/mercado y hash del artefacto obtenido. La documentación puede cambiar; volver a consultarla al ejecutar la evaluación.

## 8. Evidencia actual y trabajo restante

Ya existen un adaptador Binance WebSocket de solo lectura, sincronización snapshot + eventos, detección de huecos, captura separada de tiempo de evento/recepción y pruebas offline. Eso demuestra lógica de contrato bajo fixtures; **no demuestra que se haya ejecutado una captura en vivo ni que las tarifas de la cuenta estén verificadas**.

Para cerrar el Issue #18 se requieren conjuntamente:
- requisitos de frescura y tamaños de escenarios derivados del contexto del producto, mediciones y filtros oficiales; cualquier umbral interno debe estar justificado y aprobado, sin atribuirlo a ISO/Binance;
- implementación enlazada a esa política aprobada;
- ejecución de pruebas y artefactos reproducibles;
- evidencia real de captura en vivo cuando el criterio requiera frescura operativa;
- evidencia oficial de tarifas aplicables al escenario y la cuenta, o abstención explícita documentada.

**Estado actual recomendado: NO CERRAR.** Esta propuesta organiza decisiones y reduce ambigüedad, pero no constituye aprobación, evidencia de mercado en vivo, autorización de trading ni preparación para producción.
