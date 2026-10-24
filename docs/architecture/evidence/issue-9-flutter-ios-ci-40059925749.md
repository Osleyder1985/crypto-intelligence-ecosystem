# Issue 9 Flutter iOS measurements — CI run 40059925749

**Status:** PASS for three clean Debug builds, incremental Debug build and Release build.  
**Run:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059925749  
**Source commit:** `24fd8664e63926796d814ca208e88ccf8c6fbc98`  
**Target:** Flutter 3.47.5 stable, iOS device Release build with code signing disabled; Debug builds measured separately.

## Environment

- macOS 26 ARM64 runner image `macos-26-arm64`, release `20261021.0445`.
- Apple M1 (Virtual), 3 cores, 7 GB RAM.
- Xcode 26.6; Flutter 3.47.5 stable.
- Canonical fixture byte-for-byte comparison and Flutter widget tests passed in the workflow.

## Measurements

| Operation | Wall time | Maximum RSS | Peak memory footprint | App bundle |
|---|---:|---:|---:|---:|
| Clean Debug build 1 | 40.14 s | 204,455,936 bytes | 76,482,240 bytes | 97,276 KB |
| Clean Debug build 2 | 23.43 s | 202,899,456 bytes | 76,678,784 bytes | 97,276 KB |
| Clean Debug build 3 | 22.49 s | 207,044,608 bytes | 76,318,336 bytes | 97,276 KB |
| Incremental Debug after touching `lib/main.dart` | 9.61 s (timestamp-only preliminary; content-edit measurement pending) | 201,588,736 bytes | 76,695,168 bytes | 97,276 KB |
| Release build | 29.56 s | 201,195,520 bytes | 75,204,288 bytes | 14,560 KB |

Clean Debug median: **23.43 s**; range: **22.49–40.14 s**. Release build time: **29.56 s**. Release app bundle: **14,560 KB**. Code signing was disabled; this is a build artifact, not an installable signed distribution.

## Interpretation

These are hosted macOS measurements. Debug and Release sizes are reported separately; Debug is not a production-size proxy. The newer workflow also repeats the Release build after touching `lib/main.dart`; that run is pending. Do not compare these results directly with Android or Windows runs.
