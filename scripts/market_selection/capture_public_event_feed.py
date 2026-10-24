"""Capture authorized public RSS/Atom feeds, linked articles, and historical archive evidence.

Every network request is gated by source/provider approval. Feed, archive-index, article,
entity-resolution, fact-review and causal-review evidence remain separate artifacts.
Terms-pending sources are blocked before network access.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import math
import json
from html.parser import HTMLParser
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
import socket
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import xml.etree.ElementTree as ET
from typing import Any

from scripts.market_selection.event_source_registry import (
    get_source,
    source_entry_sha256,
    source_is_approved,
)
from scripts.market_selection.external_event_evidence import (
    INPUT_SCHEMA as EVENT_SCHEMA,
    parse_timestamp,
    validate_event,
)
from scripts.market_selection.provider_license_gate import (
    ASSESSMENT_SCHEMA_VERSION,
    POLICY_VERSION,
    evaluate_artifact_use,
    evaluate_provider_use,
)

from scripts.market_selection.shared_request_rate_limiter import RateLimitCoordinationError, wait_for_rate_slot as _wait_for_rate_slot

FEED_CAPTURE_SCHEMA = "crypto-public-event-feed-capture-v1"
ARTICLE_CAPTURE_SCHEMA = "crypto-public-event-article-capture-v1"
ARCHIVE_CAPTURE_SCHEMA = "crypto-public-event-archive-capture-v1"
ARCHIVE_CANDIDATE_SCHEMA = "crypto-public-event-archive-candidate-v1"
_REQUIRED_USE_CASES = ("internal_analysis", "persistent_storage")
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


def _urlopen_with_transient_dns_retries(request: Request, timeout_seconds: float, attempts: int = 3):
    """Retry only DNS resolution failures; never retry HTTP responses or ambiguous timeouts."""
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError("attempts must be a positive integer")
    for attempt in range(attempts):
        try:
            return urlopen(request, timeout=float(timeout_seconds))
        except (URLError, OSError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            if not isinstance(reason, socket.gaierror) or attempt + 1 >= attempts:
                raise
            # DNS failed before an HTTP request could be sent. Short bounded backoff
            # helps transient resolver failures without retrying server-side failures.
            time.sleep(0.25 * (2 ** attempt))


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
        or not math.isfinite(timeout_seconds)
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
        "requested_url": source["source_url"],
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
        "provider_policy_assessments": assessments,
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
        "reason_codes": blockers,
        "feed_items": [],
        "feed_item_count": 0,
        "unique_item_count": 0,
        "duplicate_item_count": 0,
        "errors": [],
    }


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
        with _urlopen_with_transient_dns_retries(request, timeout_seconds) as response:
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
            "requested_url": source["source_url"],
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
            "provider_use_assessment": assessments[0],
            "persistent_storage_assessment": assessments[1],
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
        "requested_url": source["source_url"],
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
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
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



class _AllowlistedRedirectHandler(HTTPRedirectHandler):
    """Permit redirects only to HTTPS hosts explicitly allowed for the source."""

    def __init__(self, allowed_hosts: set[str], allowed_path_prefixes: list[str] | None = None):
        super().__init__()
        self.allowed_hosts = {host.casefold() for host in allowed_hosts}
        self.allowed_path_prefixes = list(allowed_path_prefixes or [])

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if (
            parts.scheme != "https"
            or (parts.hostname or "").casefold() not in self.allowed_hosts
            or parts.username is not None
            or parts.password is not None
            or parts.port not in (None, 443)
            or (
                self.allowed_path_prefixes
                and not any(_path_has_prefix(parts.path, prefix) for prefix in self.allowed_path_prefixes)
            )
        ):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_allowlisted_url(
    request: Request,
    timeout_seconds: float,
    allowed_hosts: set[str],
    allowed_path_prefixes: list[str] | None = None,
):
    opener = build_opener(_AllowlistedRedirectHandler(allowed_hosts, allowed_path_prefixes))
    return opener.open(request, timeout=float(timeout_seconds))



class _ArchiveHTMLParser(HTMLParser):
    """Extract archive navigation text while excluding embedded/third-party payloads.

    This parser is for derived evidence only. It does not itself authorize storing the
    original response; the source authorization gate remains mandatory.
    """
    _NON_TEXT_SUBTREES = {
        "script", "style", "noscript", "iframe", "frame", "frameset", "svg",
        "canvas", "video", "audio", "picture", "object", "embed", "template",
        "header", "footer", "nav", "aside",
    }
    _NON_TEXT_ELEMENTS = {"img", "source", "track"}

    def __init__(self, allowed_hosts=None):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.page_text = []
        self._anchor = None
        self._anchor_external = False
        self._allowed_hosts = {str(host).casefold() for host in (allowed_hosts or [])}
        self._suppressed_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        if self._suppressed_depth:
            if tag in self._NON_TEXT_SUBTREES:
                self._suppressed_depth += 1
            return
        if tag in self._NON_TEXT_SUBTREES:
            self._suppressed_depth = 1
            return
        if tag in self._NON_TEXT_ELEMENTS:
            return
        if tag == "a":
            attrs_map = dict(attrs)
            href = attrs_map.get("href")
            parts = urlsplit(href) if isinstance(href, str) else None
            self._anchor_external = bool(
                parts is not None
                and (
                    (parts.scheme and parts.scheme.casefold() not in {"http", "https"})
                    or (parts.netloc and (parts.hostname or "").casefold() not in self._allowed_hosts)
                )
            )
            self._anchor = {"href": href, "text": []}

    def handle_startendtag(self, tag, attrs):
        # Void elements carry no textual evidence and must not affect suppression depth.
        if tag.casefold() in self._NON_TEXT_ELEMENTS:
            return
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self._suppressed_depth:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if text and not self._anchor_external:
            self.page_text.append(text)
            if self._anchor is not None:
                self._anchor["text"].append(text)

    def handle_endtag(self, tag):
        tag = tag.casefold()
        if self._suppressed_depth:
            if tag in self._NON_TEXT_SUBTREES:
                self._suppressed_depth -= 1
            return
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = re.sub(r"\s+", " ", " ".join(self._anchor["text"])).strip()
            if not self._anchor_external:
                self.anchors.append(self._anchor)
            self._anchor = None
            self._anchor_external = False


def _archive_text_evidence(raw: bytes, allowed_hosts=None) -> dict:
    """Extract visible text while excluding embedded payloads and external-link labels."""
    parser = _ArchiveHTMLParser(allowed_hosts=allowed_hosts)
    parser.feed(raw.decode("utf-8", errors="replace"))
    parser.close()
    return {
        "schema_version": "official-archive-text-evidence-v1",
        "anchors": parser.anchors,
        "page_text": parser.page_text,
    }


def _load_archive_text_evidence(capture: dict) -> dict:
    """Load and verify derived text evidence, or derive it from a retained full response."""
    mode = capture.get("stored_content_mode", "FULL_RESPONSE")
    if mode == "EXTRACTED_TEXT_EVIDENCE":
        encoded = capture.get("text_evidence_base64")
        expected_hash = capture.get("text_evidence_sha256")
        expected_size = capture.get("text_evidence_bytes")
        if not isinstance(encoded, str):
            raise PermissionError("archive extracted text evidence is missing")
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise PermissionError("archive extracted text evidence is invalid base64") from exc
        if hashlib.sha256(payload).hexdigest() != expected_hash or len(payload) != expected_size:
            raise PermissionError("archive extracted text evidence integrity check failed")
        try:
            parsed = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PermissionError("archive extracted text evidence is not valid JSON") from exc
        if (
            not isinstance(parsed, dict)
            or parsed.get("schema_version") != "official-archive-text-evidence-v1"
            or not isinstance(parsed.get("anchors"), list)
            or not isinstance(parsed.get("page_text"), list)
        ):
            raise PermissionError("archive extracted text evidence schema is invalid")
        return parsed
    raw_b64 = capture.get("raw_response_base64")
    if not isinstance(raw_b64, str):
        raise PermissionError("archive capture body is missing")
    try:
        raw = base64.b64decode(raw_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("archive capture body base64 is invalid") from exc
    if hashlib.sha256(raw).hexdigest() != capture.get("raw_response_sha256") or len(raw) != capture.get("raw_response_bytes"):
        raise PermissionError("archive capture body integrity check failed")
    source = get_source(capture.get("source_id"))
    return _archive_text_evidence(raw, allowed_hosts=source.get("allowed_article_hosts"))


def _store_response_body_fields(source: dict, raw: bytes, *, html: bool) -> dict:
    """Hash the complete response but persist only derived text when source policy requires it."""
    fields = {
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "capture_truncated": False,
    }
    if source.get("response_storage_mode") == "EXTRACTED_TEXT_EVIDENCE" and html:
        payload = json.dumps(
            _archive_text_evidence(raw, allowed_hosts=source.get("allowed_article_hosts")),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        fields.update({
            "stored_content_mode": "EXTRACTED_TEXT_EVIDENCE",
            "raw_response_base64": None,
            "text_evidence_base64": base64.b64encode(payload).decode("ascii"),
            "text_evidence_sha256": hashlib.sha256(payload).hexdigest(),
            "text_evidence_bytes": len(payload),
        })
    elif source.get("response_storage_mode") == "EXTRACTED_TEXT_EVIDENCE":
        fields.update({
            "stored_content_mode": "UNSUPPORTED_CONTENT_NOT_PERSISTED",
            "raw_response_base64": None,
            "text_evidence_base64": None,
            "text_evidence_sha256": None,
            "text_evidence_bytes": None,
        })
    else:
        fields.update({
            "stored_content_mode": "FULL_RESPONSE",
            "raw_response_base64": base64.b64encode(raw).decode("ascii"),
            "text_evidence_base64": None,
            "text_evidence_sha256": None,
            "text_evidence_bytes": None,
        })
    return fields


def _path_has_prefix(path: str, prefix: str) -> bool:
    normalized = prefix.rstrip("/")
    return path == normalized or path.startswith(normalized + "/")


def _archive_url_allowed(source: dict, value: object) -> bool:
    parts = urlsplit(value) if isinstance(value, str) else None
    prefixes = source.get("allowed_archive_path_prefixes", [])
    hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    return bool(
        parts is not None
        and parts.scheme == "https"
        and (parts.hostname or "").casefold() in hosts
        and parts.port in (None, 443)
        and parts.username is None
        and parts.password is None
        and any(_path_has_prefix(parts.path, prefix) for prefix in prefixes)
    )


def capture_public_event_archive_index(
    source_id: str,
    archive_url: str,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float = 10.0,
    captured_at: str | None = None,
) -> dict:
    """Capture one explicitly allowlisted official archive page, preserving all bytes."""
    captured = _normalize_timestamp(captured_at)
    source, assessments, blockers, registry_hash = _authorization_state(
        source_id, authorization_record, user_agent, timeout_seconds
    )
    result = {
        "schema_version": ARCHIVE_CAPTURE_SCHEMA,
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "requested_url": archive_url,
        "final_url": None,
        "captured_at": captured,
        "capture_status": "BLOCKED",
        "network_request_made": False,
        "http_status": None,
        "response_headers": {},
        "content_type": None,
        "raw_response_bytes": 0,
        "raw_response_sha256": None,
        "raw_response_base64": None,
        "capture_truncated": False,
        "provider_policy_assessments": assessments,
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
        "reason_codes": list(blockers),
        "errors": [],
        "coverage_scope": source.get("coverage_scope"),
    }
    if blockers:
        return result
    if not _archive_url_allowed(source, archive_url):
        result["reason_codes"].append("ARCHIVE_URL_OUTSIDE_ALLOWLIST")
        return result
    rate = source.get("max_requests_per_second")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        result["reason_codes"].append("INVALID_SOURCE_RATE_LIMIT")
        return result
    _wait_for_rate_slot(source_id, rate)
    request = Request(
        archive_url,
        headers={"User-Agent": user_agent.strip(), "Accept": "text/html, application/xhtml+xml"},
        method="GET",
    )
    status_code = None
    headers = {}
    raw = b""
    read_error = None
    final_url = archive_url
    try:
        with _open_allowlisted_url(
            request, float(timeout_seconds), set(source["allowed_article_hosts"]),
            source.get("allowed_archive_path_prefixes", []),
        ) as response:
            status_code = int(getattr(response, "status", 200))
            headers = _safe_headers(getattr(response, "headers", None))
            geturl = getattr(response, "geturl", None)
            if callable(geturl):
                final_url = geturl()
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
        result.update({
            "capture_status": "NETWORK_ERROR",
            "network_request_made": True,
            "reason_codes": ["ARCHIVE_REQUEST_FAILED"],
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        })
        return result
    result.update({
        "network_request_made": True,
        "http_status": status_code,
        "response_headers": headers,
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
        "final_url": final_url,
        **_store_response_body_fields(
            source,
            raw,
            html=(headers.get("Content-Type") or headers.get("content-type") or "").split(";", 1)[0].strip().lower()
            in {"text/html", "application/xhtml+xml"},
        ),
        "capture_truncated": read_error is not None,
    })
    final_ok = _archive_url_allowed(source, final_url)
    if read_error is not None:
        result["capture_status"] = "PARTIAL"
        result["reason_codes"] = ["RESPONSE_READ_INCOMPLETE"]
        result["errors"] = [{"type": type(read_error).__name__, "message": str(read_error)}]
    elif status_code != 200:
        result["capture_status"] = "HTTP_ERROR"
        result["reason_codes"] = ["HTTP_STATUS_UNEXPECTED"]
        result["errors"] = [{"type": "HTTP_STATUS", "message": f"unexpected HTTP status {status_code}"}]
    elif not final_ok:
        result["capture_status"] = "BLOCKED_REDIRECT_TARGET"
        result["reason_codes"] = ["FINAL_URL_OUTSIDE_ALLOWLIST"]
    elif not isinstance(result["content_type"], str) or result["content_type"].split(";", 1)[0].strip().lower() not in {"text/html", "application/xhtml+xml"}:
        result["capture_status"] = "UNSUPPORTED_CONTENT_TYPE"
        result["reason_codes"] = ["ARCHIVE_CONTENT_TYPE_UNSUPPORTED"]
    else:
        result["capture_status"] = "PASS"
        result["reason_codes"] = []
    return result


def validate_public_event_archive_candidate(archive_capture: dict, candidate_record: dict) -> dict:
    """Revalidate a manually selected archive candidate against the preserved index bytes."""
    if not isinstance(archive_capture, dict) or archive_capture.get("schema_version") != ARCHIVE_CAPTURE_SCHEMA:
        raise ValueError("archive_capture has an invalid schema")
    source_id = archive_capture.get("source_id")
    source = get_source(source_id)
    current_hash = source_entry_sha256(source)
    if (
        archive_capture.get("capture_status") != "PASS"
        or archive_capture.get("capture_truncated") is not False
        or archive_capture.get("network_request_made") is not True
        or archive_capture.get("http_status") != 200
        or archive_capture.get("source_registry_status") != "APPROVED"
        or archive_capture.get("source_registry_entry_sha256") != current_hash
        or not source_is_approved(source)
        or not _archive_url_allowed(source, archive_capture.get("requested_url"))
        or not _archive_url_allowed(source, archive_capture.get("final_url"))
    ):
        raise PermissionError("archive capture is incomplete, stale, or outside the approved archive path")
    text_evidence = _load_archive_text_evidence(archive_capture)
    if not isinstance(candidate_record, dict) or candidate_record.get("schema_version") != ARCHIVE_CANDIDATE_SCHEMA:
        raise ValueError("candidate_record has an invalid schema")
    if (
        candidate_record.get("source_id") != source_id
        or candidate_record.get("archive_url") != archive_capture.get("requested_url")
        or candidate_record.get("archive_capture_sha256") != archive_capture.get("raw_response_sha256")
    ):
        raise PermissionError("archive candidate does not match the preserved archive capture")
    candidate_url = candidate_record.get("candidate_url")
    parts = urlsplit(candidate_url) if isinstance(candidate_url, str) else None
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    if (
        parts is None or parts.scheme != "https" or (parts.hostname or "").casefold() not in allowed_hosts
        or parts.port not in (None, 443) or parts.username is not None or parts.password is not None
    ):
        raise PermissionError("archive candidate URL is outside the source host allowlist")
    title = candidate_record.get("title")
    date_evidence = candidate_record.get("publication_time_evidence")
    if not isinstance(title, str) or not title.strip() or not isinstance(date_evidence, str) or not date_evidence.strip():
        raise ValueError("archive candidate title and publication_time_evidence are required")
    published = parse_timestamp(candidate_record.get("published_at"), "archive_candidate.published_at")
    selected_by = candidate_record.get("selected_by")
    selected_at = parse_timestamp(candidate_record.get("selected_at"), "archive_candidate.selected_at")
    rationale = candidate_record.get("selection_rationale")
    if not isinstance(selected_by, str) or not selected_by.strip() or not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("archive candidate requires selected_by and selection_rationale")
    if selected_at < parse_timestamp(archive_capture["captured_at"], "archive_capture.captured_at"):
        raise ValueError("archive candidate selection cannot precede archive capture")
    if published > parse_timestamp(archive_capture["captured_at"], "archive_capture.captured_at"):
        raise ValueError("archive candidate publication timestamp is after archive capture")
    parser = _ArchiveHTMLParser()
    parser.anchors = text_evidence["anchors"]
    parser.page_text = text_evidence["page_text"]
    archive_url = archive_capture["requested_url"]
    archive_base_url = archive_capture.get("final_url") or archive_url
    candidate_url_canonical = candidate_url.split("#", 1)[0]
    matching_anchors = []
    for anchor in parser.anchors:
        href = anchor.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        absolute = urljoin(archive_base_url, href.strip()).split("#", 1)[0]
        if absolute == candidate_url_canonical:
            matching_anchors.append(anchor)
    normalize_text = lambda value: re.sub(r"\s+", " ", value).strip().casefold()
    title_norm = normalize_text(title)
    if not matching_anchors or not any(title_norm in normalize_text(anchor.get("text", "")) for anchor in matching_anchors):
        raise PermissionError("candidate URL/title is not present as an anchor in the preserved archive page")
    page_text = normalize_text(" ".join(parser.page_text))
    if normalize_text(date_evidence) not in page_text:
        raise PermissionError("publication_time_evidence is not present in the preserved archive page")
    identity = {
        "schema_version": ARCHIVE_CANDIDATE_SCHEMA,
        "source_id": source_id,
        "archive_url": archive_capture["requested_url"],
        "archive_capture_sha256": archive_capture["raw_response_sha256"],
        "candidate_url": candidate_url_canonical,
        "title": title.strip(),
        "published_at": published.isoformat().replace("+00:00", "Z"),
        "publication_time_evidence": date_evidence.strip(),
        "selected_by": selected_by.strip(),
        "selected_at": selected_at.isoformat().replace("+00:00", "Z"),
        "selection_rationale": rationale.strip(),
    }
    expected_id = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    if candidate_record.get("candidate_id") != expected_id:
        raise PermissionError("archive candidate ID does not match its evidence and selection review fields")
    return {**identity, "candidate_id": expected_id}



ARCHIVE_COVERAGE_MANIFEST_SCHEMA = "crypto-public-event-archive-coverage-manifest-v1"


def build_public_event_archive_coverage_manifest(
    source_id: str,
    scope_id: str,
    scope_definition: str,
    expected_partitions: list[dict],
    segments: list[dict],
    reviewed_by: str,
    reviewed_at: str,
) -> dict:
    """Create an auditable coverage ledger without overstating archive completeness."""
    source = get_source(source_id)
    current_hash = source_entry_sha256(source)
    if not source_is_approved(source):
        raise PermissionError("archive coverage manifest requires an APPROVED source")
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise ValueError("scope_id is required")
    if not isinstance(scope_definition, str) or not scope_definition.strip():
        raise ValueError("scope_definition must state the exact archive/time/filter scope")
    if not isinstance(reviewed_by, str) or not reviewed_by.strip():
        raise ValueError("reviewed_by is required")
    reviewed_time = parse_timestamp(reviewed_at, "reviewed_at")
    if not isinstance(expected_partitions, list) or not expected_partitions:
        raise ValueError("expected_partitions must declare at least one partition")
    partition_map = {}
    for partition in expected_partitions:
        if not isinstance(partition, dict):
            raise ValueError("each expected partition must be an object")
        partition_id = partition.get("partition_id")
        page_count = partition.get("page_count")
        period_start = partition.get("period_start")
        period_end = partition.get("period_end")
        if not isinstance(partition_id, str) or not partition_id.strip():
            raise ValueError("partition_id is required")
        if partition_id in partition_map:
            raise ValueError("partition_id values must be unique")
        if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 1:
            raise ValueError("page_count must be a positive integer")
        if not isinstance(period_start, str) or not period_start.strip() or not isinstance(period_end, str) or not period_end.strip():
            raise ValueError("period_start and period_end must declare the partition scope")
        partition_map[partition_id] = {
            "partition_id": partition_id,
            "page_count": page_count,
            "period_start": period_start.strip(),
            "period_end": period_end.strip(),
        }
    if not isinstance(segments, list):
        raise ValueError("segments must be a list")
    normalized_segments = []
    seen_pages = set()
    seen_urls = set()
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segments[{index}] must be an object")
        capture = segment.get("archive_capture")
        if not isinstance(capture, dict) or capture.get("schema_version") != ARCHIVE_CAPTURE_SCHEMA:
            raise ValueError(f"segments[{index}].archive_capture has an invalid schema")
        if (
            capture.get("source_id") != source_id
            or capture.get("capture_status") != "PASS"
            or capture.get("capture_truncated") is not False
            or capture.get("network_request_made") is not True
            or capture.get("http_status") != 200
            or capture.get("source_registry_status") != "APPROVED"
            or capture.get("source_registry_entry_sha256") != current_hash
            or not _archive_url_allowed(source, capture.get("requested_url"))
            or not _archive_url_allowed(source, capture.get("final_url"))
        ):
            raise PermissionError(f"segments[{index}] is not a complete capture from the currently approved archive source")
        try:
            _load_archive_text_evidence(capture)
        except PermissionError as exc:
            raise PermissionError(f"segments[{index}] stored evidence integrity check failed: {exc}") from exc
        if (
            isinstance(capture.get("raw_response_bytes"), bool)
            or not isinstance(capture.get("raw_response_bytes"), int)
            or capture.get("raw_response_bytes") < 0
            or not isinstance(capture.get("raw_response_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", capture.get("raw_response_sha256", ""))
        ):
            raise PermissionError(f"segments[{index}] original response hash/byte count is invalid")
        partition_id = segment.get("partition_id")
        page_index = segment.get("page_index")
        expected_page_count = segment.get("expected_page_count")
        if partition_id not in partition_map:
            raise ValueError(f"segments[{index}] references an undeclared partition")
        partition = partition_map[partition_id]
        if (
            isinstance(page_index, bool) or not isinstance(page_index, int) or page_index < 1
            or isinstance(expected_page_count, bool) or not isinstance(expected_page_count, int)
            or expected_page_count != partition["page_count"] or page_index > expected_page_count
        ):
            raise ValueError(f"segments[{index}] page index/count disagrees with the declared partition")
        page_key = (partition_id, page_index)
        if page_key in seen_pages:
            raise ValueError("duplicate partition/page index in archive coverage manifest")
        requested_url = capture.get("requested_url")
        if requested_url in seen_urls:
            raise ValueError("duplicate archive URL in coverage manifest")
        seen_pages.add(page_key)
        seen_urls.add(requested_url)
        normalized_segments.append({
            "partition_id": partition_id,
            "page_index": page_index,
            "expected_page_count": expected_page_count,
            "requested_url": requested_url,
            "final_url": capture.get("final_url"),
            "captured_at": capture.get("captured_at"),
            "http_status": capture.get("http_status"),
            "raw_response_bytes": capture.get("raw_response_bytes"),
            "raw_response_sha256": capture.get("raw_response_sha256"),
            "stored_content_mode": capture.get("stored_content_mode", "FULL_RESPONSE"),
            "text_evidence_sha256": capture.get("text_evidence_sha256"),
            "text_evidence_bytes": capture.get("text_evidence_bytes"),
        })
    normalized_segments.sort(key=lambda item: (item["partition_id"], item["page_index"]))
    missing_pages = []
    for partition_id, partition in partition_map.items():
        for page_index in range(1, partition["page_count"] + 1):
            if (partition_id, page_index) not in seen_pages:
                missing_pages.append({"partition_id": partition_id, "page_index": page_index})
    status = "COMPLETE_FOR_DECLARED_SCOPE" if not missing_pages else "PARTIAL"
    manifest = {
        "schema_version": ARCHIVE_COVERAGE_MANIFEST_SCHEMA,
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": current_hash,
        "scope_id": scope_id.strip(),
        "scope_definition": scope_definition.strip(),
        "coverage_status": status,
        "completeness_claim_scope": "DECLARED_SCOPE_ONLY" if not missing_pages else "NONE",
        "expected_partitions": [partition_map[key] for key in sorted(partition_map)],
        "captured_segment_count": len(normalized_segments),
        "expected_segment_count": sum(item["page_count"] for item in partition_map.values()),
        "missing_pages": missing_pages,
        "segments": normalized_segments,
        "reviewed_by": reviewed_by.strip(),
        "reviewed_at": reviewed_time.isoformat().replace("+00:00", "Z"),
        "global_archive_exhaustiveness_claimed": False,
        "orders_submitted": False,
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return manifest



def select_public_event_archive_candidate(
    archive_capture: dict,
    *,
    candidate_url: str,
    title: str,
    published_at: str,
    publication_time_evidence: str,
    selected_by: str,
    selected_at: str,
    selection_rationale: str,
) -> dict:
    """Create a reviewed archive candidate only when URL/title/date evidence is in the preserved page."""
    source = get_source(archive_capture.get("source_id"))
    raw_hash = archive_capture.get("raw_response_sha256")
    published = parse_timestamp(published_at, "published_at")
    selected_at_normalized = parse_timestamp(selected_at, "selected_at").isoformat().replace("+00:00", "Z")
    identity = {
        "schema_version": ARCHIVE_CANDIDATE_SCHEMA,
        "source_id": archive_capture.get("source_id"),
        "archive_url": archive_capture.get("requested_url"),
        "archive_capture_sha256": raw_hash,
        "candidate_url": candidate_url.split("#", 1)[0] if isinstance(candidate_url, str) else candidate_url,
        "title": title.strip() if isinstance(title, str) else title,
        "published_at": published.isoformat().replace("+00:00", "Z"),
        "publication_time_evidence": publication_time_evidence.strip() if isinstance(publication_time_evidence, str) else publication_time_evidence,
        "selected_by": selected_by.strip() if isinstance(selected_by, str) else selected_by,
        "selected_at": selected_at_normalized,
        "selection_rationale": selection_rationale.strip() if isinstance(selection_rationale, str) else selection_rationale,
    }
    candidate_id = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    candidate = {**identity, "candidate_id": candidate_id}
    return validate_public_event_archive_candidate(archive_capture, candidate)



def _blocked_article_result(
    source: dict,
    registry_hash: str,
    candidate_id: str,
    captured_at: str,
    assessments: list[dict],
    blockers: list[str],
) -> dict:
    return {
        "schema_version": ARTICLE_CAPTURE_SCHEMA,
        "source_id": source["source_id"],
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "candidate_id": candidate_id,
        "requested_url": None,
        "final_url": None,
        "captured_at": captured_at,
        "capture_status": "BLOCKED",
        "network_request_made": False,
        "http_status": None,
        "response_headers": {},
        "content_type": None,
        "raw_response_bytes": 0,
        "raw_response_sha256": None,
        "raw_response_base64": None,
        "capture_truncated": False,
        "provider_policy_assessments": assessments,
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
        "reason_codes": blockers,
        "errors": [],
    }


def capture_public_event_article(
    feed_capture: dict,
    candidate_id: str,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float = 10.0,
    captured_at: str | None = None,
) -> dict:
    """Capture one allowlisted article only after source/use authorization passes.

    The full response body is preserved to EOF and hashed. Redirects are followed only
    when the destination remains HTTPS and within the source's explicit host allowlist.
    This function never resolves an asset or claims that the article caused a market move.
    """
    if not isinstance(feed_capture, dict) or feed_capture.get("schema_version") != FEED_CAPTURE_SCHEMA:
        raise ValueError("feed_capture has an invalid schema")
    source_id = feed_capture.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("feed_capture.source_id is required")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("candidate_id is required")
    captured = _normalize_timestamp(captured_at)
    source, assessments, blockers, registry_hash = _authorization_state(
        source_id, authorization_record, user_agent, timeout_seconds
    )
    if blockers:
        return _blocked_article_result(source, registry_hash, candidate_id, captured, assessments, blockers)
    if (
        feed_capture.get("capture_status") != "PASS"
        or feed_capture.get("capture_truncated") is not False
        or feed_capture.get("network_request_made") is not True
    ):
        raise PermissionError("article capture requires a complete successful feed capture")
    if (
        feed_capture.get("source_registry_status") != "APPROVED"
        or feed_capture.get("source_registry_entry_sha256") != registry_hash
        or feed_capture.get("source_url") != source["source_url"]
    ):
        raise PermissionError("feed source registry evidence is missing or stale")
    for use_case in _REQUIRED_USE_CASES:
        if evaluate_artifact_use(feed_capture, use_case)["decision"] != "ALLOW":
            raise PermissionError(f"feed capture does not authorize {use_case}")
    raw_b64 = feed_capture.get("raw_response_base64")
    if not isinstance(raw_b64, str):
        raise PermissionError("feed capture raw response is missing")
    try:
        feed_raw = base64.b64decode(raw_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("feed capture raw response base64 is invalid") from exc
    if (
        hashlib.sha256(feed_raw).hexdigest() != feed_capture.get("raw_response_sha256")
        or len(feed_raw) != feed_capture.get("raw_response_bytes")
    ):
        raise PermissionError("feed capture body integrity check failed")
    try:
        parsed_items, _, _ = _parse_feed(feed_raw, source)
    except (ET.ParseError, ValueError) as exc:
        raise PermissionError("feed capture is not valid RSS/Atom") from exc
    candidate = next((item for item in parsed_items if item.get("candidate_id") == candidate_id), None)
    if candidate is None:
        raise ValueError("candidate_id was not present in preserved feed bytes")
    if candidate.get("url_status") != "ALLOWLISTED_SOURCE_HOST":
        raise PermissionError("candidate URL is outside the source host allowlist")
    if candidate.get("publication_time_status") != "PARSED" or not candidate.get("published_at"):
        raise ValueError("candidate has no eligible publication timestamp")
    feed_captured = parse_timestamp(feed_capture.get("captured_at"), "feed_capture.captured_at")
    article_captured = parse_timestamp(captured, "captured_at")
    if article_captured < feed_captured:
        raise ValueError("article captured_at cannot precede feed captured_at")
    published = parse_timestamp(candidate["published_at"], "candidate.published_at")
    if published > feed_captured:
        raise ValueError("candidate publication timestamp is after the feed capture cutoff")
    article_url = candidate.get("url")
    parts = urlsplit(article_url) if isinstance(article_url, str) else None
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    if (
        parts is None
        or parts.scheme != "https"
        or (parts.hostname or "").casefold() not in allowed_hosts
        or parts.port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
    ):
        raise PermissionError("candidate URL is outside the approved HTTPS host allowlist")

    rate = source.get("max_requests_per_second")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        return _blocked_article_result(source, registry_hash, candidate_id, captured, assessments, ["INVALID_SOURCE_RATE_LIMIT"])
    _wait_for_rate_slot(source_id, rate)
    request = Request(
        article_url,
        headers={"User-Agent": user_agent.strip(), "Accept": "text/html, application/xhtml+xml, application/pdf;q=0.8, */*;q=0.5"},
        method="GET",
    )
    status_code: int | None = None
    headers: dict[str, str] = {}
    raw = b""
    read_error: Exception | None = None
    final_url = article_url
    try:
        with _open_allowlisted_url(request, float(timeout_seconds), allowed_hosts) as response:
            status_code = int(getattr(response, "status", 200))
            headers = _safe_headers(getattr(response, "headers", None))
            geturl = getattr(response, "geturl", None)
            if callable(geturl):
                final_url = geturl()
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
            **_blocked_article_result(source, registry_hash, candidate_id, captured, assessments, ["ARTICLE_REQUEST_FAILED"]),
            "capture_status": "NETWORK_ERROR",
            "network_request_made": True,
            "requested_url": article_url,
            "final_url": None,
            "raw_response_sha256": hashlib.sha256(b"").hexdigest(),
            "raw_response_base64": "",
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        }

    reason_codes: list[str] = []
    errors: list[dict] = []
    if read_error is not None:
        status = "PARTIAL"
        reason_codes.append("RESPONSE_READ_INCOMPLETE")
        errors.append({"type": type(read_error).__name__, "message": str(read_error)})
    elif status_code != 200:
        status = "HTTP_ERROR"
        reason_codes.append("HTTP_STATUS_UNEXPECTED")
        errors.append({"type": "HTTP_STATUS", "message": f"unexpected HTTP status {status_code}"})
    else:
        final_parts = urlsplit(final_url)
        if (
            final_parts.scheme != "https"
            or (final_parts.hostname or "").casefold() not in allowed_hosts
            or final_parts.username is not None
            or final_parts.password is not None
            or final_parts.port not in (None, 443)
        ):
            status = "BLOCKED_REDIRECT_TARGET"
            reason_codes.append("FINAL_URL_OUTSIDE_ALLOWLIST")
        else:
            status = "PASS"
    return {
        "schema_version": ARTICLE_CAPTURE_SCHEMA,
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "candidate_id": candidate_id,
        "requested_url": article_url,
        "final_url": final_url,
        "captured_at": captured,
        "capture_status": status,
        "network_request_made": True,
        "http_status": status_code,
        "response_headers": headers,
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_response_base64": base64.b64encode(raw).decode("ascii"),
        "capture_truncated": read_error is not None,
        "provider_policy_assessments": assessments,
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
        "reason_codes": reason_codes,
        "errors": errors,
    }



def capture_public_event_archive_article(
    archive_capture: dict,
    candidate_record: dict,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float = 10.0,
    captured_at: str | None = None,
) -> dict:
    """Capture the article linked by a validated official archive candidate."""
    if not isinstance(archive_capture, dict) or archive_capture.get("schema_version") != ARCHIVE_CAPTURE_SCHEMA:
        raise ValueError("archive_capture has an invalid schema")
    source_id = archive_capture.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("archive_capture.source_id is required")
    captured = _normalize_timestamp(captured_at)
    source, assessments, blockers, registry_hash = _authorization_state(
        source_id, authorization_record, user_agent, timeout_seconds
    )
    candidate_id = candidate_record.get("candidate_id", "unvalidated-candidate") if isinstance(candidate_record, dict) else "unvalidated-candidate"
    if blockers:
        return _blocked_article_result(source, registry_hash, candidate_id, captured, assessments, blockers)
    candidate = validate_public_event_archive_candidate(archive_capture, candidate_record)
    if candidate["source_id"] != source_id:
        raise PermissionError("archive candidate source ID does not match archive capture")
    if archive_capture.get("source_registry_entry_sha256") != registry_hash:
        raise PermissionError("archive capture source registry evidence is stale")
    for use_case in _REQUIRED_USE_CASES:
        if evaluate_artifact_use(archive_capture, use_case)["decision"] != "ALLOW":
            raise PermissionError(f"archive capture does not authorize {use_case}")
    archive_captured = parse_timestamp(archive_capture.get("captured_at"), "archive_capture.captured_at")
    article_captured = parse_timestamp(captured, "captured_at")
    published = parse_timestamp(candidate["published_at"], "candidate.published_at")
    if article_captured < archive_captured or article_captured < published:
        raise ValueError("article capture time precedes archive capture or publication time")
    article_url = candidate["candidate_url"]
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    if not _archive_url_allowed(source, archive_capture.get("requested_url")):
        raise PermissionError("archive index URL is outside the approved archive path")
    parts = urlsplit(article_url)
    if (
        parts.scheme != "https" or (parts.hostname or "").casefold() not in allowed_hosts
        or parts.port not in (None, 443) or parts.username is not None or parts.password is not None
    ):
        raise PermissionError("archive article URL is outside the approved HTTPS host allowlist")
    rate = source.get("max_requests_per_second")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        return _blocked_article_result(source, registry_hash, candidate["candidate_id"], captured, assessments, ["INVALID_SOURCE_RATE_LIMIT"])
    _wait_for_rate_slot(source_id, rate)
    request = Request(
        article_url,
        headers={"User-Agent": user_agent.strip(), "Accept": "text/html, application/xhtml+xml"},
        method="GET",
    )
    status_code = None
    headers = {}
    raw = b""
    read_error = None
    final_url = article_url
    try:
        with _open_allowlisted_url(request, float(timeout_seconds), allowed_hosts) as response:
            status_code = int(getattr(response, "status", 200))
            headers = _safe_headers(getattr(response, "headers", None))
            geturl = getattr(response, "geturl", None)
            if callable(geturl):
                final_url = geturl()
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
            **_blocked_article_result(source, registry_hash, candidate["candidate_id"], captured, assessments, ["ARTICLE_REQUEST_FAILED"]),
            "capture_status": "NETWORK_ERROR",
            "network_request_made": True,
            "requested_url": article_url,
            "final_url": None,
            "raw_response_sha256": hashlib.sha256(b"").hexdigest(),
            "raw_response_base64": "",
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        }
    reason_codes = []
    errors = []
    final_parts = urlsplit(final_url)
    final_ok = (
        final_parts.scheme == "https"
        and (final_parts.hostname or "").casefold() in allowed_hosts
        and final_parts.port in (None, 443)
        and final_parts.username is None
        and final_parts.password is None
    )
    if read_error is not None:
        status = "PARTIAL"
        reason_codes.append("RESPONSE_READ_INCOMPLETE")
        errors.append({"type": type(read_error).__name__, "message": str(read_error)})
    elif status_code != 200:
        status = "HTTP_ERROR"
        reason_codes.append("HTTP_STATUS_UNEXPECTED")
        errors.append({"type": "HTTP_STATUS", "message": f"unexpected HTTP status {status_code}"})
    elif not final_ok:
        status = "BLOCKED_REDIRECT_TARGET"
        reason_codes.append("FINAL_URL_OUTSIDE_ALLOWLIST")
    else:
        status = "PASS"
    return {
        "schema_version": ARTICLE_CAPTURE_SCHEMA,
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": source["status"],
        "source_registry_entry_sha256": registry_hash,
        "source_url": source["source_url"],
        "candidate_id": candidate["candidate_id"],
        "requested_url": article_url,
        "final_url": final_url,
        "captured_at": captured,
        "capture_status": status,
        "network_request_made": True,
        "http_status": status_code,
        "response_headers": headers,
        "content_type": headers.get("Content-Type") or headers.get("content-type"),
        **_store_response_body_fields(
            source,
            raw,
            html=(headers.get("Content-Type") or headers.get("content-type") or "").split(";", 1)[0].strip().lower()
            in {"text/html", "application/xhtml+xml"},
        ),
        "capture_truncated": read_error is not None,
        "provider_policy_assessments": assessments,
        "provider_use_assessment": assessments[0],
        "persistent_storage_assessment": assessments[1],
        "reason_codes": reason_codes,
        "errors": errors,
    }


def promote_public_archive_candidate_to_event(
    archive_capture: dict,
    candidate_record: dict,
    article_capture: dict,
    event_type: str,
    claim: str,
    entity_resolution: dict,
) -> dict:
    """Promote a historical archive candidate only with a reviewed stable-entity mapping."""
    candidate = validate_public_event_archive_candidate(archive_capture, candidate_record)
    source_id = candidate["source_id"]
    source = get_source(source_id)
    current_hash = source_entry_sha256(source)
    if not source_is_approved(source):
        raise PermissionError("source registry status must be APPROVED before archive promotion")
    if archive_capture.get("source_registry_entry_sha256") != current_hash:
        raise PermissionError("archive source registry evidence is missing or stale")
    if (
        archive_capture.get("capture_status") != "PASS"
        or archive_capture.get("capture_truncated") is not False
        or archive_capture.get("network_request_made") is not True
    ):
        raise PermissionError("archive capture is incomplete")
    for use_case in _REQUIRED_USE_CASES:
        if evaluate_artifact_use(archive_capture, use_case)["decision"] != "ALLOW":
            raise PermissionError(f"archive capture does not authorize {use_case}")
    if not isinstance(article_capture, dict) or article_capture.get("schema_version") != ARTICLE_CAPTURE_SCHEMA:
        raise ValueError("a valid preserved article_capture is required for archive promotion")
    if (
        article_capture.get("source_id") != source_id
        or article_capture.get("candidate_id") != candidate["candidate_id"]
        or article_capture.get("capture_status") != "PASS"
        or article_capture.get("http_status") != 200
        or article_capture.get("network_request_made") is not True
        or article_capture.get("capture_truncated") is not False
        or article_capture.get("source_registry_status") != "APPROVED"
        or article_capture.get("source_registry_entry_sha256") != current_hash
        or article_capture.get("requested_url") != candidate["candidate_url"]
    ):
        raise PermissionError("article capture is incomplete, stale, or does not match the archive candidate")
    archive_captured = parse_timestamp(archive_capture.get("captured_at"), "archive_capture.captured_at")
    article_captured = parse_timestamp(article_capture.get("captured_at"), "article_capture.captured_at")
    published = parse_timestamp(candidate["published_at"], "candidate.published_at")
    if article_captured < archive_captured or article_captured < published:
        raise ValueError("article capture time precedes archive capture or publication time")
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    final_parts = urlsplit(article_capture.get("final_url", ""))
    if (
        final_parts.scheme != "https" or (final_parts.hostname or "").casefold() not in allowed_hosts
        or final_parts.port not in (None, 443) or final_parts.username is not None or final_parts.password is not None
    ):
        raise PermissionError("article final URL is outside the approved HTTPS host allowlist")
    article_hash = article_capture.get("raw_response_sha256")
    article_size = article_capture.get("raw_response_bytes")
    if (
        not isinstance(article_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", article_hash)
        or isinstance(article_size, bool) or not isinstance(article_size, int) or article_size < 0
    ):
        raise PermissionError("article original response byte count or SHA-256 is missing or invalid")
    _load_archive_text_evidence(article_capture)
    content_type = article_capture.get("content_type")
    if not isinstance(content_type, str) or content_type.split(";", 1)[0].strip().lower() not in {"text/html", "application/xhtml+xml"}:
        raise PermissionError("article content type must be HTML or XHTML")
    for use_case in _REQUIRED_USE_CASES:
        assessment_key = "provider_use_assessment" if use_case == "internal_analysis" else "persistent_storage_assessment"
        assessment = article_capture.get(assessment_key)
        if not isinstance(assessment, dict) or assessment.get("decision") != "ALLOW" or assessment.get("provider_id") != source["provider_id"]:
            raise PermissionError(f"article capture does not authorize {use_case}")
    if not isinstance(entity_resolution, dict) or entity_resolution.get("status") != "APPROVED":
        raise ValueError("entity_resolution.status APPROVED is required")
    reviewer = entity_resolution.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("entity_resolution.reviewed_by is required")
    reviewed_at = parse_timestamp(entity_resolution.get("reviewed_at"), "entity_resolution.reviewed_at")
    entities = entity_resolution.get("entities")
    if not isinstance(entities, list) or not entities:
        raise ValueError("entity_resolution.entities must contain stable identifiers")
    evidence_b64 = entity_resolution.get("evidence_record_base64")
    evidence_hash = entity_resolution.get("evidence_record_sha256")
    if not isinstance(evidence_b64, str) or not evidence_b64:
        raise ValueError("entity_resolution.evidence_record_base64 is required")
    if not isinstance(evidence_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", evidence_hash):
        raise ValueError("entity_resolution.evidence_record_sha256 must be a SHA-256")
    try:
        evidence_bytes = base64.b64decode(evidence_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("entity_resolution.evidence_record_base64 is invalid") from exc
    if hashlib.sha256(evidence_bytes).hexdigest() != evidence_hash.lower():
        raise ValueError("entity-resolution evidence SHA-256 mismatch")
    event_type_text = event_type.strip() if isinstance(event_type, str) else ""
    claim_text = claim.strip() if isinstance(claim, str) else ""
    if not event_type_text or not claim_text:
        raise ValueError("event_type and claim must be explicit; the connector does not infer causality")
    event_id = f"{source_id}:" + hashlib.sha256(candidate["candidate_id"].encode("utf-8")).hexdigest()
    event = {
        "schema_version": EVENT_SCHEMA,
        "event_id": event_id,
        "title": candidate["title"],
        "event_type": event_type_text,
        "source": {
            "source_type": source["source_type"],
            "url": candidate["candidate_url"],
            "publisher": source["display_name"],
        },
        "published_at": candidate["published_at"],
        "captured_at": article_capture["captured_at"],
        "entities": entities,
        "evidence": [{"url": candidate["candidate_url"], "claim": claim_text}],
        "capture_method": "public_event_archive_html_v1",
        "content_sha256": article_hash,
        "license_notes": (
            "Official archive index and article captured under the source-specific authorization gate; "
            f"registry_entry_sha256={current_hash}. Archive listing date evidence and article body are preserved; "
            "the fact and causal claims remain separately reviewable."
        ),
        "metadata": {
            "source_id": source_id,
            "archive_url": candidate["archive_url"],
            "archive_candidate_id": candidate["candidate_id"],
            "archive_candidate_record": candidate,
            "archive_raw_response_sha256": archive_capture["raw_response_sha256"],
            "archive_text_evidence_sha256": archive_capture.get("text_evidence_sha256"),
            "archive_publication_time_evidence": candidate["publication_time_evidence"],
            "entity_resolution_reviewed_by": reviewer.strip(),
            "entity_resolution_reviewed_at": reviewed_at.isoformat().replace("+00:00", "Z"),
            "entity_resolution_evidence_record_sha256": evidence_hash.lower(),
            "entity_resolution_evidence_record_base64": evidence_b64,
            "causality_status": "NOT_ASSESSED",
            "article_raw_response_sha256": article_hash,
            "article_text_evidence_sha256": article_capture.get("text_evidence_sha256"),
            "article_content_type": content_type,
        },
    }
    normalized = validate_event(event)
    normalized.update({
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": "APPROVED",
        "source_registry_entry_sha256": current_hash,
        "provider_use_assessment": archive_capture["provider_use_assessment"],
        "persistent_storage_assessment": archive_capture["persistent_storage_assessment"],
        "provider_policy_assessments": archive_capture["provider_policy_assessments"],
        "source_capture_assessments": {
            "archive": archive_capture,
            "article": article_capture,
        },
        "orders_submitted": False,
        "causality_claimed": False,
    })
    return normalized



def promote_public_feed_candidate_to_event(
    feed_capture: dict,
    candidate_id: str,
    event_type: str,
    claim: str,
    entity_resolution: dict,
    article_capture: dict,
) -> dict:
    """Promote a feed candidate only with a preserved article and reviewed stable-entity mapping."""

    if not isinstance(feed_capture, dict) or feed_capture.get("schema_version") != FEED_CAPTURE_SCHEMA:
        raise ValueError("feed_capture has an invalid schema")
    source_id = feed_capture.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("feed_capture.source_id is required")
    source = get_source(source_id)
    if not source_is_approved(source):
        raise PermissionError("source registry is not approved")
    if feed_capture.get("capture_status") != "PASS" or feed_capture.get("capture_truncated") is not False:
        raise PermissionError("feed capture must be a complete PASS capture")
    if feed_capture.get("network_request_made") is not True:
        raise PermissionError("feed capture must prove a network request")
    current_registry_hash = source_entry_sha256(source)
    if (
        feed_capture.get("source_registry_status") != "APPROVED"
        or feed_capture.get("source_registry_entry_sha256") != current_registry_hash
    ):
        raise PermissionError("source registry evidence is missing or stale")
    if feed_capture.get("source_url") != source["source_url"]:
        raise PermissionError("feed capture source URL does not match the source registry")
    for use_case in ("internal_analysis", "persistent_storage"):
        if evaluate_artifact_use(feed_capture, use_case)["decision"] != "ALLOW":
            raise PermissionError(f"feed capture does not authorize {use_case}")
    raw_b64 = feed_capture.get("raw_response_base64")
    if not isinstance(raw_b64, str):
        raise PermissionError("feed capture raw response is missing")
    try:
        raw = base64.b64decode(raw_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("feed capture raw response base64 is invalid") from exc
    if hashlib.sha256(raw).hexdigest() != feed_capture.get("raw_response_sha256"):
        raise PermissionError("feed capture raw response hash mismatch")
    if len(raw) != feed_capture.get("raw_response_bytes"):
        raise PermissionError("feed capture raw response byte count mismatch")

    candidate = next(
        (item for item in feed_capture.get("feed_items", []) if item.get("candidate_id") == candidate_id),
        None,
    )
    if candidate is None:
        raise ValueError("candidate_id was not present in feed_capture")
    if candidate.get("url_status") != "ALLOWLISTED_SOURCE_HOST":
        raise PermissionError("candidate URL is outside the source host allowlist")
    if candidate.get("publication_time_status") != "PARSED" or not candidate.get("published_at"):
        raise ValueError("candidate has no eligible publication timestamp")
    published = parse_timestamp(candidate["published_at"], "candidate.published_at")
    feed_captured = parse_timestamp(feed_capture.get("captured_at"), "feed_capture.captured_at")
    if published > feed_captured:
        raise ValueError("candidate publication timestamp is after the capture cutoff")
    allowed_hosts = {host.casefold() for host in source.get("allowed_article_hosts", [])}
    parts = urlsplit(candidate["url"])
    if (
        parts.scheme != "https"
        or (parts.hostname or "").casefold() not in allowed_hosts
        or parts.port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
    ):
        raise PermissionError("candidate URL is outside the approved source host allowlist")

    if not isinstance(article_capture, dict) or article_capture.get("schema_version") != ARTICLE_CAPTURE_SCHEMA:
        raise ValueError("a valid preserved article_capture is required for promotion")
    if (
        article_capture.get("source_id") != source_id
        or article_capture.get("candidate_id") != candidate_id
        or article_capture.get("capture_status") != "PASS"
        or article_capture.get("http_status") != 200
        or article_capture.get("network_request_made") is not True
        or article_capture.get("capture_truncated") is not False
        or article_capture.get("source_registry_status") != "APPROVED"
        or article_capture.get("source_registry_entry_sha256") != current_registry_hash
        or article_capture.get("requested_url") != candidate["url"]
    ):
        raise PermissionError("article capture is incomplete, stale, or does not match the selected feed candidate")
    article_captured = parse_timestamp(article_capture.get("captured_at"), "article_capture.captured_at")
    if article_captured < feed_captured or article_captured < published:
        raise ValueError("article capture time precedes feed capture or publication time")
    final_parts = urlsplit(article_capture.get("final_url", ""))
    if (
        final_parts.scheme != "https"
        or (final_parts.hostname or "").casefold() not in allowed_hosts
        or final_parts.port not in (None, 443)
        or final_parts.username is not None
        or final_parts.password is not None
    ):
        raise PermissionError("article final URL is outside the approved HTTPS host allowlist")
    article_b64 = article_capture.get("raw_response_base64")
    article_hash = article_capture.get("raw_response_sha256")
    article_size = article_capture.get("raw_response_bytes")
    if (
        not isinstance(article_b64, str)
        or not isinstance(article_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", article_hash)
        or isinstance(article_size, bool)
        or not isinstance(article_size, int)
        or article_size < 0
    ):
        raise PermissionError("article body, byte count, or SHA-256 is missing or invalid")
    try:
        article_raw = base64.b64decode(article_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("article body base64 is invalid") from exc
    if hashlib.sha256(article_raw).hexdigest() != article_hash or len(article_raw) != article_size:
        raise PermissionError("article body integrity check failed")
    content_type = article_capture.get("content_type")
    if not isinstance(content_type, str) or content_type.split(";", 1)[0].strip().lower() not in {"text/html", "application/xhtml+xml"}:
        raise PermissionError("article content type must be HTML or XHTML")
    for use_case in _REQUIRED_USE_CASES:
        assessment_key = "provider_use_assessment" if use_case == "internal_analysis" else "persistent_storage_assessment"
        assessment = article_capture.get(assessment_key)
        if not isinstance(assessment, dict) or assessment.get("decision") != "ALLOW" or assessment.get("provider_id") != source["provider_id"]:
            raise PermissionError(f"article capture does not authorize {use_case}")

    if not isinstance(entity_resolution, dict) or entity_resolution.get("status") != "APPROVED":
        raise ValueError("entity_resolution.status APPROVED is required")
    reviewer = entity_resolution.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("entity_resolution.reviewed_by is required")
    reviewed_at = parse_timestamp(entity_resolution.get("reviewed_at"), "entity_resolution.reviewed_at")
    entities = entity_resolution.get("entities")
    if not isinstance(entities, list) or not entities:
        raise ValueError("entity_resolution.entities must contain stable identifiers")
    evidence_b64 = entity_resolution.get("evidence_record_base64")
    evidence_hash = entity_resolution.get("evidence_record_sha256")
    if not isinstance(evidence_b64, str) or not evidence_b64:
        raise ValueError("entity_resolution.evidence_record_base64 is required")
    if not isinstance(evidence_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", evidence_hash):
        raise ValueError("entity_resolution.evidence_record_sha256 must be a SHA-256")
    try:
        evidence_bytes = base64.b64decode(evidence_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("entity_resolution.evidence_record_base64 is invalid") from exc
    if hashlib.sha256(evidence_bytes).hexdigest() != evidence_hash.lower():
        raise ValueError("entity-resolution evidence SHA-256 mismatch")
    event_type_text = event_type.strip() if isinstance(event_type, str) else ""
    claim_text = claim.strip() if isinstance(claim, str) else ""
    if not event_type_text or not claim_text:
        raise ValueError("event_type and claim must be explicit; the connector does not infer causality")

    event_id = f"{source_id}:" + hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()
    event = {
        "schema_version": EVENT_SCHEMA,
        "event_id": event_id,
        "title": candidate.get("title") or source["display_name"],
        "event_type": event_type_text,
        "source": {
            "source_type": source["source_type"],
            "url": candidate["url"],
            "publisher": source["display_name"],
        },
        "published_at": candidate["published_at"],
        "captured_at": article_capture["captured_at"],
        "entities": entities,
        "evidence": [{"url": candidate["url"], "claim": claim_text}],
        "capture_method": "public_event_feed_rss_atom_v1",
        "content_sha256": article_hash,
        "license_notes": (
            "Source registry and provider authorization allow internal_analysis and persistent_storage; "
            f"registry_entry_sha256={current_registry_hash}. Full article body captured and hashed; "
            "source claim still requires factual review. Causality has not been assessed."
        ),
        "metadata": {
            "source_id": source_id,
            "feed_candidate_id": candidate_id,
            "feed_raw_response_sha256": feed_capture["raw_response_sha256"],
            "feed_item_record": candidate,
            "entity_resolution_reviewed_by": reviewer.strip(),
            "entity_resolution_reviewed_at": reviewed_at.isoformat().replace("+00:00", "Z"),
            "entity_resolution_evidence_record_sha256": evidence_hash.lower(),
            "entity_resolution_evidence_record_base64": evidence_b64,
            "causality_status": "NOT_ASSESSED",
            "article_raw_response_sha256": article_hash,
            "article_content_type": content_type,
        },
    }
    normalized = validate_event(event)
    normalized.update({
        "source_id": source_id,
        "provider_id": source["provider_id"],
        "source_registry_status": "APPROVED",
        "source_registry_entry_sha256": current_registry_hash,
        "provider_use_assessment": feed_capture["provider_use_assessment"],
        "persistent_storage_assessment": feed_capture["persistent_storage_assessment"],
        "provider_policy_assessments": feed_capture["provider_policy_assessments"],
        "source_capture_assessments": {
            "feed": {
                key: feed_capture.get(key)
                for key in (
                    "capture_status", "network_request_made", "capture_truncated",
                    "source_registry_status", "source_registry_entry_sha256", "source_url",
                    "requested_url", "captured_at", "response_headers", "raw_response_bytes",
                    "raw_response_sha256", "raw_response_base64", "provider_use_assessment",
                    "persistent_storage_assessment", "provider_policy_assessments",
                )
            },
            "article": article_capture,
        },
        "orders_submitted": False,
        "causality_claimed": False,
    })
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True, help="Source ID from the deployment-controlled event source registry")
    parser.add_argument("--provider-authorization-registry", required=True, type=Path, help="Deployment-controlled provider authorization registry JSON")
    parser.add_argument("--user-agent", required=True, help="Identifiable operator-reviewed User-Agent")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--captured-at", help="Optional explicit ISO-8601 capture timestamp")
    parser.add_argument("--feed-capture", type=Path, help="Existing complete feed-capture JSON; enables article capture mode")
    parser.add_argument("--article-candidate-id", help="Candidate ID from --feed-capture; required in article capture mode")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if bool(args.feed_capture) != bool(args.article_candidate_id):
        parser.error("--feed-capture and --article-candidate-id must be supplied together")
    registry = json.loads(args.provider_authorization_registry.read_text(encoding="utf-8"))
    record = registry.get(args.source_id) if isinstance(registry, dict) else None
    failure_exit_code = 0
    try:
        if args.feed_capture is not None:
            feed_capture = json.loads(args.feed_capture.read_text(encoding="utf-8"))
            if not isinstance(feed_capture, dict) or feed_capture.get("source_id") != args.source_id:
                parser.error("--feed-capture source_id must match --source-id")
            result = capture_public_event_article(
                feed_capture,
                args.article_candidate_id,
                authorization_record=record,
                user_agent=args.user_agent,
                timeout_seconds=args.timeout_seconds,
                captured_at=args.captured_at,
            )
            summary = {
                "output": str(args.output),
                "source_id": result["source_id"],
                "candidate_id": result["candidate_id"],
                "capture_status": result["capture_status"],
                "network_request_made": result["network_request_made"],
                "raw_response_bytes": result["raw_response_bytes"],
                "reason_codes": result["reason_codes"],
            }
        else:
            result = capture_public_event_feed(
                args.source_id,
                authorization_record=record,
                user_agent=args.user_agent,
                timeout_seconds=args.timeout_seconds,
                captured_at=args.captured_at,
            )
            summary = {
                "output": str(args.output),
                "source_id": result["source_id"],
                "capture_status": result["capture_status"],
                "network_request_made": result["network_request_made"],
                "feed_item_count": result["feed_item_count"],
                "duplicate_item_count": result["duplicate_item_count"],
                "reason_codes": result["reason_codes"],
            }
    except RateLimitCoordinationError:
        failure_exit_code = 2
        result = {
            "schema_version": "crypto-public-event-capture-error-v1",
            "source_id": args.source_id,
            "capture_status": "BLOCKED_RATE_LIMIT_COORDINATION",
            "network_request_made": False,
            "reason_codes": ["RATE_LIMIT_COORDINATION_FAILED"],
            "errors": [{
                "type": "RATE_LIMIT_COORDINATION",
                "message": "Shared request-rate coordination is unavailable; no network request was made.",
            }],
        }
        summary = {
            "output": str(args.output),
            "source_id": args.source_id,
            "capture_status": result["capture_status"],
            "network_request_made": False,
            "reason_codes": result["reason_codes"],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return failure_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
