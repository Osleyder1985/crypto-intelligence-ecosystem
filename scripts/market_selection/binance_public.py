"""Public, credential-free Binance Spot reader. It never places orders."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from data_contract import CONTRACT_VERSION, sha256_hex, utc_now_iso, validate_observation
from scripts.market_selection.provider_license_gate import evaluate_provider_use

PARSER_VERSION = "binance-public-v1"
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,30}$")


class ExchangeReadError(RuntimeError):
    """A public endpoint failed or returned data outside the expected contract."""


def _default_http_get(url: str, timeout: float, authorization_record: dict | None = None, use_case: str = "internal_analysis") -> bytes:
    assessment = evaluate_provider_use("binance_spot_market_data", use_case, authorization_record)
    if assessment["decision"] != "ALLOW":
        raise PermissionError("Binance public reader blocked before network: " + ",".join(assessment["reason_codes"]))
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "crypto-intelligence-ecosystem/0.1"})
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise ExchangeReadError(f"public endpoint returned HTTP {status}")
        chunks: list[bytes] = []
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


class BinancePublicSpotReader:
    """Read public Spot market data only; no API key, secret, or order methods."""

    def __init__(
        self,
        http_get: Callable[[str, float], bytes] | None = None,
        clock: Callable[[], str] = utc_now_iso,
        timeout_seconds: float = 10.0,
        authorization_record: dict | None = None,
        use_case: str = "internal_analysis",
    ) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._authorization_record = authorization_record
        self._use_case = use_case
        self._http_get = http_get or (lambda url, timeout: _default_http_get(url, timeout, self._authorization_record, self._use_case))
        self._clock = clock
        self._timeout = float(timeout_seconds)
        self._last_provider_assessment: dict[str, object] | None = None

    @staticmethod
    def _symbol(symbol: str) -> str:
        if not isinstance(symbol, str) or not _SYMBOL_RE.fullmatch(symbol):
            raise ValueError("symbol must be an uppercase alphanumeric Binance symbol")
        return symbol

    def _get_json(self, url: str) -> tuple[object, bytes]:
        try:
            assessment = evaluate_provider_use("binance_spot_market_data", self._use_case, self._authorization_record)
        except (TypeError, ValueError) as exc:
            raise ExchangeReadError("provider use blocked: invalid authorization record") from exc
        self._last_provider_assessment = assessment
        if assessment["decision"] != "ALLOW":
            raise ExchangeReadError("provider use blocked before network: " + ",".join(assessment["reason_codes"]))
        try:
            raw = self._http_get(url, self._timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ExchangeReadError(f"public endpoint request failed: {type(exc).__name__}") from exc
        if not isinstance(raw, bytes):
            raise ExchangeReadError("HTTP transport must return response bytes")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExchangeReadError("endpoint returned invalid UTF-8 JSON") from exc
        if isinstance(payload, dict) and ("code" in payload and "msg" in payload):
            raise ExchangeReadError(f"exchange API error {payload.get('code')}: {payload.get('msg')}")
        return payload, raw

    def fetch_spot_symbol_status(self, symbol: str) -> dict[str, object]:
        """Confirm exact native symbol and Spot trading status from exchangeInfo."""
        symbol = self._symbol(symbol)
        url = "https://api.binance.com/api/v3/exchangeInfo?" + urlencode({"symbol": symbol})
        payload, raw = self._get_json(url)
        if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
            raise ExchangeReadError("exchangeInfo response is missing symbols array")
        matches = [item for item in payload["symbols"] if isinstance(item, dict) and item.get("symbol") == symbol]
        if len(matches) == 0:
            status = "unavailable"
            detail = None
        elif len(matches) > 1:
            raise ExchangeReadError("exchangeInfo returned duplicate exact-symbol entries")
        else:
            detail = matches[0]
            if detail.get("isSpotTradingAllowed") is not True:
                status = "unavailable"
            elif detail.get("status") != "TRADING":
                status = "unavailable"
            else:
                status = "confirmed"
        return {
            "exchange_id": "binance",
            "market_type": "spot",
            "symbol_native": symbol,
            "availability_status": status,
            "source_ref": url,
            "captured_at_utc": self._clock(),
            "payload_sha256": sha256_hex(raw),
            "source_timestamp_utc": None,
            "limitations": ["exchangeInfo response does not provide a market-data timestamp"],
            "raw_payload_retained": False,
            "provider_use_assessment": self._last_provider_assessment,
            "detail": detail,
        }

    def fetch_market_snapshot(self, symbol: str, limit: int = 100) -> dict[str, object]:
        """Join a depth snapshot with exact-symbol metadata from exchangeInfo.

        Returns no order book when Binance does not confirm that exact symbol as
        tradable Spot. Metadata and depth provenance remain separately visible.
        """
        symbol = self._symbol(symbol)
        availability = self.fetch_spot_symbol_status(symbol)
        if availability["availability_status"] != "confirmed":
            return {"availability": availability, "observation": None}
        detail = availability.get("detail")
        if not isinstance(detail, dict):
            raise ExchangeReadError("confirmed symbol status has no metadata object")
        base_asset, quote_asset = detail.get("baseAsset"), detail.get("quoteAsset")
        if not isinstance(base_asset, str) or not base_asset or not isinstance(quote_asset, str) or not quote_asset:
            raise ExchangeReadError("exchangeInfo metadata is missing baseAsset or quoteAsset")
        observation = self.fetch_order_book(symbol, limit)
        observation["base_asset"] = base_asset
        observation["quote_asset"] = quote_asset
        observation["availability_status"] = "confirmed"
        observation["metadata_source_ref"] = availability["source_ref"]
        observation["metadata_payload_sha256"] = availability["payload_sha256"]
        observation["metadata_captured_at_utc"] = availability["captured_at_utc"]
        violations = validate_observation(observation)
        if violations:
            raise ExchangeReadError("joined market snapshot failed contract validation: " + "; ".join(violations))
        return {"availability": availability, "observation": observation}

    def fetch_order_book(self, symbol: str, limit: int = 100) -> dict[str, object]:
        """Fetch a public depth snapshot and emit a normalized observation.

        Binance depth snapshots expose lastUpdateId rather than an event timestamp;
        therefore source_timestamp_utc is null and quality is INDETERMINATE for
        time-sensitive selection until a separate timestamp policy is approved.
        """
        symbol = self._symbol(symbol)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit not in {5, 10, 20, 50, 100, 500, 1000, 5000}:
            raise ValueError("limit must be one of Binance's supported depth limits")
        url = "https://api.binance.com/api/v3/depth?" + urlencode({"symbol": symbol, "limit": limit})
        payload, raw = self._get_json(url)
        if not isinstance(payload, dict) or not isinstance(payload.get("bids"), list) or not isinstance(payload.get("asks"), list):
            raise ExchangeReadError("depth response must contain bids and asks arrays")
        if not payload["bids"] or not payload["asks"]:
            raise ExchangeReadError("depth response contains an empty book side")

        def levels(raw_levels: list[object], side: str) -> list[dict[str, float]]:
            parsed: list[dict[str, float]] = []
            for index, level in enumerate(raw_levels):
                if not isinstance(level, list) or len(level) != 2:
                    raise ExchangeReadError(f"{side}[{index}] must be a [price, quantity] pair")
                try:
                    price, quantity = float(level[0]), float(level[1])
                except (TypeError, ValueError) as exc:
                    raise ExchangeReadError(f"{side}[{index}] price/quantity are not numeric") from exc
                if price <= 0 or quantity <= 0 or not all(map(lambda x: x < float("inf"), (price, quantity))):
                    raise ExchangeReadError(f"{side}[{index}] price/quantity must be finite and positive")
                parsed.append({"price": price, "quantity": quantity})
            prices = [item["price"] for item in parsed]
            if len(prices) != len(set(prices)):
                raise ExchangeReadError(f"{side} contains duplicate price levels")
            return parsed

        bids = levels(payload["bids"], "bids")
        asks = levels(payload["asks"], "asks")
        bids.sort(key=lambda item: item["price"], reverse=True)
        asks.sort(key=lambda item: item["price"])
        best_bid, best_ask = bids[0]["price"], asks[0]["price"]
        if best_bid > best_ask:
            raise ExchangeReadError("depth response is a crossed order book")

        captured = self._clock()
        record: dict[str, object] = {
            "contract_version": CONTRACT_VERSION,
            "observation_id": f"binance:{symbol}:depth:{payload.get('lastUpdateId', 'unknown')}:{captured}",
            "exchange_id": "binance",
            "market_type": "spot",
            "symbol_native": symbol,
            "base_asset": None,
            "quote_asset": None,
            "source_kind": "order_book_snapshot",
            "source_ref": url,
            "source_timestamp_utc": None,
            "captured_at_utc": captured,
            "payload_sha256": sha256_hex(raw),
            "parser_version": PARSER_VERSION,
            "quality_status": "INDETERMINATE",
            "limitations": [
                "Depth snapshot has lastUpdateId but no source event timestamp",
                "base_asset and quote_asset require exact exchangeInfo metadata enrichment",
                "A single snapshot does not guarantee executable liquidity",
            ],
            "source_sequence": payload.get("lastUpdateId"),
            "bids": bids,
            "asks": asks,
            "raw_payload_retained": False,
            "provider_use_assessment": self._last_provider_assessment,
        }
        violations = validate_observation(record)
        # Asset metadata is intentionally unresolved until joined to the exact exchangeInfo symbol.
        structural_errors = [item for item in violations if not item.startswith(("base_asset must", "quote_asset must"))]
        if structural_errors:
            raise ExchangeReadError("normalized observation failed contract validation: " + "; ".join(structural_errors))
        return record
