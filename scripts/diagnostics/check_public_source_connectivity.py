"""Diagnose DNS and HTTPS reachability without capturing source content.

This utility is read-only: it performs DNS lookups and one bounded HTTPS HEAD
request per URL. It does not alter network configuration or source approvals.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def diagnose_url(url: str, timeout_seconds: float = 5.0) -> dict:
    """Return a sanitized DNS/TLS/HTTP diagnostic for one HTTPS URL."""
    result = {
        "url": url,
        "host": None,
        "dns_status": "NOT_CHECKED",
        "https_status": "NOT_CHECKED",
        "http_status": None,
        "elapsed_ms": 0,
        "error_type": None,
    }
    parts = urlsplit(url) if isinstance(url, str) else None
    if (
        parts is None
        or parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.port not in (None, 443)
    ):
        result.update({"dns_status": "INVALID_URL", "https_status": "NOT_ATTEMPTED"})
        return result

    host = parts.hostname
    result["host"] = host
    started = time.monotonic()
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        result["dns_status"] = "PASS"
    except (socket.gaierror, OSError) as exc:
        result.update({
            "dns_status": "FAILED",
            "https_status": "NOT_ATTEMPTED",
            "error_type": type(exc).__name__,
        })
        result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        return result

    request = Request(
        url,
        method="HEAD",
        headers={"User-Agent": "CryptoIntelligenceConnectivityCheck/1.0", "Accept": "*/*"},
    )
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            result["http_status"] = int(response.status)
            result["https_status"] = "PASS" if 200 <= int(response.status) < 400 else "HTTP_ERROR"
    except HTTPError as exc:
        # HTTP 3xx/4xx/5xx still proves DNS + TLS + HTTP reachability.
        result["http_status"] = int(exc.code)
        result["https_status"] = "PASS" if 300 <= int(exc.code) < 400 else "HTTP_ERROR"
        result["error_type"] = "HTTPError"
        try:
            exc.close()
        except OSError:
            pass
    except (URLError, TimeoutError, OSError, ssl.SSLError) as exc:
        result["https_status"] = "FAILED"
        reason = getattr(exc, "reason", None)
        result["error_type"] = type(reason if isinstance(reason, BaseException) else exc).__name__
    result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="HTTPS URLs to check (maximum 20)")
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    args = parser.parse_args()
    if len(args.urls) > 20:
        parser.error("a maximum of 20 URLs is allowed")
    if not 0.1 <= args.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 0.1 and 30")
    results = [diagnose_url(url, args.timeout_seconds) for url in args.urls]
    print(json.dumps({
        "schema_version": "crypto-connectivity-diagnostic-v1",
        "network_configuration_changed": False,
        "source_authorization_changed": False,
        "results": results,
    }, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if all(r["dns_status"] == "PASS" and r["https_status"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
