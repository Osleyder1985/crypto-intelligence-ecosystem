# Issue 9 mobile PoC build, dependency and licence evidence — 2026-10-24

**Purpose:** preserve reproducible observations for the Flutter and bare React Native mobile chart references. These are PoC/CI observations, not production benchmarks or a final stack ranking.

## Shared Android runner class

Both Android PoCs ran on GitHub-hosted Ubuntu 24.04 image release `20261012.334`, x86_64, Linux 6.17.0-1022-azure, AMD EPYC 7763 with 4 virtual CPUs and 16,766,402,560 bytes of RAM. Both used Node.js 22.23.x and Eclipse Temurin OpenJDK 17.0.20.1. They ran as separate GitHub-hosted instances; the machine class matches, but the physical VM and cache state were not identical.

### Flutter 3.47.5 / Dart 3.13.4

Workflow: [run 40061691295](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061691295), source commit `75a46d3fe1beebd389cc366eb23db217b78866d8`.

| Observation | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| Clean Debug build (seconds) | 161.49 | 19.18 | 18.28 |
| Peak RSS (KB) | 290,516 | 119,948 | 106,008 |
| Debug APK bytes | 150,302,356 | 150,302,356 | 150,302,356 |

- Median clean Debug build: **19.18 s**; range: **18.28–161.49 s**.
- Debug incremental build after a source edit: **7.75 s**, peak RSS 100,724 KB.
- Release build: **55.85 s**, peak RSS 130,676 KB.
- Release APK: **45,445,816 bytes**.
- The post-edit Debug APK was reported as 165,199,496 bytes, different from the three clean outputs. This unexplained size change is preserved as an anomaly and is not used for ranking.
- Widget tests and canonical fixture byte-for-byte check passed in the workflow.

### React Native bare 0.88.0 / React 19.3.0

Workflow: [run 40061699498](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061699498), source commit `a9b8ddb90dd00d81b056cb1fe589f5936e186020`.

| Observation | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| Clean Debug build (seconds) | 152.53 | 70.36 | 67.85 |
| Peak RSS (KB) | 122,300 | 99,936 | 104,220 |
| Debug APK bytes | 125,271,411 | 125,271,411 | 125,271,411 |

- Median clean Debug build: **70.36 s**; range: **67.85–152.53 s**.
- Release build: **123.33 s**, peak RSS 109,464 KB.
- Release APK: **55,447,313 bytes**.
- Release incremental build after a JS source edit: **15.65 s**, peak RSS 103,500 KB; resulting Release APK remained 55,447,313 bytes.
- Canonical fixture check and fixture validator passed.

### Interpretation of Android build numbers

The first build in each three-run sequence is substantially slower than the subsequent builds. `flutter clean` and `gradlew clean` remove generated outputs but do not necessarily clear global package/Gradle caches. Therefore the first run is a cold-ish build, not a guaranteed clean-machine build; later runs benefit from cached dependencies and compilation state. Report every run and the range rather than relying on a single median. The separate workflow runs share the same runner image/class, but are not the same physical machine; these data are informative, not a controlled A/B experiment. The dedicated same-emulator runtime workflow is required for launch time and running-process memory.

## React Native dependency and licence audit

The build workflow ran `npm audit --audit-level=high`, which reported **0 vulnerabilities** for the resolved npm dependency graph and advisory data available at the time of the run. This does not prove absence of all vulnerabilities and does not replace source review.

Evidence artifact: [issue-9-react-native-android-evidence, artifact 12548285744](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061699498).

- Generated npm lockfile: 859 `packages` entries, 448,613 bytes, SHA-256 `7f0714a346fdc692685b06dbcb77d2368b0d71bf9e4ca94733f5ab7b8371ef3d`.
- Dependency tree JSON: 349,200 bytes, SHA-256 `4c37ca1c445b827a0b0673904c2678ee955cc6aae020d8278eed300f7c31392a`.
- Licence inventory JSON: 427,858 bytes, SHA-256 `0ffeacd147745b467234c9627f608145a41b194675cd39fe7d863f3148bbb762`.
- Inventory covers 803 dependency entries, with **0 UNKNOWN** labels. Declared labels include MIT (705), ISC (41), BSD-3-Clause (25), Apache-2.0 (12), BSD-2-Clause (11), and other expressions.
- `caniuse-lite` declares `CC-BY-4.0`; `minimatch` declares `BlueOak-1.0.0`. These need notice/attribution and licence-compatibility review for the intended distribution. The only `UNLICENSED` entry is the private PoC application itself.
- npm emitted deprecation warnings for transitive `rimraf@3.0.2` and `inflight@1.0.6`; no high-severity advisory was reported. Record these as maintenance debt to reassess when the dependency graph is pinned for the real app.

The lockfile is generated in CI and its SHA-256 is checked before `npm ci`; it is preserved in the artifact rather than committed as a lockfile. For a production application, commit and review the actual lockfile, not only its hash.

## Python PoC dependency audit

The same commit's separate Python audit [run 40061699483](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40061699483) reported:
- `pip check`: no broken requirements;
- `pip-audit`: no known vulnerabilities in the pinned requirements/advisory data available at run time;
- Python inventory: 42 entries, 16 reported `UNKNOWN` by the default metadata source.

Those 16 UNKNOWN labels are an inventory quality gap, not proof that the packages have no licence. The audit workflow has been updated to combine metadata and classifiers and preserve license/notice-file evidence; its new run must be reviewed before treating the Python licence inventory as complete. The prior inventory is retained as a historical finding.

## iOS comparability correction

The earlier Flutter iOS runs targeted `iphoneos` while React Native targeted iOS Simulator. Those artifact sizes and build times are **not comparable**. Flutter's workflow has been corrected to `--simulator`; React Native is being constrained to `ARCHS=arm64 ONLY_ACTIVE_ARCH=YES`, and both workflows now record wall-clock elapsed seconds. Only the new successful runs using those matching simulator/architecture targets may be used for an iOS comparison.

## Not yet demonstrated

- Same-emulator Flutter vs React Native launch time, UI visibility, and running-process PSS/RSS: latest benchmark run still pending/completing at this checkpoint.
- Actual user's Windows 11 build time and peak memory: the local measurement script is available, but it has not run on the user's PC.
- Physical-device chart latency, accessibility/screen-reader behavior, sustained memory, crash behavior and network/offline resilience.
- Full legal review of third-party licence obligations and notices, and upstream release/maintenance policy for the eventual pinned production dependency graph.
