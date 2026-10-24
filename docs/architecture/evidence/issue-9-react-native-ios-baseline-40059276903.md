# Issue 9 React Native iOS baseline — CI run 40059276903

**Status:** preliminary single-build baseline; superseded for ranking by the repeated-build workflow now in the branch.  
**Workflow:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059276903  
**Source commit:** `00ef33d36f11d0d0c4bc9aad5c05a78c8e7a830a`  
**Build target:** iOS Simulator Debug, code signing disabled.

## Environment

- Runner image: `macos-26-arm64`, image release `20261021.0445`.
- Host: Apple Virtual Machine 1, Apple M1 (Virtual), 3 cores, 7 GB RAM.
- Xcode: 26.6.
- Node.js: v22.23.4; npm: 10.9.9.
- React Native: 0.88.0; React: 19.3.0.
- Canonical fixture comparison: passed byte-for-byte.
- Fixture validator: passed.
- `npm audit --audit-level=high`: passed, reported 0 vulnerabilities.

## Measurements observed

- iOS Simulator build succeeded.
- Wall-clock build time: 105.40 seconds.
- Maximum resident set size reported by macOS `/usr/bin/time -l`: 204,537,856 bytes.
- Peak memory footprint reported by macOS `/usr/bin/time -l`: 118,721,216 bytes.
- A single build only; no clean-build repetition or incremental build in this run.
- App bundle size was not measured in this run; the newer workflow adds bundle-size capture.

## Dependency and licence inventory

The generated lockfile had lockfile version 3 and 859 package entries. SHA-256: `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`. It was retained in CI artifact 12546857048 rather than committed to the repository; this is a PoC lockfile and must be reviewed/committed before production use.

The generated licence inventory covered 804 packages, with zero `UNKNOWN` licence labels. Most were MIT (706), ISC (41), BSD-3-Clause (25), Apache-2.0 (12) and BSD-2-Clause (11); other expressions included `(MIT OR CC0-1.0)`, `(MIT OR Apache-2.0)`, `0BSD`, `BlueOak-1.0.0`, `CC-BY-4.0` and `Python-2.0`. The only `UNLICENSED` entry was the private PoC app itself. The full JSON inventory is in the run artifact; a full obligation/notice review is still required before ratification.

## Interpretation

This proves that the bare React Native iOS Simulator project compiled on this specific hosted macOS runner and that the scanned dependency graph had no high-severity audit findings at that run. It does not establish runtime chart performance, physical-device accessibility, Windows performance, or equivalence with Flutter. Do not compare this single build time to another runner without matching environment context.
