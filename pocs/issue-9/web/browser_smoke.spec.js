import { test, expect } from '@playwright/test';
import { performance } from 'node:perf_hooks';

test('browser renders the shared OHLCV fixture and accessible zoom/pan controls work', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  const startedAt = performance.now();
  await page.goto('http://127.0.0.1:8000/pocs/issue-9/web/index.html');
  await expect(page.locator('#status')).toContainText('Loaded 12 synthetic candles');
  await expect(page.locator('#data tbody tr')).toHaveCount(12);
  console.log('BROWSER_CHART_READY_MS=' + (performance.now() - startedAt).toFixed(3));

  await page.getByRole('button', { name: 'Zoom in chart' }).click();
  await expect(page.locator('#status')).toContainText('Zoom 125%');

  await page.getByRole('button', { name: 'Pan chart right' }).click();
  await expect(page.locator('#status')).toContainText(/pan [1-9][0-9]*px/);

  await page.getByRole('button', { name: 'Pan chart left' }).click();
  await page.getByRole('button', { name: 'Zoom out chart' }).click();
  await expect(page.locator('#status')).toContainText('Zoom 100%');
  expect(pageErrors).toEqual([]);
});
