import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import os from 'node:os';
import { performance } from 'node:perf_hooks';
import { computeCandleGeometry } from './chart_geometry.js';

const fixturePath = new URL('../../../tests/stack_poc/fixtures/ohlcv_synthetic_v1.json', import.meta.url);
const raw = readFileSync(fixturePath);
const fixture = JSON.parse(raw.toString('utf8'));
if (fixture.kind !== 'synthetic-not-market-data') throw new Error('fixture provenance marker missing');
const candles = fixture.candles;
const width = 1200;
const height = 640;
const warmupRuns = 100;
const measuredRuns = 1000;

for (let i = 0; i < warmupRuns; i += 1) computeCandleGeometry(candles, width, height, 24);
const samplesMs = [];
const rssBeforeBytes = process.memoryUsage().rss;
for (let i = 0; i < measuredRuns; i += 1) {
  const start = performance.now();
  const result = computeCandleGeometry(candles, width, height, 24);
  samplesMs.push(performance.now() - start);
  if (result.candles.length !== candles.length) throw new Error('geometry candle count mismatch');
}
const rssAfterBytes = process.memoryUsage().rss;
const sorted = [...samplesMs].sort((a, b) => a - b);
const percentile = (p) => sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * p))];
const digest = createHash('sha256').update(raw).digest('hex');
const report = {
  benchmark: 'issue-9-web-chart-geometry-v1',
  fixture_id: fixture.fixture_version,
  fixture_sha256: digest,
  fixture_candles: candles.length,
  runtime: { node: process.version, platform: process.platform, arch: process.arch },
  host: { os_type: os.type(), os_release: os.release(), cpu_model: os.cpus()[0]?.model ?? 'unknown', logical_cpus: os.cpus().length, total_memory_bytes: os.totalmem() },
  conditions: { width, height, padding: 24, warmup_runs: warmupRuns, measured_runs: measuredRuns },
  geometry_duration_ms: {
    min: Number(sorted[0].toFixed(6)),
    median: Number(percentile(0.5).toFixed(6)),
    p95: Number(percentile(0.95).toFixed(6)),
    max: Number(sorted.at(-1).toFixed(6))
  },
  process_rss_bytes: { before: rssBeforeBytes, after: rssAfterBytes, interpretation: 'two point-in-time observations, not peak memory and not a browser rendering measurement' },
  limitations: [
    'Node.js geometry computation only; excludes DOM, browser layout, GPU, network, and actual on-screen chart readiness.',
    'CI host results are specific to this runner and must not be compared directly with local Windows, Android, iOS, or another runner.',
    'Synthetic fixture is not historical market data.'
  ]
};
console.log(JSON.stringify(report, null, 2));
