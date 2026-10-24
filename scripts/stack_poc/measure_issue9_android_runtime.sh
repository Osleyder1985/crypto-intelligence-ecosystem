#!/usr/bin/env bash
set -euo pipefail

: "${FLUTTER_APK:?FLUTTER_APK must point to the Flutter Release APK}"
: "${RN_APK:?RN_APK must point to the React Native Release APK}"
: "${KOTLIN_APK:?KOTLIN_APK must point to the Kotlin Android Release APK}"
OUT_DIR="${OUTPUT_DIR:-artifacts/issue-9-android-runtime}"
mkdir -p "$OUT_DIR"
CSV="$OUT_DIR/runtime-measurements.csv"
LOG="$OUT_DIR/runtime-measurements.log"
printf 'stack,run,package,activity,start_wait_ms,total_time_ms,pss_kb_max,rss_kb_max,title_visible,fixture_label_visible,fixture_data_visible,android_api\n' > "$CSV"
: > "$LOG"

SDK_ROOT="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
AAPT="$(find "$SDK_ROOT/build-tools" -type f -name aapt 2>/dev/null | sort -V | tail -n 1)"
if [[ -z "$AAPT" ]]; then echo "aapt not found under $SDK_ROOT/build-tools" >&2; exit 1; fi
API="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
echo "ANDROID_API=$API" | tee -a "$LOG"
echo "EMULATOR=$(adb shell getprop ro.product.model | tr -d '\r')" | tee -a "$LOG"
adb shell wm size 1080x1920 >/dev/null || true
adb shell settings put global window_animation_scale 0 || true
adb shell settings put global transition_animation_scale 0 || true
adb shell settings put global animator_duration_scale 0 || true

measure_app() {
  local label="$1"
  local apk="$2"
  local expected_title="$3"
  local expected_fixture="$4"
  local expected_data="$5"
  local badging pkg activity install_out start_out total wait pss rss pss_max rss_max title_visible fixture_visible data_visible ui_file data_ui_file
  badging="$("$AAPT" dump badging "$apk")"
  pkg="$(printf '%s\n' "$badging" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -n 1)"
  activity="$(printf '%s\n' "$badging" | sed -n "s/^launchable-activity: name='\([^']*\)'.*/\1/p" | head -n 1)"
  if [[ -z "$pkg" || -z "$activity" ]]; then echo "Unable to discover package/activity for $label" >&2; exit 1; fi
  echo "INSTALL stack=$label package=$pkg activity=$activity apk_bytes=$(stat -c %s "$apk")" | tee -a "$LOG"
  # Release APK transfer/install can be slow on a cold software-rendered emulator.
  # Keep the operation bounded, but preserve diagnostics if ADB stalls or install fails.
  if install_out="$(timeout 300s adb install -r "$apk" 2>&1)"; then
    :
  else
    install_status=$?
    printf '%s\n' "${install_out:-ADB install timed out or failed (exit=$install_status)}" | tee -a "$LOG" >&2
    echo "ADB_INSTALL_DIAGNOSTICS stack=$label" | tee -a "$LOG"
    timeout 15s adb devices -l 2>&1 | tee -a "$LOG" || true
    timeout 20s adb shell getprop sys.boot_completed 2>&1 | tee -a "$LOG" || true
    timeout 30s adb logcat -d -t 250 2>&1 | tail -n 250 | tee -a "$LOG" || true
    exit 1
  fi
  printf '%s\n' "$install_out" | tee -a "$LOG"
  for run in 1 2 3; do
    adb shell am force-stop "$pkg" || true
    if start_out="$(timeout 45s adb shell am start -W -n "$pkg/$activity" 2>&1)"; then
      start_status=0
    else
      start_status=$?
    fi
    printf 'START stack=%s run=%s exit=%s\n%s\n' "$label" "$run" "$start_status" "$start_out" | tee -a "$LOG"
    if [[ "$start_status" -ne 0 ]] || ! printf '%s\n' "$start_out" | grep -q 'Status: ok'; then
      echo "Activity failed to start: stack=$label run=$run package=$pkg activity=$activity" | tee -a "$LOG"
      echo "START_FAILURE_DIAGNOSTICS stack=$label run=$run" | tee -a "$LOG"
      timeout 15s adb shell dumpsys activity activities 2>&1 | tail -n 160 | tee -a "$LOG" || true
      timeout 15s adb shell dumpsys activity processes 2>&1 | tail -n 120 | tee -a "$LOG" || true
      timeout 15s adb shell pidof "$pkg" 2>&1 | tee -a "$LOG" || true
      timeout 30s adb logcat -d -t 500 2>&1 | tail -n 500 | tee -a "$LOG" || true
      exit 1
    fi
    total="$(printf '%s\n' "$start_out" | awk -F': ' '/TotalTime:/ {print $2; exit}')"
    wait="$(printf '%s\n' "$start_out" | awk -F': ' '/WaitTime:/ {print $2; exit}')"
    if [[ "$run" == 1 ]]; then sleep 3; else sleep 1; fi
    pss_max=0
    rss_max=0
    for sample in 1 2; do
      local mem pss_now rss_now
      mem="$(timeout 15s adb shell dumpsys meminfo "$pkg" 2>&1 || true)"
      pss_now="$(printf '%s\n' "$mem" | awk '/TOTAL PSS:/ {print $3; exit}')"
      rss_now="$(printf '%s\n' "$mem" | awk '/TOTAL RSS:/ {print $3; exit}')"
      if [[ "$pss_now" =~ ^[0-9]+$ ]] && (( pss_now > pss_max )); then pss_max="$pss_now"; fi
      if [[ "$rss_now" =~ ^[0-9]+$ ]] && (( rss_now > rss_max )); then rss_max="$rss_now"; fi
      sleep 1
    done
    title_visible=true
    fixture_visible=true
    if [[ "$run" == 1 ]]; then
      ui_file="$OUT_DIR/${label}-ui-initial.xml"
      timeout 20s adb shell uiautomator dump /sdcard/issue9-window.xml >/dev/null 2>&1 || true
      timeout 15s adb pull /sdcard/issue9-window.xml "$ui_file" >/dev/null 2>&1 || true
      timeout 20s adb exec-out screencap -p > "$OUT_DIR/${label}-screen-initial.png"
      title_visible=false
      fixture_visible=false
      data_visible=false
      if [[ -f "$ui_file" ]] && grep -Fq "$expected_title" "$ui_file"; then title_visible=true; fi
      if [[ -f "$ui_file" ]] && grep -Fq "$expected_fixture" "$ui_file"; then fixture_visible=true; fi
      # Scroll to the visible fixture table and inspect actual values, not only the bundled JSON file.
      for scroll in 1 2 3; do adb shell input swipe 540 1650 540 450 450; sleep 1; done
      data_ui_file="$OUT_DIR/${label}-ui-fixture-data.xml"
      timeout 20s adb shell uiautomator dump /sdcard/issue9-fixture-data.xml >/dev/null 2>&1 || true
      timeout 15s adb pull /sdcard/issue9-fixture-data.xml "$data_ui_file" >/dev/null 2>&1 || true
      timeout 20s adb exec-out screencap -p > "$OUT_DIR/${label}-screen-fixture-data.png"
      if [[ -f "$data_ui_file" ]] && grep -Fq "$expected_data" "$data_ui_file" && grep -Fq "102.0" "$data_ui_file"; then data_visible=true; fi
      if [[ "$title_visible" != true || "$fixture_visible" != true || "$data_visible" != true ]]; then
        echo "UI verification failed: stack=$label title_visible=$title_visible fixture_label_visible=$fixture_visible fixture_data_visible=$data_visible initial_hierarchy=$ui_file data_hierarchy=$data_ui_file" | tee -a "$LOG"
        exit 1
      fi
    fi
    [[ "$pss_max" -gt 0 ]] || pss_max=""
    [[ "$rss_max" -gt 0 ]] || rss_max=""
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$label" "$run" "$pkg" "$activity" "${wait:-}" "${total:-}" "$pss_max" "$rss_max" "$title_visible" "$fixture_visible" "$data_visible" "$API" >> "$CSV"
    echo "RESULT stack=$label run=$run wait_ms=${wait:-N/E} total_ms=${total:-N/E} max_pss_kb=$pss_max max_rss_kb=$rss_max title_visible=$title_visible fixture_label_visible=$fixture_visible fixture_data_visible=$data_visible" | tee -a "$LOG"
    adb shell am force-stop "$pkg" || true
  done
}

measure_app "flutter" "$FLUTTER_APK" "Market chart reference PoC" "12 synthetic OHLCV candles" "2026-01-05T00:00:00Z"
measure_app "react-native" "$RN_APK" "Crypto Intelligence" "12 candles" "2026-01-05T00:00:00Z"
measure_app "kotlin" "$KOTLIN_APK" "Kotlin chart reference" "12 synthetic OHLCV candles" "2026-01-05T00:00:00Z"
