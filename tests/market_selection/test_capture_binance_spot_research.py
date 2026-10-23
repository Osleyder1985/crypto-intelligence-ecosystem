import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_binance_spot_research import (
    EXCHANGE_INFO_URL,
    capture_exchange_info,
    capture_and_build_report,
)


class FakeResponse:
    def __init__(self, raw, status=200, chunk_size=7):
        self.raw = raw
        self.status = status
        self.position = 0
        self.chunk_size = chunk_size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        if self.position >= len(self.raw):
            return b""
        # Simulate short network reads; callers must continue to EOF.
        end = min(self.position + min(size, self.chunk_size), len(self.raw))
        chunk = self.raw[self.position:end]
        self.position = end
        return chunk


def exchange_info_payload(symbol="BTCUSDT", base="BTC", quote="USDT", status="TRADING", spot=True):
    return {"symbols": [{
        "symbol": symbol, "baseAsset": base, "quoteAsset": quote,
        "status": status, "isSpotTradingAllowed": spot,
        "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": [], "permissions": ["SPOT"],
    }]}


class BinanceSpotResearchCaptureTests(unittest.TestCase):

    def test_internal_analysis_is_blocked_before_metadata_network_request(self):
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen") as network:
            with self.assertRaisesRegex(PermissionError, "blocked before exchangeInfo request"):
                capture_exchange_info("BTCUSDT", use_case="internal_analysis")
        network.assert_not_called()

    def test_pipeline_blocks_before_any_network_or_candle_capture_without_authorization(self):
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen") as network, patch(
            "scripts.market_selection.capture_binance_spot_research.capture_history"
        ) as candles:
            with self.assertRaises(PermissionError):
                capture_and_build_report(
                    symbol="BTCUSDT", interval="1h", start_time_ms=0,
                    end_time_ms_exclusive=3_600_000, config={}, base_asset_ticker="BTC",
                    use_case="internal_analysis",
                )
        network.assert_not_called()
        candles.assert_not_called()

    def test_preserves_complete_exchange_info_universe_without_local_size_cap(self):
        payload = exchange_info_payload()
        payload["symbols"].append({
            "symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC",
            "status": "TRADING", "isSpotTradingAllowed": True,
            "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": [],
        })
        raw = json.dumps(payload).encode("utf-8")
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)) as network:
            out = capture_exchange_info("BTCUSDT", use_case="live_technical_test")
        evidence = out["captured_exchange_info"]
        self.assertEqual(out["base_asset"], "BTC")
        self.assertEqual(out["quote_asset"], "USDT")
        self.assertEqual(evidence["response_bytes"], len(raw))
        self.assertEqual(evidence["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(base64.b64decode(evidence["response_base64"]), raw)
        self.assertEqual(evidence["url"], EXCHANGE_INFO_URL)
        self.assertEqual(json.loads(base64.b64decode(evidence["response_base64"]))["symbols"], payload["symbols"])
        self.assertNotIn("symbol=", network.call_args.args[0].full_url)

    def test_ticker_resolves_only_when_quote_market_is_unique(self):
        payload = exchange_info_payload()
        payload["symbols"].append({
            "symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC",
            "status": "TRADING", "isSpotTradingAllowed": True,
            "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": [],
        })
        raw = json.dumps(payload).encode("utf-8")
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)):
            selected = capture_exchange_info(
                None, base_asset_ticker="BTC", quote_asset="USDT", use_case="live_technical_test"
            )
        self.assertEqual(selected["symbol_native"], "BTCUSDT")
        self.assertEqual(selected["base_asset"], "BTC")
        self.assertEqual(selected["market_resolution"]["resolution_status"], "UNIQUE_MARKET")

    def test_ticker_without_quote_fails_closed_when_multiple_pairs_match(self):
        payload = exchange_info_payload()
        payload["symbols"].append({
            "symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC",
            "status": "TRADING", "isSpotTradingAllowed": True,
            "baseAssetPrecision": 8, "quoteAssetPrecision": 8, "filters": [],
        })
        raw = json.dumps(payload).encode("utf-8")
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)):
            with self.assertRaisesRegex(ValueError, "AMBIGUOUS_MARKET"):
                capture_exchange_info(None, base_asset_ticker="BTC", use_case="live_technical_test")

    def test_fails_closed_when_symbol_not_found(self):
        raw = json.dumps({"symbols": []}).encode()
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)):
            with self.assertRaisesRegex(ValueError, "NO_MARKET"):
                capture_exchange_info("NOPEUSDT", use_case="live_technical_test")

    def test_fails_closed_when_symbol_not_trading_or_spot_disabled(self):
        raw = json.dumps(exchange_info_payload(status="BREAK")).encode()
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)):
            with self.assertRaisesRegex(ValueError, "NO_MARKET"):
                capture_exchange_info("BTCUSDT", use_case="live_technical_test")
        raw = json.dumps(exchange_info_payload(spot=False)).encode()
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw)):
            with self.assertRaisesRegex(ValueError, "NO_MARKET"):
                capture_exchange_info("BTCUSDT", use_case="live_technical_test")

    def test_pipeline_blocks_technical_capture_before_internal_report(self):
        from scripts.market_selection.capture_binance_spot_ohlcv import SCHEMA_VERSION
        metadata_raw = json.dumps(exchange_info_payload()).encode()
        artifact = {
            "schema_version": SCHEMA_VERSION,
            "overall_status": "PASS",
            "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": "BTCUSDT", "interval": "1h"},
            "window": {"start_time_ms_inclusive": 0, "end_time_ms_exclusive": 21_600_000},
            "requested_open_candle_count": 6,
            "captured_candle_count": 6,
            "missing_open_time_ms": [],
            "unexpected_open_time_ms": [],
            "pages": [{
                "capture_status": "PASS", "normalization_status": "PASS",
                "response_bytes": 1, "response_sha256": hashlib.sha256(b"x").hexdigest(),
                "response_base64": base64.b64encode(b"x").decode(), "parsed_json": [],
            }],
            "candles": [{
                "open_time_ms": i * 3_600_000, "close_time_ms": i * 3_600_000 + 3_599_999,
                "open": str(10+i), "high": str(12+i), "low": str(9+i), "close": str(11+i),
                "base_volume": "10", "quote_volume": "1000", "trade_count": 10,
                "closed_at_capture": True, "eligible_for_closed_candle_analysis": True,
            } for i in range(6)],
        }
        config = {
            "methodology_id": "technical-descriptive-baseline", "methodology_version": "1.0.0",
            "movement": {"lookback_bars": 2, "return_threshold_pct": 5.0, "volume_ratio_threshold": 3.0},
            "support_resistance": {"pivot_left": 1, "pivot_right": 1, "tolerance_bps": 100.0},
        }
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(metadata_raw)) as network, \
             patch("scripts.market_selection.capture_binance_spot_research.capture_history", return_value=artifact) as candles:
            with self.assertRaisesRegex(PermissionError, "research report blocked before analysis"):
                capture_and_build_report(
                    symbol="BTCUSDT", interval="1h", start_time_ms=0,
                    end_time_ms_exclusive=21_600_000, config=config, base_asset_ticker="BTC", use_case="live_technical_test",
                )
        network.assert_called_once()
        candles.assert_called_once()


    def test_preserves_complete_response_larger_than_five_mib_without_truncation(self):
        # The pipeline has no project-imposed response-byte ceiling. This fixture
        # verifies complete-body preservation even when a response exceeds 5 MiB.
        payload = exchange_info_payload()
        payload["large_extension_field"] = "x" * (6 * 1024 * 1024)
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(raw, chunk_size=8191)):
            out = capture_exchange_info("BTCUSDT", use_case="live_technical_test")
        evidence = out["captured_exchange_info"]
        restored = base64.b64decode(evidence["response_base64"], validate=True)
        self.assertGreater(len(raw), 5 * 1024 * 1024)
        self.assertEqual(evidence["response_bytes"], len(raw))
        self.assertEqual(restored, raw)
        self.assertEqual(evidence["response_sha256"], hashlib.sha256(raw).hexdigest())

    def test_rejects_asset_id_that_does_not_match_resolved_base_ticker(self):
        metadata_raw = json.dumps(exchange_info_payload()).encode()
        artifact = {
            "schema_version": "binance-spot-ohlcv-capture-v1", "overall_status": "PASS",
            "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": "BTCUSDT", "interval": "1h"},
            "window": {"start_time_ms_inclusive": 0, "end_time_ms_exclusive": 3_600_000},
            "pages": [{"capture_status": "PASS", "normalization_status": "PASS", "response_base64": base64.b64encode(b"x").decode(), "response_bytes": 1, "response_sha256": hashlib.sha256(b"x").hexdigest()}],
            "candles": [{"open_time_ms": 0, "close_time_ms": 3_599_999, "open": "10", "high": "12", "low": "9", "close": "11", "base_volume": "10", "quote_volume": "100", "trade_count": 10, "closed_at_capture": True, "eligible_for_closed_candle_analysis": True}],
        }
        config = {"methodology_id":"test","methodology_version":"1","movement":{"lookback_bars":1,"return_threshold_pct":5,"volume_ratio_threshold":2},"support_resistance":{"pivot_left":1,"pivot_right":1,"tolerance_bps":100}}
        with patch("scripts.market_selection.capture_binance_spot_research.urlopen", return_value=FakeResponse(metadata_raw)), patch(
            "scripts.market_selection.capture_binance_spot_research.capture_history", return_value=artifact
        ):
            with self.assertRaisesRegex(ValueError, "base_asset_ticker does not match")
                capture_and_build_report(symbol="BTCUSDT", interval="1h", start_time_ms=0, end_time_ms_exclusive=3_600_000, config=config, base_asset_ticker="ETH", use_case="live_technical_test")


if __name__ == "__main__":
    unittest.main()
