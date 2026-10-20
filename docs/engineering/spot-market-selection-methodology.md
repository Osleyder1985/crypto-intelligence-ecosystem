# Metodología reproducible para seleccionar mercados spot

- **Estado:** especificación propuesta; no aprobada como línea base.
- **Issue principal:** [#7 — Selección reproducible de exchanges y pares spot por liquidez](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7).
- **Relación:** [Issue #13 — Evaluación histórica, ranking, eventos y liquidez](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13).
- **Matriz de criterios:** [matriz de cierre verificable #7/#13](acceptance-closure-matrix-issues-7-13.md).
- **Límite:** análisis de solo lectura. Esta especificación no consulta APIs, no contiene resultados de mercado y no autoriza operaciones reales.

## 1. Propósito y principios

La metodología debe permitir reconstruir, para una fecha y una configuración conocidas, por qué un mercado spot/par fue incluido, excluido o quedó sin conclusión. No se utilizará el precio nominal del token ni el volumen declarado como sustituto de liquidez ejecutable.

Principios obligatorios:

1. Comparar únicamente mercados spot; excluir futuros, perpetuos, margen y productos apalancados.
2. Conservar por separado los hechos observados, los cálculos derivados, los umbrales configurados y la decisión final.
3. Tratar la falta de datos como desconocida, nunca convertirla silenciosamente en cero.
4. No comparar cifras con unidades, ventanas, timestamps o definiciones incompatibles.
5. Registrar captura y timestamp de origen por separado, en UTC normalizado y conservando el valor original y su zona.
6. Versionar el método, la configuración, el parser y el manifiesto de fuentes.
7. No producir una puntuación agregada que oculte un bloqueo crítico.
8. La disponibilidad del par en el exchange de ejecución (Pionex, según el alcance actual) es un control separado de la liquidez observada en exchanges de referencia.

## 2. Alcance de evaluación

Universo inicial propuesto por el Issue #7:

- Referencia de comparación: Binance.
- Comparación: OKX, Bybit, MEXC, Gate y Bitget.
- Plataforma de ejecución que debe verificarse por separado: Pionex.
- Solo spot; los derivados no se mezclan con el conjunto de evaluación.

Este universo es un punto de partida documental, no evidencia de que cada API, par o región esté disponible. El alcance ampliado de 15–20 exchanges del Issue #13 queda condicionado a cobertura comprobada, restricciones geográficas/legales, límites de API, calidad de datos y comparabilidad. No se fuerza un número objetivo si no hay evidencia suficiente.

## 3. Entidades y claves de datos

Cada observación debe identificar al menos:

| Campo | Definición | Regla |
|---|---|---|
| `observation_id` | Identificador único de la observación | No se reutiliza entre capturas |
| `exchange_id` | Identificador canónico del exchange | Mantener alias/nombre original por separado |
| `market_type` | Tipo de mercado | Debe ser `spot`; otro valor queda fuera del análisis |
| `symbol_native` | Símbolo exacto del proveedor | Conservarlo sin modificar |
| `base_asset`, `quote_asset` | Activos base y cotizado normalizados | Registrar regla y versión de normalización |
| `source_kind` | Tipo de fuente | Distinguir ticker, libro, trades, tarifas y listado |
| `source_ref` | Endpoint/URL/documento/identificador de origen | No registrar secretos ni tokens de acceso |
| `source_timestamp` | Hora que declara la fuente | Nulo si no se proporciona; no inventarlo |
| `captured_at_utc` | Hora de recepción/captura | ISO 8601 UTC; separar del tiempo de mercado |
| `payload_hash` | Hash del payload original cuando sea permitido | Identifica la entrada, no prueba su veracidad |
| `parser_version` | Versión del parser | Obligatoria para reproducir transformación |
| `quality_status` | Resultado de controles de calidad | `VALID`, `INVALID` o `INDETERMINATE` |
| `limitations` | Limitaciones observadas | Lista explícita; vacía solo si se evaluó |

Las observaciones de ticker, libro de órdenes, trades recientes, tarifas y estado/listado del par son registros distintos. No deben fusionarse en una sola fila sin conservar las referencias a cada fuente y su timestamp.

## 4. Contrato mínimo de captura

Una captura de evaluación debe persistir:

- `evaluation_id`, fecha objetivo, fecha/hora de ejecución y zona horaria.
- Versión del método y del archivo de configuración.
- Universo de exchanges/pares solicitado y reglas de normalización.
- Fuentes consultadas, endpoints, parámetros no secretos, códigos de respuesta y errores.
- Payload original o referencia/hash verificable, sujeto a licencia y condiciones de uso.
- Transformaciones, unidades, redondeos y campos descartados.
- Resultado de cada prueba de calidad, incluidos resultados negativos.
- Resultado por dimensión, razón de exclusión o causa de indeterminación.
- Versión del código y artefacto de salida.

La hora de captura no se debe presentar como hora del dato de mercado. Si una fuente no entrega timestamp, la observación debe indicarlo y no puede satisfacer un criterio de frescura que dependa de esa marca temporal.

## 5. Métricas y definiciones

Las fórmulas siguientes fijan cómo calcular métricas; no fijan umbrales de aceptación. Los parámetros de ventanas, bandas de precio, tamaños de orden y límites deben aprobarse en configuración antes de evaluar resultados.

### 5.1 Volumen spot

- Registrar volumen, moneda/unidad, ventana, fuente y si la cifra es volumen base, volumen cotizado o estimación convertida.
- No comparar volumen base con volumen cotizado sin una conversión explícita y precio de referencia fechado.
- No sumar ventanas ni exchanges si las ventanas temporales se solapan o las unidades no son comparables.
- Para estabilidad, calcular cada ventana aprobada por separado y mostrar la serie; no extrapolar una observación de 24 h como estabilidad de largo plazo.
- Investigar discrepancias entre proveedores antes de seleccionar un valor representativo.

### 5.2 Spread bid-ask

Para mejor bid (b) y mejor ask (a), válidos y positivos:

[
\text{mid} = \frac{a+b}{2}
\qquad
\text{spread}_{bps} = \frac{a-b}{\text{mid}}\times 10{,}000
]

Si falta bid/ask, el precio es no positivo, el libro está cruzado ((b>a)) o el snapshot no supera controles de calidad, la métrica no pasa a cero: se marca inválida o indeterminada con razón explícita. Si (a=b), el spread matemático es cero, pero el registro debe conservar esa observación y revisar la calidad del snapshot.

### 5.3 Profundidad

Para una banda aprobada alrededor del mid, sumar cantidades y valor nocional por lado dentro de esa banda. Documentar:

- definición exacta de la banda (porcentual o absoluta);
- niveles incluidos, moneda de las cantidades y conversión de nocional;
- lado bid/ask evaluado;
- profundidad disponible y porcentaje de banda cubierto;
- timestamp y antigüedad de la captura.

No inferir profundidad desde el volumen de 24 h. Si la respuesta del libro está truncada o no cubre la banda requerida, el resultado será indeterminado o insuficiente, según una regla previamente aprobada.

### 5.4 Slippage estimado por tamaño de orden

Dado un libro ask para compra o bid para venta, simular el consumo secuencial de niveles para un tamaño de orden configurado. Registrar el lado, unidad de tamaño (base o cotizada), niveles consumidos, cantidad ejecutable, cantidad no cubierta y VWAP estimado.

Para compra, el coste de referencia puede expresarse como:

[
\text{slippage}_{bps} =
\left(\frac{\text{VWAP}_{buy}}{\text{mid}}-1\right)\times 10{,}000
]

Para venta:

[
\text{slippage}_{bps} =
\left(1-\frac{\text{VWAP}_{sell}}{\text{mid}}\right)\times 10{,}000
]

La convención de signos debe mantenerse uniforme en todos los informes. La estimación usa un snapshot y no garantiza ejecución real; no modela por sí sola latencia, cambios del libro, impacto de mercado más allá de la profundidad observada ni ejecución parcial en producción. Si el libro no cubre el tamaño de referencia, informar cantidad no cubierta y no publicar una cifra de slippage como si el tamaño completo fuera ejecutable.

### 5.5 Comisiones

Separar maker/taker, tarifa de retiro, red, activo de pago, nivel de cuenta, descuentos y condiciones aplicables. Cada tarifa debe incluir fuente oficial, fecha de consulta y supuestos. Si la tarifa depende del usuario o no puede confirmarse, mostrarla como desconocida o escenario, no como tarifa universal.

### 5.6 Disponibilidad exacta del par en Pionex

La validación debe confirmar el mercado spot exacto, activo base, activo cotizado, estado del par y fuente/fecha. Una coincidencia aproximada de ticker no es suficiente. Si el par no se confirma, no debe aparecer como ejecutable en el universo de oportunidades; la razón debe distinguir entre no listado, suspendido, símbolo ambiguo, restricción de acceso y evidencia no concluyente.

## 6. Controles de calidad de datos

Como mínimo, probar:

- campos obligatorios ausentes o vacíos;
- tipos inválidos, valores no finitos y cantidades/precios negativos;
- duplicados según clave de observación;
- timestamps ausentes, fuera de orden o imposibles;
- datos caducados según un límite configurado;
- libro vacío, cruzado o truncado;
- unidad, moneda o ventana incompatible;
- discrepancias entre fuentes;
- símbolos duplicados/ambiguos tras normalización;
- payload que no coincide con el esquema esperado;
- errores de API, rate limit, timeout y respuesta parcial.

Un valor atípico no se elimina automáticamente: se conserva y se etiqueta para investigación conforme a una regla aprobada. La eliminación o corrección debe quedar documentada y ser reproducible.

## 7. Motor de decisión: sin umbrales implícitos

Cada dimensión emite uno de estos estados:

- **PASS:** la evidencia es válida y satisface un criterio/umbral aprobado previamente.
- **FAIL:** la evidencia válida incumple un criterio/umbral aprobado o se confirma una condición de exclusión.
- **INDETERMINATE:** evidencia insuficiente, contradictoria o no comparable.
- **NOT_APPLICABLE:** dimensión no aplicable con justificación documentada.
- **NOT_RUN:** prueba no ejecutada.

La decisión por par conserva el vector de estados por dimensión; no se reduce a una media ponderada por defecto. La política de bloqueo debe definir qué dimensiones son críticas y cómo se trata cada estado. Sin esa política aprobada, el resultado global será **INDETERMINATE**, aunque algunas métricas pasen.

Configuración obligatoria antes de producir una decisión:

- ventanas de volumen y tolerancia a discrepancias;
- edad máxima por clase de dato;
- bandas de profundidad;
- tamaños de orden y unidad;
- límites de spread/slippage;
- política de comisiones;
- exchanges/regiones/par elegibles;
- condiciones críticas de exclusión;
- versión y fecha de aprobación.

Los valores faltantes en esta configuración provocan un error de configuración o un resultado indeterminado; nunca se completan con valores por defecto ocultos.

## 8. Resultado de evaluación esperado

Cada fila de salida por exchange/par debe contener:

| Campo | Propósito |
|---|---|
| `evaluation_id`, `method_version`, `config_version` | Identidad y reproducibilidad |
| `exchange_id`, `market_type`, `symbol_native`, `base_asset`, `quote_asset` | Identificación de mercado |
| `availability_status` | Estado confirmado del par en la plataforma objetivo |
| `volume_status`, `spread_status`, `depth_status`, `slippage_status`, `fees_status`, `api_status`, `asset_risk_status`, `freshness_status` | Resultado separado por dimensión |
| `decision_status` | PASS/FAIL/INDETERMINATE/NOT_RUN según política aprobada |
| `decision_reasons` | Códigos y explicaciones por dimensión |
| `source_refs` | Referencias a cada observación usada |
| `missing_data`, `limitations` | Incertidumbres y limitaciones explícitas |
| `evaluated_at_utc` | Hora de evaluación |
| `artifact_ref` | Ubicación o identificador del artefacto reproducible |

La salida debe permitir responder: qué dato se usó, de dónde salió, cuándo se capturó, cómo se calculó, qué configuración se aplicó y por qué la decisión quedó en ese estado.

## 9. Plan de validación y criterios de aceptación

| Prueba | Fixture/caso | Resultado esperado |
|---|---|---|
| Par de mercado no spot | Registro etiquetado como futuro | Excluido del universo spot con razón explícita |
| Bid/ask válido | Libro con precios positivos y ask mayor o igual que bid | Spread calculado con fórmula y unidad documentadas |
| Libro cruzado | Bid mayor que ask | Observación inválida o indeterminada; nunca spread negativo aceptado silenciosamente |
| Libro incompleto | Profundidad menor al tamaño de orden | Cantidad no cubierta registrada; slippage de tamaño completo no afirmado |
| Timestamp ausente | Fuente sin tiempo de mercado | Frescura indeterminada cuando la política requiere ese timestamp |
| Unidad incompatible | Volumen base comparado con volumen cotizado | Comparación bloqueada hasta conversión documentada |
| Par ambiguo en Pionex | Símbolo similar pero activos base/cotizado distintos | No se confirma disponibilidad |
| Umbral no aprobado | Configuración sin límite de spread o slippage requerido | Evaluación global indeterminada/error de configuración |
| Repetición determinista | Mismos payloads, código y configuración | Mismos resultados derivados, salvo campos de ejecución explícitamente variables |
| Fuente discrepante | Dos fuentes con resultados fuera de tolerancia configurada | Discrepancia visible; no se escoge silenciosamente el valor favorable |

Los fixtures y las pruebas deben implementarse y ejecutarse antes de marcar estas filas como PASS. Esta tabla es todavía una especificación de pruebas, no evidencia de ejecución.

## 10. Decisiones pendientes

1. Aprobar ventanas, bandas, tamaños de orden y umbrales por dimensión.
2. Aprobar política de exclusión crítica y reglas para estado global.
3. Nombrar responsables humanos de mercado/datos, cuantitativo, riesgo y QA.
4. Confirmar regiones objetivo, condiciones de proveedores y cobertura real de cada API.
5. Decidir política de retención y reproducción cuando licencias impidan guardar payloads.
6. Ejecutar una prueba de concepto de captura en modo solo lectura, sin secretos de trading.
7. Revisar resultados adversos y límites de cobertura antes de ampliar el universo.

## 11. Límites de esta especificación

- No contiene capturas reales ni afirma que algún exchange/par pase.
- No fija umbrales arbitrarios ni recomienda activos de inversión.
- No garantiza que el histórico de profundidad esté disponible; la captura propia solo genera historial desde su inicio.
- No ejecuta órdenes ni requiere claves privadas/API de trading.
- No acredita cumplimiento ISO ni validación independiente.


## 12. Estado del prototipo ejecutable

Se incorporó una primera implementación de solo lectura para probar fórmulas y reglas de decisión con fixtures sintéticos:

- Motor: [scripts/market_selection/selector.py](../../scripts/market_selection/selector.py).
- Pruebas: [tests/market_selection/test_selector.py](../../tests/market_selection/test_selector.py).
- Workflow: [.github/workflows/spot-market-selection.yml](../../.github/workflows/spot-market-selection.yml).

### Evidencia de CI

- Commit de referencia de las pruebas adversariales: 51cdf528a03cf65af901db0bd5c658c0a99f5ef2.
- [Ejecución del selector #10](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364246863): completada con éxito; el log registra 24 pruebas ejecutadas y resultado OK.
- [Validación de trazabilidad #39](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364246855): completada con éxito.

Las pruebas cubren spread, profundidad, slippage por VWAP, libro cruzado, profundidad insuficiente, mercado no spot, disponibilidad no confirmada, configuración incompleta/no aprobada y repetibilidad determinista.

### Límites de esta evidencia

- Los datos de prueba son sintéticos; no se consultaron exchanges ni se capturaron libros reales.
- La referencia de aprobación del fixture es TEST-ONLY; no representa aprobación humana de umbrales ni autoriza usar esa configuración en producción.
- No están implementadas la captura de proveedores, frescura temporal, tarifas, evaluación de riesgo del activo ni verificación real de pares Pionex.
- El éxito de estas pruebas no demuestra rentabilidad, ejecución real, cobertura de mercado ni conformidad ISO.
- La metodología y los umbrales continúan propuestos; el prototipo no debe utilizarse para decisiones de inversión reales.


## 13. Ampliación del prototipo: frescura y tarifas (en validación)

Se amplió el motor para que no considere suficiente un libro numéricamente válido si la temporalidad del dato no puede demostrarse. La observación debe incluir `source_timestamp_utc`, `captured_at_utc` y `evaluation_time_utc`, todos ISO-8601 con zona horaria explícita. La configuración debe definir `max_source_lag_seconds` y `max_snapshot_age_seconds`. Marcas temporales ausentes, sin zona, inconsistentes o futuras provocan `INDETERMINATE`; superar límites configurados produce `FAIL` en la dimensión de frescura.

También se añadieron campos explícitos `maker_fee_bps` y `taker_fee_bps`. El motor expone tarifas por lado y una estimación de tarifa taker de ida y vuelta (dos lados). Este cálculo **no** incluye automáticamente retiros, red, descuentos, niveles de cuenta ni condiciones particulares; la dimensión `fees = PASS` significa únicamente que los inputs de tarifas configurados son numéricamente válidos, no que la operación sea rentable o que la tarifa haya sido verificada con el exchange.

La configuración del fixture continúa marcada como TEST-ONLY. Los nuevos controles no equivalen a captura de datos real, validación de tarifas oficiales ni aprobación de una política financiera. La ejecución del selector #10 confirmó 24 pruebas aprobadas; se añadieron casos adversariales para niveles de precio duplicados, booleanos usados como tarifas y timestamps de captura futuros. Esta evidencia solo valida la lógica de fixtures sintéticos, no fuentes ni mercados reales.


## 14. Contrato normalizado y adaptador público Binance Spot (implementación inicial)

Se añadieron los siguientes componentes en la rama del PR:

- [Contrato normalizado](../../scripts/market_selection/data_contract.py): versión `market-observation-v1`, validación estructural, timestamps ISO-8601 con zona explícita, campos de procedencia, hash SHA-256, control de duplicados en niveles y estados de calidad.
- [Lector público Binance Spot](../../scripts/market_selection/binance_public.py): consulta de solo lectura a `GET /api/v3/depth` y `GET /api/v3/exchangeInfo`, sin claves, secretos ni métodos de envío de órdenes.
- [Pruebas deterministas](../../tests/market_selection/test_data_contract_and_binance.py): respuestas simuladas para libro válido, JSON inválido, error de API, libro cruzado, niveles duplicados, símbolo inválido, estado de símbolo, unión de metadatos exactos, bloqueo de libro cuando el símbolo no está disponible y hash de ambos payloads.

### Reglas importantes de procedencia y calidad

1. El hash se calcula sobre los bytes exactos de la respuesta recibida; no demuestra que la fuente sea correcta ni que el dato sea auténtico.
2. El payload original no se persiste en el registro de observación (`raw_payload_retained=false`). El hash permite comparar una copia externa si se conserva conforme a la política aplicable, pero no reconstruir por sí solo la respuesta.
3. El snapshot de profundidad de Binance expone `lastUpdateId`, no un timestamp de evento equivalente a la hora de mercado. Por ello, `source_timestamp_utc=null` y `quality_status=INDETERMINATE`; no se permite convertir la hora de captura en timestamp de origen.
4. El método `fetch_market_snapshot` consulta `exchangeInfo` y profundidad por separado, exige coincidencia exacta del símbolo y une `baseAsset`/`quoteAsset` al snapshot solo si el par está confirmado como Spot negociable. Conserva por separado las referencias, hashes y horas de captura de ambos payloads. El snapshot sigue `INDETERMINATE` por falta de timestamp de origen de la profundidad.
5. El estado de disponibilidad describe exclusivamente el listado/estado reportado por Binance. No demuestra que el mismo par esté disponible en Pionex, que pueda usarse en una región concreta o que sea apropiado para invertir.
6. El adaptador valida símbolos y límites, limita el tamaño de respuesta y distingue errores HTTP/transporte, JSON inválido, errores declarados por la API y payloads fuera de esquema. Los tests inyectan un transporte simulado: no dependen de una conexión real.
7. La captura real, las condiciones de servicio, límites de frecuencia, política de reintentos, retención de payloads y reconciliación automática con Pionex permanecen pendientes. No se afirma que se haya consultado el mercado en vivo ni que un par real haya superado los criterios de selección.

### Ejecución reproducible

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests/market_selection -p 'test_*.py' -v
```

La ejecución de CI asociada al commit que incorpora estos componentes debe verificarse antes de registrar PASS. El resultado de los tests sintéticos no equivale a una prueba de integración contra Binance ni a validación independiente del contrato.


### Evidencia CI de esta ampliación

- Commit de código y corrección del contrato: `62af41bf0161fd15b9d653fb64eabb47960131bc`.
- [Ejecución del selector #16](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364681504): `completed / success`; el log confirma `Ran 39 tests`, incluidas las pruebas nuevas del contrato y del lector público.
- [Validación de trazabilidad #46](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364681509): en curso al redactar esta actualización; no se registra todavía como PASS.
- La ejecución #15 falló inicialmente en dos pruebas porque la validación de activos desconocidos no coincidía con el estado `INDETERMINATE`. La regla se corrigió en el commit indicado y la ejecución #16 quedó en éxito. Se conserva esta incidencia como evidencia del ciclo de corrección, no se oculta.
- El éxito de #16 valida fixtures sintéticos y la implementación en CI; **no** acredita una consulta real a Binance, disponibilidad en Pionex, validez de tarifas, rentabilidad ni conformidad ISO.


### Evidencia final de CI para la unión de metadatos

- Commit de implementación y prueba: `df8da4d0c567eabb70ef4b9a9519023b73beb607`.
- [Ejecución del selector #20](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364821104): **completed / success**; log confirma 41 pruebas ejecutadas y `OK`.
- [Validación de trazabilidad #47](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39364821165): **completed / success**.
- Se comprobó que el snapshot solo une base/cotizado cuando `exchangeInfo` confirma el símbolo exacto como Spot negociable, conserva hash y referencia de ambas respuestas y no solicita el libro cuando el símbolo está ausente.
- El contrato ahora impide declarar `quality_status=VALID` si faltan los metadatos base/cotizado o el timestamp de origen. La profundidad sin timestamp de evento continúa explícitamente en `INDETERMINATE`.
- En una ejecución anterior, la prueba del contrato falló porque el fixture declaraba calidad `VALID` sin timestamp de origen. Se corrigió el fixture para reflejar el contrato; la ejecución #20 pasó. Se mantiene la distinción entre evidencia sintética CI y prueba de integración real.


## 15. Verificación exacta de disponibilidad en Pionex

Se añadió [`pionex_public.py`](../../scripts/market_selection/pionex_public.py) para consultar el endpoint público `GET /api/v1/common/symbols` sin credenciales ni operaciones de trading. La implementación sigue el contrato público descrito en la [documentación oficial de Common Symbols de Pionex](https://www.pionex.com/docs/api-docs/trade-api/common) y la [especificación OpenAPI oficial](https://github.com/pionex-official/pionex-open-api/blob/main/openapi.yaml).

La validación exige una coincidencia exacta del símbolo `BASE_QUOTE`, tipo `SPOT`, coincidencia de `baseCurrency`/ `quoteCurrency` y `enable=true`. Un símbolo ausente, deshabilitado o no Spot no se etiqueta como disponible. Respuestas malformadas, fallos API o metadatos base/cotizado contradictorios generan error explícito, no una falsa conclusión de indisponibilidad.

El resultado conserva URL consultada, timestamp de respuesta si está disponible, hora de captura y SHA-256 de los bytes recibidos. Si falta el timestamp de respuesta, la frescura queda `INDETERMINATE`; no se inventa una marca temporal. La disponibilidad es una observación puntual y no demuestra acceso regional, elegibilidad de cuenta, liquidez suficiente, comisiones, calidad de inversión ni rentabilidad.

Las pruebas de [`test_pionex_public.py`](../../tests/market_selection/test_pionex_public.py) usan payloads sintéticos. No se ha hecho una llamada real al endpoint desde esta implementación; la verificación de un símbolo en vivo debe ejecutarse de forma separada y registrarse con fecha, respuesta/hash y limitaciones antes de usarla como evidencia operativa.


## 16. Captura de integración pública reproducible

Se añadieron:

- [`capture_public_market_data.py`](../../scripts/market_selection/capture_public_market_data.py): solicita tres respuestas públicas: disponibilidad exacta de `BTC_USDT` en Pionex, `exchangeInfo` de `BTCUSDT` en Binance y snapshot de profundidad de Binance con 20 niveles. No usa credenciales ni envía órdenes.
- [Workflow de captura](../../.github/workflows/public-market-capture.yml): ejecuta la captura en PR cuando cambian el script o el workflow, y permite ejecución manual. Siempre intenta subir el artefacto aunque falle alguna API; el job falla si una o más capturas no se validan.
- [Pruebas de integridad de captura](../../tests/market_selection/test_public_market_capture.py): verifican SHA-256 sobre bytes exactos, reversibilidad de Base64 y rechazo de JSON inválido/esquemas no objeto.

El artefacto `public-market-capture.json` incluye endpoint, hora de inicio/captura UTC, código HTTP, tamaño, SHA-256, respuesta original codificada en Base64, JSON parseado y resumen de la evaluación. La retención configurada del artefacto es de 14 días. Las respuestas se guardan como evidencia de CI y no se añaden al repositorio como si fueran datos permanentes.

### Interpretación de resultados

- Cada proveedor se evalúa por separado; un fallo de Pionex no convierte el estado de Binance en fallo y viceversa.
- `overall_status=PASS` solo se produce cuando las tres respuestas HTTP/JSON se capturan y validan.
- `availability=confirmed` es una observación puntual según los campos públicos de listado; no acredita acceso regional/de cuenta ni liquidez suficiente.
- SHA-256 acredita identidad de bytes, no autenticidad criptográfica del proveedor.
- La profundidad de Binance no incluye un timestamp de evento equivalente; no se infiere frescura de mercado a partir de la hora local de captura.
- La captura inicial y los tests de integración deben distinguirse de los tests unitarios simulados. Hasta que el workflow publique el artefacto, no se declara una captura integrada completada.


### Evidencia de integración real — 2026-10-20

La ejecución [Public market API capture #39365452045](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365452045) terminó en `completed / success`, con `overall_status=PASS`. Artefacto: [public-market-capture-39365452045-1](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365452045/artifacts/12238519886). SHA-256 del ZIP del artefacto reportado por GitHub: `fc692bb5888aef94cb362729d5a4666bb4b48722be85d9130d092d563774dc32`. Retención configurada hasta el 2026-11-03.

| Captura | Resultado observado | Captura UTC | Bytes | SHA-256 del payload |
|---|---|---|---:|---|
| Pionex `BTC_USDT` | HTTP 200; una coincidencia exacta; `type=SPOT`; base `BTC`; quote `USDT`; `enable=true` | 2026-10-20T03:39:42.247Z | 368 | `ae6c10cfb32f27bcf9a77bd74cb722eb19a3348d756392725efee244554e6980` |
| Binance `BTCUSDT` `exchangeInfo` | HTTP 200; estado `TRADING`; `isSpotTradingAllowed=true`; base `BTC`; quote `USDT` | 2026-10-20T03:39:42.826Z | 5349 | `81e78b15613d5711fe1d902a2ff1e7bcff2f2119ea9bb286e9a721da5feea2b0` |
| Binance `BTCUSDT` profundidad, 20 niveles | HTTP 200; 20 bids y 20 asks; mejor bid `82071.42`; mejor ask `82071.43`; `lastUpdateId=101665041948` | 2026-10-20T03:39:43.382Z | 1327 | `76c4d224b9569c41ad198ec45d055988cee0c8ac82e0f3e95b0c6b4cfa927c49` |

El spread observado en ese snapshot de Binance es aproximadamente `0.001218 bps`, calculado como `(ask-bid)/mid × 10,000`. Es una lectura de un único instante y un libro limitado a 20 niveles; no representa el spread histórico, no mide por sí solo la profundidad ejecutable para un tamaño de orden y no es una señal de rentabilidad.

La ejecución [tests #39365452000](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365452000) terminó en `success`; el log confirma `Ran 53 tests` y `OK`. La [validación de trazabilidad #39365451982](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39365451982) también terminó en `success`.

**Alcance de esta evidencia:** confirma que los endpoints públicos respondieron y que los campos listados estaban presentes en esa captura. No confirma acceso a la cuenta/región del usuario, disponibilidad futura, comisiones efectivas, retirada/redes, suficiencia de liquidez para una orden no especificada, riesgo fundamental del activo ni rentabilidad. El artefacto de CI conserva los bytes originales en Base64 y sus hashes para poder reproducir la verificación mientras no expire.
