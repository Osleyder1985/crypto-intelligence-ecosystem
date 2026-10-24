# Native Kotlin Android chart reference build evidence — run 40064396892

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40064396892
- Result: PASS; canonical fixture check, three clean Debug builds, incremental Debug rebuild, Release build, and dependency-graph capture completed.
- Commit: `b2218b14c00f200df9365f37a1c7115ff62006cc`.
- Host: Ubuntu 24.04, image release `20261012.334`, Linux 6.17.0-1022-azure, AMD EPYC 9V45, 4 vCPU, 16,766,414,848 bytes RAM.
- Java: Temurin 17.0.20.1. System Gradle used to generate the wrapper: 9.8.1. Build wrapper pinned to Gradle 8.11.1.
- Android compileSdk/targetSdk 36, minSdk 26, Kotlin Android plugin 2.1.20, Android Gradle Plugin 8.10.1.
- The Release APK is signed with the generated debug key solely to allow emulator installation; this is not a production-signing configuration.

## Build measurements

| Build | Time | Artifact size | Peak RSS |
|---|---:|---:|---:|
| Clean Debug 1 | 22.84 s | 839,249 bytes | 128,044 KB |
| Clean Debug 2 | 12.13 s | 839,249 bytes | 106,572 KB |
| Clean Debug 3 | 11.98 s | 839,249 bytes | 108,420 KB |
| Incremental Debug after source touch | 5.74 s | 839,249 bytes | 522,008 KB |
| Release | 25.92 s | 638,316 bytes | 117,452 KB |

The unusually high incremental peak RSS is retained as observed; it must not be discarded or normalized without investigating the sampling/resource-accounting method. The three clean Debug APKs were identical in size.

## Dependency and maintenance findings

- App runtime dependency graph: `org.jetbrains.kotlin:kotlin-stdlib:2.1.20` and `org.jetbrains:annotations:13.0`; no third-party chart library or market-data client is used.
- The build-plugin graph includes Android Gradle Plugin 8.10.1, Kotlin Gradle plugin 2.1.20 and their transitive build dependencies. The full graph is retained in artifact `issue-9-kotlin-android-build-evidence`, ID 12548796271.
- Gradle emitted a deprecation warning for `kotlinOptions` and a warning that deprecated Gradle features will be incompatible with Gradle 10. These are maintenance findings, not compilation failures. A follow-up should migrate to `compilerOptions` and review plugin compatibility before a Gradle major upgrade.
- Artifact digest: SHA-256 `757877f3566bf0a57be3f62a4fead278cfc6cf688fa2a8e8795d59322f9efe83`.

## Limits

This is a hosted Ubuntu build observation, not the user's Windows 11 PC. It is not directly comparable in build time with Flutter or React Native standalone runs made on different virtual CPU models. The shared-emulator workflow must measure launch wait, visible chart content and process memory for all three apps on the same emulator. Build-tool licence obligations and production signing remain separate reviews.
