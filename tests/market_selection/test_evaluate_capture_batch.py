"""Offline tests for the multi-pair capture evaluator."""
import base64, hashlib, json, unittest
from scripts.market_selection.evaluate_capture_batch import evaluate_batch

def rec(market, provider, payload):
    raw=json.dumps(payload,separators=(",",":")).encode()
    return {"market_id":market,"provider":provider,"capture_status":"PASS","http_status":200,
      "response_base64":base64.b64encode(raw).decode(),"response_sha256":hashlib.sha256(raw).hexdigest(),
      "response_bytes":len(raw),"parsed_json":payload}
def fixture():
    market="BTC_USDT"
    pionex_depth = rec(market,"pionex_depth",{
      "result":True,"timestamp":1792454400250,
      "data":{"updateTime":1792454400100,"bids":[["99.99","10"]],"asks":[["100.01","10"]]}
    })
    pionex_depth.update({
      "source_market_update_timestamp_status":"VALID",
      "source_response_timestamp_status":"VALID",
      "source_market_update_at_utc":"2026-10-20T00:00:00.100Z",
      "source_response_at_utc":"2026-10-20T00:00:00.250Z",
      "captured_at_utc":"2026-10-20T00:00:00.300Z",
    })
    return {"schema_version":"public-market-capture-batch-v1","overall_status":"PASS",
      "created_at_utc":"2026-10-20T00:00:00Z",
      "universe":[{"pionex_symbol":market,"binance_symbol":"BTCUSDT","base_asset":"BTC","quote_asset":"USDT"}],
      "records":[
        rec(market,"pionex",{"result":True,"data":{"symbols":[{"symbol":market,"type":"SPOT","baseCurrency":"BTC","quoteCurrency":"USDT","enable":True}]}}),
        rec(market,"binance_exchange_info",{"symbols":[{"symbol":"BTCUSDT","status":"TRADING","isSpotTradingAllowed":True,"baseAsset":"BTC","quoteAsset":"USDT"}]}),
        rec(market,"binance_depth",{"bids":[["99.99","10"],["99.98","10"]],"asks":[["100.01","10"],["100.02","10"]],"lastUpdateId":123}),
        pionex_depth]}

class BatchEvaluatorTests(unittest.TestCase):
    def test_integrity_market_states_and_spread(self):
        out=evaluate_batch(fixture()); m=out["markets"][0]
        self.assertEqual(m["dimension_status"]["pionex_spot_availability"],"PASS")
        self.assertEqual(m["dimension_status"]["binance_spot_market"],"PASS")
        self.assertAlmostEqual(m["metrics"]["spread_bps"],2.0,places=5)
        self.assertEqual(m["dimension_status"]["pionex_depth_timestamp_evidence"],"PASS")
        self.assertAlmostEqual(m["metrics"]["pionex_response_minus_book_update_ms"],150.0)
        self.assertAlmostEqual(m["metrics"]["pionex_capture_minus_book_update_ms"],200.0)
        self.assertAlmostEqual(m["metrics"]["pionex_capture_minus_response_ms"],50.0)
        self.assertEqual(m["metrics"]["pionex_depth_bid_levels"],1)
        self.assertEqual(out["decision_status"],"INDETERMINATE")
        self.assertFalse(out["orders_submitted"]); self.assertFalse(out["network_requests_made"])
    def test_configured_depth_and_slippage(self):
        cfg={"max_spread_bps":5,"depth_band_bps":10,"min_depth_quote":100,"order_size_base":0.1,"max_slippage_bps":10}
        out=evaluate_batch(fixture(),cfg); m=out["markets"][0]
        self.assertIn("min_side_depth_quote",m["metrics"]); self.assertIn("buy_execution",m["metrics"])
        self.assertEqual(m["dimension_status"]["depth"],"PASS"); self.assertEqual(m["dimension_status"]["slippage"],"PASS")
        self.assertFalse(out["config_approved"])
    def test_missing_pionex_depth_timing_remains_indeterminate(self):
        a=fixture()
        a["records"]=[r for r in a["records"] if r["provider"] != "pionex_depth"]
        m=evaluate_batch(a)["markets"][0]
        self.assertEqual(m["dimension_status"]["pionex_depth_timestamp_evidence"],"INDETERMINATE")
        self.assertEqual(m["dimension_status"]["source_freshness"],"INDETERMINATE")

    def test_pionex_response_before_book_update_is_indeterminate(self):
        a=fixture()
        record=next(r for r in a["records"] if r["provider"]=="pionex_depth")
        record["source_response_at_utc"]="2026-10-20T00:00:00.050Z"
        m=evaluate_batch(a)["markets"][0]
        self.assertEqual(m["dimension_status"]["pionex_depth_timestamp_evidence"],"INDETERMINATE")
        self.assertLess(m["metrics"]["pionex_response_minus_book_update_ms"],0)

    def test_tampered_hash_rejected(self):
        a=fixture(); a["records"][0]["response_sha256"]="0"*64
        with self.assertRaises(ValueError): evaluate_batch(a)

    def test_binance_asset_identity_mismatch_fails_closed(self):
        a=fixture()
        payload=a["records"][1]["parsed_json"]
        payload["symbols"][0]["baseAsset"]="ETH"
        a["records"][1]=rec("BTC_USDT","binance_exchange_info",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["binance_spot_market"],"FAIL")
        self.assertTrue(any("baseAsset/quoteAsset" in reason for reason in market["reasons"]))

    def test_duplicate_book_price_level_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "99.99", "10" ], [ "99.99", "7" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("duplicate price" in reason for reason in market["reasons"]))

    def test_unsorted_book_is_not_silently_normalized(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "99.98", "10" ], [ "99.99", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("not ordered" in reason for reason in market["reasons"]))

    def test_crossed_book_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "100.02", "10" ], [ "99.99", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("crossed" in reason for reason in market["reasons"]))
    def test_invalid_book_marks_all_book_metrics_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "100.02", "10" ], [ "99.99", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a,{"depth_band_bps":10,"min_depth_quote":100,"order_size_base":0.1,"max_slippage_bps":10})["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["depth"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["slippage"],"INDETERMINATE")

    def test_locked_book_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "100.0", "10" ], [ "99.99", "10" ]]
        payload["asks"]=[[ "100.0", "10" ], [ "100.01", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertNotIn("spread_bps",market["metrics"])
        self.assertTrue(any("book is locked" in reason for reason in market["reasons"]))

    def test_empty_book_side_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["asks"]=[]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("side is empty" in reason for reason in market["reasons"]))

    def test_malformed_book_level_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["asks"]=[[ "100.01" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("malformed book level" in reason for reason in market["reasons"]))

    def test_unsorted_asks_are_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["asks"]=[[ "100.02", "10" ], [ "100.01", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("asks side is not ordered" in reason for reason in market["reasons"]))

    def test_invalid_nonfinite_book_level_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["bids"]=[[ "nan", "10" ], [ "99.98", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("invalid book level" in reason for reason in market["reasons"]))

    def test_invalid_book_quantity_is_indeterminate(self):
        a=fixture()
        payload=a["records"][2]["parsed_json"]
        payload["asks"]=[[ "100.01", "0" ], [ "100.02", "10" ]]
        a["records"][2]=rec("BTC_USDT","binance_depth",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["spread"],"INDETERMINATE")
        self.assertTrue(any("invalid book level" in reason for reason in market["reasons"]))

    def test_pionex_quote_identity_mismatch_fails_closed(self):
        a=fixture()
        payload=a["records"][0]["parsed_json"]
        payload["data"]["symbols"][0]["quoteCurrency"]="BTC"
        a["records"][0]=rec("BTC_USDT","pionex",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["pionex_spot_availability"],"FAIL")
        self.assertTrue(any("baseCurrency/quoteCurrency" in reason for reason in market["reasons"]))

    def test_binance_quote_identity_mismatch_fails_closed(self):
        a=fixture()
        payload=a["records"][1]["parsed_json"]
        payload["symbols"][0]["quoteAsset"]="BTC"
        a["records"][1]=rec("BTC_USDT","binance_exchange_info",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["binance_spot_market"],"FAIL")
        self.assertTrue(any("baseAsset/quoteAsset" in reason for reason in market["reasons"]))

    def test_duplicate_pionex_symbols_are_indeterminate(self):
        a=fixture()
        payload=a["records"][0]["parsed_json"]
        payload["data"]["symbols"].append(dict(payload["data"]["symbols"][0]))
        a["records"][0]=rec("BTC_USDT","pionex",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["pionex_spot_availability"],"INDETERMINATE")
        self.assertTrue(any("exactly one matching symbol" in reason for reason in market["reasons"]))

    def test_duplicate_binance_symbols_are_indeterminate(self):
        a=fixture()
        payload=a["records"][1]["parsed_json"]
        payload["symbols"].append(dict(payload["symbols"][0]))
        a["records"][1]=rec("BTC_USDT","binance_exchange_info",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["binance_spot_market"],"INDETERMINATE")
        self.assertTrue(any("exactly one matching symbol" in reason for reason in market["reasons"]))

    def test_pionex_missing_identity_field_is_indeterminate(self):
        for field in ("baseCurrency", "quoteCurrency", "type", "enable"):
            with self.subTest(field=field):
                a=fixture()
                payload=a["records"][0]["parsed_json"]
                payload["data"]["symbols"][0].pop(field)
                a["records"][0]=rec("BTC_USDT","pionex",payload)
                market=evaluate_batch(a)["markets"][0]
                self.assertEqual(market["dimension_status"]["pionex_spot_availability"],"INDETERMINATE")
                self.assertTrue(any("missing or invalid" in reason for reason in market["reasons"]))

    def test_pionex_wrong_base_asset_fails_closed(self):
        a=fixture()
        payload=a["records"][0]["parsed_json"]
        payload["data"]["symbols"][0]["baseCurrency"]="ETH"
        a["records"][0]=rec("BTC_USDT","pionex",payload)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["pionex_spot_availability"],"FAIL")
        self.assertTrue(any("baseCurrency/quoteCurrency" in reason for reason in market["reasons"]))

    def test_pionex_non_spot_and_disabled_markets_fail(self):
        for field, value in (("type","MARGIN"),("enable",False)):
            with self.subTest(field=field):
                a=fixture()
                payload=a["records"][0]["parsed_json"]
                payload["data"]["symbols"][0][field]=value
                a["records"][0]=rec("BTC_USDT","pionex",payload)
                market=evaluate_batch(a)["markets"][0]
                self.assertEqual(market["dimension_status"]["pionex_spot_availability"],"FAIL")

    def test_binance_missing_identity_field_is_indeterminate(self):
        for field in ("baseAsset", "quoteAsset", "status", "isSpotTradingAllowed"):
            with self.subTest(field=field):
                a=fixture()
                payload=a["records"][1]["parsed_json"]
                payload["symbols"][0].pop(field)
                a["records"][1]=rec("BTC_USDT","binance_exchange_info",payload)
                market=evaluate_batch(a)["markets"][0]
                self.assertEqual(market["dimension_status"]["binance_spot_market"],"INDETERMINATE")
                self.assertTrue(any("missing or invalid" in reason for reason in market["reasons"]))

    def test_binance_non_trading_or_spot_disabled_fails(self):
        for field, value in (("status","BREAK"),("isSpotTradingAllowed",False)):
            with self.subTest(field=field):
                a=fixture()
                payload=a["records"][1]["parsed_json"]
                payload["symbols"][0][field]=value
                a["records"][1]=rec("BTC_USDT","binance_exchange_info",payload)
                market=evaluate_batch(a)["markets"][0]
                self.assertEqual(market["dimension_status"]["binance_spot_market"],"FAIL")

    def test_missing_timestamps_and_unknown_fees_remain_indeterminate(self):
        a=fixture()
        for record in a["records"]:
            record.pop("captured_at_utc", None)
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["fees"],"INDETERMINATE")

    def test_stale_timestamps_and_obsolete_fee_metadata_do_not_pass(self):
        a=fixture()
        for record in a["records"]:
            record["captured_at_utc"]="2020-01-01T00:00:00Z"
            record["fee_metadata"]={"source":"fixture","observed_at_utc":"2020-01-01T00:00:00Z","maker":0,"taker":0}
        market=evaluate_batch(a)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["fees"],"INDETERMINATE")

    def test_insufficient_book_depth_keeps_slippage_indeterminate(self):
        a=fixture()
        cfg={"order_size_base":1000,"max_slippage_bps":10}
        market=evaluate_batch(a,cfg)["markets"][0]
        self.assertEqual(market["dimension_status"]["slippage"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["fees"],"INDETERMINATE")
        self.assertEqual(market["dimension_status"]["source_freshness"],"INDETERMINATE")

    def test_boolean_book_values_are_indeterminate(self):
        cases = (
            ("bids", [["99.99", "10"], [True, "10"]]),
            ("asks", [["100.01", "10"], ["100.02", True]]),
        )
        for side, levels in cases:
            with self.subTest(side=side):
                a = fixture()
                payload = a["records"][2]["parsed_json"]
                payload[side] = levels
                a["records"][2] = rec("BTC_USDT", "binance_depth", payload)
                market = evaluate_batch(a)["markets"][0]
                self.assertEqual(market["dimension_status"]["spread"], "INDETERMINATE")
                self.assertEqual(market["dimension_status"]["depth"], "INDETERMINATE")
                self.assertEqual(market["dimension_status"]["slippage"], "INDETERMINATE")
                self.assertTrue(any("invalid book level" in reason for reason in market["reasons"]))

    def test_duplicate_provider_record_rejected(self):
        a=fixture(); a["records"].append(a["records"][0])
        with self.assertRaises(ValueError): evaluate_batch(a)
    def test_duplicate_market_identity_in_universe_rejected(self):
        a=fixture()
        a["universe"].append(dict(a["universe"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate market_id"):
            evaluate_batch(a)

    def test_duplicate_binance_symbol_across_universe_rejected(self):
        a=fixture()
        a["universe"].append({"pionex_symbol":"ETH_USDT","binance_symbol":"BTCUSDT","base_asset":"ETH","quote_asset":"USDT"})
        with self.assertRaisesRegex(ValueError, "duplicate Binance symbol"):
            evaluate_batch(a)

    def test_wrong_schema_rejected(self):
        a=fixture(); a["schema_version"]="public-market-capture-v1"
        with self.assertRaises(ValueError): evaluate_batch(a)
    def test_missing_source_event_timestamp_keeps_freshness_indeterminate(self):
        artifact = fixture()
        # The captured Binance depth response exposes lastUpdateId, not a verified
        # market-event timestamp. Capture time must not be used as a substitute.
        for record in artifact["records"]:
            self.assertIsNone(record.get("source_event_at_utc"))
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "INDETERMINATE")
        self.assertTrue(any("capture time is not a substitute" in reason for reason in market["reasons"]))

    def test_missing_account_applicable_fee_evidence_keeps_fees_indeterminate(self):
        artifact = fixture()
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["fees"], "INDETERMINATE")
        self.assertTrue(any("no verified account-applicable official fee schedule" in reason for reason in market["reasons"]))
        self.assertEqual(evaluate_batch(artifact)["decision_status"], "INDETERMINATE")


    def test_future_source_timestamp_never_passes_without_approved_policy(self):
        artifact = fixture()
        for record in artifact["records"]:
            record["captured_at_utc"] = "2026-10-21T00:00:00Z"
            record["source_event_at_utc"] = "2026-10-21T00:00:01Z"
            record["source_timestamp_field"] = "eventTime"
            record["source_timestamp_semantics"] = "provider event time"
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "INDETERMINATE")
        self.assertEqual(market["decision_status"], "INDETERMINATE")

    def test_malformed_source_timestamp_never_passes(self):
        artifact = fixture()
        for record in artifact["records"]:
            record["captured_at_utc"] = "2026-10-21T00:00:00Z"
            record["source_event_at_utc"] = "not-a-timestamp"
            record["source_timestamp_field"] = "eventTime"
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["source_freshness"], "INDETERMINATE")
        self.assertEqual(market["decision_status"], "INDETERMINATE")

    def test_zero_fee_fixture_without_account_evidence_never_passes(self):
        artifact = fixture()
        for record in artifact["records"]:
            record["fee_metadata"] = {
                "source": "unverified fixture",
                "observed_at_utc": "2026-10-21T00:00:00Z",
                "maker": 0,
                "taker": 0,
            }
        market = evaluate_batch(artifact)["markets"][0]
        self.assertEqual(market["dimension_status"]["fees"], "INDETERMINATE")
        self.assertEqual(market["decision_status"], "INDETERMINATE")

if __name__=="__main__": unittest.main()
