"""Capture and promote reviewed candidates from official historical event archives."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.market_selection.shared_request_rate_limiter import RateLimitCoordinationError

from scripts.market_selection.capture_public_event_feed import (
    build_public_event_archive_coverage_manifest,
    capture_public_event_archive_article,
    capture_public_event_archive_index,
    promote_public_archive_candidate_to_event,
    select_public_event_archive_candidate,
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture-index", help="Capture one allowlisted official archive index page")
    capture.add_argument("--source-id", required=True)
    capture.add_argument("--archive-url", required=True)
    capture.add_argument("--provider-authorization-registry", required=True, type=Path)
    capture.add_argument("--user-agent", required=True)
    capture.add_argument("--timeout-seconds", type=float, default=10.0)
    capture.add_argument("--captured-at")
    capture.add_argument("--output", required=True, type=Path)

    select = subparsers.add_parser("select-candidate", help="Select a candidate only when URL, title and date evidence appear in the preserved index")
    select.add_argument("--archive-capture", required=True, type=Path)
    select.add_argument("--candidate-url", required=True)
    select.add_argument("--title", required=True)
    select.add_argument("--published-at", required=True)
    select.add_argument("--publication-time-evidence", required=True)
    select.add_argument("--selected-by", required=True)
    select.add_argument("--selected-at", required=True)
    select.add_argument("--selection-rationale", required=True)
    select.add_argument("--output", required=True, type=Path)

    article = subparsers.add_parser("capture-article", help="Capture the article selected from a preserved archive index")
    article.add_argument("--source-id", required=True)
    article.add_argument("--archive-capture", required=True, type=Path)
    article.add_argument("--candidate", required=True, type=Path)
    article.add_argument("--provider-authorization-registry", required=True, type=Path)
    article.add_argument("--user-agent", required=True)
    article.add_argument("--timeout-seconds", type=float, default=10.0)
    article.add_argument("--captured-at")
    article.add_argument("--output", required=True, type=Path)

    coverage = subparsers.add_parser("coverage-manifest", help="Validate declared archive page coverage and list missing pages")
    coverage.add_argument("--input", required=True, type=Path, help="JSON with source_id, scope_id, scope_definition, expected_partitions and segments")
    coverage.add_argument("--output", required=True, type=Path)

    promote = subparsers.add_parser("promote", help="Promote a reviewed archive candidate after stable-entity review")
    promote.add_argument("--archive-capture", required=True, type=Path)
    promote.add_argument("--candidate", required=True, type=Path)
    promote.add_argument("--article-capture", required=True, type=Path)
    promote.add_argument("--entity-resolution", required=True, type=Path)
    promote.add_argument("--event-type", required=True)
    promote.add_argument("--claim", required=True)
    promote.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    blocked_rate_limit = False
    try:
        if args.command == "coverage-manifest":
            specification = _read_json(args.input)
            if not isinstance(specification, dict):
                parser.error("--input must contain a JSON object")
            segments = []
            for index, item in enumerate(specification.get("segments", [])):
                if not isinstance(item, dict) or not isinstance(item.get("archive_capture_path"), str):
                    parser.error(f"segments[{index}] requires archive_capture_path")
                segments.append({
                    "archive_capture": _read_json(Path(item["archive_capture_path"])),
                    "partition_id": item.get("partition_id"),
                    "page_index": item.get("page_index"),
                    "expected_page_count": item.get("expected_page_count"),
                })
            result = build_public_event_archive_coverage_manifest(
                specification.get("source_id"),
                specification.get("scope_id"),
                specification.get("scope_definition"),
                specification.get("expected_partitions"),
                segments,
                specification.get("reviewed_by"),
                specification.get("reviewed_at"),
            )
        elif args.command == "capture-index":
            authorization_registry = _read_json(args.provider_authorization_registry)
            record = authorization_registry.get(args.source_id) if isinstance(authorization_registry, dict) else None
            result = capture_public_event_archive_index(
                args.source_id,
                args.archive_url,
                authorization_record=record,
                user_agent=args.user_agent,
                timeout_seconds=args.timeout_seconds,
                captured_at=args.captured_at,
            )
        elif args.command == "select-candidate":
            result = select_public_event_archive_candidate(
                _read_json(args.archive_capture),
                candidate_url=args.candidate_url,
                title=args.title,
                published_at=args.published_at,
                publication_time_evidence=args.publication_time_evidence,
                selected_by=args.selected_by,
                selected_at=args.selected_at,
                selection_rationale=args.selection_rationale,
            )
        elif args.command == "capture-article":
            archive_capture = _read_json(args.archive_capture)
            candidate = _read_json(args.candidate)
            if archive_capture.get("source_id") != args.source_id or candidate.get("source_id") != args.source_id:
                parser.error("--source-id must match both archive capture and candidate")
            authorization_registry = _read_json(args.provider_authorization_registry)
            record = authorization_registry.get(args.source_id) if isinstance(authorization_registry, dict) else None
            result = capture_public_event_archive_article(
                archive_capture,
                candidate,
                authorization_record=record,
                user_agent=args.user_agent,
                timeout_seconds=args.timeout_seconds,
                captured_at=args.captured_at,
            )
        else:
            result = promote_public_archive_candidate_to_event(
                _read_json(args.archive_capture),
                _read_json(args.candidate),
                _read_json(args.article_capture),
                args.event_type,
                args.claim,
                _read_json(args.entity_resolution),
            )
    
    except RateLimitCoordinationError:
        if args.command not in {"capture-index", "capture-article"}:
            raise
        blocked_rate_limit = True
        result = {
            "schema_version": "crypto-public-event-capture-error-v1",
            "source_id": getattr(args, "source_id", None),
            "capture_status": "BLOCKED_RATE_LIMIT_COORDINATION",
            "network_request_made": False,
            "reason_codes": ["RATE_LIMIT_COORDINATION_FAILED"],
            "errors": [{
                "type": "RATE_LIMIT_COORDINATION",
                "message": "Shared request-rate coordination is unavailable; no network request was made.",
            }],
        }
    _write_json(args.output, result)
    print(json.dumps({
        "output": str(args.output),
        "command": args.command,
        "status": result.get("capture_status", result.get("capture_method", result.get("schema_version"))),
        "network_request_made": result.get("network_request_made"),
        "event_id": result.get("event_id"),
        "coverage_status": result.get("coverage_status"),
        "missing_pages": result.get("missing_pages", []),
        "reason_codes": result.get("reason_codes", []),
    }, ensure_ascii=False, indent=2))
    return 2 if blocked_rate_limit else 0


if __name__ == "__main__":
    raise SystemExit(main())
