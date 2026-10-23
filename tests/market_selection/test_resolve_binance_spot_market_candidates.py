import unittest

from scripts.market_selection.resolve_binance_spot_market_candidates import (
    SCHEMA_VERSION,
    resolve_spot_market_candidates,
)


def payload():
    return {"symbols": [
        {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT",
         "status": "TRADING", "isSpotTradingAllowed": True},
        {"symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC",
         "status": "TRADING", "isSpotTradingAllowed": True},
        {"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC",
         "status": "TRADING", "isSpotTradingAllowed": True},
        {"symbol": "OLDUSDT", "baseAsset": "OLD", "quoteAsset": "USDT",
         "status": "BREAK", "isSpotTradingAllowed": True},
        {"symbol": "HALTUSDT", "baseAsset": "HALT", "quoteAsset": "USDT",
         "status": "TRADING", "isSpotTradingAllowed": False},
    ]}


class BinanceSpotMarketCandidateResolutionTests(unittest.TestCase):
    def test_base_ticker_with_multiple_quote_markets_is_ambiguous(self):
        result = resolve_spot_market_candidates(payload(), "btc")
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(result["resolution_status"], "AMBIGUOUS_MARKET")
        self.assertEqual(result["candidate_count"], 2)
        self.assertIsNone(result["selected_market"])
        self.assertEqual([item["symbol_native"] for item in result["candidates"]], ["BTCUSDC", "BTCUSDT"])
        self.assertEqual(result["canonical_asset_identity_status"], "NOT_RESOLVED")

    def test_quote_filter_selects_exactly_one_market(self):
        result = resolve_spot_market_candidates(payload(), "BTC", quote_asset="usdt")
        self.assertEqual(result["resolution_status"], "UNIQUE_MARKET")
        self.assertEqual(result["selected_market"]["symbol_native"], "BTCUSDT")

    def test_exact_native_symbol_resolves_one_market(self):
        result = resolve_spot_market_candidates(payload(), "ethbtc", identifier_type="native_symbol")
        self.assertEqual(result["resolution_status"], "UNIQUE_MARKET")
        self.assertEqual(result["selected_market"]["base_asset"], "ETH")

    def test_non_trading_and_spot_disabled_markets_are_excluded(self):
        for ticker in ("OLD", "HALT"):
            result = resolve_spot_market_candidates(payload(), ticker)
            self.assertEqual(result["resolution_status"], "NO_MARKET")
            self.assertEqual(result["candidate_count"], 0)

    def test_missing_or_invalid_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "symbols must be an array"):
            resolve_spot_market_candidates({}, "BTC")
        with self.assertRaisesRegex(ValueError, "non-empty"):
            resolve_spot_market_candidates(payload(), " ")
        with self.assertRaisesRegex(ValueError, "identifier_type"):
            resolve_spot_market_candidates(payload(), "BTC", identifier_type="name")


if __name__ == "__main__":
    unittest.main()
