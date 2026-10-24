param(
  [int]$BuildRepeats = 3,
  [switch]$SkipFlutterBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $repoRoot) { throw 'Run this script from inside the crypto-intelligence-ecosystem git checkout.' }
$repoRoot = (Resolve-Path $repoRoot).Path
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $repoRoot 'artifacts/issue-9-windows'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$logDir = Join-Path $outDir $stamp
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-CommandOutput([string]$Command, [string[]]$Arguments) {
  try {
    $output = & $Command @Arguments 2>&1
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
  } catch {
    return "NOT_AVAILABLE: $($_.Exception.Message)"
  }
}

function Invoke-MeasuredCommand([string]$Name, [string]$CommandLine, [string]$WorkingDirectory) {
  $safeName = $Name -replace '[^a-zA-Z0-9_-]', '_'
  $stdout = Join-Path $logDir "$safeName.stdout.log"
  $stderr = Join-Path $logDir "$safeName.stderr.log"
  $start = Get-Date
  $process = Start-Process -FilePath $env:ComSpec -ArgumentList @('/d','/c',$CommandLine) -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  [int64]$peakBytes = 0
  while ($true) {
    $process.Refresh()
    if ($process.HasExited) { break }
    $all = @(Get-CimInstance Win32_Process -Property ProcessId,ParentProcessId,WorkingSetSize)
    $ids = New-Object 'System.Collections.Generic.HashSet[int]'
    [void]$ids.Add([int]$process.Id)
    $changed = $true
    while ($changed) {
      $changed = $false
      foreach ($p in $all) {
        if ($ids.Contains([int]$p.ParentProcessId) -and -not $ids.Contains([int]$p.ProcessId)) {
          [void]$ids.Add([int]$p.ProcessId)
          $changed = $true
        }
      }
    }
    [int64]$sampleBytes = 0
    foreach ($p in $all) {
      if ($ids.Contains([int]$p.ProcessId)) { $sampleBytes += [int64]$p.WorkingSetSize }
    }
    if ($sampleBytes -gt $peakBytes) { $peakBytes = $sampleBytes }
    Start-Sleep -Milliseconds 250
  }
  $process.WaitForExit()
  $elapsed = [Math]::Round(((Get-Date) - $start).TotalSeconds, 3)
  $result = [ordered]@{
    command = $CommandLine
    working_directory = $WorkingDirectory
    elapsed_seconds = $elapsed
    peak_process_tree_working_set_bytes = $peakBytes
    exit_code = $process.ExitCode
    stdout_log = $stdout
    stderr_log = $stderr
  }
  if ($process.ExitCode -ne 0) {
    throw "Command failed ($($process.ExitCode)): $CommandLine. See $stdout and $stderr"
  }
  return $result
}

$os = Get-CimInstance Win32_OperatingSystem
$cpu = @(Get-CimInstance Win32_Processor)
$flutterMachine = $null
if (Get-Command flutter -ErrorAction SilentlyContinue) {
  try { $flutterMachine = (flutter --version --machine | ConvertFrom-Json) } catch { $flutterMachine = $null }
}
$nodeVersion = Get-CommandOutput 'node' @('--version')
$npmVersion = Get-CommandOutput 'npm' @('--version')
$javaVersion = Get-CommandOutput 'java' @('-version')
$commit = Get-CommandOutput 'git' @('rev-parse','HEAD')
$webDir = Join-Path $repoRoot 'pocs/issue-9/web'
$webReportPath = Join-Path $logDir 'web-geometry-benchmark.json'
if (Get-Command node -ErrorAction SilentlyContinue) {
  Push-Location $webDir
  try {
    $web = & node 'benchmark.js' 2>&1
    if ($LASTEXITCODE -eq 0) { [System.IO.File]::WriteAllText($webReportPath, (($web | ForEach-Object { "$_" }) -join "`n"), (New-Object System.Text.UTF8Encoding($false))) }
  } finally { Pop-Location }
}

$buildResults = @()
if (-not $SkipFlutterBuild) {
  if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    $buildResults += [ordered]@{ status = 'SKIPPED'; reason = 'Flutter CLI not installed or not on PATH' }
  } else {
    $flutterDir = Join-Path $repoRoot 'pocs/issue-9/flutter'
    Push-Location $flutterDir
    try {
      for ($i = 1; $i -le $BuildRepeats; $i++) {
        & flutter clean
        if ($LASTEXITCODE -ne 0) { throw 'flutter clean failed' }
        $pub = Invoke-MeasuredCommand "flutter-pub-get-$i" 'flutter pub get' $flutterDir
        $build = Invoke-MeasuredCommand "flutter-android-debug-build-$i" 'flutter build apk --debug' $flutterDir
        $apk = Join-Path $flutterDir 'build/app/outputs/flutter-apk/app-debug.apk'
        $size = if (Test-Path $apk) { (Get-Item $apk).Length } else { $null }
        $buildResults += [ordered]@{ run = $i; pub_get = $pub; build = $build; debug_apk_bytes = $size }
      }
      $mainDart = Join-Path $flutterDir 'lib/main.dart'
      (Get-Item $mainDart).LastWriteTime = Get-Date
      $incremental = Invoke-MeasuredCommand 'flutter-android-incremental' 'flutter build apk --debug' $flutterDir
      $release = Invoke-MeasuredCommand 'flutter-android-release' 'flutter build apk --release' $flutterDir
      $releaseApk = Join-Path $flutterDir 'build/app/outputs/flutter-apk/app-release.apk'
      $releaseSize = if (Test-Path $releaseApk) { (Get-Item $releaseApk).Length } else { $null }
    } finally { Pop-Location }
  }
}

$report = [ordered]@{
  schema_version = '1.0'
  measurement_id = "issue-9-windows-$stamp"
  timestamp_local = (Get-Date).ToString('o')
  commit_sha = $commit
  environment = [ordered]@{
    os_caption = $os.Caption
    os_version = $os.Version
    os_build = $os.BuildNumber
    architecture = $env:PROCESSOR_ARCHITECTURE
    cpu_models = @($cpu | ForEach-Object { $_.Name })
    logical_processors = [int]($cpu | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
    total_physical_memory_bytes = [int64]$os.TotalVisibleMemorySize * 1024
    powershell_version = $PSVersionTable.PSVersion.ToString()
    node_version = $nodeVersion
    npm_version = $npmVersion
    java_version = $javaVersion
    flutter_version = $flutterMachine
  }
  build_repeats = $BuildRepeats
  flutter_android_debug_builds = $buildResults
  flutter_android_incremental_build = if ($incremental) { $incremental } else { $null }
  flutter_android_release_build = if ($release) { $release } else { $null }
  flutter_android_release_apk_bytes = if ($releaseSize) { $releaseSize } else { $null }
  web_geometry_report = if (Test-Path $webReportPath) { $webReportPath } else { $null }
  limitations = @(
    'Measurements are from this Windows machine only; do not combine with hosted CI results.',
    'Process-tree memory is sampled every 250 ms and may miss short peaks.',
    'Debug APK size is not a production size; release size is recorded separately.',
    'This script does not measure physical-device chart readiness or accessibility.'
  )
}
$json = $report | ConvertTo-Json -Depth 10
$reportPath = Join-Path $logDir 'issue-9-windows-measurement.json'
[System.IO.File]::WriteAllText($reportPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Measurement report: $reportPath"
Write-Output "Logs: $logDir"
