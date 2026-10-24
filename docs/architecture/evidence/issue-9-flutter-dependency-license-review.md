# Issue 9 Flutter dependency and licence review

**Status:** partial inventory; native dependency licence/security review remains open.  
**PoC source:** `pocs/issue-9/flutter/pubspec.yaml`  
**Latest inventory workflow:** `.github/workflows/issue-9-flutter-poc.yml` and `.github/workflows/issue-9-flutter-ios-poc.yml`.

## Dart package surface

The Flutter PoC declares only `flutter` from the Flutter SDK and `flutter_test` from the Flutter SDK. It has no third-party Dart charting or networking dependency; the chart is drawn by a local `CustomPainter` and the fixture is a local synthetic JSON asset. The generated `pubspec.lock` and `flutter pub deps --json` output are preserved by the updated workflows.

## Native build dependency surface

The Android workflow preserves the Gradle `releaseRuntimeClasspath` dependency tree and Gradle build environment. The iOS workflow preserves `Podfile.lock` and the installed CocoaPods list. These inventories are necessary because an SDK-only Dart dependency list does not enumerate the Android Gradle plugin, Kotlin/AndroidX transitive dependencies, Flutter engine/framework artifacts, CocoaPods or the Xcode toolchain.

## Security and licence disposition

- No third-party Dart charting package is present in this PoC.
- The runtime fixture is synthetic; the PoC does not request market APIs or embed credentials.
- A full vulnerability audit and licence/notice review of the generated native dependency trees has **not** yet been completed. Do not infer that the native dependency graph is clean merely because `pubspec.yaml` has no external packages.
- Review each captured dependency version against its official advisory source and licence text; retain the tool version, scan timestamp, findings and disposition. Any unresolved or unclassified licence remains a blocker for final ADR ratification.
- This is not an ISO certification or a declaration of complete application security.

The next review update must cite the actual workflow artifacts and enumerate the direct/transitive native dependencies, any advisories, licence files/notices and unresolved exceptions.
