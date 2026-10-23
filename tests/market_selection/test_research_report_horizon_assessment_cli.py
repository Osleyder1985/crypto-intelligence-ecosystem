"""Pruebas CLI offline para integrar evaluaciones independientes por horizonte."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.market_selection import research_report
from test_attach_horizon_assessment_to_report import assessment as assessment_fixture
from test_research_report import artifact, candle, config


class ResearchReportHorizonAssessmentCliTests(unittest.TestCase):
    def test_cli_attaches_validated_horizon_assessment_and_preserves_indeterminate_decision(self):
        source = artifact([
            candle(0, 10, 11, 9, 10),
            candle(1, 10, 11, 8, 9),
            candle(2, 9, 10, 7, 8),
            candle(3, 8, 9, 8, 8.5),
            candle(4, 8.5, 10, 8, 9.5),
            candle(5, 9.5, 11, 9, 10.5),
        ])
        assessment = assessment_fixture()
        assessment["asset_id"] = "BTC"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact_path = root / "ohlcv.json"
            config_path = root / "config.json"
            assessment_path = root / "horizon-assessment.json"
            output_path = root / "report.json"
            artifact_path.write_text(json.dumps(source), encoding="utf-8")
            config_path.write_text(json.dumps(config()), encoding="utf-8")
            assessment_path.write_text(json.dumps(assessment), encoding="utf-8")

            argv = [
                "research_report",
                "--asset-id", "BTC",
                "--artifact", str(artifact_path),
                "--config", str(config_path),
                "--horizon-assessment", str(assessment_path),
                "--output", str(output_path),
            ]
            allow = {"decision": "ALLOW", "reason_codes": ["SYNTHETIC_TEST_GATE_ONLY"]}
            with patch.object(sys, "argv", argv), patch(
                "scripts.market_selection.research_report.evaluate_artifact_use",
                return_value=allow,
            ), patch(
                "scripts.market_selection.analyze_ohlcv_risk_profile.evaluate_artifact_use",
                return_value=allow,
            ), patch(
                "scripts.market_selection.analyze_support_resistance.evaluate_artifact_use",
                return_value=allow,
            ), patch(
                "scripts.market_selection.detect_ohlcv_movement_events.evaluate_artifact_use",
                return_value=allow,
            ):
                self.assertEqual(research_report.main(), 0)

            result = json.loads(output_path.read_text(encoding="utf-8"))
            attached = result["horizon_assessment"]["assessment"]
            self.assertEqual(result["horizon_assessment"]["status"], "VALIDATED_ASSESSMENT_ATTACHED")
            self.assertEqual(attached["horizons"]["short"]["conclusion"], "FAVORABLE")
            self.assertEqual(attached["horizons"]["medium"]["conclusion"], "BASE")
            self.assertEqual(attached["horizons"]["long"]["conclusion"], "ADVERSE")
            self.assertEqual(attached["aggregation"], "NONE")
            self.assertTrue(all(item["conclusion"] == "INDETERMINATE" for item in result["horizons"].values()))
            self.assertEqual(result["decision_status"], "INDETERMINATE")
            self.assertFalse(result["orders_submitted"])
            self.assertEqual(
                result["horizon_assessment"]["source_assessment_sha256"],
                hashlib.sha256(assessment_path.read_bytes()).hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
