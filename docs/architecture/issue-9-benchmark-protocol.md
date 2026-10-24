# Issue 9: Reproducible stack benchmark protocol

**Status:** protocol defined; cross-client measurements not yet executed.  
**Purpose:** make the remaining client, charting, resource, licensing, and security comparison reproducible without treating unmeasured values as evidence.  
**Decision rule:** this document defines the method, not a winning stack. Do not populate scores until raw evidence is attached.

## 1. Comparison boundary

Compare the smallest useful vertical slice for the same market-research workflow:

1. Search a canonical asset and open its detail view.
2. Request a historical OHLCV series from a shared fixture.
3. Render candles and volume, with time labels and a visible loading/empty/error state.
4. Support zoom/pan and accessible text alternatives for the chart.
5. Display evaluation history with timestamp, horizon, methodology version, status, and evidence references.
6. Request an evaluation through the versioned API; show queued/running/completed/failed/indeterminate without fabricating a result.
7. Keep provider credentials and canonical analysis rules out of the client.

Candidates: Flutter, React Native, Kotlin/Jetpack Compose as an Android reference, React/TypeScript web (Next.js only if SSR is a stated requirement; otherwise include a simpler Vite reference). Native Android is not an equivalent iOS candidate and must not be scored as a complete cross-platform solution.

## 2. Shared fixture and correctness oracle

Create one versioned, synthetic OHLCV fixture for every implementation; do not use live market data for benchmark repeatability. The fixture must include:

- UTC timestamps at a documented interval, in strictly ascending order.
- Positive OHLC prices with low <= min(open, close) <= max(open, close) <= high.
- Non-negative volume.
- A deliberate gap, a flat interval, a high-volume interval, and enough points to exercise viewport movement.
- A fixed fixture version and SHA-256 recorded in the result report.

The correctness oracle is the fixture itself: every implementation must render the same candle count, timestamp range, extrema, and volume aggregation. Any downsampling must be documented and must preserve the same selected time range and explain its aggregation rule. No fixture is to be described as historical market evidence.

## 3. Fix conditions before running

Record these for every run:

- Commit SHA, branch, fixture version and SHA-256.
- OS/build, CPU model, logical processor count, installed RAM, available disk, power mode, display scale and device/emulator model.
- Exact SDK, runtime, compiler, package manager, chart-library and dependency versions.
- Clean-build vs incremental-build status; cache state; commands and exit codes.
- Start/end timestamps, number of repetitions, raw output and any failed attempt.
- Whether the measurement is from local Windows hardware, a hosted CI runner, emulator, or physical device. Never combine these as if they were the same environment.

Run a clean build at least three times per candidate in the same environment and report each observation plus median and range; retain raw observations. If the environment cannot be held constant, label the results non-comparable instead of normalizing them by guesswork. Do not invent acceptance thresholds after observing results.

## 4. Measures

| Measure | Operational definition | Evidence to retain |
|---|---|---|
| Clean build duration | Wall-clock seconds from build command start to successful exit | Command log and timestamps |
| Incremental build duration | Same measurement after one documented source edit | Command log and timestamps |
| Build artifact size | Sum and individual sizes of distributable artifacts produced for the declared target | File list and byte counts |
| Peak memory | Peak resident memory for the build process and, separately, running app where measurable | Tool output and sampling method |
| Cold start | Time from launch request to first usable asset-detail screen | Repeated timestamped observations or automated trace |
| Chart readiness | Time from fixture availability to all required candles/volume rendered | Trace or instrumented test |
| Interaction correctness | Pan/zoom preserves selected range and values; loading/error states are truthful | Automated assertions and screen recording where useful |
| Accessibility | Keyboard/screen-reader navigation, text scaling, contrast, reduced motion and non-colour-only status cues | Checklist with OS/tool versions and failures |
| Reliability | Repeated navigation and refresh without crash, stale-data mislabelling or duplicate request effects | Test counts, logs and crash output |
| Dependency/security posture | Direct/transitive dependencies, known advisories, permissions, secrets handling and update cadence | Machine-readable scan output, timestamp and disposition |
| Licence obligations | Licence and notice for direct/transitive dependencies and chart library | SPDX/SBOM or equivalent inventory and reviewed exceptions |
| Maintenance/operations | Required toolchains, platform-specific code, CI minutes, external services and release steps | Reproducible setup notes; no unsupported cost estimate |

## 5. Reproduction workflow

For each candidate, commit a runnable vertical slice and a README with exact commands. Use pinned versions and lockfiles. Run:

1. Clean dependency installation from the lockfile.
2. Static analysis/lint and unit tests.
3. Contract tests against the same OpenAPI contract.
4. Fixture-based chart correctness tests.
5. Accessibility checks for the target platform.
6. Clean and incremental builds.
7. Repeated start/chart-readiness measurements.
8. Dependency and licence inventory.
9. A review of generated logs to confirm they contain no secrets.
10. Export raw measurements and a short result summary.

Do not claim a candidate passed a step that was not run. A CI pass on Linux does not establish build success on Windows, Android, or iOS. iOS build evidence must state whether it came from macOS and which Xcode version was used; it cannot be inferred from a Windows-only run.

## 6. Result record template

Create one record per candidate and environment. Use N/E until measured.

| Field | Value |
|---|---|
| Candidate / target | N/E |
| Commit SHA | N/E |
| Environment | N/E |
| Fixture version / SHA-256 | N/E |
| Toolchain and dependency lock | N/E |
| Clean build observations (seconds) | N/E |
| Incremental build observations (seconds) | N/E |
| Artifact size (bytes) | N/E |
| Peak memory and method | N/E |
| Cold start observations | N/E |
| Chart readiness observations | N/E |
| Correctness/accessibility result | N/E |
| Security scan and disposition | N/E |
| Licence inventory and exceptions | N/E |
| Failures and limitations | N/E |
| Raw evidence link | N/E |
| Reviewer/date | N/E |

## 7. Decision matrix discipline

Keep the existing Issue #9 weights and 1–5 scale as proposals until the product owner approves them before scoring. Every score must cite a reproducible result record. Mark unmeasured dimensions N/E; do not replace missing evidence with popularity, intuition, vendor claims, or numbers from a different environment. Do not calculate a winner while critical dimensions remain N/E.

After measurements exist, perform the documented sensitivity analysis (vary each proposed weight by ±20%, renormalize weights, and disclose whether ranking changes). This is an analytical sensitivity exercise, not a statistical confidence interval. If rankings are unstable, record the decision as unresolved and gather evidence targeted at the dimensions that change the result.

## 8. Security and licensing safeguards

- Scan locked dependencies at the time of evaluation and preserve tool/database versions and scan timestamp.
- Distinguish a known vulnerability finding from a verified exploitable vulnerability; document disposition rather than suppressing findings silently.
- Review licences for the full transitive dependency graph, charting library, fonts and bundled assets. Do not infer licence permission from repository visibility.
- Keep tokens out of source, fixtures, test output and screenshots; use disposable test credentials only.
- Treat public market data and network failures as untrusted inputs. A failed request is an error state, not a valid empty market response.
- This protocol is not an ISO certification or a substitute for a risk-based security review.

## 9. Current evidence boundary

Already verified in the Issue #9 branch: OpenAPI contract validation; API/history/idempotency PoC; SQLite worker concurrency/transaction recovery tests; PostgreSQL history PoC; and contract conformance tests on GitHub Actions run [40057411699](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40057411699). These demonstrate only the tested behaviours in those workflows.

Still not evidenced by this protocol alone: Flutter/React Native/native/web comparative builds, chart performance, local Windows resource measurements, iOS build, licence/security review results, operational cost comparison, sensitivity analysis, and final ADR approval. Do not close Issue #9 until the applicable acceptance criteria have evidence and the PR has been reviewed.
