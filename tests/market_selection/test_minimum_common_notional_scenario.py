import base64
import hashlib
import json
import unittest

from scripts.market_selection.analyze_minimum_common_notional_scenario import analyze_artifact


def rec(market, provider, payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return {
        "market_id": market, "provider": provider, "capture_status": "PASS", "http_status": 200,
        "response_base64": base64.b64encode(raw).decode(),
        "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw),
        "parsed_json": payload,
    }


def fixture(depth_qty="2"):
    market = "BTC_USDT"
    pionex_symbol = {
        "symbol": market, "type": "SPOT", "baseCurrency": "BTC", "quoteCurrency": "USDT",
        "enable": True, "minAmount": "10", "minTradeSize": "0.001",
    }
    binance_symbol = {
        "symbol": "BTCUSDT", "status": "TRADING", "baseAsset": "BTC", "quoteAsset": "USDT",
        "filters": [
            {"filterType": "LOT_SIZE", "minQty": "0.001", "stepSize": "0.001", "maxQty": "100"},
            {"filterType": "NOTIONAL", "minNotional": "5", "applyMinToMarket": True, "maxNotional": "100000"},
        ],
    }
    pbook = {"result": True, "timestamp": 1792627200250, "data": {
        "updateTime": 1792627200100, "bids": [["99.99", depth_qty], ["99.98", depth_qty]],
        "asks": [["100.01", depth_qty], ["100.02", depth_qty]],
    }}
    bbook = {"lastUpdateId": 123, "bids": [["99.99", depth_qty], ["99.98", "2"]],
             "asks": [["100.01", depth_qty], ["100.02", "2"]]}
    return {
        "schema_version": "public-market-capture-batch-v1", "overall_status": "PASS",
        "created_at_utc": "2026-10-22T00:00:00Z",
        "universe": [{"pionex_symbol": market, "binance_symbol": "BTCUSDT", "base_asset": "BTC", "quote_asset": "USDT"}],
        "records": [
            rec(market, "pionex", {"result": True, "data": {"symbols": [pionex_symbol]}}),
            rec(market, "binance_exchange_info", {"symbols": [binance_symbol]}),
            rec(market, "pionex_depth", pbook),
            rec(market, "binance_depth", bbook),
        ],
    }


class MinimumCommonNotionalTests(unittest.TestCase):
    def test_derives_common_quantity_from_public_minimums_and_calculates_round_trip(self):
        out = analyze_artifact(fixture())
        self.assertEqual(out["decision_status"], "INDETERMINATE")
        self.assertEqual(len(out["results"]), 1)
        item = out["results"][0]
        self.assertEqual(item["scenario_type"], "minimum_common_quote_notional_boundary")
        self.assertEqual(item["scenario_status"], "PASS")
        self.assertAlmostEqual(item["common_base_quantity"], 0.1)
        self.assertTrue(item["constraints"]["pionex_minimums_satisfied"])
        self.assertTrue(item["constraints"]["binance_minimums_satisfied"])
        self.assertAlmostEqual(item["pionex"]["buy"]["quote_notional"], 10.001)
        self.assertAlmostEqual(item["pionex"]["sell"]["quote_notional"], 9.999)
        self.assertAlmostEqual(item["pionex"]["static_snapshot_round_trip_cost_quote"], 0.012)
        self.assertAlmostEqual(item["binance"]["static_snapshot_round_trip_cost_quote"], 0.022)
        self.assertFalse(item["account_effective_fee_verified"])
        self.assertEqual(item["pionex"]["public_fee_reference"]["observed_at_utc"], "2026-10-22")
        self.assertEqual(item["binance"]["public_fee_reference"]["observed_at_utc"], "2026-10-22")
        self.assertFalse(item["orders_submitted"])

    def test_insufficient_captured_depth_is_indeterminate_without_extrapolation(self):
        out = analyze_artifact(fixture(depth_qty="0.02"))
        item = out["results"][0]
        self.assertEqual(item["scenario_status"], "INDETERMINATE")
        self.assertGreater(item["pionex"]["buy"]["uncovered_base"], 0)
        self.assertIsNone(item["pionex"]["static_snapshot_round_trip_cost_quote"])

    def test_tampered_metadata_hash_fails_closed(self):
        a = fixture()
        a["records"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            analyze_artifact(a)


if __name__ == "__main__":
    unittest.main()
