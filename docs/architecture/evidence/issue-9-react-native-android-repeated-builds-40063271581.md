# React Native bare Android repeated build evidence — run 40063271581

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063271581
- Source commit: `a8d5e851038f98b07a9a84b0b77c1c49ed004293`
- Result: PASS; canonical fixture, npm audit, dependency tree/licence inventory, three clean Android Debug builds, Android Release build, and incremental Release rebuild after JS edit all completed.
- Environment: Ubuntu 24.04, image `20261012.334`, Linux 6.17.0-1022-azure, AMD EPYC 7763, 4 vCPU, 16,766,414,848 bytes RAM, Node.js 22.23.3 / npm 10.9.9, Temurin JDK 17.0.20.1.
- React Native 0.88.0 / React 19.3.0, bare Community CLI (no Expo).
- `npm audit --audit-level=high`: zero vulnerabilities reported in the generated lockfile/advisory data at run time.
- Lockfile: 859 entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`.
- Licence inventory: 804 entries, 0 `UNKNOWN`, 1 `UNLICENSED` (the private PoC app itself). Counts: MIT 706, ISC 41, BSD-3-Clause 25, Apache-2.0 12, BSD-2-Clause 11, plus Python-2.0, CC-BY-4.0, BlueOak-1.0.0, 0BSD and dual-licence expressions. See the separate iOS evidence report for the versioned expression list and review obligations.
- Artifact: `issue-9-react-native-android-evidence`, ID 12549010233, SHA-256 `c79cdbeb8ac529927b458c2ea283db9a676691fcc16d40ce7243a561e1612710`.

## Build measurements

| Build | Time | Artifact size | Peak RSS |
|---|---:|---:|---:|
| Clean Debug 1 | 156.13 s | 125,271,411 bytes | 116,276 KB |
| Clean Debug 2 | 70.88 s | 125,271,411 bytes | 96,612 KB |
| Clean Debug 3 | 68.90 s | 125,271,411 bytes | 99,116 KB |
| Release | 128.24 s | 55,447,309 bytes | 100,632 KB |
| Incremental Release after JS edit | 17.19 s | 55,447,309 bytes | 103,112 KB |

The first clean build is retained as the cold-build observation. The three Debug APKs were identical in size. Release results are the relevant artefacts for comparison with Flutter Release on the same class of Ubuntu runner.

## Limits

These are hosted CI build results, not measurements from the user's Windows 11 PC. The separate common-emulator benchmark must complete before comparing launch wait, chart visibility and process memory. The inventory does not replace a legal review of third-party licence obligations and notices.
