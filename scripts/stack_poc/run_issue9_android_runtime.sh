#!/usr/bin/env bash
set -euo pipefail

# Runs as one Bash process: the emulator action otherwise launches each script
# line separately through /bin/sh, which breaks compound statements and heredocs.
SDK_ROOT="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
OUT_DIR="${OUTPUT_DIR:-artifacts/issue-9-android-runtime}"
mkdir -p "$OUT_DIR"

# Stop build daemons to reduce contention while collecting runtime measurements.
(cd pocs/issue-9/kotlin-android && ./gradlew --stop) || true
(cd pocs/issue-9/react-native/build-project/android && ./gradlew --stop) || true
jps -l | awk '/GradleDaemon/ {print $1}' | xargs -r kill || true

ready=0
for attempt in $(seq 1 120); do
  state="$(adb get-state 2>/dev/null || true)"
  boot="$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  if [[ "$state" == "device" && "$boot" == "1" ]]; then ready=1; break; fi
  sleep 5
done
if [[ "$ready" != "1" ]]; then
  adb devices -l || true
  adb logcat -d -t 300 || true
  echo "Android emulator did not reach device/boot_completed=1 within 10 minutes" >&2
  exit 1
fi

adb shell getprop ro.build.version.sdk
{
  echo "ADB_READY_AT=$(date -u +%FT%TZ)"
  adb devices -l
} | tee "$OUT_DIR/emulator-ready.txt"

exec bash scripts/stack_poc/measure_issue9_android_runtime.sh
