"""Capture a bounded batch of public spot markets without credentials or orders.

The artifact preserves raw response bytes per (market, provider) record. A capture
is evidence of a point-in-time response, not a ranking or investment decision.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.market_selection.provider_license_gate import evaluate_provider_use, SUPPORTED_USE_CASES

TIMEOUT_SECONDS = 12
READ_CHUNK_BYTES = 64 * 1024  # Read buffer size only; not a response-size limit.
BINANCE_DEPTH_LIMIT = 5000  # Official GET /api/v3/depth maximum; weight 250.
PIONEX_DEPTH_LIMIT = 1000  # Official GET /api/v1/market/depth maximum.
SCHEMA_VERSION = "public-market-capture-batch-v1"
# Deliberately small, explicit starter universe. This is not a liquidity ranking.
DEFAULT_MARKETS = (
    ("BTC_USDT", "BTCUSDT", "BTC", "USDT"),
    ("ETH_USDT", "ETHUSDT", "ETH", "USDT"),
    ("SOL_USDT", "SOLUSDT", "SOL", "USDT"),
)



def read_complete(response: object) -> tuple[bytes, str | None]:
    """Read the entire HTTP body in chunks; chunk size does not cap total bytes."""
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    chunks: list[bytes] = []
    while True:
        chunk = response.read(READ_CHUNK_BYTES)  # type: ignore[attr-defined]
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks), content_length


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_capture(market_id: str, provider: str, url: str, *, use_case: str = "live_technical_test", authorization_records: dict | None = None) -> dict[str, object]:
    record: dict[str, object] = {
        "market_id": market_id, "provider": provider, "url": url,
        "request_started_at_utc": now_utc(), "captured_at_utc": None,
        # The current endpoints do not provide a verified event timestamp in this capture contract.
        # Keep provenance explicit; capture time must never be treated as source-event time.
        "source_event_at_utc": None,
        "source_market_update_at_utc": None,
        "source_market_update_timestamp_status": "NOT_PROVIDED",
        "source_response_at_utc": None,
        "source_response_timestamp_status": "NOT_PROVIDED",
        "source_timestamp_field": None,
        "source_timestamp_semantics": None,
        "http_status": None, "response_bytes": None, "response_sha256": None,
        "provider_use_assessment": None,
        "response_base64": None, "parsed_json": None, "capture_status": "FAIL",
        "error_type": None, "error_message": None,
    }
    provider_id = "pionex_spot_market_data" if provider.startswith("pionex") else "binance_spot_market_data"
    authorization_record = (authorization_records or {}).get(provider_id)
    try:
        assessment = evaluate_provider_use(provider_id, use_case, authorization_record)
    except (TypeError, ValueError) as exc:
        assessment = {
            "schema_version": "crypto-provider-use-assessment-v1",
            "provider_id": provider_id, "use_case": use_case, "decision": "BLOCK",
            "reason_codes": ["AUTHORIZATION_RECORD_INVALID"],
            "authorization_evidence_status": "INVALID", "validation_error": str(exc),
        }
    record["provider_use_assessment"] = assessment
    if assessment["decision"] != "ALLOW":
        record.update(capture_status="BLOCKED", error_type="ProviderUseBlocked",
                      error_message=";".join(assessment["reason_codes"]))
        return record
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "crypto-intelligence-ecosystem-public-batch-capture/0.1",
    })
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            # Preserve the complete provider response. Do not truncate or reject data at an arbitrary byte threshold.
            # Actual limits are the provider, network, and available runtime resources—not a project-defined cap.
            raw, _content_length = read_complete(response)
        record.update({
            "http_status": status, "captured_at_utc": now_utc(),
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_base64": base64.b64encode(raw).decode("ascii"),
        })
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            record.update(error_type=type(exc).__name__, error_message="response was not valid UTF-8 JSON")
            return record
        record["parsed_json"] = parsed
        if provider in ("pionex", "pionex_depth"):
            # Pionex documents this top-level timestamp in milliseconds as response metadata.
            # It is distinct from data.updateTime and local capture time.
            record["source_timestamp_field"] = "timestamp"
            endpoint_name = "Common Symbols" if provider == "pionex" else "market depth"
            record["source_timestamp_semantics"] = (
                f"Pionex {endpoint_name} API response timestamp in epoch milliseconds; "
                "response metadata time, not the order-book update timestamp"
            )
            timestamp = parsed.get("timestamp") if isinstance(parsed, dict) else None
            if isinstance(timestamp, int) and not isinstance(timestamp, bool) and timestamp >= 0:
                try:
                    record["source_response_at_utc"] = (
                        datetime.fromtimestamp(timestamp / 1000, timezone.utc)
                        .isoformat(timespec="milliseconds").replace("+00:00", "Z")
                    )
                    record["source_response_timestamp_status"] = "VALID"
                except (OverflowError, OSError, ValueError):
                    record["source_response_timestamp_status"] = "INVALID"
            elif timestamp is None:
                record["source_response_timestamp_status"] = "MISSING"
            else:
                record["source_response_timestamp_status"] = "INVALID"
        if provider == "pionex_depth":
            # Pionex documents data.updateTime as the order-book update timestamp in epoch ms.
            # Keep it separate from the top-level response timestamp and local capture time.
            data = parsed.get("data") if isinstance(parsed, dict) else None
            timestamp = data.get("updateTime") if isinstance(data, dict) else None
            record["source_timestamp_field"] = "data.updateTime"
            record["source_timestamp_semantics"] = (
                "Pionex Spot order-book update timestamp in epoch milliseconds; "
                "distinct from response timestamp and local capture time"
            )
            if isinstance(timestamp, int) and not isinstance(timestamp, bool) and timestamp >= 0:
                try:
                    record["source_market_update_at_utc"] = (
                        datetime.fromtimestamp(timestamp / 1000, timezone.utc)
                        .isoformat(timespec="milliseconds").replace("+00:00", "Z")
                    )
                    record["source_market_update_timestamp_status"] = "VALID"
                except (OverflowError, OSError, ValueError):
                    record["source_market_update_timestamp_status"] = "INVALID"
            elif timestamp is None:
                record["source_market_update_timestamp_status"] = "MISSING"
            else:
                record["source_market_update_timestamp_status"] = "INVALID"
        if status != 200:
            record.update(error_type="UnexpectedHTTPStatus", error_message=f"expected HTTP 200, received {status}")
            return record
        if not isinstance(parsed, dict):
            record.update(error_type="InvalidResponseSchema", error_message="top-level JSON value must be an object")
            return record
        record["capture_status"] = "PASS"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        record["captured_at_utc"] = now_utc()
        record["error_type"] = type(exc).__name__
        record["error_message"] = str(exc)[:300]
    return record


def build_requests(markets: tuple[tuple[str, str, str, str], ...]) -> list[tuple[str, str, str]]:
    pionex_base = "https://api.pionex.com/api/v1/common/symbols"
    pionex_depth_base = "https://api.pionex.com/api/v1/market/depth"
    binance_base = "https://data-api.binance.vision/api/v3"
    requests = []
    for pionex_symbol, binance_symbol, _base, _quote in markets:
        requests.extend([
            (pionex_symbol, "pionex", pionex_base + "?" + urlencode({"symbols": pionex_symbol, "type": "SPOT"})),
            (pionex_symbol, "pionex_depth", pionex_depth_base + "?" + urlencode({"symbol": pionex_symbol, "limit": PIONEX_DEPTH_LIMIT})),
            (pionex_symbol, "binance_exchange_info", binance_base + "/exchangeInfo?" + urlencode({"symbol": binance_symbol})),
            (pionex_symbol, "binance_depth", binance_base + "/depth?" + urlencode({"symbol": binance_symbol, "limit": BINANCE_DEPTH_LIMIT})),
        ])
    return requests


def capture_batch(markets: tuple[tuple[str, str, str, str], ...] = DEFAULT_MARKETS, *, use_case: str = "live_technical_test", authorization_records: dict | None = None) -> dict[str, object]:
    if not markets:
        raise ValueError("market universe must not be empty")
    market_ids = [item[0] for item in markets]
    if len(set(market_ids)) != len(market_ids):
        raise ValueError("market identifiers must be unique")
    records = [request_capture(*request, use_case=use_case, authorization_records=authorization_records) for request in build_requests(markets)]
    expected = len(markets) * 4
    complete = len(records) == expected and all(item["capture_status"] == "PASS" for item in records)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": now_utc(),
        "scope": "bounded public spot market data only; no credentials; no orders",
        "universe": [
            {"pionex_symbol": p, "binance_symbol": b, "base_asset": base, "quote_asset": quote}
            for p, b, base, quote in markets
        ],
        "records": records,
        "expected_record_count": expected,
        "actual_record_count": len(records),
        "overall_status": "PASS" if complete else "FAIL",
        "limitations": [
            "Point-in-time public API capture; not an investment recommendation or ranking.",
            "Provider availability does not prove regional/account access, liquidity, or execution.",
            "Binance depth requests use the documented maximum of 5000 levels (weight 250); Pionex depth requests use the documented maximum of 1000 levels. These are maximum-size snapshots, not the complete or persistent order book.",
            "Pionex data.updateTime is preserved separately from the response timestamp and capture time; it does not alone prove freshness against a product-specific policy.",
            "Binance lastUpdateId is not a market-event timestamp; source freshness may be indeterminate.",
            "Hashes establish byte identity, not provider authenticity or correctness.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use-case", choices=sorted(SUPPORTED_USE_CASES), default="live_technical_test")
    parser.add_argument("--authorization-records", help="JSON object mapping provider IDs to authorization records")
    parser.add_argument("--output", default="artifacts/public-market-capture-batch.json")
    args = parser.parse_args()
    authorization_records = {}
    if args.authorization_records:
        try:
            loaded = json.loads(Path(args.authorization_records).read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                authorization_records = loaded
            else:
                authorization_records = {"__invalid_file__": loaded}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            authorization_records = {"__invalid_file__": {"invalid": True}}
    artifact = capture_batch(use_case=args.use_case, authorization_records=authorization_records)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path), "schema_version": artifact["schema_version"],
        "overall_status": artifact["overall_status"],
        "expected_record_count": artifact["expected_record_count"],
        "actual_record_count": artifact["actual_record_count"],
        "records": [
            {key: item.get(key) for key in ("market_id", "provider", "capture_status", "http_status", "response_bytes", "response_sha256", "error_type", "error_message")}
            for item in artifact["records"]
        ],
    }, ensure_ascii=False, indent=2))
    return 0 if artifact["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
