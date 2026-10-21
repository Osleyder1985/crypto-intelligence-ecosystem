import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from scripts.market_selection.capture_binance_regional_rest_diagnostic import (
    ASSETS, VENUES, capture_endpoint, capture_venue, request_json,
)


class BinanceRegionalRestDiagnosticTests(unittest.TestCase):
    def test_uses_only_official_distinct_hosts(self):
        self.assertEqual(len(VENUES), 2)
        self.assertEqual(VENUES[0]["base_url"], "https://data-api.binance.vision")
        self.assertEqual(VENUES[1]["base_url"], "https://api.binance.us")
        self.assertEqual(ASSETS, ("BTC", "ETH", "SOL"))

    def test_http_451_is_recorded_with_status_and_body(self):
        url = "https://data-api.binance.vision/api/v3/time"
        error = HTTPError(url, 451, "restricted", {}, BytesIO(b'{"code":-1,"msg":"restricted location"}'))
        venue = VENUES[0]
        with patch("scripts.market_selection.capture_binance_regional_rest_diagnostic.urlopen", side_effect=error):
            record = capture_endpoint(venue, "server_time", url)
        self.assertEqual(record["capture_status"], "FAIL")
        self.assertEqual(record["http_status"], 451)
        self.assertIn("restricted location", record["error_message"])
        self.assertIsNotNone(record["response_sha256"])

    def test_server_time_schema(self):
        response = {"serverTime": 123456789}
        fake = {"http_status": 200, "raw": b'{"serverTime":123456789}', "payload": response}
        with patch("scripts.market_selection.capture_binance_regional_rest_diagnostic.request_json", return_value=fake):
            record = capture_endpoint(VENUES[0], "server_time", "https://example.invalid/api/v3/time")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["parsed_summary"]["server_time_ms"], 123456789)

    def test_exchange_info_selects_existing_symbol(self):
        payload = {"symbols": [
            {"symbol": "BTCUSD", "baseAsset": "BTC", "quoteAsset": "USD", "status": "TRADING"},
            {"symbol": "ETHUSDT", "baseAsset": "ETH", "quoteAsset": "USDT", "status": "TRADING"},
        ]}
        fake = {"http_status": 200, "raw": b'{}', "payload": payload}
        with patch("scripts.market_selection.capture_binance_regional_rest_diagnostic.request_json", return_value=fake):
            record = capture_endpoint(VENUES[1], "exchange_info", "https://example.invalid/api/v3/exchangeInfo")
        pairs = record["parsed_summary"]["available_asset_pairs"]
        self.assertEqual(pairs["BTC"], "BTCUSD")
        self.assertEqual(pairs["ETH"], "ETHUSDT")
        self.assertIsNone(pairs["SOL"])

    def test_book_parser_captures_top_of_book_and_sequence(self):
        payload = {"lastUpdateId": 77, "bids": [["100", "2"]], "asks": [["101", "3"]]}
        fake = {"http_status": 200, "raw": b'{}', "payload": payload}
        with patch("scripts.market_selection.capture_binance_regional_rest_diagnostic.request_json", return_value=fake):
            record = capture_endpoint(VENUES[0], "order_book", "https://example.invalid/api/v3/depth?symbol=BTCUSDT&limit=20", "BTCUSDT")
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["parsed_summary"]["best_bid"], "100")
        self.assertEqual(record["parsed_summary"]["best_ask"], "101")
        self.assertEqual(record["parsed_summary"]["last_update_id"], 77)

    def test_missing_market_is_not_reported_as_pass(self):
        info = {"capture_status": "PASS", "parsed_summary": {"available_asset_pairs": {"BTC": "BTCUSDT", "ETH": None, "SOL": None}}}
        with patch("scripts.market_selection.capture_binance_regional_rest_diagnostic.capture_endpoint", side_effect=[
            {"capture_status": "PASS"}, info,
            {"kind": "order_book", "capture_status": "PASS", "parsed_summary": {"best_bid": "1", "best_ask": "2"}},
            {"capture_status": "NOT_AVAILABLE"}, {"capture_status": "NOT_AVAILABLE"},
        ]) as mocked:
            records = capture_venue(VENUES[0])
        books = [r for r in records if r.get("kind") == "order_book"]
        self.assertEqual(len(books), 3)
        self.assertEqual(books[0]["capture_status"], "PASS")
        self.assertEqual(books[1]["capture_status"], "NOT_AVAILABLE")
        self.assertEqual(mocked.call_count, 5)


if __name__ == "__main__":
    unittest.main()
