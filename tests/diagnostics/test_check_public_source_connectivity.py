import socket
import unittest
from unittest.mock import patch

from scripts.diagnostics.check_public_source_connectivity import diagnose_url


class ConnectivityDiagnosticTests(unittest.TestCase):
    def test_rejects_non_https_url_without_network(self):
        with patch("scripts.diagnostics.check_public_source_connectivity.socket.getaddrinfo") as dns:
            result = diagnose_url("http://example.com")
        self.assertEqual(result["dns_status"], "INVALID_URL")
        self.assertEqual(result["https_status"], "NOT_ATTEMPTED")
        dns.assert_not_called()

    def test_classifies_dns_failure_without_attempting_https(self):
        with patch(
            "scripts.diagnostics.check_public_source_connectivity.socket.getaddrinfo",
            side_effect=socket.gaierror("temporary failure"),
        ), patch("scripts.diagnostics.check_public_source_connectivity.build_opener") as opener:
            result = diagnose_url("https://example.com/policy")
        self.assertEqual(result["dns_status"], "FAILED")
        self.assertEqual(result["https_status"], "NOT_ATTEMPTED")
        self.assertEqual(result["error_type"], "gaierror")
        opener.assert_not_called()

    def test_classifies_successful_https_response(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        opener_instance = unittest.mock.Mock()
        opener_instance.open.return_value = Response()
        with patch("scripts.diagnostics.check_public_source_connectivity.socket.getaddrinfo", return_value=[]), patch(
            "scripts.diagnostics.check_public_source_connectivity.build_opener",
            return_value=opener_instance,
        ):
            result = diagnose_url("https://example.com/policy", 1.0)
        self.assertEqual(result["dns_status"], "PASS")
        self.assertEqual(result["https_status"], "PASS")
        self.assertEqual(result["http_status"], 200)
        opener_instance.open.assert_called_once()

    def test_http_error_still_confirms_transport_reachability(self):
        from urllib.error import HTTPError
        error = HTTPError("https://example.com", 405, "Method Not Allowed", {}, None)
        with patch("scripts.diagnostics.check_public_source_connectivity.socket.getaddrinfo", return_value=[]), patch(
            "scripts.diagnostics.check_public_source_connectivity.build_opener"
        ) as build_opener:
            build_opener.return_value.open.side_effect = error
            result = diagnose_url("https://example.com/policy")
        self.assertEqual(result["dns_status"], "PASS")
        self.assertEqual(result["https_status"], "HTTP_ERROR")
        self.assertEqual(result["http_status"], 405)


if __name__ == "__main__":
    unittest.main()
