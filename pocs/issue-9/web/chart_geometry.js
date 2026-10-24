export function computeCandleGeometry(candles, width, priceHeight, padding = 24) {
  if (!Array.isArray(candles) || candles.length === 0) throw new Error('candles must be a non-empty array');
  if (!(width > padding * 2) || !(priceHeight > 0)) throw new Error('chart dimensions must be positive');
  const minPrice = Math.min(...candles.map(c => c.low));
  const maxPrice = Math.max(...candles.map(c => c.high));
  const span = maxPrice - minPrice || 1;
  const slot = (width - padding * 2) / candles.length;
  const y = value => padding + ((maxPrice - value) / span) * (priceHeight - padding * 2);
  return {
    minPrice,
    maxPrice,
    candles: candles.map((c, i) => ({
      timestamp: c.timestamp,
      x: padding + slot * (i + 0.5),
      openY: y(c.open),
      closeY: y(c.close),
      highY: y(c.high),
      lowY: y(c.low),
      bodyWidth: Math.max(1, slot * 0.62),
      volume: c.volume,
      rising: c.close >= c.open
    }))
  };
}
