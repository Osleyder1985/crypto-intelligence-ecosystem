"""Cross-module offline E2E for technical report, order book, and event timing.

All provider responses and source approvals are synthetic fixtures. This test
proves pipeline wiring and fail-safe semantics, not live source authorization.
"""
import copy
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.research_report import build_research_report
from scripts.market_selection.research_evidence_integration import enrich_research_report

from test_research_report import artifact, candle, config, identity_evidence
from test_research_evidence_integration import (
    approved_event_source, event, methodology,
)


class CombinedResearchPipelineE2ETests(unittest.TestCase):
    def test_report_links_order_book_levels_and_event_to_observed_movement_episode(self):
        candles = [
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
            candle(5, 9.5, 11, 9, 10.5),
            candle(6, 10.5, 12, 10, 11.5),
            candle(7, 11.5, 11.8, 10.5, 11.0),
        ]
        source = artifact(candles)
        raw_source = json.dumps(source, ensure_ascii=False, sort_keys=True).encode("utf-8")
        identity = copy.deepcopy(identity_evidence())
        identity["stable_id"] = "example-asset"
        order_book = {
            "schema_version": "crypto-spot-order-book-snapshot-v1",
            "capture_status": "PASS",
            "provider_id": "binance_spot_market_data",
            "market": {
                "exchange": "binance", "symbol_native": "BTCUSDT",
                "quote_asset": "USDT",
            },
            "captured_at_utc": "2026-10-20T10:00:00Z",
            "bids": [["10.9", "10"], ["10.8", "20"]],
            "asks": [["11.1", "8"], ["11.2", "12"]],
        }

        with patch(
            "scripts.market_selection.research_report.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.analyze_ohlcv_risk_profile.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.analyze_support_resistance.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.detect_ohlcv_movement_events.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ), patch(
            "scripts.market_selection.analyze_order_book_snapshot.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ):
            report = build_research_report(
                source, config(), "BTC", raw_source,
                identity_evidence=identity,
                order_book_artifact=order_book,
                order_book_authorization_registry={
                    "binance_spot_market_data": {"synthetic_fixture_only": True},
                },
            )

        analyses = report["descriptive_analyses"]
        self.assertTrue(analyses["support_resistance"]["events"])
        self.assertTrue(analyses["movement_episodes"]["episodes"])
        self.assertEqual(analyses["order_book"]["status"], "DESCRIPTIVE_SNAPSHOT")
        self.assertEqual(analyses["order_book"]["book"]["best_bid"], "10.9")
        self.assertEqual(analyses["order_book"]["book"]["best_ask"], "11.1")

        episode = analyses["movement_episodes"]["episodes"][0]
        source_entry = approved_event_source()
        with patch.dict(
            EVENT_SOURCE_REGISTRY["sources"],
            {"sec_press_releases": source_entry},
        ):
            enriched = enrich_research_report(
                report,
                events=[{
                    "event": event(),
                    "target_entity": {
                        "id_type": "coingecko_id",
                        "id": "example-asset",
                    },
                    "movement_episode_id": episode["episode_id"],
                }],
                observations=[],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "native_l1"},
                evaluation_as_of="2026-10-21T00:00:00Z",
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["movement_episode"]["episode_id"], episode["episode_id"])
        self.assertEqual(
            assessment["movement_episode"]["event_relation_to_swing"],
            "FOLLOWS_SWING",
        )
        self.assertEqual(
            enriched["event_causal_assessment"]["episode_assessments"][0]["status"],
            "TEMPORAL_ASSOCIATION_ONLY",
        )
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertFalse(enriched["event_causal_assessment"]["causality_claimed"])
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["orders_submitted"])


if __name__ == "__main__":
    unittest.main()
