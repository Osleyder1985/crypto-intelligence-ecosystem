import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.market_selection import capture_public_event_archive, capture_public_event_feed
from scripts.market_selection.event_source_registry import EVENT_SOURCE_REGISTRY
from scripts.market_selection.shared_request_rate_limiter import RateLimitCoordinationError
from test_public_event_feed import USER_AGENT, approved_source, authorization_record


class TestStructuredRateLimitFailure(unittest.TestCase):
    def _write_authorization(self, directory, source_id, entry):
        path = Path(directory) / "authorization.json"
        path.write_text(json.dumps({source_id: authorization_record(entry)}), encoding="utf-8")
        return path

    def _assert_failure_artifact(self, path):
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["capture_status"], "BLOCKED_RATE_LIMIT_COORDINATION")
        self.assertEqual(result["reason_codes"], ["RATE_LIMIT_COORDINATION_FAILED"])
        self.assertFalse(result["network_request_made"])
        self.assertEqual(result["errors"][0]["type"], "RATE_LIMIT_COORDINATION")
        self.assertNotIn(str(Path.home()), result["errors"][0]["message"])
        return result

    def test_feed_cli_writes_structured_failure_without_network(self):
        source_id = "cftc_general_press_releases"
        entry = approved_source(source_id)
        with tempfile.TemporaryDirectory() as directory:
            auth = self._write_authorization(directory, source_id, entry)
            output = Path(directory) / "feed.json"
            argv = [
                "capture_public_event_feed.py", "--source-id", source_id,
                "--provider-authorization-registry", str(auth),
                "--user-agent", USER_AGENT, "--output", str(output),
            ]
            with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}), \
                 patch.object(sys, "argv", argv), \
                 patch("scripts.market_selection.capture_public_event_feed._wait_for_rate_slot",
                       side_effect=RateLimitCoordinationError("private database path must not leak")), \
                 patch("scripts.market_selection.capture_public_event_feed.urlopen") as network, \
                 patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as article_network:
                self.assertEqual(capture_public_event_feed.main(), 2)
            network.assert_not_called()
            article_network.assert_not_called()
            self._assert_failure_artifact(output)

    def test_archive_cli_writes_structured_failure_without_network(self):
        source_id = "cftc_press_release_archive"
        entry = approved_source(source_id)
        with tempfile.TemporaryDirectory() as directory:
            auth = self._write_authorization(directory, source_id, entry)
            output = Path(directory) / "archive.json"
            argv = [
                "capture_public_event_archive.py", "capture-index",
                "--source-id", source_id,
                "--archive-url", entry["source_url"],
                "--provider-authorization-registry", str(auth),
                "--user-agent", USER_AGENT, "--output", str(output),
            ]
            with patch.dict(EVENT_SOURCE_REGISTRY["sources"], {source_id: entry}), \
                 patch.object(sys, "argv", argv), \
                 patch("scripts.market_selection.capture_public_event_feed._wait_for_rate_slot",
                       side_effect=RateLimitCoordinationError("private database path must not leak")), \
                 patch("scripts.market_selection.capture_public_event_feed._open_allowlisted_url") as network:
                self.assertEqual(capture_public_event_archive.main(), 2)
            network.assert_not_called()
            self._assert_failure_artifact(output)


if __name__ == "__main__":
    unittest.main()
