# Runtime provider license gate

## Purpose

The source-license review in `issue-128-provider-license-gates.md` is now backed by an offline fail-closed policy evaluator at `scripts/market_selection/provider_license_gate.py`. The evaluator does not fetch data or provide legal advice; it requires an explicit authorization record before production use.

## Current baseline

- `binance_spot_market_data`: allows only `live_technical_test` by baseline. This is not a commercial license. Internal analysis, public display, persistent storage, and redistribution require a separately reviewed authorization record.
- `defillama_api`: blocks all live use cases without an explicit approved record plus a URL and SHA-256 for written authorization.
- `coingecko_api`: requires an approved record, an explicit allowed use case, a non-demo plan for commercial product use, attribution for public display, refresh no slower than 24 hours plus encryption/deletion policy for persistent cache, and custom redistribution rights for export/redistribution.
- Unknown providers fail closed.

## Authorization record

The record is versioned as `crypto-provider-authorization-v1` and binds a provider, status, allowed use cases, terms URL/hash, review timestamp and reviewer. Provider-specific additional fields are required where the official terms impose them. The record's presence is not proof that the terms or agreement are genuine; the governance process must verify and retain the underlying authorization.

## Tests and limits

Twelve offline tests cover baseline decisions, unknown-provider blocking, written authorization, plan/scope, attribution, cache policy and redistribution rights. No real provider requests are made. A successful validation means only that the policy record meets the software contract; it does not replace legal review or provider approval.
