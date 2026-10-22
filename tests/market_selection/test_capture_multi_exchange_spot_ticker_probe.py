import unittest
from scripts.market_selection.capture_multi_exchange_spot_ticker_probe import build_requests, extract_quote_volume

class QuoteVolumeProbeTests(unittest.TestCase):
    def test_covers_seven_venues_and_three_spot_assets(self):
        requests=build_requests()
        self.assertEqual(len(requests),21)
        self.assertEqual({x['exchange'] for x in requests},{'binance','okx','bybit','mexc','gate','bitget','pionex'})
        self.assertEqual({x['asset'] for x in requests},{'BTC','ETH','SOL'})
        self.assertTrue(all(x['quote_currency']=='USDT' for x in requests))
    def test_binance_quote_volume_is_not_base_volume(self):
        value,ts,sem=extract_quote_volume('binance',{'symbol':'BTCUSDT','quoteVolume':'123.45','closeTime':99},'BTCUSDT')
        self.assertEqual(value,'123.45'); self.assertEqual(ts,99); self.assertIn('quote-asset',sem)
    def test_okx_uses_quote_currency_volume(self):
        value,ts,sem=extract_quote_volume('okx',{'code':'0','data':[{'instId':'BTC-USDT','vol24h':'2','volCcy24h':'100','ts':'9'}]},'BTC-USDT')
        self.assertEqual(value,'100'); self.assertEqual(ts,'9'); self.assertIn('quote-currency',sem)
    def test_bybit_uses_turnover_not_base_volume(self):
        value,ts,sem=extract_quote_volume('bybit',{'retCode':0,'time':8,'result':{'list':[{'symbol':'BTCUSDT','volume24h':'2','turnover24h':'200'}]}},'BTCUSDT')
        self.assertEqual(value,'200'); self.assertEqual(ts,8); self.assertIn('turnover24h',sem)
    def test_mexc_missing_quote_volume_is_preserved(self):
        value,ts,sem=extract_quote_volume('mexc',{'symbol':'BTCUSDT','quoteVolume':None,'closeTime':5},'BTCUSDT')
        self.assertIsNone(value); self.assertEqual(ts,5)
    def test_gate_uses_quote_volume(self):
        value,ts,sem=extract_quote_volume('gate',[{'currency_pair':'BTC_USDT','quote_volume':'50','time':'7'}],'BTC_USDT')
        self.assertEqual(value,'50'); self.assertEqual(ts,'7')
    def test_bitget_checks_success_code(self):
        value,ts,sem=extract_quote_volume('bitget',{'code':'00000','data':[{'symbol':'BTCUSDT','turnover24h':'30','ts':'6'}]},'BTCUSDT')
        self.assertEqual(value,'30'); self.assertEqual(ts,'6')
        with self.assertRaises(ValueError): extract_quote_volume('bitget',{'code':'40001','data':[]},'BTCUSDT')
    def test_pionex_uses_amount_and_ticker_time(self):
        value,ts,sem=extract_quote_volume('pionex',{'result':True,'timestamp':5,'data':{'tickers':[{'symbol':'BTC_USDT','amount':'70','time':4}]}},'BTC_USDT')
        self.assertEqual(value,'70'); self.assertEqual(ts,4)

    def test_rejects_ticker_for_wrong_market(self):
        with self.assertRaisesRegex(ValueError, "expected exactly one ticker"):
            extract_quote_volume('binance', {'symbol':'ETHUSDT','quoteVolume':'999','closeTime':1}, 'BTCUSDT')

    def test_rejects_duplicate_matching_tickers(self):
        payload = {'code':'0','data':[
            {'instId':'BTC-USDT','volCcy24h':'10','ts':'1'},
            {'instId':'BTC-USDT','volCcy24h':'20','ts':'2'},
        ]}
        with self.assertRaisesRegex(ValueError, "found 2"):
            extract_quote_volume('okx', payload, 'BTC-USDT')

    def test_rejects_missing_native_symbol(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            extract_quote_volume('gate', [{'quote_volume':'50','time':'7'}], 'BTC_USDT')

if __name__=='__main__': unittest.main()
