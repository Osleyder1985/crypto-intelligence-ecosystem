"""Run a source-authorized, read-only historical backfill for Issue #132.

The script persists derived official text only, records original response hashes/sizes,
promotes only articles with a stable asset identifier, and never asserts market causality.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.market_selection.capture_public_event_feed import (
    build_public_event_archive_coverage_manifest,
    capture_public_event_archive_article,
    capture_public_event_archive_index,
    promote_public_archive_candidate_to_event,
    select_public_event_archive_candidate,
)
from scripts.market_selection.event_source_registry import get_source, source_entry_sha256


REVIEWER = "AI-assisted technical review; owner-authorized project scope"
USER_AGENT = "CryptoIntelligenceIssue132PolicyReview/1.0 (contact: repository maintainer)"
SEC_MANGO_URL = "https://www.sec.gov/newsroom/press-releases/2024-154"
CFTC_BTC_URL = "https://www.cftc.gov/PressRoom/PressReleases/9240-26"
FED_STABLECOIN_URL = "https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260924a.htm"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")


def require_pass(record: dict, label: str) -> None:
    if record.get("capture_status") != "PASS" or record.get("capture_truncated") is not False:
        raise RuntimeError(
            f"{label} did not pass: status={record.get('capture_status')}, "
            f"reason_codes={record.get('reason_codes')}, errors={record.get('errors')}"
        )
    if record.get("network_request_made") is not True:
        raise RuntimeError(f"{label} did not prove a real network request")


def entity_resolution(asset_id: str, asset_name: str, symbol: str, source_url: str, output_path: Path) -> dict:
    evidence = {
        "schema_version": "crypto-stable-asset-identity-evidence-v1",
        "provider": "CoinGecko",
        "provider_asset_id": asset_id,
        "asset_name": asset_name,
        "symbol": symbol,
        "identity_source_url": source_url,
        "scope_note": "Stable identity mapping only; it does not establish that the source event caused a price move.",
    }
    evidence_bytes = canonical_bytes(evidence)
    result = {
        "status": "APPROVED",
        "reviewed_by": REVIEWER,
        "reviewed_at": now_utc(),
        "evidence_record_base64": base64.b64encode(evidence_bytes).decode("ascii"),
        "evidence_record_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "entities": [{"id_type": "coingecko_id", "id": asset_id}],
    }
    write_json(output_path, result)
    return result


def capture_one(
    *,
    output_dir: Path,
    auth_registry: dict,
    source_id: str,
    archive_url: str,
    candidate_url: str,
    title: str,
    published_at: str,
    date_evidence: str,
    scope_id: str,
    scope_definition: str,
    period_start: str,
    period_end: str,
    entity: tuple[str, str, str, str] | None,
    event_type: str | None,
    claim: str | None,
) -> dict:
    source_dir = output_dir / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    authorization = auth_registry.get(source_id)
    if not isinstance(authorization, dict):
        raise PermissionError(f"no source-specific authorization record for {source_id}")
    source = get_source(source_id)
    if source.get("status") != "APPROVED":
        raise PermissionError(f"{source_id} is not APPROVED in the source registry")
    registry_hash = source_entry_sha256(source)

    archive = capture_public_event_archive_index(
        source_id, archive_url, authorization, USER_AGENT, timeout_seconds=20.0
    )
    require_pass(archive, f"{source_id} archive index")
    archive_path = source_dir / "archive-capture.json"
    write_json(archive_path, archive)

    candidate = select_public_event_archive_candidate(
        archive,
        candidate_url=candidate_url,
        title=title,
        published_at=published_at,
        publication_time_evidence=date_evidence,
        selected_by=REVIEWER,
        selected_at=now_utc(),
        selection_rationale=(
            "Selected only because the official archive capture contains the canonical URL, title, "
            "and publication-date evidence. Date-only evidence is normalized to 00:00:00Z without asserting "
            "time-of-day. This is event identity review, not causal attribution."
        ),
    )
    candidate_path = source_dir / "candidate.json"
    write_json(candidate_path, candidate)

    article = capture_public_event_archive_article(
        archive, candidate, authorization, USER_AGENT, timeout_seconds=20.0
    )
    require_pass(article, f"{source_id} article")
    article_path = source_dir / "article-capture.json"
    write_json(article_path, article)

    event = None
    entity_path = None
    if entity is not None:
        asset_id, asset_name, symbol, identity_url = entity
        entity_path = source_dir / "entity-resolution.json"
        resolution = entity_resolution(asset_id, asset_name, symbol, identity_url, entity_path)
        event = promote_public_archive_candidate_to_event(
            archive,
            candidate,
            article,
            event_type or "OFFICIAL_REGULATORY_EVENT",
            claim or "Official event recorded as context only; no market-causality claim is made.",
            resolution,
        )
        event_path = source_dir / "event-record.json"
        write_json(event_path, event)
    else:
        event_path = None
        write_json(source_dir / "entity-resolution-decision.json", {
            "status": "NOT_MAPPED",
            "reviewed_by": REVIEWER,
            "reviewed_at": now_utc(),
            "reason": "The official release describes a broad payment-stablecoin regulatory proposal and does not identify a single crypto asset. No token mapping is inferred.",
            "article_url": candidate_url,
        })

    coverage = build_public_event_archive_coverage_manifest(
        source_id=source_id,
        scope_id=scope_id,
        scope_definition=scope_definition,
        expected_partitions=[{
            "partition_id": scope_id,
            "page_count": 1,
            "period_start": period_start,
            "period_end": period_end,
        }],
        segments=[{
            "archive_capture": archive,
            "partition_id": scope_id,
            "page_index": 1,
            "expected_page_count": 1,
        }],
        reviewed_by=REVIEWER,
        reviewed_at=now_utc(),
    )
    coverage_path = source_dir / "coverage-manifest.json"
    write_json(coverage_path, coverage)

    artifact_paths = [archive_path, candidate_path, article_path, coverage_path]
    if entity_path:
        artifact_paths.append(entity_path)
    if event_path:
        artifact_paths.append(event_path)
    else:
        artifact_paths.append(source_dir / "entity-resolution-decision.json")
    artifact_records = []
    for artifact_path in sorted(artifact_paths):
        body = artifact_path.read_bytes()
        artifact_records.append({
            "path": str(artifact_path.relative_to(output_dir)),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        })
    return {
        "source_id": source_id,
        "source_registry_entry_sha256": registry_hash,
        "archive_url": archive_url,
        "candidate_url": candidate_url,
        "candidate_id": candidate["candidate_id"],
        "original_archive_response": {
            "bytes": archive["raw_response_bytes"],
            "sha256": archive["raw_response_sha256"],
            "stored_content_mode": archive.get("stored_content_mode"),
            "text_evidence_bytes": archive.get("text_evidence_bytes"),
            "text_evidence_sha256": archive.get("text_evidence_sha256"),
        },
        "original_article_response": {
            "bytes": article["raw_response_bytes"],
            "sha256": article["raw_response_sha256"],
            "stored_content_mode": article.get("stored_content_mode"),
            "text_evidence_bytes": article.get("text_evidence_bytes"),
            "text_evidence_sha256": article.get("text_evidence_sha256"),
        },
        "event_id": event.get("event_id") if event else None,
        "event_causality_status": event.get("metadata", {}).get("causality_status") if event else "NOT_ASSESSED",
        "coverage_status": coverage.get("coverage_status"),
        "coverage_manifest_sha256": coverage.get("manifest_sha256"),
        "artifacts": artifact_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization-registry", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    auth_registry = json.loads(args.authorization_registry.read_text(encoding="utf-8"))
    if not isinstance(auth_registry, dict):
        raise ValueError("authorization registry must be an object")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    # Each source has its own authorization, endpoint, and declared one-page scope.
    records.append(capture_one(
        output_dir=args.output_dir, auth_registry=auth_registry,
        source_id="sec_press_release_archive",
        archive_url="https://www.sec.gov/newsroom/press-releases?combine=crypto&page=1",
        candidate_url=SEC_MANGO_URL,
        title="SEC Charges Entities Operating Crypto Asset Trading Platform Mango Markets for Unregistered Offers and Sales of the Platform’s “MNGO” Governance Tokens",
        published_at="2024-09-27T00:00:00Z", date_evidence="Sept. 27, 2024",
        scope_id="sec-crypto-2024-query-page",
        scope_definition="Single SEC press-release archive query page filtered to crypto and year 2024; not a claim of exhaustive 2024 coverage.",
        period_start="2024-01-01", period_end="2024-12-31",
        entity=("mango-markets", "Mango", "MNGO", "https://www.coingecko.com/en/coins/mango"),
        event_type="SEC_ENFORCEMENT_SETTLEMENT",
        claim="The SEC reported settled charges concerning unregistered offers and sales of MNGO tokens. This records the official event only and does not assert it caused a market move.",
    ))
    records.append(capture_one(
        output_dir=args.output_dir, auth_registry=auth_registry,
        source_id="cftc_press_release_archive",
        archive_url="https://www.cftc.gov/PressRoom/PressReleases?c=1172200&page=1",
        candidate_url=CFTC_BTC_URL,
        title="CFTC Approves BTCPERP Contract Submitted by KalshiEX, LLC",
        published_at="2026-05-29T00:00:00Z", date_evidence="05/29/2026",
        scope_id="cftc-2026-may-page-1",
        scope_definition="Single CFTC press-release archive page 1 containing release 9240-26; not a claim of exhaustive 2026 coverage.",
        period_start="2026-05-29", period_end="2026-05-29",
        entity=("bitcoin", "Bitcoin", "BTC", "https://www.coingecko.com/en/coins/bitcoin"),
        event_type="CFTC_BITCOIN_DERIVATIVE_APPROVAL",
        claim="The CFTC announced approval of a KalshiEX perpetual contract referencing spot Bitcoin. This is an official regulatory/product event, not proof of price causality.",
    ))
    records.append(capture_one(
        output_dir=args.output_dir, auth_registry=auth_registry,
        source_id="federal_reserve_press_release_archive",
        archive_url="https://www.federalreserve.gov/newsevents/pressreleases/2026-press.htm",
        candidate_url=FED_STABLECOIN_URL,
        title="Federal Reserve Board requests public comment on two proposals related to establishing a regulatory framework for Board-supervised payment stablecoin issuers under the GENIUS Act",
        published_at="2026-09-24T00:00:00Z", date_evidence="9/24/2026",
        scope_id="federal-reserve-2026-press-page",
        scope_definition="Single Federal Reserve 2026 press-release archive page containing the 2026-09-24 stablecoin proposal; not a claim of exhaustive archive coverage.",
        period_start="2026-01-01", period_end="2026-12-31",
        entity=None,
        event_type=None,
        claim=None,
    ))

    backfill = {
        "schema_version": "crypto-issue-132-real-backfill-manifest-v1",
        "created_at": now_utc(),
        "purpose": "Real source-authorized historical archive/article capture; source-level hashes and extracted-text artifacts are independently verifiable.",
        "read_to_eof_without_local_size_cap": True,
        "no_full_html_persisted_for_approved_archive_sources": all(
            record["original_archive_response"]["stored_content_mode"] == "EXTRACTED_TEXT_EVIDENCE"
            and record["original_article_response"]["stored_content_mode"] == "EXTRACTED_TEXT_EVIDENCE"
            for record in records
        ),
        "causality_claimed": False,
        "sources": records,
    }
    backfill["manifest_sha256"] = digest_json(backfill)
    write_json(args.output_dir / "backfill-manifest.json", backfill)
    print(json.dumps({
        "manifest": str(args.output_dir / "backfill-manifest.json"),
        "manifest_sha256": backfill["manifest_sha256"],
        "sources": [{
            "source_id": record["source_id"],
            "coverage_status": record["coverage_status"],
            "event_id": record["event_id"],
            "causality_status": record["event_causality_status"],
        } for record in records],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
