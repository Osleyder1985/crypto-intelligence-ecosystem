"""Capture one authorized public RSS/Atom feed as immutable candidate evidence.

This adapter never bypasses source/provider approval, never fetches linked articles,
and never promotes feed headlines into verified asset events. Terms-pending sources
are blocked before network access.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from typing import Any

from scripts.market_selection.event_source_registry import (
    get_source,
    source_entry_sha256,
)
from scripts.market_selection.external_event_evidence import parse_timestamp
from scripts.market_selection.provider_license_gate import (
    ASSESSMENT_SCHEMA_VERSION,
    evaluate_provider_use,
)

FEED_CAPTURE_SCHEMA = "crypto-public-event-feed-capture-v1"
_REQUIRED_USE_CASES = ("internal_analysis", "persistent_storage")
_RATE_LOCK = threading.Lock()
_LAST_REQUEST_MONOTONIC: dict[str, float] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_timestamp(value: str | None) -> str:
    if value is None:
        return _utc_now()
    return parse_timestamp(value, "captured_at").isoformat().replace("+00:00", "Z")


def _safe_headers(headers: Any) -> dict[str, str]:
    if headers is None or not hasattr(headers, "items"):
        return {}
    excluded = {"set-cookie", "authorization", "proxy-authorization", "www-authenticate"}
    return {
        str(key): str(value)
        for key, value in headers.items()
        if str(key).lower() not in excluded
    }


def _read_to_eof(stream: Any) -> tuple[bytes, Exception | None]:
    chunks: list[bytes] = []
    while True:
        try:
            chunk = stream.read(65536)
        except (URLError, TimeoutError, OSError) as exc:
            return b"".join(chunks), exc
        if not chunk:
            return b"".join(chunks), None
        if not isinstance(chunk, (bytes, bytearray)):
            return b"".join(chunks), TypeError("response stream returned a non-bytes chunk")
        chunks.append(bytes(chunk))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _direct_text(element: ET.Element, names: set[str]) -> str | None:
    for child in list(element):
        if _local_name(child.tag) in names:
            value = child.text
            if isinstance(value, str) and value.strip():
                return value.strip()
            if _local_name(child.tag) == "link":
                href = child.attrib.get("href")
                if isinstance(href, str) and href.strip():
                    return href.strip()
    return None


def _link_value(element: ET.Element) -> str | None:
    links = [child for child in list(element) if _local_name(child.tag) == "link"]
    for child in links:
        href = child.attrib.get("href")
        rel = child.attrib.get("rel", "alternate")
        if isinstance(href, str) and href.strip() and rel in {"alternate", ""}:
            return href.strip()
        if isinstance(child.text, str) and child.text.strip():
            return child.text.strip()
    return None


def _published_timestamp(value: str | None) -> tuple[str | None, str]:
    if not isinstance(value, str) or not value.strip():
        return None, "MISSING"
    raw = value.strip()
    try:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            parsed = parse_timestamp(raw, "published_at")
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None, "UNPARSEABLE_OR_TIMEZONE_MISSING"
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), "PARSED"
    except (TypeError, ValueError, OverflowError):
        return None, "UNPARSEABLE_OR_TIMEZONE_MISSING"


def _item_key(guid: str | None, link: str | None, title: str | None, published_at: str | None) -> str:
    if guid:
        return "guid:" + guid.strip().casefold()
    if link:
        return "url:" + link.strip().casefold()
    canonical = json.dumps(
        {"title": title or "", "published_at": published_at or ""},
        sort_keys=True,
        separators=(",", ":"),
    )
    return "content:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_feed(raw: bytes, source: dict) -> tuple[list[dict], int, int]:
    root = ET.fromstring(raw)
    nodes = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    seen: set[str] = set()
    items: list[dict] = []
    duplicates = 0
    for node in nodes:
        title = _direct_text(node, {"title"})
        link = _link_value(node) or _direct_text(node, {"link"})
        guid = _direct_text(node, {"guid", "id"})
        date_value = _direct_text(node, {"pubdate", "published", "updated", "date"})
        published_at, time_status = _published_timestamp(date_value)
        summary = _direct_text(node, {"description", "summary", "content", "encoded"})
        key = _item_key(guid, link, title, published_at)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        link_status = "MISSING"
        if link:
            parts = urlsplit(link)
            if parts.scheme not in {"http", "https"} or not parts.netloc:
                link_status = "INVALID_URL"
            elif (parts.hostname or "").casefold() not in allowed_hosts:
                link_status = "OUTSIDE_SOURCE_ALLOWLIST"
            else:
                link_status = "ALLOWLISTED_SOURCE_HOST"
        item_bytes = ET.tostring(node, encoding="utf-8")
        items.append({
            "candidate_id": hashlib.sha256(f"{source['source_id']}|{key}".encode("utf-8")).hexdigest(),
            "source_id": source["source_id"],
            "title": title,
            "url": link,
            "url_status": link_status,
            "guid": guid,
            "published_at": published_at,
            "publication_time_status": time_status,
            "summary": summary,
            "item_xml_sha256": hashlib.sha256(item_bytes).hexdigest(),
            "asset_identity_status": "NOT_RESOLVED",
            "event_verification_status": "CANDIDATE_ONLY",
        })
    return items, duplicates, len(nodes)


def _assessment(provider_id: str, use_case: str, authorization_record: dict | None) -> dict:
    try:
        return evaluate_provider_use(provider_id, use_case, authorization_record)
    except (TypeError, ValueError):
        return {
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "provider_id": provider_id,
            "use_case": use_case,
            "decision": "BLOCK",
            "reason_codes": ["AUTHORIZATION_RECORD_INVALID"],
            "authorization_evidence_status": "INVALID_RECORD",
        }


def _authorization_state(
    source_id: str,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float,
) -> tuple[dict, list[dict], list[str], str]:
    source = get_source(source_id)
    registry_hash = source_entry_sha256(source)
    assessments = [
        _assessment(source_id, use_case, authorization_record)
        for use_case in _REQUIRED_USE_CASES
    ]
    blockers: list[str] = []
    if source.get("status") != "APPROVED":
        blockers.append("SOURCE_TERMS_PENDING")
    source_parts = urlsplit(source.get("source_url", ""))
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    if source_parts.scheme != "https" or (source_parts.hostname or "").casefold() not in allowed_hosts:
        blockers.append("SOURCE_URL_OUTSIDE_ALLOWLIST")
    if not set(source.get("allowed_use_cases", [])).issuperset(_REQUIRED_USE_CASES):
        blockers.append("SOURCE_USE_CASES_NOT_APPROVED")
    if not isinstance(authorization_record, dict):
        blockers.append("AUTHORIZATION_RECORD_MISSING")
    else:
        if authorization_record.get("terms_url") != source.get("terms_url"):
            blockers.append("AUTHORIZATION_TERMS_URL_MISMATCH")
        if authorization_record.get("terms_sha256") != source.get("terms_sha256"):
            blockers.append("AUTHORIZATION_TERMS_HASH_MISMATCH")
    if source.get("user_agent_required"):
        if (
            not isinstance(user_agent, str)
            or not user_agent.strip()
            or "\r" in user_agent
            or "\n" in user_agent
        ):
            blockers.append("USER_AGENT_REQUIRED")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or timeout_seconds <= 0
    ):
        blockers.append("INVALID_TIMEOUT_SECONDS")
    for assessment in assessments:
        if assessment.get("decision") != "ALLOW":
            blockers.extend(assessment.get("reason_codes") or ["PROVIDER_USE_NOT_AUTHORIZED"])
    return source, assessments, sorted(set(blockers)), registry_hash


def _blocked_result(
    source: dict,
    registry_hash: str,
    captured_at: str,
    assessments: list[dict],
    blockers: list[str],
) -> dict:
    return {
        "schema_version": FEED_CAPTURE_SCHEMA,
        "source_id": source["source_id"],
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "captured_at": captured_at,
        "capture_status": "BLOCKED",
        "network_request_made": False,
        "orders_submitted": False,
        "events_promoted": False,
        "asset_identity_resolved": False,
        "http_status": None,
        "response_headers": {},
        "raw_response_bytes": 0,
        "raw_response_sha256": None,
        "raw_response_base64": None,
        "capture_truncated": False,
        "provider_policy_assessments": assessments,
        "reason_codes": blockers,
        "feed_items": [],
        "feed_item_count": 0,
        "unique_item_count": 0,
        "duplicate_item_count": 0,
        "errors": [],
    }


def _wait_for_rate_slot(source_id: str, requests_per_second: float) -> None:
    interval = 1.0 / requests_per_second
    with _RATE_LOCK:
        now = time.monotonic()
        last = _LAST_REQUEST_MONOTONIC.get(source_id)
        if last is not None:
            delay = interval - (now - last)
            if delay > 0:
                time.sleep(delay)
        _LAST_REQUEST_MONOTONIC[source_id] = time.monotonic()


def capture_public_event_feed(
    source_id: str,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float = 10.0,
    captured_at: str | None = None,
) -> dict:
    """Capture one registry-approved feed, or return BLOCKED without network access."""
    captured = _normalize_timestamp(captured_at)
    source, assessments, blockers, registry_hash = _authorization_state(
        source_id, authorization_record, user_agent, timeout_seconds
    )
    if blockers:
        return _blocked_result(source, registry_hash, captured, assessments, blockers)

    rate = source.get("max_requests_per_second")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        return _blocked_result(source, registry_hash, captured, assessments, ["INVALID_SOURCE_RATE_LIMIT"])
    _wait_for_rate_slot(source_id, rate)
    request = Request(
        source["source_url"],
        headers={
            "User-Agent": user_agent.strip(),
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9",
        },
        method="GET",
    )
    status_code: int | None = None
    headers: dict[str, str] = {}
    raw = b""
    read_error: Exception | None = None
    try:
        with urlopen(request, timeout=float(timeout_seconds)) as response:
            status_code = int(getattr(response, "status", 200))
            headers = _safe_headers(getattr(response, "headers", None))
            raw, read_error = _read_to_eof(response)
    except HTTPError as exc:
        status_code = int(exc.code)
        headers = _safe_headers(exc.headers)
        raw, read_error = _read_to_eof(exc)
        try:
            exc.close()
        except OSError:
            pass
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "schema_version": FEED_CAPTURE_SCHEMA,
            "source_id": source_id,
            "provider_id": source_id,
            "source_registry_status": source["status"],
            "source_registry_entry_sha256": registry_hash,
            "source_url": source["source_url"],
            "captured_at": captured,
            "capture_status": "NETWORK_ERROR",
            "network_request_made": True,
            "orders_submitted": False,
            "events_promoted": False,
            "asset_identity_resolved": False,
            "http_status": None,
            "response_headers": {},
            "raw_response_bytes": 0,
            "raw_response_sha256": hashlib.sha256(b"").hexdigest(),
            "raw_response_base64": "",
            "capture_truncated": False,
            "provider_policy_assessments": assessments,
            "reason_codes": ["NETWORK_REQUEST_FAILED"],
            "feed_items": [],
            "feed_item_count": 0,
            "unique_item_count": 0,
            "duplicate_item_count": 0,
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        }

    errors = []
    items: list[dict] = []
    duplicates = 0
    feed_item_count = 0
    reason_codes: list[str] = []
    if read_error is not None:
        capture_status = "PARTIAL"
        reason_codes.append("RESPONSE_READ_INCOMPLETE")
        errors.append({"type": type(read_error).__name__, "message": str(read_error)})
    elif status_code != 200:
        capture_status = "HTTP_ERROR"
        reason_codes.append("HTTP_STATUS_UNEXPECTED")
        errors.append({"type": "HTTP_STATUS", "message": f"unexpected HTTP status {status_code}"})
    else:
        try:
            items, duplicates, feed_item_count = _parse_feed(raw, source)
            captured_dt = parse_timestamp(captured, "captured_at")
            for item in items:
                if item.get("published_at") and parse_timestamp(item["published_at"], "published_at") > captured_dt:
                    item["publication_time_status"] = "AFTER_CAPTURE_CUTOFF"
            capture_status = "PASS"
        except (ET.ParseError, ValueError) as exc:
            capture_status = "PARSE_ERROR"
            reason_codes.append("FEED_PARSE_ERROR")
            errors.append({"type": type(exc).__name__, "message": str(exc)})

    return {
        "schema_version": FEED_CAPTURE_SCHEMA,
        "source_id": source_id,
        "provider_id": source_id,
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "publisher": source["display_name"],
        "source_type": source["source_type"],
        "coverage_scope": source["coverage_scope"],
        "captured_at": captured,
        "capture_status": capture_status,
        "network_request_made": True,
        "http_status": status_code,
        "response_headers": headers,
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_response_base64": base64.b64encode(raw).decode("ascii"),
        "capture_truncated": read_error is not None,
        "provider_policy_assessments": assessments,
        "reason_codes": reason_codes,
        "feed_items": items,
        "feed_item_count": feed_item_count,
        "unique_item_count": len(items),
        "duplicate_item_count": duplicates,
        "errors": errors,
        "events_promoted": False,
        "asset_identity_resolved": False,
        "orders_submitted": False,
        "network_requests_made": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True, help="Source ID from the deployment-controlled event source registry")
    parser.add_argument("--provider-authorization-registry", required=True, type=Path, help="Deployment-controlled provider authorization registry JSON")
    parser.add_argument("--user-agent", required=True, help="Identifiable operator-reviewed User-Agent")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--captured-at", help="Optional explicit ISO-8601 capture timestamp")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    registry = json.loads(args.provider_authorization_registry.read_text(encoding="utf-8"))
    record = registry.get(args.source_id) if isinstance(registry, dict) else None
    result = capture_public_event_feed(
        args.source_id,
        authorization_record=record,
        user_agent=args.user_agent,
        timeout_seconds=args.timeout_seconds,
        captured_at=args.captured_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "source_id": result["source_id"],
        "capture_status": result["capture_status"],
        "network_request_made": result["network_request_made"],
        "feed_item_count": result["feed_item_count"],
        "duplicate_item_count": result["duplicate_item_count"],
        "reason_codes": result["reason_codes"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
