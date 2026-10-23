"""Promote one preserved generic RSS/Atom candidate to a validated event record.

This command performs no network requests. It only consumes a preserved capture
and an explicit reviewed entity-mapping evidence record.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.market_selection.capture_public_event_feed import (
    promote_public_feed_candidate_to_event,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True, type=Path,
                        help="Preserved crypto-public-event-feed-capture-v1 JSON")
    parser.add_argument("--candidate-id", required=True,
                        help="Exact candidate_id from the preserved feed capture")
    parser.add_argument("--event-type", required=True,
                        help="Explicit event taxonomy label; no causality is inferred")
    parser.add_argument("--claim", required=True,
                        help="Explicit claim grounded in the preserved article body")
    parser.add_argument("--entity-resolution", required=True, type=Path,
                        help="Reviewed entity-resolution JSON including stable IDs and evidence bytes/hash")
    parser.add_argument("--article-capture", required=True, type=Path,
                        help="Complete authorized crypto-public-event-article-capture-v1 JSON for this candidate")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output path for the promoted validated event JSON")
    args = parser.parse_args(argv)

    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8"))
        resolution = json.loads(args.entity_resolution.read_text(encoding="utf-8"))
        article_capture = json.loads(args.article_capture.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read valid UTF-8 JSON input: {exc}")

    event = promote_public_feed_candidate_to_event(
        capture,
        args.candidate_id,
        args.event_type,
        args.claim,
        resolution,
        article_capture=article_capture,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "event_id": event["event_id"],
        "source_id": event["source_id"],
        "published_at": event["published_at"],
        "capture_method": event["capture_method"],
        "causality_status": event["metadata"]["causality_status"],
        "causality_claimed": event["causality_claimed"],
        "orders_submitted": event["orders_submitted"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
