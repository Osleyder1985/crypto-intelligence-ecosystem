"""Compare causal Spot support/resistance zones across supplied timeframes.

This wrapper preserves each timeframe's independent analysis. It does not merge
levels across timeframes or infer that a level will hold.
"""
from __future__ import annotations

import argparse
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from scripts.market_selection.analyze_support_resistance import analyze_support_resistance
except ModuleNotFoundError:
    from analyze_support_resistance import analyze_support_resistance

INPUT_SCHEMA = "multi-timeframe-support-resistance-input-v1"
OUTPUT_SCHEMA = "multi-timeframe-support-resistance-events-v1"


def _within_price_tolerance(left: Decimal, right: Decimal, tolerance_bps: Decimal) -> bool:
    """Compare two positive prices using a symmetric midpoint denominator."""
    midpoint = (left + right) / Decimal(2)
    if midpoint <= 0:
        return False
    return abs(left - right) / midpoint * Decimal(10_000) <= tolerance_bps


def analyze_multi_timeframe_support_resistance(
    artifacts: list[dict[str, Any]],
    *,
    pivot_left: int,
    pivot_right: int,
    tolerance_bps: float,
    confluence_tolerance_bps: float | None = None,
) -> dict[str, Any]:
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("artifacts must be a non-empty list")
    if confluence_tolerance_bps is not None and (
        isinstance(confluence_tolerance_bps, bool)
        or not isinstance(confluence_tolerance_bps, (int, float))
        or not math.isfinite(confluence_tolerance_bps)
        or not 0 <= confluence_tolerance_bps <= 10_000
    ):
        raise ValueError("confluence_tolerance_bps must be finite and from 0 to 10000")

    analyses = []
    identity = None
    intervals = set()
    for index, artifact in enumerate(artifacts):
        result = analyze_support_resistance(
            artifact, pivot_left=pivot_left, pivot_right=pivot_right,
            tolerance_bps=tolerance_bps,
        )
        market = result["market"]
        current_identity = (market["exchange"], market["market_type"], market["symbol_native"])
        if identity is None:
            identity = current_identity
        elif current_identity != identity:
            raise ValueError("all artifacts must refer to the same exchange, market type, and native symbol")
        interval = market["interval"]
        if interval in intervals:
            raise ValueError(f"duplicate timeframe interval: {interval}")
        intervals.add(interval)
        analyses.append({
            "timeframe_index": index,
            "interval": interval,
            "data_quality_status": result["data_quality_status"],
            "source_integrity_status": result["source_integrity_status"],
            "sample": result["sample"],
            "method": result["method"],
            "zones": result["zones"],
            "events": result["events"],
            "gaps": result["gaps"],
        })

    analyses.sort(key=lambda item: item["interval"])
    confluence_groups = []
    if confluence_tolerance_bps is not None:
        flattened = []
        for analysis in analyses:
            for zone in analysis["zones"]:
                flattened.append({
                    "interval": analysis["interval"],
                    "zone_id": zone["zone_id"],
                    "kind": zone["kind"],
                    "center_price": Decimal(zone["center_price"]),
                    "lower_bound_price": Decimal(zone["lower_bound_price"]),
                    "upper_bound_price": Decimal(zone["upper_bound_price"]),
                })
        seen_groups = set()
        tolerance = Decimal(str(confluence_tolerance_bps))
        for seed in flattened:
            selected = [seed]
            for interval in sorted({item["interval"] for item in flattened if item["interval"] != seed["interval"]}):
                candidates = [
                    item for item in flattened
                    if item["interval"] == interval and item["kind"] == seed["kind"]
                    and _within_price_tolerance(item["center_price"], seed["center_price"], tolerance)
                ]
                if candidates:
                    selected.append(min(candidates, key=lambda item: (
                        abs(item["center_price"] - seed["center_price"]), item["zone_id"]
                    )))
            if len(selected) < 2:
                continue
            refs = tuple(sorted((item["interval"], item["zone_id"]) for item in selected))
            if refs in seen_groups:
                continue
            seen_groups.add(refs)
            centers = [item["center_price"] for item in selected]
            lows = [item["lower_bound_price"] for item in selected]
            highs = [item["upper_bound_price"] for item in selected]
            confluence_groups.append({
                "kind": seed["kind"],
                "zone_refs": [{"interval": item["interval"], "zone_id": item["zone_id"]} for item in selected],
                "timeframe_count": len({item["interval"] for item in selected}),
                "center_price_min": str(min(centers)),
                "center_price_max": str(max(centers)),
                "observed_lower_bound_min": str(min(lows)),
                "observed_upper_bound_max": str(max(highs)),
                "matching_rule": "same zone kind and symmetric midpoint-relative center-price distance within explicit bps tolerance",
            })
        confluence_groups.sort(key=lambda item: (
            item["kind"], Decimal(item["center_price_min"]), item["timeframe_count"]
        ))
    overall_quality = (
        "COMPLETE" if all(item["data_quality_status"] == "COMPLETE" for item in analyses)
        else "INCOMPLETE" if any(item["data_quality_status"] == "INCOMPLETE" for item in analyses)
        else "INSUFFICIENT"
    )
    return {
        "schema_version": OUTPUT_SCHEMA,
        "analysis_status": "DESCRIPTIVE_ONLY",
        "data_quality_status": overall_quality,
        "market": {
            "exchange": identity[0],
            "market_type": identity[1],
            "symbol_native": identity[2],
        },
        "timeframe_count": len(analyses),
        "timeframes": analyses,
        "cross_timeframe_confluence": "COMPUTED_BY_EXPLICIT_PRICE_TOLERANCE" if confluence_tolerance_bps is not None else "NOT_COMPUTED",
        "confluence_tolerance_bps": confluence_tolerance_bps,
        "confluence_groups": confluence_groups,
        "limitations": [
            "Each timeframe is analyzed independently with its own closed candles and confirmation timestamps.",
            "Zone prices and event counts are not combined across timeframes; cross-timeframe confluence is not computed.",
            "Different timeframe inputs may cover different periods; compare coverage before interpreting differences.",
            "A zone is a descriptive OHLCV heuristic, not proof of resting orders, guaranteed reaction, or an investment recommendation.",
            "Each input must pass the existing provider-use authorization and source-integrity checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file containing artifacts array")
    parser.add_argument("--pivot-left", type=int, required=True)
    parser.add_argument("--pivot-right", type=int, required=True)
    parser.add_argument("--tolerance-bps", type=float, required=True)
    parser.add_argument("--confluence-tolerance-bps", type=float, help="Optional explicit center-price tolerance for same-kind zones across distinct timeframes, in bps")
    parser.add_argument("--output", default="artifacts/multi-timeframe-support-resistance.json")
    args = parser.parse_args()
    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    result = analyze_multi_timeframe_support_resistance(
        source.get("artifacts"), pivot_left=args.pivot_left,
        pivot_right=args.pivot_right, tolerance_bps=args.tolerance_bps,
        confluence_tolerance_bps=args.confluence_tolerance_bps,
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(path), "analysis_status": result["analysis_status"],
        "data_quality_status": result["data_quality_status"],
        "market": result["market"], "timeframe_count": result["timeframe_count"],
        "cross_timeframe_confluence": result["cross_timeframe_confluence"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
