"""Offline contract tests for Issue 132 real-market temporal context output."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.market_selection.run_issue_132_live_backfill import capture_btc_movement_context


def cftc_btc_event():
    return {
        "schema_version": "crypto-external-event-record-v1",
        "event_id": "cftc_press_release_archive:btc-event-fixture",
        "title": "CFTC Approves BTCPERP Contract Submitted by KalshiEX, LLC",
        "event_type": "CFTC_BITCOIN_DERIVATIVE_APPROVAL",
        "source_id": "cftc_press_release_archive",
        "provider_id": "cftc_press_release_archive",
        "source": {
            "source_type": "REGULATORY",
            "url": "https://www.cftc.gov/PressRoom/PressReleases/9240-26",
            "publisher": "U.S. Commodity Futures Trading Commission press release archive",
        },
        "published_at": "2026-05-29T00:00:00Z",
        "captured_at": "2026-10-24T02:40:00Z",
        "entities": [{"id_type": "coingecko_id", "id": "bitcoin"}],
        "evidence": [{
            "url": "https://www.cftc.gov/PressRoom/PressReleases/9240-26",
            "claim": "Official release announces approval of a Bitcoin-referencing perpetual contract.",
        }],
        "capture_method": "public_event_archive_html_v1",
        "content_sha256": "a" * 64,
        "license_notes": "Official text with attribution; third-party content excluded.",
        "metadata": {
            "archive_publication_time_evidence": "05/29/2026",
            "causality_status": "NOT_ASSESSED",
        },
    }


class Issue132TemporalContextTests(unittest.TestCase):
    def test_report_retains_episode_linkage_but_not_raw_ohlcv_payload(self):
        start_ms = 1779926400000  # 2026-05-28T00:00:00Z
        end_ms = 1780099200000    # 2026-05-30T00:00:00Z
        observable_ms = 1780185600000  # 2026-05-31T00:00:00Z
        capture = {
            "overall_status": "PASS",
            "source": "https://data-api.binance.vision/api/v3/klines",
            "requested_open_candle_count": 696,
            "captured_candle_count": 696,
            "missing_open_time_ms": [],
            "provider_use_assessment": {
                "provider_id": "binance_spot_market_data",
                "decision": "ALLOW",
                "use_case": "internal_analysis",
                "authorization": {"authorized_use_cases": ["internal_analysis", "persistent_storage"]},
            },
            "pages": [{
                "url": "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT",
                "request_started_at_utc": "2026-10-24T02:40:00Z",
                "captured_at_utc": "2026-10-24T02:40:01Z",
                "http_status": 200,
                "response_bytes": 12345,
                "response_sha256": "b" * 64,
                "capture_status": "PASS",
                "normalization_status": "PASS",
                "response_base64": "MUST_NOT_BE_PERSISTED",
                "parsed_json": [["MUST_NOT_BE_PERSISTED"]],
            }],
        }
        sr = {
            "method": {"pivot_left": 1, "pivot_right": 1, "tolerance_bps": 100},
            "sample": {"confirmed_pivot_count": 2, "segment_count": 1},
        }
        episodes = {
            "method": {"name": "adjacent alternating confirmed local pivots"},
            "episodes": [{
                "episode_id": "swing-1",
                "direction": "BULLISH",
                "classification": "TECHNICAL_SWING_CANDIDATE",
                "start": {"pivot_open_time_ms": start_ms, "pivot_price": "100"},
                "end": {"pivot_open_time_ms": end_ms, "pivot_price": "110"},
                "episode_observable_only_at_ms": observable_ms,
                "causality_status": "NOT_ASSESSED",
            }],
        }
        auth = {
            "provider_id": "binance_spot_market_data",
            "status": "APPROVED",
            "approval_scope": {"automated_access": {"user_agent": "Issue132Test/1.0"}},
        }
        with tempfile.TemporaryDirectory() as tmp, \
             patch("scripts.market_selection.run_issue_132_live_backfill.capture_history", return_value=capture), \
             patch("scripts.market_selection.run_issue_132_live_backfill.analyze_support_resistance", return_value=sr), \
             patch("scripts.market_selection.run_issue_132_live_backfill.build_movement_episodes", return_value=episodes):
            result = capture_btc_movement_context(
                output_dir=Path(tmp),
                event_record=cftc_btc_event(),
                authorization_record=auth,
                captured_at="2026-10-24T02:40:02Z",
            )
            raw = (Path(tmp) / "btc-movement-context-report.json").read_bytes()
            report = json.loads(raw)

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["raw_ohlcv_persisted"])
        self.assertEqual(report["market_data"]["captured_candle_count"], 696)
        self.assertEqual(report["market_data"]["user_agent"], "Issue132Test/1.0")
        self.assertNotIn("candles", report["market_data"])
        self.assertNotIn("response_base64", json.dumps(report))
        self.assertNotIn("parsed_json", json.dumps(report))
        self.assertEqual(len(report["event_episode_assessments"]), 1)
        assessment = report["event_episode_assessments"][0]
        self.assertEqual(assessment["publication_date_relation"], "PUBLICATION_DATE_OVERLAPS_SWING_TIME_UNKNOWN")
        self.assertEqual(assessment["point_in_time_assessment"]["status"], "NOT_AVAILABLE_AT_DECISION_TIME")
        self.assertFalse(report["causality_claimed"])
        self.assertEqual(
            report["report_sha256"],
            hashlib.sha256(json.dumps({k: v for k, v in report.items() if k != "report_sha256"},
                                      sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
