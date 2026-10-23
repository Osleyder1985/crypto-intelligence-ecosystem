"""Validate and conservatively relate external crypto events to market movements.

This module is deliberately offline and source-neutral. It validates evidence records;
it does not fetch news, infer asset identity from a ticker, or establish causality.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urldefrag, urlsplit, urlunsplit

INPUT_SCHEMA = "crypto-external-event-record-v1"
OUTPUT_SCHEMA = "crypto-event-evidence-assessment-v1"
SOURCE_TYPES = {"PRIMARY_OFFICIAL", "REGULATORY", "SECONDARY_MEDIA", "AGGREGATOR", "OTHER"}
CAUSALITY_LABELS = {
    "FACT_VERIFIED",
    "TEMPORAL_ASSOCIATION",
    "PLAUSIBLE_HYPOTHESIS",
    "SUPPORTED_CAUSALITY",
    "CAUSE_UNIDENTIFIED",
}


def parse_timestamp(value: object, field: str) -> datetime:
    """Parse an ISO-8601 timestamp and require an explicit UTC offset."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _valid_http_url(value: object, field: str) -> str:
    url = _nonempty_string(value, field)
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    return url


def validate_event(event: object) -> dict:
    """Return a normalized event record or fail closed on missing/ambiguous evidence."""
    if not isinstance(event, dict):
        raise ValueError("event must be an object")
    if event.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"schema_version must be {INPUT_SCHEMA}")

    event_id = _nonempty_string(event.get("event_id"), "event_id")
    title = _nonempty_string(event.get("title"), "title")
    event_type = _nonempty_string(event.get("event_type"), "event_type")
    source = event.get("source")
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    source_type = _nonempty_string(source.get("source_type"), "source.source_type")
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"source.source_type must be one of {sorted(SOURCE_TYPES)}")
    source_url = _valid_http_url(source.get("url"), "source.url")
    publisher = _nonempty_string(source.get("publisher"), "source.publisher")

    published_at = parse_timestamp(event.get("published_at"), "published_at")
    captured_at = parse_timestamp(event.get("captured_at"), "captured_at")
    if captured_at < published_at:
        raise ValueError("captured_at cannot precede published_at")

    entities = event.get("entities")
    if not isinstance(entities, list) or not entities:
        raise ValueError("entities must be a non-empty list of explicit asset identifiers")
    normalized_entities = []
    seen_entities = set()
    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            raise ValueError(f"entities[{index}] must be an object")
        entity_type = _nonempty_string(entity.get("id_type"), f"entities[{index}].id_type")
        entity_id = _nonempty_string(entity.get("id"), f"entities[{index}].id")
        if entity_type not in {"coingecko_id", "chain_contract", "exchange_asset_id", "project_id"}:
            raise ValueError(
                f"entities[{index}].id_type must be a stable identifier; ticker-only matching is forbidden"
            )
        key = (entity_type, entity_id.casefold())
        if key not in seen_entities:
            normalized_entities.append({"id_type": entity_type, "id": entity_id})
            seen_entities.add(key)

    evidence = event.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must contain at least one evidence reference")
    normalized_evidence = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValueError(f"evidence[{index}] must be an object")
        normalized_evidence.append({
            "url": _valid_http_url(item.get("url"), f"evidence[{index}].url"),
            "claim": _nonempty_string(item.get("claim"), f"evidence[{index}].claim"),
        })

    capture_method = _nonempty_string(event.get("capture_method"), "capture_method")
    content_sha256 = event.get("content_sha256")
    if content_sha256 is not None:
        if not isinstance(content_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", content_sha256):
            raise ValueError("content_sha256 must be a 64-character hexadecimal SHA-256 digest")

    return {
        "schema_version": INPUT_SCHEMA,
        "event_id": event_id,
        "title": title,
        "event_type": event_type,
        "source": {
            "source_type": source_type,
            "url": source_url,
            "publisher": publisher,
        },
        "published_at": published_at.isoformat().replace("+00:00", "Z"),
        "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
        "entities": normalized_entities,
        "evidence": normalized_evidence,
        "capture_method": capture_method,
        "content_sha256": content_sha256.lower() if content_sha256 else None,
        "license_notes": str(event.get("license_notes", "UNKNOWN")),
        "metadata": event.get("metadata", {}) if isinstance(event.get("metadata", {}), dict) else {},
    }


def _normalized_title(title: str) -> str:
    folded = unicodedata.normalize("NFKC", title).casefold()
    return " ".join(re.findall(r"\w+", folded, flags=re.UNICODE))


def deduplication_key(event: dict) -> str:
    """Prefer stable source identifiers; only fall back to exact publisher/title matching."""
    normalized = validate_event(event)
    source = normalized["source"]
    metadata = normalized["metadata"]
    provider_id = metadata.get("provider_article_id")
    if isinstance(provider_id, str) and provider_id.strip():
        basis = f"provider:{source['publisher'].casefold()}:{provider_id.strip()}"
    else:
        url = urlsplit(urldefrag(source["url"]).url)
        canonical = urlunsplit((url.scheme.casefold(), url.netloc.casefold(), url.path.rstrip("/"), url.query, ""))
        basis = f"url:{canonical}"
        # Different URL variants may point to the same syndicated story; use exact publisher/title
        # only when the source URL is absent (which validation intentionally forbids).
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def deduplicate_events(events: list[dict]) -> dict:
    """Deduplicate within a batch, preserving every input ID and reporting conflicts."""
    if not isinstance(events, list):
        raise ValueError("events must be a list")
    unique = []
    duplicates = []
    by_key = {}
    for index, event in enumerate(events):
        normalized = validate_event(event)
        key = deduplication_key(normalized)
        if key not in by_key:
            by_key[key] = len(unique)
            unique.append(normalized)
            continue
        original_index = by_key[key]
        original = unique[original_index]
        # Same canonical source identity but conflicting core claims must be surfaced, not silently merged.
        original_hash = original["content_sha256"]
        duplicate_hash = normalized["content_sha256"]
        content_changed = (
            original_hash is not None
            and duplicate_hash is not None
            and original_hash != duplicate_hash
        )
        conflict = (
            original["title"] != normalized["title"]
            or original["event_type"] != normalized["event_type"]
            or original["entities"] != normalized["entities"]
            or original["published_at"] != normalized["published_at"]
            or original["evidence"] != normalized["evidence"]
            or content_changed
        )
        duplicates.append({
            "duplicate_event_id": normalized["event_id"],
            "canonical_event_id": original["event_id"],
            "input_index": index,
            "conflict": conflict,
            "resolution": "CONFLICT_REQUIRES_REVIEW" if conflict else "DUPLICATE_COLLAPSED",
        })
    return {
        "schema_version": OUTPUT_SCHEMA,
        "input_count": len(events),
        "unique_count": len(unique),
        "duplicate_count": len(duplicates),
        "events": unique,
        "duplicates": duplicates,
    }


def assess_temporal_association(
    event: dict,
    *,
    movement_start: str,
    movement_end: str,
    evaluation_as_of: str,
    target_entity: dict,
) -> dict:
    """Assess entity match and temporal eligibility, never infer causality from proximity alone."""
    normalized = validate_event(event)
    if not isinstance(target_entity, dict):
        raise ValueError("target_entity must be an explicit stable asset identifier")
    target_type = _nonempty_string(target_entity.get("id_type"), "target_entity.id_type")
    target_id = _nonempty_string(target_entity.get("id"), "target_entity.id")
    if target_type not in {"coingecko_id", "chain_contract", "exchange_asset_id", "project_id"}:
        raise ValueError("target_entity must use a stable identifier; ticker-only matching is forbidden")
    entity_matches = any(
        item["id_type"] == target_type and item["id"].casefold() == target_id.casefold()
        for item in normalized["entities"]
    )
    start = parse_timestamp(movement_start, "movement_start")
    end = parse_timestamp(movement_end, "movement_end")
    as_of = parse_timestamp(evaluation_as_of, "evaluation_as_of")
    published = parse_timestamp(normalized["published_at"], "published_at")
    captured = parse_timestamp(normalized["captured_at"], "captured_at")
    if end < start:
        raise ValueError("movement_end must not precede movement_start")

    # For a reproducible historical backtest, require both publication and actual capture by as-of.
    available_by_as_of = published <= as_of and captured <= as_of
    overlaps_window = start <= published <= end
    if not entity_matches:
        status = "ENTITY_NOT_MATCHED"
        label = "CAUSE_UNIDENTIFIED"
        reason = "No exact stable identifier links this event to the target asset."
    elif not available_by_as_of:
        status = "NOT_AVAILABLE_AS_OF"
        label = "CAUSE_UNIDENTIFIED"
        reason = "The event was published or captured after the evaluation cutoff."
    elif overlaps_window:
        status = "TEMPORALLY_ELIGIBLE"
        label = "TEMPORAL_ASSOCIATION"
        reason = "Publication overlaps the defined movement window; temporal proximity is not causality."
    else:
        status = "OUTSIDE_MOVEMENT_WINDOW"
        label = "CAUSE_UNIDENTIFIED"
        reason = "The publication timestamp is outside the defined movement window."
    return {
        "schema_version": OUTPUT_SCHEMA,
        "event_id": normalized["event_id"],
        "target_entity": {"id_type": target_type, "id": target_id},
        "entity_match": entity_matches,
        "status": status,
        "causality_label": label,
        "published_at": normalized["published_at"],
        "captured_at": normalized["captured_at"],
        "movement_window": {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
        },
        "evaluation_as_of": as_of.isoformat().replace("+00:00", "Z"),
        "reason": reason,
        "evidence_urls": [item["url"] for item in normalized["evidence"]],
        "causality_claimed": False,
    }


def canonical_json_sha256(value: object) -> str:
    """Hash a canonical JSON representation; this is not a source-document hash."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
