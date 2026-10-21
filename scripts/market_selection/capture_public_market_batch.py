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
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 12
SCHEMA_VERSION = "public-market-capture-batch-v1"
# Deliberately small, explicit starter universe. This is not a liquidity ranking.
DEFAULT_MARKETS = (
    ("BTC_USDT", "BTCUSDT", "BTC", "USDT"),
    ("ETH_USDT", "ETHUSDT", "ETH", "USDT"),
    ("SOL_USDT", "SOLUSDT", "SOL", "USDT"),
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_capture(market_id: str, provider: str, url: str) -> dict[str, object]:
    record: dict[str, object] = {
        "market_id": market_id, "provider": provider, "url": url,
        "request_started_at_utc": now_utc(), "captured_at_utc": None,
        # The current endpoints do not provide a verified event timestamp in this capture contract.
        # Keep provenance explicit; capture time must never be treated as source-event time.
        "source_event_at_utc": None, "source_timestamp_field": None,
        "source_timestamp_semantics": None,
        "http_status": None, "response_bytes": None, "response_sha256": None,
        "response_base64": None, "parsed_json": None, "capture_status": "FAIL",
        "error_type": None, "error_message": None,
    }
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "crypto-intelligence-ecosystem-public-batch-capture/0.1",
    })
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"response exceeded {MAX_BYTES} byte safety limit")
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
    binance_base = "https://data-api.binance.vision/api/v3"
    requests = []
    for pionex_symbol, binance_symbol, _base, _quote in markets:
        requests.extend([
            (pionex_symbol, "pionex", pionex_base + "?" + urlencode({"symbols": pionex_symbol, "type": "SPOT"})),
            (pionex_symbol, "binance_exchange_info", binance_base + "/exchangeInfo?" + urlencode({"symbol": binance_symbol})),
            (pionex_symbol, "binance_depth", binance_base + "/depth?" + urlencode({"symbol": binance_symbol, "limit": 20})),
        ])
    return requests


def capture_batch(markets: tuple[tuple[str, str, str, str], ...] = DEFAULT_MARKETS) -> dict[str, object]:
    if not markets:
        raise ValueError("market universe must not be empty")
    market_ids = [item[0] for item in markets]
    if len(set(market_ids)) != len(market_ids):
        raise ValueError("market identifiers must be unique")
    records = [request_capture(*request) for request in build_requests(markets)]
    expected = len(markets) * 3
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
            "Each Binance depth response is limited to 20 levels and is not the full order book.",
            "Binance lastUpdateId is not a market-event timestamp; source freshness may be indeterminate.",
            "Hashes establish byte identity, not provider authenticity or correctness.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/public-market-capture-batch.json")
    args = parser.parse_args()
    artifact = capture_batch()
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
