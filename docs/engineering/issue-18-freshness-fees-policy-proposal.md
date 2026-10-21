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

## 3. Decisiones que requieren aprobación explícita

Los valores numéricos siguientes son **propuestas iniciales para discusión**, no valores desplegados ni aprobados.

| ID | Decisión | Propuesta para revisión | Qué pasa si no se aprueba |
|---|---|---|---|
| D18-01 | Edad máxima de evento para libro WebSocket de profundidad | 2.000 ms en el instante de evaluación, siempre que el reloj supere la comprobación D18-02 | `source_freshness=INDETERMINATE` |
| D18-02 | Tolerancia máxima de desfase reloj cliente/proveedor | 2.000 ms; fuente y método de estimación deben quedar registrados | `source_freshness=INDETERMINATE` |
| D18-03 | Antigüedad máxima desde la recepción del último evento aplicado | 1.000 ms para una observación de libro en vivo; requiere conexión sincronizada y sin huecos | `source_freshness=INDETERMINATE` |
| D18-04 | Edad máxima del documento oficial de tarifas | 24 h desde la consulta para tarifa dinámica; consultar fuente oficial en cada ejecución económica | `fees=INDETERMINATE` si no se actualiza o no se conserva la respuesta |
| D18-05 | Tamaños de orden de referencia para comparar coste | Escenarios cotizados de 10, 100 y 1.000 USDT, convertidos a cantidad base al precio medio fechado; cubrir compra y venta | Coste comparativo no ejecutado/indeterminado |
| D18-06 | Alcance de tarifa | Spot, maker y taker por separado; nivel de cuenta aplicable, descuento, activo de pago y condiciones; retiros/red solo cuando el flujo de producto los incluya | `fees=INDETERMINATE` |
| D18-07 | Profundidad insuficiente | Si no cubre el 100 % del tamaño de referencia, no publicar slippage como si la orden completa fuera ejecutable; conservar cantidad no cubierta | Coste total `INDETERMINATE` para ese escenario |
| D18-08 | Política de timestamps ausentes/malformados/futuros | Ausente o malformado: `INDETERMINATE`; evento futuro más allá de tolerancia aprobada: `INDETERMINATE`; nunca corregir silenciosamente | Sin excepción implícita |
| D18-09 | Comparación entre exchanges | No agregar costes con distintas monedas, niveles de cuenta, ventanas o conceptos de tarifa; mostrar componentes y supuestos por separado | Comparación global `INDETERMINATE` |

El propietario debe aprobar, modificar o rechazar cada propuesta antes de que se cambie el estado a política aprobada. La implementación puede añadir validaciones y conservar evidencia sin asumir esa aprobación.

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
- reloj fuera de tolerancia o sin evidencia para evaluar esa tolerancia;
- sesión no sincronizada, desconexión, hueco de secuencia o evento inválido;
- tarifa desconocida, vencida, no oficial o no aplicable al nivel de cuenta/escenario;
- libro truncado o insuficiente para cubrir el tamaño de referencia;
- unidad, mercado, horizonte o definición de coste no comparable.

Un resultado `PASS` en integridad de captura no levanta ninguno de estos bloqueos.

## 7. Pruebas automatizadas requeridas

La suite debe incluir y preservar casos para:

- timestamp de evento ausente, malformado, futuro y obsoleto;
- desfase de reloj por debajo, en el límite y por encima del umbral aprobado;
- evento fresco pero recepción/captura vieja y el caso inverso;
- sesión desconectada, secuencia con hueco y libro sincronizado con evento fresco;
- tarifa desconocida, oficial obsoleta, nivel de cuenta incompatible y tarifa configurada a cero sin evidencia;
- profundidad insuficiente para cada tamaño de orden, incluyendo cantidad no cubierta;
- moneda/unidad no comparable y retiro no aplicable;
- repetición de la evaluación sobre el mismo artefacto/configuración, con resultado idéntico.

Las pruebas con reloj simulado validan la lógica, no sustituyen evidencia de una sesión real. La ejecución en vivo debe ser explícita, acotada, de solo lectura y guardar artefacto saneado, SHA de código, configuración, hora UTC y limitaciones.

## 8. Evidencia actual y trabajo restante

Ya existen un adaptador Binance WebSocket de solo lectura, sincronización snapshot + eventos, detección de huecos, captura separada de tiempo de evento/recepción y pruebas offline. Eso demuestra lógica de contrato bajo fixtures; **no demuestra que se haya ejecutado una captura en vivo ni que las tarifas de la cuenta estén verificadas**.

Para cerrar el Issue #18 se requieren conjuntamente:
- decisión del propietario sobre D18-01 a D18-09, registrada con fecha y versión;
- implementación enlazada a esa política aprobada;
- ejecución de pruebas y artefactos reproducibles;
- evidencia real de captura en vivo cuando el criterio requiera frescura operativa;
- evidencia oficial de tarifas aplicables al escenario y la cuenta, o abstención explícita documentada.

**Estado actual recomendado: NO CERRAR.** Esta propuesta organiza decisiones y reduce ambigüedad, pero no constituye aprobación, evidencia de mercado en vivo, autorización de trading ni preparación para producción.
