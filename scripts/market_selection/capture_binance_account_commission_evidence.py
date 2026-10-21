"""Capture account-specific Binance Spot commission evidence (read-only; no orders)."""
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

DEFAULT_BASE_URL = "https://api.binance.com"
SCHEMA_VERSION = "binance-spot-account-commission-evidence-v1"
COMMISSION_GROUPS = ("standardCommission", "taxCommission", "specialCommission")
RATE_FIELDS = ("maker", "taker", "buyer", "seller")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _valid_rate(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        return False
    return number.is_finite() and number >= 0


def validate_commission_response(payload: object, symbol: str) -> tuple[bool, str]:
    """Validate documented response structure without assuming any rate is universally applicable."""
    if not isinstance(payload, dict):
        return False, "response is not a JSON object"
    if payload.get("symbol") != symbol:
        return False, "response symbol does not match requested symbol"
    for group in COMMISSION_GROUPS:
        rates = payload.get(group)
        if not isinstance(rates, dict) or any(not _valid_rate(rates.get(field)) for field in RATE_FIELDS):
            return False, f"{group} is missing valid maker/taker/buyer/seller rates"
    discount = payload.get("discount")
    if not isinstance(discount, dict):
        return False, "discount metadata is missing"
    if not isinstance(discount.get("enabledForAccount"), bool):
        return False, "discount.enabledForAccount is missing or invalid"
    if not isinstance(discount.get("enabledForSymbol"), bool):
        return False, "discount.enabledForSymbol is missing or invalid"
    if discount.get("enabledForAccount") and discount.get("enabledForSymbol"):
        if not isinstance(discount.get("discountAsset"), str) or not discount["discountAsset"]:
            return False, "discount asset is missing while discount is enabled"
        if not _valid_rate(discount.get("discount")):
            return False, "discount rate is missing or invalid while discount is enabled"
    return True, "account-specific commission response passed structural validation"


def build_signed_url(symbol: str, api_secret: str, timestamp_ms: int, base_url: str = DEFAULT_BASE_URL) -> str:
    """Build a signed GET URL. Callers must never log or persist this URL (it contains a signature)."""
    if not symbol or not symbol.isascii():
        raise ValueError("symbol must be a non-empty ASCII string")
    if not api_secret:
        raise ValueError("API secret is required")
    query = urlencode((("symbol", symbol), ("timestamp", str(timestamp_ms))))
    signature = hmac.new(api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{base_url.rstrip('/')}/api/v3/account/commission?{query}&signature={signature}"


def capture_commission_evidence(
    symbol: str,
    api_key: str,
    api_secret: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timestamp_ms: int | None = None,
    opener=urlopen,
) -> dict[str, object]:
    """Query a signed account endpoint; no order endpoint is called and secrets are not returned."""
    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET are required")
    queried_at = now_utc()
    timestamp = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    request = Request(
        build_signed_url(symbol, api_secret, timestamp, base_url),
        headers={"X-MBX-APIKEY": api_key, "Accept": "application/json"},
    )
    result: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "provider": "Binance Spot",
        "endpoint": "GET /api/v3/account/commission",
        "symbol": symbol,
        "queried_at_utc": queried_at,
        "http_status": None,
        "response_sha256": None,
        "commission_evidence_status": "INDETERMINATE",
        "validation_reason": "no valid response received",
        "response": None,
        "orders_submitted": False,
        "limitations": [
            "The response is account- and symbol-specific at query time; re-query to verify current applicability.",
            "Structural validation does not by itself calculate total execution cost for an order scenario.",
            "This collector does not place, test, or cancel orders.",
            "Use only credentials authorized for the account and endpoint, with the minimum required permissions.",
        ],
    }
    try:
        with opener(request, timeout=12) as response:
            status = getattr(response, "status", None)
            raw = response.read()
        result["http_status"] = status
        result["response_sha256"] = hashlib.sha256(raw).hexdigest()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            result["validation_reason"] = "response was not valid UTF-8 JSON"
            return result
        if status != 200:
            result["validation_reason"] = f"expected HTTP 200, received {status}"
            return result
        valid, reason = validate_commission_response(payload, symbol)
        result["validation_reason"] = reason
        if valid:
            result["commission_evidence_status"] = "PASS"
            result["response"] = payload
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["validation_reason"] = f"HTTP error {exc.code}; response body intentionally not persisted"
    except (URLError, TimeoutError, OSError) as exc:
        result["validation_reason"] = f"request failed: {type(exc).__name__}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="Exact Binance Spot symbol, e.g. BTCUSDT")
    parser.add_argument("--output", default="artifacts/binance-spot-account-commission-evidence.json")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Official API base URL for the authorized account/region")
    args = parser.parse_args()
    api_key, api_secret = os.environ.get("BINANCE_API_KEY"), os.environ.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        parser.error("set BINANCE_API_KEY and BINANCE_API_SECRET in the local environment; never commit them")
    evidence = capture_commission_evidence(args.symbol, api_key, api_secret, base_url=args.base_url)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path),
        "symbol": evidence["symbol"],
        "commission_evidence_status": evidence["commission_evidence_status"],
        "http_status": evidence["http_status"],
        "response_sha256": evidence["response_sha256"],
        "validation_reason": evidence["validation_reason"],
        "orders_submitted": False,
    }, ensure_ascii=False, indent=2))
    return 0 if evidence["commission_evidence_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
