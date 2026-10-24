# Issue 9 web chart and browser benchmark evidence — run 40063297746

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063297746
- Commit: `135ede409dfad926b03b3725067ec1b708c76fca`
- Result: PASS; all workflow steps completed successfully.
- Runtime: Ubuntu GitHub-hosted runner, Node.js 22, Chromium 156.0.8078.4, Playwright Test 1.64.1.
- Canonical fixture: synthetic-only OHLCV fixture; validation passed.

## Browser interaction checks

Three Playwright repetitions passed. Each verified that the browser renders the shared 12-candle OHLCV fixture, exposes accessible zoom/pan controls, and permits the tested zoom/pan interaction without a browser page error. Chart-ready observations recorded by the browser were 128.745 ms, 173.772 ms, and 121.467 ms. These are three samples on one hosted runner, not a cross-device performance guarantee.

## Geometry-only microbenchmark

Three independent fresh Node processes reported median geometry-computation times of 0.003226 ms, 0.003296 ms, and 0.003226 ms. The aggregate median-of-medians was 0.003226 ms. Per-process p95 values were 0.007404 ms, 0.007684 ms, and 0.007134 ms. The largest observed single sample in each process was 0.519380 ms, 0.538215 ms, and 0.512817 ms.

The geometry microbenchmark excludes DOM rendering, browser layout, GPU, network, and actual on-screen readiness; it does not measure memory. Use the Playwright chart-ready observations for browser readiness, not the geometry-only numbers.

## Security/dependency result and caveats

The Playwright tooling install and `npm audit --audit-level=high` passed; npm reported zero vulnerabilities. The lockfile and JSON audit report are retained in artifact `issue-9-web-geometry-benchmark` (artifact ID 12548282897). The log emitted upstream Node deprecation warnings for `punycode` and legacy `url.parse()`, plus a GitHub Actions Node 20 deprecation warning for pinned actions. These are maintenance warnings, not a reported npm advisory; track upgrades of the action revisions and investigate the transitive package emitting the Node warnings before production.

## Limits

This is web PoC evidence, not a full production chart benchmark. No peak memory, long historical series, high-frequency update load, touch-device behaviour, screen-reader audit, or API-backed rendering was measured. Do not compare the Node geometry timing to mobile app build times or mobile runtime measurements.
