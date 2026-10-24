import hashlib
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import URLError
from unittest.mock import Mock

from scripts.market_selection.capture_source_policy_evidence import capture_policy_page, validate_url


class FakeResponse:
    status = 200

    def __init__(self, body=b"official policy bytes", url="https://www.sec.gov/about/privacy-information"):
        self.body = body
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body

    def geturl(self):
        return self.url


class SourcePolicyEvidenceCaptureTests(unittest.TestCase):
    def test_retries_transient_dns_failure_and_preserves_exact_bytes_and_hash(self):
        client = Mock()
        client.open.side_effect = [URLError("temporary DNS failure"), FakeResponse()]
        sleeps = []
        with tempfile.TemporaryDirectory() as tmp:
            result = capture_policy_page(
                "https://www.sec.gov/about/privacy-information",
                Path(tmp),
                "CryptoIntelligenceResearch/1.0 (contact: operator)",
                retries=2,
                backoff_seconds=0.25,
                opener=client,
                sleep=sleeps.append,
            )
            raw = (Path(tmp) / "policy-response.bin").read_bytes()
            metadata = json.loads((Path(tmp) / "policy-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(result["capture_status"], "PASS")
        self.assertEqual(raw, b"official policy bytes")
        self.assertEqual(result["body_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(metadata["body_sha256"], result["body_sha256"])
        self.assertEqual(result["retry_count"], 1)
        self.assertEqual(sleeps, [0.25])
        self.assertFalse(result["provider_approved"])
        self.assertIsNone(result["application_size_limit_bytes"])

    def test_rejects_non_https_or_non_official_host(self):
        for url in ("http://www.sec.gov/policy", "https://example.com/policy", "https://sec.gov.evil.example/policy"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_network_failure_is_persisted_and_returns_non_pass(self):
        client = Mock()
        client.open.side_effect = URLError("temporary DNS failure")
        with tempfile.TemporaryDirectory() as tmp:
            result = capture_policy_page(
                "https://www.cftc.gov/WebPolicy/index.htm",
                Path(tmp),
                "CryptoIntelligenceResearch/1.0 (contact: operator)",
                retries=1,
                backoff_seconds=0,
                opener=client,
                sleep=lambda _: None,
            )
            metadata = json.loads((Path(tmp) / "policy-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(result["capture_status"], "NETWORK_ERROR")
        self.assertEqual(result["retry_count"], 1)
        self.assertFalse(result["read_to_eof"])
        self.assertEqual(len(metadata["attempts"]), 2)
        self.assertIsNone(result["body_sha256"])


    def test_persistence_failure_does_not_repeat_network_request(self):
        client = Mock()
        client.open.return_value = FakeResponse()
        with tempfile.TemporaryDirectory() as tmp, unittest.mock.patch(
            "scripts.market_selection.capture_source_policy_evidence._atomic_write",
            side_effect=OSError("disk full"),
        ):
            with self.assertRaisesRegex(OSError, "disk full"):
                capture_policy_page(
                    "https://www.sec.gov/about/privacy-information",
                    Path(tmp),
                    "CryptoIntelligenceResearch/1.0 (contact: operator)",
                    retries=3,
                    backoff_seconds=0,
                    opener=client,
                    sleep=lambda _: None,
                )
        client.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
