"""Exploratory Pareto frontier from preserved public Spot ticker and order-book snapshots.

No thresholds, weights, investment recommendation, or trading action is applied.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from scripts.market_selection.provider_license_gate import evaluate_artifact_use
except ModuleNotFoundError:
    from provider_license_gate import evaluate_artifact_use

QUOTE_SCHEMA = "multi-exchange-spot-quote-volume-v1"
BOOK_SCHEMA = "multi-exchange-spot-book-probe-v1"
OUTPUT_SCHEMA = "spot-market-exploratory-pareto-v1"
TOP_LEVELS = 10


def _time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any, field: str, *, positive: bool = True) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be decimal") from exc
    if not number.is_finite() or (number <= 0 if positive else number < 0):
        raise ValueError(f"{field} must be finite and {'positive' if positive else 'non-negative'}")
    return number


def _load(path: str | Path, schema: str) -> dict[str, Any]:
    source = Path(path)
    raw_file = source.read_bytes()
    try:
        artifact = json.loads(raw_file.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{source.name}: invalid UTF-8 JSON") from exc
    if not isinstance(artifact, dict) or artifact.get("schema_version") != schema:
        raise ValueError(f"{source.name}: expected schema_version {schema}")
    _time(artifact.get("created_at_utc"), f"{source.name}.created_at_utc")
    records = artifact.get("records")
    if not isinstance(records, list) or artifact.get("expected_record_count") != len(records) or artifact.get("actual_record_count") != len(records):
        raise ValueError(f"{source.name}: expected/actual/array record counts do not match")
    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"{source.name}: records[{index}] must be an object")
        key = (str(record.get("exchange", "")), str(record.get("asset", "")))
        if not all(key) or key in seen:
            raise ValueError(f"{source.name}: missing or duplicate exchange/asset key {key}")
        seen.add(key)
        encoded = record.get("response_base64")
        if not isinstance(encoded, str) or not encoded:
            if record.get("capture_status") == "PASS":
                raise ValueError(f"{source.name}: successful record {key} has no preserved body")
            record["_integrity_status"] = "UNAVAILABLE"
            continue
        try:
            body = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError(f"{source.name}: invalid Base64 for {key}") from exc
        digest = record.get("response_sha256")
        if not isinstance(digest, str) or hashlib.sha256(body).hexdigest() != digest:
            raise ValueError(f"{source.name}: SHA-256 mismatch for {key}")
        if isinstance(record.get("response_bytes"), bool) or record.get("response_bytes") != len(body):
            raise ValueError(f"{source.name}: response byte count mismatch for {key}")
        if record.get("capture_status") == "PASS":
            try:
                parsed = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"{source.name}: successful response is not UTF-8 JSON for {key}") from exc
            if parsed != record.get("parsed_json"):
                raise ValueError(f"{source.name}: parsed_json differs from preserved bytes for {key}")
        record["_integrity_status"] = "VERIFIED"
    return {
        "schema_version": schema,
        "path": source.name,
        "file_sha256": hashlib.sha256(raw_file).hexdigest(),
        "created_at_utc": artifact["created_at_utc"],
        "overall_status": artifact.get("overall_status"),
        "expected_record_count": len(records),
        "actual_record_count": len(records),
        "records": records,
    }


def _levels(exchange: str, payload: dict[str, Any]) -> tuple[Any, Any]:
    if exchange in ("binance", "mexc", "gate"):
        return payload.get("bids"), payload.get("asks")
    if exchange == "okx":
        rows = payload.get("data")
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            raise ValueError("OKX order-book row missing")
        return rows[0].get("bids"), rows[0].get("asks")
    if exchange == "bybit":
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("Bybit result object missing")
        return result.get("b"), result.get("a")
    if exchange == "bitget":
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Bitget data object missing")
        return data.get("b"), data.get("a")
    if exchange == "pionex":
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Pionex data object missing")
        return data.get("bids"), data.get("asks")
    raise ValueError(f"unsupported exchange: {exchange}")


def _parse_levels(raw: Any, side: str, exchange: str) -> list[tuple[Decimal, Decimal]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{exchange} {side} must be a non-empty list")
    result = []
    for index, level in enumerate(raw):
        if not isinstance(level, list) or len(level) < 2:
            raise ValueError(f"{exchange} {side}[{index}] must contain price and quantity")
        result.append((_decimal(level[0], f"{side}[{index}].price"),
                       _decimal(level[1], f"{side}[{index}].quantity")))
    prices = [item[0] for item in result]
    if len(prices) != len(set(prices)):
        raise ValueError(f"{exchange} {side} has duplicate prices")
    if prices != sorted(prices, reverse=(side == "bids")):
        raise ValueError(f"{exchange} {side} is not price-sorted")
    return result


def _quote_value(record: dict[str, Any]) -> tuple[Decimal | None, list[str]]:
    reasons = []
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        return None, [f"quote_capture_not_success:{record.get('http_status')}"]
    if record.get("_integrity_status") != "VERIFIED":
        reasons.append("quote_payload_integrity_not_verified")
    if record.get("quote_currency") != "USDT":
        reasons.append("quote_currency_not_USDT")
    if record.get("quote_volume_status") != "VALID":
        reasons.append("quote_volume_status_not_valid")
    if record.get("quote_volume_unit") != "USDT":
        reasons.append("quote_volume_unit_not_USDT")
    if record.get("quote_volume_unit_status") != "DOCUMENTED":
        reasons.append("quote_volume_unit_not_documented")
    try:
        value = _decimal(record.get("quote_volume_decimal"), "quote_volume_decimal", positive=False)
    except ValueError:
        value = None
    if value is None:
        reasons.append("quote_volume_value_missing_or_invalid")
    return (value if not reasons else None), reasons


def _book_values(record: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        return None, [f"book_capture_not_success:{record.get('http_status')}"]
    if record.get("_integrity_status") != "VERIFIED":
        return None, ["book_payload_integrity_not_verified"]
    payload = record.get("parsed_json")
    if not isinstance(payload, dict):
        return None, ["book_payload_not_object"]
    try:
        bids_raw, asks_raw = _levels(str(record.get("exchange")), payload)
        bids = _parse_levels(bids_raw, "bids", str(record.get("exchange")))
        asks = _parse_levels(asks_raw, "asks", str(record.get("exchange")))
    except ValueError as exc:
        return None, [f"book_levels_invalid:{exc}"]
    if len(bids) < TOP_LEVELS or len(asks) < TOP_LEVELS:
        return None, [f"fewer_than_{TOP_LEVELS}_levels_on_each_side"]
    bid, ask = bids[0][0], asks[0][0]
    if bid > ask:
        return None, ["crossed_order_book"]
    mid = (bid + ask) / Decimal(2)
    spread = (ask - bid) / mid * Decimal(10_000)
    bid_depth = sum((p * q for p, q in bids[:TOP_LEVELS]), Decimal(0))
    ask_depth = sum((p * q for p, q in asks[:TOP_LEVELS]), Decimal(0))
    return {
        "best_bid": str(bid), "best_ask": str(ask), "spread_bps": str(spread),
        "bid_top10_quote_notional": str(bid_depth), "ask_top10_quote_notional": str(ask_depth),
        "bid_levels_received": len(bids), "ask_levels_received": len(asks),
        "book_source_timestamp_raw": record.get("source_timestamp_raw"),
    }, []


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    av = [Decimal(a[k]) for k in ("quote_turnover_24h", "bid_top10_quote_notional", "ask_top10_quote_notional")]
    bv = [Decimal(b[k]) for k in ("quote_turnover_24h", "bid_top10_quote_notional", "ask_top10_quote_notional")]
    asp, bsp = Decimal(a["spread_bps"]), Decimal(b["spread_bps"])
    no_worse = all(x >= y for x, y in zip(av, bv)) and asp <= bsp
    strictly_better = any(x > y for x, y in zip(av, bv)) or asp < bsp
    return no_worse and strictly_better


def analyze_files(quote_path: str | Path, book_path: str | Path) -> dict[str, Any]:
    quote = _load(quote_path, QUOTE_SCHEMA)
    book = _load(book_path, BOOK_SCHEMA)
    for artifact in (quote, book):
        provider_use = evaluate_artifact_use(artifact, "internal_analysis")
        if provider_use["decision"] != "ALLOW":
            raise PermissionError("Pareto analysis blocked before use: " + ",".join(provider_use["reason_codes"]))
    qmap = {(r["exchange"], r["asset"]): r for r in quote["records"]}
    bmap = {(r["exchange"], r["asset"]): r for r in book["records"]}
    candidates = []
    for exchange, asset in sorted(set(qmap) | set(bmap)):
        q, b = qmap.get((exchange, asset)), bmap.get((exchange, asset))
        reasons = []
        qvalue, bvalue = None, None
        if q is None or b is None:
            reasons.append("quote_or_book_record_missing")
        if q is not None:
            qvalue, qreasons = _quote_value(q)
            reasons.extend(qreasons)
        if b is not None:
            bvalue, breasons = _book_values(b)
            reasons.extend(breasons)
        if q is not None and b is not None and q.get("symbol") != b.get("symbol"):
            reasons.append("native_symbol_mismatch_between_artifacts")
        qtime = q.get("captured_at_utc") if q else None
        btime = b.get("captured_at_utc") if b else None
        skew_ms = None
        if qtime and btime:
            try:
                skew_ms = round(abs((_time(qtime, "quote captured_at_utc") -
                                     _time(btime, "book captured_at_utc")).total_seconds()) * 1000, 3)
            except ValueError:
                reasons.append("capture_timestamp_invalid")
        complete = qvalue is not None and bvalue is not None and not reasons
        row = {
            "market_id": f"{exchange}:{asset}", "exchange": exchange, "asset": asset,
            "symbol_native": (q or b or {}).get("symbol"),
            "quote_turnover_24h": str(qvalue) if qvalue is not None else None,
            "quote_source_timestamp_raw": q.get("source_timestamp_raw") if q else None,
            "quote_captured_at_utc": qtime, "book_captured_at_utc": btime,
            "quote_book_capture_skew_ms": skew_ms,
            "freshness_status": "INDETERMINATE",
            "candidate_status": "EXPLORATORY_ONLY" if complete else "INDETERMINATE",
            "exclusion_reasons": [] if complete else sorted(set(reasons)),
            "pareto_frontier_member": False, "dominated_by": [],
        }
        if bvalue:
            row.update(bvalue)
            row["book_source_timestamp_present"] = bvalue.get("book_source_timestamp_raw") is not None
        else:
            row.update({"spread_bps": None, "bid_top10_quote_notional": None,
                        "ask_top10_quote_notional": None, "book_source_timestamp_present": False})
        candidates.append(row)
    frontier_by_asset = []
    for asset in sorted({row["asset"] for row in candidates}):
        valid = [row for row in candidates if row["asset"] == asset and row["candidate_status"] == "EXPLORATORY_ONLY"]
        for row in valid:
            row["dominated_by"] = sorted(other["market_id"] for other in valid
                if other["market_id"] != row["market_id"] and _dominates(other, row))
            row["pareto_frontier_member"] = not row["dominated_by"]
        frontier_by_asset.append({
            "asset": asset, "candidate_count": len(valid),
            "excluded_count": sum(1 for row in candidates if row["asset"] == asset and row["candidate_status"] == "INDETERMINATE"),
            "frontier_market_ids": sorted(row["market_id"] for row in valid if row["pareto_frontier_member"]),
        })
    created = max(_time(quote["created_at_utc"], "quote created_at_utc"),
                  _time(book["created_at_utc"], "book created_at_utc"))
    return {
        "schema_version": OUTPUT_SCHEMA,
        "created_at_utc": created.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "analysis_mode": "exploratory_pareto_snapshot",
        "decision_status": "INDETERMINATE",
        "quote_artifact": {k: quote[k] for k in ("path", "file_sha256", "created_at_utc", "overall_status", "expected_record_count", "actual_record_count")},
        "book_artifact": {k: book[k] for k in ("path", "file_sha256", "created_at_utc", "overall_status", "expected_record_count", "actual_record_count")},
        "objectives": {
            "maximize": ["quote_turnover_24h", "bid_top10_quote_notional", "ask_top10_quote_notional"],
            "minimize": ["spread_bps"], "weights": None, "thresholds_applied": False,
        },
        "frontier_by_asset": frontier_by_asset,
        "candidates": sorted(candidates, key=lambda row: (row["asset"], row["exchange"])),
        "limitations": [
            "Pareto membership is exploratory, not an approved eligibility decision, asset ranking, or investment recommendation.",
            "Freshness remains INDETERMINATE: no approved maximum source lag or snapshot age is applied, and source timestamp semantics differ by venue.",
            "Ticker turnover is a rolling 24-hour window; changes between captures are not interval volume.",
            "Book snapshots are sequential, not synchronized; quote/book capture skew is recorded without an unapproved threshold.",
            "Top-10 notional is visible snapshot depth only, not full-book or guaranteed executable liquidity.",
            "Pionex amount is excluded unless its quote-currency denomination is officially documented; HTTP failures are not converted to zero.",
            "No fees are inferred as account-effective, no recommendation is generated, and no orders are submitted.",
        ],
        "orders_submitted": False, "recommendation_generated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quote-artifact", required=True)
    parser.add_argument("--book-artifact", required=True)
    parser.add_argument("--output", default="artifacts/spot-market-exploratory-pareto.json")
    args = parser.parse_args()
    result = analyze_files(args.quote_artifact, args.book_artifact)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output), "decision_status": result["decision_status"],
        "candidate_count": len(result["candidates"]), "frontier_by_asset": result["frontier_by_asset"],
        "orders_submitted": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
