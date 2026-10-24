import { computeCandleGeometry } from './chart_geometry.js';

const canvas = document.querySelector('#chart');
const status = document.querySelector('#status');
const tbody = document.querySelector('#data tbody');
const context = canvas.getContext('2d');

function render(data) {
  const candles = data.candles;
  const ratio = window.devicePixelRatio || 1;
  const bounds = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(bounds.width * ratio));
  canvas.height = Math.round(440 * ratio);
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  const width = bounds.width;
  const height = 440;
  const plotHeight = 300;
  const padding = 32;
  const geometry = computeCandleGeometry(candles, width, plotHeight, padding);
  const maxVolume = Math.max(...candles.map(c => c.volume), 1);
  context.clearRect(0, 0, width, height);
  context.font = '12px system-ui';
  context.fillStyle = getComputedStyle(document.body).color;
  context.strokeStyle = '#8888';
  context.beginPath();
  context.moveTo(padding, plotHeight);
  context.lineTo(width - padding, plotHeight);
  context.stroke();
  for (const c of geometry.candles) {
    const color = c.rising ? '#16834a' : '#c33d3d';
    context.strokeStyle = color;
    context.fillStyle = color;
    context.beginPath();
    context.moveTo(c.x, c.highY);
    context.lineTo(c.x, c.lowY);
    context.stroke();
    const top = Math.min(c.openY, c.closeY);
    const bodyHeight = Math.max(1, Math.abs(c.closeY - c.openY));
    context.fillRect(c.x - c.bodyWidth / 2, top, c.bodyWidth, bodyHeight);
    const volumeHeight = (c.volume / maxVolume) * 82;
    context.globalAlpha = 0.65;
    context.fillRect(c.x - c.bodyWidth / 2, 330 + 82 - volumeHeight, c.bodyWidth, volumeHeight);
    context.globalAlpha = 1;
  }
  context.fillText(`High ${geometry.maxPrice}`, padding, 14);
  context.fillText(`Low ${geometry.minPrice}`, padding, plotHeight - 4);
  context.fillText('Volume', padding, 326);
  tbody.replaceChildren();
  for (const c of candles) {
    const row = document.createElement('tr');
    for (const value of [c.timestamp, c.open, c.high, c.low, c.close, c.volume]) {
      const cell = document.createElement('td');
      cell.textContent = String(value);
      row.append(cell);
    }
    tbody.append(row);
  }
  status.textContent = `Loaded ${candles.length} synthetic candles; UTC range ${candles[0].timestamp} to ${candles.at(-1).timestamp}. No live market source used.`;
}

async function load() {
  try {
    const response = await fetch('../../../tests/stack_poc/fixtures/ohlcv_synthetic_v1.json');
    if (!response.ok) throw new Error(`Fixture request failed: HTTP ${response.status}`);
    const data = await response.json();
    if (data.kind !== 'synthetic-not-market-data' || !Array.isArray(data.candles)) throw new Error('Fixture schema or provenance marker is invalid');
    render(data);
  } catch (error) {
    status.textContent = `Unable to load chart fixture: ${error.message}`;
  }
}

window.addEventListener('resize', load);
load();
