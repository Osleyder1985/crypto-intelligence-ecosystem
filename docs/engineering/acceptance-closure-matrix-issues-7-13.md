# Matriz de cierre verificable de criterios de aceptación — Issues #7 y #13

- **Estado:** propuesta de verificación; no aprobada como línea base.
- **Línea base actual:** `main`; la matriz se incorporó originalmente mediante [PR #12](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/pull/12).
- **Issues fuente:** [#7 — Selección reproducible de mercados spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7) y [#13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13).
- **Especificación metodológica para Issue #7:** [metodología reproducible de selección spot](spot-market-selection-methodology.md).
- **Registro de fuentes oficiales:** [endpoints y límites semánticos](market-data-official-source-register.md).
- **Propósito:** descomponer criterios y entregables en evidencias, métodos de verificación y decisiones pendientes. Esta matriz no declara que el producto exista, que un criterio esté satisfecho ni que un Issue pueda cerrarse.
- **Regla de decisión:** PASS solo se permite cuando el criterio, la fuente de datos, el entorno/versiones, el procedimiento, el resultado y el artefacto reproducible estén registrados y el umbral haya sido aprobado antes de evaluar. Si falta umbral, fuente o evidencia, el estado es **PENDIENTE**, no PASS.
- **Responsabilidad:** los roles indicados son propuestas funcionales. No hay personas responsables nominadas ni decisiones de aceptación delegadas por este documento.

## 1. Issue #7 — Selección reproducible de exchanges y pares spot

### 1.1 Criterios metodológicos del Issue

| ID | Criterio del Issue | Requisito relacionado | Evidencia mínima exigida | Método de verificación reproducible | Decisión/umbral pendiente | Estado observado (2026-10-22) |
|---|---|---|---|---|---|---|
| 7-M01 | Volumen spot de 24 h y estabilidad en ventanas mayores | REQ-P-003, REQ-P-025, REQ-P-029; NFR-003 | Respuesta original fechada, exchange, par, ventana, moneda/unidad, zona horaria, endpoint y transformaciones | Repetir captura para fecha fijada; reconciliar ventanas y unidades; detectar huecos, duplicados y discrepancias | Ventanas mayores, tolerancia a discrepancias y mínimo aceptable por aprobar | Parcial: 4 capturas; 18/21 respuestas accesibles y 15/21 valores comparables por muestra; Bybit 403 y Pionex `amount` sin unidad documentada; ventana total aproximada 3 h 37 min, insuficiente para estabilidad de largo plazo |
| 7-M02 | Spread bid-ask y profundidad del libro | REQ-P-025; NFR-003 | Snapshot bid/ask con timestamp, niveles, unidades, símbolo canónico y fuente | Recalcular spread y profundidad a bandas de precio definidas; comprobar libro vacío/cruzado, orden y frescura | Bandas de profundidad, spread máximo y edad máxima de snapshot por aprobar | Parcial: 3 snapshots íntegros 21/21; 18/21 válidos por muestra; top-10 spread/notional calculados; última captura 6.757 s, secuencial y no sincronizada |
| 7-M03 | Slippage estimado para tamaños de orden definidos | REQ-P-009, REQ-P-025 | Libro completo suficiente, lado, tamaño y fórmula/versionado del cálculo | Simular consumo del libro para órdenes de referencia; contrastar con caso manual y registrar profundidad insuficiente | Tamaños de orden, límite de slippage y tratamiento de libro incompleto por aprobar | Parcial: estimador y curvas paramétricas implementados; no existe tamaño comercial típico aprobado y el snapshot solo cubre 20/100 niveles |
| 7-M04 | Comisiones de operación y retiro cuando sean relevantes | REQ-P-009, REQ-P-025 | Tabla de tarifas con fuente oficial, fecha, activo/red y condición aplicable | Reproducir coste total para cada escenario; separar tarifa maker/taker, retiro y costes no comparables | Escenarios de coste, niveles de cuenta y reglas de comparabilidad por aprobar | Parcial: tarifas públicas y capturadores read-only implementados; no hay artefacto privado de tarifa efectiva por cuenta; retiros no aplican al flujo actual |
| 7-M05 | Calidad, disponibilidad, límites y consistencia de API | REQ-P-011, REQ-P-029, REQ-P-032; NFR-002, NFR-003 | Documentación oficial, endpoints usados, límites, códigos de error, timestamps y muestras de respuesta | Pruebas de esquema, timeout, rate limit, reintento, duplicados, campos ausentes y reconciliación de símbolos | Objetivos de disponibilidad/frescura, política de reintentos y tolerancias por aprobar | Parcial: hashes, esquema y cuerpo completo verificados; Bybit HTTP 403; faltan mediciones de disponibilidad y latencia sostenidas |
| 7-M06 | Disponibilidad del par exacto en Pionex y restricciones geográficas/regulatorias | REQ-P-003, REQ-P-025, REQ-P-029 | Evidencia fechada de listado/estado del par exacto en Pionex y documentación oficial sobre restricciones relevantes | Consultar por símbolo normalizado y confirmar base/quote/mercado spot; registrar región y limitaciones conocidas | Regiones objetivo y regla para evidencia no concluyente por aprobar | Parcial: BTC_USDT confirmado Spot en una captura real; otros pares/región/cuenta no quedan certificados por esa observación |
| 7-M07 | Riesgo del activo: antigüedad, concentración, volatilidad, tokenomics y pérdida prolongada | REQ-P-012, REQ-P-015, REQ-P-016, REQ-P-025 | Fuentes fechadas por métrica, definición, unidad, cobertura y limitación | Reproducir métricas; ejecutar casos con datos ausentes/no aplicables; comprobar que ausencia no se convierta silenciosamente en cero | Ventanas, límites de exclusión y tratamiento por categoría de activo por aprobar | Pendiente |
| 7-M08 | Frescura, zona horaria, procedencia, fecha de captura y reproducibilidad | REQ-P-005, REQ-P-011, REQ-P-020, REQ-P-025; NFR-003 | Registro inmutable de captura, UTC, fuente, endpoint/referencia, versión de parser y hash de entrada cuando sea posible | Repetir evaluación sobre la misma captura; validar orden temporal, zona horaria, integridad y diferencias explicables | Edad máxima de cada tipo de dato y política de retención por aprobar | Parcial: UTC, hashes y semántica documentados; Binance/MEXC book sin timestamp de evento; frescura absoluta sigue INDETERMINATE cuando no puede probarse |

### 1.2 Entregables exigidos por el Issue

| ID | Entregable/condición | Evidencia de cierre | Regla de aceptación | Estado observado (2026-10-22) |
|---|---|---|---|---|
| 7-D01 | Matriz de comparación de exchanges y pares spot | Dataset versionado con una fila por exchange/par y campos comparables | Ninguna fila sin identificación de mercado, timestamp, fuente y estado de calidad; datos ausentes se marcan explícitamente | Parcial: 3 activos × 7 venues; 18/21 respuestas técnicamente accesibles, pero solo 15/21 valores comparables como turnover cotizado (3 Bybit HTTP 403; 3 Pionex `amount` con unidad indeterminada) |
| 7-D02 | Umbrales y reglas de exclusión justificadas | Decisión aprobada con racional, sensibilidad, responsable y fecha | Umbrales definidos antes de clasificar el conjunto de evaluación; exclusiones explicables y reproducibles | Pendiente: no se inventan umbrales; el selector exige configuración explícita aprobada |
| 7-D03 | Registro de fuentes y método de reproducción | Manifiesto de fuentes, versiones, consultas, pasos y artefactos | Una tercera ejecución puede reconstruir el resultado a partir de referencias disponibles, o declarar qué dato no es recuperable | Parcial: registro oficial y artefactos de CI disponibles; retención finita y descarga previa a expiración requerida |
| 7-D04 | Pruebas de calidad: campos ausentes, duplicados, timestamps, discrepancias y outliers | Suite de fixtures y reporte de ejecución con casos positivos y negativos | Cada clase de defecto tiene un caso que se detecta y un resultado esperado; umbrales de outlier aprobados | Parcial: integridad, campos ausentes, timestamps y profundidad insuficiente cubiertos; regla de outliers pendiente |
| 7-D05 | ADR que justifique decisiones antes de implementar componentes | ADR con contexto, alternativas, criterios, evidencia, consecuencias y estado de aprobación | No presentar elección técnica como aprobada antes de revisar la evidencia y recibir decisión autorizada | Parcial: [ADR-07](adr-issue-7-market-selection-policy-proposal.md) propuesta documentada; no aprobada y sin umbrales numéricos |
| 7-D06 | Aceptación reproducible para una fecha determinada | Expediente de ejecución con fecha objetivo, fecha de captura y resultado por par | Cada par queda PASS/FAIL/INDETERMINADO con razón; no se inventan datos faltantes ni se confunde fecha de consulta con fecha del mercado | Parcial: artefactos fechados y hashes; serie demasiado corta para aceptación de estabilidad |

### 1.3 Separación obligatoria de dimensiones

No colapsar las siguientes preguntas en una sola puntuación:

1. **Existencia/listado:** ¿el par spot exacto existe en el exchange?
2. **Accesibilidad:** ¿el endpoint/dato puede consultarse en las condiciones y región objetivo?
3. **Calidad/frescura:** ¿la captura es válida, comparable y suficientemente reciente según una política aprobada?
4. **Liquidez observable:** ¿qué spread y profundidad estaban disponibles en el snapshot?
5. **Coste de ejecución estimado:** ¿qué slippage y comisiones implica un tamaño de referencia?
6. **Riesgo del activo:** ¿qué riesgos fundamentales, de concentración, tokenomics o volatilidad constan en evidencia?
7. **Decisión operativa:** ¿pasa los criterios aprobados para el propósito definido? Una buena puntuación agregada no sustituye un bloqueo crítico ni implica que el activo sea una buena inversión.

El universo inicial del Issue (# Binance como referencia; OKX, Bybit, MEXC, Gate y Bitget como comparación; Pionex como plataforma de ejecución del usuario) se trata como **alcance propuesto**, no como cobertura ya comprobada. El objetivo de 15–20 exchanges del Issue #13 está condicionado a cobertura, legalidad/geografía, acceso API, límites y comparabilidad; no debe forzarse si no hay evidencia suficiente.

## 2. Issue #13 — Cobertura de criterios de aceptación

| ID | Criterio de aceptación del Issue | Requisitos relacionados | Evidencia y método de verificación | Decisiones/umbrales pendientes | Estado observado (2026-10-22) |
|---|---|---|---|---|---|
| 13-C01 | Cada requisito tiene identificador estable, prioridad, responsable y trazabilidad | REQ-P-020, REQ-P-033 | Catálogo validado; cada ID enlazado a Issue, artefacto, prueba y rol; revisión de duplicados y huérfanos | Prioridades finales y personas responsables por aprobar | Parcial: estructura documental existente; aprobación pendiente |
| 13-C02 | Se define el esquema de evaluación histórica sin sobrescribir ejecuciones previas | REQ-P-005, REQ-P-011, REQ-P-020 | Esquema/versionado, identificador de ejecución, almacenamiento de entradas o referencias inmutables y prueba de dos ejecuciones conservadas | Política de retención, inmutabilidad y disponibilidad de fuentes por aprobar | Parcial: PR #120 integrado; adaptador Binance OHLCV normalizado y prototipo local content-addressed con SHA-256; PR actual añade captura raw Pionex sin límite local de bytes/páginas/velas, pero semántica temporal/volumen INDETERMINATE; sin persistencia central, backups/restore ni política de retención permanente |
| 13-C03 | Se especifica comparación y se separan cambios de mercado de cambios de método | REQ-P-021, REQ-P-020 | Fixture de dos o más evaluaciones con cambios de precio/datos, metodología, proveedor y parámetros; salida debe atribuir cada diferencia | Tolerancias de comparación y normalización por aprobar | Parcial: comparador local integrado en PR #120 separa alcance, metodología, implementación, conjunto de fuentes, calidad, hashes de entrada y deltas numéricos; no atribuye causalidad ni resuelve tolerancias de producto |
| 13-C04 | El ranking se reconstruye y explica puntuación, universo, horizonte, incertidumbre y exclusiones | REQ-P-012, REQ-P-022, REQ-P-020 | Reproducción histórica del ranking con versión de método, pesos, universo y snapshot; prueba de incompatibilidad de horizontes | Universo elegible, vigencia, pesos, penalizaciones y reglas de abstención por aprobar | Pendiente |
| 13-C05 | Movimientos alcistas/bajistas tienen reglas explícitas y pruebas contra fuga de información | REQ-P-014, REQ-P-023 | Especificación operacional por temporalidad; fixtures sintéticos y walk-forward; test que añade o modifica velas futuras y comprueba que el pasado no cambia | Definición de eventos, ventanas, umbrales y criterios de evaluación por aprobar | Parcial: detector OHLCV integrado en PR #120 con parámetros explícitos, baseline solo con velas previas y tests anti-look-ahead; sin atribución causal ni validación fuera de muestra |
| 13-C06 | Eventos guardan fuentes y tiempos verificables, alternativas y grado de evidencia | REQ-P-011, REQ-P-020, REQ-P-023 | Expedientes de eventos con hora de publicación/captura UTC, fuente, URL, entidad, relevancia, hipótesis, alternativas y evidencia contraria | Taxonomía de fuentes, niveles de fiabilidad y reglas de confianza por aprobar | Pendiente |
| 13-C07 | Hipótesis predictivas tienen protocolo fuera de muestra y registro de resultados | REQ-P-013, REQ-P-014, REQ-P-024 | Protocolo temporal predefinido, registro de predicciones emitidas, benchmark, resultados negativos y métricas de calibración | Horizontes, objetivos, métricas, tamaño mínimo de muestra y tolerancias por aprobar | Pendiente |
| 13-C08 | Análisis de exchanges distingue cobertura, liquidez, datos instantáneos/históricos y límites API | REQ-P-003, REQ-P-025, REQ-P-029, REQ-P-011 | Manifiesto de cobertura por exchange/par/campo; snapshots y trades separados de históricos; tests de frescura, límites y disponibilidad Pionex | Universo final, ventanas, tamaños de referencia y límites de liquidez por aprobar | Parcial: snapshots/turnover para 7 venues/3 pares; Bybit 403 y Pionex turnover INDETERMINATE; Binance histórico normalizado y captura raw Pionex en implementación; Pionex timestamp-role/volume-unit aún impiden análisis histórico comparable; falta histórico multiexchange normalizado |
| 13-C09 | Soportes/resistencias incluyen método, fuerza estimada, invalidación e incertidumbre | REQ-P-026, REQ-P-014 | Fixtures OHLCV versionados; resultado con zona, método, contactos, rechazos, antigüedad, volumen disponible, invalidación y confianza; test anti-look-ahead | Métodos candidatos, definición de fuerza y protocolo retrospectivo por aprobar | Parcial: prototipo causal de pivotes, toques, rechazos e invalidación integrado en PR #120; la fuerza se expresa mediante conteos; faltan antigüedad, ponderación por volumen, confianza y validación fuera de muestra |
| 13-C10 | UX tiene criterios medibles de usabilidad, accesibilidad, rendimiento y responsividad | REQ-P-006, REQ-P-027; NFR-001, NFR-006, NFR-018 | Casos de uso por dispositivo, pruebas con usuarios/tecnologías de asistencia, benchmarks bajo carga y matriz de viewport | Dispositivos, tareas, objetivos de éxito, latencia y criterios de accesibilidad por aprobar | Pendiente |
| 13-C11 | Matriz normativa enlaza controles aplicables con artefactos/evidencias sin afirmar certificación infundada | REQ-P-028, REQ-P-033; NFR-004, NFR-005 | Para cada control: fuente oficial/edición, justificación de aplicabilidad, requisito, artefacto, prueba, resultado y responsable de revisión | Aplicabilidad final y revisión competente por aprobar | Parcial: matriz preliminar; no acredita conformidad |
| 13-C12 | Requisitos se incorporan a documentación y trazabilidad en un único PR controlado tras revisar Issues/PR existentes | REQ-P-020, REQ-P-033 | Revisión de PR abiertos/archivos solapados, diff del PR existente, enlaces Issue–requisito y validación CI | Aprobación del propietario antes de integrar | Parcial: PR #12 está fusionado; integró la documentación inicial, pero no satisface por sí solo todos los criterios de Issue #13 |

## 3. Descomposición funcional del Issue #13 para diseñar pruebas

Esta tabla enlaza las capacidades RF-01–RF-09 descritas en el Issue con los tipos de prueba mínimos. Es un plan de verificación, no evidencia de que el comportamiento esté implementado.

| Capacidad | Pruebas mínimas | Fallos que deben detectarse | Evidencia que debe persistir |
|---|---|---|---|
| RF-01 Evaluación individual persistente | Esquema, idempotencia de consulta, dos ejecuciones sin sobrescritura, entrada faltante y fuente retrasada | Resultado sin timestamp/método; pérdida de ejecución previa; conclusión pese a dato crítico ausente | Informe, inputs/referencias, versiones, advertencias y hash/manifiesto |
| RF-02 Comparación de evaluaciones | Cambios absolutos/relativos y cambios de proveedor/método/cobertura | Atribuir al mercado un cambio causado por método o corrección de datos | Diferencias, clasificación de causa y versión comparada |
| RF-03 Ranking | Reconstrucción, elegibilidad, exclusiones, sensibilidad de pesos e incompatibilidad de horizonte | Mezcla de universos o métodos; omisión silenciosa de incertidumbre | Universo, pesos, exclusiones, puntuaciones y versión del ranking |
| RF-04 Movimientos/eventos | Fixtures OHLCV, ventanas de evento, reloj de publicación vs captura y pruebas anti-look-ahead | Giro detectado usando velas futuras; causalidad inferida solo por proximidad temporal | Reglas, snapshots, evidencia del evento, alternativas y grado de confianza |
| RF-05 Memoria/predicción | Registro no retroactivo, walk-forward, supervivencia, leakage, sobreajuste, costes y calibración | Predicción reescrita; evaluación con datos futuros; métrica sin baseline | Predicción original, timestamp, horizonte, invalidación, outcome y métricas |
| RF-06 Libro/profundidad/liquidez | Libro vacío/cruzado, niveles insuficientes, spread, profundidad, imbalance, slippage y límites API | Volumen reportado usado como sustituto de liquidez; snapshot viejo presentado como actual | Snapshot/trades por separado, exchange/par, edad, tamaño de referencia y método |
| RF-07 Soportes/resistencias | Detección en múltiples temporalidades, zona e invalidación, reproducción histórica | Nivel calculado con datos futuros o presentado como garantía | Método, ventana, zona, contactos, rechazos, volumen disponible e incertidumbre |
| RF-08 Experiencia de usuario | Tareas de ranking/historial/eventos, móvil/escritorio, teclado/lector, movimiento reducido y benchmark | Datos críticos ocultos, error no explicado, navegación inaccesible o lenta | Plan de prueba, dispositivo/browser, mediciones, hallazgos y correcciones |
| RF-09 Auditoría/control normativo | Recorrido requisito→control→implementación→prueba→ejecución→resultado→aprobación; acceso/retención/restore | Eslabón sin evidencia, norma/edición no verificada o afirmación de certificación sin base | Registro de trazabilidad, logs, versiones, decisiones y evidencia fechada |

## 4. Contrato de evidencia para cada prueba

Toda evidencia que pretenda sustentar PASS debe incluir, cuando aplique:

- ID de criterio y requisito(s) relacionado(s).
- Versión de metodología/código, parámetros y entorno.
- Fecha objetivo del análisis, hora de captura y timestamps originales; todos normalizados a UTC sin descartar la zona de origen.
- Proveedor, endpoint o URL, condiciones/licencia relevantes y estado de acceso.
- Dataset/fixtures, hash o referencia inmutable y transformaciones aplicadas.
- Comando/procedimiento de reproducción y resultado bruto, incluidos fallos.
- Resultado **PASS**, **FAIL**, **INDETERMINADO** o **NO EJECUTADO**, con justificación.
- Umbral, unidad, ventana, tamaño de muestra y responsable que aprobó el criterio antes de ejecutar.
- Artefacto persistido y vínculo desde el Issue/PR.

No se exige guardar datos cuya redistribución esté prohibida; en tal caso, registrar metadatos, hash, licencia y procedimiento de obtención, y marcar las limitaciones de reproducibilidad.

## 5. Decisiones necesarias antes de declarar cierre

1. Nombrar responsables humanos para producto, datos, investigación cuantitativa, QA y seguridad; el rol propuesto no equivale a asignación.
2. Aprobar los umbrales y el método de medición para spread, profundidad, slippage, volumen/frescura, riesgo, predicción, UX y rendimiento.
3. Elegir tamaños de orden y ventanas de análisis con justificación; no inferirlos del resultado observado.
4. Confirmar universo/regiones y restricciones de proveedor, junto con disponibilidad exacta de pares spot en Pionex.
5. Ejecutar pruebas con fixtures y capturas fechadas; publicar resultados negativos y no concluyentes.
6. Actualizar esta matriz solo con referencias verificables; no cambiar un estado a PASS por tener una descripción o un test escrito sin ejecución.
7. Mantener el PR en borrador hasta revisión humana. Esta matriz no autoriza merge, release, claves de trading ni operaciones reales.

## 6. Límites explícitos

- Los criterios numéricos están pendientes de aprobación; no se inventan umbrales.
- La matriz es una propuesta de verificación interna y requiere revisión humana/adversarial.
- El CI documental no prueba rendimiento del producto, liquidez real de mercado, exactitud predictiva ni conformidad ISO.
- No se asume que la información histórica de profundidad esté disponible en un proveedor; cuando no exista, la captura propia solo sirve desde su fecha de inicio.


## 3. Estado del registro de fuentes

El registro de fuentes oficiales está acompañado por evidencia real: cuatro capturas de turnover móvil de 24 h (18/21 respuestas técnicamente accesibles y 15/21 valores comparables por captura; Bybit 403 y unidad de Pionex `amount` indeterminada) y tres snapshots de libros (18/21 válidos por muestra), con cuerpos y hashes verificados. La ventana de las capturas de turnover abarca aproximadamente 3 h 37 min; el último snapshot de libro abarca 6.757 s y no está sincronizado. Binance/MEXC no aportan timestamp de evento utilizable para profundidad. Estos resultados permiten marcar criterios como Parciales, no PASS: sigue faltando una serie suficientemente larga, acceso a Bybit desde un entorno autorizado, política de frescura para fuentes sin timestamp de evento y evidencia privada de tarifas efectivas. PR #120 ya está integrado y contiene el primer adaptador histórico OHLCV de Binance, análisis descriptivo de riesgo, detección de movimientos, soportes/resistencias y un prototipo local de historial/comparación. Todavía no existe motor histórico multiexchange, ranking aprobado, protocolo predictivo fuera de muestra, integración de noticias ni evaluación de riesgo fundamental/tokenomics.
