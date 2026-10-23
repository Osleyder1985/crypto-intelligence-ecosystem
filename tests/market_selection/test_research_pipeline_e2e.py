"""Prueba E2E offline del informe, libro de órdenes, eventos y métricas fundamentales.

Todas las respuestas de proveedores y autorizaciones son fixtures sintéticas.
La prueba valida la integración y los controles conservadores, no permisos reales.
"""
import base64
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import (
    capture_public_event_feed,
    promote_public_feed_candidate_to_event,
)
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.research_report import build_research_report
from scripts.market_selection.research_evidence_integration import enrich_research_report
from scripts.market_selection.attach_horizon_assessment_to_report import attach_horizon_assessment

from test_public_event_feed import (
    FakeResponse as GenericFeedFakeResponse,
    USER_AGENT as GENERIC_FEED_USER_AGENT,
    approved_source as approved_generic_source,
    authorization_record as generic_authorization_record,
    feed_xml as generic_feed_xml,
)
from test_research_report import artifact, candle, config, identity_evidence
from test_research_evidence_integration import (
    approved_defillama_authorization_fixture,
    fundamental_observation,
    methodology,
)
from test_attach_horizon_assessment_to_report import assessment as horizon_assessment_fixture
from test_attach_horizon_assessment_to_report import approved_methodology as approved_horizon_methodology_fixture


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
        four_hour_source = copy.deepcopy(source)
        four_hour_source["market"]["interval"] = "4h"
        for index, row in enumerate(four_hour_source["candles"]):
            row["open_time_ms"] = index * 14_400_000
            row["close_time_ms"] = (index + 1) * 14_400_000 - 1
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
                multi_timeframe_support_resistance_artifacts=[source, four_hour_source],
                multi_timeframe_confluence_tolerance_bps=25,
            )

        analyses = report["descriptive_analyses"]
        self.assertTrue(analyses["support_resistance"]["events"])
        self.assertTrue(analyses["movement_episodes"]["episodes"])
        self.assertEqual(analyses["order_book"]["status"], "DESCRIPTIVE_SNAPSHOT")
        self.assertEqual(analyses["order_book"]["book"]["best_bid"], "10.9")
        self.assertEqual(analyses["order_book"]["book"]["best_ask"], "11.1")
        multi = analyses["support_resistance_multi_timeframe"]
        self.assertEqual(multi["timeframe_count"], 2)
        self.assertEqual(
            multi["cross_timeframe_confluence"],
            "COMPUTED_BY_EXPLICIT_PRICE_TOLERANCE",
        )
        self.assertTrue(multi["confluence_groups"])
        self.assertEqual(
            {timeframe["interval"] for timeframe in multi["timeframes"]},
            {"1h", "4h"},
        )

        episode = analyses["movement_episodes"]["episodes"][0]
        source_entry = approved_generic_source()
        mapping_evidence = b'{"asset":"example-asset","mapping":"reviewed synthetic fixture"}'
        entity_resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-test-fixture",
            "reviewed_at": "2026-10-22T12:20:00Z",
            "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
            "evidence_record_base64": base64.b64encode(mapping_evidence).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(mapping_evidence).hexdigest(),
        }
        with patch.dict(
            EVENT_SOURCE_REGISTRY["sources"],
            {"cftc_general_press_releases": source_entry},
        ), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=GenericFeedFakeResponse(generic_feed_xml()),
        ):
            feed_capture = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record=generic_authorization_record(source_entry),
                user_agent=GENERIC_FEED_USER_AGENT,
                captured_at="2026-10-22T12:30:00Z",
            )
            promoted_event = promote_public_feed_candidate_to_event(
                feed_capture,
                feed_capture["feed_items"][0]["candidate_id"],
                "REGULATORY_ENFORCEMENT",
                "The preserved synthetic feed summary reports a regulatory announcement.",
                entity_resolution,
            )
        with patch.dict(
            EVENT_SOURCE_REGISTRY["sources"],
            {"cftc_general_press_releases": source_entry},
        ), patch(
            "scripts.market_selection.research_evidence_integration.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ):
            enriched = enrich_research_report(
                report,
                events=[{
                    "event": promoted_event,
                    "target_entity": {
                        "id_type": "coingecko_id",
                        "id": "example-asset",
                    },
                    "movement_episode_id": episode["episode_id"],
                }],
                observations=[fundamental_observation(terms_status="APPROVED")],
                methodology=methodology(),
                asset={"stable_id": "example-asset", "category": "smart_contract_token"},
                evaluation_as_of="2026-10-21T00:00:00Z",
                provider_authorization_registry={
                    "defillama_api": approved_defillama_authorization_fixture(),
                },
            )

        assessment = enriched["external_event_evidence"]["assessments"][0]
        self.assertEqual(assessment["movement_episode"]["episode_id"], episode["episode_id"])
        self.assertEqual(
            assessment["movement_episode"]["event_relation_to_swing"],
            "FOLLOWS_SWING",
        )
        self.assertEqual(
            enriched["event_causal_assessment"]["episode_assessments"][0]["status"],
            "NO_SUPPORTING_EVENT_IN_SUPPLIED_EVIDENCE",
        )
        self.assertEqual(
            enriched["event_causal_assessment"]["episode_assessments"][0]["event_ids"],
            [assessment["event_id"]],
        )
        self.assertFalse(enriched["external_event_evidence"]["causality_claimed"])
        self.assertFalse(enriched["event_causal_assessment"]["causality_claimed"])
        fundamental = enriched["fundamental_onchain_assessment"]
        tvl = fundamental["metrics"]["protocol.tvl"]
        self.assertEqual(tvl["status"], "OBSERVED")
        self.assertEqual(tvl["value"], 123456.0)
        self.assertEqual(tvl["observation_ids"], ["tvl-example-20261020"])
        self.assertEqual(
            fundamental["metrics"]["stablecoin.reserve_attestation"]["status"],
            "NOT_APPLICABLE",
        )
        self.assertEqual(
            enriched["fundamental_source_use_assessments"][0]["decision"],
            "ALLOW",
        )
        self.assertEqual(
            enriched["fundamental_source_use_assessments"][1]["decision"],
            "ALLOW",
        )
        self.assertEqual(enriched["decision_status"], "INDETERMINATE")
        self.assertFalse(enriched["orders_submitted"])

        horizon_assessment = copy.deepcopy(horizon_assessment_fixture())
        horizon_assessment["asset_id"] = enriched["requested_asset_id"]
        combined = attach_horizon_assessment(
            enriched, horizon_assessment, methodology=approved_horizon_methodology_fixture()
        )
        attached = combined["horizon_assessment"]["assessment"]
        self.assertEqual(attached["horizons"]["short"]["conclusion"], "FAVORABLE")
        self.assertEqual(attached["horizons"]["medium"]["conclusion"], "BASE")
        self.assertEqual(attached["horizons"]["long"]["conclusion"], "ADVERSE")
        self.assertEqual(attached["aggregation"], "NONE")
        self.assertEqual(combined["horizons"], enriched["horizons"])
        self.assertTrue(
            all(item["conclusion"] == "INDETERMINATE" for item in combined["horizons"].values())
        )
        self.assertEqual(combined["decision_status"], "INDETERMINATE")
        self.assertFalse(combined["orders_submitted"])


if __name__ == "__main__":
    unittest.main()
