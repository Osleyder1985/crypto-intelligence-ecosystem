"""Capture all Pionex public Spot OHLCV history available through the documented endpoint.

This adapter imposes no total byte, page-count, or candle-count cap. It paginates backwards
until an empty page, a provider-declared history limit, or a recorded failure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.pionex.com/api/v1/market/klines"
DOC_URL = "https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines"
OPENAPI_URL = "https://github.com/pionex-official/pionex-open-api/blob/main/openapi.yaml"
TIMEOUT_SECONDS = 15
READ_CHUNK_BYTES = 64 * 1024  # Buffer only; not a total response-size cap.
PAGE_LIMIT = 500  # Official endpoint maximum.
OFFICIAL_HISTORY_LIMIT_RECORDS = 10_000  # Metadata only; not a local stop condition.
SCHEMA_VERSION = "pionex-spot-ohlcv-capture-v1"
INTERVAL_MS = {
    "1M": 60_000, "5M": 300_000, "15M": 900_000, "30M": 1_800_000,
    "60M": 3_600_000, "4H": 14_400_000, "8H": 28_800_000,
    "12H": 43_200_000, "1D": 86_400_000,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read_complete(response: Any) -> bytes:
    """Read to EOF in chunks; never cap total response bytes."""
    chunks = []
    while True:
        chunk = response.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a decimal value") from exc
    if not result.is_finite() or (result <= 0 if positive else result < 0):
        raise ValueError(f"{field} must be finite and {'positive' if positive else 'non-negative'}")
    return result


def normalize_kline(row: Any, symbol: str, interval: str, captured_at_utc: str, page_index: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError("Pionex kline must be a JSON object")
    try:
        source_time_ms = int(row["time"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("kline time must be an integer millisecond timestamp") from exc
    if source_time_ms < 0:
        raise ValueError("kline time must be non-negative")
    prices = {key: _decimal(row.get(key), key, positive=True) for key in ("open", "high", "low", "close")}
    if prices["high"] < max(prices["open"], prices["close"], prices["low"]):
        raise ValueError("kline high is below the OHLC envelope")
    if prices["low"] > min(prices["open"], prices["close"], prices["high"]):
        raise ValueError("kline low is above the OHLC envelope")
    volume_raw = _decimal(row.get("volume"), "volume")
    return {
        "exchange": "pionex", "market_type": "SPOT", "symbol_native": symbol,
        "interval_native": interval, "source_time_ms": source_time_ms,
        "source_time_utc": datetime.fromtimestamp(source_time_ms / 1000, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "timestamp_unit": "milliseconds",
        "timestamp_role_status": "INDETERMINATE_OFFICIAL_SCHEMA_DOES_NOT_SPECIFY_OPEN_OR_CLOSE_ROLE",
        "open": str(prices["open"]), "high": str(prices["high"]),
        "low": str(prices["low"]), "close": str(prices["close"]),
        "volume_raw": str(volume_raw),
        "volume_semantics": "Official schema describes total trading volume; denomination is not specified.",
        "volume_unit_status": "INDETERMINATE", "captured_at_utc": captured_at_utc,
        "source_endpoint": BASE_URL, "page_index": page_index, "raw_row": row,
    }


def build_url(symbol: str, interval: str, end_time_ms: int | None = None) -> str:
    params: dict[str, str] = {"symbol": symbol, "interval": interval, "limit": str(PAGE_LIMIT)}
    if end_time_ms is not None:
        params["endTime"] = str(end_time_ms)
    return BASE_URL + "?" + urlencode(params)


def request_page(url: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "url": url, "request_started_at_utc": utc_now(), "captured_at_utc": None,
        "http_status": None, "response_bytes": None, "response_sha256": None,
        "response_base64": None, "parsed_json": None, "capture_status": "FAIL",
        "normalization_status": "NOT_RUN", "normalization_error": None,
        "error_type": None, "error_message": None,
    }
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "crypto-intelligence-ecosystem-pionex-ohlcv/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw = read_complete(response)
        record.update(http_status=status, captured_at_utc=utc_now(), response_bytes=len(raw),
                      response_sha256=hashlib.sha256(raw).hexdigest(),
                      response_base64=base64.b64encode(raw).decode("ascii"))
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("response is not valid UTF-8 JSON") from exc
        record["parsed_json"] = payload
        if status != 200:
            raise ValueError(f"expected HTTP 200, received {status}")
        if not isinstance(payload, dict) or payload.get("result") is not True:
            raise ValueError("Pionex response result was not true")
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("klines"), list):
            raise ValueError("Pionex response has no data.klines array")
        record["capture_status"] = "PASS"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        record.update(captured_at_utc=utc_now(), error_type=type(exc).__name__, error_message=str(exc)[:300])
        if isinstance(exc, HTTPError):
            record["http_status"] = exc.code
            try:
                raw = read_complete(exc)
                record.update(response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest(),
                              response_base64=base64.b64encode(raw).decode("ascii"))
                try:
                    record["parsed_json"] = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass
            except OSError:
                pass
    return record


def _provider_limit_error(page: dict[str, Any]) -> bool:
    payload = page.get("parsed_json")
    if not isinstance(payload, dict):
        return False
    code = payload.get("code") or payload.get("errorCode") or payload.get("error_code")
    return code == "MARKET_INVALID_TIME" or "MARKET_INVALID_TIME" in json.dumps(payload, ensure_ascii=False).upper()


def capture_history(
    symbol: str, interval: str, *, end_time_ms: int | None = None,
    start_time_ms: int | None = None,
    page_fetcher: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not isinstance(symbol, str) or not symbol.strip() or symbol.strip() != symbol or any(ch.isspace() for ch in symbol):
        raise ValueError("symbol must be a non-empty native Pionex symbol without whitespace")
    if interval not in INTERVAL_MS:
        raise ValueError("unsupported Pionex interval: " + str(interval))
    if end_time_ms is not None and (isinstance(end_time_ms, bool) or not isinstance(end_time_ms, int) or end_time_ms < 0):
        raise ValueError("end_time_ms must be a non-negative integer")
    if start_time_ms is not None and (isinstance(start_time_ms, bool) or not isinstance(start_time_ms, int) or start_time_ms < 0):
        raise ValueError("start_time_ms must be a non-negative integer")
    if start_time_ms is not None and end_time_ms is not None and start_time_ms >= end_time_ms:
        raise ValueError("start_time_ms must be less than end_time_ms")
    fetch_page = page_fetcher or request_page
    cursor_end = end_time_ms
    pages: list[dict[str, Any]] = []
    candles: list[dict[str, Any]] = []
    seen_times: set[int] = set()
    duplicate_times: set[int] = set()
    previous_page_oldest: int | None = None
    stop_reason: str | None = None
    provider_history_limit_reached = False
    pagination_progress_status = "PASS"

    while True:
        page = fetch_page(build_url(symbol, interval, cursor_end))
        page_index = len(pages)
        pages.append(page)
        page["page_index"] = page_index
        if page.get("capture_status") != "PASS":
            if _provider_limit_error(page):
                stop_reason = "PROVIDER_HISTORY_LIMIT_REACHED"
                provider_history_limit_reached = True
            else:
                stop_reason = "REQUEST_OR_SCHEMA_FAILURE"
            break
        rows = page["parsed_json"]["data"]["klines"]
        if not rows:
            page["normalization_status"] = "PASS"
            stop_reason = "NO_MORE_RECORDS"
            break
        try:
            normalized = [normalize_kline(row, symbol, interval, page.get("captured_at_utc") or utc_now(), page_index) for row in rows]
        except ValueError as exc:
            page["normalization_status"] = "FAIL"
            page["normalization_error"] = str(exc)[:300]
            stop_reason = "NORMALIZATION_FAILURE"
            break
        normalized.sort(key=lambda item: item["source_time_ms"])
        page_times = [item["source_time_ms"] for item in normalized]
        if len(page_times) != len(set(page_times)):
            duplicate_times.update(t for t in page_times if page_times.count(t) > 1)
            page["normalization_status"] = "FAIL"
            page["normalization_error"] = "duplicate source_time_ms within one page"
            candles.extend(normalized)
            stop_reason = "DUPLICATE_SOURCE_TIMESTAMPS"
            break
        page_oldest = page_times[0]
        duplicate_times.update(set(page_times) & seen_times)
        if previous_page_oldest is not None and page_oldest >= previous_page_oldest:
            pagination_progress_status = "FAIL"
            page["normalization_status"] = "FAIL"
            page["normalization_error"] = "backward pagination did not move to older source timestamps"
            candles.extend(normalized)
            stop_reason = "PAGINATION_NO_PROGRESS"
            break
        page["normalization_status"] = "PASS"
        page["normalized_candle_count"] = len(normalized)
        for candle in normalized:
            timestamp = candle["source_time_ms"]
            seen_times.add(timestamp)
            if start_time_ms is None or timestamp >= start_time_ms:
                candles.append(candle)
        if start_time_ms is not None and page_oldest <= start_time_ms:
            stop_reason = "REQUESTED_START_BOUND_REACHED"
            break
        if page_oldest <= 0:
            stop_reason = "EARLIEST_REPRESENTABLE_TIMESTAMP_REACHED"
            break
        previous_page_oldest = page_oldest
        # Boundary inclusivity is not explicit in the official contract. Subtract 1 ms
        # from the oldest observed timestamp and detect overlap/no-progress explicitly.
        cursor_end = page_oldest - 1

    candles.sort(key=lambda item: (item["source_time_ms"], item["page_index"]))
    timestamps = [item["source_time_ms"] for item in candles]
    unique_times = sorted(set(timestamps))
    expected_step = INTERVAL_MS[interval]
    gaps = [
        {"previous_source_time_ms": left, "next_source_time_ms": right,
         "observed_delta_ms": right - left, "nominal_interval_ms": expected_step}
        for left, right in zip(unique_times, unique_times[1:]) if right - left > expected_step
    ]
    all_pages_pass = bool(pages) and all(
        page.get("capture_status") == "PASS" and page.get("normalization_status") == "PASS"
        for page in pages
    )
    complete_stop = stop_reason in {"NO_MORE_RECORDS", "REQUESTED_START_BOUND_REACHED", "EARLIEST_REPRESENTABLE_TIMESTAMP_REACHED"}
    if len(candles) >= OFFICIAL_HISTORY_LIMIT_RECORDS:
        provider_history_limit_reached = True
    history_completeness = (
        "INDETERMINATE_PROVIDER_HISTORY_LIMIT"
        if provider_history_limit_reached
        else "OBSERVED_ENDPOINT_BOUNDARY_REACHED"
        if stop_reason == "NO_MORE_RECORDS"
        else "REQUESTED_START_BOUND_REACHED"
        if stop_reason == "REQUESTED_START_BOUND_REACHED"
        else "INDETERMINATE_CAPTURE_INTERRUPTED"
    )
    overall = "PASS" if all_pages_pass and complete_stop and not duplicate_times and pagination_progress_status == "PASS" and candles and not provider_history_limit_reached else "PARTIAL"
    return {
        "schema_version": SCHEMA_VERSION, "overall_status": overall,
        "analysis_readiness_status": "INDETERMINATE", "created_at_utc": utc_now(),
        "market": {"exchange": "pionex", "market_type": "SPOT", "symbol_native": symbol, "interval_native": interval},
        "request": {
            "source_endpoint": BASE_URL, "official_documentation": DOC_URL, "official_openapi": OPENAPI_URL,
            "end_time_ms_initial": end_time_ms, "start_time_ms_optional": start_time_ms,
            "page_limit": PAGE_LIMIT, "official_page_limit_range": [1, 500],
            "official_documented_history_limit_records": OFFICIAL_HISTORY_LIMIT_RECORDS,
            "local_total_response_byte_limit": None, "local_total_candle_limit": None, "local_page_count_limit": None,
            "pagination_policy": "backward endTime cursor = oldest observed source_time_ms - 1; progress and duplicate checks enabled",
            "end_time_inclusivity_status": "INDETERMINATE_OFFICIAL_CONTRACT_DOES_NOT_SPECIFY_BOUNDARY_INCLUSIVITY",
        },
        "coverage": {
            "pages_captured": len(pages), "captured_candle_rows": len(candles),
            "unique_source_timestamps": len(set(timestamps)), "duplicate_source_time_ms": sorted(duplicate_times),
            "observed_timestamp_gaps": gaps,
            "oldest_source_time_ms": min(timestamps) if timestamps else None,
            "newest_source_time_ms": max(timestamps) if timestamps else None,
            "stop_reason": stop_reason, "provider_history_limit_reached": provider_history_limit_reached,
            "history_completeness_status": history_completeness,
            "pagination_progress_status": pagination_progress_status,
        },
        "pages": pages, "candles": candles,
        "limitations": [
            "Official documentation defines Kline.time as a millisecond timestamp but does not explicitly label it as candle-open or candle-close time; timestamp role remains INDETERMINATE.",
            "Official documentation describes volume as total trading volume but does not document its denomination; volume_unit_status remains INDETERMINATE and volume is never relabelled as base or quote volume.",
            "The official endpoint documents a maximum of 10,000 retrievable records and a page limit of 500. The adapter imposes no additional total response-byte, page-count, or candle-count cap.",
            "endTime boundary inclusivity is not explicit in the official contract; backward pagination uses oldest source timestamp minus one millisecond and records duplicate/progress anomalies.",
            "An empty page marks the endpoint's observed history boundary, not proof of history beyond provider availability.",
            "This artifact is raw-history capture, not cross-venue comparability, prediction, investment recommendation, or trading authorization.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="Exact native Pionex Spot symbol, e.g. BTC_USDT")
    parser.add_argument("--interval", required=True, choices=tuple(INTERVAL_MS))
    parser.add_argument("--end-time-ms", type=int, default=None, help="Optional source timestamp cursor; omit to start at latest history")
    parser.add_argument("--start-time-ms", type=int, default=None, help="Optional lower source timestamp boundary; omit to page to provider boundary")
    parser.add_argument("--output", default="artifacts/pionex-spot-ohlcv.json")
    args = parser.parse_args()
    result = capture_history(args.symbol, args.interval, end_time_ms=args.end_time_ms, start_time_ms=args.start_time_ms)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output), "overall_status": result["overall_status"],
        "analysis_readiness_status": result["analysis_readiness_status"],
        "pages_captured": result["coverage"]["pages_captured"],
        "captured_candle_rows": result["coverage"]["captured_candle_rows"],
        "stop_reason": result["coverage"]["stop_reason"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
