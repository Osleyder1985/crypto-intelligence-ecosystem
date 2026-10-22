"""Read-only spot order-book probes across multiple exchanges.

Captures public REST responses and hashes them. It never authenticates or submits orders.
A successful HTTP response is not, by itself, a liquidity or trading-readiness verdict.
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
from urllib.parse import urlencode

TIMEOUT_SECONDS = 12
SCHEMA_VERSION = "multi-exchange-spot-book-probe-v1"

# The quote differs where a venue's public spot market uses USD rather than USDT.
READ_CHUNK_BYTES = 64 * 1024  # Read buffer size only; not a response-size limit.

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

MARKETS = (
    {"asset": "BTC", "pionex": "BTC_USDT", "binance": "BTCUSDT", "okx": "BTC-USDT", "bybit": "BTCUSDT", "mexc": "BTCUSDT", "gate": "BTC_USDT", "bitget": "BTCUSDT"},
    {"asset": "ETH", "pionex": "ETH_USDT", "binance": "ETHUSDT", "okx": "ETH-USDT", "bybit": "ETHUSDT", "mexc": "ETHUSDT", "gate": "ETH_USDT", "bitget": "ETHUSDT"},
    {"asset": "SOL", "pionex": "SOL_USDT", "binance": "SOLUSDT", "okx": "SOL-USDT", "bybit": "SOLUSDT", "mexc": "SOLUSDT", "gate": "SOL_USDT", "bitget": "SOLUSDT"},
)

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def build_requests() -> list[dict[str, str]]:
    requests = []
    for market in MARKETS:
        asset = market["asset"]
        requests.extend([
            {"exchange": "binance", "asset": asset, "symbol": market["binance"], "url": "https://data-api.binance.vision/api/v3/depth?" + urlencode({"symbol": market["binance"], "limit": "100"})},
            {"exchange": "okx", "asset": asset, "symbol": market["okx"], "url": "https://www.okx.com/api/v5/market/books?" + urlencode({"instId": market["okx"], "sz": "20"})},
            {"exchange": "bybit", "asset": asset, "symbol": market["bybit"], "url": "https://api.bybit.com/v5/market/orderbook?" + urlencode({"category": "spot", "symbol": market["bybit"], "limit": "50"})},
            {"exchange": "mexc", "asset": asset, "symbol": market["mexc"], "url": "https://api.mexc.com/api/v3/depth?" + urlencode({"symbol": market["mexc"], "limit": "100"})},
            {"exchange": "gate", "asset": asset, "symbol": market["gate"], "url": "https://api.gateio.ws/api/v4/spot/order_book?" + urlencode({"currency_pair": market["gate"], "limit": "20", "with_id": "true"})},
            {"exchange": "bitget", "asset": asset, "symbol": market["bitget"], "url": "https://api.bitget.com/api/v3/market/orderbook?" + urlencode({"category": "SPOT", "symbol": market["bitget"], "limit": "100"})},
            {"exchange": "pionex", "asset": asset, "symbol": market["pionex"], "url": "https://api.pionex.com/api/v1/market/depth?" + urlencode({"symbol": market["pionex"], "limit": "100"})},
        ])
    return requests

def extract_top_of_book(exchange: str, payload: object) -> tuple[object, object, object]:
    """Return bids, asks, and documented source time where available."""
    if not isinstance(payload, dict):
        raise ValueError("top-level response must be an object")
    if exchange in ("binance", "mexc"):
        return payload.get("bids"), payload.get("asks"), None
    if exchange == "okx":
        if payload.get("code") != "0": raise ValueError("OKX response code was not 0")
        rows = payload.get("data")
        if not isinstance(rows, list) or not rows: raise ValueError("OKX response has no order book")
        book = rows[0]
        return book.get("bids"), book.get("asks"), book.get("ts")
    if exchange == "bybit":
        if payload.get("retCode") != 0: raise ValueError("Bybit retCode was not 0")
        result = payload.get("result")
        if not isinstance(result, dict): raise ValueError("Bybit response has no result object")
        return result.get("b"), result.get("a"), result.get("cts", result.get("ts"))
    if exchange == "gate":
        return payload.get("bids"), payload.get("asks"), payload.get("update")
    if exchange == "bitget":
        if payload.get("code") != "00000": raise ValueError("Bitget response code was not 00000")
        data = payload.get("data")
        if not isinstance(data, dict): raise ValueError("Bitget response has no data object")
        return data.get("b"), data.get("a"), data.get("ts")
    if exchange == "pionex":
        if payload.get("result") is not True: raise ValueError("Pionex response result was not true")
        data = payload.get("data")
        if not isinstance(data, dict): raise ValueError("Pionex response has no data object")
        return data.get("bids"), data.get("asks"), data.get("updateTime")
    raise ValueError(f"unsupported exchange: {exchange}")

def capture_one(spec: dict[str, str]) -> dict[str, object]:
    record: dict[str, object] = {
        **spec, "request_started_at_utc": now_utc(), "captured_at_utc": None,
        "http_status": None, "response_bytes": None, "response_bytes_observed": None,
        "response_limit_bytes": None, "content_length_header": None, "oversize_prefix_sha256": None, "response_sha256": None,
        "response_base64": None, "parsed_json": None, "source_timestamp_raw": None,
        "bids_count": None, "asks_count": None, "best_bid": None, "best_ask": None,
        "capture_status": "FAIL", "error_type": None, "error_message": None,
    }
    request = Request(spec["url"], headers={"Accept": "application/json",
        "User-Agent": "crypto-intelligence-ecosystem-multi-exchange-probe/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw, content_length = read_complete(response)
        record.update(http_status=status, captured_at_utc=now_utc(),
            response_bytes=len(raw), response_bytes_observed=len(raw), content_length_header=content_length, response_sha256=hashlib.sha256(raw).hexdigest(),
            response_base64=base64.b64encode(raw).decode("ascii"))
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("response was not valid UTF-8 JSON") from exc
        record["parsed_json"] = payload
        if status != 200:
            raise ValueError(f"expected HTTP 200, received {status}")
        bids, asks, source_ts = extract_top_of_book(spec["exchange"], payload)
        if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
            raise ValueError("response does not contain non-empty bid and ask arrays")
        # Exchange APIs use string-valued price/size tuples in all adapters here.
        bid_price, ask_price = float(bids[0][0]), float(asks[0][0])
        if bid_price <= 0 or ask_price <= 0:
            raise ValueError("best bid/ask prices must be positive")
        record.update(source_timestamp_raw=source_ts, bids_count=len(bids), asks_count=len(asks),
            best_bid=str(bids[0][0]), best_ask=str(asks[0][0]), capture_status="PASS")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, IndexError, KeyError) as exc:
        record["captured_at_utc"] = now_utc()
        record["error_type"] = type(exc).__name__
        record["error_message"] = str(exc)[:300]
        if isinstance(exc, HTTPError):
            try:
                body = read_complete(exc)[0]
                record["response_bytes_observed"] = len(body)
                record["content_length_header"] = exc.headers.get("Content-Length") if exc.headers else None
                record["response_bytes"] = len(body)
                record["response_sha256"] = hashlib.sha256(body).hexdigest()
                record["response_base64"] = base64.b64encode(body).decode("ascii")
            except OSError:
                pass
    return record


def capture_batch() -> dict[str, object]:
    records = [capture_one(spec) for spec in build_requests()]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": now_utc(),
        "scope": "public spot order-book snapshots only; no credentials; no orders",
        "expected_record_count": len(build_requests()),
        "actual_record_count": len(records),
        "records": records,
        "exchange_status": {
            exchange: ("PASS" if any(r["exchange"] == exchange and r["capture_status"] == "PASS" for r in records) else "FAIL")
            for exchange in ("binance", "okx", "bybit", "mexc", "gate", "bitget", "pionex")
        },
        "overall_status": "PASS" if all(r["capture_status"] == "PASS" for r in records) else "PARTIAL",
        "limitations": [
            "Snapshots are point-in-time observations, not synchronized streaming books.",
            "Snapshot depth and API timestamps have venue-specific semantics; Binance and MEXC REST depth do not provide an event timestamp.",
            "Provider depth limits differ and snapshots do not represent the complete order book.",
            "PASS means a parseable public order-book response only, not adequate liquidity, low slippage, fee approval, or regional trading eligibility.",
            "No orders are submitted and no credentials are used.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/multi-exchange-spot-book-probe.json")
    args = parser.parse_args()
    artifact = capture_batch()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path), "schema_version": artifact["schema_version"],
        "overall_status": artifact["overall_status"], "expected_record_count": artifact["expected_record_count"],
        "actual_record_count": artifact["actual_record_count"], "exchange_status": artifact["exchange_status"],
        "records": [{k: r.get(k) for k in ("exchange", "asset", "symbol", "capture_status", "http_status", "response_bytes", "response_bytes_observed", "response_limit_bytes", "content_length_header", "best_bid", "best_ask", "error_type", "error_message")} for r in artifact["records"]],
    }, ensure_ascii=False, indent=2))
    return 0 if artifact["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
