import base64
import hashlib
import json
import unittest
from urllib.parse import parse_qs, urlparse

from scripts.market_selection.capture_pionex_spot_ohlcv import (
    BASE_URL, build_url, capture_history, normalize_kline, read_complete,
)


def make_page(rows, *, status=200, payload=None, captured_at="2026-10-22T16:00:00.000Z"):
    if payload is None:
        payload = {"result": True, "data": {"klines": rows}, "timestamp": 1792684800000}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    success = status == 200 and isinstance(payload, dict) and payload.get("result") is True
    return {
        "url": BASE_URL, "request_started_at_utc": "2026-10-22T15:59:59.000Z",
        "captured_at_utc": captured_at, "http_status": status,
        "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_base64": base64.b64encode(raw).decode("ascii"), "parsed_json": payload,
        "capture_status": "PASS" if success else "FAIL", "normalization_status": "NOT_RUN",
        "normalization_error": None, "error_type": None, "error_message": None,
    }


def kline(time_ms, open_price="10", high="12", low="9", close="11", volume="4.5"):
    return {"time": time_ms, "open": open_price, "high": high, "low": low, "close": close, "volume": volume}


class FakeResponse:
    def __init__(self, body):
        self.body = body
        self.offset = 0

    def read(self, size):
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class PionexOhlcvCaptureTests(unittest.TestCase):
    def test_build_url_uses_documented_limit_and_end_time_without_start_time(self):
        query = parse_qs(urlparse(build_url("BTC_USDT", "1M", 239999)).query)
        self.assertEqual(query["symbol"], ["BTC_USDT"])
        self.assertEqual(query["interval"], ["1M"])
        self.assertEqual(query["limit"], ["500"])
        self.assertEqual(query["endTime"], ["239999"])
        self.assertNotIn("startTime", query)

    def test_backward_pagination_continues_until_empty_page(self):
        pages = [
            make_page([kline(240000), kline(300000)]),
            make_page([kline(120000), kline(180000)]),
            make_page([]),
        ]
        urls = []

        def fetch(url):
            urls.append(url)
            return pages.pop(0)

        out = capture_history("BTC_USDT", "1M", page_fetcher=fetch)
        self.assertEqual(out["overall_status"], "PASS")
        self.assertEqual(out["coverage"]["stop_reason"], "NO_MORE_RECORDS")
        self.assertEqual(out["coverage"]["pages_captured"], 3)
        self.assertEqual(out["coverage"]["captured_candle_rows"], 4)
        self.assertEqual(out["coverage"]["unique_source_timestamps"], 4)
        self.assertEqual(out["coverage"]["duplicate_source_time_ms"], [])
        self.assertEqual(parse_qs(urlparse(urls[1]).query)["endTime"], ["239999"])
        self.assertEqual(parse_qs(urlparse(urls[2]).query)["endTime"], ["119999"])
        self.assertTrue(all(c["volume_unit_status"] == "INDETERMINATE" for c in out["candles"]))
        self.assertTrue(all("base_volume" not in c and "quote_volume" not in c for c in out["candles"]))
        self.assertTrue(all(c["timestamp_role_status"].startswith("INDETERMINATE") for c in out["candles"]))

    def test_provider_history_limit_is_preserved_as_partial(self):
        error = make_page([], status=400, payload={"result": False, "code": "MARKET_INVALID_TIME", "message": "history limit"})
        out = capture_history("BTC_USDT", "1D", page_fetcher=lambda _: error)
        self.assertEqual(out["overall_status"], "PARTIAL")
        self.assertEqual(out["coverage"]["stop_reason"], "PROVIDER_HISTORY_LIMIT_REACHED")
        self.assertTrue(out["coverage"]["provider_history_limit_reached"])
        self.assertEqual(out["pages"][0]["response_sha256"], error["response_sha256"])
        self.assertIsNotNone(out["pages"][0]["response_base64"])

    def test_duplicate_timestamps_across_pages_are_preserved_and_flagged(self):
        pages = [
            make_page([kline(240000), kline(300000)]),
            make_page([kline(180000), kline(240000)]),
            make_page([]),
        ]
        out = capture_history("BTC_USDT", "1M", page_fetcher=lambda _: pages.pop(0))
        self.assertEqual(out["overall_status"], "PARTIAL")
        self.assertEqual(out["coverage"]["duplicate_source_time_ms"], [240000])
        self.assertEqual(out["coverage"]["captured_candle_rows"], 4)
        self.assertEqual(out["coverage"]["unique_source_timestamps"], 3)

    def test_pagination_no_progress_does_not_loop_forever(self):
        pages = [make_page([kline(240000), kline(300000)]), make_page([kline(240000), kline(300000)])]
        out = capture_history("BTC_USDT", "1M", page_fetcher=lambda _: pages.pop(0))
        self.assertEqual(out["overall_status"], "PARTIAL")
        self.assertEqual(out["coverage"]["stop_reason"], "PAGINATION_NO_PROGRESS")
        self.assertEqual(out["coverage"]["pagination_progress_status"], "FAIL")

    def test_normalizer_does_not_invent_volume_or_timestamp_semantics(self):
        candle = normalize_kline(kline(60000), "BTC_USDT", "1M", "2026-10-22T16:00:00Z", 0)
        self.assertEqual(candle["source_time_ms"], 60000)
        self.assertEqual(candle["volume_raw"], "4.5")
        self.assertEqual(candle["volume_unit_status"], "INDETERMINATE")
        self.assertIn("INDETERMINATE", candle["timestamp_role_status"])
        self.assertNotIn("base_volume", candle)
        self.assertNotIn("quote_volume", candle)

    def test_invalid_ohlc_envelope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "high is below"):
            normalize_kline(kline(60000, open_price="10", high="10", low="9", close="11"),
                            "BTC_USDT", "1M", "2026-10-22T16:00:00Z", 0)

    def test_reads_response_larger_than_five_mib_to_eof(self):
        body = b"x" * (5 * 1024 * 1024 + 137)
        self.assertEqual(read_complete(FakeResponse(body)), body)

    def test_unsupported_interval_is_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "unsupported Pionex interval"):
            capture_history("BTC_USDT", "1m", page_fetcher=lambda _: self.fail("network must not be called"))


if __name__ == "__main__":
    unittest.main()
