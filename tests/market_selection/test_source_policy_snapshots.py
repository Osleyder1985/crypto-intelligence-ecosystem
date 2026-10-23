import io
import unittest
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts.market_selection import capture_source_policy_snapshots as snapshots


class FakeResponse:
    def __init__(self, body=b"<html>policy</html>", status=200, url="https://www.sec.gov/about/privacy-information"):
        self.body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"
        self.headers["ETag"] = '"policy-v1"'
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body

    def geturl(self):
        return self.url


class SourcePolicyConnectivityTests(unittest.TestCase):
    def test_retries_transient_http_503_then_captures_complete_body(self):
        error_headers = Message()
        error_headers["Retry-After"] = "0"
        transient = HTTPError(
            "https://www.sec.gov/about/privacy-information",
            503,
            "Service Unavailable",
            error_headers,
            io.BytesIO(b"temporary"),
        )
        with patch.object(snapshots, "urlopen", side_effect=[transient, FakeResponse()]) as open_url, patch.object(snapshots.time, "sleep"):
            record, body = snapshots.capture(
                "https://www.sec.gov/about/privacy-information",
                "CryptoIntelligence connectivity test",
                1.0,
                2,
            )
        self.assertEqual(open_url.call_count, 2)
        self.assertEqual(record["capture_status"], "PASS")
        self.assertEqual(record["attempts_used"], 2)
        self.assertEqual(record["body_bytes"], len(body))
        self.assertEqual(record["body_sha256"], snapshots.hashlib.sha256(body).hexdigest())

    def test_network_failure_reports_dns_diagnostic_without_fake_success(self):
        with patch.object(snapshots, "urlopen", side_effect=URLError("temporary DNS failure")), patch.object(
            snapshots, "sleep", create=True
        ), patch.object(snapshots.socket, "getaddrinfo", side_effect=snapshots.socket.gaierror("name not resolved")) as resolve, patch.object(
            snapshots.time, "sleep"
        ):
            record, body = snapshots.capture(
                "https://www.sec.gov/about/privacy-information",
                "CryptoIntelligence connectivity test",
                1.0,
                1,
            )
        self.assertIsNone(body)
        self.assertEqual(record["capture_status"], "NETWORK_ERROR")
        self.assertEqual(record["dns_diagnostic"]["host"], "www.sec.gov")
        self.assertIn("error", record["dns_diagnostic"])
        resolve.assert_called_once()


if __name__ == "__main__":
    unittest.main()
