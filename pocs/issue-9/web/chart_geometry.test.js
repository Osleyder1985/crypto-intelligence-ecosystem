import test from 'node:test';
import assert from 'node:assert/strict';
import { computeCandleGeometry } from './chart_geometry.js';

const fixtureCandles = [
  { timestamp: '2026-01-05T00:00:00Z', open: 100, high: 103, low: 99, close: 102, volume: 12 },
  { timestamp: '2026-01-05T00:05:00Z', open: 102, high: 104, low: 101, close: 101, volume: 18 },
];

test('maps each candle into finite geometry within chart bounds', () => {
  const result = computeCandleGeometry(fixtureCandles, 500, 300, 24);
  assert.equal(result.candles.length, 2);
  assert.equal(result.minPrice, 99);
  assert.equal(result.maxPrice, 104);
  for (const c of result.candles) {
    for (const key of ['x', 'openY', 'closeY', 'highY', 'lowY', 'bodyWidth']) assert.ok(Number.isFinite(c[key]));
    assert.ok(c.x >= 24 && c.x <= 476);
    assert.ok(c.bodyWidth > 0);
    assert.ok(c.highY <= c.lowY);
  }
  assert.equal(result.candles[0].rising, true);
  assert.equal(result.candles[1].rising, false);
});

test('flat-price fixture does not divide by zero', () => {
  const result = computeCandleGeometry([{ timestamp: 't', open: 5, high: 5, low: 5, close: 5, volume: 0 }], 320, 200, 20);
  assert.ok(result.candles.every(c => Number.isFinite(c.openY) && Number.isFinite(c.closeY)));
});

test('rejects empty fixture and unusable dimensions', () => {
  assert.throws(() => computeCandleGeometry([], 500, 300), /non-empty/);
  assert.throws(() => computeCandleGeometry(fixtureCandles, 20, 300, 24), /dimensions/);
});
