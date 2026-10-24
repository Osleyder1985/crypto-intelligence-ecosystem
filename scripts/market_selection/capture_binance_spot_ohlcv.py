"""Capture bounded, read-only Binance Spot OHLCV history with immutable page evidence."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from scripts.market_selection.provider_license_gate import evaluate_provider_use, SUPPORTED_USE_CASES
except ModuleNotFoundError:  # Direct script execution places this directory, not the repo root, on sys.path.
    from provider_license_gate import evaluate_provider_use, SUPPORTED_USE_CASES

BASE_URL = "https://data-api.binance.vision/api/v3/klines"
TIMEOUT_SECONDS = 15
READ_CHUNK_BYTES = 64 * 1024
PAGE_LIMIT = 1000
SCHEMA_VERSION = "binance-spot-ohlcv-capture-v1"
INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}
SUPPORTED_INTERVALS = tuple(INTERVAL_MS) + ("1M",)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read_complete(response) -> bytes:
    chunks = []
    while True:
        chunk = response.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _decimal(value, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} is not a decimal value") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def normalize_kline(row, symbol: str, interval: str, captured_at_utc: str) -> dict:
    if not isinstance(row, list) or len(row) != 12:
        raise ValueError("Binance kline row must be an array with exactly 12 fields")
    try:
        open_time = int(row[0])
        close_time = int(row[6])
        trade_count = int(row[8])
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("kline timestamps and trade count must be integers") from exc
    if open_time < 0 or close_time < open_time or trade_count < 0:
        raise ValueError("kline timestamps or trade count are invalid")
    expected_close_time = next_open_time(open_time, interval) - 1
    if close_time != expected_close_time:
        raise ValueError("kline close time does not match the interval boundary")
    open_price = _decimal(row[1], "open")
    high_price = _decimal(row[2], "high")
    low_price = _decimal(row[3], "low")
    close_price = _decimal(row[4], "close")
    base_volume = _decimal(row[5], "base_volume")
    quote_volume = _decimal(row[7], "quote_volume")
    taker_buy_base = _decimal(row[9], "taker_buy_base_volume")
    taker_buy_quote = _decimal(row[10], "taker_buy_quote_volume")
    if min(open_price, high_price, low_price, close_price) <= 0:
        raise ValueError("OHLC prices must be positive")
    if high_price < max(open_price, close_price, low_price) or low_price > min(open_price, close_price):
        raise ValueError("OHLC high/low envelope is invalid")
    if min(base_volume, quote_volume, taker_buy_base, taker_buy_quote) < 0:
        raise ValueError("volume fields must be non-negative")
    return {
        "symbol": symbol,
        "market_type": "SPOT",
        "interval": interval,
        "open_time_ms": open_time,
        "close_time_ms": close_time,
        "open": str(open_price),
        "high": str(high_price),
        "low": str(low_price),
        "close": str(close_price),
        "base_volume": str(base_volume),
        "quote_volume": str(quote_volume),
        "trade_count": trade_count,
        "taker_buy_base_volume": str(taker_buy_base),
        "taker_buy_quote_volume": str(taker_buy_quote),
        "source_timestamp_unit": "milliseconds",
        "captured_at_utc": captured_at_utc,
        "source": BASE_URL,
        "raw_row": row,
    }


def next_open_time(open_time_ms: int, interval: str) -> int:
    if interval in INTERVAL_MS:
        return open_time_ms + INTERVAL_MS[interval]
    if interval != "1M":
        raise ValueError("unsupported interval: " + interval)
    current = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
    if current.day != 1 or any((current.hour, current.minute, current.second, current.microsecond)):
        raise ValueError("1M candle open time must be the first day of a UTC month")
    year, month = current.year, current.month + 1
    if month == 13:
        year, month = year + 1, 1
    return int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)


def is_interval_boundary(timestamp_ms: int, interval: str) -> bool:
    if interval == "1M":
        current = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return current.day == 1 and current.hour == current.minute == current.second == current.microsecond == 0
    if interval == "1w":
        current = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return current.weekday() == 0 and current.hour == current.minute == current.second == current.microsecond == 0
    duration = INTERVAL_MS.get(interval)
    return duration is not None and timestamp_ms % duration == 0


def validate_window(start_time_ms: int, end_time_ms_exclusive: int, interval: str) -> None:
    if interval not in SUPPORTED_INTERVALS:
        raise ValueError("unsupported interval: " + interval)
    if start_time_ms < 0 or end_time_ms_exclusive <= start_time_ms:
        raise ValueError("time window must satisfy 0 <= start < end")
    if not is_interval_boundary(start_time_ms, interval) or not is_interval_boundary(end_time_ms_exclusive, interval):
        raise ValueError("start and exclusive end must align to UTC candle boundaries")


def expected_open_times(start_time_ms: int, end_time_ms_exclusive: int, interval: str) -> list[int]:
    validate_window(start_time_ms, end_time_ms_exclusive, interval)
    expected = []
    current = start_time_ms
    while current < end_time_ms_exclusive:
        expected.append(current)
        following = next_open_time(current, interval)
        if following <= current:
            raise ValueError("interval progression did not advance")
        current = following
    return expected


def build_url(symbol: str, interval: str, start_time_ms: int, end_time_ms_exclusive: int, cursor_ms: int) -> str:
    # Binance endTime is inclusive; project interface uses an exclusive end boundary.
    query = urlencode({
        "symbol": symbol,
        "interval": interval,
        "startTime": cursor_ms,
        "endTime": end_time_ms_exclusive - 1,
        "limit": PAGE_LIMIT,
    })
    return BASE_URL + "?" + query


def request_page(
    url: str,
    *,
    use_case: str = "live_technical_test",
    authorization_record: dict | None = None,
    user_agent: str = "crypto-intelligence-ecosystem-ohlcv/1.0",
) -> dict:
    started = utc_now()
    record = {
        "url": url, "request_started_at_utc": started, "captured_at_utc": None,
        "http_status": None, "response_bytes": None, "response_sha256": None,
        "response_base64": None, "parsed_json": None, "capture_status": "FAIL",
        "normalization_status": "NOT_RUN", "normalization_error": None,
        "error_type": None, "error_message": None, "provider_use_assessment": None,
    }
    try:
        assessment = evaluate_provider_use("binance_spot_market_data", use_case, authorization_record)
    except (TypeError, ValueError):
        assessment = {"schema_version":"crypto-provider-use-assessment-v1","provider_id":"binance_spot_market_data","use_case":use_case,"decision":"BLOCK","reason_codes":["AUTHORIZATION_RECORD_INVALID"],"authorization_evidence_status":"INVALID"}
    record["provider_use_assessment"] = assessment
    if assessment["decision"] != "ALLOW":
        record.update(captured_at_utc=utc_now(),capture_status="BLOCKED",error_type="ProviderUseBlocked",error_message=";".join(assessment["reason_codes"]))
        return record
    if not isinstance(user_agent, str) or not user_agent.strip() or "\\r" in user_agent or "\\n" in user_agent:
        record.update(captured_at_utc=utc_now(), capture_status="FAIL", error_type="InvalidUserAgent",
                      error_message="user_agent must be non-empty and contain no CR/LF")
        return record
    req = Request(url, headers={"Accept": "application/json", "User-Agent": user_agent})
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw = read_complete(response)
        record.update(
            http_status=status, captured_at_utc=utc_now(), response_bytes=len(raw),
            response_sha256=hashlib.sha256(raw).hexdigest(),
            response_base64=base64.b64encode(raw).decode("ascii"),
        )
        payload = json.loads(raw.decode("utf-8"))
        record["parsed_json"] = payload
        if status != 200:
            raise ValueError("expected HTTP 200, received " + str(status))
        if not isinstance(payload, list):
            raise ValueError("Binance klines response must be a JSON array")
        record["capture_status"] = "PASS"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        record.update(captured_at_utc=utc_now(), error_type=type(exc).__name__, error_message=str(exc)[:300])
        if isinstance(exc, HTTPError):
            record["http_status"] = exc.code
            try:
                raw = read_complete(exc)
                record.update(response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest(),
                              response_base64=base64.b64encode(raw).decode("ascii"))
            except OSError:
                pass
    return record


def capture_history(
    symbol: str,
    interval: str,
    start_time_ms: int,
    end_time_ms_exclusive: int,
    *,
    use_case: str = "live_technical_test",
    authorization_record: dict | None = None,
    user_agent: str = "crypto-intelligence-ecosystem-ohlcv/1.0",
) -> dict:
    if not isinstance(symbol, str) or not symbol or symbol.strip() != symbol:
        raise ValueError("symbol must be a non-empty native Binance symbol")
    symbol = symbol.upper()
    validate_window(start_time_ms, end_time_ms_exclusive, interval)
    try:
        assessment = evaluate_provider_use("binance_spot_market_data", use_case, authorization_record)
    except (TypeError, ValueError) as exc:
        assessment = {
            "schema_version": "crypto-provider-use-assessment-v1",
            "provider_id": "binance_spot_market_data",
            "use_case": use_case,
            "decision": "BLOCK",
            "reason_codes": ["AUTHORIZATION_RECORD_INVALID"],
            "authorization_evidence_status": "INVALID",
            "validation_error": str(exc),
        }
    if assessment["decision"] != "ALLOW":
        return {
            "schema_version": SCHEMA_VERSION,
            "overall_status": "BLOCKED",
            "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": symbol, "interval": interval},
            "window": {"start_time_ms_inclusive": start_time_ms, "end_time_ms_exclusive": end_time_ms_exclusive,
                       "timezone": "UTC", "boundary_policy": "half-open [start, end) aligned to candle boundaries"},
            "source": BASE_URL, "requested_open_candle_count": len(expected_open_times(start_time_ms, end_time_ms_exclusive, interval)),
            "captured_candle_count": 0, "missing_open_time_ms": expected_open_times(start_time_ms, end_time_ms_exclusive, interval),
            "unexpected_open_time_ms": [], "pages": [], "candles": [],
            "provider_use_assessment": assessment,
            "limitations": ["Capture was blocked by provider-use authorization policy before any network request."],
        }
    cursor = start_time_ms
    pages = []
    candles_by_open = {}
    while cursor < end_time_ms_exclusive:
        url = build_url(symbol, interval, start_time_ms, end_time_ms_exclusive, cursor)
        page = request_page(
            url,
            use_case=use_case,
            authorization_record=authorization_record,
            user_agent=user_agent,
        )
        pages.append(page)
        if page["capture_status"] != "PASS":
            break
        rows = page["parsed_json"]
        if not rows:
            page["normalization_status"] = "PASS"
            break
        captured_at = page["captured_at_utc"]
        try:
            parsed = [normalize_kline(row, symbol, interval, captured_at) for row in rows]
            parsed.sort(key=lambda candle: candle["open_time_ms"])
            for candle in parsed:
                open_time = candle["open_time_ms"]
                if open_time < cursor:
                    raise ValueError("provider returned a candle older than the pagination cursor")
                if not start_time_ms <= open_time < end_time_ms_exclusive:
                    raise ValueError("provider returned a candle outside the requested half-open window")
                if open_time in candles_by_open:
                    raise ValueError("duplicate candle open time across pages")
            for candle in parsed:
                candles_by_open[candle["open_time_ms"]] = candle
            page["normalization_status"] = "PASS"
        except ValueError as exc:
            page["normalization_status"] = "FAIL"
            page["normalization_error"] = str(exc)
            break
        last_open = parsed[-1]["open_time_ms"]
        next_cursor = last_open + 1
        if next_cursor <= cursor:
            raise ValueError("pagination cursor failed to advance")
        cursor = next_cursor
        if len(rows) < PAGE_LIMIT:
            break

    expected = expected_open_times(start_time_ms, end_time_ms_exclusive, interval)
    actual = sorted(candles_by_open)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    candles = []
    for open_time in actual:
        candle = candles_by_open[open_time]
        candle["closed_at_capture"] = candle["close_time_ms"] < now_ms
        candle["eligible_for_closed_candle_analysis"] = candle["closed_at_capture"]
        candles.append(candle)
    all_pages_pass = bool(pages) and all(page["capture_status"] == "PASS" and page.get("normalization_status") == "PASS" for page in pages)
    complete = all_pages_pass and not missing and not unexpected and len(candles) == len(expected)
    return {
        "schema_version": SCHEMA_VERSION,
        "overall_status": "PASS" if complete else "PARTIAL",
        "market": {"exchange": "binance", "market_type": "SPOT", "symbol_native": symbol, "interval": interval},
        "window": {"start_time_ms_inclusive": start_time_ms, "end_time_ms_exclusive": end_time_ms_exclusive,
                   "timezone": "UTC", "boundary_policy": "half-open [start, end) aligned to candle boundaries"},
        "source": BASE_URL,
        "provider_use_assessment": assessment,
        "requested_open_candle_count": len(expected),
        "captured_candle_count": len(candles),
        "missing_open_time_ms": missing,
        "unexpected_open_time_ms": unexpected,
        "pages": pages,
        "candles": candles,
        "limitations": [
            "Only Binance Spot is implemented by this capture adapter; cross-venue comparisons require separate venue adapters and semantic reconciliation.",
            "A candle's presence in a response does not mean it was closed at capture time; use eligible_for_closed_candle_analysis to prevent current-candle look-ahead.",
            "OHLCV history does not include historical order-book depth; depth-derived metrics cannot be reconstructed from candles.",
            "A successful HTTP capture does not establish investment merit, future performance, or execution availability.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="exact native Binance Spot symbol, e.g. BTCUSDT")
    parser.add_argument("--interval", required=True, choices=SUPPORTED_INTERVALS)
    parser.add_argument("--start-time-ms", required=True, type=int, help="inclusive UTC candle boundary in Unix milliseconds")
    parser.add_argument("--end-time-ms", required=True, type=int, help="exclusive UTC candle boundary in Unix milliseconds")
    parser.add_argument("--use-case", choices=sorted(SUPPORTED_USE_CASES), default="live_technical_test",
                        help="intended use of the provider data; non-test use requires an authorization record")
    parser.add_argument("--authorization-record", help="JSON authorization record matching provider and exact use-case")
    parser.add_argument("--output", default="artifacts/binance-spot-ohlcv.json")
    args = parser.parse_args()
    authorization_record = None
    if args.authorization_record:
        try:
            authorization_record = json.loads(Path(args.authorization_record).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            authorization_record = {"invalid_authorization_file": True}
    result = capture_history(args.symbol, args.interval, args.start_time_ms, args.end_time_ms,
                             use_case=args.use_case, authorization_record=authorization_record)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(path), "overall_status": result["overall_status"],
        "market": result["market"], "requested_open_candle_count": result["requested_open_candle_count"],
        "captured_candle_count": result["captured_candle_count"],
        "missing_candle_count": len(result["missing_open_time_ms"]),
        "page_count": len(result["pages"]), "provider_use_assessment": result.get("provider_use_assessment"), "orders_submitted": False,
    }, ensure_ascii=False, indent=2))
    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
