"""Compare official public Binance.com market-data-only and Binance.US REST access.

Read-only diagnostic: checks server time, exchange metadata, and BTC/ETH/SOL books.
It does not authenticate, place orders, use alternate routing, or attempt to evade
regional restrictions. A successful public-data response is not proof of trading eligibility.
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
from urllib.request import Request, urlopen

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 12
SCHEMA_VERSION = "binance-regional-rest-diagnostic-v1"
VENUES = (
    {
        "venue": "binance_global_market_data_only",
        "base_url": "https://data-api.binance.vision",
        "docs": "https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md",
    },
    {
        "venue": "binance_us",
        "base_url": "https://api.binance.us",
        "docs": "https://github.com/binance-us/binance-us-api-docs",
    },
)
ASSETS = ("BTC", "ETH", "SOL")
QUOTE_PREFERENCE = ("USDT", "USD", "USDC")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_json(url: str) -> dict[str, object]:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "crypto-intelligence-ecosystem-binance-region-diagnostic/1.0",
    })
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        status = getattr(response, "status", None)
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f"response exceeded {MAX_BYTES} byte safety limit")
    if status != 200:
        raise ValueError(f"expected HTTP 200, received {status}")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("response JSON must be an object")
    return {"http_status": status, "raw": raw, "payload": payload}


def capture_endpoint(venue: dict[str, str], kind: str, url: str, asset: str | None = None) -> dict[str, object]:
    record: dict[str, object] = {
        "venue": venue["venue"], "kind": kind, "asset": asset, "url": url,
        "request_started_at_utc": now_utc(), "captured_at_utc": None,
        "http_status": None, "response_bytes": None, "response_sha256": None,
        "response_base64": None, "capture_status": "FAIL",
        "error_type": None, "error_message": None, "parsed_summary": None,
    }
    try:
        result = request_json(url)
        raw = result["raw"]
        payload = result["payload"]
        record.update(
            http_status=result["http_status"], captured_at_utc=now_utc(),
            response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest(),
            response_base64=base64.b64encode(raw).decode("ascii"),
        )
        if kind == "server_time":
            server_ms = payload.get("serverTime")
            if isinstance(server_ms, bool) or not isinstance(server_ms, int):
                raise ValueError("server-time response has no integer serverTime")
            record["parsed_summary"] = {"server_time_ms": server_ms}
        elif kind == "exchange_info":
            symbols = payload.get("symbols")
            if not isinstance(symbols, list):
                raise ValueError("exchange-info response has no symbols list")
            tradable = {
                str(item.get("symbol")): {
                    "baseAsset": item.get("baseAsset"),
                    "quoteAsset": item.get("quoteAsset"),
                    "status": item.get("status"),
                    "isSpotTradingAllowed": item.get("isSpotTradingAllowed"),
                }
                for item in symbols if isinstance(item, dict)
                and item.get("status") == "TRADING"
                and item.get("isSpotTradingAllowed", True) is not False
            }
            record["parsed_summary"] = {
                "trading_symbol_count": len(tradable),
                "available_asset_pairs": {
                    asset: next((f"{asset}{quote}" for quote in QUOTE_PREFERENCE
                                 if f"{asset}{quote}" in tradable), None)
                    for asset in ASSETS
                },
                "symbol_metadata": {
                    symbol: tradable[symbol] for symbol in tradable
                    if any(symbol == f"{asset}{quote}" for asset in ASSETS for quote in QUOTE_PREFERENCE)
                },
            }
        elif kind == "order_book":
            bids, asks = payload.get("bids"), payload.get("asks")
            if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
                raise ValueError("order-book response has no non-empty bids/asks")
            bid_price, ask_price = float(bids[0][0]), float(asks[0][0])
            if bid_price <= 0 or ask_price <= 0:
                raise ValueError("best bid/ask must be positive")
            record["parsed_summary"] = {
                "symbol": asset, "last_update_id": payload.get("lastUpdateId"),
                "best_bid": str(bids[0][0]), "best_ask": str(asks[0][0]),
                "bids_count": len(bids), "asks_count": len(asks),
            }
        else:
            raise ValueError(f"unsupported probe kind: {kind}")
        record["capture_status"] = "PASS"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError,
            UnicodeDecodeError, json.JSONDecodeError, IndexError, KeyError) as exc:
        record["captured_at_utc"] = now_utc()
        record["error_type"] = type(exc).__name__
        record["error_message"] = str(exc)[:300]
        if isinstance(exc, HTTPError):
            record["http_status"] = exc.code
            try:
                body = exc.read(MAX_BYTES + 1)
                if len(body) <= MAX_BYTES:
                    record["response_bytes"] = len(body)
                    record["response_sha256"] = hashlib.sha256(body).hexdigest()
                    record["response_base64"] = base64.b64encode(body).decode("ascii")
                    record["error_message"] = body.decode("utf-8", errors="replace")[:300] or str(exc)[:300]
            except OSError:
                pass
    return record


def capture_venue(venue: dict[str, str]) -> list[dict[str, object]]:
    base = venue["base_url"]
    records = [
        capture_endpoint(venue, "server_time", f"{base}/api/v3/time"),
        capture_endpoint(venue, "exchange_info", f"{base}/api/v3/exchangeInfo"),
    ]
    info = records[1].get("parsed_summary")
    available = info.get("available_asset_pairs", {}) if isinstance(info, dict) else {}
    for asset in ASSETS:
        symbol = available.get(asset) if isinstance(available, dict) else None
        if not symbol:
            records.append({
                "venue": venue["venue"], "kind": "order_book", "asset": asset, "symbol": None,
                "url": None, "request_started_at_utc": now_utc(), "captured_at_utc": now_utc(),
                "http_status": None, "capture_status": "NOT_AVAILABLE",
                "error_type": None, "error_message": "No supported TRADING spot pair found for BTC/ETH/SOL using quote preference USDT, USD, USDC.",
                "parsed_summary": None,
            })
            continue
        url = f"{base}/api/v3/depth?symbol={symbol}&limit=20"
        book = capture_endpoint(venue, "order_book", url, asset=symbol)
        book["asset"] = asset
        records.append(book)
    return records


def capture_batch() -> dict[str, object]:
    records = [record for venue in VENUES for record in capture_venue(venue)]
    venue_status = {}
    for venue in VENUES:
        own = [r for r in records if r["venue"] == venue["venue"]]
        venue_status[venue["venue"]] = {
            "server_time": next((r["capture_status"] for r in own if r["kind"] == "server_time"), "MISSING"),
            "exchange_info": next((r["capture_status"] for r in own if r["kind"] == "exchange_info"), "MISSING"),
            "order_books_passed": sum(r["capture_status"] == "PASS" for r in own if r["kind"] == "order_book"),
            "order_books_expected": len(ASSETS),
        }
    all_pass = all(r["capture_status"] == "PASS" for r in records)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": now_utc(),
        "scope": "official public Binance REST diagnostics only; no credentials; no orders",
        "venue_status": venue_status,
        "expected_asset_count_per_venue": len(ASSETS),
        "records": records,
        "overall_status": "PASS" if all_pass else "PARTIAL",
        "orders_submitted": False,
        "limitations": [
            "Binance.com market-data-only and Binance.US are tested as separate official services.",
            "A public REST success does not establish account eligibility, regional trading eligibility, or WebSocket access.",
            "Order-book snapshots are point-in-time observations, not synchronized streaming books.",
            "Quote currency is recorded and must be normalized before cross-market price comparison.",
            "HTTP 451 is recorded as observed; its precise policy cause is not inferred from status alone.",
            "No proxy, alternate-region routing, credentials, or order endpoints are used.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/binance-regional-rest-diagnostic.json")
    args = parser.parse_args()
    artifact = capture_batch()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path), "overall_status": artifact["overall_status"],
        "venue_status": artifact["venue_status"],
        "records": [{k: r.get(k) for k in ("venue", "kind", "asset", "capture_status", "http_status", "error_type", "error_message", "parsed_summary")} for r in artifact["records"]],
    }, ensure_ascii=False, indent=2))
    return 0 if artifact["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
