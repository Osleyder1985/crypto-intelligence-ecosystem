"""Resolve Binance Spot market candidates from a preserved exchangeInfo payload.

This selects market pairs only. It does not establish canonical token identity, and it
never picks an arbitrary quote market when multiple candidates remain.
"""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "binance-spot-market-candidate-resolution-v1"
IDENTIFIER_TYPES = {"native_symbol", "base_asset"}


def resolve_spot_market_candidates(
    exchange_info_payload: dict,
    identifier: str,
    *,
    identifier_type: str = "base_asset",
    quote_asset: str | None = None,
) -> dict:
    """Return all matching active Spot markets, preserving ambiguity explicitly."""
    if not isinstance(exchange_info_payload, dict):
        raise ValueError("exchange_info_payload must be an object")
    symbols = exchange_info_payload.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("exchange_info_payload.symbols must be an array")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("identifier must be a non-empty string")
    identifier = identifier.strip()
    if identifier_type not in IDENTIFIER_TYPES:
        raise ValueError("identifier_type must be native_symbol or base_asset")
    if quote_asset is not None:
        if not isinstance(quote_asset, str) or not quote_asset.strip():
            raise ValueError("quote_asset must be a non-empty string when provided")
        quote_asset = quote_asset.strip()

    matches = []
    for item in symbols:
        if not isinstance(item, dict):
            continue
        native_symbol = item.get("symbol")
        base_asset = item.get("baseAsset")
        quote = item.get("quoteAsset")
        if not all(isinstance(value, str) and value.strip() for value in (native_symbol, base_asset, quote)):
            continue
        if item.get("status") != "TRADING" or item.get("isSpotTradingAllowed") is not True:
            continue
        target = native_symbol if identifier_type == "native_symbol" else base_asset
        if target.casefold() != identifier.casefold():
            continue
        if quote_asset is not None and quote.casefold() != quote_asset.casefold():
            continue
        matches.append({
            "symbol_native": native_symbol,
            "base_asset": base_asset,
            "quote_asset": quote,
            "status": item["status"],
            "is_spot_trading_allowed": True,
        })

    matches.sort(key=lambda item: item["symbol_native"].casefold())
    count = len(matches)
    status = "NO_MARKET" if count == 0 else "UNIQUE_MARKET" if count == 1 else "AMBIGUOUS_MARKET"
    return {
        "schema_version": SCHEMA_VERSION,
        "requested_identifier": {"type": identifier_type, "value": identifier, "quote_asset": quote_asset},
        "resolution_status": status,
        "candidate_count": count,
        "selected_market": matches[0] if count == 1 else None,
        "candidates": matches,
        "canonical_asset_identity_status": "NOT_RESOLVED",
        "reason_codes": [
            "NO_ELIGIBLE_SPOT_MARKET" if count == 0 else
            "UNIQUE_SPOT_MARKET_CANDIDATE" if count == 1 else
            "MULTIPLE_SPOT_MARKETS_REQUIRE_QUOTE_SELECTION"
        ],
    }
