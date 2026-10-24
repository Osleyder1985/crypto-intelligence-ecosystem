"""Capture official source-policy pages with retryable connectivity and byte-level evidence.

This utility captures policy pages only; it does not capture event feeds, approve a provider,
or grant permission to store/reuse provider content. Response bodies are read to EOF without
an application-level size cap. Redirects are restricted to the allowlisted official domains.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ALLOWED_HOSTS = {"sec.gov", "www.sec.gov", "cftc.gov", "www.cftc.gov", "federalreserve.gov", "www.federalreserve.gov"}
RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_url(url: str) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or (parts.hostname or "").casefold() not in ALLOWED_HOSTS
        or parts.username is not None
        or parts.password is not None
        or parts.port not in (None, 443)
    ):
        raise ValueError("URL must use HTTPS on an allowlisted official SEC, CFTC, or Federal Reserve host")


class AllowlistedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def capture_policy_page(
    url: str,
    output_dir: Path,
    user_agent: str,
    timeout_seconds: float = 20.0,
    retries: int = 3,
    backoff_seconds: float = 1.0,
    opener=None,
    sleep=time.sleep,
) -> dict:
    validate_url(url)
    if not isinstance(user_agent, str) or not user_agent.strip() or "\r" in user_agent or "\n" in user_agent:
        raise ValueError("a non-empty, single-line identifiable User-Agent is required")
    if timeout_seconds <= 0 or retries < 0 or backoff_seconds < 0:
        raise ValueError("timeout must be positive; retries and backoff must be non-negative")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    body_path = output_dir / "policy-response.bin"
    metadata_path = output_dir / "policy-evidence.json"
    client = opener or build_opener(AllowlistedRedirectHandler())
    attempts = []
    last_error = None
    for attempt in range(retries + 1):
        req = Request(
            url,
            headers={
                "User-Agent": user_agent.strip(),
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
            },
            method="GET",
        )
        # Keep transport exceptions separate from local persistence failures. Only
        # transport failures may trigger a retry; disk errors must never repeat GET.
        try:
            with client.open(req, timeout=float(timeout_seconds)) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read()
                headers = {
                    str(k): str(v)
                    for k, v in response.headers.items()
                    if str(k).lower() not in {"set-cookie", "authorization"}
                }
                final_url = response.geturl()
            validate_url(final_url)
            attempts.append({"attempt": attempt + 1, "http_status": status})
            if status in RETRYABLE_HTTP and attempt < retries:
                sleep(backoff_seconds * (2 ** attempt))
                continue
            last_error = None
            break
        except HTTPError as exc:
            attempts.append({"attempt": attempt + 1, "http_status": int(exc.code)})
            retryable = exc.code in RETRYABLE_HTTP
            try:
                exc.close()
            except OSError:
                pass
            if retryable and attempt < retries:
                sleep(backoff_seconds * (2 ** attempt))
                continue
            last_error = {
                "type": "HTTPError",
                "message": f"HTTP {exc.code}",
                "http_status": int(exc.code),
            }
            raw = None
            headers = {}
            final_url = None
            status = int(exc.code)
            break
        except (URLError, TimeoutError, socket.gaierror, OSError) as exc:
            attempts.append({
                "attempt": attempt + 1,
                "error_type": type(exc).__name__,
                "message": str(exc),
            })
            if attempt < retries:
                sleep(backoff_seconds * (2 ** attempt))
                continue
            last_error = {"type": type(exc).__name__, "message": str(exc)}
            raw = None
            headers = {}
            final_url = None
            status = None
            break

    if last_error is None:
        # Persistence deliberately sits outside the transport retry loop.
        # If disk write fails, propagate it rather than issuing another GET.
        _atomic_write(body_path, raw)
        result = {
            "schema_version": "official-source-policy-evidence-v1",
            "capture_status": "PASS" if status == 200 else "HTTP_ERROR",
            "requested_url": url,
            "final_url": final_url,
            "captured_at": utc_now(),
            "http_status": status,
            "response_headers": headers,
            "user_agent": user_agent.strip(),
            "attempts": attempts,
            "retry_count": len(attempts) - 1,
            "body_file": body_path.name,
            "body_bytes": len(raw),
            "body_sha256": hashlib.sha256(raw).hexdigest(),
            "read_to_eof": True,
            "application_size_limit_bytes": None,
            "provider_approved": False,
            "approval_note": "Evidence capture only; human review of scope, retention, attribution, and third-party content remains required.",
            "errors": [],
        }
    else:
        result = {
            "schema_version": "official-source-policy-evidence-v1",
            "capture_status": "NETWORK_ERROR" if "http_status" not in last_error else "HTTP_ERROR",
            "requested_url": url,
            "final_url": None,
            "captured_at": utc_now(),
            "http_status": last_error.get("http_status"),
            "response_headers": {},
            "user_agent": user_agent.strip(),
            "attempts": attempts,
            "retry_count": len(attempts) - 1,
            "body_file": None,
            "body_bytes": 0,
            "body_sha256": None,
            "read_to_eof": False,
            "application_size_limit_bytes": None,
            "provider_approved": False,
            "approval_note": "No policy body captured; do not approve the source from this result.",
            "errors": [last_error],
        }
    _atomic_write(
        metadata_path,
        (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\\n").encode("utf-8"),
    )
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Official policy URL on sec.gov, cftc.gov, or federalreserve.gov")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        result = capture_policy_page(args.url, args.output_dir, args.user_agent, args.timeout_seconds, args.retries, args.backoff_seconds)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["capture_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
