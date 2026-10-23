import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.market_selection.evaluation_record import (
    build_evaluation_record,
    compare_evaluation_records,
    verify_evaluation_record,
)


def manifest(source_path, **overrides):
    data = {
        "generated_at_utc": "2026-10-22T12:00:00Z",
        "asset_id": "BTC",
        "market_id": "binance:BTCUSDT:SPOT",
        "horizon": "1d",
        "methodology_id": "risk-profile",
        "methodology_version": "1.0.0",
        "code_version": "git:abc123",
        "git_sha": "abc123",
        "parameters": {"interval": "1h", "lookback": 24},
        "results": {"return_pct": 2.5, "risk": {"drawdown_pct": -1.2}},
        "quality": {"status": "PASS", "coverage_ratio": 1.0},
        "uncertainty": ["single venue"],
        "warnings": [],
        "source_artifacts": [{
            "path": str(source_path), "source": "binance", "endpoint": "/api/v3/klines",
            "window_start_utc": "2026-10-21T12:00:00Z", "window_end_utc": "2026-10-22T12:00:00Z",
            "quality_status": "PASS",
        }],
    }
    data.update(overrides)
    return data


class EvaluationRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.json"
        self.source.write_text('{"rows":[1,2,3]}', encoding="utf-8")
        self.archive = self.root / "archive"
        self.records = self.root / "records"

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, src=None, **overrides):
        return build_evaluation_record(manifest(src or self.source, **overrides), self.archive, self.records)

    def test_builds_content_addressed_record_and_archives_exact_input(self):
        record = self.build()
        path = self.records / f'{record["evaluation_id"]}.json'
        self.assertTrue(path.exists())
        source = record["source_artifacts"][0]
        archived = self.archive / source["archive_relative_path"]
        self.assertEqual(archived.read_bytes(), self.source.read_bytes())
        self.assertEqual(source["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertFalse(record["orders_submitted"])
        self.assertEqual(verify_evaluation_record(path, self.archive)["valid"], True)

    def test_repeated_content_reuses_input_blob_but_record_is_create_only(self):
        first = self.build()
        with self.assertRaises(FileExistsError):
            self.build()

    def test_tampered_archived_input_fails_verification(self):
        record = self.build()
        path = self.archive / record["source_artifacts"][0]["archive_relative_path"]
        path.write_bytes(b"tampered")
        result = verify_evaluation_record(self.records / f'{record["evaluation_id"]}.json', self.archive)
        self.assertFalse(result["valid"])
        self.assertTrue(any("source_archive_integrity_mismatch" in error for error in result["errors"]))

    def test_tampered_record_fails_verification(self):
        record = self.build()
        path = self.records / f'{record["evaluation_id"]}.json'
        data = json.loads(path.read_text(encoding="utf-8"))
        data["results"]["return_pct"] = 999
        path.write_text(json.dumps(data), encoding="utf-8")
        result = verify_evaluation_record(path, self.archive)
        self.assertFalse(result["valid"])
        self.assertIn("evaluation_id_mismatch", result["errors"])

    def test_comparison_separates_comparable_observed_change_from_method_changes(self):
        old = self.build()
        source2 = self.root / "source2.json"
        source2.write_text('{"rows":[1,2,4]}', encoding="utf-8")
        new = build_evaluation_record(manifest(source2, generated_at_utc="2026-10-22T13:00:00Z",
            results={"return_pct": 3.0, "risk": {"drawdown_pct": -1.5}}), self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        self.assertTrue(result["scope_compatible"])
        self.assertFalse(result["methodology_changed"])
        self.assertFalse(result["implementation_changed"])
        self.assertTrue(result["input_data_changed"])
        self.assertEqual(result["attribution_status"], "COMPARABLE_OBSERVED_CHANGE_CANDIDATE")
        self.assertEqual(result["numeric_metric_deltas"][0]["metric"], "return_pct")

    def test_methodology_change_blocks_market_only_attribution(self):
        old = self.build()
        source2 = self.root / "source2.json"
        source2.write_text('{"rows":[1,2,4]}', encoding="utf-8")
        new = build_evaluation_record(manifest(source2, generated_at_utc="2026-10-22T13:00:00Z",
            methodology_version="2.0.0", results={"return_pct": 3.0}), self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        self.assertTrue(result["methodology_changed"])
        self.assertEqual(result["attribution_status"], "MIXED_OR_INCOMPATIBLE_CAUSES")

    def test_scope_change_is_incompatible(self):
        old = self.build()
        source2 = self.root / "source2.json"
        source2.write_text('{"rows":[1,2,4]}', encoding="utf-8")
        new = build_evaluation_record(manifest(source2, market_id="okx:BTC-USDT:SPOT"), self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        self.assertFalse(result["scope_compatible"])
        self.assertEqual(result["attribution_status"], "INCOMPATIBLE_SCOPE")

    def test_identical_inputs_with_changed_results_are_flagged(self):
        old = self.build()
        new = build_evaluation_record(manifest(self.source, generated_at_utc="2026-10-22T13:00:00Z",
            results={"return_pct": 99}), self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        self.assertFalse(result["input_data_changed"])
        self.assertEqual(result["attribution_status"], "INCONSISTENT_RESULTS_FOR_IDENTICAL_INPUT_HASHES")

    def test_non_finite_results_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-finite"):
            self.build(results={"metric": float("nan")})

    def test_explicit_base_asset_must_match_declared_asset(self):
        with self.assertRaisesRegex(ValueError, "base_asset_id must match asset_id"):
            self.build(market_metadata={"base_asset_id": "ETH", "quote_asset_id": "USDT", "market_type": "SPOT"})

    def test_delimited_market_pair_must_match_explicit_quote_asset(self):
        with self.assertRaisesRegex(ValueError, "quote_asset_id must match the delimited market pair"):
            self.build(market_id="okx:BTC-USDT:SPOT",
                       market_metadata={"base_asset_id": "BTC", "quote_asset_id": "USD", "market_type": "SPOT"})

    def test_explicit_market_type_must_match_market_id(self):
        with self.assertRaisesRegex(ValueError, "market_type must match market_id"):
            self.build(market_metadata={"market_type": "FUTURES"})

    def test_valid_explicit_market_metadata_is_persisted(self):
        record = self.build(market_id="okx:BTC-USDT:SPOT",
                            market_metadata={"base_asset_id": "BTC", "quote_asset_id": "USDT", "market_type": "SPOT"})
        self.assertEqual(record["market_metadata"], {
            "base_asset_id": "BTC", "quote_asset_id": "USDT", "market_type": "SPOT"
        })

    def test_market_metadata_change_makes_comparison_scope_incompatible(self):
        old = self.build(market_id="okx:BTC-USDT:SPOT",
                         market_metadata={"base_asset_id": "BTC", "quote_asset_id": "USDT", "market_type": "SPOT"})
        new = build_evaluation_record(
            manifest(self.source, market_id="okx:BTC-USDT:SPOT",
                     market_metadata={"market_type": "SPOT"}),
            self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        self.assertFalse(result["scope_compatible"])
        self.assertEqual(result["attribution_status"], "INCOMPATIBLE_SCOPE")

    def test_source_artifact_metadata_is_required(self):
        data = manifest(self.source)
        data["source_artifacts"][0]["endpoint"] = ""
        with self.assertRaisesRegex(ValueError, "endpoint"):
            build_evaluation_record(data, self.archive, self.records)

    def test_comparison_uses_zero_safe_relative_delta(self):
        old = self.build(results={"return_pct": 0, "risk": {"drawdown_pct": -1.2}})
        source2 = self.root / "source2.json"
        source2.write_text('{"rows":[0]}', encoding="utf-8")
        new = build_evaluation_record(manifest(source2, generated_at_utc="2026-10-22T13:00:00Z",
            results={"return_pct": 2.5, "risk": {"drawdown_pct": -1.2}}), self.archive, self.root / "records2")
        result = compare_evaluation_records(old, new)
        metric = next(x for x in result["numeric_metric_deltas"] if x["metric"] == "return_pct")
        self.assertEqual(metric["relative_delta_pct"], None)
        self.assertTrue(metric["old_zero_baseline"])


if __name__ == "__main__":
    unittest.main()
