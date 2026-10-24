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
            "terms_url": "https://www.cftc.gov/WebPolicy/index.htm",
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
            "terms_url": "https://www.federalreserve.gov/disclaimer.htm",
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
            "terms_url": "https://www.sec.gov/files/about/webmaster-faq.htm",
            "access_policy_url": "https://www.sec.gov/about/developer-resources",
            "status": "APPROVED",
            "terms_sha256": "65eed3611c0cd41c17e50a5493855c6ac612f5640f95eca19f9bd749c07be620",
            "terms_content_base64": "PHA+QWxsIEdvdmVybm1lbnQtY3JlYXRlZCBjb250ZW50IG9uIHNlYy5nb3YgYW5kIEVER0FSIHB1YmxpYyBmaWxpbmcgY29udGVudCBhcmUgZnJlZSB0byBhY2Nlc3MgYW5kIHJldXNlLiBTZWUgPGEgaHJlZj0iL3ByaXZhY3kuaHRtI2Rpc3NlbWluYXRpb24iPldlYnNpdGUgRGlzc2VtaW5hdGlvbjwvYT4gZm9yIG91ciBwZXJtaXNzaW9ucyBwb2xpY3kuPC9wPg==",
            "terms_evidence_scope": "Exact HTML paragraph excerpt from the official Webmaster FAQ; full page bytes and SHA-256 are preserved in the Issue 132 policy snapshot artifact.",
            "reviewed_by": "AI-assisted technical review; owner-authorized project scope",
            "reviewed_at": "2026-10-24T02:22:00Z",
            "allowed_use_cases": ["internal_analysis", "persistent_storage"],
            "user_agent_required": True,
            "user_agent_policy": "Use the identifiable project User-Agent recorded in approval_scope; respect SEC fair-access requirements and never crawl unclassified endpoints.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "response_storage_mode": "EXTRACTED_TEXT_EVIDENCE",
            "approval_scope": {
                "allowed_content": {"metadata": True, "official_text": True, "full_html": False, "attachments": False},
                "third_party_content": {"handling": "EXCLUDED", "evidence": "SEC Webmaster FAQ states government-created sec.gov content and EDGAR public filing content are free to access and reuse, while examples of excluded material include stock-art photos. The extractor omits media, embedded payloads, page chrome, and labels of external links; it never follows those external links."},
                "retention": {
                    "stored_fields": ["source_id", "requested_url", "final_url", "captured_at", "http_status", "raw_response_bytes", "raw_response_sha256", "text_evidence_base64", "text_evidence_sha256", "text_evidence_bytes", "provider_policy_assessments"],
                    "duration": "Until the official policy or approved scope changes, or the project owner revokes approval.",
                    "deletion_or_recheck_rule": "Re-check the official policy snapshot and registry hash before a new capture batch; suspend capture and remove stored text evidence if the source scope is no longer supported."
                },
                "attribution": {"required": True, "format": "Source: U.S. Securities and Exchange Commission (SEC), with the canonical press-release URL."},
                "automated_access": {
                    "approved_endpoint": "https://www.sec.gov/newsroom/press-releases",
                    "user_agent": "CryptoIntelligenceIssue132PolicyReview/1.0 (contact: repository maintainer)",
                    "max_aggregate_requests_per_second": 1,
                    "timeout_seconds": 20,
                    "redirect_policy": "HTTPS redirects only to allowlisted SEC hosts and approved press-release paths."
                },
                "limitations": ["No RSS authorization is inherited from this archive record.", "Do not persist full HTML, attachments, images, graphics, logos, or external-link labels.", "Do not infer an asset identity from ticker or title alone.", "Temporal association does not establish causality.", "One request per invocation; no parallel requests."],
                "decision_rationale": "The SEC Webmaster FAQ explicitly permits reuse of government-created SEC content and EDGAR public filing content. Approval is restricted to official text and metadata, with external/embedded content excluded and SEC fair-access controls applied."
            },
            "coverage_scope": "One explicitly captured official archive page/query segment per invocation; not exhaustive unless all relevant pagination/year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Archive-only authorization. Full HTML and attachments are not persisted; RSS remains separately gated."
        },
        "cftc_press_release_archive": {
            "source_id": "cftc_press_release_archive",
            "provider_id": "cftc_press_release_archive",
            "display_name": "U.S. Commodity Futures Trading Commission press release archive",
            "source_type": "REGULATORY",
            "source_url": "https://www.cftc.gov/PressRoom/PressReleases",
            "allowed_article_hosts": ["www.cftc.gov", "cftc.gov"],
            "allowed_archive_path_prefixes": ["/PressRoom/PressReleases"],
            "terms_url": "https://www.cftc.gov/WebPolicy/index.htm",
            "status": "APPROVED",
            "terms_sha256": "22d2072bca694e4b67820ccd72544ef03b00acf1229a6c58f25b1d72d0eb5448",
            "terms_content_base64": "PHA+R292ZXJubWVudCBpbmZvcm1hdGlvbiBhdCB0aGUgQ0ZUQyB3ZWJzaXRlIGlzIGluIHRoZSBwdWJsaWMgZG9tYWluLiBQdWJsaWMgZG9tYWluIGluZm9ybWF0aW9uIG1heSBiZSBmcmVlbHkgZGlzdHJpYnV0ZWQgYW5kIGNvcGllZCwgYnV0IGl0IGlzIHJlcXVlc3RlZCB0aGF0IGluIGFueSBzdWJzZXF1ZW50IHVzZSB0aGUgQ0ZUQyBiZSBnaXZlbiBhcHByb3ByaWF0ZSBhY2tub3dsZWRnZW1lbnQuIFdoZW4gdXNpbmcgdGhlIENGVEMgd2Vic2l0ZSwgeW91IG1heSBlbmNvdW50ZXIgZG9jdW1lbnRzLCBpbGx1c3RyYXRpb25zLCBwaG90b2dyYXBocywgb3Igb3RoZXIgaW5mb3JtYXRpb24gcmVzb3VyY2VzIGNvbnRyaWJ1dGVkIG9yIGxpY2Vuc2VkIGJ5IHByaXZhdGUgaW5kaXZpZHVhbHMsIGNvbXBhbmllcywgb3Igb3JnYW5pemF0aW9ucyB0aGF0IG1heSBiZSBwcm90ZWN0ZWQgYnkgVS5TLiBhbmQgZm9yZWlnbiBjb3B5cmlnaHQgbGF3cy4gVHJhbnNtaXNzaW9uIG9yIHJlcHJvZHVjdGlvbiBvZiBwcm90ZWN0ZWQgaXRlbXMgYmV5b25kIHRoYXQgYWxsb3dlZCBieSBmYWlyIHVzZSBhcyBkZWZpbmVkIGluIHRoZSBjb3B5cmlnaHQgbGF3cyByZXF1aXJlcyB0aGUgd3JpdHRlbiBwZXJtaXNzaW9uIG9mIHRoZSBjb3B5cmlnaHQgb3duZXJzLjwvcD4=",
            "terms_evidence_scope": "Exact HTML paragraph excerpt from the official CFTC Web Policy; full page bytes and SHA-256 are preserved in the Issue 132 policy snapshot artifact.",
            "reviewed_by": "AI-assisted technical review; owner-authorized project scope",
            "reviewed_at": "2026-10-24T02:22:00Z",
            "allowed_use_cases": ["internal_analysis", "persistent_storage"],
            "user_agent_required": True,
            "user_agent_policy": "Use the identifiable project User-Agent recorded in approval_scope; do not request the CFTC RSS endpoint while its official status page says disabled.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "response_storage_mode": "EXTRACTED_TEXT_EVIDENCE",
            "approval_scope": {
                "allowed_content": {"metadata": True, "official_text": True, "full_html": False, "attachments": False},
                "third_party_content": {"handling": "EXCLUDED", "evidence": "CFTC Web Policy states government information is public domain with attribution and warns that contributed/licensed third-party documents, illustrations, photographs, and other resources may be protected. The extractor omits media, embedded payloads, page chrome, and labels of external links; it never follows external links."},
                "retention": {
                    "stored_fields": ["source_id", "requested_url", "final_url", "captured_at", "http_status", "raw_response_bytes", "raw_response_sha256", "text_evidence_base64", "text_evidence_sha256", "text_evidence_bytes", "provider_policy_assessments"],
                    "duration": "Until the official policy or approved scope changes, or the project owner revokes approval.",
                    "deletion_or_recheck_rule": "Re-check the official policy snapshot and registry hash before a new capture batch; suspend capture and remove stored text evidence if the source scope is no longer supported."
                },
                "attribution": {"required": True, "format": "Source: U.S. Commodity Futures Trading Commission (CFTC), with the canonical press-release URL."},
                "automated_access": {
                    "approved_endpoint": "https://www.cftc.gov/PressRoom/PressReleases",
                    "user_agent": "CryptoIntelligenceIssue132PolicyReview/1.0 (contact: repository maintainer)",
                    "max_aggregate_requests_per_second": 1,
                    "timeout_seconds": 20,
                    "redirect_policy": "HTTPS redirects only to allowlisted CFTC hosts and approved press-release paths."
                },
                "limitations": ["CFTC RSS remains disabled and is not polled.", "Do not persist full HTML, attachments, images, graphics, logos, or external-link labels.", "Do not infer an asset identity from ticker or title alone.", "Temporal association does not establish causality.", "One request per invocation; no parallel requests."],
                "decision_rationale": "The CFTC Web Policy permits copying public-domain government information with attribution. Approval is restricted to official text and metadata, with contributed/licensed third-party content excluded and RSS disabled."
            },
            "coverage_scope": "One explicitly captured official archive page/query segment per invocation; not exhaustive unless all relevant pagination/year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Archive-only authorization. CFTC RSS is a separate source and remains unrequested while disabled."
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
            "status": "APPROVED",
            "terms_sha256": "7069bc3163ce548b4f2f5e837f78dd4b3427c491a93cd867735baeb6f653a04d",
            "terms_content_base64": "PHA+VW5sZXNzIG90aGVyd2lzZSBpbmRpY2F0ZWQsIGluZm9ybWF0aW9uIG9uIEJvYXJkJ3Mgd2Vic2l0ZSBpcyBpbiB0aGUgcHVibGljIGRvbWFpbiBhbmQgbWF5IGJlIGNvcGllZCBhbmQgZGlzdHJpYnV0ZWQgd2l0aG91dCBwZXJtaXNzaW9uLiBQbGVhc2UgY2l0ZSB0byB0aGUgQm9hcmQgYXMgdGhlIHNvdXJjZSBvZiB0aGUgaW5mb3JtYXRpb24uIEZvciBhbnkgcGhvdG8sIGdyYXBoaWMsIG9yIG90aGVyIG1hdGVyaWFsIHRoYXQgaXMgaWRlbnRpZmllZCBhcyBiZWluZyBhc3NvY2lhdGVkIHdpdGggYSBub24tQm9hcmQgKHN1Y2ggYXMgbWF0ZXJpYWxzIHdpdGggYSBjb3B5cmlnaHQgb3IgdHJhZGVtYXJrKSBwZXJtaXNzaW9uIHRvIGNvcHkgYW5kIGRpc3RyaWJ1dGUgc3VjaCBwaG90bywgZ3JhcGhpYywgb3IgbWF0ZXJpYWwgbXVzdCBiZSBvYnRhaW5lZCBmcm9tIHRoZSBub24tQm9hcmQgc291cmNlLjwvcD4=",
            "terms_evidence_scope": "Exact HTML paragraph excerpt from the official Federal Reserve disclaimer; full page bytes and SHA-256 are preserved in the Issue 132 policy snapshot artifact.",
            "reviewed_by": "AI-assisted technical review; owner-authorized project scope",
            "reviewed_at": "2026-10-24T02:22:00Z",
            "allowed_use_cases": ["internal_analysis", "persistent_storage"],
            "user_agent_required": True,
            "user_agent_policy": "Use the identifiable project User-Agent recorded in approval_scope; one request per invocation and no parallel requests.",
            "max_requests_per_second": 1,
            "max_requests_per_invocation": 1,
            "parallel_requests": False,
            "response_body_policy": "READ_TO_EOF_NO_LOCAL_SIZE_CAP",
            "response_storage_mode": "EXTRACTED_TEXT_EVIDENCE",
            "approval_scope": {
                "allowed_content": {"metadata": True, "official_text": True, "full_html": False, "attachments": False},
                "third_party_content": {"handling": "EXCLUDED", "evidence": "The Federal Reserve disclaimer permits copying public-domain Board information with attribution and requires permission for identified non-Board material. The extractor omits media, embedded payloads, page chrome, and labels of external links; it never follows external links."},
                "retention": {
                    "stored_fields": ["source_id", "requested_url", "final_url", "captured_at", "http_status", "raw_response_bytes", "raw_response_sha256", "text_evidence_base64", "text_evidence_sha256", "text_evidence_bytes", "provider_policy_assessments"],
                    "duration": "Until the official policy or approved scope changes, or the project owner revokes approval.",
                    "deletion_or_recheck_rule": "Re-check the official policy snapshot and registry hash before a new capture batch; suspend capture and remove stored text evidence if the source scope is no longer supported."
                },
                "attribution": {"required": True, "format": "Source: Board of Governors of the Federal Reserve System, with the canonical press-release URL."},
                "automated_access": {
                    "approved_endpoint": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
                    "user_agent": "CryptoIntelligenceIssue132PolicyReview/1.0 (contact: repository maintainer)",
                    "max_aggregate_requests_per_second": 1,
                    "timeout_seconds": 20,
                    "redirect_policy": "HTTPS redirects only to allowlisted Federal Reserve hosts and approved press-release paths."
                },
                "limitations": ["RSS authorization is separate and not inherited from this archive record.", "Do not persist full HTML, attachments, images, graphics, logos, or external-link labels.", "Do not infer an asset identity from ticker or title alone.", "Temporal association does not establish causality.", "One request per invocation; no parallel requests."],
                "decision_rationale": "The Federal Reserve disclaimer permits copying Board public-domain information with attribution, subject to third-party material exceptions. Approval is restricted to official text and metadata, with non-Board content excluded."
            },
            "coverage_scope": "One explicitly captured official archive page/year segment per invocation; not exhaustive unless all relevant year segments are recorded.",
            "entity_resolution_policy": "No asset identity is inferred from title, ticker, or description.",
            "notes": "Archive-only authorization. Full HTML and attachments are not persisted; RSS remains separately gated."
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
    expected_source_terms = {
        "sec_press_releases": ("REGULATORY", "https://www.sec.gov/news/pressreleases.rss", "https://www.sec.gov/about/developer-resources"),
        "cftc_general_press_releases": ("REGULATORY", "https://www.cftc.gov/RSS/RSSGP/rssgp.xml", "https://www.cftc.gov/WebPolicy/index.htm"),
        "federal_reserve_press_releases": ("PRIMARY_OFFICIAL", "https://www.federalreserve.gov/feeds/press_all.xml", "https://www.federalreserve.gov/disclaimer.htm"),
    }
    expected = expected_source_terms.get(source_id)
    if expected is not None:
        expected_type, expected_source_url, expected_terms_url = expected
        if source_type != expected_type:
            raise ValueError(f"{source_id} source_type must match the reviewed official source classification")
        if source_url != expected_source_url:
            raise ValueError(f"{source_id} source_url must match the reviewed official endpoint")
        if terms_url != expected_terms_url:
            raise ValueError(f"{source_id} terms_url must match the official policy URL documented for review")
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
        _validate_approval_scope(entry)
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


def _validate_approval_scope(entry: dict) -> None:
    """Require an explicit, source-specific decision scope before runtime approval."""
    scope = entry.get("approval_scope")
    if not isinstance(scope, dict):
        raise ValueError("approved source must include approval_scope")

    content = scope.get("allowed_content")
    content_fields = {"metadata", "official_text", "full_html", "attachments"}
    if not isinstance(content, dict) or set(content) != content_fields or any(
        not isinstance(content[field], bool) for field in content_fields
    ):
        raise ValueError("approval_scope.allowed_content must explicitly decide metadata, official_text, full_html, and attachments")

    third_party = scope.get("third_party_content")
    if not isinstance(third_party, dict):
        raise ValueError("approval_scope.third_party_content must be an object")
    handling = third_party.get("handling")
    if handling not in {"EXCLUDED", "NON_PERSISTENT", "AUTHORIZED_WITH_EVIDENCE"}:
        raise ValueError("approval_scope.third_party_content.handling is unsupported")
    if handling == "AUTHORIZED_WITH_EVIDENCE":
        _non_empty(third_party.get("evidence"), "approval_scope.third_party_content.evidence")

    retention = scope.get("retention")
    if not isinstance(retention, dict):
        raise ValueError("approval_scope.retention must be an object")
    stored_fields = retention.get("stored_fields")
    if not isinstance(stored_fields, list) or not stored_fields or any(
        not isinstance(item, str) or not item.strip() for item in stored_fields
    ):
        raise ValueError("approval_scope.retention.stored_fields must be a non-empty list of strings")
    _non_empty(retention.get("duration"), "approval_scope.retention.duration")
    _non_empty(retention.get("deletion_or_recheck_rule"), "approval_scope.retention.deletion_or_recheck_rule")

    attribution = scope.get("attribution")
    if not isinstance(attribution, dict) or not isinstance(attribution.get("required"), bool):
        raise ValueError("approval_scope.attribution.required must be boolean")
    _non_empty(attribution.get("format"), "approval_scope.attribution.format")

    access = scope.get("automated_access")
    if not isinstance(access, dict):
        raise ValueError("approval_scope.automated_access must be an object")
    endpoint = _https_url(access.get("approved_endpoint"), "approval_scope.automated_access.approved_endpoint")
    endpoint_parts = urlsplit(endpoint)
    allowed_hosts = set(entry.get("allowed_article_hosts") or [])
    if endpoint_parts.hostname not in allowed_hosts:
        raise ValueError("approval_scope.automated_access.approved_endpoint host is outside allowed_article_hosts")
    archive_prefixes = entry.get("allowed_archive_path_prefixes") or []
    endpoint_path = endpoint_parts.path or "/"
    if archive_prefixes and not any(
        endpoint_path == prefix or endpoint_path.startswith(prefix.rstrip("/") + "/")
        for prefix in archive_prefixes
    ):
        raise ValueError("approval_scope.automated_access.approved_endpoint path is outside allowed_archive_path_prefixes")
    _non_empty(access.get("user_agent"), "approval_scope.automated_access.user_agent")
    max_rate = access.get("max_aggregate_requests_per_second")
    if isinstance(max_rate, bool) or not isinstance(max_rate, (int, float)) or max_rate <= 0:
        raise ValueError("approval_scope.automated_access.max_aggregate_requests_per_second must be positive")
    registry_rate = entry.get("max_requests_per_second")
    if isinstance(registry_rate, bool) or not isinstance(registry_rate, (int, float)) or registry_rate <= 0:
        raise ValueError("max_requests_per_second must be positive before approval scope validation")
    if max_rate > registry_rate:
        raise ValueError("approval_scope aggregate request rate exceeds the source registry ceiling")
    timeout = access.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("approval_scope.automated_access.timeout_seconds must be positive")
    _non_empty(access.get("redirect_policy"), "approval_scope.automated_access.redirect_policy")

    limitations = scope.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(item, str) or not item.strip() for item in limitations):
        raise ValueError("approval_scope.limitations must be a list of non-empty strings")
    _non_empty(scope.get("decision_rationale"), "approval_scope.decision_rationale")


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
