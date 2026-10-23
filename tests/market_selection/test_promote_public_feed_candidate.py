import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.market_selection.capture_public_event_feed import capture_public_event_feed
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.promote_public_feed_candidate import main
from test_public_event_feed import (
    FakeResponse, USER_AGENT, approved_source, authorization_record, feed_xml, capture_article,
)


class PromotePublicFeedCandidateCliTests(unittest.TestCase):
    def test_cli_promotes_preserved_candidate_without_network_access(self):
        entry = approved_source()
        with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
            "scripts.market_selection.capture_public_event_feed.urlopen",
            return_value=FakeResponse(feed_xml()),
        ):
            capture = capture_public_event_feed(
                "cftc_general_press_releases",
                authorization_record(entry),
                USER_AGENT,
                captured_at="2026-10-22T12:30:00Z",
            )

        article = capture_article(entry, capture)
        evidence = b'{"asset":"example-asset","review":"synthetic"}'
        resolution = {
            "status": "APPROVED",
            "reviewed_by": "offline-test-fixture",
            "reviewed_at": "2026-10-22T12:20:00Z",
            "entities": [{"id_type": "coingecko_id", "id": "example-asset"}],
            "evidence_record_base64": base64.b64encode(evidence).decode("ascii"),
            "evidence_record_sha256": hashlib.sha256(evidence).hexdigest(),
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.json"
            resolution_path = root / "resolution.json"
            article_path = root / "article.json"
            output_path = root / "event.json"
            capture_path.write_text(json.dumps(capture), encoding="utf-8")
            resolution_path.write_text(json.dumps(resolution), encoding="utf-8")
            article_path.write_text(json.dumps(article), encoding="utf-8")

            with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {"cftc_general_press_releases": entry}), patch(
                "scripts.market_selection.capture_public_event_feed.urlopen",
            ) as network:
                status = main([
                    "--capture", str(capture_path),
                    "--candidate-id", capture["feed_items"][0]["candidate_id"],
                    "--event-type", "REGULATORY_ENFORCEMENT",
                    "--claim", "The preserved feed summary reports a regulatory announcement.",
                    "--entity-resolution", str(resolution_path),
                    "--article-capture", str(article_path),
                    "--output", str(output_path),
                ])

            network.assert_not_called()
            self.assertEqual(status, 0)
            event = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(event["source_id"], "cftc_general_press_releases")
            self.assertEqual(event["entities"], resolution["entities"])
            self.assertEqual(event["metadata"]["causality_status"], "NOT_ASSESSED")
            self.assertFalse(event["causality_claimed"])
            self.assertFalse(event["orders_submitted"])

    def test_cli_rejects_capture_when_source_terms_are_pending(self):
        capture = {
            "schema_version": "crypto-public-event-feed-capture-v1",
            "source_id": "cftc_general_press_releases",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.json"
            resolution_path = root / "resolution.json"
            article_path = root / "article.json"
            output_path = root / "event.json"
            capture_path.write_text(json.dumps(capture), encoding="utf-8")
            resolution_path.write_text("{}", encoding="utf-8")
            article_path.write_text("{}", encoding="utf-8")
            with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {
                "cftc_general_press_releases": dict(
                    EVENT_SOURCE_REGISTRY["sources"]["cftc_general_press_releases"]
                )
            }):
                with self.assertRaises(PermissionError):
                    main([
                        "--capture", str(capture_path),
                        "--candidate-id", "missing",
                        "--event-type", "REGULATORY_ENFORCEMENT",
                        "--claim", "Synthetic claim.",
                        "--entity-resolution", str(resolution_path),
                        "--article-capture", str(article_path),
                        "--output", str(output_path),
                    ])
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
