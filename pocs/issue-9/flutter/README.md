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

The workflow uses an Ubuntu GitHub-hosted runner, installs Flutter 3.47.5, runs widget tests and builds a debug APK. `/usr/bin/time -v` records the runner's build duration and peak resident memory, and `stat` reports APK bytes. These numbers are Linux hosted-runner observations, not measurements of the user's Windows PC, and must not be mixed with web or future React Native measurements. The workflow currently records one build observation; three clean repetitions and incremental-build measurements are still required by the benchmark protocol.

## Limitations

- CustomPainter chart is a minimal reference, not a production financial chart library.
- Accessibility is partial: the chart has a Semantics label and data table, but TalkBack, text scaling, orientation, and physical-device testing remain pending.
- No browser chart-ready metric or iOS/macOS build evidence is implied.
- Security/licence review of Flutter SDK and any future chart dependency remains required.
