"""Capture official source-policy pages byte-for-byte for Issue #132 review.

This utility captures policy pages only; it does not access feeds or articles and does
not approve any source. Bodies are read to EOF without a local size cap. Output should
be uploaded as a short-lived CI artifact, not committed automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ALLOWED_HOSTS = {"sec.gov", "www.sec.gov", "cftc.gov", "www.cftc.gov", "federalreserve.gov", "www.federalreserve.gov", "developers.binance.com"}

POLICY_URLS = {
    "sec_website_dissemination": "https://www.sec.gov/about/privacy-information",
    "sec_developer_resources": "https://www.sec.gov/about/developer-resources",
    "sec_webmaster_faq": "https://www.sec.gov/files/about/webmaster-faq.htm",
    "cftc_web_policy": "https://www.cftc.gov/WebPolicy/index.htm",
    "cftc_rss_status": "https://www.cftc.gov/RSS/index.htm",
    "federal_reserve_disclaimer": "https://www.federalreserve.gov/disclaimer.htm",
    "binance_spot_rest_api": "https://developers.binance.com/en/docs/products/spot/rest-api",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def capture(url: str, user_agent: str, timeout: float, attempts: int) -> tuple[dict, bytes | None]:
    parsed_url = urlsplit(url)
    if parsed_url.scheme != "https" or parsed_url.hostname not in ALLOWED_HOSTS or parsed_url.port not in (None, 443):
        return {"requested_url": url, "final_url": None, "captured_at": utc_now(), "http_status": None,
                "content_type": None, "last_modified": None, "etag": None, "response_headers": {},
                "attempts_used": 0, "body_bytes": 0, "body_sha256": hashlib.sha256(b"").hexdigest(),
                "capture_status": "BLOCKED_URL", "error": "URL must use HTTPS on an allowlisted official host."}, None
    last_error = None
    for attempt in range(1, attempts + 1):
        request = Request(url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}, method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
                status = int(getattr(response, "status", 200))
                headers = {str(k): str(v) for k, v in response.headers.items() if str(k).lower() not in {"set-cookie", "cookie", "authorization"}}
                final_parts = urlsplit(response.geturl())
                if final_parts.scheme != "https" or final_parts.hostname not in ALLOWED_HOSTS or final_parts.port not in (None, 443):
                    return {
                        "requested_url": url, "final_url": response.geturl(), "captured_at": utc_now(),
                        "http_status": status, "content_type": headers.get("Content-Type"),
                        "last_modified": headers.get("Last-Modified"), "etag": headers.get("ETag"),
                        "response_headers": headers, "attempts_used": attempt, "body_bytes": 0,
                        "body_sha256": hashlib.sha256(b"").hexdigest(), "capture_status": "BLOCKED_REDIRECT",
                        "error": "Redirect target is outside the official HTTPS host allowlist.",
                    }, None
                record = {
                    "requested_url": url,
                    "final_url": response.geturl(),
                    "captured_at": utc_now(),
                    "http_status": status,
                    "content_type": headers.get("Content-Type"),
                    "last_modified": headers.get("Last-Modified"),
                    "etag": headers.get("ETag"),
                    "response_headers": headers,
                    "attempts_used": attempt,
                    "body_bytes": len(body),
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                    "capture_status": "PASS" if status == 200 else "HTTP_ERROR",
                    "error": None,
                }
                return record, body
        except HTTPError as exc:
            body = exc.read()
            headers = {str(k): str(v) for k, v in (exc.headers.items() if exc.headers else [])}
            status = int(exc.code)
            # Reintentar solo errores transitorios; nunca tratarlos como aprobación.
            if status in {429, 500, 502, 503, 504} and attempt < attempts:
                retry_after = headers.get("Retry-After", "")
                try:
                    delay = min(max(float(retry_after), 0.0), 30.0) if retry_after else min(2 ** (attempt - 1), 8)
                except ValueError:
                    delay = min(2 ** (attempt - 1), 8)
                time.sleep(delay)
                continue
            return {
                "requested_url": url, "final_url": exc.geturl(), "captured_at": utc_now(),
                "http_status": status, "content_type": headers.get("Content-Type"),
                "last_modified": headers.get("Last-Modified"), "etag": headers.get("ETag"),
                "response_headers": headers, "attempts_used": attempt, "body_bytes": len(body),
                "body_sha256": hashlib.sha256(body).hexdigest(), "capture_status": "HTTP_ERROR",
                "error": str(exc),
            }, body
        except (URLError, TimeoutError, OSError, socket.gaierror) as exc:
            last_error = {"type": type(exc).__name__, "message": "Network request failed after bounded retries."}
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
    hostname = urlsplit(url).hostname
    dns_diagnostic = {"host": hostname, "resolved_addresses": [], "error": None}
    try:
        dns_diagnostic["resolved_addresses"] = sorted({item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)})
    except (OSError, socket.gaierror) as exc:
        dns_diagnostic["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return {
        "requested_url": url, "final_url": None, "captured_at": utc_now(),
        "http_status": None, "content_type": None, "last_modified": None, "etag": None,
        "response_headers": {}, "attempts_used": attempts, "body_bytes": 0,
        "body_sha256": hashlib.sha256(b"").hexdigest(), "capture_status": "NETWORK_ERROR",
        "dns_diagnostic": dns_diagnostic,
        "error": last_error,
    }, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()
    if not args.user_agent.strip() or "\r" in args.user_agent or "\n" in args.user_agent:
        parser.error("--user-agent must be a non-empty single-line identifier")
    if args.timeout_seconds <= 0 or args.attempts < 1:
        parser.error("--timeout-seconds must be positive and --attempts at least 1")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "crypto-source-policy-snapshot-manifest-v1",
        "captured_at": utc_now(),
        "purpose": "policy evidence only; not source approval or feed capture",
        "read_to_eof_without_local_size_cap": True,
        "sources": [],
    }
    for source_id, url in POLICY_URLS.items():
        record, body = capture(url, args.user_agent, args.timeout_seconds, args.attempts)
        record["source_id"] = source_id
        record["body_file"] = None
        if source_id == "binance_spot_rest_api" and record.get("http_status") == 202:
            # Binance's documentation CDN may challenge automated clients. Record the block,
            # but never preserve its challenge body as if it were policy text.
            record["capture_status"] = "AUTOMATION_CHALLENGE"
            record["manual_review_required"] = True
            record["policy_evidence_captured"] = False
            record["error"] = "Official documentation endpoint returned HTTP 202; no policy body accepted."
            body = None
        if body is not None and record["capture_status"] == "PASS":
            filename = f"{source_id}.html"
            (args.output_dir / filename).write_bytes(body)
            record["body_file"] = filename
        manifest["sources"].append(record)
        print(f"{source_id}: {record['capture_status']} bytes={record['body_bytes']} attempts={record['attempts_used']}")
    manifest["manual_review_required_sources"] = [
        item["source_id"] for item in manifest["sources"]
        if item.get("capture_status") == "AUTOMATION_CHALLENGE"
    ]
    manifest["overall_status"] = (
        "PARTIAL_MANUAL_REVIEW_REQUIRED"
        if manifest["manual_review_required_sources"]
        else "PASS"
    )
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    blocking_failures = [
        item for item in manifest["sources"]
        if item["capture_status"] != "PASS"
        and item.get("capture_status") != "AUTOMATION_CHALLENGE"
    ]
    return 0 if not blocking_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
