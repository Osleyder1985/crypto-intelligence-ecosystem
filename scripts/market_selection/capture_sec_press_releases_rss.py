"""Read-only SEC RSS/article capture, fail-closed until source terms are approved.

The default source registry is TERMS_PENDING. No HTTP request occurs until the registry,
provider authorization, persistent-storage scope, User-Agent, and timeout all pass.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from typing import Any

try:
    from scripts.market_selection.external_event_evidence import INPUT_SCHEMA as EVENT_SCHEMA, parse_timestamp, validate_event
    from scripts.market_selection.event_source_registry import get_source, source_entry_sha256, source_is_approved
    from scripts.market_selection.provider_license_gate import (
        ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION, evaluate_provider_use,
    )
except ModuleNotFoundError:
    from external_event_evidence import INPUT_SCHEMA as EVENT_SCHEMA, parse_timestamp, validate_event
    from event_source_registry import get_source, source_entry_sha256, source_is_approved
    from provider_license_gate import ASSESSMENT_SCHEMA_VERSION, POLICY_VERSION, evaluate_provider_use

FEED_CAPTURE_SCHEMA = "crypto-sec-rss-capture-v1"
ARTICLE_CAPTURE_SCHEMA = "crypto-sec-article-capture-v1"
SOURCE_ID = "sec_press_releases"
_REQUIRED_USE_CASES = ("internal_analysis", "persistent_storage")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


_RATE_LOCK = threading.Lock()
_LAST_REQUEST_MONOTONIC: float | None = None


def _wait_for_rate_slot(max_requests_per_second: float) -> None:
    """Enforce the source's published per-process request-start ceiling."""
    global _LAST_REQUEST_MONOTONIC
    interval = 1.0 / max_requests_per_second
    with _RATE_LOCK:
        now = time.monotonic()
        if _LAST_REQUEST_MONOTONIC is not None:
            delay = interval - (now - _LAST_REQUEST_MONOTONIC)
            if delay > 0:
                time.sleep(delay)
                now = time.monotonic()
        _LAST_REQUEST_MONOTONIC = now


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_timestamp(value: str | None) -> str:
    if value is None:
        return _utc_now()
    return parse_timestamp(value, "captured_at").isoformat().replace("+00:00", "Z")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == name:
            value = child.text
            return value.strip() if isinstance(value, str) and value.strip() else None
    return None


def _safe_headers(headers: Any) -> dict[str, str]:
    if headers is None or not hasattr(headers, "items"):
        return {}
    excluded = {"set-cookie", "authorization", "proxy-authorization", "www-authenticate"}
    return {str(key): str(value) for key, value in headers.items() if str(key).lower() not in excluded}


def _assessment(use_case: str, authorization_record: dict | None) -> dict:
    try:
        return evaluate_provider_use(SOURCE_ID, use_case, authorization_record)
    except (TypeError, ValueError):
        return {
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "policy_version": POLICY_VERSION,
            "provider_id": SOURCE_ID,
            "use_case": use_case,
            "decision": "BLOCK",
            "reason_codes": ["AUTHORIZATION_RECORD_INVALID"],
            "authorization_evidence_status": "INVALID_RECORD",
        }


def _effective_assessment(raw: dict, blockers: list[str]) -> dict:
    result = deepcopy(raw)
    reasons = set(result.get("reason_codes", []))
    reasons.update(blockers)
    if blockers or raw.get("decision") != "ALLOW":
        result["decision"] = "BLOCK"
    result["reason_codes"] = sorted(reasons)
    return result


def _authorization_state(
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float,
) -> tuple[dict, dict, dict, list[str], str]:
    source = get_source(SOURCE_ID)
    registry_hash = source_entry_sha256(source)
    raw_analysis = _assessment("internal_analysis", authorization_record)
    raw_storage = _assessment("persistent_storage", authorization_record)
    blockers: list[str] = []

    if source["status"] != "APPROVED":
        status_reason = {
            "PROPOSED": "SOURCE_TERMS_PENDING",
            "TERMS_PENDING": "SOURCE_TERMS_PENDING",
            "SUSPENDED": "SOURCE_SUSPENDED",
            "RETIRED": "SOURCE_RETIRED",
            "REJECTED": "SOURCE_REJECTED",
        }.get(source["status"], "SOURCE_NOT_APPROVED")
        blockers.append(status_reason)
    if not set(source["allowed_use_cases"]).issuperset(_REQUIRED_USE_CASES):
        blockers.append("SOURCE_USE_CASES_NOT_APPROVED")

    if not isinstance(authorization_record, dict):
        blockers.append("AUTHORIZATION_RECORD_MISSING")
    else:
        if authorization_record.get("terms_url") != source["terms_url"]:
            blockers.append("AUTHORIZATION_TERMS_URL_MISMATCH")
        if authorization_record.get("terms_sha256") != source.get("terms_sha256"):
            blockers.append("AUTHORIZATION_TERMS_HASH_MISMATCH")

    if source.get("user_agent_required"):
        if not isinstance(user_agent, str) or not user_agent.strip() or "\r" in user_agent or "\n" in user_agent:
            blockers.append("USER_AGENT_REQUIRED")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        blockers.append("INVALID_TIMEOUT_SECONDS")

    if raw_analysis.get("decision") != "ALLOW":
        blockers.extend(raw_analysis.get("reason_codes") or ["INTERNAL_ANALYSIS_NOT_AUTHORIZED"])
    if raw_storage.get("decision") != "ALLOW":
        blockers.extend(raw_storage.get("reason_codes") or ["PERSISTENT_STORAGE_NOT_AUTHORIZED"])
    blockers = sorted(set(blockers))
    analysis = _effective_assessment(raw_analysis, blockers)
    storage = _effective_assessment(raw_storage, blockers)
    state = {
        "source": source,
        "source_registry_entry_sha256": registry_hash,
        "provider_policy_assessments": [raw_analysis, raw_storage],
        "provider_use_assessment": analysis,
        "persistent_storage_assessment": storage,
    }
    return state, analysis, storage, blockers, registry_hash


def _blocked_result(schema: str, state: dict, captured_at: str, blockers: list[str], requested_url: str) -> dict:
    return {
        "schema_version": schema,
        "source_id": SOURCE_ID,
        "provider_id": SOURCE_ID,
        "source_registry_status": state["source"]["status"],
        "source_registry_entry_sha256": state["source_registry_entry_sha256"],
        "source_url": state["source"]["source_url"],
        "requested_url": requested_url,
        "captured_at": captured_at,
        "capture_status": "BLOCKED",
        "network_request_made": False,
        "http_status": None,
        "response_headers": {},
        "raw_response_bytes": 0,
        "raw_response_sha256": None,
        "raw_response_base64": None,
        "provider_policy_assessments": state["provider_policy_assessments"],
        "provider_use_assessment": state["provider_use_assessment"],
        "persistent_storage_assessment": state["persistent_storage_assessment"],
        "reason_codes": sorted(set(blockers)),
        "errors": [],
    }


def _response_capture(
    schema: str,
    state: dict,
    captured_at: str,
    requested_url: str,
    status_code: int,
    headers: dict[str, str],
    raw: bytes,
    capture_status: str,
    *,
    feed_items: list[dict] | None = None,
    errors: list[dict] | None = None,
) -> dict:
    result = {
        "schema_version": schema,
        "source_id": SOURCE_ID,
        "provider_id": SOURCE_ID,
        "source_registry_status": state["source"]["status"],
        "source_registry_entry_sha256": state["source_registry_entry_sha256"],
        "source_url": state["source"]["source_url"],
        "requested_url": requested_url,
        "publisher": state["source"]["display_name"],
        "source_type": state["source"]["source_type"],
        "captured_at": captured_at,
        "capture_status": capture_status,
        "network_request_made": True,
        "http_status": status_code,
        "response_headers": headers,
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_response_base64": base64.b64encode(raw).decode("ascii"),
        "provider_policy_assessments": state["provider_policy_assessments"],
        "provider_use_assessment": state["provider_use_assessment"],
        "persistent_storage_assessment": state["persistent_storage_assessment"],
        "reason_codes": [],
        "errors": errors or [],
    }
    if schema == FEED_CAPTURE_SCHEMA:
        result["feed_items"] = feed_items or []
        result["feed_item_count"] = len(feed_items or [])
        result["coverage"] = {
            "scope": state["source"]["coverage_scope"],
            "historical_archive_complete": False,
            "empty_feed_proves_no_event": False,
            "entities_auto_resolved": False,
        }
    else:
        result["coverage"] = {
            "scope": "Single SEC article response body only",
            "historical_archive_complete": False,
            "entities_auto_resolved": False,
        }
    return result


def _request(
    state: dict,
    captured_at: str,
    requested_url: str,
    user_agent: str,
    timeout_seconds: float,
    opener: Any,
    schema: str,
) -> tuple[dict | None, bytes | None, int | None, dict[str, str]]:
    _wait_for_rate_slot(float(state["source"]["max_requests_per_second"]))
    request = Request(
        requested_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.1",
        },
        method="GET",
    )
    try:
        response = opener(request, timeout=timeout_seconds)
    except HTTPError as exc:
        raw = exc.read()  # Preserve the complete error body too.
        headers = _safe_headers(exc.headers)
        result = _response_capture(
            schema, state, captured_at, requested_url, int(exc.code),
            headers, raw, "HTTP_ERROR",
            errors=[{"error_type": "HTTPError", "reason_code": "HTTP_STATUS_NOT_SUCCESS"}],
        )
        return result, raw, int(exc.code), headers
    except (URLError, TimeoutError, OSError) as exc:
        result = _blocked_result(schema, state, captured_at, [], requested_url)
        result["capture_status"] = "NETWORK_ERROR"
        result["network_request_made"] = True
        result["reason_codes"] = ["NETWORK_REQUEST_FAILED"]
        result["errors"] = [{"error_type": type(exc).__name__, "reason_code": "NETWORK_REQUEST_FAILED"}]
        return result, None, None, {}

    try:
        status_code = getattr(response, "status", None)
        if status_code is None:
            status_code = response.getcode()
        status_code = int(status_code)
        headers = _safe_headers(getattr(response, "headers", None))
        try:
            raw = response.read()  # Read to EOF; no local response-size cap.
        except (URLError, TimeoutError, OSError) as exc:
            result = _blocked_result(schema, state, captured_at, ["NETWORK_RESPONSE_READ_FAILED"], requested_url)
            result["capture_status"] = "NETWORK_ERROR"
            result["network_request_made"] = True
            result["errors"] = [{"error_type": type(exc).__name__, "reason_code": "NETWORK_RESPONSE_READ_FAILED"}]
            return result, None, None, {}
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()

    if status_code != 200:
        result = _response_capture(
            schema, state, captured_at, requested_url, status_code, headers, raw, "HTTP_ERROR",
            errors=[{"error_type": "HTTPStatus", "reason_code": "HTTP_STATUS_NOT_SUCCESS"}],
        )
        result["reason_codes"] = ["HTTP_STATUS_NOT_SUCCESS"]
        return result, raw, status_code, headers
    return None, raw, status_code, headers


def _parse_rss(raw: bytes) -> list[dict]:
    root = ET.fromstring(raw)
    root_name = _local_name(root.tag)
    if root_name not in {"rss", "RDF"}:
        raise ValueError("document root is not RSS/RDF")

    items = []
    for element in root.iter():
        if _local_name(element.tag) != "item":
            continue
        title = _child_text(element, "title")
        link = _child_text(element, "link")
        guid = _child_text(element, "guid")
        description = _child_text(element, "description")
        published_raw = _child_text(element, "pubDate")
        item_bytes = ET.tostring(element, encoding="utf-8")
        normalized_item = {
            "title": title,
            "link": link,
            "guid": guid,
            "description": description,
            "published_at_raw": published_raw,
        }
        item_hash = hashlib.sha256(
            json.dumps(normalized_item, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        item_id = guid or link or f"sha256:{item_hash}"

        published_at_utc = None
        if not published_raw:
            timestamp_status = "MISSING_PUBLISHED_AT"
        else:
            try:
                parsed = parsedate_to_datetime(published_raw)
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    timestamp_status = "PUBLISHED_AT_TIMEZONE_MISSING"
                else:
                    published_at_utc = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                    timestamp_status = "PARSED"
            except (TypeError, ValueError, OverflowError):
                timestamp_status = "PUBLISHED_AT_UNPARSEABLE"

        items.append({
            "item_id": item_id,
            "title": title,
            "link": link,
            "guid": guid,
            "description": description,
            "published_at_raw": published_raw,
            "published_at_utc": published_at_utc,
            "timestamp_status": timestamp_status,
            "normalized_item_sha256": item_hash,
            "normalized_item_xml_bytes": len(item_bytes),
            "entity_resolution_status": "NOT_RESOLVED",
            "event_promotion_status": "REQUIRES_REVIEWED_STABLE_ENTITY_AND_ARTICLE_CAPTURE",
            "reason_codes": ["STABLE_ASSET_IDENTIFIER_NOT_SUPPLIED"],
        })
    return items


def _approved_article_url(source: dict, article_url: str) -> bool:
    parsed = urlsplit(article_url)
    try:
        return (
            parsed.scheme == "https"
            and parsed.hostname in set(source["allowed_article_hosts"])
            and parsed.port in (None, 443)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def capture_sec_press_releases_rss(
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float,
    *,
    captured_at: str | None = None,
    opener: Any = None,
) -> dict:
    state, analysis, storage, blockers, registry_hash = _authorization_state(
        authorization_record, user_agent, timeout_seconds
    )
    timestamp = _normalize_timestamp(captured_at)
    source = state["source"]
    if blockers:
        return _blocked_result(FEED_CAPTURE_SCHEMA, state, timestamp, blockers, source["source_url"])

    response_result, raw, status_code, response_headers = _request(
        state, timestamp, source["source_url"], user_agent.strip(), timeout_seconds,
        opener or urlopen, FEED_CAPTURE_SCHEMA,
    )
    if response_result is not None:
        return response_result
    try:
        items = _parse_rss(raw or b"")
    except (ET.ParseError, ValueError):
        result = _response_capture(
            FEED_CAPTURE_SCHEMA, state, timestamp, source["source_url"], status_code or 200, response_headers, raw or b"", "PARSE_ERROR",
            errors=[{"error_type": "RSSParseError", "reason_code": "RSS_DOCUMENT_INVALID"}],
        )
        result["reason_codes"] = ["RSS_DOCUMENT_INVALID"]
        return result

    return _response_capture(
        FEED_CAPTURE_SCHEMA, state, timestamp, source["source_url"], status_code or 200, response_headers, raw or b"", "PASS",
        feed_items=items,
    )


def capture_sec_press_release_article(
    article_url: str,
    authorization_record: dict | None,
    user_agent: str | None,
    timeout_seconds: float,
    *,
    captured_at: str | None = None,
    opener: Any = None,
) -> dict:
    state, analysis, storage, blockers, registry_hash = _authorization_state(
        authorization_record, user_agent, timeout_seconds
    )
    timestamp = _normalize_timestamp(captured_at)
    source = state["source"]
    if not _approved_article_url(source, article_url):
        blockers = sorted(set(blockers + ["ARTICLE_URL_NOT_ALLOWLISTED"]))
    if blockers:
        return _blocked_result(ARTICLE_CAPTURE_SCHEMA, state, timestamp, blockers, article_url)

    response_result, raw, status_code, response_headers = _request(
        state, timestamp, article_url, user_agent.strip(), timeout_seconds,
        opener or urlopen, ARTICLE_CAPTURE_SCHEMA,
    )
    if response_result is not None:
        return response_result
    content_type = next(
        (value.split(";", 1)[0].strip().lower() for key, value in response_headers.items() if key.lower() == "content-type"),
        "",
    )
    if content_type not in {"text/html", "application/xhtml+xml"}:
        result = _response_capture(
            ARTICLE_CAPTURE_SCHEMA, state, timestamp, article_url, status_code or 200,
            response_headers, raw or b"", "CONTENT_TYPE_UNEXPECTED",
            errors=[{"error_type": "ContentType", "reason_code": "ARTICLE_CONTENT_TYPE_UNEXPECTED"}],
        )
        result["reason_codes"] = ["ARTICLE_CONTENT_TYPE_UNEXPECTED"]
        return result
    return _response_capture(
        ARTICLE_CAPTURE_SCHEMA, state, timestamp, article_url, status_code or 200, response_headers, raw or b"", "PASS",
    )


def _verify_capture_body(capture: dict, field: str) -> bytes:
    encoded = capture.get("raw_response_base64")
    if not isinstance(encoded, str):
        raise ValueError(f"{field}.raw_response_base64 is required")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError(f"{field}.raw_response_base64 is invalid") from exc
    if hashlib.sha256(raw).hexdigest() != capture.get("raw_response_sha256"):
        raise ValueError(f"{field} raw-response SHA-256 mismatch")
    if len(raw) != capture.get("raw_response_bytes"):
        raise ValueError(f"{field} raw-response byte count mismatch")
    return raw


def promote_sec_press_release_to_event(
    feed_capture: dict,
    feed_item_id: str,
    article_capture: dict,
    event_type: str,
    claim: str,
    entity_resolution: dict,
) -> dict:
    """Promote only a fully captured article with explicit reviewed stable entity mapping."""
    source = get_source(SOURCE_ID)
    if not source_is_approved(source):
        raise ValueError("SEC source registry is not approved")
    if not isinstance(feed_capture, dict) or feed_capture.get("schema_version") != FEED_CAPTURE_SCHEMA:
        raise ValueError("feed_capture has an invalid schema")
    if not isinstance(article_capture, dict) or article_capture.get("schema_version") != ARTICLE_CAPTURE_SCHEMA:
        raise ValueError("article_capture has an invalid schema")
    if feed_capture.get("capture_status") != "PASS" or article_capture.get("capture_status") != "PASS":
        raise ValueError("feed and article captures must both be PASS")
    if feed_capture.get("source_registry_status") != "APPROVED" or article_capture.get("source_registry_status") != "APPROVED":
        raise ValueError("source registry must be approved for both captures")
    current_registry_hash = source_entry_sha256(source)
    if feed_capture.get("source_registry_entry_sha256") != current_registry_hash or article_capture.get("source_registry_entry_sha256") != current_registry_hash:
        raise ValueError("source registry changed after capture; recapture under the current reviewed entry")
    for capture, name in ((feed_capture, "feed_capture"), (article_capture, "article_capture")):
        if capture.get("provider_use_assessment", {}).get("decision") != "ALLOW":
            raise ValueError(f"{name} does not authorize internal_analysis")
        if capture.get("persistent_storage_assessment", {}).get("decision") != "ALLOW":
            raise ValueError(f"{name} does not authorize persistent_storage")
        _verify_capture_body(capture, name)

    feed_item = next((item for item in feed_capture.get("feed_items", []) if item.get("item_id") == feed_item_id), None)
    if feed_item is None:
        raise ValueError("feed item id was not present in feed_capture")
    article_url = feed_item.get("link")
    if not isinstance(article_url, str) or article_capture.get("requested_url") != article_url:
        raise ValueError("article_capture URL does not match the selected RSS item")
    if not _approved_article_url(source, article_url):
        raise ValueError("selected RSS item URL is outside the approved SEC host allowlist")
    if not feed_item.get("published_at_utc"):
        raise ValueError("feed item has no parseable publication timestamp")

    if not isinstance(entity_resolution, dict) or entity_resolution.get("status") != "APPROVED":
        raise ValueError("explicit entity_resolution status APPROVED is required")
    reviewed_by = entity_resolution.get("reviewed_by")
    reviewed_at = entity_resolution.get("reviewed_at")
    if not isinstance(reviewed_by, str) or not reviewed_by.strip():
        raise ValueError("entity_resolution.reviewed_by is required")
    reviewed_at_utc = parse_timestamp(reviewed_at, "entity_resolution.reviewed_at").isoformat().replace("+00:00", "Z")
    entities = entity_resolution.get("entities")
    if not isinstance(entities, list) or not entities:
        raise ValueError("entity_resolution.entities must contain stable identifiers")

    claim_text = claim.strip() if isinstance(claim, str) else ""
    event_type_text = event_type.strip() if isinstance(event_type, str) else ""
    if not claim_text or not event_type_text:
        raise ValueError("event_type and claim are required; no event/causality is inferred from a headline")

    article_hash = article_capture["raw_response_sha256"]
    event_id = "sec_press_release:" + hashlib.sha256(feed_item_id.encode("utf-8")).hexdigest()
    event = {
        "schema_version": EVENT_SCHEMA,
        "event_id": event_id,
        "title": feed_item.get("title") or "SEC press release",
        "event_type": event_type_text,
        "source": {
            "source_type": "REGULATORY",
            "url": article_url,
            "publisher": source["display_name"],
        },
        "published_at": feed_item["published_at_utc"],
        "captured_at": article_capture["captured_at"],
        "entities": entities,
        "evidence": [{"url": article_url, "claim": claim_text}],
        "capture_method": "sec_press_releases_rss_plus_article_v1",
        "content_sha256": article_hash,
        "license_notes": (
            "Source registry approved for internal_analysis and persistent_storage; "
            f"registry_entry_sha256={source_entry_sha256(source)}. This record does not assert causality."
        ),
        "metadata": {
            "source_id": SOURCE_ID,
            "feed_item_id": feed_item_id,
            "feed_raw_response_sha256": feed_capture["raw_response_sha256"],
            "article_raw_response_sha256": article_hash,
            "normalized_feed_item_sha256": feed_item.get("normalized_item_sha256"),
            "entity_resolution_reviewed_by": reviewed_by.strip(),
            "entity_resolution_reviewed_at": reviewed_at_utc,
            "causality_status": "NOT_ASSESSED",
        },
    }
    return validate_event(event)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Capture SEC press-release RSS or one allowlisted article")
    parser.add_argument("--authorization-record", type=Path, help="Reviewed provider authorization record JSON")
    parser.add_argument("--user-agent", help="Classified User-Agent required by the source policy")
    parser.add_argument("--timeout-seconds", type=float, required=True, help="Explicit per-request timeout")
    parser.add_argument("--article-url", help="Optional SEC article URL; without it, capture the RSS feed")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON artifact path")
    args = parser.parse_args(argv)
    authorization_record = json.loads(args.authorization_record.read_text(encoding="utf-8")) if args.authorization_record else None
    if args.article_url:
        result = capture_sec_press_release_article(
            args.article_url, authorization_record, args.user_agent, args.timeout_seconds,
        )
    else:
        result = capture_sec_press_releases_rss(
            authorization_record, args.user_agent, args.timeout_seconds,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "capture_status": result["capture_status"],
        "network_request_made": result["network_request_made"],
        "source_registry_status": result["source_registry_status"],
        "http_status": result.get("http_status"),
        "feed_item_count": result.get("feed_item_count"),
        "raw_response_bytes": result.get("raw_response_bytes"),
        "reason_codes": result.get("reason_codes", []),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["capture_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
