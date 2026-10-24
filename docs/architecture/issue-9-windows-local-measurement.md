# Local Windows measurements for Issue 9

The GitHub-hosted Ubuntu/macOS runs are useful CI evidence, but they cannot represent the user's Windows PC. To collect measurements from the actual machine, run the script below from a local clone of this repository after Flutter, Android SDK/command-line tools, JDK and Node are installed.

## Command

Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\stack_poc\measure_issue9_windows.ps1
```

The script writes a timestamped JSON report and command logs under `artifacts/issue-9-windows/`. It records Windows version/build, CPU model and logical processors, installed RAM, PowerShell/Node/npm/Java/Flutter versions, three Flutter Android debug builds, an incremental build after touching the Dart source timestamp, a release build, artifact sizes, sampled process-tree working set, and the web geometry microbenchmark.

Use `-SkipFlutterBuild` if you only want the environment and web microbenchmark. Use `-BuildRepeats 3` (the default) for three build observations.

## Interpretation

- The report belongs to the exact local machine and commit recorded inside it; keep it separate from GitHub-hosted runner results.
- The process-tree memory sampler polls every 250 ms and can miss short-lived peaks. It is an approximation, not a hardware performance-counter trace.
- Debug APK size is reported separately from release APK size.
- This script does not run an Android emulator or measure on-screen chart readiness, touch latency, or screen-reader accessibility. Those require a physical device/emulator test.
- Do not enter credentials or API keys for this benchmark; the PoC uses only synthetic data.

Until this report is produced on the target Windows PC, the local Windows performance/resource cells in the stack matrix must remain N/E.
