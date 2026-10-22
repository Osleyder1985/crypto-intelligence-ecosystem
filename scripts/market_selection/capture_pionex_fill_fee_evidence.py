"""Capture Pionex Spot fills as read-only account-specific fee evidence."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.pionex.com"
PATH = "/api/v1/trade/fills"
SCHEMA = "pionex-spot-fill-fee-evidence-v1"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sign_get(path: str, params: dict[str, str], secret: str) -> str:
    if not secret:
        raise ValueError("Pionex API secret is required")
    canonical = "&".join(f"{key}={params[key]}" for key in sorted(params))
    message = f"GET{path}?{canonical}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _decimal(value: object, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} is not a valid decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def normalize_fills(payload: object, symbol: str, quote_currency: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict) or payload.get("result") is not True:
        raise ValueError("Pionex response is not a successful result object")
    data = payload.get("data")
    fills = data.get("fills") if isinstance(data, dict) else None
    if not isinstance(fills, list):
        raise ValueError("Pionex response data.fills is missing")
    out = []
    for i, fill in enumerate(fills):
        if not isinstance(fill, dict):
            raise ValueError(f"fills[{i}] is not an object")
        if fill.get("symbol") != symbol:
            raise ValueError(f"fills[{i}] symbol does not match request")
        side, role = fill.get("side"), fill.get("role")
        if side not in ("BUY", "SELL") or role not in ("MAKER", "TAKER"):
            raise ValueError(f"fills[{i}] side/role is missing or invalid")
        price = _decimal(fill.get("price"), f"fills[{i}].price")
        size = _decimal(fill.get("size"), f"fills[{i}].size")
        fee = _decimal(fill.get("fee"), f"fills[{i}].fee")
        fee_coin = fill.get("feeCoin")
        timestamp = fill.get("timestamp")
        if price <= 0 or size <= 0 or not isinstance(fee_coin, str) or not fee_coin:
            raise ValueError(f"fills[{i}] price, size or fee currency is invalid")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
            raise ValueError(f"fills[{i}].timestamp must be a non-negative millisecond integer")
        quote_notional = price * size
        fee_rate = fee / quote_notional if fee_coin == quote_currency else None
        out.append({
            "symbol": symbol,
            "side": side,
            "role": role,
            "price": str(price),
            "size": str(size),
            "quote_notional": str(quote_notional),
            "fee": str(fee),
            "fee_coin": fee_coin,
            "fee_rate_vs_quote_notional": str(fee_rate) if fee_rate is not None else None,
            "fee_rate_status": "CALCULABLE" if fee_rate is not None else "INDETERMINATE_FEE_COIN_DIFFERS_FROM_QUOTE",
            "fill_timestamp_ms": timestamp,
        })
    return out


def build_evidence(payload: object, raw: bytes, symbol: str, quote_currency: str, requested_start_ms: int, requested_end_ms: int, captured_at_utc: str) -> dict[str, object]:
    fills = normalize_fills(payload, symbol, quote_currency)
    truncated_possible = len(fills) >= 100
    rates = [Decimal(item["fee_rate_vs_quote_notional"]) for item in fills if item["fee_rate_vs_quote_notional"] is not None]
    return {
        "schema_version": SCHEMA,
        "provider": "pionex",
        "market_type": "SPOT",
        "endpoint": PATH,
        "symbol": symbol,
        "quote_currency": quote_currency,
        "requested_start_time_ms": requested_start_ms,
        "requested_end_time_ms": requested_end_ms,
        "captured_at_utc": captured_at_utc,
        "response_timestamp_ms": payload.get("timestamp") if isinstance(payload, dict) else None,
        "http_status": 200,
        "raw_response_bytes": len(raw),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "fills_count": len(fills),
        "truncation_possible": truncated_possible,
        "capture_status": "INDETERMINATE" if truncated_possible or not fills else "PASS",
        "fee_evidence_status": "INDETERMINATE" if truncated_possible or not fills or len(rates) != len(fills) else "OBSERVED_FILLS_ONLY",
        "observed_fill_fee_rates_vs_quote_notional": [str(rate) for rate in rates],
        "observed_rate_min": str(min(rates)) if rates else None,
        "observed_rate_max": str(max(rates)) if rates else None,
        "fills": fills,
        "limitations": [
            "This is historical fill evidence, not proof of the current prospective fee schedule.",
            "Fee rate is calculated only when feeCoin equals the symbol quote currency; no conversion is invented for other fee assets.",
            "The documented endpoint returns latest 100 fills when results exceed 100; a 100-record response is treated as potentially truncated.",
            "No order, cancellation, transfer, or account mutation endpoint is called.",
            "Raw response content is not persisted; its byte length and SHA-256 are retained to reduce disclosure of private trading history.",
        ],
    }


def capture(symbol: str, quote_currency: str, start_ms: int, end_ms: int, api_key: str, api_secret: str, timeout: float = 20.0) -> dict[str, object]:
    if not symbol or not symbol.isascii() or not quote_currency or not quote_currency.isascii():
        raise ValueError("symbol and quote currency must be non-empty ASCII strings")
    if start_ms < 0 or end_ms <= start_ms:
        raise ValueError("time range must satisfy 0 <= start_ms < end_ms")
    timestamp = str(int(time.time() * 1000))
    params = {"endTime": str(end_ms), "startTime": str(start_ms), "symbol": symbol, "timestamp": timestamp}
    signature = sign_get(PATH, params, api_secret)
    query = urlencode(sorted(params.items()))
    url = f"{BASE_URL}{PATH}?{query}"
    request = Request(url, headers={"PIONEX-KEY": api_key, "PIONEX-SIGNATURE": signature, "Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            raw = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"Pionex HTTP error {exc.code}; response body intentionally omitted") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Pionex transport error: {type(exc).__name__}; details omitted") from None
    if status != 200:
        raise RuntimeError(f"Pionex unexpected HTTP status {status}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("Pionex response was not valid UTF-8 JSON; body omitted") from None
    evidence = build_evidence(payload, raw, symbol, quote_currency, start_ms, end_ms, now_utc())
    evidence["http_status"] = status
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="Pionex Spot symbol, e.g. BTC_USDT")
    parser.add_argument("--quote-currency", required=True, help="Quote asset for the symbol, e.g. USDT")
    parser.add_argument("--start-ms", required=True, type=int, help="Inclusive fill timestamp in milliseconds")
    parser.add_argument("--end-ms", required=True, type=int, help="Exclusive fill timestamp in milliseconds")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    api_key, api_secret = os.environ.get("PIONEX_API_KEY", ""), os.environ.get("PIONEX_API_SECRET", "")
    if not api_key or not api_secret:
        print("PIONEX_API_KEY and PIONEX_API_SECRET environment variables are required.", file=sys.stderr)
        return 2
    try:
        evidence = capture(args.symbol, args.quote_currency, args.start_ms, args.end_ms, api_key, api_secret)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence[key] for key in ("output", "symbol", "fills_count", "capture_status", "fee_evidence_status", "raw_response_sha256") if key in evidence} | {"output": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
