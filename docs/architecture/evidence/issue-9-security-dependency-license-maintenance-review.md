# Issue 9 — security, dependency, licence and maintenance review

**Status: PARTIAL — final review remains open.** This record distinguishes completed automated checks from unresolved manual obligations. A green audit is time-bounded evidence, not a guarantee of future vulnerability-free dependencies or ISO conformity.

## Findings by component

| Component | Evidence completed | Current disposition | Remaining work |
|---|---|---|---|
| Python API/worker PoC | `pip check` passed; `pip-audit` reported no known vulnerabilities in the tested pinned environment; dependency/license inventory preserved in `docs/architecture/evidence/issue-9-python-dependency-license-review.md` | No known advisory reported by that scan at its timestamp | Re-run against current pinned requirements; review notices/obligations and the production dependency set before deployment |
| Bare React Native 0.88.0 / React 19.3.0 | Android/iOS lockfiles match SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`; `npm audit --audit-level=high` reported 0 vulnerabilities; inventory reported 0 UNKNOWN labels | Expo-based candidate with five high-severity transitive findings was rejected in favour of bare Community CLI; no destructive downgrade applied | Review legal obligations and notice requirements for MIT, ISC, BSD-3-Clause, Apache-2.0, CC-BY-4.0, BlueOak-1.0.0 and Python-2.0 entries; finish current Android Release/incremental and iOS Release runs |
| Flutter 3.47.5 | `pubspec.yaml` declares only Flutter SDK and flutter_test SDK dependencies; no third-party Dart chart library. New workflows preserve `pubspec.lock`, `flutter pub deps --json`, Gradle runtime/build-environment trees and CocoaPods lock/list | No third-party Dart package surface in the PoC; native dependency graph must still be reviewed | Inspect captured Gradle, AndroidX, Kotlin, Flutter engine and CocoaPods/Xcode dependency versions; classify licences and advisories from the actual artifacts |
| Web reference | No external runtime package dependency; Chromium smoke test passed on the earlier pinned Playwright run; the current Playwright 1.64.1 lock/audit/repeated-readiness workflow is pending | Static HTML/JS client is small in dependency surface; CI test tooling is separate from runtime | Confirm the current Playwright audit and preserve its generated lock/audit artifact; record static asset size and browser readiness measurements |
| Shared API/history contract | OpenAPI contract, idempotency, worker recovery and PostgreSQL history PoCs passed their documented workflows | The proof covers tested paths only; client PoCs do not yet consume the real API | Threat-model production auth, authorization, rate limits, provider credentials, persistence, migrations, backups, retention and observability before production use |

## Licence review rules

1. The generated React Native app itself is private PoC code and is labelled `UNLICENSED`; this is not an assertion that third-party packages are unlicensed.
2. A licence inventory label is not a legal conclusion. Review full licence texts, attribution/notice obligations, bundled assets/fonts and transitive dependencies; preserve the review date and reviewer.
3. An absent or ambiguous licence remains unresolved. Do not infer permission from repository visibility or package-manager installation success.
4. Generated native dependency inventories must be retained with the exact toolchain versions; a Dart-only dependency list is insufficient for Android/iOS.
5. Re-run vulnerability scans at the point of release and whenever lockfiles or toolchains change. Preserve scanner/database version, timestamp, findings and disposition.
6. CI build minutes and maintenance effort have not been converted to a monetary cost; repository evidence does not establish account billing rates. Cost remains N/E.

## Maintenance and operational risk

- Flutter has the smallest Dart-level dependency surface in this PoC, but requires Flutter/Dart, Gradle/Android SDK and Xcode/CocoaPods toolchains for platform builds.
- Bare React Native requires Node/npm, React Native Community CLI, Metro/Gradle and Xcode/CocoaPods. Its lockfile is guarded by SHA-256; the initial Expo candidate was dropped due to high-severity findings.
- Web avoids mobile SDKs for the browser client but still requires browser compatibility/accessibility testing, static hosting, API versioning and dependency updates for CI tooling.
- All candidates use the same API/history backend PoC; that common service still needs production threat modelling, monitoring, backup/recovery and operational ownership.

## Closure gate

This review cannot be marked complete until the Flutter native dependency artifacts and Playwright 1.64.1 audit are inspected, React Native Release/incremental builds finish, all third-party licence obligations are reviewed, and the matrix records remaining unknowns. Do not describe the system as ISO-certified or fully secure on the basis of these checks.


## React Native licence exceptions requiring disposition

The generated inventory and lockfile identify these non-standard labels; they are not `UNKNOWN`, but they still require explicit treatment:

| Package | Version | Licence label | Observed dependency context | Required action |
|---|---|---|---|---|
| `caniuse-lite` | `1.0.30001819` | CC-BY-4.0 | Browser compatibility data dependency; lockfile does not mark it exclusively dev-only | Confirm whether any data is included in the distributed app bundle. If redistributed, preserve attribution and licence notice; record the bundle inspection. |
| `minimatch` | `10.2.6` | BlueOak-1.0.0 | Marked dev dependency in the generated lockfile | Review the actual licence text and confirm it is not bundled in the end-user app; retain notice in the development dependency inventory. |
| nested `argparse` | `2.0.1` | Python-2.0 | Nested under ESLint tooling and marked dev-only in the lockfile | Review licence/notice text and confirm it is not shipped in the app bundle. |
| `Issue9RnReference` | `0.0.1` | UNLICENSED | The private PoC application itself, not a third-party package | Keep private and do not redistribute as an open-source package until an explicit project licence is chosen. |

The lockfile also contains a separate `argparse@1.0.10` MIT entry; do not conflate it with the nested `argparse@2.0.1` entry. The inventory's zero-UNKNOWN result is useful but does not itself settle these obligations. Bundle inclusion and attribution review remain open.
