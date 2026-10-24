# ADR-0001: Criterios y límites para seleccionar el stack

- **Estado:** Propuesto; no aprobado como selección tecnológica definitiva.
- **Issue:** #9.
- **Fecha:** 2026-10-24.
- **Decisores:** propietario del producto; revisión técnica mediante PR.
- **Evidencia relacionada:** docs/architecture/stack-technology-evaluation.md.

## Contexto

El producto necesita clientes web, Android e iOS que compartan resultados canónicos, una API versionada, análisis cuantitativo en Python, almacenamiento histórico y captura de datos públicos verificable. El repositorio no acredita todavía una PoC comparativa completa de cliente móvil, gráficos, API, persistencia y tareas asíncronas. Por tanto, seleccionar un stack definitivo ahora confundiría una hipótesis arquitectónica con evidencia validada.

## Decisión provisional

1. Mantener Python para el código analítico existente; evaluar FastAPI frente a Django REST Framework para la API mediante una PoC contractual.
2. Evaluar Flutter y React Native para móvil; incluir Kotlin nativo como referencia técnica Android y una PWA responsive como referencia de coste/distribución.
3. Evaluar React/Next.js para web y React/Vite si no se demuestra necesidad de SSR.
4. Usar PostgreSQL como candidato inicial para persistencia estructurada, sin adoptar extensión temporal o base especializada hasta medir consultas históricas representativas.
5. Empezar con un worker/proceso persistente e idempotente; diferir broker, caché y streaming hasta que una carga medida los justifique.
6. Usar OpenAPI como contrato de API, con validación automática y generación de tipos/clientes solo si reduce deriva demostrablemente.
7. No introducir claves de proveedor en clientes, duplicar reglas analíticas críticas ni activar órdenes reales de trading.

Esta decisión limita la experimentación; **no aprueba** una tecnología como ganadora ni autoriza despliegue productivo.

## Alternativas descartadas por ahora

- Microservicios, Kubernetes, Kafka y Redis: no hay evidencia de carga/operación que justifique su complejidad.
- Base de datos especializada de series temporales: pendiente de benchmark con consultas y volumen representativos.
- Android nativo como único cliente móvil: no cubre iOS sin un segundo cliente.
- Selección definitiva de Flutter o React Native por familiaridad o popularidad: requiere PoC comparable.

## Consecuencias

- Se mantiene reversible la arquitectura y se evita asumir costes operativos sin evidencia.
- La decisión final se retrasa hasta ejecutar PoC y medir.
- Los clientes dependerán de contratos versionados; el backend será la autoridad de las reglas de dominio.
- La evaluación debe registrar versiones, licencias, comandos, resultados, fallos, hashes y límites de interpretación.

## Riesgos y controles

| Riesgo | Control |
|---|---|
| Elegir por preferencia en vez de evidencia | Fijar pesos y criterios antes de puntuar |
| Comparación no reproducible | Mismo fixture, entorno descrito y comandos documentados |
| Rendimiento no representativo | Registrar tamaño/diseño del dataset y no extrapolar |
| Deriva de contratos | OpenAPI, validación de esquemas y pruebas de contrato |
| Fallo de captura interpretado como dato válido | Estados explícitos, fail-closed e idempotencia |
| Afirmación falsa de conformidad | No declarar certificación ni conformidad ISO sin evaluación pertinente |

## Condiciones para ratificar o sustituir

Ratificar el ADR solo después de: (a) PoC API/contratos; (b) persistencia histórica; (c) cliente y gráficos multiplataforma; (d) worker idempotente con recuperación; (e) CI y revisión de seguridad; (f) matriz puntuada con evidencia y análisis de sensibilidad; y (g) aprobación explícita del propietario del producto. Cualquier fallo, cambio de requisitos o evidencia que cambie el ranking exige revisar este ADR mediante PR.

## Verificación

- [ ] PoC ejecutadas en entorno documentado.
- [ ] Resultados PASS/FAIL reproducibles adjuntos.
- [ ] Matriz puntuada con referencias a evidencia.
- [ ] Análisis de sensibilidad completado.
- [ ] Revisión de licencias, soporte y vulnerabilidades.
- [ ] Decisión final aprobada por el propietario del producto.
