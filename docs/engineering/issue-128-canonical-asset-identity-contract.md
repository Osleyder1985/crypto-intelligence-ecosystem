# Canonical crypto-asset identity contract

## Purpose

Ticker and display name are not globally unique asset identifiers. A symbol such as BTC or ETH can be reused by unrelated projects, and an exchange pair only establishes the exchange's reported base/quote mapping for that market. Wrapped tokens, chain migrations, forks, and bridged assets require separate identities unless explicit authoritative evidence proves equivalence.

## Contract

The offline validator `scripts/market_selection/canonical_asset_identity.py` accepts:
- chain namespace and chain reference;
- asset namespace and asset reference;
- provider name and HTTPS source URL;
- SHA-256 of the evidence artifact;
- observation and capture timestamps with timezone;
- optional ticker, retained as a display/search label only.

It produces a namespaced identifier of the form `chain_namespace:chain_reference/asset_namespace:asset_reference`, consistent with the structure used by CAIP-19-style asset identifiers. This contract does not claim that any provider is authoritative, that namespaces are registered, or that cross-chain assets are economically equivalent. Those checks remain a separate source-governance step.

If identity coordinates are missing, the result is `NOT_RESOLVED` with explicit missing components. Ticker-only input never resolves identity. Malformed evidence is rejected rather than silently repaired.

## Current Binance integration

The Binance Spot capture in PR #139 verifies the base ticker reported for the exact market symbol, but deliberately retains `canonical_asset_identity_status=NOT_RESOLVED`. This identity contract is a separate building block; it is not yet wired into the report orchestrator and does not upgrade the current report to resolved identity.

## Tests and limitations

Eight tests cover resolved explicit coordinates, ticker-only abstention, evidence presence, HTTPS URLs, SHA-256 syntax, timezone-aware timestamps, reference syntax, and schema version. Tests use a controlled fixture and do not prove that a live provider's claim is true. The validator makes no network requests and does not approve a source, terms of use, token mapping, or investment conclusion.
