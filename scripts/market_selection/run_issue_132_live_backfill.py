"""Run a source-authorized, read-only historical backfill for Issue #132.

The script persists derived official text only, records original response hashes/sizes,
promotes only articles with a stable asset identifier, and never asserts market causality.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.market_selection.capture_public_event_feed import (
    build_public_event_archive_coverage_manifest,
    capture_public_event_archive_article,
    capture_public_event_archive_index,
    promote_public_archive_candidate_to_event,
    select_public_event_archive_candidate,
)
from scripts.market_selection.event_source_registry import get_source, source_entry_sha256
from scripts.market_selection.capture_binance_spot_ohlcv import capture_history
from scripts.market_selection.analyze_support_resistance import analyze_support_resistance
from scripts.market_selection.build_movement_episodes import build_movement_episodes
from scripts.market_selection.external_event_evidence import assess_temporal_association


REVIEWER = "AI-assisted technical review; owner-authorized project scope"
USER_AGENT = "CryptoIntelligenceIssue132PolicyReview/1.0 (contact: repository maintainer)"
SEC_MANGO_URL = "https://www.sec.gov/newsroom/press-releases/2024-154"
CFTC_BTC_URL = "https://www.cftc.gov/PressRoom/PressReleases/9240-26"
FED_STABLECOIN_URL = "https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260924a.htm"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


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


def iso_utc_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def capture_btc_movement_context(
    *,
    output_dir: Path,
    event_record: dict,
    authorization_record: dict,
    captured_at: str,
) -> dict:
    """Analyze real BTC Spot swings around a real event without persisting raw OHLCV."""
    event_date = datetime.fromisoformat(event_record["published_at"].replace("Z", "+00:00")).astimezone(timezone.utc).date()
    window_start = datetime(event_date.year, event_date.month, event_date.day, tzinfo=timezone.utc)
    start = window_start - timedelta(days=14)
    end_exclusive = window_start + timedelta(days=15)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end_exclusive.timestamp() * 1000)

    capture = capture_history(
        "BTCUSDT",
        "1h",
        start_ms,
        end_ms,
        use_case="internal_analysis",
        authorization_record=authorization_record,
        user_agent=authorization_record.get("approval_scope", {}).get("automated_access", {}).get(
            "user_agent", "crypto-intelligence-ecosystem-ohlcv/1.0"
        ),
    )
    if capture.get("overall_status") != "PASS":
        raise RuntimeError(
            "Binance historical BTC Spot capture did not pass: "
            f"status={capture.get('overall_status')}, "
            f"assessment={capture.get('provider_use_assessment')}, "
            f"missing_candles={len(capture.get('missing_open_time_ms') or [])}"
        )

    repository_root = Path(__file__).resolve().parents[2]
    methodology_path = repository_root / "configs" / "technical-descriptive-baseline.json"
    methodology_bytes = methodology_path.read_bytes()
    config = json.loads(methodology_bytes.decode("utf-8"))
    pivot = config["support_resistance"]
    sr = analyze_support_resistance(
        capture,
        pivot_left=pivot["pivot_left"],
        pivot_right=pivot["pivot_right"],
        tolerance_bps=pivot["tolerance_bps"],
    )
    episodes_artifact = build_movement_episodes(sr)
    episodes = episodes_artifact["episodes"]

    page_evidence = []
    for page in capture.get("pages", []):
        page_evidence.append({
            "url": page.get("url"),
            "request_started_at_utc": page.get("request_started_at_utc"),
            "captured_at_utc": page.get("captured_at_utc"),
            "http_status": page.get("http_status"),
            "response_bytes": page.get("response_bytes"),
            "response_sha256": page.get("response_sha256"),
            "capture_status": page.get("capture_status"),
            "normalization_status": page.get("normalization_status"),
        })

    publication_day_start_ms = start_ms + (14 * 86_400_000)
    publication_day_end_ms = publication_day_start_ms + 86_400_000
    temporal_assessments = []
    for episode in episodes:
        movement_start_ms = episode["start"]["pivot_open_time_ms"]
        movement_end_ms = episode["end"]["pivot_open_time_ms"]
        observable_at_ms = episode["episode_observable_only_at_ms"]
        if movement_end_ms < publication_day_start_ms:
            date_relation = "SWING_PRECEDES_PUBLICATION_DATE"
        elif movement_start_ms >= publication_day_end_ms:
            date_relation = "SWING_FOLLOWS_PUBLICATION_DATE"
        else:
            date_relation = "PUBLICATION_DATE_OVERLAPS_SWING_TIME_UNKNOWN"

        point_in_time = assess_temporal_association(
            event_record,
            movement_start=iso_utc_ms(movement_start_ms),
            movement_end=iso_utc_ms(movement_end_ms),
            evaluation_as_of=captured_at,
            target_entity={"id_type": "coingecko_id", "id": "bitcoin"},
            availability_cutoff=iso_utc_ms(observable_at_ms),
            pre_movement_window_minutes=0,
            post_movement_window_minutes=0,
        )
        temporal_assessments.append({
            "event_id": event_record["event_id"],
            "event_published_at_normalized": event_record["published_at"],
            "publication_time_precision": "DATE_ONLY",
            "publication_time_evidence": event_record.get("metadata", {}).get("archive_publication_time_evidence"),
            "movement_episode_id": episode["episode_id"],
            "movement_direction": episode["direction"],
            "movement_start": iso_utc_ms(movement_start_ms),
            "movement_end": iso_utc_ms(movement_end_ms),
            "episode_observable_only_at": iso_utc_ms(observable_at_ms),
            "publication_date_relation": date_relation,
            "point_in_time_assessment": point_in_time,
            "causality_status": "NOT_ASSESSED",
            "interpretation": (
                "Retrospective temporal context only. The article was captured after this historical episode; "
                "the point-in-time gate must not treat it as information available at the episode's observation cutoff."
            ),
        })

    response_bytes_total = sum(
        page["response_bytes"] for page in page_evidence
        if isinstance(page.get("response_bytes"), int) and not isinstance(page.get("response_bytes"), bool)
    )
    report = {
        "schema_version": "crypto-issue-132-movement-context-report-v1",
        "created_at": captured_at,
        "asset": {
            "stable_id": "coingecko_id:bitcoin",
            "asset_name": "Bitcoin",
            "symbol_native": "BTC",
            "market_symbol": "BTCUSDT",
            "identity_basis": "Exact stable entity identifier in the CFTC event record; no ticker-only event matching.",
        },
        "event": {
            "event_id": event_record["event_id"],
            "source_id": event_record["source_id"],
            "title": event_record["title"],
            "url": event_record.get("source", {}).get("url"),
            "published_at": event_record["published_at"],
            "publication_time_precision": "DATE_ONLY",
            "captured_at": event_record["captured_at"],
            "causality_status": "NOT_ASSESSED",
        },
        "market_data": {
            "provider_id": "binance_spot_market_data",
            "endpoint": capture.get("source"),
            "interval": "1h",
            "window_start_utc": start.isoformat().replace("+00:00", "Z"),
            "window_end_exclusive_utc": end_exclusive.isoformat().replace("+00:00", "Z"),
            "capture_status": capture["overall_status"],
            "requested_candle_count": capture["requested_open_candle_count"],
            "captured_candle_count": capture["captured_candle_count"],
            "missing_candle_count": len(capture.get("missing_open_time_ms") or []),
            "response_bytes_total": response_bytes_total,
            "pages": page_evidence,
            "provider_use_assessment": capture.get("provider_use_assessment"),
            "raw_ohlcv_persisted": False,
        },
        "methodology": {
            "config_path": "configs/technical-descriptive-baseline.json",
            "config_sha256": hashlib.sha256(methodology_bytes).hexdigest(),
            "methodology_id": config.get("methodology_id"),
            "methodology_version": config.get("methodology_version"),
            "status": "EXPERIMENTAL_NOT_APPROVED",
            "support_resistance_method": sr.get("method"),
            "support_resistance_sample": sr.get("sample"),
            "episode_method": episodes_artifact.get("method"),
            "window_rationale": (
                "A symmetric 14-calendar-day context on either side of the publication date is used only to inspect "
                "nearby observed swings. It is not a validated causal window or an investment horizon."
            ),
        },
        "movement_episodes": episodes,
        "event_episode_assessments": temporal_assessments,
        "causality_claimed": False,
        "limitations": [
            "Raw OHLCV response payloads and candle rows were used transiently in memory and are not persisted in this report.",
            "The methodology configuration is explicitly experimental and not approved for investment decisions.",
            "The publication source gives a date but no exact time of day; intraday ordering on that date is indeterminate.",
            "The historical article was captured after the movement, so it was not available to the system at the episode's historical observation cutoff.",
            "A technical swing and temporal overlap do not establish that the event caused the move.",
            "This is a single-exchange BTC Spot context, not a global-market or cross-exchange causal attribution.",
        ],
    }
    report["report_sha256"] = digest_json(report)
    output_path = output_dir / "btc-movement-context-report.json"
    write_json(output_path, report)
    return {
        "path": str(output_path.relative_to(output_dir)),
        "bytes": len(output_path.read_bytes()),
        "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "report_sha256": report["report_sha256"],
        "event_episode_assessment_count": len(temporal_assessments),
        "movement_episode_count": len(episodes),
        "status": "PASS",
        "raw_ohlcv_persisted": False,
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

    specs = [
        {
            "source_id": "cftc_press_release_archive",
            "archive_url": "https://www.cftc.gov/PressRoom/PressReleases?c=1172200&page=1",
            "candidate_url": CFTC_BTC_URL,
            "title": "CFTC Approves BTCPERP Contract Submitted by KalshiEX, LLC",
            "published_at": "2026-05-29T00:00:00Z",
            "date_evidence": "05/29/2026",
            "scope_id": "cftc-2026-may-page-1",
            "scope_definition": "Single CFTC press-release archive page 1 containing release 9240-26; not a claim of exhaustive 2026 coverage.",
            "period_start": "2026-05-29",
            "period_end": "2026-05-29",
            "entity": ("bitcoin", "Bitcoin", "BTC", "https://www.coingecko.com/en/coins/bitcoin"),
            "event_type": "CFTC_BITCOIN_DERIVATIVE_APPROVAL",
            "claim": "The CFTC announced approval of a KalshiEX perpetual contract referencing spot Bitcoin. This is an official regulatory/product event, not proof of price causality.",
        },
        {
            "source_id": "federal_reserve_press_release_archive",
            "archive_url": "https://www.federalreserve.gov/newsevents/pressreleases/2026-press.htm",
            "candidate_url": FED_STABLECOIN_URL,
            "title": "Federal Reserve Board requests public comment on two proposals related to establishing a regulatory framework for Board-supervised payment stablecoin issuers under the GENIUS Act",
            "published_at": "2026-09-24T00:00:00Z",
            "date_evidence": "9/24/2026",
            "scope_id": "federal-reserve-2026-press-page",
            "scope_definition": "Single Federal Reserve 2026 press-release archive page containing the 2026-09-24 stablecoin proposal; not a claim of exhaustive archive coverage.",
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
            "entity": None,
            "event_type": None,
            "claim": None,
        },
        {
            "source_id": "sec_press_release_archive",
            "archive_url": "https://www.sec.gov/newsroom/press-releases?combine=Mango&page=0",
            "candidate_url": SEC_MANGO_URL,
            "title": "SEC Charges Entities Operating Crypto Asset Trading Platform Mango Markets for Unregistered Offers and Sales of the Platform’s “MNGO” Governance Tokens",
            "published_at": "2024-09-27T00:00:00Z",
            "date_evidence": "Sept. 27, 2024",
            "scope_id": "sec-crypto-page-1",
            "scope_definition": "Single SEC press-release archive page 1 filtered to crypto; not a claim of exhaustive coverage of all SEC releases.",
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "entity": ("mango-markets", "Mango", "MNGO", "https://www.coingecko.com/en/coins/mango"),
            "event_type": "SEC_ENFORCEMENT_SETTLEMENT",
            "claim": "The SEC reported settled charges concerning unregistered offers and sales of MNGO tokens. This records the official event only and does not assert it caused a market move.",
        },
    ]
    records = []
    failures = []
    for spec in specs:
        source_id = spec["source_id"]
        try:
            records.append(capture_one(
                output_dir=args.output_dir,
                auth_registry=auth_registry,
                **spec,
            ))
        except Exception as exc:
            failure = {
                "source_id": source_id,
                "status": "FAILED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "recorded_at": now_utc(),
            }
            failures.append(failure)
            write_json(args.output_dir / f"{source_id}-failure.json", failure)
            print(json.dumps(failure, ensure_ascii=False, indent=2))

    market_context_record = None
    try:
        cftc_record_path = args.output_dir / "cftc_press_release_archive" / "event-record.json"
        if not cftc_record_path.is_file():
            raise RuntimeError("CFTC event record is unavailable; cannot create a BTC movement context")
        market_authorization = auth_registry.get("binance_spot_market_data")
        if not isinstance(market_authorization, dict):
            raise PermissionError("no scoped Binance public market-data authorization record")
        cftc_event_record = json.loads(cftc_record_path.read_text(encoding="utf-8"))
        market_context_record = capture_btc_movement_context(
            output_dir=args.output_dir,
            event_record=cftc_event_record,
            authorization_record=market_authorization,
            captured_at=now_utc(),
        )
    except Exception as exc:
        failure = {
            "source_id": "binance_spot_market_data",
            "status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "recorded_at": now_utc(),
        }
        failures.append(failure)
        write_json(args.output_dir / "binance_spot_market_data-failure.json", failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2))

    event_bundle_records = []
    contextual_records = []
    for record in records:
        source_id = record["source_id"]
        if record.get("event_id"):
            event_path = args.output_dir / source_id / "event-record.json"
            event_record = json.loads(event_path.read_text(encoding="utf-8"))
            event_bundle_records.append({
                "source_id": source_id,
                "event_id": record["event_id"],
                "event_record_path": str(event_path.relative_to(args.output_dir)),
                "event_record_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest(),
                "asset_identifiers": event_record.get("entities", []),
                "temporal_association_status": "NOT_EVALUATED_NO_MOVEMENT_WINDOW",
                "causality_status": "NOT_ASSESSED",
            })
        else:
            source_dir = args.output_dir / source_id
            article = json.loads((source_dir / "article-capture.json").read_text(encoding="utf-8"))
            candidate = json.loads((source_dir / "candidate.json").read_text(encoding="utf-8"))
            contextual_records.append({
                "source_id": source_id,
                "title": candidate["title"],
                "article_url": candidate["candidate_url"],
                "article_raw_response_sha256": article["raw_response_sha256"],
                "article_text_evidence_sha256": article["text_evidence_sha256"],
                "asset_mapping_status": "NOT_MAPPED",
                "reason": "The release concerns payment-stablecoin regulation generally and does not identify one specific token; no asset identity is inferred.",
                "temporal_association_status": "NOT_EVALUATED_NO_MOVEMENT_WINDOW",
                "causality_status": "NOT_ASSESSED",
            })
    if market_context_record is not None:
        for event_item in event_bundle_records:
            if event_item.get("source_id") == "cftc_press_release_archive":
                event_item["temporal_assessment_status"] = "ASSESSED_PER_OBSERVED_BTC_EPISODE"
                event_item["movement_context_report_path"] = market_context_record["path"]
                event_item["movement_context_report_sha256"] = market_context_record["sha256"]
                event_item["temporal_assessment_count"] = market_context_record["event_episode_assessment_count"]

    research_bundle = {
        "schema_version": "crypto-issue-132-research-event-evidence-bundle-v1",
        "created_at": now_utc(),
        "scope": "Official regulatory event evidence plus retrospective, descriptive BTC movement context; no market-causality conclusion is inferred.",
        "events": event_bundle_records,
        "contextual_unmapped_sources": contextual_records,
        "movement_context_report": market_context_record,
        "causality_claimed": False,
    }
    research_bundle["bundle_sha256"] = digest_json(research_bundle)
    bundle_path = args.output_dir / "research-event-evidence-bundle.json"
    write_json(bundle_path, research_bundle)

    backfill = {
        "schema_version": "crypto-issue-132-real-backfill-manifest-v1",
        "created_at": now_utc(),
        "purpose": "Real source-authorized historical archive/article capture; source-level hashes and extracted-text artifacts are independently verifiable.",
        "repository_relative_root": "data/research_evidence/issue-132/live-backfill",
        "read_to_eof_without_local_size_cap": True,
        "no_full_html_persisted_for_approved_archive_sources": bool(records) and all(
            record["original_archive_response"]["stored_content_mode"] == "EXTRACTED_TEXT_EVIDENCE"
            and record["original_article_response"]["stored_content_mode"] == "EXTRACTED_TEXT_EVIDENCE"
            for record in records
        ),
        "causality_claimed": False,
        "research_event_evidence_bundle": {
            "path": str(bundle_path.relative_to(args.output_dir)),
            "bytes": len(bundle_path.read_bytes()),
            "sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            "bundle_sha256": research_bundle["bundle_sha256"],
        },
        "sources": records,
        "market_context_report": market_context_record,
        "failures": failures,
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
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
