# Issue 9 React Native Android baseline — CI run 40059276905

**Status:** preliminary single-build baseline; repeated clean/incremental/release builds are running in the updated workflow.  
**Workflow:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059276905  
**Source commit:** `00ef33d36f11d0d0c4bc9aad5c05a78c8e7a830a`  
**Target:** Android debug APK from bare React Native Community CLI template.

## Environment

- Runner image: Ubuntu 24.04, image release `20261012.334`.
- Kernel: Linux 6.17.0-1022-azure, x86_64.
- CPU: AMD EPYC 7763 64-Core Processor; 4 virtual CPUs.
- RAM: 16,766,414,848 bytes reported by the runner.
- Node.js v22.23.3; npm 10.9.9.
- OpenJDK Temurin 17.0.20.1.
- React Native 0.88.0; React 19.3.0; CLI template generated in CI.
- Canonical fixture comparison: PASS byte-for-byte; fixture validator: PASS.

## Build and security results

- Android debug APK build: **271.10 seconds**.
- Peak resident memory reported by GNU `time`: **164,168 KB**.
- Debug APK size: **125,271,411 bytes**.
- `npm audit --audit-level=high`: PASS; reported **0 vulnerabilities** for the generated project lockfile and advisory data available to the run.
- Licence inventory: 803 package entries, 0 `UNKNOWN` labels. Counts: MIT 705, ISC 41, BSD-3-Clause 25, Apache-2.0 12, BSD-2-Clause 11, plus other declared expressions. The only `UNLICENSED` entry was the private PoC app itself.
- Generated lockfile: npm lockfile version 3, 859 package entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`.
- CI artifact: [issue-9-react-native-android-evidence, artifact 12547116357](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059276905).

## Interpretation

This is one debug build on a hosted Ubuntu runner, not three clean builds and not a production/release APK size. The later workflow repeats builds, measures incremental time, and builds a release APK. The license inventory must be reviewed for obligations/notices (including CC-BY-4.0 and BlueOak-1.0.0); a clean `npm audit` is not a complete source-code security review. Do not compare this result directly with another machine or with the user's Windows PC.
