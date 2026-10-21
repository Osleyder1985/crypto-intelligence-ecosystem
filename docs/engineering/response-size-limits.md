# Complete HTTP response capture

## Policy

The market-data capture scripts must not truncate an HTTP response because it exceeds a locally chosen byte threshold. The former 5 MiB global limit and subsequent 64 KiB / 2 MiB endpoint limits were internal engineering choices, not requirements imposed by ISO/IEC or exchange documentation. They have been removed from runtime enforcement.

Official API references:
- Binance Spot REST API: https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md
- Binance market-data-only endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
- Coinbase Exchange product book endpoint: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductbook

## Runtime behavior

Both capture clients now read the complete response body in repeated chunks. `READ_CHUNK_BYTES = 65,536` is only the per-read buffer size; it is **not** a maximum response size. Reading continues until the HTTP stream reaches EOF. The byte count, SHA-256, Base64 evidence, and parsed JSON are computed from the complete body.

The response-limit field is retained in the JSON schema for compatibility and is set to `null`, meaning no application-level response-size cap is configured. There is no oversized-prefix success or truncation path.

If a network timeout, connection failure, invalid JSON, or storage failure occurs, the capture must be reported as failed rather than claimed complete. The transport timeout is a time limit, not a byte-size limit. A response cannot be guaranteed complete if the provider or connection stops sending data.

## Important scope distinction

Capturing the complete HTTP response means retaining every byte returned for the specific request. It does not automatically mean the endpoint returned every possible market-data record. Request parameters such as Binance `depth?limit=20`, OKX `sz=20`, Bybit `limit=50`, and Kraken `count=20` intentionally request limited order-book depth. Expanding those parameters is a separate API-scope decision and must respect each provider's documented maximums and response semantics.

## Resource and artifact considerations

No fixed response-size cutoff is enforced, but full-body capture necessarily consumes storage proportional to response size. The current evidence format embeds response bodies as Base64 in JSON, which adds roughly one-third encoding overhead and can increase memory use because the raw bytes, parsed JSON, and serialized artifact coexist. For very large payloads, a future storage optimization should stream the original response to an artifact file while incrementally hashing it, then parse from the stored complete body or a supported streaming parser. Such optimization must preserve the full response and must not silently truncate it.

A response that cannot be fully read or stored is a failed/incomplete capture and must never be labelled as a complete successful capture. No arbitrary byte threshold should be reintroduced without explicit user approval and documented justification.
