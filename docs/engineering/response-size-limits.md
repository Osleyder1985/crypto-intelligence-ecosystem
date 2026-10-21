# Response-size limits for public market-data capture

## Provenance and status

The former global `MAX_BYTES = 5 * 1024 * 1024` (5 MiB / 5,242,880 bytes) had no documented ISO/IEC or exchange-specific basis. It was an internal defensive implementation parameter, and the project had not established that it was optimal. It has now been replaced by provisional endpoint-class limits based on measured public responses. These are engineering choices, not ISO or provider requirements.

Official references consulted:
- Binance Spot REST API: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Binance market-data-only endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
- Coinbase Exchange product book endpoint: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductbook
- ISO/IEC 25010:2023: https://www.iso.org/standard/78176.html
- ISO/IEC 27001: https://www.iso.org/standard/27001

These references do not prescribe the numeric limits below.

## Provisional endpoint-class limits

| Capture class | Limit | Evidence from GitHub Actions | Rationale |
|---|---:|---:|---|
| Binance server time, filtered exchange metadata, and depth limit 20 | 64 KiB (65,536 bytes) | Largest successful response in the measured run was 15,197 bytes (filtered exchange metadata); books were 1,287–1,337 bytes | About 4.3x headroom over the largest measured response |
| OKX, Bybit, and Kraken order-book probes in this script | 64 KiB (65,536 bytes) | Successful books were 1,285–1,456 bytes; Bybit returned 96-byte HTTP 403 error bodies in the observed run | About 45x headroom over the largest successful measured book |
| Coinbase Exchange `/products/{product_id}/book?level=2` | 2 MiB (2,097,152 bytes) | BTC/USD 1,080,547 bytes; ETH/USD 485,460 bytes; SOL/USD 322,672 bytes | About 1.94x headroom over the largest measured level-2 book |

Evidence sources:
- Binance diagnostic: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39673248108
- Multi-exchange probe: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/39673248104

These are single-run observations, not guaranteed maxima or statistical percentiles. The new limits are **provisional**, must be monitored across repeated captures, and should be revised if valid responses exceed them. In particular, Coinbase level-2 returns an aggregated book whose size can vary; its 2 MiB limit is a bounded-read safeguard, not a guarantee that every future snapshot will fit.

## Runtime behavior

The clients read at most the endpoint-specific limit plus one byte to detect an oversized response without buffering the full body. An over-limit response remains a failure; a truncated prefix is never parsed or treated as a successful capture. Evidence records the configured limit, observed lower-bound byte count, declared `Content-Length` when provided, and SHA-256 of the bounded prefix. The full response hash and Base64 body are populated only when the complete response fits the cap. This avoids retaining an oversized partial body as Base64.

`Content-Length` is diagnostic only: it may be absent or inaccurate, so enforcement is based on bytes actually read. The byte count for an oversized response is explicitly a lower bound (limit + 1), not the total response size.

## Reassessment rule

Retain reproducible observations per endpoint (URL/path and query parameters, timestamp, status, declared length, observed bytes, response hash where complete, and prefix hash for overflow). Verify request scope against the provider's official API contract and evaluate memory, artifact size, and operational needs. If the response can be narrowed using documented API parameters while preserving required data, prefer the narrower request.

The selected limits are internal and provisional. Collect repeated samples across normal market conditions, track maximum and percentile sizes, test exact-boundary and over-limit behavior, and adjust the limits with an explicit safety margin. Do not attribute any threshold to a standard or exchange without an explicit source.
