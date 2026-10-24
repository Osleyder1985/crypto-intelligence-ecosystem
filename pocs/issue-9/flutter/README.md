# Issue 9 Flutter chart reference PoC

This app is a dependency-free Flutter reference for Android chart rendering. It loads a byte-for-byte copy of the canonical synthetic OHLCV fixture, draws candles and volume with `CustomPainter`, supports pinch-to-zoom and drag-to-pan through `InteractiveViewer`, and displays a data table. It has no exchange integration or trading functionality.

## Local commands

Requires Flutter SDK 3.47.5 or a compatible SDK and Android build tooling for APK generation. The repository intentionally stores the Dart app and generates the platform-specific Android scaffold during setup:

```bash
cd pocs/issue-9/flutter
flutter create --platforms=android --project-name issue_9_flutter_chart_reference --org com.crypto.intelligence --no-pub .
flutter pub get
flutter test
flutter build apk --debug
```

The canonical fixture is `tests/stack_poc/fixtures/ohlcv_synthetic_v1.json`; the asset copy must remain byte-for-byte identical. The CI workflow checks this using `cmp` before testing/building.

## CI evidence

The workflows use GitHub-hosted Ubuntu and macOS runners, install Flutter 3.47.5, run widget tests, record three clean Debug builds, an incremental build, and a Release build, and preserve time/memory/artifact measurements. These are hosted-runner observations, not measurements of the user's Windows PC, and must not be mixed with results from different hardware as if they were a controlled head-to-head comparison.

## Limitations

- CustomPainter chart is a minimal reference, not a production financial chart library.
- Accessibility is partial: the chart has a Semantics label and data table, but TalkBack, text scaling, orientation, and physical-device testing remain pending.
- No browser chart-ready metric or iOS/macOS build evidence is implied.
- CI inventories the resolved Dart package graph, copies available licence/notice texts with SHA-256 hashes, and flags missing text for manual review. For SDK packages without a package-local licence file, the inventory falls back to the Flutter SDK root licence. This is evidence collection, not SPDX classification or legal approval; build-tool and platform licence obligations still require review.


The CI workflows pin Flutter 3.47.5 (stable) and record the exact Flutter/Xcode or Android runner context alongside build measurements. See the [official Flutter release archive](https://docs.flutter.dev/release/archive).
