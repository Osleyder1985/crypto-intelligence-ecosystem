import { readFileSync } from 'node:fs';
const fixture = JSON.parse(readFileSync(new URL('../assets/ohlcv_synthetic_v1.json', import.meta.url), 'utf8'));
if (fixture.kind !== 'synthetic-not-market-data') throw new Error('fixture provenance marker missing');
if (!Array.isArray(fixture.candles) || fixture.candles.length < 10) throw new Error('fixture candle set incomplete');
let previous = -Infinity;
for (const c of fixture.candles) {
  const t = Date.parse(c.timestamp);
  if (!Number.isFinite(t) || t <= previous) throw new Error('timestamps must be strictly increasing');
  previous = t;
  if (!(c.low > 0 && c.low <= Math.min(c.open,c.close) && Math.max(c.open,c.close) <= c.high && c.volume >= 0)) throw new Error('invalid OHLCV candle: '+c.timestamp);
}
if (!fixture.candles.some(c => c.open === c.high && c.high === c.low && c.low === c.close)) throw new Error('flat candle missing');
console.log(JSON.stringify({fixture_version:fixture.fixture_version,candles:fixture.candles.length,status:'PASS',classification:fixture.kind},null,2));
