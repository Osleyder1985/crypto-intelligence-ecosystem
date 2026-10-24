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


## Evidence checkpoint — 2026-10-24 (not final ratification)

### Completed evidence

- Web: [run 40060309796](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40060309796) passed geometry unit tests and a Chromium smoke test for the canonical 12-candle fixture, 12 textual rows, zoom 100→125→100%, pan left/right and no page errors. Three Node geometry process medians were 0.003307, 0.003266 and 0.003327 ms. This excludes GPU, real-device frame time, peak memory and chart-ready time. The newer Playwright 1.64.1 dependency audit/repeated-readiness run is pending.
- Cross-platform fixture integrity: [Windows hosted run 40059988216](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059988216) passed and confirmed the same SHA-256 as Linux after adding `.gitattributes` with LF line endings. This runner is Windows Server 2025, not the user's Windows 11 PC.
- Flutter Android: [run 40059925721](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059925721) passed on Flutter 3.47.5 stable, Ubuntu 24.04.5, AMD EPYC 7763 / 4 vCPU / 16.77 GB / Temurin JDK 17.0.20.1. Debug builds: 163.34, 19.42 and 18.74 s; incremental 4.50 s; Android Release build 57.13 s. Debug APK 150,302,356 bytes; Release APK 45,445,816 bytes. The first clean build is a cold-run outlier and remains in the record. Detailed evidence: `docs/architecture/evidence/issue-9-flutter-android-ci-40059925721.md`.
- React Native bare iOS: [run 40059801779](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801779) passed three iOS Simulator Debug builds (64.51, 39.76, 40.60 s) and incremental build (13.86 s) on macOS 26 ARM64 / Apple M1 virtual / 3 cores / 7 GB / Xcode 26.6. `npm audit --audit-level=high` reported zero vulnerabilities; lockfile hash matched Android and the inventory had no UNKNOWN licence labels. Detailed evidence: `docs/architecture/evidence/issue-9-react-native-ios-repeated-builds-40059801779.md`.
- React Native bare Android baseline: [run 40059276905](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059276905) passed a single Debug build and reported zero vulnerabilities. It is not a three-run or Release comparison; the updated repeated Android/Release workflow is pending.
- Shared API/history: OpenAPI conformance, API/history/idempotency, worker recovery and PostgreSQL history PoCs passed their recorded workflows. These are PoCs, not production service validation.
- Security disposition: the first Expo-based RN attempt reported five high-severity transitive findings in Expo CLI; it was replaced with bare React Native Community CLI rather than applying a destructive downgrade. The finding and disposition are documented in `docs/architecture/evidence/issue-9-expo-cli-audit-finding.md`.

### Partial scoring and sensitivity

The input in `docs/architecture/evidence/issue-9-partial-score-input.json` scores only criteria with evidence and preserves N/E for missing dimensions. Its partial subtotals are not comparable because coverage differs: Web 74.2857/100 at 35% weight coverage, Flutter 74.2857/100 at 35%, bare React Native 60/100 at 50%, Kotlin reference 60/100 at 10%. The script returns `ranking=[]` and no full sensitivity when the matrix is incomplete.

A separate diagnostic sensitivity subset uses only charts/series, common historical persistence PoC and tests/CI for Web, Flutter and React Native. It yields Web=Flutter 74.2857 and React Native 60, with ranking unchanged across six ±20% weight scenarios. This is explicitly a subset, excludes Kotlin and six matrix criteria, and is **not** a final stack ranking. The reproducible input is `docs/architecture/evidence/issue-9-subset-sensitivity-input.json`; the CI artifact must confirm the output.

The first subset-sensitivity artifact exposed a score-scale defect (`score_out_of_100` held 0–1 fractions). The calculation and unit tests were corrected to 0–100; the earlier artifact [run 40061223306](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061223306) is superseded and must not be used for scoring.

### Decision at this checkpoint

**Do not ratify a final stack yet.** The mobile release/build workflows are still completing their updated comparable runs; the React Native Android repeated/Release run and Flutter iOS Debug/Release run are pending. The user's actual Windows 11 PC has not been measured. Real-device chart readiness, screen-reader accessibility, full dependency/licence obligation review and several matrix criteria remain N/E. The current partial scores are diagnostic only. On the same class of Ubuntu runner, the observed Flutter Android Release build was 57.13 s / 45,445,816 bytes versus React Native bare at 124.23 s / 55,447,309 bytes; this favours Flutter on that specific build metric but does not settle the ADR. React Native's Release incremental-after-JS-edit run and iOS Release comparison are still pending, as are runtime/device and local Windows measurements. Once the pending runs finish, update the matrix with the final comparable evidence and re-evaluate the sensitivity; ratify only if the full matrix is evidenced and the ranking is defensible, otherwise record a formal defer decision.


## Updated evidence checkpoint — 2026-10-24 04:53 UTC (still provisional)

The mobile build-only evidence has advanced since the earlier checkpoint:

- Flutter Android [run 40063244382](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244382): PASS; three Debug builds, incremental Debug, Release APK 45,445,816 bytes.
- Flutter iOS [run 40063244341](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244341): PASS; three Simulator Debug builds and device-target Release (code signing disabled), 14,560 KB bundle.
- React Native bare Android [run 40063271581](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271581): PASS; three Debug builds, incremental Release after JS edit, Release APK 55,447,309 bytes; `npm audit` reported zero vulnerabilities.
- React Native bare iOS [run 40063271628](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271628): PASS; three Simulator Debug builds and device-target Release (code signing disabled), 22,420 KB bundle; `npm audit` reported zero vulnerabilities.
- On the same class of Ubuntu 24.04 runner, the observed Flutter Release build was 52.52 s / 45,445,816 bytes versus React Native 128.24 s / 55,447,309 bytes. On the same class of macOS/Xcode runner, Flutter device-target Release was 44 s / 14,560 KB versus React Native 76 s / 22,420 KB. These are separate runs with different cache states and PoC artifacts; they support only the build-time/size criterion, not the overall architecture decision.
- Web browser chart PoC [run 40063297746](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063297746): PASS; three Chromium interactions and 121.467–173.772 ms chart-ready observations for the synthetic fixture.
- Python dependency scan [run 40063600439](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063600439): `pip check` PASS and `pip-audit` reported no known vulnerabilities. Licence triage is partial: 4 manual-review packages, 3 without captured licence text, and 39 packages without a separate NOTICE file/text. Missing separate NOTICE is not automatically a violation, but distribution obligations remain unreviewed.

**Still not ratified:** the common Android-emulator runtime comparison (startup/visible fixture/PSS/RSS) remains in progress; Flutter's Dart/Gradle/CocoaPods licence text inventory is being added and must be reviewed; the 4 Python licence items need resolution; the Windows 11 PC actually used by the owner has not been measured; physical-device accessibility, screen-reader behaviour, and full-matrix sensitivity remain incomplete. The subset sensitivity remains diagnostic and does not include all criteria or the Kotlin reference. Do not mark ADR-0001 ratified or close Issue #9 on build evidence alone.


## Kotlin reference evidence and comparison correction — 2026-10-24

The native Kotlin Android reference now compiles and packages successfully in [run 40064396892](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40064396892). Three clean Debug builds: 22.84 / 12.13 / 11.98 s; incremental Debug 5.74 s; Release 25.92 s; Debug APK 839,249 bytes and Release APK 638,316 bytes. The hosted runner was Ubuntu 24.04 / AMD EPYC 9V45 / 4 vCPU / ~16.77 GB / Temurin JDK 17.0.20.1. This is a different virtual CPU model from the standalone Flutter and React Native builds.

**Scoring correction:** standalone build times from different virtual CPU models are not scored head-to-head. Artifact sizes can be recorded, but performance/build-time ranking must use the shared-runner workflow or a controlled repeated run with matching hardware/software/cache conditions. The common Android emulator workflow is being extended to Flutter, React Native and Kotlin and must verify that each app visibly renders the canonical fixture before recording launch/PSS/RSS.

The Kotlin Release build uses debug-key signing solely for emulator installation, not production. The build graph has no third-party chart library; runtime dependencies are Kotlin stdlib and JetBrains annotations, while the Android Gradle/Kotlin build-plugin graph remains subject to licence review. Gradle emitted a deprecation warning for `kotlinOptions` and a future Gradle 10 compatibility warning.

ADR-0001 remains **provisional**: no overall winner is ratified until the common-emulator comparison passes, the four Python licence items and special npm/Dart/build-tool obligations are reviewed, the Windows 11 target-machine report exists, and the complete sensitivity analysis uses approved scoring weights and documented uncertainty.


## Scoring governance addendum — 2026-10-24

The required score anchors, N/E handling, full-matrix requirement and sensitivity scenarios are defined in `docs/architecture/issue-9-scoring-and-sensitivity-protocol.md`. A partial score or diagnostic subset cannot ratify the architecture. Before approval, the complete matrix must cite exact run/artifact/source evidence for every candidate/criterion, and the owner must approve the selected trade-offs after CI and residual-risk review.

At this checkpoint the ADR remains **Proposed**. The common Android runtime comparison, final platform workflows, local Windows 11 report, and full dependency/licence obligation disposition have not all passed review. No final winner is declared.
