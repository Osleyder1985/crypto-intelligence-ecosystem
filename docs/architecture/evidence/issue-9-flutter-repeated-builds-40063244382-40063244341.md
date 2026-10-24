# Flutter Android and iOS repeated build evidence — run 40063244382 / 40063244341

## Android
- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244382
- Commit: `f2f002c55e9f88d34dae0dbce49c4f8427b723fe`
- Result: PASS; Flutter widget tests and three clean Android Debug builds, incremental Debug rebuild, and Android Release build completed.
- Environment: Ubuntu 24.04.5 LTS, Linux 6.17.0-1022-azure, Intel Xeon Platinum 8573C, 4 vCPU, 16,765,370,368 bytes RAM, Flutter 3.47.5 stable, JDK 17.0.20.1.
- Clean Debug build times: 178.59 s / 17.70 s / 17.14 s.
- Debug APK size after each clean build: 150,302,356 bytes.
- Incremental Debug after source edit: 8.77 s; observed APK after edit: 165,199,496 bytes.
- Android Release build: 52.52 s; Release APK: 45,445,816 bytes.
- Peak RSS from GNU `time`: clean Debug 292,380 / 113,952 / 120,344 KB; incremental 106,772 KB; Release 125,040 KB.
- Artifact ID 12548029239 contains logs, Flutter dependency lock, pub dependency inventory and Gradle release runtime dependency listing.

The first clean build is a cold-build outlier and is retained, not discarded. Debug artifact size changed after the source edit, so only the stable clean-build APK size is used for that repeated series.

## iOS
- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063244341
- Same source commit and Flutter 3.47.5.
- Environment: macOS hosted runner, Apple Virtual Machine 1, virtual Apple M1, 3 cores, 7 GB RAM.
- iOS Simulator Debug clean builds: 81 s / 57 s / 40 s; app bundle 142,300 KB in each run.
- Incremental iOS Simulator Debug after source edit: 21 s; app bundle 142,300 KB.
- iOS device-target Release build with code signing disabled: 44 s; `Runner.app` size 14,560 KB.
- `/usr/bin/time -l` maximum RSS / peak memory footprint:
  - Simulator Debug runs: 188,661,760 / 75,581,056 bytes; 188,661,760 / 76,973,760 bytes; 188,661,760 / 76,711,616 bytes.
  - Incremental Simulator Debug: 207,929,344 / 76,760,704 bytes.
  - Device-target Release: 202,424,320 / 75,040,384 bytes.
- Artifact ID 12547842973 contains build log, pubspec lock, dependency inventory and CocoaPods inventory.

## Comparability
Android and iOS are different platforms and must not be compared directly. Compare Flutter vs React Native Android Release only on the same class of Ubuntu runner and the same emulator/runtime benchmark; compare iOS builds only for the same target (Simulator Debug vs Simulator Debug, device Release vs device Release) on comparable macOS runner images. The current numbers describe hosted PoCs, not the user's Windows 11 PC or physical-device performance. Flutter doctor also reported some Android SDK licenses not accepted on the hosted runner; the build succeeded, but the local development machine must accept applicable Android SDK licenses through the SDK manager.
