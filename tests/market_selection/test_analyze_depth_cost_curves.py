import base64
import hashlib
import json
import unittest

from scripts.market_selection.analyze_depth_cost_curves import analyze_artifact, analyze_depth_record


def record(market, provider, payload, **metadata):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    out = {
        "market_id": market, "provider": provider, "capture_status": "PASS", "http_status": 200,
        "response_base64": base64.b64encode(raw).decode(),
        "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw),
        "parsed_json": payload, "captured_at_utc": "2026-10-22T00:00:00.300Z",
    }
    out.update(metadata)
    return out


def artifact():
    market = "BTC_USDT"
    pionex = record(market, "pionex_depth", {
        "result": True, "timestamp": 1792627200250,
        "data": {"updateTime": 1792627200100, "bids": [["99", "2"], ["98", "3"]], "asks": [["101", "1"], ["102", "4"]]},
    }, source_response_at_utc="2026-10-22T00:00:00.250Z", source_market_update_at_utc="2026-10-22T00:00:00.100Z")
    binance = record(market, "binance_depth", {
        "lastUpdateId": 12, "bids": [["99", "2"], ["98", "3"]], "asks": [["101", "1"], ["102", "4"]],
    })
    return {"schema_version": "public-market-capture-batch-v1", "overall_status": "PASS",
            "created_at_utc": "2026-10-22T00:00:00.300Z",
            "universe": [{"pionex_symbol": market, "binance_symbol": "BTCUSDT", "base_asset": "BTC", "quote_asset": "USDT"}],
            "records": [pionex, binance]}


class DepthCostCurveTests(unittest.TestCase):
    def test_curves_cover_each_returned_level_without_selecting_size_or_fees(self):
        result = analyze_artifact(artifact())
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertEqual(len(result["books"]), 2)
        book = next(x for x in result["books"] if x["venue"] == "pionex")
        buy = book["execution_cost_curve"]["buy_consuming_asks"]
        sell = book["execution_cost_curve"]["sell_consuming_bids"]
        self.assertEqual(len(buy), 2)
        self.assertEqual(len(sell), 2)
        self.assertEqual(buy[-1]["cumulative_base"], 5.0)
        self.assertEqual(buy[-1]["cumulative_quote"], 509.0)
        self.assertGreater(buy[1]["slippage_bps_vs_mid"], buy[0]["slippage_bps_vs_mid"])
        self.assertGreater(sell[1]["slippage_bps_vs_mid"], sell[0]["slippage_bps_vs_mid"])
        self.assertFalse(book["fee_cost_included"])
        self.assertFalse(book["order_size_selected"])

    def test_tampered_raw_bytes_fail_closed(self):
        a = artifact()
        a["records"][0]["response_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            analyze_artifact(a)

    def test_locked_book_is_rejected(self):
        r = record("BTC_USDT", "binance_depth", {"bids": [["100", "1"]], "asks": [["100", "1"]]})
        with self.assertRaisesRegex(ValueError, "locked or crossed"):
            analyze_depth_record(r, "BTC_USDT", "binance")


if __name__ == "__main__":
    unittest.main()
