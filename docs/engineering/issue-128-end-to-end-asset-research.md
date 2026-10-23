# Flujo integral de investigación de un criptoactivo — Issue #128

- **Estado:** especificación funcional propuesta; no es evidencia de implementación ni aprobación de una estrategia de inversión.
- **Issues rectores:** [#11](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/11), [#13](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13) y [#128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128).
- **Alcance inicial:** investigación de mercados Spot y fuentes públicas/read-only. La ejecución de órdenes reales permanece fuera de alcance.

## Estado de implementación verificado — 2026-10-23

Este estado describe código existente; **no declara cerrado este Issue ni que el producto esté listo para producción**.

| Tramo | Evidencia en el repositorio | Estado y límite |
|---|---|---|
| Captura de mercado e histórico | `scripts/market_selection/capture_binance_spot_research.py`, `scripts/market_selection/resolve_binance_spot_market_candidates.py`, `scripts/market_selection/capture_binance_spot_ohlcv.py` | Admite símbolo nativo o ticker base con cotización explícita; devuelve error ante cero o múltiples candidatos. No resuelve nombres de activos ni identidad canónica cross-chain, ni cubre todas las fuentes del expediente. |
| Integridad, cobertura y frescura observada | `tests/market_selection/test_capture_binance_spot_research.py`, `scripts/market_selection/research_report.py` | La captura conserva respuestas completas, hash, contadores y listas explícitas de huecos; el informe mide la edad de la última vela cerrada elegible en el momento de captura. Sin política de frescura aprobada, no la etiqueta automáticamente como fresca/caducada. No se aplica un límite arbitrario de bytes del proyecto. |
| Composición de informe | `scripts/market_selection/research_report.py` | Produce JSON descriptivo con riesgo OHLCV, eventos de movimiento, soportes/resistencias, cobertura histórica, cotización y procedencia de resolución del par, y tres horizontes. Ahora acepta opcionalmente una instantánea de libro normalizada y autorizada, solo si exchange y símbolo coinciden. |
| Identidad canónica | `scripts/market_selection/canonical_asset_identity.py` | Valida evidencia proporcionada y revisada; no descubre ni verifica por sí mismo la autoridad real de una fuente externa. |
| Autorización de fuentes | `scripts/market_selection/provider_license_gate.py` | Falla de forma cerrada. La prueba técnica no autoriza el análisis interno; no hay que fabricar ni inferir permisos. |
| Noticias, catalizadores y on-chain | Integración de evidencia existente, con registros de fuentes y autorizaciones | Cobertura incompleta; no equivale a una investigación automática completa de noticias, fundamentales y datos on-chain. |
| Evaluación por horizontes | Contrato `crypto-asset-research-report-v2` | Los tres horizontes se emiten, pero permanecen `INDETERMINATE` mientras falten metodología aprobada y evidencia suficiente. |
| Producto utilizable por el usuario | No se acredita una API/UI desplegada con resolución automática, historial central y experiencia completa | Pendiente. El CLI requiere parámetros y artefactos explícitos. |

### Bloqueadores para afirmar «introducir una criptomoneda y recibir una evaluación integral»

1. Disponer de autorización real y revisada para cada uso de datos requerido; la disponibilidad técnica de una API no prueba derechos de uso.
2. Resolver el activo canónico y los pares sin inferencias por ticker; para tokens y wrapped assets se necesita cadena y contrato cuando corresponda.
3. Orquestar fuentes adicionales autorizadas (liquidez, eventos/noticias, fundamentales y on-chain), con integridad, cobertura y tiempos de captura verificables.
4. Aprobar metodologías versionadas para los tres horizontes y validar cualquier afirmación predictiva con pruebas temporales fuera de muestra.
5. Añadir persistencia/versionado y una interfaz que acepte un identificador de activo sin exigir que el usuario prepare manualmente todos los artefactos.
6. Ejecutar y conservar una prueba E2E con evidencias reales autorizadas. Los fixtures sintéticos demuestran comportamiento del código, no permisos de proveedores ni cobertura real de mercado.

El siguiente incremento debe cerrar bloqueadores con evidencia verificable; no debe convertir una captura técnica o un informe descriptivo parcial en una señal favorable/desfavorable sin respaldo.


### Incremento de libro de órdenes (integración descriptiva)

- **Analizador:** `scripts/market_selection/analyze_order_book_snapshot.py`.
- **Entrada:** `crypto-spot-order-book-snapshot-v1`, con `capture_status=PASS`, `provider_id`, mercado, timestamp y niveles `bids/asks`. La autorización se resuelve fuera del artefacto mediante un registro confiable de despliegue.
- **Integración:** `research_report.py --order-book-artifact PATH --provider-authorization-registry PATH`. El segundo archivo debe ser configuración confiable controlada por el despliegue, nunca un registro aportado por el usuario o incluido dentro de la instantánea. El exchange y el símbolo deben coincidir con el mercado del informe.
- **Salida:** `descriptive_analyses.order_book`; calcula mejor bid/ask, precio medio, spread absoluto y en puntos básicos, cantidades visibles, nocional visible e imbalance descriptivo. Conserva todos los niveles recibidos en el artefacto.
- **Fail-closed:** el módulo ignora cualquier autorización embebida en la instantánea y resuelve `provider_id` exclusivamente contra el registro confiable suministrado por el despliegue. Si falta autorización explícita para análisis interno, la integración falla; una prueba técnica en vivo no autoriza análisis interno ni persistencia.
- **Adaptador de captura preservada:** `scripts/market_selection/normalize_order_book_probe.py` selecciona exactamente un registro del artefacto `multi-exchange-spot-book-probe-v1`, verifica Base64, SHA-256, bytes y que `parsed_json` coincida con el cuerpo preservado, y exige autorización `internal_analysis` desde el registro confiable. Uso CLI: `--multi-exchange-order-book-probe PATH --order-book-exchange EXCHANGE --order-book-symbol SYMBOL` junto con `--provider-authorization-registry PATH`. El probe original también debe haber capturado el registro; el adaptador no hace solicitudes de red.
- **Límites:** esta integración consume una captura preservada, no activa por sí misma la captura en vivo ni sustituye el libro local sincronizado de WebSocket. La captura multi-exchange actual tiene pares predefinidos (BTC/ETH/SOL contra USDT), y los usos de proveedores siguen bloqueados salvo autorización válida. No clasifica órdenes como «muros» con umbrales inventados, no detecta órdenes ocultas, no promete liquidez ejecutable y no envía órdenes. Si no se suministra la instantánea, el informe marca `NOT_PROVIDED`.

## 1. Resultado de producto

El usuario introduce un activo y el ecosistema produce un expediente histórico y una evaluación explicable para **corto, medio y largo plazo**, cada horizonte por separado. El resultado puede ser favorable, desfavorable o **INDETERMINATE**. El sistema no está obligado a encontrar una oportunidad y no promete rentabilidad.

La evaluación debe responder, en la medida que las fuentes lo permitan:

1. Qué ocurrió históricamente con precio, volumen, volatilidad, drawdowns y liquidez observable.
2. Cuándo comenzaron, se aceleraron, agotaron, revirtieron o terminaron movimientos relevantes, según reglas versionadas.
3. Qué noticias, anuncios, eventos del proyecto, listados/delistados, incidentes, regulación, factores macro, datos on-chain o movimientos generales de mercado podrían explicar esos cambios.
4. Qué zonas de soporte y resistencia se observan, con método, temporalidad, evidencia e invalidación.
5. Qué factores favorecen o perjudican cada horizonte, qué riesgos pueden invalidar la tesis y qué evidencia falta.
6. Cuánta confianza merece el resultado y qué pruebas respaldan la metodología.

## 2. Flujo funcional y contratos

### F-01 — Resolución de identidad
Resolver identificadores ambiguos antes de analizar: nombre, ticker, activo/red cuando proceda, mercados y pares reales. Mostrar las decisiones de identidad y no combinar activos diferentes por compartir ticker. La coincidencia de un ticker de par no constituye identidad canónica. Un identificador canónico solo se marca `VERIFIED` con evidencia única y revisada que vincule el identificador solicitado con el activo base del mercado; los tokens/wrapped assets requieren cadena y dirección de contrato. Sin evidencia, la salida es `INDETERMINATE` y el informe no se presenta como completo.

### F-02 — Expediente de datos
Reunir series históricas OHLCV, volumen, volatilidad, drawdown, mercados/pares, spread, profundidad recibida, trades si están disponibles, metadatos del activo, tokenomics, datos on-chain, anuncios, noticias, incidentes, regulación y contexto macro/mercado según cobertura. Cada fuente debe declarar periodo, unidad, zona horaria, timestamps, licencia/condiciones conocidas, calidad y huecos.

No presentar una fuente no disponible como si se hubiera consultado. Distinguir dato no existente, no accesible, no permitido, incompleto y fallido.

### F-03 — Integridad y completitud de captura
Preservar respuestas completas hasta EOF y calcular hashes verificables. No introducir límites arbitrarios de tamaño impuestos por el proyecto. Los límites reales de API, rate limits, timeouts, almacenamiento o recursos operativos deben identificarse por fuente/entorno, documentarse y gestionarse sin descartar datos silenciosamente. Registrar bytes/elementos capturados, estado de terminación, paginación, reintentos, truncamiento, errores y posibilidad de reanudar. Una captura interrumpida no se etiqueta completa.

### F-04 — Detección histórica de movimientos
Detectar candidatos a inicio, aceleración, agotamiento, reversión y fin de movimientos mediante reglas explícitas, versionadas y probables de reproducir. La confirmación de un punto de giro solo puede estar disponible a partir del momento en que los datos requeridos existieron; las evaluaciones históricas no pueden usar velas, noticias ni metadatos futuros (look-ahead).

### F-05 — Investigación de detonantes
Buscar evidencia en ventanas temporales justificadas antes y después del movimiento. Conservar URL o identificador de fuente, autor/editor si consta, hora de publicación, hora de captura, zona horaria, activo relacionado, fuente primaria/secundaria, fiabilidad, relevancia y relación temporal.

Cada explicación se clasifica como:
- **Hecho verificado:** evidencia primaria o fuentes suficientes que confirman el evento.
- **Coincidencia temporal/correlación:** el evento ocurrió cerca del movimiento; no demuestra causalidad.
- **Hipótesis plausible:** mecanismo y evidencia compatibles, pero no concluyentes.
- **Causalidad respaldada:** convergen evidencias y mecanismo; se explicitan límites y alternativas.
- **Causa no identificada:** no hay evidencia suficiente.

No atribuir causalidad por proximidad temporal ni inventar una noticia para completar el relato. Incluir explicaciones alternativas y nivel de confianza.

### F-06 — Soportes y resistencias
Calcular zonas multi-temporalidad mediante métodos documentados. Exponer rango, método, puntos de contacto/rechazo, antigüedad, volumen asociado si existe, distancia al precio, invalidación, sensibilidad de parámetros y confianza. Una zona no garantiza reacción del mercado. Validar con datos disponibles en el momento analizado.

### F-07 — Evaluación por horizonte
Producir tres evaluaciones separadas. La duración exacta de cada horizonte se define en una metodología versionada y aprobada, no se inventa como constante universal.

Cada horizonte debe incluir:
- tendencia y estructura de mercado;
- momentum y volatilidad;
- liquidez/spread/profundidad observada y limitaciones de ejecución estimada;
- soportes/resistencias e invalidaciones;
- fundamentales, tokenomics y datos on-chain solo cuando sean accesibles y verificables;
- catalizadores/eventos y calidad de la evidencia;
- riesgos de mercado, liquidez, concentración, contraparte, protocolo, regulación y datos cuando sean pertinentes;
- escenarios favorables, base y adversos, con supuestos explícitos;
- evidencia a favor y en contra;
- conclusión favorable, desfavorable o INDETERMINATE;
- incertidumbre, limitaciones y razones para abstenerse.

No fusionar los tres horizontes en una única puntuación opaca. Si existe una puntuación compuesta, publicar fórmula, pesos, sensibilidad, universo y versión de metodología; separar calidad del activo, oportunidad, riesgo y calidad de evidencia.

### F-08 — Informe y experiencia de usuario
El informe presenta primero una síntesis comparativa por horizonte y después detalle navegable: gráficos, cronología, fuentes, datos, movimientos, detonantes, indicadores, soportes/resistencias, riesgos y metodología. Cada afirmación material debe enlazar su evidencia. Mostrar fecha de evaluación, periodo cubierto, cobertura y datos faltantes.

### F-09 — Historial y comparación
Guardar cada ejecución como registro inmutable/versionado, sin sobrescribir informes anteriores. Registrar entradas o referencias/hash, código, metodología, parámetros, fuentes, transformaciones, exclusiones, advertencias y resultados. Comparar evaluaciones separando cambios del mercado de cambios de metodología, proveedor, cobertura o correcciones.

### F-10 — Validación empírica
Las reglas y puntuaciones que pretendan aportar señal predictiva requieren backtesting temporal y evaluación fuera de muestra/walk-forward, benchmarks pertinentes, costes/supuestos explícitos, análisis de sensibilidad, calibración y controles de leakage, survivorship bias, data snooping y sobreajuste. No ajustar umbrales mirando el conjunto final de prueba. Registrar predicciones con su timestamp y medir resultados posteriores.

## 3. Requisitos no funcionales

| ID | Requisito | Evidencia de aceptación |
|---|---|---|
| NFR-01 | Reproducibilidad | Reejecución con entradas y versiones idénticas reproduce resultados dentro de tolerancias documentadas. |
| NFR-02 | Integridad de datos | Hashes verificables, estado EOF/paginación y detección de capturas truncadas; sin límite arbitrario de bytes del proyecto. |
| NFR-03 | Trazabilidad | Requisito → Issue → ADR/diseño → código → prueba → ejecución/artefacto → resultado. |
| NFR-04 | Temporalidad correcta | Separación de tiempos de evento, publicación, proveedor, captura y procesamiento; ausencia de timestamps no se convierte en frescura supuesta. |
| NFR-05 | Fallo seguro | Datos críticos ausentes, ambiguos o incompatibles producen advertencias o INDETERMINATE, no inferencias silenciosas. |
| NFR-06 | Seguridad | Lectura pública en el alcance inicial; secretos fuera de logs/artefactos; ninguna orden real. |
| NFR-07 | Usabilidad y accesibilidad | Flujos de búsqueda/informe utilizables en móvil y escritorio; gráficos legibles, navegación por teclado y movimiento reducido cuando aplique. |
| NFR-08 | Operabilidad | Logs estructurados, errores tipados, métricas, reintentos/reanudación documentados y diagnóstico de fallos. |
| NFR-09 | Rendimiento | Umbrales definidos tras medir casos de uso, volumen y entorno; pruebas registradas. No se inventan SLA ni umbrales universales. |
| NFR-10 | Seguridad de la conclusión | Toda conclusión declara límites y evidencia; no garantiza rentabilidad ni transforma correlación en causalidad. |

## 4. Matriz de trazabilidad propuesta

| ID | Capacidad | Issue/documento relacionado | Prueba mínima |
|---|---|---|---|
| E2E-01 | Entrada y resolución de activo | #128, #13, #17, #130 | Ticker ambiguo, activo inexistente, par incompatible, identidad sin evidencia, identidad no única y conflicto de cadena/contrato. |
| E2E-02 | Captura histórica íntegra | #128, #13 y documentación de captura | Paginación, EOF, huecos, reintentos, hash y captura interrumpida. |
| E2E-03 | Detección de movimientos | #13, documento de eventos OHLCV | Casos sintéticos/observados y prueba anti-look-ahead. |
| E2E-04 | Investigación de eventos/detonantes | #13, #128 | Evento con fuente, publicación tardía, fuentes contradictorias y causa desconocida. |
| E2E-05 | Soportes/resistencias | #13, documento de eventos S/R | Temporalidades, invalidación, pivotes confirmados y anti-look-ahead. |
| E2E-06 | Tres horizontes | #128 y catálogo de requisitos | Informe con resultados separados, supuestos versionados y abstención. |
| E2E-07 | Riesgos/costes/liquidez | #7, #18 | Datos incompletos, profundidad parcial y tarifa no demostrada. |
| E2E-08 | Historial reproducible | #13, historial de evaluaciones | Repetición determinista, comparación y preservación de versiones. |
| E2E-09 | Validación predictiva | #13, #128 | Split temporal, benchmark, costes, leakage y calibración. |
| E2E-10 | Informe final completo | #6, #8, #11, #128 | Prueba de aceptación de extremo a extremo con artefactos archivados. |

## 5. Criterios de cierre

- [ ] Una prueba E2E parte de un activo y entrega un informe reproducible con tres horizontes separados.
- [ ] El expediente histórico identifica cobertura, huecos, procedencia, temporalidad e integridad.
- [ ] Los movimientos se detectan con reglas versionadas sin usar información futura.
- [ ] Cada posible detonante se clasifica con evidencia y explicaciones alternativas; se admite causa desconocida.
- [ ] Soportes/resistencias tienen método, temporalidad, invalidación e incertidumbre.
- [ ] Cada horizonte contiene tesis, evidencia a favor/en contra, escenarios, riesgos e invalidaciones.
- [ ] La conclusión puede ser favorable, desfavorable o INDETERMINATE y no se fuerza una señal.
- [ ] La validación predictiva aporta resultados fuera de muestra y documenta sesgos/costes.
- [ ] La matriz requisito–implementación–prueba–resultado está actualizada.
- [ ] Las pruebas E2E, integración, seguridad y rendimiento exigibles están ejecutadas y archivadas antes de declarar preparación para producción.
- [ ] La revisión documental no se confunde con implementación ni con conformidad/certificación ISO.

## 6. Decisiones no fijadas por esta especificación

Este documento no decide arbitrariamente duración de horizontes, pesos, umbrales de frescura, universos de activos, costes típicos ni umbrales de rendimiento. Cada decisión necesita fuente, evidencia, análisis de sensibilidad, propietario/aprobación y versión. Si no existe base suficiente, se conserva como indeterminada.

## 7. Referencias internas

- [Issue #128 — Flujo integral](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128)
- [Issue #13 — Requisitos analíticos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/13)
- [Issue #6 — Plataforma central de datos](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/6)
- [Issue #7 — Selección de mercados Spot](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/7)
- [Issue #18 — Frescura, comisiones y coste](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18)
- [Issue #19 — Validación integral y preparación operativa](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/19)


### Salvaguardas temporales de evidencia por episodio

Al asociar un evento mediante `movement_episode_id`, la integración verifica que el episodio exista una sola vez y que `evaluation_as_of` no sea anterior a `episode_observable_only_at_ms`. El resultado distingue si la publicación precede, cae dentro o sigue al intervalo técnico, sin convertir esa relación temporal en causalidad. Se permite una `movement_window` explícita junto al ID del episodio para evaluar un intervalo previo/posterior más amplio; la relación con el movimiento se sigue clasificando respecto a los pivotes reales. La ventana ampliada debe justificarse y versionarse; no existe una duración universal aprobada para buscar detonantes.
