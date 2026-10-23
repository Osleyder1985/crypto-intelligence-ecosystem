"""Offline tests for attaching visible order-book evidence to research reports."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts.market_selection.attach_order_book_evidence_to_report import (
    INTEGRATION_SCHEMA,
    attach_order_book_evidence,
)
from scripts.market_selection.research_report import REPORT_SCHEMA


def report():
    return {
        "schema_version": REPORT_SCHEMA,
        "requested_asset_id": "binance:BTCUSDT",
        "decision_status": "INDETERMINATE",
        "orders_submitted": False,
        "source_artifact": {"provider_use_assessment": {"decision": "ALLOW"}},
        "horizons": {
            "short": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
            "medium": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
            "long": {"status": "INDETERMINATE", "conclusion": "INDETERMINATE"},
        },
    }


def snapshot():
    return {
        "schema_version": "crypto-spot-order-book-snapshot-v1",
        "capture_status": "PASS",
        "provider_id": "binance_spot_market_data",
        "market": {"exchange": "binance", "symbol_native": "BTCUSDT", "quote_asset": "USDT"},
        "captured_at_utc": "2026-10-22T00:00:00Z",
        "bids": [["99", "2"], ["98", "3"]],
        "asks": [["101", "1"], ["102", "4"]],
    }


def allow_gates():
    return (
        patch(
            "scripts.market_selection.attach_order_book_evidence_to_report.evaluate_artifact_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ),
        patch(
            "scripts.market_selection.attach_order_book_evidence_to_report.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ),
        patch(
            "scripts.market_selection.analyze_order_book_snapshot.evaluate_provider_use",
            return_value={"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]},
        ),
    )


class AttachOrderBookEvidenceTests(unittest.TestCase):
    def test_attaches_visible_bid_ask_depth_without_changing_decisions(self):
        original = report()
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            result = attach_order_book_evidence(
                original, [snapshot()], evaluation_as_of="2026-10-23T00:00:00Z",
                authorization_registry={"binance_spot_market_data": {"synthetic": True}},
            )
        evidence = result["order_book_evidence"]
        analysis = evidence["analyses"][0]["analysis"]
        self.assertEqual(evidence["integration_schema"], INTEGRATION_SCHEMA)
        self.assertEqual(evidence["status"], "ANALYZED")
        self.assertEqual(evidence["snapshot_count"], 1)
        self.assertEqual(analysis["book"]["best_bid"], "99")
        self.assertEqual(analysis["book"]["best_ask"], "101")
        self.assertEqual(analysis["book"]["visible_bid_quote_notional"], "492")
        self.assertEqual(analysis["book"]["visible_ask_quote_notional"], "509")
        self.assertEqual(result["decision_status"], "INDETERMINATE")
        self.assertFalse(result["orders_submitted"])
        self.assertEqual(result["horizons"], original["horizons"])
        self.assertNotIn("order_book_evidence", original)

    def test_preserves_hashes_of_exact_input_bytes(self):
        value, items = report(), [snapshot()]
        report_raw = json.dumps(value, sort_keys=True).encode()
        snapshots_raw = json.dumps(items, sort_keys=True).encode()
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            result = attach_order_book_evidence(
                value, items, evaluation_as_of="2026-10-23T00:00:00Z",
                authorization_registry={"binance_spot_market_data": {"synthetic": True}},
                report_bytes=report_raw, snapshots_bytes=snapshots_raw,
            )
        evidence = result["order_book_evidence"]
        self.assertEqual(evidence["source_report_sha256"], hashlib.sha256(report_raw).hexdigest())
        self.assertEqual(evidence["source_snapshots_sha256"], hashlib.sha256(snapshots_raw).hexdigest())

    def test_rejects_snapshot_after_historical_cutoff(self):
        value = snapshot()
        value["captured_at_utc"] = "2026-10-24T00:00:00Z"
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            with self.assertRaisesRegex(ValueError, "captured after evaluation_as_of"):
                attach_order_book_evidence(
                    report(), [value], evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={"binance_spot_market_data": {"synthetic": True}},
                )

    def test_rejects_market_identity_mismatch(self):
        value = snapshot()
        value["market"]["symbol_native"] = "ETHUSDT"
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            with self.assertRaisesRegex(ValueError, "does not match report.requested_asset_id"):
                attach_order_book_evidence(
                    report(), [value], evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={"binance_spot_market_data": {"synthetic": True}},
                )

    def test_rejects_duplicate_market_capture_timestamp(self):
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            with self.assertRaisesRegex(ValueError, "duplicate order-book capture"):
                attach_order_book_evidence(
                    report(), [snapshot(), copy.deepcopy(snapshot())],
                    evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={"binance_spot_market_data": {"synthetic": True}},
                )

    def test_rejects_provider_storage_not_authorized(self):
        gates = allow_gates()
        with gates[0], patch(
            "scripts.market_selection.attach_order_book_evidence_to_report.evaluate_provider_use",
            return_value={"decision": "BLOCK", "reason_codes": ["STORAGE_NOT_AUTHORIZED"]},
        ), gates[2]:
            with self.assertRaisesRegex(PermissionError, "provider storage blocked"):
                attach_order_book_evidence(
                    report(), [snapshot()], evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={"binance_spot_market_data": {"synthetic": True}},
                )

    def test_empty_snapshot_list_is_explicitly_not_available(self):
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            result = attach_order_book_evidence(
                report(), [], evaluation_as_of="2026-10-23T00:00:00Z",
                authorization_registry={},
            )
        self.assertEqual(result["order_book_evidence"]["status"], "NOT_AVAILABLE")
        self.assertEqual(result["order_book_evidence"]["snapshot_count"], 0)
        self.assertFalse(result["orders_submitted"])

    def test_refuses_to_overwrite_existing_order_book_evidence(self):
        value = report()
        value["order_book_evidence"] = {"status": "EXISTING"}
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                attach_order_book_evidence(
                    value, [], evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={},
                )

    def test_rejects_non_indeterminate_report(self):
        value = report()
        value["decision_status"] = "FAVORABLE"
        with self.assertRaisesRegex(ValueError, "only INDETERMINATE"):
            attach_order_book_evidence(value, [], evaluation_as_of="2026-10-23T00:00:00Z")

    def test_rejects_mismatched_raw_input_bytes(self):
        gates = allow_gates()
        with gates[0], gates[1], gates[2]:
            with self.assertRaisesRegex(ValueError, "report_bytes do not match"):
                attach_order_book_evidence(
                    report(), [], evaluation_as_of="2026-10-23T00:00:00Z",
                    authorization_registry={}, report_bytes=b'{"wrong":true}',
                )


if __name__ == "__main__":
    unittest.main()
