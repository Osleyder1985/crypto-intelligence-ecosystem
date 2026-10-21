"""Offline evaluator for preserved multi-pair public market captures."""
from __future__ import annotations
import argparse, base64, hashlib, json, math
from pathlib import Path
from typing import Any
try:
    from .selector import depth_quote, estimate_slippage_bps, spread_bps
except ImportError:  # Support direct CLI execution from this directory.
    from selector import depth_quote, estimate_slippage_bps, spread_bps

SCHEMA = "public-market-batch-evaluation-v1"
PROVIDERS = ("pionex", "binance_exchange_info", "binance_depth")

def _payload(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("capture_status") != "PASS" or record.get("http_status") != 200:
        raise ValueError("source record is not HTTP 200 PASS")
    raw = base64.b64decode(record["response_base64"], validate=True)
    if hashlib.sha256(raw).hexdigest() != record.get("response_sha256"):
        raise ValueError("raw response SHA-256 mismatch")
    if isinstance(record.get("response_bytes"), bool) or len(raw) != record.get("response_bytes"):
        raise ValueError("raw response byte count mismatch")
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict) or parsed != record.get("parsed_json"):
        raise ValueError("parsed_json does not match preserved raw bytes")
    return parsed

def _one(records, market, provider):
    found = [r for r in records if r.get("market_id") == market and r.get("provider") == provider]
    if len(found) != 1:
        raise ValueError(f"expected exactly one {provider} record for {market}; found {len(found)}")
    return _payload(found[0])

def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

def evaluate_batch(artifact: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = {} if config is None else config
    if not isinstance(artifact, dict) or artifact.get("schema_version") != "public-market-capture-batch-v1":
        raise ValueError("unsupported batch artifact schema")
    universe, records = artifact.get("universe"), artifact.get("records")
    if artifact.get("overall_status") != "PASS" or not isinstance(universe, list) or not universe or not isinstance(records, list):
        raise ValueError("batch artifact must be PASS with non-empty universe and records")
    results = []
    seen_market_ids, seen_pionex_symbols, seen_binance_symbols = set(), set(), set()
    for spec in universe:
        if not isinstance(spec, dict):
            raise ValueError("universe entries must be objects")
        market, bsym = spec.get("pionex_symbol"), spec.get("binance_symbol")
        base, quote = spec.get("base_asset"), spec.get("quote_asset")
        if not all(isinstance(x, str) and x for x in (market, bsym, base, quote)):
            raise ValueError("market symbols and base/quote must be non-empty strings")
        if market in seen_market_ids:
            raise ValueError(f"duplicate market_id in universe: {market}")
        if market in seen_pionex_symbols:
            raise ValueError(f"duplicate Pionex symbol in universe: {market}")
        if bsym in seen_binance_symbols:
            raise ValueError(f"duplicate Binance symbol in universe: {bsym}")
        seen_market_ids.add(market)
        seen_pionex_symbols.add(market)
        seen_binance_symbols.add(bsym)
        pionex = _one(records, market, "pionex")
        info = _one(records, market, "binance_exchange_info")
        depth = _one(records, market, "binance_depth")
        status = {"capture_integrity":"PASS", "pionex_spot_availability":"INDETERMINATE",
                  "binance_spot_market":"INDETERMINATE", "spread":"NOT_RUN", "depth":"NOT_RUN",
                  "slippage":"NOT_RUN", "source_freshness":"INDETERMINATE", "fees":"INDETERMINATE"}
        metrics, reasons = {}, [
            "Source-event freshness is INDETERMINATE: the captured Binance depth payload has no source event timestamp; capture time is not a substitute.",
            "Trading fees and total execution cost are INDETERMINATE: no verified account-applicable official fee schedule is included in this artifact.",
        ]
        pdata = pionex.get("data")
        syms = pdata.get("symbols") if isinstance(pdata, dict) else None
        matches = [s for s in syms if isinstance(s, dict) and s.get("symbol") == market] if isinstance(syms, list) else []
        if pionex.get("result") is True and len(matches) == 1:
            s = matches[0]
            p_base, p_quote, p_type, p_enable = (
                s.get("baseCurrency"), s.get("quoteCurrency"), s.get("type"), s.get("enable")
            )
            if not all(isinstance(v, str) and v for v in (p_base, p_quote, p_type)) or not isinstance(p_enable, bool):
                status["pionex_spot_availability"] = "INDETERMINATE"
                reasons.append("Pionex identity/type/enable metadata is missing or invalid")
            elif p_type != "SPOT" or p_enable is False:
                status["pionex_spot_availability"] = "FAIL"
                reasons.append("Pionex market is not enabled spot")
            elif p_base != base or p_quote != quote:
                status["pionex_spot_availability"] = "FAIL"
                reasons.append("Pionex baseCurrency/quoteCurrency do not match the declared market identity")
            else:
                status["pionex_spot_availability"] = "PASS"
        else:
            status["pionex_spot_availability"] = "FAIL" if not matches else "INDETERMINATE"
            reasons.append("Pionex did not confirm exactly one matching symbol")
        bsymbols = info.get("symbols")
        bmatches = [s for s in bsymbols if isinstance(s, dict) and s.get("symbol") == bsym] if isinstance(bsymbols, list) else []
        if len(bmatches) == 1:
            s = bmatches[0]
            b_base, b_quote = s.get("baseAsset"), s.get("quoteAsset")
            if not all(isinstance(v, str) and v for v in (b_base, b_quote)):
                status["binance_spot_market"] = "INDETERMINATE"
                reasons.append("Binance baseAsset/quoteAsset metadata is missing or invalid")
            elif b_base != base or b_quote != quote:
                status["binance_spot_market"] = "FAIL"
                reasons.append("Binance baseAsset/quoteAsset do not match the declared market identity")
            elif not isinstance(s.get("status"), str) or not s.get("status") or not isinstance(s.get("isSpotTradingAllowed"), bool):
                status["binance_spot_market"] = "INDETERMINATE"
                reasons.append("Binance status/spot permission metadata is missing or invalid")
            elif s.get("status") != "TRADING" or s.get("isSpotTradingAllowed") is False:
                status["binance_spot_market"] = "FAIL"
                reasons.append("Binance market is not trading or spot trading is not allowed")
            else:
                status["binance_spot_market"] = "PASS"
        else:
            status["binance_spot_market"] = "FAIL" if not bmatches else "INDETERMINATE"
            reasons.append("Binance did not return exactly one matching symbol")
        try:
            def levels(raw, name):
                if not isinstance(raw, list) or not raw: raise ValueError(f"{name} side is empty")
                out=[]
                seen_prices=set()
                previous=None
                for item in raw:
                    if not isinstance(item, list) or len(item) != 2: raise ValueError("malformed book level")
                    price, qty=float(item[0]),float(item[1])
                    if not math.isfinite(price) or not math.isfinite(qty) or price<=0 or qty<=0: raise ValueError("invalid book level")
                    if price in seen_prices: raise ValueError(f"{name} side contains duplicate price levels")
                    if previous is not None and ((name == "bids" and price > previous) or (name == "asks" and price < previous)):
                        raise ValueError(f"{name} side is not ordered best-price-first")
                    seen_prices.add(price)
                    previous=price
                    out.append({"price":price,"quantity":qty})
                return out
            bids, asks = levels(depth.get("bids"), "bids"), levels(depth.get("asks"), "asks")
            bid, ask = bids[0]["price"], asks[0]["price"]
            if bid == ask: raise ValueError("book is locked: best bid equals best ask")
            if bid > ask: raise ValueError("book is crossed: best bid exceeds best ask")
            mid=(bid+ask)/2
            spr=spread_bps(bid, ask)
            metrics.update(best_bid=bid,best_ask=ask,mid=mid,spread_bps=spr,bid_levels=len(bids),ask_levels=len(asks))
            if _num(config.get("max_spread_bps")) and config["max_spread_bps"]>=0:
                status["spread"]="PASS" if spr<=config["max_spread_bps"] else "FAIL"
            if _num(config.get("depth_band_bps")) and config["depth_band_bps"]>=0:
                db=depth_quote(bids,mid,config["depth_band_bps"],"bids")
                da=depth_quote(asks,mid,config["depth_band_bps"],"asks")
                metrics.update(depth_band_bps=config["depth_band_bps"],depth_bid_quote=db,depth_ask_quote=da,min_side_depth_quote=min(db,da))
                minimum=config.get("min_depth_quote")
                status["depth"]="PASS" if _num(minimum) and minimum>0 and min(db,da)>=minimum else ("FAIL" if _num(minimum) and minimum>0 else "INDETERMINATE")
            size=config.get("order_size_base")
            if _num(size) and size>0:
                buy=estimate_slippage_bps(asks,mid,size,"asks"); sell=estimate_slippage_bps(bids,mid,size,"bids")
                metrics.update(buy_execution=buy,sell_execution=sell)
                maximum=config.get("max_slippage_bps")
                if buy["slippage_bps"] is None or sell["slippage_bps"] is None: status["slippage"]="INDETERMINATE"
                elif _num(maximum) and maximum>=0: status["slippage"]="PASS" if max(buy["slippage_bps"],sell["slippage_bps"])<=maximum else "FAIL"
                else: status["slippage"]="INDETERMINATE"
        except (ValueError, TypeError, IndexError, KeyError) as exc:
            status["spread"] = "INDETERMINATE"
            status["depth"] = "INDETERMINATE"
            status["slippage"] = "INDETERMINATE"
            reasons.append(f"book metrics unavailable: {exc}")
        results.append({"market_id":market,"binance_symbol":bsym,"dimension_status":status,"metrics":metrics,"reasons":reasons,"decision_status":"INDETERMINATE"})
    return {"schema_version":SCHEMA,"source_schema_version":artifact["schema_version"],
            "source_created_at_utc":artifact.get("created_at_utc"),"config":config,"config_approved":False,
            "markets_evaluated":len(results),"markets":results,"decision_status":"INDETERMINATE",
            "orders_submitted":False,"network_requests_made":False,
            "limitations":["Snapshot metrics only; no execution guarantee.","Depth is limited to captured levels.",
                           "Source freshness and fees remain INDETERMINATE.","PASS applies only to a named dimension and supplied snapshot/configuration."]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact",required=True); parser.add_argument("--config"); parser.add_argument("--output",required=True)
    args=parser.parse_args()
    artifact=json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    config=json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {}
    result=evaluate_batch(artifact,config)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"markets_evaluated":result["markets_evaluated"],"decision_status":result["decision_status"],
      "markets":[{"market_id":m["market_id"],"dimension_status":m["dimension_status"],"metrics":m["metrics"]} for m in result["markets"]],
      "orders_submitted":False,"network_requests_made":False},indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
