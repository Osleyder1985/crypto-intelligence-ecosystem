import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const directory = process.argv[2] ?? 'benchmark-measurements';
const files = readdirSync(directory).filter(name => /^run-[1-3]\.json$/.test(name)).sort();
if (files.length !== 3) throw new Error(`expected exactly 3 raw benchmark reports, found ${files.length}`);
const reports = files.map(name => JSON.parse(readFileSync(join(directory, name), 'utf8')));
const fixtureHashes = new Set(reports.map(r => r.fixture_sha256));
const runtimes = new Set(reports.map(r => JSON.stringify(r.runtime)));
const hosts = new Set(reports.map(r => JSON.stringify(r.host)));
if (fixtureHashes.size !== 1 || runtimes.size !== 1 || hosts.size !== 1) {
  throw new Error('fixture, runtime, or host differs between repetitions; do not aggregate non-comparable runs');
}
const sorted = reports.map(r => r.geometry_duration_ms.median).sort((a, b) => a - b);
const median = sorted[1];
const summary = {
  benchmark: 'issue-9-web-chart-geometry-three-run-summary-v1',
  repetitions: reports.length,
  fixture_sha256: reports[0].fixture_sha256,
  runtime: reports[0].runtime,
  host: reports[0].host,
  per_process_median_ms: reports.map((r, i) => ({ run: i + 1, median_ms: r.geometry_duration_ms.median, p95_ms: r.geometry_duration_ms.p95, min_ms: r.geometry_duration_ms.min, max_ms: r.geometry_duration_ms.max, rss_before_bytes: r.process_rss_bytes.before, rss_after_bytes: r.process_rss_bytes.after })),
  across_process_median_of_medians_ms: median,
  across_process_median_range_ms: { min: sorted[0], max: sorted[2] },
  limitations: [
    'Three fresh Node processes in one hosted CI job, not three clean application builds.',
    'Geometry microbenchmark only; excludes browser rendering and does not measure peak memory.',
    'Hosted Linux results are not directly comparable to local Windows, Android, iOS, or other runner types.'
  ]
};
mkdirSync(directory, { recursive: true });
writeFileSync(join(directory, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary, null, 2));
