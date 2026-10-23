"""Join validated event, fundamental/on-chain, and methodology evidence into a report.

This is an offline integration layer. It does not fetch sources, train/evaluate models,
approve methodology, infer causality, or issue investment recommendations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scripts.market_selection.external_event_evidence import assess_temporal_association, parse_timestamp, validate_event
from scripts.market_selection.fundamental_onchain_contract import evaluate_observations
from scripts.market_selection.analyze_multi_timeframe_support_resistance import analyze_multi_timeframe_support_resistance
from scripts.market_selection.methodology_contract import validate_methodology
from scripts.market_selection.provider_license_gate import evaluate_artifact_use, evaluate_provider_use
from scripts.market_selection.event_source_registry import get_source, source_entry_sha256, source_is_approved
from scripts.market_selection.capture_sec_press_releases_rss import parse_sec_press_releases_rss
from scripts.market_selection.capture_public_event_feed import _parse_feed as _parse_public_feed

REPORT_SCHEMA = "crypto-asset-research-report-v2"
BUNDLE_SCHEMA = "crypto-research-evidence-bundle-v1"
SUPPORT_RESISTANCE_INPUT_SCHEMA = "research-support-resistance-input-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FUNDAMENTAL_SOURCE_BINDINGS = {
    "defillama-free-api": {
        "provider_id": "defillama_api",
        "allowed_host": "api.llama.fi",
        "allowed_path_prefix": "/protocol/",
    },
}


def _object(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp with offset")
    return value.strip()


def _movement_episode_window(report: dict, episode_id: str) -> tuple[dict, dict]:
    """Resolve an evidence window from a report's confirmed-pivot episode."""
    analyses = _object(report.get("descriptive_analyses"), "report.descriptive_analyses")
    episodes_artifact = _object(analyses.get("movement_episodes"), "report.descriptive_analyses.movement_episodes")
    episodes = episodes_artifact.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError("report movement_episodes.episodes must be a list")
    matches = [
        episode for episode in episodes
        if isinstance(episode, dict) and episode.get("episode_id") == episode_id
    ]
    if len(matches) != 1:
        raise ValueError(f"movement_episode_id must identify exactly one report episode: {episode_id}")
    episode = matches[0]
    start = _object(episode.get("start"), f"movement episode {episode_id}.start")
    end = _object(episode.get("end"), f"movement episode {episode_id}.end")
    start_ms = start.get("pivot_open_time_ms")
    end_ms = end.get("pivot_open_time_ms")
    for value, field in ((start_ms, "start.pivot_open_time_ms"), (end_ms, "end.pivot_open_time_ms")):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"movement episode {episode_id}.{field} must be a non-negative integer")
    if end_ms < start_ms:
        raise ValueError(f"movement episode {episode_id} end precedes start")
    def iso_utc(timestamp_ms: int) -> str:
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return (
        {"start": iso_utc(start_ms), "end": iso_utc(end_ms)},
        {
            "episode_id": episode_id,
            "direction": episode.get("direction"),
            "classification": episode.get("classification"),
            "segment_index": episode.get("segment_index"),
            "start_pivot_open_time_ms": start_ms,
            "end_pivot_open_time_ms": end_ms,
            "episode_observable_only_at_ms": episode.get("episode_observable_only_at_ms"),
        },
    )



def _verify_fundamental_observation_sources(
    observations: list[dict],
    authorization_registry: dict | None = None,
) -> list[dict]:
    """Require explicit provider authorization for every fundamental observation consumed.

    The report-level market-data gate does not cover the separate observations argument.
    Authorization records are resolved only from trusted runtime configuration, never from
    caller-supplied observation metadata. Each source must be approved for both use cases.
    """
    if authorization_registry is None:
        authorization_registry = {}
    if not isinstance(authorization_registry, dict):
        raise PermissionError("trusted provider authorization registry must be an object")
    assessments = []
    for index, raw_observation in enumerate(observations):
        observation = _object(raw_observation, f"observations[{index}]")
        source = _object(observation.get("source"), f"observations[{index}].source")
        source_id = source.get("source_id")
        provider_id = source.get("provider_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise PermissionError(f"fundamental source id missing at observations[{index}]")
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise PermissionError(f"fundamental provider id missing at observations[{index}]")
        binding = FUNDAMENTAL_SOURCE_BINDINGS.get(source_id)
        if binding is None:
            raise PermissionError(f"fundamental source is not registered at observations[{index}]")
        if provider_id != binding["provider_id"]:
            raise PermissionError(f"fundamental provider id does not match source registry at observations[{index}]")
        source_url = source.get("url")
        parsed_source_url = urlsplit(source_url) if isinstance(source_url, str) else None
        if (
            parsed_source_url is None
            or parsed_source_url.scheme != "https"
            or parsed_source_url.hostname != binding["allowed_host"]
            or parsed_source_url.port not in (None, 443)
            or parsed_source_url.username is not None
            or parsed_source_url.password is not None
            or not parsed_source_url.path.startswith(binding["allowed_path_prefix"])
        ):
            raise PermissionError(f"fundamental source URL is outside registry allowlist at observations[{index}]")
        if source.get("terms_status") != "APPROVED":
            raise PermissionError(
                f"fundamental source terms are not approved at observations[{index}]"
            )
        # Do not accept source.authorization_record: observations are input evidence,
        # not a trust anchor. Only deployment-controlled configuration can authorize a provider.
        authorization_record = authorization_registry.get(provider_id)
        for use_case in ("internal_analysis", "persistent_storage"):
            try:
                assessment = evaluate_provider_use(provider_id, use_case, authorization_record)
            except ValueError as exc:
                raise PermissionError(
                    f"fundamental provider authorization is invalid at observations[{index}]"
                ) from exc
            if assessment.get("decision") != "ALLOW":
                reasons = ",".join(assessment.get("reason_codes") or ["PROVIDER_USE_BLOCKED"])
                raise PermissionError(
                    f"fundamental provider {provider_id} blocked for {use_case} "
                    f"at observations[{index}]: {reasons}"
                )
            assessments.append({
                "observation_id": observation.get("observation_id"),
                "source_id": source_id,
                "provider_id": provider_id,
                **assessment,
            })
    return assessments


def _verify_source_capture(
    capture: dict,
    *,
    field: str,
    source_entry: dict,
    registry_hash: str,
    expected_requested_url: str,
) -> bytes:
    capture = _object(capture, field)
    if capture.get("capture_status") != "PASS" or capture.get("capture_truncated") is not False:
        raise PermissionError(f"{field} is not a complete PASS capture")
    if capture.get("network_request_made") is not True:
        raise PermissionError(f"{field} does not prove a network capture")
    if capture.get("source_registry_status") != "APPROVED":
        raise PermissionError(f"{field} source registry was not approved")
    if capture.get("source_registry_entry_sha256") != registry_hash:
        raise PermissionError(f"{field} source registry hash is stale")
    if capture.get("source_url") != source_entry["source_url"]:
        raise PermissionError(f"{field} source URL does not match registry")
    if capture.get("requested_url") != expected_requested_url:
        raise PermissionError(f"{field} requested URL does not match expected source")
    for key, use_case in (
        ("provider_use_assessment", "internal_analysis"),
        ("persistent_storage_assessment", "persistent_storage"),
    ):
        assessment = _object(capture.get(key), f"{field}.{key}")
        if assessment.get("provider_id") != source_entry["provider_id"] or assessment.get("decision") != "ALLOW":
            raise PermissionError(f"{field} does not authorize {use_case}")
    encoded = capture.get("raw_response_base64")
    if not isinstance(encoded, str):
        raise PermissionError(f"{field} raw response bytes are missing")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError(f"{field} raw response base64 is invalid") from exc
    digest = capture.get("raw_response_sha256")
    size = capture.get("raw_response_bytes")
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise PermissionError(f"{field} raw response SHA-256 is invalid")
    if hashlib.sha256(raw).hexdigest() != digest:
        raise PermissionError(f"{field} raw response SHA-256 mismatch")
    if isinstance(size, bool) or not isinstance(size, int) or len(raw) != size:
        raise PermissionError(f"{field} raw response byte count mismatch")
    return raw


def _verify_promoted_sec_event(event_record: dict, source_entry: dict, registry_hash: str) -> None:
    captures = _object(event_record.get("source_capture_assessments"), "event.source_capture_assessments")
    feed_capture = _object(captures.get("feed"), "event.source_capture_assessments.feed")
    article_capture = _object(captures.get("article"), "event.source_capture_assessments.article")
    event_source = _object(event_record.get("source"), "event.source")
    event_url = event_source.get("url")

    feed_raw = _verify_source_capture(
        feed_capture, field="event.feed_capture", source_entry=source_entry,
        registry_hash=registry_hash, expected_requested_url=source_entry["source_url"],
    )
    article_raw = _verify_source_capture(
        article_capture, field="event.article_capture", source_entry=source_entry,
        registry_hash=registry_hash, expected_requested_url=event_url,
    )
    content_type = next(
        (value.split(";", 1)[0].strip().lower() for key, value in article_capture.get("response_headers", {}).items()
         if key.lower() == "content-type"),
        "",
    )
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise PermissionError("event article capture has an unexpected Content-Type")
    if article_capture.get("captured_at") != event_record.get("captured_at"):
        raise PermissionError("event captured_at does not match article capture time")

    metadata = _object(event_record.get("metadata"), "event.metadata")
    feed_hash = feed_capture["raw_response_sha256"]
    article_hash = article_capture["raw_response_sha256"]
    if metadata.get("feed_raw_response_sha256") != feed_hash:
        raise PermissionError("event feed response hash does not match preserved capture")
    if metadata.get("article_raw_response_sha256") != article_hash or event_record.get("content_sha256") != article_hash:
        raise PermissionError("event article hash does not match preserved capture")

    try:
        parsed_items = parse_sec_press_releases_rss(feed_raw)
    except (ET.ParseError, ValueError) as exc:
        raise PermissionError("event feed capture is not valid RSS/RDF") from exc
    item_id = metadata.get("feed_item_id")
    matched = next((item for item in parsed_items if item.get("item_id") == item_id), None)
    if matched is None:
        raise PermissionError("event feed item is not present in preserved RSS bytes")
    item_record = _object(metadata.get("feed_item_record"), "event.metadata.feed_item_record")
    for key in ("item_id", "title", "link", "published_at_utc", "normalized_item_sha256"):
        if item_record.get(key) != matched.get(key):
            raise PermissionError(f"event feed item metadata mismatch: {key}")
    if metadata.get("normalized_feed_item_sha256") != matched.get("normalized_item_sha256"):
        raise PermissionError("event normalized feed item hash mismatch")
    if (
        event_record.get("title") != matched.get("title")
        or event_record.get("published_at") != matched.get("published_at_utc")
        or event_url != matched.get("link")
    ):
        raise PermissionError("event title, URL, or publication time is not grounded in the captured feed")
    if article_capture.get("requested_url") != matched.get("link"):
        raise PermissionError("article capture URL does not match the RSS item")

    mapping_b64 = metadata.get("entity_resolution_evidence_record_base64")
    mapping_hash = metadata.get("entity_resolution_evidence_record_sha256")
    if not isinstance(mapping_b64, str) or not isinstance(mapping_hash, str) or not _SHA256_RE.fullmatch(mapping_hash):
        raise PermissionError("reviewed entity-mapping evidence is missing")
    try:
        mapping_raw = base64.b64decode(mapping_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("reviewed entity-mapping evidence base64 is invalid") from exc
    if hashlib.sha256(mapping_raw).hexdigest() != mapping_hash:
        raise PermissionError("reviewed entity-mapping evidence SHA-256 mismatch")
    reviewer = metadata.get("entity_resolution_reviewed_by")
    reviewed_at = metadata.get("entity_resolution_reviewed_at")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise PermissionError("reviewed entity-mapping reviewer is missing")
    try:
        parse_timestamp(reviewed_at, "entity_resolution_reviewed_at")
    except ValueError as exc:
        raise PermissionError("reviewed entity-mapping timestamp is invalid") from exc
    if metadata.get("causality_status") != "NOT_ASSESSED":
        raise PermissionError("event evidence must not claim causality")


def _verify_promoted_public_feed_event(event_record: dict, source_entry: dict, registry_hash: str) -> None:
    captures = _object(event_record.get("source_capture_assessments"), "event.source_capture_assessments")
    feed_capture = _object(captures.get("feed"), "event.source_capture_assessments.feed")
    event_source = _object(event_record.get("source"), "event.source")
    event_url = event_source.get("url")
    feed_raw = _verify_source_capture(
        feed_capture,
        field="event.feed_capture",
        source_entry=source_entry,
        registry_hash=registry_hash,
        expected_requested_url=source_entry["source_url"],
    )
    captures = _object(event_record.get("source_capture_assessments"), "event.source_capture_assessments")
    article_capture = _object(captures.get("article"), "event.source_capture_assessments.article")
    article_raw = _verify_source_capture(
        article_capture,
        field="event.article_capture",
        source_entry=source_entry,
        registry_hash=registry_hash,
        expected_requested_url=event_url,
    )
    metadata = _object(event_record.get("metadata"), "event.metadata")
    if article_capture.get("candidate_id") != metadata.get("feed_candidate_id"):
        raise PermissionError("article capture candidate ID does not match event metadata")
    content_type = next(
        (value.split(";", 1)[0].strip().lower() for key, value in article_capture.get("response_headers", {}).items()
         if key.lower() == "content-type"),
        "",
    )
    if article_capture.get("http_status") != 200:
        raise PermissionError("event article capture did not return HTTP 200")
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise PermissionError("event article capture has an unexpected Content-Type")
    if article_capture.get("captured_at") != event_record.get("captured_at"):
        raise PermissionError("event captured_at does not match article capture time")
    if parse_timestamp(article_capture.get("captured_at"), "article_capture.captured_at") < parse_timestamp(
        feed_capture.get("captured_at"), "feed_capture.captured_at"
    ):
        raise PermissionError("article capture precedes feed capture")
    final_url = article_capture.get("final_url")
    final_parts = urlsplit(final_url) if isinstance(final_url, str) else None
    allowed_hosts = {host.casefold() for host in source_entry.get("allowed_article_hosts", [])}
    if (
        final_parts is None
        or final_parts.scheme != "https"
        or (final_parts.hostname or "").casefold() not in allowed_hosts
        or final_parts.port not in (None, 443)
        or final_parts.username is not None
        or final_parts.password is not None
    ):
        raise PermissionError("article final URL is outside the source allowlist")
    if metadata.get("feed_raw_response_sha256") != feed_capture.get("raw_response_sha256"):
        raise PermissionError("event feed response hash does not match preserved capture")
    if (
        metadata.get("article_raw_response_sha256") != article_capture.get("raw_response_sha256")
        or event_record.get("content_sha256") != article_capture.get("raw_response_sha256")
        or hashlib.sha256(article_raw).hexdigest() != event_record.get("content_sha256")
    ):
        raise PermissionError("event article hash does not match preserved article capture")
    try:
        parsed_items, _, _ = _parse_public_feed(feed_raw, source_entry)
    except (ET.ParseError, ValueError) as exc:
        raise PermissionError("event feed capture is not valid RSS/Atom") from exc
    candidate_id = metadata.get("feed_candidate_id")
    matched = next((item for item in parsed_items if item.get("candidate_id") == candidate_id), None)
    if matched is None:
        raise PermissionError("event candidate is not present in preserved feed bytes")
    item_record = _object(metadata.get("feed_item_record"), "event.metadata.feed_item_record")
    for key in ("candidate_id", "title", "url", "guid", "published_at", "publication_time_status", "item_xml_sha256"):
        if item_record.get(key) != matched.get(key):
            raise PermissionError(f"event feed item metadata mismatch: {key}")
    if (
        event_record.get("title") != matched.get("title")
        or event_record.get("published_at") != matched.get("published_at")
        or event_url != matched.get("url")
        or article_capture.get("requested_url") != matched.get("url")
    ):
        raise PermissionError("event title, URL, or publication time is not grounded in captured feed/article")
    if matched.get("url_status") != "ALLOWLISTED_SOURCE_HOST" or matched.get("publication_time_status") != "PARSED":
        raise PermissionError("event candidate did not pass URL and publication-time eligibility")
    mapping_b64 = metadata.get("entity_resolution_evidence_record_base64")
    mapping_hash = metadata.get("entity_resolution_evidence_record_sha256")
    if not isinstance(mapping_b64, str) or not isinstance(mapping_hash, str) or not _SHA256_RE.fullmatch(mapping_hash):
        raise PermissionError("reviewed entity-mapping evidence is missing")
    try:
        mapping_raw = base64.b64decode(mapping_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise PermissionError("reviewed entity-mapping evidence base64 is invalid") from exc
    if hashlib.sha256(mapping_raw).hexdigest() != mapping_hash:
        raise PermissionError("reviewed entity-mapping evidence SHA-256 mismatch")
    reviewer = metadata.get("entity_resolution_reviewed_by")
    reviewed_at = metadata.get("entity_resolution_reviewed_at")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise PermissionError("reviewed entity-mapping reviewer is missing")
    try:
        parse_timestamp(reviewed_at, "entity_resolution_reviewed_at")
    except ValueError as exc:
        raise PermissionError("reviewed entity-mapping timestamp is invalid") from exc
    if metadata.get("causality_status") != "NOT_ASSESSED" or event_record.get("causality_claimed") is not False:
        raise PermissionError("generic feed event must not claim causality")


def _assess_support_resistance_input(
    raw_input: dict | None,
    *,
    stable_id: str,
    category: str,
    evaluation_as_of: str,
) -> dict:
    """Analyze caller-supplied, authorized OHLCV artifacts without look-ahead."""
    if raw_input is None:
        return {
            "status": "NOT_AVAILABLE",
            "reason_code": "NO_SUPPORT_RESISTANCE_INPUT_SUPPLIED",
            "analysis": None,
        }
    source = _object(raw_input, "support_resistance_input")
    if source.get("schema_version") != SUPPORT_RESISTANCE_INPUT_SCHEMA:
        raise ValueError(f"support_resistance_input.schema_version must be {SUPPORT_RESISTANCE_INPUT_SCHEMA}")
    source_asset = _object(source.get("asset"), "support_resistance_input.asset")
    if (
        not isinstance(source_asset.get("stable_id"), str)
        or source_asset["stable_id"].strip().casefold() != stable_id.strip().casefold()
        or source_asset.get("category") != category
    ):
        raise ValueError("support_resistance_input.asset must match the target stable_id and category")
    mapping_url = source.get("asset_mapping_evidence_url")
    parsed_mapping_url = urlsplit(mapping_url) if isinstance(mapping_url, str) else None
    if (
        parsed_mapping_url is None
        or parsed_mapping_url.scheme != "https"
        or not parsed_mapping_url.hostname
        or parsed_mapping_url.port not in (None, 443)
        or parsed_mapping_url.username is not None
        or parsed_mapping_url.password is not None
    ):
        raise ValueError("support_resistance_input.asset_mapping_evidence_url must be an absolute HTTPS URL")

    artifacts = source.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("support_resistance_input.artifacts must be a non-empty list")
    parameters = _object(source.get("parameters"), "support_resistance_input.parameters")
    allowed_parameters = {"pivot_left", "pivot_right", "tolerance_bps", "confluence_tolerance_bps"}
    unknown_parameters = set(parameters) - allowed_parameters
    if unknown_parameters:
        raise ValueError("support_resistance_input.parameters has unknown fields: " + ",".join(sorted(unknown_parameters)))
    for required in ("pivot_left", "pivot_right", "tolerance_bps"):
        if required not in parameters:
            raise ValueError(f"support_resistance_input.parameters.{required} is required")

    cutoff = parse_timestamp(evaluation_as_of, "evaluation_as_of")
    cutoff_ms = int(cutoff.timestamp() * 1000)
    filtered_artifacts = []
    excluded_after_cutoff = 0
    for artifact_index, raw_artifact in enumerate(artifacts):
        artifact = _object(raw_artifact, f"support_resistance_input.artifacts[{artifact_index}]")
        candles = artifact.get("candles")
        if not isinstance(candles, list):
            raise ValueError(f"support_resistance_input.artifacts[{artifact_index}].candles must be a list")
        eligible_candles = []
        for candle_index, raw_candle in enumerate(candles):
            candle = _object(
                raw_candle,
                f"support_resistance_input.artifacts[{artifact_index}].candles[{candle_index}]",
            )
            close_time_ms = candle.get("close_time_ms")
            if isinstance(close_time_ms, bool) or not isinstance(close_time_ms, int) or close_time_ms < 0:
                raise ValueError("support/resistance candle close_time_ms must be a non-negative integer")
            if close_time_ms > cutoff_ms:
                excluded_after_cutoff += 1
            else:
                eligible_candles.append(candle)
        filtered_artifacts.append({**artifact, "candles": eligible_candles})

    analysis = analyze_multi_timeframe_support_resistance(
        filtered_artifacts,
        pivot_left=parameters["pivot_left"],
        pivot_right=parameters["pivot_right"],
        tolerance_bps=parameters["tolerance_bps"],
        confluence_tolerance_bps=parameters.get("confluence_tolerance_bps"),
    )
    return {
        "status": "ASSESSED",
        "schema_version": SUPPORT_RESISTANCE_INPUT_SCHEMA,
        "evaluation_as_of": cutoff.isoformat().replace("+00:00", "Z"),
        "asset_mapping": {
            "stable_id": stable_id.strip(),
            "category": category,
            "evidence_url": mapping_url,
            "status": "CALLER_SUPPLIED_REQUIRES_REVIEW",
        },
        "input_artifact_count": len(artifacts),
        "excluded_after_cutoff_candle_count": excluded_after_cutoff,
        "analysis": analysis,
        "limitations": [
            "Candles closing after evaluation_as_of are excluded before pivot analysis.",
            "Asset-to-market mapping evidence is supplied by the caller and is not independently verified by this integration layer.",
            "Support/resistance zones are descriptive OHLCV heuristics, not proof of resting orders or guaranteed price reactions.",
        ],
    }


EVENT_FACT_REVIEW_SCHEMA = "crypto-event-fact-review-v1"
_EVENT_FACT_REVIEW_DECISIONS = {
    "VERIFIED_PRIMARY_SOURCE",
    "CONFLICTING_SOURCES",
    "REJECTED",
    "INSUFFICIENT_EVIDENCE",
}
_FACT_REVIEW_EVIDENCE_ROLES = {"PRIMARY_SOURCE", "SECONDARY_SOURCE", "MARKET_DATA", "COUNTER_EVIDENCE"}


def _assess_event_fact_review(event_record: dict, *, evaluation_as_of: str) -> dict:
    """Validate a separately reviewed fact claim; never infer verification from timing."""
    metadata = _object(event_record.get("metadata", {}), "event.metadata")
    review = metadata.get("fact_review")
    if review is None:
        return {
            "schema_version": EVENT_FACT_REVIEW_SCHEMA,
            "status": "NOT_REVIEWED",
            "decision": "NOT_REVIEWED",
            "effective_decision": "NOT_REVIEWED",
            "available_as_of": False,
            "reason": "No explicit fact-review record was supplied; article capture and temporal proximity are not fact verification.",
        }
    review = _object(review, "event.metadata.fact_review")
    if review.get("schema_version") != EVENT_FACT_REVIEW_SCHEMA:
        raise ValueError(f"event.metadata.fact_review.schema_version must be {EVENT_FACT_REVIEW_SCHEMA}")
    event_id = event_record.get("event_id")
    if review.get("event_id") != event_id:
        raise PermissionError("fact review event_id does not match the event")
    decision = review.get("decision")
    if decision not in _EVENT_FACT_REVIEW_DECISIONS:
        raise ValueError("fact review decision is unsupported")
    reviewer = review.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("fact review reviewed_by is required")
    reviewed_at = parse_timestamp(review.get("reviewed_at"), "fact_review.reviewed_at")
    rationale = review.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("fact review rationale is required")
    refs = review.get("evidence_refs")
    if not isinstance(refs, list):
        raise ValueError("fact review evidence_refs must be a list")
    normalized_refs = []
    for index, raw_ref in enumerate(refs):
        ref = _object(raw_ref, f"fact_review.evidence_refs[{index}]")
        url = ref.get("url")
        role = ref.get("role")
        parts = urlsplit(url) if isinstance(url, str) else None
        if (
            parts is None or parts.scheme != "https" or not parts.netloc
            or parts.username is not None or parts.password is not None
        ):
            raise ValueError(f"fact_review.evidence_refs[{index}].url must be an absolute HTTPS URL")
        if role not in _FACT_REVIEW_EVIDENCE_ROLES:
            raise ValueError(f"fact_review.evidence_refs[{index}].role is unsupported")
        publisher = ref.get("publisher", "")
        if not isinstance(publisher, str):
            raise ValueError(f"fact_review.evidence_refs[{index}].publisher must be text")
        normalized_refs.append({"url": url, "role": role, "publisher": publisher.strip()})

    record_b64 = review.get("evidence_record_base64")
    record_hash = review.get("evidence_record_sha256")
    if not isinstance(record_b64, str) or not record_b64:
        raise ValueError("fact review evidence_record_base64 is required")
    if not isinstance(record_hash, str) or not _SHA256_RE.fullmatch(record_hash):
        raise ValueError("fact review evidence_record_sha256 must be a SHA-256")
    try:
        record_bytes = base64.b64decode(record_b64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("fact review evidence_record_base64 is invalid") from exc
    if hashlib.sha256(record_bytes).hexdigest() != record_hash:
        raise PermissionError("fact review evidence record SHA-256 mismatch")
    try:
        record = json.loads(record_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("fact review evidence record must be UTF-8 JSON") from exc
    record = _object(record, "fact review evidence record")
    expected = {
        "schema_version": EVENT_FACT_REVIEW_SCHEMA,
        "event_id": event_id,
        "decision": decision,
        "reviewed_by": reviewer.strip(),
        "reviewed_at": reviewed_at.isoformat().replace("+00:00", "Z"),
        "rationale": rationale.strip(),
        "evidence_refs": normalized_refs,
    }
    if record != expected:
        raise PermissionError("fact review evidence record does not match its declared review fields")
    if decision == "VERIFIED_PRIMARY_SOURCE":
        event_source = _object(event_record.get("source"), "event.source")
        if not any(ref["role"] == "PRIMARY_SOURCE" and ref["url"] == event_source.get("url") for ref in normalized_refs):
            raise ValueError("verified primary-source review must reference the event's primary source URL")
    if decision == "CONFLICTING_SOURCES" and len({ref["url"] for ref in normalized_refs}) < 2:
        raise ValueError("conflicting-sources review must reference at least two distinct URLs")
    if decision in {"REJECTED", "VERIFIED_PRIMARY_SOURCE"} and not normalized_refs:
        raise ValueError("fact review decision requires evidence references")

    cutoff = parse_timestamp(evaluation_as_of, "evaluation_as_of")
    available = reviewed_at <= cutoff
    effective = decision if available else "NOT_AVAILABLE_AS_OF"
    return {
        "schema_version": EVENT_FACT_REVIEW_SCHEMA,
        "status": "REVIEWED" if available else "NOT_AVAILABLE_AS_OF",
        "decision": decision,
        "effective_decision": effective,
        "available_as_of": available,
        "reviewed_by": reviewer.strip(),
        "reviewed_at": reviewed_at.isoformat().replace("+00:00", "Z"),
        "rationale": rationale.strip(),
        "evidence_refs": normalized_refs,
        "evidence_record_sha256": record_hash.lower(),
        "reason": (
            "Fact review is explicitly recorded and available by the evaluation cutoff."
            if available else
            "Fact review occurred after the evaluation cutoff and cannot be used as information available at that time."
        ),
    }


EVENT_SOURCE_COVERAGE_SCHEMA = "crypto-event-source-coverage-v1"
_EVENT_CAPTURE_STATUSES = {"BLOCKED", "NETWORK_ERROR", "PARTIAL", "HTTP_ERROR", "PARSE_ERROR", "PASS"}


def _assess_event_source_coverage(
    raw_coverage: list[dict] | None,
    *,
    evaluation_as_of: str,
) -> dict:
    """Describe what each event-source capture did and did not establish.

    A successful empty feed means only that the returned feed contained no items;
    it is not evidence that no catalyst existed in the source's full history.
    """
    if raw_coverage is None:
        return {
            "schema_version": EVENT_SOURCE_COVERAGE_SCHEMA,
            "status": "NOT_PROVIDED",
            "source_count": 0,
            "sources": [],
            "interpretation": "No source-capture coverage records were supplied; this is not a negative event search.",
        }
    if not isinstance(raw_coverage, list):
        raise ValueError("event_source_coverage must be a list")
    cutoff = parse_timestamp(evaluation_as_of, "evaluation_as_of")
    sources = []
    seen_source_capture_pairs = set()
    for index, raw in enumerate(raw_coverage):
        record = _object(raw, f"event_source_coverage[{index}]")
        source_id = record.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"event_source_coverage[{index}].source_id must be non-empty")
        try:
            source = get_source(source_id)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"event_source_coverage[{index}].source_id is not registered") from exc
        capture_status = record.get("capture_status")
        if capture_status not in _EVENT_CAPTURE_STATUSES:
            raise ValueError(f"event_source_coverage[{index}].capture_status is unsupported")
        captured_at = parse_timestamp(record.get("captured_at"), f"event_source_coverage[{index}].captured_at")
        network_made = record.get("network_request_made")
        truncated = record.get("capture_truncated")
        if not isinstance(network_made, bool) or not isinstance(truncated, bool):
            raise ValueError(f"event_source_coverage[{index}] must declare boolean network_request_made and capture_truncated")
        count = record.get("feed_item_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"event_source_coverage[{index}].feed_item_count must be a non-negative integer")
        scope = record.get("coverage_scope", source.get("coverage_scope"))
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError(f"event_source_coverage[{index}].coverage_scope must be non-empty")
        errors = record.get("errors", [])
        if not isinstance(errors, list):
            raise ValueError(f"event_source_coverage[{index}].errors must be a list")
        source_hash = record.get("source_registry_entry_sha256")
        expected_hash = source_entry_sha256(source)
        if source_hash is not None and (
            not isinstance(source_hash, str) or not _SHA256_RE.fullmatch(source_hash)
        ):
            raise ValueError(f"event_source_coverage[{index}].source_registry_entry_sha256 must be SHA-256")
        key = (source_id, captured_at.isoformat())
        if key in seen_source_capture_pairs:
            raise ValueError("event_source_coverage contains duplicate source/capture records")
        seen_source_capture_pairs.add(key)

        if source_hash is not None and source_hash != expected_hash:
            coverage_status = "STALE_SOURCE_REGISTRY"
        elif captured_at > cutoff:
            coverage_status = "NOT_AVAILABLE_AS_OF"
        elif capture_status == "BLOCKED":
            coverage_status = "BLOCKED_BY_SOURCE_POLICY" if not network_made else "INCONSISTENT_CAPTURE_POLICY"
        elif capture_status == "NETWORK_ERROR":
            coverage_status = "UNAVAILABLE"
        elif capture_status in {"PARTIAL", "HTTP_ERROR", "PARSE_ERROR"} or truncated:
            coverage_status = "PARTIAL_OR_FAILED"
        elif capture_status == "PASS":
            if source.get("status") != "APPROVED" or not network_made:
                coverage_status = "INCONSISTENT_CAPTURE_POLICY"
            elif count == 0:
                coverage_status = "CAPTURED_NO_ITEMS_IN_RETURNED_FEED"
            else:
                coverage_status = "CAPTURED_WITH_ITEMS"
        else:
            coverage_status = "UNCLASSIFIED"
        sources.append({
            "source_id": source_id,
            "source_registry_status": source.get("status"),
            "source_registry_entry_sha256": source_hash,
            "capture_status": capture_status,
            "coverage_status": coverage_status,
            "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
            "coverage_scope": scope.strip(),
            "feed_item_count": count,
            "network_request_made": network_made,
            "capture_truncated": truncated,
            "errors": errors,
            "raw_response_sha256": record.get("raw_response_sha256"),
            "interpretation": (
                "Zero items were present in the returned feed only; this does not establish absence of a catalyst."
                if coverage_status == "CAPTURED_NO_ITEMS_IN_RETURNED_FEED"
                else "Coverage is limited to this source capture and its declared scope; it does not establish absence of a catalyst."
            ),
        })
    statuses = sorted({item["coverage_status"] for item in sources})
    return {
        "schema_version": EVENT_SOURCE_COVERAGE_SCHEMA,
        "status": "ASSESSED",
        "source_count": len(sources),
        "coverage_statuses": statuses,
        "sources": sources,
        "interpretation": "Capture outcomes describe source availability and returned-feed coverage, not proof that no catalyst existed.",
    }


def enrich_research_report(
    report: dict,
    *,
    events: list[dict],
    observations: list[dict],
    methodology: dict,
    asset: dict,
    evaluation_as_of: str,
    provider_authorization_registry: dict | None = None,
    fundamental_freshness_policy_seconds: dict[str, int] | None = None,
    support_resistance_input: dict | None = None,
    event_source_coverage: list[dict] | None = None,
) -> dict:
    """Validate and attach supplied evidence while retaining fail-closed decision states.

    Each event item is an object with an `event` record and a declared `movement_window`
    containing `start` and `end`. Capture/publication timestamps are validated by the
    source-neutral event contract. Observations and methodology use their own versioned
    contracts. The function never upgrades INDETERMINATE to a favorable/unfavorable decision.
    """
    report = _object(report, "report")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError(f"report.schema_version must be {REPORT_SCHEMA}")
    provider_use = evaluate_artifact_use(report, "internal_analysis")
    if provider_use["decision"] != "ALLOW":
        raise PermissionError("evidence integration blocked before use: " + ",".join(provider_use["reason_codes"]))
    provider_storage = evaluate_artifact_use(report, "persistent_storage")
    if provider_storage["decision"] != "ALLOW":
        raise PermissionError("evidence integration storage blocked before use: " + ",".join(provider_storage["reason_codes"]))
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    if not isinstance(observations, list):
        raise ValueError("observations must be a list")
    asset = _object(asset, "asset")
    stable_id = asset.get("stable_id")
    category = asset.get("category")
    if not isinstance(stable_id, str) or not stable_id.strip():
        raise ValueError("asset.stable_id must be a non-empty stable identifier")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("asset.category must be non-empty")
    cutoff = _timestamp(evaluation_as_of, "evaluation_as_of")
    event_coverage_assessment = _assess_event_source_coverage(
        event_source_coverage, evaluation_as_of=cutoff
    )

    validated_methodology = validate_methodology(methodology)
    event_assessments = []
    seen_event_ids = set()
    for index, item in enumerate(events):
        item = _object(item, f"events[{index}]")
        event_record = _object(item.get("event"), f"events[{index}].event")
        event_use = evaluate_artifact_use(event_record, "internal_analysis")
        if event_use["decision"] != "ALLOW":
            raise PermissionError(
                f"event evidence blocked before use at events[{index}]: " + ",".join(event_use["reason_codes"])
            )
        event_storage = evaluate_artifact_use(event_record, "persistent_storage")
        if event_storage["decision"] != "ALLOW":
            raise PermissionError(
                f"event evidence storage blocked before use at events[{index}]: " + ",".join(event_storage["reason_codes"])
            )

        source_id = event_record.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise PermissionError(f"event source registry id missing at events[{index}]")
        try:
            source_entry = get_source(source_id)
        except (KeyError, ValueError) as exc:
            raise PermissionError(f"event source is not registered at events[{index}]") from exc
        if not source_is_approved(source_entry):
            raise PermissionError(f"event source registry is not approved at events[{index}]")
        if event_record.get("provider_id") != source_entry.get("provider_id"):
            raise PermissionError(f"event provider id does not match registry at events[{index}]")
        for assessment_field in ("provider_use_assessment", "persistent_storage_assessment"):
            assessment = _object(event_record.get(assessment_field), f"events[{index}].event.{assessment_field}")
            if assessment.get("provider_id") != source_entry.get("provider_id") or assessment.get("decision") != "ALLOW":
                raise PermissionError(f"event {assessment_field} does not match the approved source at events[{index}]")
        registry_hash = source_entry_sha256(source_entry)
        if (
            event_record.get("source_registry_status") != "APPROVED"
            or event_record.get("source_registry_entry_sha256") != registry_hash
        ):
            raise PermissionError(f"event source registry evidence is missing or stale at events[{index}]")
        if source_id == "sec_press_releases":
            _verify_promoted_sec_event(event_record, source_entry, registry_hash)
        elif event_record.get("capture_method") == "public_event_feed_rss_atom_v1":
            _verify_promoted_public_feed_event(event_record, source_entry, registry_hash)
        else:
            raise PermissionError(f"generic event source requires verified feed-capture evidence at events[{index}]")
        event_source = _object(event_record.get("source"), f"events[{index}].event.source")
        source_url = event_source.get("url")
        parsed_source_url = urlsplit(source_url) if isinstance(source_url, str) else None
        allowed_hosts = set(source_entry.get("allowed_article_hosts") or [])
        if not allowed_hosts:
            base_host = urlsplit(source_entry["source_url"]).hostname
            allowed_hosts = {base_host} if base_host else set()
        if (
            parsed_source_url is None
            or parsed_source_url.scheme != "https"
            or parsed_source_url.hostname not in allowed_hosts
            or parsed_source_url.port not in (None, 443)
            or parsed_source_url.username is not None
            or parsed_source_url.password is not None
        ):
            raise PermissionError(f"event source URL is outside registry allowlist at events[{index}]")
        if event_source.get("source_type") != source_entry.get("source_type"):
            raise PermissionError(f"event source type does not match registry at events[{index}]")
        if event_source.get("publisher") != source_entry.get("display_name"):
            raise PermissionError(f"event publisher does not match registry at events[{index}]")

        event = validate_event(event_record)
        event_id = event["event_id"]
        if event_id in seen_event_ids:
            raise ValueError(f"duplicate event_id in evidence bundle: {event_id}")
        seen_event_ids.add(event_id)
        episode_id = item.get("movement_episode_id")
        if episode_id is not None:
            if not isinstance(episode_id, str) or not episode_id.strip():
                raise ValueError(f"events[{index}].movement_episode_id must be a non-empty string")
            window, episode_context = _movement_episode_window(report, episode_id.strip())
            observable_at = episode_context.get("episode_observable_only_at_ms")
            if (
                isinstance(observable_at, bool)
                or not isinstance(observable_at, int)
                or observable_at < 0
            ):
                raise ValueError(f"movement episode {episode_id} has invalid observable timestamp")
            if parse_timestamp(cutoff, "evaluation_as_of").timestamp() * 1000 < observable_at:
                raise ValueError(f"movement episode {episode_id} was not observable at evaluation_as_of")
            # A justified, versioned wider window may be supplied for pre/post catalyst research.
            # The relation to the swing itself is always classified against the actual pivots.
            if item.get("movement_window") is not None:
                explicit_window = _object(item.get("movement_window"), f"events[{index}].movement_window")
                window = {
                    "start": _timestamp(explicit_window.get("start"), f"events[{index}].movement_window.start"),
                    "end": _timestamp(explicit_window.get("end"), f"events[{index}].movement_window.end"),
                }
        else:
            window = _object(item.get("movement_window"), f"events[{index}].movement_window")
            episode_context = None
        availability_cutoff = cutoff
        if episode_context is not None:
            availability_cutoff = datetime.fromtimestamp(
                episode_context["episode_observable_only_at_ms"] / 1000,
                tz=timezone.utc,
            ).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        pre_movement_window_minutes = item.get("pre_movement_window_minutes", 0)
        if (
            isinstance(pre_movement_window_minutes, bool)
            or not isinstance(pre_movement_window_minutes, int)
            or pre_movement_window_minutes < 0
        ):
            raise ValueError(f"events[{index}].pre_movement_window_minutes must be a non-negative integer")
        post_movement_window_minutes = item.get("post_movement_window_minutes", 0)
        if (
            isinstance(post_movement_window_minutes, bool)
            or not isinstance(post_movement_window_minutes, int)
            or post_movement_window_minutes < 0
        ):
            raise ValueError(f"events[{index}].post_movement_window_minutes must be a non-negative integer")
        temporal_assessment = assess_temporal_association(
            event,
            movement_start=_timestamp(window.get("start"), f"events[{index}].movement_window.start"),
            movement_end=_timestamp(window.get("end"), f"events[{index}].movement_window.end"),
            evaluation_as_of=cutoff,
            target_entity=item.get("target_entity") or {},
            availability_cutoff=availability_cutoff,
            pre_movement_window_minutes=pre_movement_window_minutes,
            post_movement_window_minutes=post_movement_window_minutes,
        )
        if episode_context is not None:
            published_ms = parse_timestamp(event["published_at"], "published_at").timestamp() * 1000
            start_ms = episode_context["start_pivot_open_time_ms"]
            end_ms = episode_context["end_pivot_open_time_ms"]
            if published_ms < start_ms:
                event_relation = "PRECEDES_SWING"
            elif published_ms > end_ms:
                event_relation = "FOLLOWS_SWING"
            else:
                event_relation = "DURING_SWING"
            episode_context = {
                **episode_context,
                "event_relation_to_swing": event_relation,
                "temporal_interpretation": (
                    "Publication before, during, or after a technical swing is temporal context only; it does not establish causality."
                ),
            }
        event_assessments.append({
            **temporal_assessment,
            **({"movement_episode": episode_context} if episode_context is not None else {}),
            "source_use_assessment": event_use,
            "source_storage_assessment": event_storage,
            "source_registry_entry_sha256": registry_hash,
        })

    fundamental_source_use_assessments = _verify_fundamental_observation_sources(
        observations, authorization_registry=provider_authorization_registry
    )
    fundamental = evaluate_observations(
        observations,
        asset={"stable_id": stable_id.strip(), "category": category.strip()},
        evaluation_as_of=cutoff,
        freshness_policy_seconds=fundamental_freshness_policy_seconds,
    )

    horizons = report.get("horizons")
    if not isinstance(horizons, dict) or set(horizons) != {"short", "medium", "long"}:
        raise ValueError("report.horizons must define exactly short, medium, and long")
    episode_assessments = []
    analyses = report.get("descriptive_analyses")
    if analyses is not None:
        analyses = _object(analyses, "report.descriptive_analyses")
        episodes_artifact = analyses.get("movement_episodes")
        if episodes_artifact is not None:
            episodes_artifact = _object(episodes_artifact, "report.descriptive_analyses.movement_episodes")
            episodes = episodes_artifact.get("episodes")
            if not isinstance(episodes, list):
                raise ValueError("report.descriptive_analyses.movement_episodes.episodes must be a list")
            for index, episode in enumerate(episodes):
                episode = _object(episode, f"movement_episodes.episodes[{index}]")
                episode_id = episode.get("episode_id")
                if not isinstance(episode_id, str) or not episode_id.strip():
                    raise ValueError(f"movement_episodes.episodes[{index}].episode_id must be non-empty")
                linked = [
                    assessment for assessment in event_assessments
                    if (assessment.get("movement_episode") or {}).get("episode_id") == episode_id
                ]
                if not events:
                    status = "NOT_ASSESSED_NO_EVENT_EVIDENCE_SUPPLIED"
                elif not linked:
                    status = "NOT_ASSESSED_NO_EPISODE_LINKED_EVIDENCE"
                elif any(
                    item.get("entity_match") is True and item.get("causality_label") == "TEMPORAL_ASSOCIATION"
                    for item in linked
                ):
                    status = "TEMPORAL_ASSOCIATION_ONLY"
                else:
                    status = "NO_SUPPORTING_EVENT_IN_SUPPLIED_EVIDENCE"
                episode_assessments.append({
                    "episode_id": episode_id,
                    "direction": episode.get("direction"),
                    "status": status,
                    "supplied_event_count": len(linked),
                    "event_ids": [item["event_id"] for item in linked],
                    "causality_claimed": False,
                    "interpretation": (
                        "A temporal association is not proof of causality."
                        if status == "TEMPORAL_ASSOCIATION_ONLY"
                        else "This status describes only the supplied evidence; it does not prove that no catalyst existed."
                    ),
                })

    output = dict(report)
    output["external_event_evidence"] = {
        "source_coverage": event_coverage_assessment,
        "schema_version": "crypto-event-evidence-assessment-v1",
        "status": "ASSESSED" if event_assessments or event_coverage_assessment["status"] == "ASSESSED" else "NOT_AVAILABLE",
        "event_count": len(event_assessments),
        "assessments": event_assessments,
        "causality_claimed": False,
        "interpretation": "Temporal association is not proof of causality; event absence does not prove no catalyst existed.",
        "episode_assessments": episode_assessments,
    }
    output["event_causal_assessment"] = {
        "status": "ASSESSED" if event_assessments else "NOT_ASSESSED",
        "episode_count": len(episode_assessments),
        "episode_assessments": episode_assessments,
        "causality_claimed": False,
        "reason": "Episode-level summaries classify supplied evidence only; no causal attribution is inferred.",
    }
    output["fundamental_onchain_assessment"] = fundamental
    output["fundamental_source_use_assessments"] = fundamental_source_use_assessments
    output["technical_structure_assessment"] = _assess_support_resistance_input(
        support_resistance_input,
        stable_id=stable_id,
        category=category,
        evaluation_as_of=cutoff,
    )
    output["downstream_use_assessment"] = provider_use
    output["downstream_storage_assessment"] = provider_storage
    output["methodology_assessment"] = {
        "schema_version": validated_methodology["schema_version"],
        "methodology_id": validated_methodology["methodology_id"],
        "version": validated_methodology["version"],
        "status": validated_methodology["status"],
        "horizons": validated_methodology["horizons"],
        "threshold_policy_status": validated_methodology["threshold_policy"]["status"],
        "cost_components": validated_methodology["cost_model"],
        "contract_valid": True,
        "predictive_performance_validated": False,
        "investment_methodology_approved": validated_methodology["status"] == "APPROVED",
    }
    output["evidence_bundle"] = {
        "schema_version": BUNDLE_SCHEMA,
        "asset": {"stable_id": stable_id.strip(), "category": category.strip()},
        "evaluation_as_of": cutoff,
        "events_supplied": len(events),
        "event_source_coverage_supplied": event_coverage_assessment["source_count"],
        "fundamental_observations_supplied": len(observations),
    }
    output["decision_status"] = "INDETERMINATE"
    for horizon in ("short", "medium", "long"):
        output["horizons"][horizon] = dict(output["horizons"][horizon])
        output["horizons"][horizon]["status"] = "INDETERMINATE"
        output["horizons"][horizon]["conclusion"] = "INDETERMINATE"
        reasons = list(output["horizons"][horizon].get("reason_codes", []))
        for reason in ("PREDICTIVE_PERFORMANCE_NOT_VALIDATED", "EVIDENCE_INTEGRATION_IS_NOT_AN_INVESTMENT_SIGNAL"):
            if reason not in reasons:
                reasons.append(reason)
        output["horizons"][horizon]["reason_codes"] = reasons
    output["limitations"] = list(output.get("limitations", []))
    if output["technical_structure_assessment"]["status"] == "NOT_AVAILABLE":
        output["limitations"].append("Support/resistance was not assessed because no support_resistance_input was supplied.")
    else:
        output["limitations"].append("Support/resistance asset mapping is caller-supplied and requires review; it is not independently verified.")
    output["limitations"].append(
        "External events must pass source-registry approval plus provider authorization for internal analysis and persistent storage. These controls enforce recorded policy but do not prove legal authority, source completeness, or predictive value."
    )
    output["limitations"].append(
        "Fundamental/on-chain observations remain supplied, contract-validated inputs; this integration does not fetch them or prove their source authority."
    )
    output["limitations"].append(
        "Methodology contract validity is not a backtest result; no predictive performance, calibrated confidence, or investment recommendation is claimed."
    )
    output["network_requests_made"] = False
    output["orders_submitted"] = False
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="Existing crypto-asset-research-report-v2 JSON")
    parser.add_argument("--events", required=True, type=Path, help="JSON array of validated event records linked to movement_window or movement_episode_id")
    parser.add_argument("--observations", required=True, type=Path, help="JSON array of fundamental/on-chain observations")
    parser.add_argument("--methodology", required=True, type=Path, help="Versioned crypto-investment-methodology-v1 JSON")
    parser.add_argument("--asset-stable-id", required=True)
    parser.add_argument("--asset-category", required=True)
    parser.add_argument("--evaluation-as-of", required=True)
    parser.add_argument(
        "--fundamental-freshness-policy", type=Path,
        help="Optional JSON object mapping metric IDs to maximum observation age in seconds",
    )
    parser.add_argument(
        "--support-resistance-input", type=Path,
        help="Optional research-support-resistance-input-v1 JSON with authorized OHLCV artifacts and parameters",
    )
    parser.add_argument(
        "--event-source-coverage", type=Path,
        help="Optional JSON array of event-feed capture results for explicit source coverage reporting",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    events = json.loads(args.events.read_text(encoding="utf-8"))
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    methodology = json.loads(args.methodology.read_text(encoding="utf-8"))
    freshness_policy = (
        json.loads(args.fundamental_freshness_policy.read_text(encoding="utf-8"))
        if args.fundamental_freshness_policy is not None else None
    )
    support_resistance_input = (
        json.loads(args.support_resistance_input.read_text(encoding="utf-8"))
        if args.support_resistance_input is not None else None
    )
    event_source_coverage = (
        json.loads(args.event_source_coverage.read_text(encoding="utf-8"))
        if args.event_source_coverage is not None else None
    )
    enriched = enrich_research_report(
        report,
        events=events,
        observations=observations,
        methodology=methodology,
        asset={"stable_id": args.asset_stable_id, "category": args.asset_category},
        evaluation_as_of=args.evaluation_as_of,
        fundamental_freshness_policy_seconds=freshness_policy,
        support_resistance_input=support_resistance_input,
        event_source_coverage=event_source_coverage,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "schema_version": enriched["schema_version"],
        "decision_status": enriched["decision_status"],
        "event_count": enriched["external_event_evidence"]["event_count"],
        "observed_fundamental_metrics": enriched["fundamental_onchain_assessment"]["coverage"]["observed_metric_count"],
        "predictive_performance_validated": enriched["methodology_assessment"]["predictive_performance_validated"],
        "orders_submitted": enriched["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
