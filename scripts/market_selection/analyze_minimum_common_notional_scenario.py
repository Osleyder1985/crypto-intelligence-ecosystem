"""Analyze a minimum common cross-venue notional boundary from preserved public symbol filters and depth."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
from typing import Any

try:
    from .analyze_depth_cost_curves import PUBLIC_FEE_REFERENCE
except ImportError:
    from analyze_depth_cost_curves import PUBLIC_FEE_REFERENCE

SCHEMA = "minimum-common-notional-reference-v1"


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        raise ValueError("source record is not HTTP 200 PASS")
    raw = base64.b64decode(record["response_base64"], validate=True)
    if hashlib.sha256(raw).hexdigest() != record.get("response_sha256"):
        raise ValueError("raw response SHA-256 mismatch")
    if len(raw) != record.get("response_bytes"):
        raise ValueError("raw response byte count mismatch")
    parsed = json.loads(raw.decode("utf-8"))
    if parsed != record.get("parsed_json") or not isinstance(parsed, dict):
        raise ValueError("parsed_json does not match preserved raw response")
    return parsed


def _d(value: Any, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} is not a valid decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def _single_record(records: list[dict[str, Any]], market: str, provider: str) -> dict[str, Any]:
    found = [r for r in records if r.get("market_id") == market and r.get("provider") == provider]
    if len(found) != 1:
        raise ValueError(f"expected exactly one {provider} record for {market}; found {len(found)}")
    return found[0]


def _levels(payload: dict[str, Any], venue: str, side: str) -> list[tuple[Decimal, Decimal]]:
    data = payload.get("data") if venue == "pionex" else payload
    if not isinstance(data, dict) or not isinstance(data.get(side), list) or not data[side]:
        raise ValueError(f"{venue} {side} book is missing or empty")
    out = []
    previous = None
    for i, item in enumerate(data[side]):
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"{venue} {side}[{i}] is malformed")
        price, qty = _d(item[0], f"{venue} {side}[{i}] price"), _d(item[1], f"{venue} {side}[{i}] quantity")
        if price <= 0 or qty <= 0:
            raise ValueError(f"{venue} {side}[{i}] must be positive")
        if previous is not None and ((side == "bids" and price > previous) or (side == "asks" and price < previous)):
            raise ValueError(f"{venue} {side} are not ordered best-price-first")
        out.append((price, qty))
        previous = price
    return out


def _fill(levels: list[tuple[Decimal, Decimal]], requested: Decimal, mid: Decimal, side: str, fee_bps: Decimal) -> dict[str, Any]:
    remaining = requested
    filled = Decimal(0)
    notional = Decimal(0)
    for price, available in levels:
        take = min(remaining, available)
        filled += take
        notional += take * price
        remaining -= take
        if remaining == 0:
            break
    if remaining > 0:
        return {
            "status": "INDETERMINATE",
            "requested_base": float(requested),
            "filled_base": float(filled),
            "uncovered_base": float(remaining),
            "vwap": None,
            "quote_notional": float(notional),
            "slippage_bps_vs_mid": None,
            "public_fee_reference_quote": None,
            "net_quote_if_sold": None,
            "fee_reference_bps_per_fill": float(fee_bps),
        }
    vwap = notional / requested
    slippage = ((vwap / mid) - 1) * Decimal(10000) if side == "buy" else (1 - vwap / mid) * Decimal(10000)
    fee = notional * fee_bps / Decimal(10000)
    return {
        "status": "PASS",
        "requested_base": float(requested),
        "filled_base": float(filled),
        "uncovered_base": 0.0,
        "vwap": float(vwap),
        "quote_notional": float(notional),
        "slippage_bps_vs_mid": float(slippage),
        "public_fee_reference_quote": float(fee),
        "net_quote_if_sold": float(notional - fee) if side == "sell" else None,
        "fee_reference_bps_per_fill": float(fee_bps),
    }


def _symbol(payload: dict[str, Any], venue: str, symbol: str) -> dict[str, Any]:
    if venue == "pionex":
        symbols = payload.get("data", {}).get("symbols", [])
        key = "symbol"
    else:
        symbols = payload.get("symbols", [])
        key = "symbol"
    matches = [item for item in symbols if isinstance(item, dict) and item.get(key) == symbol]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {venue} metadata symbol {symbol}; found {len(matches)}")
    return matches[0]


def _binance_constraints(symbol: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
    filters = symbol.get("filters")
    if not isinstance(filters, list):
        raise ValueError("Binance symbol filters are missing")
    by_type = {f.get("filterType"): f for f in filters if isinstance(f, dict)}
    lot = by_type.get("LOT_SIZE")
    notional = by_type.get("NOTIONAL") or by_type.get("MIN_NOTIONAL")
    if not isinstance(lot, dict) or not isinstance(notional, dict):
        raise ValueError("Binance LOT_SIZE and NOTIONAL/MIN_NOTIONAL filters are required")
    min_qty = _d(lot.get("minQty"), "Binance LOT_SIZE.minQty")
    step = _d(lot.get("stepSize"), "Binance LOT_SIZE.stepSize")
    min_notional = _d(notional.get("minNotional"), "Binance minimum notional")
    if step <= 0 or min_notional <= 0:
        raise ValueError("Binance LOT_SIZE step and minimum notional must be positive")
    return min_qty, step, min_notional


def analyze_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != "public-market-capture-batch-v1" or artifact.get("overall_status") != "PASS":
        raise ValueError("input must be a PASS public-market-capture-batch-v1 artifact")
    universe, records = artifact.get("universe"), artifact.get("records")
    if not isinstance(universe, list) or not isinstance(records, list):
        raise ValueError("artifact universe and records must be arrays")
    results = []
    for spec in universe:
        market, bsym = spec.get("pionex_symbol"), spec.get("binance_symbol")
        if not isinstance(market, str) or not isinstance(bsym, str):
            raise ValueError("universe market symbols are missing")
        p_meta_record = _single_record(records, market, "pionex")
        b_meta_record = _single_record(records, market, "binance_exchange_info")
        p_book_record = _single_record(records, market, "pionex_depth")
        b_book_record = _single_record(records, market, "binance_depth")
        p_symbol = _symbol(_payload(p_meta_record), "pionex", market)
        b_symbol = _symbol(_payload(b_meta_record), "binance", bsym)
        p_book, b_book = _payload(p_book_record), _payload(b_book_record)
        p_bids, p_asks = _levels(p_book, "pionex", "bids"), _levels(p_book, "pionex", "asks")
        b_bids, b_asks = _levels(b_book, "binance", "bids"), _levels(b_book, "binance", "asks")
        if p_bids[0][0] >= p_asks[0][0] or b_bids[0][0] >= b_asks[0][0]:
            raise ValueError(f"locked/crossed book for {market}")
        p_mid = (p_bids[0][0] + p_asks[0][0]) / 2
        b_mid = (b_bids[0][0] + b_asks[0][0]) / 2
        p_min_quote = _d(p_symbol.get("minAmount"), "Pionex minAmount")
        p_min_base = _d(p_symbol.get("minTradeSize"), "Pionex minTradeSize")
        b_min_base, b_step, b_min_quote = _binance_constraints(b_symbol)
        p_required_base = max(p_min_base, p_min_quote / min(p_bids[0][0], p_asks[0][0]))
        b_required_base = max(b_min_base, b_min_quote / min(b_bids[0][0], b_asks[0][0]))
        raw_common_base = max(p_required_base, b_required_base)
        common_base = (raw_common_base / b_step).to_integral_value(rounding=ROUND_CEILING) * b_step
        p_buy = _fill(p_asks, common_base, p_mid, "buy", PUBLIC_FEE_REFERENCE["pionex"]["rate_bps_per_fill"])
        p_sell = _fill(p_bids, common_base, p_mid, "sell", PUBLIC_FEE_REFERENCE["pionex"]["rate_bps_per_fill"])
        b_buy = _fill(b_asks, common_base, b_mid, "buy", PUBLIC_FEE_REFERENCE["binance"]["rate_bps_per_fill"])
        b_sell = _fill(b_bids, common_base, b_mid, "sell", PUBLIC_FEE_REFERENCE["binance"]["rate_bps_per_fill"])
        p_valid = common_base >= p_min_base and common_base * p_asks[0][0] >= p_min_quote and common_base * p_bids[0][0] >= p_min_quote
        b_valid = common_base >= b_min_base and common_base % b_step == 0 and common_base * b_asks[0][0] >= b_min_quote and common_base * b_bids[0][0] >= b_min_quote
        for venue, result in (("pionex", p_buy), ("binance", b_buy)):
            if result["status"] != "PASS":
                p_valid = False if venue == "pionex" else p_valid
                b_valid = False if venue == "binance" else b_valid
        p_round_trip = None
        if p_buy["status"] == p_sell["status"] == "PASS":
            p_round_trip = p_buy["quote_notional"] + p_buy["public_fee_reference_quote"] - p_sell["quote_notional"] + p_sell["public_fee_reference_quote"]
        b_round_trip = None
        if b_buy["status"] == b_sell["status"] == "PASS":
            b_round_trip = b_buy["quote_notional"] + b_buy["public_fee_reference_quote"] - b_sell["quote_notional"] + b_sell["public_fee_reference_quote"]
        results.append({
            "market_id": market,
            "binance_symbol": bsym,
            "scenario_type": "minimum_common_quote_notional_boundary",
            "scenario_status": "PASS" if p_valid and b_valid and all(x["status"] == "PASS" for x in (p_buy, p_sell, b_buy, b_sell)) else "INDETERMINATE",
            "common_base_quantity": float(common_base),
            "constraints": {
                "pionex_min_quote_amount": float(p_min_quote),
                "pionex_min_limit_base_quantity": float(p_min_base),
                "binance_min_base_quantity": float(b_min_base),
                "binance_limit_quantity_step": float(b_step),
                "binance_min_quote_notional": float(b_min_quote),
                "pionex_minimums_satisfied": p_valid,
                "binance_minimums_satisfied": b_valid,
            },
            "pionex": {
                "public_fee_reference": {
                    "rate_bps_per_fill": float(PUBLIC_FEE_REFERENCE["pionex"]["rate_bps_per_fill"]),
                    "source": PUBLIC_FEE_REFERENCE["pionex"]["source"],
                    "observed_at_utc": PUBLIC_FEE_REFERENCE["pionex"]["observed_at_utc"],
                    "schedule": PUBLIC_FEE_REFERENCE["pionex"]["schedule"],
                },
                "best_ask_reference_notional": float(common_base * p_asks[0][0]),
                "buy": p_buy, "sell": p_sell,
                "static_snapshot_round_trip_cost_quote": p_round_trip,
                "static_snapshot_round_trip_cost_bps_vs_buy_notional": (p_round_trip / p_buy["quote_notional"] * 10000) if p_round_trip is not None and p_buy["quote_notional"] > 0 else None,
            },
            "binance": {
                "public_fee_reference": {
                    "rate_bps_per_fill": float(PUBLIC_FEE_REFERENCE["binance"]["rate_bps_per_fill"]),
                    "source": PUBLIC_FEE_REFERENCE["binance"]["source"],
                    "observed_at_utc": PUBLIC_FEE_REFERENCE["binance"]["observed_at_utc"],
                    "schedule": PUBLIC_FEE_REFERENCE["binance"]["schedule"],
                },
                "best_ask_reference_notional": float(common_base * b_asks[0][0]),
                "buy": b_buy, "sell": b_sell,
                "static_snapshot_round_trip_cost_quote": b_round_trip,
                "static_snapshot_round_trip_cost_bps_vs_buy_notional": (b_round_trip / b_buy["quote_notional"] * 10000) if b_round_trip is not None and b_buy["quote_notional"] > 0 else None,
            },
            "public_fee_reference_only": True,
            "account_effective_fee_verified": False,
            "orders_submitted": False,
        })
    return {
        "schema_version": SCHEMA,
        "source_created_at_utc": artifact.get("created_at_utc"),
        "decision_status": "INDETERMINATE",
        "results": results,
        "method": "derive a shared base quantity from captured Pionex minimums and Binance LOT_SIZE/NOTIONAL filters; then simulate consuming captured depth",
        "limitations": [
            "This is a boundary scenario derived from public exchange minimums, not a product-approved typical order size.",
            "Pionex exposes minTradeSize and minAmount in public symbol metadata; this capture does not expose a documented quantity step, so only those known lower bounds are checked.",
            "Binance filter applicability can depend on order type and reference/average price; this scenario uses the documented limit-order LOT_SIZE and notional floor as a lower-bound reference.",
            "The buy/sell round trip is a static-snapshot simulation, not a guarantee that both sides remain available over time.",
            "Public per-fill fee schedules are illustrative; account-specific fees, discounts, tax/special commissions and fee-asset rounding are not verified.",
            "A missing or insufficient captured depth makes the scenario INDETERMINATE; no extrapolation or order submission occurs.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze_artifact(json.loads(Path(args.artifact).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": args.output,
        "decision_status": result["decision_status"],
        "scenarios": [{
            "market_id": item["market_id"],
            "scenario_status": item["scenario_status"],
            "common_base_quantity": item["common_base_quantity"],
            "pionex_round_trip_cost_quote": item["pionex"]["static_snapshot_round_trip_cost_quote"],
            "binance_round_trip_cost_quote": item["binance"]["static_snapshot_round_trip_cost_quote"],
        } for item in result["results"]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
