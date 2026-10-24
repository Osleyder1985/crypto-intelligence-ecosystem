# Issue 9 Flutter Android measurements — CI run 40059925721

**Status:** PASS for the measured build workflow.  
**Run:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40059925721  
**Source commit:** `24fd8c51a0aaf1c7a31863f8cf4055b3a16c5ed5`  
**Target:** Flutter 3.47.5 stable, Android debug APK plus a separate release APK.

## Environment

- Ubuntu 24.04.5 LTS; runner image `ubuntu-24.04`, release `20261012.334.1`.
- CPU: AMD EPYC 7763 64-Core Processor, 4 vCPU.
- RAM: 16,766,414,848 bytes reported by `free -b`.
- Flutter 3.47.5 stable.
- OpenJDK Temurin 17.0.20.1.
- Node.js 22.23.3.
- Canonical synthetic OHLCV fixture comparison and widget tests passed in the same workflow.

## Measurements

| Operation | Wall time | Peak RSS | Artifact |
|---|---:|---:|---:|
| Clean debug build 1 | 163.34 s | 281,224 KB | 150,302,356 bytes |
| Clean debug build 2 | 19.42 s | 116,092 KB | 150,302,356 bytes |
| Clean debug build 3 | 18.74 s | 108,880 KB | 150,302,356 bytes |
| Incremental debug build after source timestamp touch | 4.50 s | 102,080 KB | 150,302,356 bytes |
| Release build | 57.13 s | 124,632 KB | 45,445,816 bytes |

The three clean-build observations have median **19.42 s** and range **18.74–163.34 s**. The first run is a cold-run outlier and must remain in the record; do not discard it to improve the result. The debug APK is not a production-size proxy; release APK is recorded separately.

## Warning observed

During the release build, Flutter printed `Caught exception: Already watching path: .../pocs/issue-9/flutter/android`, but the command exited successfully and produced the release APK. This is recorded as a non-fatal tooling warning, not silently ignored. Check whether it recurs in the updated workflow and retain the log if it does.

## Interpretation

These are hosted Ubuntu measurements, not measurements of the user's Windows 11 PC. They are comparable only with runs using the same OS/runner/toolchain conditions; they are not directly comparable to the macOS/iOS or Windows results. Runtime chart readiness, actual device memory and accessibility remain separate tests.
