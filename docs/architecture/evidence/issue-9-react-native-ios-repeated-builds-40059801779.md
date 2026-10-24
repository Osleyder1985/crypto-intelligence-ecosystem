# Issue 9 React Native iOS repeated-build baseline — CI run 40059801779

**Status:** PASS for three clean Debug builds and one incremental Debug build; Release build measurement is added to the newer workflow and remains pending.  
**Run:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801779  
**Source commit:** `d90ff9399b83f80242d5fee77c624a7d4ea80d71`  
**Target:** bare React Native 0.88.0 / React 19.3.0, iOS Simulator Debug, code signing disabled.

## Environment

- macOS 26 ARM64 runner image `macos-26-arm64`, release `20261021.0445`.
- Apple M1 (Virtual), 3 cores, 7 GB RAM.
- Xcode 26.6.
- Node.js 22.23.4; npm 10.9.9 for app dependency installation.
- Canonical fixture comparison and Node fixture validator: PASS.
- `npm audit --audit-level=high`: PASS, 0 vulnerabilities.

## Measurements

| Operation | Wall time | Maximum RSS | Peak memory footprint | App bundle |
|---|---:|---:|---:|---:|
| Clean Debug build 1 | 64.51 s | 205,275,136 bytes | 123,276,096 bytes | 163,404 KB |
| Clean Debug build 2 | 39.76 s | 214,040,576 bytes | 123,292,480 bytes | 163,404 KB |
| Clean Debug build 3 | 40.60 s | 212,500,480 bytes | 121,801,600 bytes | 163,404 KB |
| Incremental Debug after source timestamp touch | 13.86 s | 196,411,392 bytes | 105,827,008 bytes | 163,404 KB |

Clean-build median: **40.60 s**; range: **39.76–64.51 s**. The first run remains in the record. Bundle size is the simulator Debug app and is not a production-size measure.

## Dependency/licence evidence

- Generated package-lock: 859 package entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`; same hash as the Android baseline.
- Licence inventory: 804 entries, 0 `UNKNOWN`; the only `UNLICENSED` entry was the private PoC app itself.
- Full lock, dependency tree, licence inventory and build log are in artifact [12547341038](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801779).

## Interpretation

This run validates the bare React Native iOS Simulator Debug build and its measured incremental behaviour on this hosted macOS environment. It does not measure on-screen chart readiness, physical-device accessibility, or the user's Windows PC. The newer workflow also builds Release to measure production-like artifact size; do not infer that result from this Debug baseline.
