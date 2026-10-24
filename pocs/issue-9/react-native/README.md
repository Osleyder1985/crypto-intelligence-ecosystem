# Issue 9 React Native chart reference PoC

This reference pins React Native 0.88.0 and React 19.3.0, using the official React Native Community CLI template rather than Expo. The version selection follows the [official React Native release overview](https://reactnative.dev/releases/overview) and [compatibility matrix](https://react-native.dev/versions/). The CI builds scaffold the native Android/iOS projects from the pinned CLI/template, then inject this app screen and the canonical fixture.

The app uses React Native core components only, with no third-party charting package. It renders the canonical synthetic OHLCV fixture, candles and volume, horizontal panning, accessible zoom controls, and a textual data table.

## Scope and limits

- Fixture is synthetic, not historical market data.
- The chart is a lightweight native-View reference, not a production chart library.
- Horizontal scrolling pans; accessible zoom buttons change candle spacing. Physical-device screen-reader checks remain pending.
- It does not connect to exchanges, submit orders or provide investment advice.
- CI runs `npm audit` and generates dependency and licence inventories. The generated lockfile is checked against `package-lock.sha256` before `npm ci`, and the exact lockfile plus reports are retained as artifacts for review. The lockfile itself must be committed and reviewed before production use.

## Run locally

The CI workflow generates the bare native template in a temporary build directory, injects `App.js` and `assets/ohlcv_synthetic_v1.json`, installs its generated lockfile, and builds the platform target. The repo-level fixture validator can be run with Node:

```bash
cd pocs/issue-9/react-native
node scripts/validate_fixture.mjs
```
