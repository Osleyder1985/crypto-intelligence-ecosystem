import hashlib
import unittest

from scripts.market_selection.capture_pionex_fill_fee_evidence import build_evidence, normalize_fills, sign_get


def payload(count=2, fee_coin="USDT"):
    fills = []
    for i in range(count):
        fills.append({
            "id": i + 1, "orderId": 99, "symbol": "BTC_USDT", "side": "BUY" if i % 2 == 0 else "SELL",
            "role": "TAKER" if i % 2 == 0 else "MAKER", "price": "100", "size": "0.01",
            "fee": "0.0005" if fee_coin == "USDT" else "0.000005", "feeCoin": fee_coin,
            "timestamp": 1792627200000 + i,
        })
    return {"result": True, "timestamp": 1792627201000, "data": {"fills": fills}}


class PionexFillFeeEvidenceTests(unittest.TestCase):
    def test_signature_is_deterministic_and_parameter_order_independent(self):
        a = sign_get("/api/v1/trade/fills", {"symbol": "BTC_USDT", "timestamp": "123"}, "secret")
        b = sign_get("/api/v1/trade/fills", {"timestamp": "123", "symbol": "BTC_USDT"}, "secret")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_quote_currency_fee_rate_is_calculated_without_storing_order_ids(self):
        raw = b'{"result":true,"data":{"fills":[]}}'
        result = build_evidence(payload(), raw, "BTC_USDT", "USDT", 1792627100000, 1792627300000, "2026-10-22T00:00:00.000Z")
        self.assertEqual(result["fee_evidence_status"], "OBSERVED_FILLS_ONLY")
        self.assertEqual(result["observed_rate_min"], "0.0005")
        self.assertEqual(result["observed_rate_max"], "0.0005")
        self.assertNotIn("orderId", result["fills"][0])
        self.assertNotIn("id", result["fills"][0])
        self.assertEqual(result["raw_response_sha256"], hashlib.sha256(raw).hexdigest())

    def test_non_quote_fee_currency_is_indeterminate_not_converted(self):
        result = normalize_fills(payload(fee_coin="BNB"), "BTC_USDT", "USDT")
        self.assertIsNone(result[0]["fee_rate_vs_quote_notional"])
        self.assertEqual(result[0]["fee_rate_status"], "INDETERMINATE_FEE_COIN_DIFFERS_FROM_QUOTE")

    def test_out_of_range_fill_timestamp_fails_closed(self):
        a = payload()
        a["data"]["fills"][0]["timestamp"] = 10
        raw = b"raw fixture bytes"
        with self.assertRaisesRegex(ValueError, "outside the requested time range"):
            build_evidence(a, raw, "BTC_USDT", "USDT", 100, 200, "2026-10-22T00:00:00.000Z")

    def test_100_fills_are_marked_as_potentially_truncated(self):
        raw = b'raw fixture bytes'
        result = build_evidence(payload(count=100), raw, "BTC_USDT", "USDT", 1792627199000, 1792627300000, "2026-10-22T00:00:00.000Z")
        self.assertTrue(result["truncation_possible"])
        self.assertEqual(result["capture_status"], "INDETERMINATE")
        self.assertEqual(result["fee_evidence_status"], "INDETERMINATE")

    def test_mismatched_symbol_and_invalid_fee_fail_closed(self):
        a = payload()
        a["data"]["fills"][0]["symbol"] = "ETH_USDT"
        with self.assertRaisesRegex(ValueError, "symbol does not match"):
            normalize_fills(a, "BTC_USDT", "USDT")
        a = payload()
        a["data"]["fills"][0]["fee"] = "NaN"
        with self.assertRaisesRegex(ValueError, "finite and non-negative"):
            normalize_fills(a, "BTC_USDT", "USDT")


if __name__ == "__main__":
    unittest.main()
