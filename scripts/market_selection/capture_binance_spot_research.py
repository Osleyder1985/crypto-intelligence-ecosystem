"""Capture Binance Spot market identity plus OHLCV and assemble a reproducible report.

Network access is read-only and restricted to documented public market-data endpoints.
This is a technical integration, not an approval of commercial data rights or a forecast.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.market_selection.capture_binance_spot_ohlcv import (
    BASE_URL as KLINES_URL,
    TIMEOUT_SECONDS,
    capture_history,
)
from scripts.market_selection.research_report import build_research_report
from scripts.market_selection.canonical_asset_identity import assess_canonical_asset_identity

EXCHANGE_INFO_URL = "https://data-api.binance.vision/api/v3/exchangeInfo"
PIPELINE_SCHEMA = "crypto-asset-live-capture-report-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read_complete(response) -> bytes:
    """Read to EOF; no local byte ceiling or silent truncation."""
    chunks = []
    while True:
        chunk = response.read(64 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def capture_exchange_info(symbol: str) -> dict:
    """Capture and preserve the full official response for one exact native symbol."""
    url = EXCHANGE_INFO_URL + "?" + urlencode({"symbol": symbol})
    started = utc_now()
    request = Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "crypto-intelligence-ecosystem-research/1.0"},
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", None)
            raw = read_complete(response)
        captured_at = utc_now()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Binance exchangeInfo capture failed: {type(exc).__name__}: {exc}") from exc

    evidence = {
        "url": url,
        "request_started_at_utc": started,
        "captured_at_utc": captured_at,
        "http_status": status,
        "response_bytes": len(raw),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_base64": base64.b64encode(raw).decode("ascii"),
        "capture_status": "PASS" if status == 200 else "FAIL",
    }
    if status != 200:
        raise RuntimeError(f"Binance exchangeInfo returned HTTP {status}; evidence hash: {evidence['response_sha256']}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Binance exchangeInfo returned invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise RuntimeError("Binance exchangeInfo response has no symbols array")
    matches = [item for item in payload["symbols"] if isinstance(item, dict) and item.get("symbol") == symbol]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one exchangeInfo entry for {symbol}, found {len(matches)}")
    item = matches[0]
    if item.get("status") != "TRADING":
        raise ValueError(f"{symbol} is not in TRADING status: {item.get('status')!r}")
    if item.get("isSpotTradingAllowed") is not True:
        raise ValueError(f"{symbol} is not explicitly marked as spot-trading allowed")
    base_asset = item.get("baseAsset")
    quote_asset = item.get("quoteAsset")
    if not isinstance(base_asset, str) or not base_asset.strip():
        raise ValueError("exchangeInfo baseAsset is missing")
    if not isinstance(quote_asset, str) or not quote_asset.strip():
        raise ValueError("exchangeInfo quoteAsset is missing")
    return {
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "symbol_status": item["status"],
        "is_spot_trading_allowed": item["isSpotTradingAllowed"],
        "base_asset_precision": item.get("baseAssetPrecision"),
        "quote_asset_precision": item.get("quoteAssetPrecision"),
        "filters": item.get("filters", []),
        "permissions": item.get("permissions"),
        "permission_sets": item.get("permissionSets"),
        "captured_exchange_info": evidence,
    }


def capture_and_build_report(
    *,
    symbol: str,
    interval: str,
    start_time_ms: int,
    end_time_ms_exclusive: int,
    config: dict,
    base_asset_ticker: str,
    identity_evidence: dict | None = None,
) -> tuple[dict, dict]:
    """Capture official exchange metadata and candles, then build report from exact artifact bytes."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("symbol must be non-empty")
    metadata = capture_exchange_info(symbol)
    artifact = capture_history(symbol, interval, start_time_ms, end_time_ms_exclusive)
    artifact["market"].update({
        "base_asset": metadata["base_asset"],
        "quote_asset": metadata["quote_asset"],
        "symbol_status_at_capture": metadata["symbol_status"],
        "is_spot_trading_allowed_at_capture": metadata["is_spot_trading_allowed"],
    })
    artifact["market_identity_evidence"] = metadata["captured_exchange_info"]
    artifact["pipeline"] = {
        "schema_version": PIPELINE_SCHEMA,
        "metadata_capture_status": metadata["captured_exchange_info"]["capture_status"],
        "metadata_sha256": metadata["captured_exchange_info"]["response_sha256"],
        "market_identity_basis": "BINANCE_EXCHANGE_INFO_BASE_ASSET",
        "canonical_cross_provider_asset_id": "NOT_RESOLVED",
        "license_review_status": "REQUIRES_PRODUCT_SPECIFIC_REVIEW",
    }
    capture_raw = (
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    report = build_research_report(artifact, config, base_asset_ticker, capture_raw)
    # The exchange metadata verifies only the pair's base ticker. It does not prove
    # a globally unique token identity across chains, wrapped assets, or providers.
    report["asset_identity_status"] = "INDETERMINATE"
    report["market_base_asset_mapping_status"] = "VERIFIED"
    report["canonical_asset_identity_status"] = "NOT_RESOLVED"
    report["canonical_asset_identity"] = {
        "identity_status": "NOT_RESOLVED",
        "canonical_asset_id": None,
        "evidence_status": "NOT_PROVIDED",
        "reason_codes": ["CANONICAL_ID_COMPONENTS_MISSING"],
        "ticker_used_as_identity": False,
    }
    report["asset_identity_scope"] = "Binance pair baseAsset ticker only; global cross-provider token identity is unresolved."
    if identity_evidence is not None:
        if not isinstance(identity_evidence, dict):
            raise ValueError("identity_evidence must be a JSON object")
        evidence_record = dict(identity_evidence)
        market_mapping = evidence_record.pop("market_mapping", None)
        if not isinstance(market_mapping, dict):
            raise ValueError("identity_evidence.market_mapping must explicitly bind identity evidence to captured market metadata")
        expected_mapping = {
            "exchange": "BINANCE",
            "symbol": symbol,
            "base_asset_ticker": metadata["base_asset"],
            "exchange_info_sha256": metadata["captured_exchange_info"]["response_sha256"],
        }
        for key, expected in expected_mapping.items():
            if market_mapping.get(key) != expected:
                raise ValueError(f"identity_evidence.market_mapping.{key} does not match captured Binance metadata")
        if str(evidence_record.get("ticker", "")).strip().upper() != metadata["base_asset"].upper():
            raise ValueError("identity_evidence.ticker must match captured Binance baseAsset ticker")
        assessment = assess_canonical_asset_identity(evidence_record)
        report["canonical_asset_identity"] = assessment
        report["canonical_asset_identity_status"] = assessment["identity_status"]
        report["canonical_asset_identity_evidence_status"] = "STRUCTURE_VALIDATED_NOT_AUTHENTICATED"
        report["canonical_asset_identity_market_mapping_status"] = "MATCHED_TO_CAPTURED_BINANCE_METADATA"
        # Complete coordinates are not proof that the provider assertion is true.
        # Keep product-level identity INDETERMINATE until source authenticity and
        # authoritative token/chain mapping are independently verified.
        report["asset_identity_status"] = "INDETERMINATE"
        report["asset_identity_scope"] = "Explicit canonical coordinates supplied; source authenticity and authoritative mapping remain unverified."
    report["report_status"] = "PARTIAL"
    report["data_quality"]["status"] = "INCOMPLETE_OR_UNVERIFIED"
    report["data_quality"]["dimensions"]["canonical_asset_identity"] = report["canonical_asset_identity_status"]
    for horizon in report["horizons"].values():
        if "CANONICAL_ASSET_ID_NOT_RESOLVED" not in horizon["reason_codes"]:
            horizon["reason_codes"].append("CANONICAL_ASSET_ID_NOT_RESOLVED")
    report["pipeline"] = {
        "schema_version": PIPELINE_SCHEMA,
        "capture_artifact_sha256": hashlib.sha256(capture_raw).hexdigest(),
        "capture_artifact_bytes": len(capture_raw),
        "exchange_info_sha256": metadata["captured_exchange_info"]["response_sha256"],
        "klines_source": KLINES_URL,
        "market_identity_basis": "BINANCE_EXCHANGE_INFO_BASE_ASSET",
        "canonical_cross_provider_asset_id": "NOT_RESOLVED",
        "license_review_status": "REQUIRES_PRODUCT_SPECIFIC_REVIEW",
        "network_requests_made": True,
        "orders_submitted": False,
    }
    report["network_requests_made"] = True
    report["orders_submitted"] = False
    report["limitations"] = list(report.get("limitations", [])) + [
        "This pipeline resolves the base ticker from Binance exchangeInfo; it does not establish a globally unique token identity across chains, wrapped assets, or other providers.",
        "Public endpoint documentation establishes technical availability, not a blanket commercial licence. Review applicable terms before commercial persistence, display, export, or redistribution.",
        "The pipeline performs read-only GET requests only. It never submits orders or uses trading credentials.",
    ]
    return {"artifact": artifact, "raw_bytes": capture_raw}, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True, help="Exact native Binance Spot symbol, e.g. BTCUSDT; no ticker guessing")
    parser.add_argument("--base-asset-ticker", required=True, help="Must equal exchangeInfo baseAsset ticker; not a global token identifier")
    parser.add_argument("--interval", required=True)
    parser.add_argument("--start-time-ms", required=True, type=int, help="Inclusive UTC candle boundary, Unix milliseconds")
    parser.add_argument("--end-time-ms", required=True, type=int, help="Exclusive UTC candle boundary, Unix milliseconds")
    parser.add_argument("--config", required=True, type=Path, help="Explicit descriptive-analysis configuration JSON")
    parser.add_argument("--identity-evidence", type=Path, help="Optional JSON with explicit chain/asset coordinates, source evidence and market_mapping bound to captured Binance metadata")
    parser.add_argument("--capture-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    identity_evidence = json.loads(args.identity_evidence.read_text(encoding="utf-8")) if args.identity_evidence else None
    captured, report = capture_and_build_report(
        symbol=args.symbol,
        interval=args.interval,
        start_time_ms=args.start_time_ms,
        end_time_ms_exclusive=args.end_time_ms,
        config=config,
        base_asset_ticker=args.base_asset_ticker,
        identity_evidence=identity_evidence,
    )
    args.capture_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.capture_output.write_bytes(captured["raw_bytes"])
    args.report_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "capture_artifact": str(args.capture_output),
        "capture_sha256": hashlib.sha256(captured["raw_bytes"]).hexdigest(),
        "report_artifact": str(args.report_output),
        "report_status": report["report_status"],
        "decision_status": report["decision_status"],
        "asset_identity_status": report["asset_identity_status"],
        "market_base_asset_mapping_status": report["market_base_asset_mapping_status"],
        "canonical_asset_identity_status": report["canonical_asset_identity_status"],
        "canonical_asset_identity_evidence_status": report.get("canonical_asset_identity_evidence_status", "NOT_PROVIDED"),
        "horizons": {key: value["status"] for key, value in report["horizons"].items()},
        "orders_submitted": False,
    }, ensure_ascii=False, indent=2))
    return 0 if captured["artifact"]["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
