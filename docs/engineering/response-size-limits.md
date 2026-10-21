# Response-size limits for public market-data capture

## Provenance and status

The current MAX_BYTES = 5 * 1024 * 1024 value is an internal defensive implementation parameter (5 MiB = 5,242,880 bytes). It is not presented as an ISO/IEC requirement or a Binance/other-exchange API requirement. The project has not established that 5 MiB is optimal for every endpoint.

Official references consulted:
- Binance Spot REST API: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Binance market-data-only endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
- ISO/IEC 25010:2023: https://www.iso.org/standard/78176.html
- ISO/IEC 27001: https://www.iso.org/standard/27001

These references do not establish a universal 5 MiB HTTP response limit for these capture scripts. ISO standards are not cited as the source of this number.

## Runtime behavior

The clients read at most MAX_BYTES + 1 bytes to detect an oversized response without buffering the full body. An over-limit response remains a failure; a truncated prefix is never parsed or treated as a successful capture. Evidence records the configured cap, observed lower-bound byte count, declared Content-Length when provided, and SHA-256 of the bounded prefix. The full response hash/bytes are populated only when the complete response fits the cap. This avoids retaining an oversized partial body as Base64.

Content-Length is diagnostic only: it may be absent or inaccurate, so enforcement is based on bytes actually read. The byte count for an oversized response is explicitly a lower bound (MAX_BYTES + 1), not the total response size.

## Reassessment rule

Do not raise or remove the cap solely to make a capture pass. Before changing it, retain a reproducible failing observation (endpoint, query parameters, timestamp, status, declared length, observed lower bound, and prefix hash), verify request scope against the provider's official API contract, and evaluate memory, artifact size, and operational needs. If the response can be narrowed using documented API parameters, prefer the narrow request when it preserves required data. Any replacement threshold remains an internal engineering decision and must be justified by measured payloads and risk, not attributed to a standard or exchange without an explicit source.
