"""Compare causal Spot support/resistance zones across supplied timeframes.

This wrapper preserves each timeframe's independent analysis. It does not merge
levels across timeframes or infer that a level will hold.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.market_selection.analyze_support_resistance import analyze_support_resistance
except ModuleNotFoundError:
    from analyze_support_resistance import analyze_support_resistance

INPUT_SCHEMA = "multi-timeframe-support-resistance-input-v1"
OUTPUT_SCHEMA = "multi-timeframe-support-resistance-events-v1"


def analyze_multi_timeframe_support_resistance(
    artifacts: list[dict[str, Any]],
    *,
    pivot_left: int,
    pivot_right: int,
    tolerance_bps: float,
) -> dict[str, Any]:
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("artifacts must be a non-empty list")

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
        "cross_timeframe_confluence": "NOT_COMPUTED",
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
    parser.add_argument("--output", default="artifacts/multi-timeframe-support-resistance.json")
    args = parser.parse_args()
    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("schema_version") != INPUT_SCHEMA:
        raise ValueError(f"expected schema_version {INPUT_SCHEMA}")
    result = analyze_multi_timeframe_support_resistance(
        source.get("artifacts"), pivot_left=args.pivot_left,
        pivot_right=args.pivot_right, tolerance_bps=args.tolerance_bps,
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
