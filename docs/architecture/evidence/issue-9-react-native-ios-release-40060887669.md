# Issue 9 React Native iOS Release and incremental build — CI run 40060887669

**Status:** PASS for three clean Debug builds, Release build and Release rebuild after JavaScript source touch.  
**Run:** https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40060887669  
**Source commit:** `09477c6e85cdf843084d6b4493cde9ce8e5a1aa7`  
**Target:** bare React Native 0.88.0 / React 19.3.0, iOS Simulator Debug and Release, code signing disabled.

## Environment

- macOS 26 ARM64 runner image `macos-26-arm64`, release `20261013.0424`.
- Apple M1 (Virtual), 3 cores, 7 GB RAM.
- Xcode 26.6.
- Node.js 22.23.3; npm 10.9.9.
- `npm audit --audit-level=high`: PASS, 0 vulnerabilities.
- Lockfile: 859 package entries, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`.
- Licence inventory: 804 entries, 0 UNKNOWN; exceptions and obligations are listed in `docs/architecture/evidence/issue-9-security-dependency-license-maintenance-review.md`.

## Measurements

| Operation | Wall time | Maximum RSS | Peak memory footprint | App bundle |
|---|---:|---:|---:|---:|
| Clean Debug build 1 | 110.60 s | 207,142,912 bytes | 121,113,408 bytes | 168,604 KB |
| Clean Debug build 2 | 46.05 s | 211,861,504 bytes | 120,310,656 bytes | 166,460 KB |
| Clean Debug build 3 | 70.30 s | 211,927,040 bytes | 119,180,032 bytes | 163,404 KB |
| Release build | 79.73 s | 200,228,864 bytes | 111,315,648 bytes | 41,784 KB |
| Release rebuild after touching `App.js` | 19.27 s | 194,969,600 bytes | 103,352,896 bytes | 41,784 KB |

Clean Debug median: **70.30 s**; range: **46.05–110.60 s**. Debug bundle sizes varied across the three clean runs (163,404–168,604 KB); retain the variation rather than selecting a preferred value. Release bundle size was stable at 41,784 KB. Release incremental rebuild after a JavaScript edit is 19.27 s.

## Comparability caveat

This run used runner image release `20261013.0424` and Node 22.23.3. The recorded Flutter iOS run used a newer macOS image release and Node 22.23.4, so these two runs are not a strict same-image comparison. A rerun on the current image is queued to improve comparability. Do not infer a final iOS winner until that run completes and the exact environment is verified.
