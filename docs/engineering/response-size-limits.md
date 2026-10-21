# Response-size limits for public market-data capture

## Provenance and status

The current `MAX_BYTES = 5 * 1024 * 1024` value is an internal defensive implementation parameter (5 MiB = 5,242,880 bytes). It is not an ISO/IEC requirement or a Binance/other-exchange API requirement. The project has not established that 5 MiB is optimal for any of these endpoints.

Official references consulted:
- Binance Spot REST API: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Binance market-data-only endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
- ISO/IEC 25010:2023: https://www.iso.org/standard/78176.html
- ISO/IEC 27001: https://www.iso.org/standard/27001

These references do not establish a universal 5 MiB HTTP response limit for these capture scripts. ISO standards are not cited as the source of this number.

## Current status: provisional, pending measured evidence

Do not interpret the current value as approved or empirically validated. It is retained temporarily while evidence is collected because removing a bound before implementing and testing a replacement could expose the capture jobs to unbounded response reads. That operational concern does not justify 5 MiB specifically.

The capture summaries print, per endpoint, the configured limit, the complete response byte count when available, the observed lower bound for oversized responses, and the declared `Content-Length` when supplied. The uploaded JSON artifact remains the detailed evidence source. Compare raw response sizes across repeated successful captures before selecting a replacement. One successful sample is not enough to establish a safe upper bound.

## Runtime behavior

The clients read at most `MAX_BYTES + 1` bytes to detect an oversized response without buffering the full body. An over-limit response remains a failure; a truncated prefix is never parsed or treated as a successful capture. Evidence records the configured cap, observed lower-bound byte count, declared `Content-Length` when provided, and SHA-256 of the bounded prefix. The full response hash/bytes are populated only when the complete response fits the cap. This avoids retaining an oversized partial body as Base64.

`Content-Length` is diagnostic only: it may be absent or inaccurate, so enforcement is based on bytes actually read. The byte count for an oversized response is explicitly a lower bound (`MAX_BYTES + 1`), not the total response size.

## Reassessment rule

Before changing the cap, retain reproducible observations per endpoint (URL/path and query parameters, timestamp, status, declared length, observed bytes, response hash where complete, and prefix hash for overflow), verify request scope against the provider's official API contract, and evaluate memory, artifact size, and operational needs. If the response can be narrowed using documented API parameters while preserving required data, prefer the narrower request.

Choose endpoint-specific limits from documented response scope and measured payloads with an explicit safety margin, then test exact-boundary and over-limit behavior. If measurements are not sufficient to support a number, keep the value explicitly provisional rather than claiming it is justified. Any replacement threshold is an internal engineering decision unless an official source explicitly states otherwise.
