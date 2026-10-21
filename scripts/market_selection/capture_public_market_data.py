"""Capture raw public market API responses with timestamps and SHA-256 provenance.

This script is read-only, uses no credentials, and never submits orders.
It retains the exact response bytes as Base64 in a local evidence artifact.
"""
from __future__ import annotations

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


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_capture(provider: str, url: str) -> dict[str, object]:
    started = now_utc()
    record: dict[str, object] = {
        "provider": provider,
        "url": url,
        "request_started_at_utc": started,
        "captured_at_utc": None,
        "http_status": None,
        "response_bytes": None,
        "response_sha256": None,
        "response_base64": None,
        "parsed_json": None,
        "capture_status": "FAIL",
        "error_type": None,
        "error_message": None,
    }
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "crypto-intelligence-ecosystem-public-capture/0.1"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"response exceeded {MAX_BYTES} byte safety limit")
        record["http_status"] = status
        record["captured_at_utc"] = now_utc()
        record["response_bytes"] = len(raw)
        record["response_sha256"] = hashlib.sha256(raw).hexdigest()
        record["response_base64"] = base64.b64encode(raw).decode("ascii")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            record["error_type"] = type(exc).__name__
            record["error_message"] = "response was not valid UTF-8 JSON"
            return record
        record["parsed_json"] = parsed
        if status != 200:
            record["error_type"] = "UnexpectedHTTPStatus"
            record["error_message"] = f"expected HTTP 200, received {status}"
            return record
        if not isinstance(parsed, dict):
            record["error_type"] = "InvalidResponseSchema"
            record["error_message"] = "top-level JSON value must be an object"
            return record
        if provider == "pionex":
            data = parsed.get("data")
            symbols = data.get("symbols", []) if isinstance(data, dict) else []
            exact = [item for item in symbols if isinstance(item, dict) and item.get("symbol") == "BTC_USDT"]
            record["summary"] = {
                "result": parsed.get("result") if isinstance(parsed, dict) else None,
                "response_timestamp_ms": parsed.get("timestamp") if isinstance(parsed, dict) else None,
                "exact_symbol_matches": len(exact),
                "symbol_details": exact,
                "availability": (
                    "confirmed" if len(exact) == 1 and exact[0].get("type") == "SPOT"
                    and exact[0].get("baseCurrency") == "BTC" and exact[0].get("quoteCurrency") == "USDT"
                    and exact[0].get("enable") is True else
                    "unavailable" if len(exact) == 0 or (len(exact) == 1 and (exact[0].get("type") != "SPOT" or exact[0].get("enable") is not True))
                    else "indeterminate"
                ),
            }
            if parsed.get("result") is not True:
                record["error_type"] = "PionexAPIError"
                record["error_message"] = "Pionex response result was not true"
                return record
        elif provider == "binance_exchange_info":
            symbols = parsed.get("symbols", []) if isinstance(parsed, dict) else []
            exact = [item for item in symbols if isinstance(item, dict) and item.get("symbol") == "BTCUSDT"]
            record["summary"] = {
                "server_time_ms": parsed.get("serverTime") if isinstance(parsed, dict) else None,
                "exact_symbol_matches": len(exact),
                "symbol_details": exact,
                "availability": (
                    "confirmed" if len(exact) == 1 and exact[0].get("status") == "TRADING"
                    and exact[0].get("isSpotTradingAllowed") is True else
                    "unavailable" if len(exact) == 0 or (len(exact) == 1 and exact[0].get("status") != "TRADING")
                    else "indeterminate"
                ),
            }
        elif provider == "binance_depth":
            bids = parsed.get("bids", []) if isinstance(parsed, dict) else []
            asks = parsed.get("asks", []) if isinstance(parsed, dict) else []
            record["summary"] = {
                "last_update_id": parsed.get("lastUpdateId") if isinstance(parsed, dict) else None,
                "bid_levels": len(bids),
                "ask_levels": len(asks),
                "best_bid": bids[0] if bids else None,
                "best_ask": asks[0] if asks else None,
                "source_event_timestamp_available": False,
            }
        record["capture_status"] = "PASS"
        return record
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        record["captured_at_utc"] = now_utc()
        record["error_type"] = type(exc).__name__
        # Avoid embedding arbitrary response bodies or headers in error text.
        record["error_message"] = str(exc)[:300]
        return record


def main() -> int:
    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    pionex_url = "https://api.pionex.com/api/v1/common/symbols?" + urlencode({"symbols": "BTC_USDT", "type": "SPOT"})
    binance_base = "https://data-api.binance.vision/api/v3"
    requests = [
        ("pionex", pionex_url),
        ("binance_exchange_info", binance_base + "/exchangeInfo?" + urlencode({"symbol": "BTCUSDT"})),
        ("binance_depth", binance_base + "/depth?" + urlencode({"symbol": "BTCUSDT", "limit": 20})),
    ]
    records = [request_capture(provider, url) for provider, url in requests]
    artifact = {
        "schema_version": "public-market-capture-v1",
        "created_at_utc": now_utc(),
        "scope": "public market data only; no credentials; no orders",
        "records": records,
        "overall_status": "PASS" if all(item["capture_status"] == "PASS" for item in records) else "FAIL",
        "limitations": [
            "This is a point-in-time public API capture, not an investment recommendation.",
            "Pionex symbol availability does not prove regional/account access or liquidity.",
            "Binance depth lastUpdateId is not an event timestamp; source-time freshness remains indeterminate.",
            "Payload hashes establish byte identity only, not provider authenticity or correctness.",
        ],
    }
    path = artifact_dir / "public-market-capture.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path),
        "overall_status": artifact["overall_status"],
        "records": [
            {key: item.get(key) for key in ("provider", "capture_status", "http_status", "captured_at_utc", "response_bytes", "response_sha256", "error_type", "error_message", "summary")}
            for item in records
        ],
    }, ensure_ascii=False, indent=2))
    return 0 if artifact["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
