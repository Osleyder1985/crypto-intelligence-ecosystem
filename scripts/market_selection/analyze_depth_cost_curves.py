"""Build deterministic, no-fixed-order-size execution cost curves from preserved public depth snapshots."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SCHEMA = "public-depth-cost-curves-v1"


def _verified_payload(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        raise ValueError("depth record is not HTTP 200 PASS")
    try:
        raw = base64.b64decode(record["response_base64"], validate=True)
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("depth response bytes are missing or invalid Base64") from exc
    if hashlib.sha256(raw).hexdigest() != record.get("response_sha256"):
        raise ValueError("depth response SHA-256 mismatch")
    if len(raw) != record.get("response_bytes"):
        raise ValueError("depth response byte count mismatch")
    parsed = json.loads(raw.decode("utf-8"))
    if parsed != record.get("parsed_json") or not isinstance(parsed, dict):
        raise ValueError("parsed depth JSON does not match preserved response bytes")
    return parsed


def _levels(raw: Any, side: str) -> list[tuple[Decimal, Decimal]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{side} side is empty")
    out: list[tuple[Decimal, Decimal]] = []
    seen: set[Decimal] = set()
    previous: Decimal | None = None
    for i, item in enumerate(raw):
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"{side}[{i}] is not a [price, quantity] pair")
        try:
            price, quantity = Decimal(str(item[0])), Decimal(str(item[1]))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{side}[{i}] contains an invalid number") from exc
        if not price.is_finite() or not quantity.is_finite() or price <= 0 or quantity <= 0:
            raise ValueError(f"{side}[{i}] has non-finite or non-positive price/quantity")
        if price in seen:
            raise ValueError(f"{side} contains duplicate price levels")
        if previous is not None and ((side == "bids" and price > previous) or (side == "asks" and price < previous)):
            raise ValueError(f"{side} is not ordered best-price-first")
        seen.add(price)
        previous = price
        out.append((price, quantity))
    return out


def _curve(levels: list[tuple[Decimal, Decimal]], mid: Decimal, side: str) -> list[dict[str, float | int]]:
    cumulative_base = Decimal(0)
    cumulative_quote = Decimal(0)
    curve = []
    for index, (price, quantity) in enumerate(levels, start=1):
        cumulative_base += quantity
        cumulative_quote += price * quantity
        vwap = cumulative_quote / cumulative_base
        if side == "buy":
            slippage_bps = (vwap / mid - Decimal(1)) * Decimal(10000)
        else:
            slippage_bps = (Decimal(1) - vwap / mid) * Decimal(10000)
        curve.append({
            "level": index,
            "cumulative_base": float(cumulative_base),
            "cumulative_quote": float(cumulative_quote),
            "vwap": float(vwap),
            "slippage_bps_vs_mid": float(slippage_bps),
        })
    return curve


def analyze_depth_record(record: dict[str, Any], market_id: str, venue: str) -> dict[str, Any]:
    payload = _verified_payload(record)
    data = payload.get("data") if venue == "pionex" else payload
    if not isinstance(data, dict):
        raise ValueError(f"{venue} depth payload has no order-book object")
    bids, asks = _levels(data.get("bids"), "bids"), _levels(data.get("asks"), "asks")
    best_bid, best_ask = bids[0][0], asks[0][0]
    if best_bid >= best_ask:
        raise ValueError("book is locked or crossed")
    mid = (best_bid + best_ask) / Decimal(2)
    spread_bps = (best_ask - best_bid) / mid * Decimal(10000)
    return {
        "market_id": market_id,
        "venue": venue,
        "captured_at_utc": record.get("captured_at_utc"),
        "source_response_at_utc": record.get("source_response_at_utc"),
        "source_market_update_at_utc": record.get("source_market_update_at_utc"),
        "levels_returned": {"bids": len(bids), "asks": len(asks)},
        "best_bid": float(best_bid),
        "best_ask": float(best_ask),
        "mid": float(mid),
        "spread_bps": float(spread_bps),
        "visible_depth_quote": {
            "bids": float(sum((price * qty for price, qty in bids), Decimal(0))),
            "asks": float(sum((price * qty for price, qty in asks), Decimal(0))),
        },
        "execution_cost_curve": {
            "buy_consuming_asks": _curve(asks, mid, "buy"),
            "sell_consuming_bids": _curve(bids, mid, "sell"),
        },
        "fee_cost_included": False,
        "order_size_selected": False,
    }


def analyze_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(artifact, dict) or artifact.get("schema_version") != "public-market-capture-batch-v1" or artifact.get("overall_status") != "PASS":
        raise ValueError("input must be a PASS public-market-capture-batch-v1 artifact")
    universe, records = artifact.get("universe"), artifact.get("records")
    if not isinstance(universe, list) or not isinstance(records, list):
        raise ValueError("artifact universe and records must be arrays")
    books = []
    for spec in universe:
        market = spec.get("pionex_symbol") if isinstance(spec, dict) else None
        if not isinstance(market, str) or not market:
            raise ValueError("universe entry is missing pionex_symbol")
        for provider, venue in (("pionex_depth", "pionex"), ("binance_depth", "binance")):
            matches = [r for r in records if r.get("market_id") == market and r.get("provider") == provider]
            if len(matches) != 1:
                raise ValueError(f"expected exactly one {provider} record for {market}; found {len(matches)}")
            books.append(analyze_depth_record(matches[0], market, venue))
    return {
        "schema_version": SCHEMA,
        "source_schema_version": artifact["schema_version"],
        "source_created_at_utc": artifact.get("created_at_utc"),
        "method": "cumulative VWAP/slippage at every returned order-book level; no fixed order size and no fee assumptions",
        "decision_status": "INDETERMINATE",
        "books": books,
        "limitations": [
            "Each curve is based only on the levels returned by one point-in-time snapshot.",
            "Binance and Pionex snapshots are captured sequentially and are not asserted to be synchronized.",
            "Slippage curves exclude fees and cannot establish account-specific total execution cost.",
            "A curve is descriptive; the product has not approved a single order size or acceptance threshold.",
            "No orders are submitted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    artifact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    result = analyze_artifact(artifact)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": args.output,
        "decision_status": result["decision_status"],
        "books": [{
            "market_id": book["market_id"], "venue": book["venue"],
            "bid_levels": book["levels_returned"]["bids"],
            "ask_levels": book["levels_returned"]["asks"],
            "spread_bps": book["spread_bps"],
            "visible_depth_quote": book["visible_depth_quote"],
        } for book in result["books"]],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
