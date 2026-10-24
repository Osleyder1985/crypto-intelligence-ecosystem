# Issue 9 Android runtime benchmark — emulator failure and remediation

**Failed run:** [40065137434](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40065137434)  
**Commit:** `4b95ca4c246dd9f398d69da126bffe7018ccba30`  
**Status:** failed runtime attempt; no comparative runtime data accepted.

## Observed failure

The Android emulator workflow built the Flutter, React Native and Kotlin release artifacts, but the shared runtime phase did not complete. Logs showed repeated `adb` failures to connect to port 5037 and the runtime script ended with exit code 124 after the available execution window. Emulator graphics also emitted ColorBuffer/texture binding errors. The workflow therefore provides no valid three-client launch-time, visible-UI, PSS or RSS comparison from this attempt.

## Corrective changes

In the next workflow revision:

- use the alternate `swiftshader` GPU mode rather than `swiftshader_indirect`;
- increase emulator boot allowance to 900 seconds;
- wait explicitly for ADB and for Android's `sys.boot_completed=1` property before measuring;
- retain three launches per app and memory samples, while checking the UI hierarchy only once per app to avoid redundant expensive dumps.

The new run is [40090510337](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40090510337). It was queued/in progress when this note was written; this document must be amended with the actual outcome, logs and artifact references after completion.

## Decision rule

Do not impute missing runtime metrics from build times or another machine. If the hosted emulator remains unstable, report the failure transparently and use a documented local Android emulator/physical-device run for runtime observations. Keep the three apps on the same emulator and record its API level, image, architecture, resolution, memory limits and exact commit.
