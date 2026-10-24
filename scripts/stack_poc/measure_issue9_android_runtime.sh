#!/usr/bin/env bash
set -euo pipefail

: "${FLUTTER_APK:?FLUTTER_APK must point to the Flutter Release APK}"
: "${RN_APK:?RN_APK must point to the React Native Release APK}"
OUT_DIR="${OUTPUT_DIR:-artifacts/issue-9-android-runtime}"
mkdir -p "$OUT_DIR"
CSV="$OUT_DIR/runtime-measurements.csv"
LOG="$OUT_DIR/runtime-measurements.log"
printf 'stack,run,package,activity,start_wait_ms,total_time_ms,pss_kb_max,rss_kb_max,title_visible,fixture_label_visible,android_api\n' > "$CSV"
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
  local badging pkg activity install_out start_out total wait pss rss pss_max rss_max title_visible fixture_visible ui_file
  badging="$("$AAPT" dump badging "$apk")"
  pkg="$(printf '%s\n' "$badging" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -n 1)"
  activity="$(printf '%s\n' "$badging" | sed -n "s/^launchable-activity: name='\([^']*\)'.*/\1/p" | head -n 1)"
  if [[ -z "$pkg" || -z "$activity" ]]; then echo "Unable to discover package/activity for $label" >&2; exit 1; fi
  echo "INSTALL stack=$label package=$pkg activity=$activity apk_bytes=$(stat -c %s "$apk")" | tee -a "$LOG"
  install_out="$(adb install -r "$apk" 2>&1)"
  printf '%s\n' "$install_out" | tee -a "$LOG"
  for run in 1 2 3; do
    adb shell am force-stop "$pkg" || true
    start_out="$(adb shell am start -W -n "$pkg/$activity" 2>&1)"
    printf 'START stack=%s run=%s\n%s\n' "$label" "$run" "$start_out" | tee -a "$LOG"
    total="$(printf '%s\n' "$start_out" | awk -F': ' '/TotalTime:/ {print $2; exit}')"
    wait="$(printf '%s\n' "$start_out" | awk -F': ' '/WaitTime:/ {print $2; exit}')"
    sleep 5
    pss_max=0
    rss_max=0
    for sample in 1 2 3; do
      local mem pss_now rss_now
      mem="$(adb shell dumpsys meminfo "$pkg" 2>&1 || true)"
      pss_now="$(printf '%s\n' "$mem" | awk '/TOTAL PSS:/ {print $3; exit}')"
      rss_now="$(printf '%s\n' "$mem" | awk '/TOTAL RSS:/ {print $3; exit}')"
      if [[ "$pss_now" =~ ^[0-9]+$ ]] && (( pss_now > pss_max )); then pss_max="$pss_now"; fi
      if [[ "$rss_now" =~ ^[0-9]+$ ]] && (( rss_now > rss_max )); then rss_max="$rss_now"; fi
      sleep 1
    done
    ui_file="$OUT_DIR/${label}-ui-${run}.xml"
    adb shell uiautomator dump /sdcard/issue9-window.xml >/dev/null 2>&1 || true
    adb pull /sdcard/issue9-window.xml "$ui_file" >/dev/null 2>&1 || true
    title_visible=false
    fixture_visible=false
    if [[ -f "$ui_file" ]] && grep -Fq "$expected_title" "$ui_file"; then title_visible=true; fi
    if [[ -f "$ui_file" ]] && grep -Fq "$expected_fixture" "$ui_file"; then fixture_visible=true; fi
    [[ "$pss_max" -gt 0 ]] || pss_max=""
    [[ "$rss_max" -gt 0 ]] || rss_max=""
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$label" "$run" "$pkg" "$activity" "${wait:-}" "${total:-}" "$pss_max" "$rss_max" "$title_visible" "$fixture_visible" "$API" >> "$CSV"
    echo "RESULT stack=$label run=$run wait_ms=${wait:-N/E} total_ms=${total:-N/E} max_pss_kb=$pss_max max_rss_kb=$rss_max title_visible=$title_visible fixture_label_visible=$fixture_visible" | tee -a "$LOG"
    adb shell am force-stop "$pkg" || true
  done
}

measure_app "flutter" "$FLUTTER_APK" "Market chart reference PoC" "12 synthetic OHLCV candles"
measure_app "react-native" "$RN_APK" "Crypto Intelligence" "12 candles"
