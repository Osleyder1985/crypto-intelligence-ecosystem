# React Native bare iOS repeated build evidence — run 40063271628

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271628
- Source commit: `a8d5e851038f98b07a9a84b0b77c1c49ed004293`
- Result: PASS; canonical fixture, dependency lock, npm audit, licence inventory, three clean iOS Simulator Debug builds, device-target Release build, and Release rebuild after JS source edit completed.
- Environment: macOS hosted runner, Apple Virtual Machine 1, virtual Apple M1, 3 cores, 7 GB RAM, Xcode 26.6, Node.js 22.23.4 / npm 10.9.9.
- React Native 0.88.0 / React 19.3.0, bare Community CLI (no Expo).
- `npm audit --audit-level=high`: zero vulnerabilities reported in the generated lockfile/advisory data at run time.
- Lockfile: 859 package entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`.
- Licence inventory: 804 entries, 0 `UNKNOWN`, 1 `UNLICENSED` (the private PoC app itself). Counts: MIT 706, ISC 41, BSD-3-Clause 25, Apache-2.0 12, BSD-2-Clause 11; other declared expressions include `(MIT OR CC0-1.0)`, `(MIT OR Apache-2.0)`, `0BSD`, `BlueOak-1.0.0`, `CC-BY-4.0` and `Python-2.0`. This is an automated inventory, not a legal obligation review.

## Build results

| Build | Time | Artifact size | Maximum RSS | Peak memory footprint |
|---|---:|---:|---:|---:|
| iOS Simulator Debug clean 1 | 85 s | 82,492 KB | 207,126,528 bytes | 118,688,384 bytes |
| iOS Simulator Debug clean 2 | 39 s | 82,492 KB | 210,796,544 bytes | 119,327,424 bytes |
| iOS Simulator Debug clean 3 | 34 s | 82,492 KB | 210,747,392 bytes | 119,163,584 bytes |
| iOS device-target Release, code signing disabled | 76 s | 22,420 KB | 197,984,256 bytes | 106,596,992 bytes |
| Incremental device-target Release after JS edit | 23 s | 21,400 KB after edit | 195,788,800 bytes | 104,467,200 bytes |

No incremental Simulator Debug measurement was recorded by this workflow; do not infer it from the Release rebuild. The app size changing after the JS edit is recorded as observed and is not treated as a production artifact-size guarantee.

## Comparison with Flutter

On the same runner class (macOS 26 ARM64 / virtual Apple M1 / 3 cores / 7 GB / Xcode 26.6), the current Flutter run measured iOS Simulator Debug 81 / 57 / 40 s, 142,300 KB app bundle, and device-target Release 44 s / 14,560 KB. These separate workflow runs have their own cache states, so build times are observations rather than a controlled A/B. On this evidence, Flutter's device-target Release build was faster and the app bundle smaller; that is only one criterion and does not determine the overall stack choice. The common Android emulator runtime benchmark, actual Windows 11 local build, physical-device readiness and accessibility remain pending.


## Licence-expression follow-up list from the 804-entry inventory

The non-baseline expressions requiring obligation/notice review are:
- `caniuse-lite@1.0.30001819` — `CC-BY-4.0` (review attribution and source/notice requirements).
- `minimatch@10.2.6` — `BlueOak-1.0.0` (review its own terms; do not treat it as MIT/BSD).
- `argparse@2.0.1` — `Python-2.0`.
- `fb-dotslash@0.5.8` — `MIT OR Apache-2.0`.
- `jsc-safe-url@0.2.4` — `0BSD`.
- `type-fest@0.20.2`, `type-fest@0.21.3`, `type-fest@0.7.1` — `MIT OR CC0-1.0`.
- `Issue9RnReference@0.0.1` is the private PoC app's own `UNLICENSED` entry, not an external dependency.

This list identifies where review effort should focus; it does not itself satisfy attribution/notice obligations. Preserve the exact lockfile and inventory artifact when a release candidate is prepared, verify the license text for each exact package version, and generate the product's third-party notices bundle before distribution.
