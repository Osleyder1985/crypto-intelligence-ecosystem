# Issue 9 web chart reference PoC

This is a dependency-free browser reference implementation for checking the shared synthetic OHLCV fixture and chart geometry. It is **not** a React/Vite candidate and must not be scored as if it were one. It provides a low-dependency visual baseline only.

## Run locally

Requirements: Python 3 for the static file server and Node.js 22 for the geometry unit tests. From the repository root:

```bash
cd pocs/issue-9/web
npm test
python -m http.server 8000
```

Open `http://localhost:8000/pocs/issue-9/web/` from the repository-root server (or serve the repository root with an equivalent static server). The app loads `tests/stack_poc/fixtures/ohlcv_synthetic_v1.json`, draws candlesticks and volume, and shows a text table. It does not connect to an exchange, submit orders, or generate investment advice.

## Automated checks

The GitHub Actions workflow runs Node.js tests for geometry bounds, rising/falling candles, flat-price input and invalid dimensions. It verifies the fixture provenance marker. These are unit tests, not a headless browser test and not a performance benchmark.

## Measurements and limitations

| Measure | Result |
|---|---|
| Browser/device and OS | N/E — no browser/device measurement recorded yet |
| Browser cold start | N/E |
| Chart readiness | N/E |
| Memory | N/E |
| Build duration/artifact size | N/A for this no-build static reference; do not compare this value to compiled clients |
| Accessibility | Partial: semantic status and data table present; screen-reader/keyboard testing still required |
| Security/licence | No third-party runtime package; still review repository policy and deployment headers before production |

Do not compare this baseline's zero-dependency setup against Flutter/React Native build numbers as if they were equivalent deliverables. The next client PoCs must implement the same workflow and fixture before ranking or matrix scoring.
