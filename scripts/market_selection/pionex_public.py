"""Public Pionex Spot symbol availability reader; no credentials or trading methods."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from data_contract import sha256_hex, utc_now_iso

MAX_RESPONSE_BYTES = 5 * 1024 * 1024
_SYMBOL_RE = re.compile(r"^[A-Z0-9]+_[A-Z0-9]+$")


class PionexReadError(RuntimeError):
    """Public Pionex endpoint failed or returned an invalid response."""


def _default_http_get(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "crypto-intelligence-ecosystem/0.1"})
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise PionexReadError(f"public endpoint returned HTTP {status}")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    if len(payload) > MAX_RESPONSE_BYTES:
        raise PionexReadError("response exceeded configured size limit")
    return payload


class PionexPublicSpotReader:
    """Confirm exact symbol, Spot market type and Pionex enable flag using public API."""

    def __init__(
        self,
        http_get: Callable[[str, float], bytes] | None = None,
        clock: Callable[[], str] = utc_now_iso,
        timeout_seconds: float = 10.0,
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        self._http_get = http_get or _default_http_get
        self._clock = clock
        self._timeout = float(timeout_seconds)

    @staticmethod
    def _symbol(symbol: str) -> tuple[str, str, str]:
        if not isinstance(symbol, str) or not _SYMBOL_RE.fullmatch(symbol):
            raise ValueError("symbol must use exact BASE_QUOTE uppercase format")
        base, quote = symbol.split("_", 1)
        return symbol, base, quote

    def check_spot_symbol(self, symbol: str) -> dict[str, object]:
        """Check exact symbol identity and enable status; never infer from Binance."""
        symbol, expected_base, expected_quote = self._symbol(symbol)
        url = "https://api.pionex.com/api/v1/common/symbols?" + urlencode({
            "symbols": symbol,
            "type": "SPOT",
        })
        try:
            raw = self._http_get(url, self._timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise PionexReadError(f"public endpoint request failed: {type(exc).__name__}") from exc
        if not isinstance(raw, bytes):
            raise PionexReadError("HTTP transport must return response bytes")
        if len(raw) > MAX_RESPONSE_BYTES:
            raise PionexReadError("response exceeded configured size limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PionexReadError("endpoint returned invalid UTF-8 JSON") from exc
        if not isinstance(payload, dict) or payload.get("result") is not True:
            raise PionexReadError("Pionex response result is missing or not true")
        data = payload.get("data")
        symbols = data.get("symbols") if isinstance(data, dict) else None
        if not isinstance(symbols, list):
            raise PionexReadError("Pionex response is missing data.symbols array")
        matches = [item for item in symbols if isinstance(item, dict) and item.get("symbol") == symbol]
        if len(matches) > 1:
            raise PionexReadError("Pionex returned duplicate exact-symbol entries")

        detail = matches[0] if matches else None
        if detail is None:
            availability = "unavailable"
            reason = "exact symbol not present in Pionex response"
        elif detail.get("type") != "SPOT":
            availability = "unavailable"
            reason = "exact symbol is not reported as Spot"
        elif detail.get("baseCurrency") != expected_base or detail.get("quoteCurrency") != expected_quote:
            raise PionexReadError("symbol base/quote metadata does not match the exact requested symbol")
        elif detail.get("enable") is not True:
            availability = "unavailable"
            reason = "Pionex symbol enable flag is not true"
        else:
            availability = "confirmed"
            reason = "exact Pionex Spot symbol is present and enabled"

        captured = self._clock()
        response_timestamp = payload.get("timestamp")
        source_timestamp = None
        freshness_status = "INDETERMINATE"
        if isinstance(response_timestamp, (int, float)) and not isinstance(response_timestamp, bool) and math.isfinite(response_timestamp) and response_timestamp > 0:
            try:
                source_timestamp = datetime.fromtimestamp(response_timestamp / 1000.0, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
                captured_dt = datetime.fromisoformat(captured.replace("Z", "+00:00"))
                source_dt = datetime.fromisoformat(source_timestamp.replace("Z", "+00:00"))
                if captured_dt.tzinfo is not None and captured_dt.utcoffset() is not None and source_dt <= captured_dt:
                    freshness_status = "PASS"
                elif source_dt > captured_dt:
                    freshness_status = "INDETERMINATE"
            except (ValueError, OverflowError, OSError):
                source_timestamp = None

        return {
            "exchange_id": "pionex",
            "market_type": "spot",
            "symbol_native": symbol,
            "base_asset": detail.get("baseCurrency") if detail else expected_base,
            "quote_asset": detail.get("quoteCurrency") if detail else expected_quote,
            "availability_status": availability,
            "availability_reason": reason,
            "freshness_status": freshness_status,
            "source_ref": url,
            "source_timestamp_utc": source_timestamp,
            "captured_at_utc": captured,
            "payload_sha256": sha256_hex(raw),
            "source_kind": "spot_symbol_listing",
            "limitations": [
                "Public listing response is a point-in-time observation",
                "Availability does not prove regional eligibility or account-specific access",
                "Availability does not assess liquidity, fees, asset risk or profitability",
            ],
            "raw_payload_retained": False,
            "detail": detail,
        }
