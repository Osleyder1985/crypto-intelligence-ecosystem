import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.market_selection.analyze_spot_market_pareto import analyze_files


def raw_record(exchange, asset, symbol, payload, **fields):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return {
        "exchange": exchange, "asset": asset, "symbol": symbol,
        "capture_status": "PASS", "http_status": 200,
        "captured_at_utc": "2026-10-22T15:57:45.000Z", "source_timestamp_raw": 1792684670000,
        "response_base64": base64.b64encode(raw).decode(),
        "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw),
        "parsed_json": payload, **fields,
    }


def levels(bid, ask, qty):
    return ([[str(bid - i / 100), str(qty)] for i in range(10)],
            [[str(ask + i / 100), str(qty)] for i in range(10)])


def fixtures():
    quote_records, book_records = [], []
    specs = [
        ("binance", "BTCUSDT", "1000", "VALID", "DOCUMENTED", 99.99, 100.01, 10),
        ("okx", "BTC-USDT", "900", "VALID", "DOCUMENTED", 99.95, 100.05, 1),
        ("pionex", "BTC_USDT", "2000", "INDETERMINATE", "INDETERMINATE", 99.98, 100.02, 5),
    ]
    for exchange, symbol, turnover, status, unit_status, bid, ask, qty in specs:
        quote_payload = {"symbol": symbol, "quoteVolume": turnover, "amount": turnover}
        quote_records.append(raw_record(
            exchange, "BTC", symbol, quote_payload, quote_currency="USDT",
            quote_volume_raw=turnover, quote_volume_decimal=turnover if status == "VALID" else None,
            quote_volume_unit="USDT" if unit_status == "DOCUMENTED" else None,
            quote_volume_status=status, quote_volume_unit_status=unit_status,
        ))
        bids, asks = levels(bid, ask, qty)
        if exchange == "okx":
            book_payload = {"code": "0", "data": [{"bids": bids, "asks": asks, "ts": "1792684670000"}]}
        elif exchange == "pionex":
            book_payload = {"result": True, "data": {"bids": bids, "asks": asks, "updateTime": 1792684670000}}
        else:
            book_payload = {"bids": bids, "asks": asks, "lastUpdateId": 123}
        book_records.append(raw_record(exchange, "BTC", symbol, book_payload))
    failed = {"error": "access denied"}
    raw = json.dumps(failed, separators=(",", ":")).encode()
    failure = {
        "exchange": "bybit", "asset": "BTC", "symbol": "BTCUSDT",
        "capture_status": "FAIL", "http_status": 403, "captured_at_utc": "2026-10-22T15:57:46.000Z",
        "source_timestamp_raw": None, "response_base64": base64.b64encode(raw).decode(),
        "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw), "parsed_json": None,
    }
    quote_records.append({**failure, "quote_currency": "USDT", "quote_volume_status": "INDETERMINATE",
                          "quote_volume_unit_status": "DOCUMENTED", "quote_volume_unit": "USDT",
                          "quote_volume_decimal": None})
    book_records.append({**failure, "captured_at_utc": "2026-10-22T15:57:46.100Z"})
    return (
        {"schema_version": "multi-exchange-spot-quote-volume-v1", "created_at_utc": "2026-10-22T15:57:46.000Z",
         "overall_status": "PARTIAL", "expected_record_count": 4, "actual_record_count": 4, "records": quote_records},
        {"schema_version": "multi-exchange-spot-book-probe-v1", "created_at_utc": "2026-10-22T15:57:47.000Z",
         "overall_status": "PARTIAL", "expected_record_count": 4, "actual_record_count": 4, "records": book_records},
    )


class ExploratoryParetoTests(unittest.TestCase):
    def _run(self, quote, book):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        q, b = Path(directory.name) / "quote.json", Path(directory.name) / "book.json"
        q.write_text(json.dumps(quote), encoding="utf-8")
        b.write_text(json.dumps(book), encoding="utf-8")
        return analyze_files(q, b)

    def test_frontier_is_exploratory_and_uses_all_four_objectives(self):
        quote, book = fixtures()
        out = self._run(quote, book)
        self.assertEqual(out["decision_status"], "INDETERMINATE")
        self.assertFalse(out["orders_submitted"])
        self.assertFalse(out["recommendation_generated"])
        self.assertFalse(out["objectives"]["thresholds_applied"])
        by_id = {row["market_id"]: row for row in out["candidates"]}
        self.assertTrue(by_id["binance:BTC"]["pareto_frontier_member"])
        self.assertFalse(by_id["okx:BTC"]["pareto_frontier_member"])
        self.assertEqual(by_id["okx:BTC"]["dominated_by"], ["binance:BTC"])
        self.assertEqual(by_id["pionex:BTC"]["candidate_status"], "INDETERMINATE")
        self.assertIn("quote_volume_unit_not_documented", by_id["pionex:BTC"]["exclusion_reasons"])
        self.assertEqual(by_id["bybit:BTC"]["candidate_status"], "INDETERMINATE")
        self.assertEqual(out["frontier_by_asset"][0]["frontier_market_ids"], ["binance:BTC"])

    def test_tampered_response_hash_fails_closed(self):
        quote, book = fixtures()
        quote["records"][0]["response_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            self._run(quote, book)

    def test_symbol_mismatch_is_not_compared(self):
        quote, book = fixtures()
        book["records"][0]["symbol"] = "OTHERUSDT"
        out = self._run(quote, book)
        by_id = {row["market_id"]: row for row in out["candidates"]}
        self.assertEqual(by_id["binance:BTC"]["candidate_status"], "INDETERMINATE")
        self.assertIn("native_symbol_mismatch_between_artifacts", by_id["binance:BTC"]["exclusion_reasons"])

    def test_fewer_than_ten_levels_is_indeterminate(self):
        quote, book = fixtures()
        payload = book["records"][0]["parsed_json"]
        payload["bids"] = payload["bids"][:9]
        raw = json.dumps(payload, separators=(",", ":")).encode()
        record = book["records"][0]
        record["response_base64"] = base64.b64encode(raw).decode()
        record["response_sha256"] = hashlib.sha256(raw).hexdigest()
        record["response_bytes"] = len(raw)
        out = self._run(quote, book)
        by_id = {row["market_id"]: row for row in out["candidates"]}
        self.assertEqual(by_id["binance:BTC"]["candidate_status"], "INDETERMINATE")
        self.assertTrue(any("fewer_than_10_levels" in reason for reason in by_id["binance:BTC"]["exclusion_reasons"]))


if __name__ == "__main__":
    unittest.main()
