# Issue 9 Windows-hosted script validation — run 40063297774

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063297774
- Result: PASS. PowerShell parser, environment capture, and web geometry capture succeeded.
- Artifact: `issue-9-windows-hosted-script-validation`, ID 12548152063, SHA-256 `81e029cbc73dac7c678fbccae0e45a71002fb22bc49235c94118311e11e3dc74`.
- Host: Windows Server 2025 Datacenter, build 26100, AMD EPYC 7763, 4 logical processors, 17,174,360,064 bytes RAM, PowerShell 7.6.7, Node v22.23.4, npm 10.9.9, Temurin JDK 17.0.20.1.
- Flutter CLI was absent; this validation intentionally used `-SkipFlutterBuild`. It did not compile an Android app.

## Web geometry on this Windows runner

- Fixture: 12 synthetic OHLCV candles, SHA-256 `0265cfa5e4d4e6673476bc7db84ed98d43147409172a00deda958bd82823f63d`.
- Conditions: 1,200 × 640 geometry, 24 px padding, 100 warm-ups, 1,000 measured iterations.
- Node geometry time: min 0.0030 ms, median 0.0033 ms, p95 0.0088 ms, max 6.0235 ms.
- Node process RSS sampled before/after: 35,315,712 / 39,587,840 bytes. This is two point samples, not peak memory.
- Full runner environment and raw JSON are in the workflow artifact.

## Limits

This is a hosted Windows Server 2025 runner, **not the user's Windows 11 PC**. Its CPU/RAM are virtualized runner resources. Do not substitute these measurements for the user's local Flutter build, nor compare the geometry microbenchmark directly with Android/iOS build times or browser chart-ready timings. The actual Windows 11 PC still requires the documented local script after Flutter/Android SDK are installed.
