# Issue 9 React Native Android repeated-build baseline — CI run 40059801811

**Status:** PASS for three clean Debug builds and Release build; this run's Debug incremental timing is not treated as a JS-bundle incremental measure. The newer workflow measures Release rebuild after touching `App.js`.  
**Run:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801811  
**Source commit:** `d90ff9399b83f80242d5fee77c624a7d4ea80d71`  
**Target:** bare React Native 0.88.0 / React 19.3.0, Android Debug and Release APK.

## Environment

- Ubuntu 24.04 runner image `ubuntu-24.04`, release `20261012.334`.
- CPU: AMD EPYC 7763 64-Core Processor, 4 vCPU.
- RAM: 16,766,414,848 bytes reported by runner.
- Node.js 22.23.3; npm 10.9.9.
- OpenJDK Temurin 17.0.20.1.
- Canonical fixture comparison and fixture validator: PASS.
- `npm audit --audit-level=high`: PASS, 0 vulnerabilities.

## Measurements

| Operation | Wall time | Peak RSS | Artifact |
|---|---:|---:|---:|
| Clean Debug build 1 | 147.40 s | 119,184 KB | 125,271,411 bytes |
| Clean Debug build 2 | 70.62 s | 100,320 KB | 125,271,411 bytes |
| Clean Debug build 3 | 67.66 s | 102,264 KB | 125,271,411 bytes |
| Release build | 124.23 s | 102,744 KB | 55,447,309 bytes |
| Debug build after JS timestamp touch | 1.98 s | 109,880 KB | 125,271,411 bytes |

Clean Debug median: **70.62 s**; range: **67.66–147.40 s**. The first build remains in the record. The 1.98 s Debug rebuild is not a valid JavaScript-bundle incremental measure because the Debug configuration may skip JS bundling. Do not compare it to Flutter's incremental Dart rebuild. The updated workflow measures Release rebuild after touching `App.js`.

## Dependency and licence inventory

- Generated package-lock: 859 package entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`, verified by the repository's lock hash guard.
- Licence inventory: 803 entries, 0 `UNKNOWN`; only the private PoC app was `UNLICENSED`. Other declarations include MIT, ISC, BSD-3-Clause, Apache-2.0, CC-BY-4.0, BlueOak-1.0.0 and Python-2.0. Legal obligations/notices still need review.
- Full logs, lockfile, dependency tree and licence inventory: artifact [12546453765](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059801811).

## Interpretation

This run used the same hosted Ubuntu runner class and toolchain as the Flutter Android run, but it is still a separate runner instance and cache state. The Release artifact/time is more suitable for distribution-build comparison than Debug. Runtime chart readiness, on-device memory and accessibility are not measured here.
