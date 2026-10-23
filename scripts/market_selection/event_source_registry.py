"""Machine-readable registry for external event/news sources.

Entries are disabled until source terms and intended uses are explicitly reviewed.
This registry is a control plane, not evidence that a source grants any particular right.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import base64
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit

try:
    from scripts.market_selection.provider_license_gate import SUPPORTED_USE_CASES
except ModuleNotFoundError:
    from provider_license_gate import SUPPORTED_USE_CASES

REGISTRY_SCHEMA_VERSION = "crypto-event-source-registry-v1"
SOURCE_STATUSES = {"PROPOSED", "TERMS_PENDING", "APPROVED", "SUSPENDED", "RETIRED", "REJECTED"}
_SOURCE_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")

EVENT_SOURCE_REGISTRY = {
    "schema_version": REGISTRY_SCHEMA_VERSION,
    "sources": {
        "sec_press_releases": {
            "source_id": "sec_press_releases",
            "provider_id": "sec_press_releases",
            "display_name": "U.S. Securities and Exchange Commission press releases RSS",
            "source_type": "REGULATORY",
            "source_url": "https://www.sec.gov/news/pressreleases.rss",
            "allowed_article_hosts": ["www.sec.gov", "sec.gov"],
            "terms_url": "https://www.sec.gov/about/developer-resources",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Caller must supply an operator-reviewed User-Agent; this code cannot verify SEC classification.",
            "max_requests_per_second": 10,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "Current RSS feed only; not a complete historical archive",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description",
            "notes": (
                "Candidate only. Keep disabled until official access/terms review and the exact intended "
                "internal-analysis and persistent-storage scopes are approved."
            ),
        },
        "cftc_general_press_releases": {
            "source_id": "cftc_general_press_releases",
            "provider_id": "cftc_general_press_releases",
            "display_name": "U.S. Commodity Futures Trading Commission general press releases RSS",
            "source_type": "REGULATORY",
            "source_url": "https://www.cftc.gov/RSS/RSSGP/rssgp.xml",
            "allowed_article_hosts": ["www.cftc.gov", "cftc.gov"],
            "terms_url": "https://www.cftc.gov/sites/default/files/cftc/cftcprivacy.htm",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Project-side conservative requirement pending source-specific access review; use an identifiable operator-reviewed User-Agent.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "Current general press-release feed only; not a complete historical archive and not limited to crypto.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Official feed endpoint verified from the CFTC RSS index. Source terms, automated-access conditions, and persistent-storage scope are not approved; runtime use must remain blocked."
        },
        "federal_reserve_press_releases": {
            "source_id": "federal_reserve_press_releases",
            "provider_id": "federal_reserve_press_releases",
            "display_name": "Federal Reserve Board all press releases RSS",
            "source_type": "PRIMARY_OFFICIAL",
            "source_url": "https://www.federalreserve.gov/feeds/press_all.xml",
            "allowed_article_hosts": ["www.federalreserve.gov", "federalreserve.gov"],
            "terms_url": "https://www.federalreserve.gov/policies.htm",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Project-side conservative requirement pending source-specific access review; use an identifiable operator-reviewed User-Agent.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "Current Board press-release feed; macro/monetary-policy context, not a complete historical archive or crypto-specific event source.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Official feed endpoint verified from the Federal Reserve RSS index. Website policies do not by themselves establish permission for the project's intended persistent storage; runtime use must remain blocked pending review."

        },
        "sec_press_release_archive": {
            "source_id": "sec_press_release_archive",
            "provider_id": "sec_press_release_archive",
            "display_name": "U.S. Securities and Exchange Commission press release archive",
            "source_type": "REGULATORY",
            "source_url": "https://www.sec.gov/newsroom/press-releases",
            "allowed_article_hosts": ["www.sec.gov", "sec.gov"],
            "allowed_archive_path_prefixes": ["/newsroom/press-releases"],
            "terms_url": "https://www.sec.gov/about/developer-resources",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Caller must supply an operator-reviewed User-Agent; archive capture remains blocked pending source approval.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "One explicitly captured official archive page/query segment per invocation; not exhaustive unless all relevant pagination/year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Separate archive source ID so adding archive paths does not invalidate existing RSS source hashes. Runtime use remains blocked pending terms and persistent-storage review."
        },
        "cftc_press_release_archive": {
            "source_id": "cftc_press_release_archive",
            "provider_id": "cftc_press_release_archive",
            "display_name": "U.S. Commodity Futures Trading Commission press release archive",
            "source_type": "REGULATORY",
            "source_url": "https://www.cftc.gov/PressRoom/PressReleases",
            "allowed_article_hosts": ["www.cftc.gov", "cftc.gov"],
            "allowed_archive_path_prefixes": ["/PressRoom/PressReleases", "/PressRoom/IntheNews"],
            "terms_url": "https://www.cftc.gov/WebPolicy/index.htm",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Use an identifiable operator-reviewed User-Agent; archive capture remains blocked pending source approval.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "One explicitly captured official archive page/query segment per invocation; not exhaustive unless all relevant pagination/year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "HTML archive is a separate source from the RSS endpoint, which may be disabled. Runtime use remains blocked pending terms and persistent-storage review."
        },
        "federal_reserve_press_release_archive": {
            "source_id": "federal_reserve_press_release_archive",
            "provider_id": "federal_reserve_press_release_archive",
            "display_name": "Federal Reserve Board press release archive",
            "source_type": "PRIMARY_OFFICIAL",
            "source_url": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
            "allowed_article_hosts": ["www.federalreserve.gov", "federalreserve.gov"],
            "allowed_archive_path_prefixes": ["/newsevents/pressreleases", "/newsevents/pressreleases.htm"],
            "terms_url": "https://www.federalreserve.gov/disclaimer.htm",
            "status": "TERMS_PENDING",
            "terms_sha256": None,
            "terms_content_base64": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "allowed_use_cases": [],
            "user_agent_required": True,
            "user_agent_policy": "Use an identifiable operator-reviewed User-Agent; archive capture remains blocked pending source approval.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "coverage_scope": "One explicitly captured official archive page/year segment per invocation; not exhaustive unless all relevant year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Separate archive source ID preserves the existing RSS source hash. Runtime use remains blocked pending terms and persistent-storage review."
        }
    },
}


def _non_empty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    raw = _non_empty(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return raw


def _https_url(value: Any, field: str) -> str:
    raw = _non_empty(value, field)
    parsed = urlsplit(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTPS URL")
    return raw


def validate_source_entry(entry: dict) -> dict:
    if not isinstance(entry, dict):
        raise ValueError("source entry must be an object")
    source_id = _non_empty(entry.get("source_id"), "source_id")
    provider_id = _non_empty(entry.get("provider_id"), "provider_id")
    if source_id != provider_id:
        raise ValueError("source_id and provider_id must match for runtime policy lookup")
    source_type = _non_empty(entry.get("source_type"), "source_type")
    source_url = _https_url(entry.get("source_url"), "source_url")
    terms_url = _https_url(entry.get("terms_url"), "terms_url")
    if source_id == "sec_press_releases":
        if source_type != "REGULATORY":
            raise ValueError("SEC press releases must remain classified as REGULATORY")
        if source_url != "https://www.sec.gov/news/pressreleases.rss":
            raise ValueError("SEC feed URL must match the reviewed official RSS URL")
        if terms_url != "https://www.sec.gov/about/developer-resources":
            raise ValueError("SEC terms URL must match the reviewed official developer-resources URL")
    hosts = entry.get("allowed_article_hosts")
    if not isinstance(hosts, list) or not hosts or any(not isinstance(host, str) or not host.strip() for host in hosts):
        raise ValueError("allowed_article_hosts must be a non-empty list of hostnames")
    if source_id == "sec_press_releases" and not set(hosts).issubset({"www.sec.gov", "sec.gov"}):
        raise ValueError("SEC article host allowlist may contain only sec.gov hosts")
    archive_prefixes = entry.get("allowed_archive_path_prefixes", [])
    if (
        not isinstance(archive_prefixes, list)
        or any(not isinstance(prefix, str) or not prefix.startswith("/") or "?" in prefix or "#" in prefix for prefix in archive_prefixes)
        or len(set(archive_prefixes)) != len(archive_prefixes)
    ):
        raise ValueError("allowed_archive_path_prefixes must be unique absolute URL paths without query or fragment")
    status = _non_empty(entry.get("status"), "status")
    if status not in SOURCE_STATUSES:
        raise ValueError(f"unsupported source status: {status}")

    allowed = entry.get("allowed_use_cases")
    if not isinstance(allowed, list) or any(not isinstance(item, str) for item in allowed):
        raise ValueError("allowed_use_cases must be a list of strings")
    if len(set(allowed)) != len(allowed) or not set(allowed).issubset(SUPPORTED_USE_CASES):
        raise ValueError("allowed_use_cases contains duplicates or unsupported use cases")

    terms_hash = entry.get("terms_sha256")
    reviewed_by = entry.get("reviewed_by")
    reviewed_at = entry.get("reviewed_at")
    if status == "APPROVED":
        if not allowed:
            raise ValueError("approved source must declare allowed_use_cases")
        if not isinstance(terms_hash, str) or not _SOURCE_SHA256.fullmatch(terms_hash):
            raise ValueError("approved source must include a reviewed terms_sha256")
        terms_content = _non_empty(entry.get("terms_content_base64"), "terms_content_base64")
        try:
            terms_bytes = base64.b64decode(terms_content, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("terms_content_base64 must be valid base64") from exc
        if hashlib.sha256(terms_bytes).hexdigest() != terms_hash.lower():
            raise ValueError("terms_sha256 does not match preserved terms_content_base64")
        _non_empty(reviewed_by, "reviewed_by")
        _timestamp(reviewed_at, "reviewed_at")
    elif allowed:
        raise ValueError("non-approved source must not allow use cases")

    rate = entry.get("max_requests_per_second")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
        raise ValueError("max_requests_per_second must be positive")
    if source_id == "sec_press_releases" and rate > 10:
        raise ValueError("SEC source rate must not exceed its published 10 requests/second ceiling")
    max_per_invocation = entry.get("max_requests_per_invocation")
    if isinstance(max_per_invocation, bool) or not isinstance(max_per_invocation, int) or max_per_invocation != 1:
        raise ValueError("this feed adapter must issue exactly one request per invocation")
    if entry.get("parallel_requests") is not False:
        raise ValueError("parallel_requests must be false")
    if entry.get("response_body_policy") != "READ_TO_EOF_NO_LOCAL_SIZE_CAP":
        raise ValueError("response_body_policy must preserve the complete body")
    return deepcopy(entry)


def get_source(source_id: str) -> dict:
    if EVENT_SOURCE_REGISTRY.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError(f"source registry schema must be {REGISTRY_SCHEMA_VERSION}")
    sources = EVENT_SOURCE_REGISTRY.get("sources")
    if not isinstance(sources, dict) or source_id not in sources:
        raise KeyError(f"unknown event source: {source_id}")
    return validate_source_entry(sources[source_id])


def source_entry_sha256(entry: dict) -> str:
    validated = validate_source_entry(entry)
    canonical = json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_is_approved(entry: dict) -> bool:
    return validate_source_entry(entry)["status"] == "APPROVED"
