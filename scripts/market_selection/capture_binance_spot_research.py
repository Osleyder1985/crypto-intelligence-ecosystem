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
from urllib.request import Request, urlopen

from scripts.market_selection.capture_binance_spot_ohlcv import (
    BASE_URL as KLINES_URL,
    TIMEOUT_SECONDS,
    capture_history,
)
from scripts.market_selection.research_report import build_research_report
from scripts.market_selection.provider_license_gate import evaluate_provider_use, SUPPORTED_USE_CASES
from scripts.market_selection.resolve_binance_spot_market_candidates import resolve_spot_market_candidates

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


def capture_exchange_info(
    symbol: str | None = None,
    *,
    base_asset_ticker: str | None = None,
    quote_asset: str | None = None,
    use_case: str = "internal_analysis",
    authorization_record: dict | None = None,
) -> dict:
    """Capture full exchangeInfo and resolve exactly one eligible Spot market."""
    if (symbol is None) == (base_asset_ticker is None):
        raise ValueError("provide exactly one of symbol or base_asset_ticker")
    if symbol is not None:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must be non-empty")
    if base_asset_ticker is not None:
        base_asset_ticker = base_asset_ticker.strip().upper()
        if not base_asset_ticker:
            raise ValueError("base_asset_ticker must be non-empty")
    assessment = evaluate_provider_use("binance_spot_market_data", use_case, authorization_record)
    if assessment["decision"] != "ALLOW":
        raise PermissionError("Binance provider use blocked before exchangeInfo request: " + ";".join(assessment["reason_codes"]))
    # Preserve the full exchangeInfo universe. No local response-size ceiling or server-side symbol filter.
    url = EXCHANGE_INFO_URL
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
        "provider_use_assessment": assessment,
    }
    if status != 200:
        raise RuntimeError(f"Binance exchangeInfo returned HTTP {status}; evidence hash: {evidence['response_sha256']}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Binance exchangeInfo returned invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise RuntimeError("Binance exchangeInfo response has no symbols array")

    if symbol is not None:
        resolution = resolve_spot_market_candidates(payload, symbol, identifier_type="native_symbol")
    else:
        resolution = resolve_spot_market_candidates(
            payload, base_asset_ticker, identifier_type="base_asset", quote_asset=quote_asset
        )
    if resolution["resolution_status"] != "UNIQUE_MARKET":
        candidates = [item["symbol_native"] for item in resolution["candidates"]]
        raise ValueError(
            f"market resolution {resolution['resolution_status']} for "
            f"{symbol if symbol is not None else base_asset_ticker}; candidates={candidates}"
        )
    selected_symbol = resolution["selected_market"]["symbol_native"]
    matches = [
        item for item in payload["symbols"]
        if isinstance(item, dict) and item.get("symbol") == selected_symbol
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one exchangeInfo entry for {selected_symbol}, found {len(matches)}")
    item = matches[0]
    base_asset = item.get("baseAsset")
    quote = item.get("quoteAsset")
    if not isinstance(base_asset, str) or not base_asset.strip():
        raise ValueError("exchangeInfo baseAsset is missing")
    if not isinstance(quote, str) or not quote.strip():
        raise ValueError("exchangeInfo quoteAsset is missing")
    return {
        "symbol_native": selected_symbol,
        "base_asset": base_asset,
        "quote_asset": quote,
        "symbol_status": item["status"],
        "is_spot_trading_allowed": item["isSpotTradingAllowed"],
        "base_asset_precision": item.get("baseAssetPrecision"),
        "quote_asset_precision": item.get("quoteAssetPrecision"),
        "filters": item.get("filters", []),
        "permissions": item.get("permissions"),
        "permission_sets": item.get("permissionSets"),
        "market_resolution": resolution,
        "captured_exchange_info": evidence,
    }

def capture_and_build_report(
    *,
    symbol: str | None,
    interval: str,
    start_time_ms: int,
    end_time_ms_exclusive: int,
    config: dict,
    base_asset_ticker: str | None = None,
    quote_asset: str | None = None,
    use_case: str = "internal_analysis",
    authorization_record: dict | None = None,
    requested_identifier_type: str = "symbol",
    requested_asset_identifier: str | None = None,
    requested_chain_id: str | None = None,
    identity_evidence: dict | None = None,
) -> tuple[dict, dict]:
    """Capture full market metadata, resolve one market, and build a reproducible report."""
    if symbol is not None:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol must be non-empty when provided")
        metadata = capture_exchange_info(symbol, use_case=use_case, authorization_record=authorization_record)
    else:
        if not isinstance(base_asset_ticker, str) or not base_asset_ticker.strip():
            raise ValueError("base_asset_ticker is required when symbol is not provided")
        metadata = capture_exchange_info(
            None, base_asset_ticker=base_asset_ticker, quote_asset=quote_asset,
            use_case=use_case, authorization_record=authorization_record,
        )
        symbol = metadata["symbol_native"]
    if base_asset_ticker is not None and base_asset_ticker.strip().casefold() != metadata["base_asset"].casefold():
        raise ValueError("base_asset_ticker does not match the resolved Binance market base asset")
    base_asset_ticker = metadata["base_asset"]
    artifact = capture_history(symbol, interval, start_time_ms, end_time_ms_exclusive, use_case=use_case, authorization_record=authorization_record)
    artifact["market"].update({
        "base_asset": metadata["base_asset"],
        "quote_asset": metadata["quote_asset"],
        "symbol_status_at_capture": metadata["symbol_status"],
        "is_spot_trading_allowed_at_capture": metadata["is_spot_trading_allowed"],
    })
    artifact["market_identity_evidence"] = metadata["captured_exchange_info"]
    if identity_evidence is not None:
        artifact["canonical_asset_identity_evidence"] = identity_evidence
    artifact["pipeline"] = {
        "schema_version": PIPELINE_SCHEMA,
        "metadata_capture_status": metadata["captured_exchange_info"]["capture_status"],
        "metadata_sha256": metadata["captured_exchange_info"]["response_sha256"],
        "market_identity_basis": "IDENTITY_EVIDENCE_SUPPLIED_PENDING_VALIDATION" if identity_evidence is not None else "BINANCE_EXCHANGE_INFO_BASE_ASSET_ONLY",
        "canonical_cross_provider_asset_id": "PENDING_VALIDATION" if identity_evidence is not None else "NOT_RESOLVED",
        "license_review_status": metadata["captured_exchange_info"]["provider_use_assessment"].get("authorization_evidence_status", "UNKNOWN"),
        "provider_use_assessment": metadata["captured_exchange_info"]["provider_use_assessment"],
    }
    capture_raw = (
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    requested_asset_id = (
        requested_asset_identifier.strip()
        if isinstance(requested_asset_identifier, str) and requested_asset_identifier.strip()
        else base_asset_ticker
    )
    report = build_research_report(
        artifact, config, requested_asset_id, capture_raw,
        requested_identifier_type=requested_identifier_type,
        requested_chain_id=requested_chain_id,
        identity_evidence=identity_evidence,
    )
    # ExchangeInfo proves only the market base ticker. Canonical identity requires
    # separate, unique, reviewed evidence linked to that base asset.
    report["asset_identity_scope"] = (
        "Reviewed unique canonical identity evidence linked to Binance baseAsset."
        if report["canonical_asset_identity_status"] == "VERIFIED"
        else "Binance pair baseAsset ticker only; canonical cross-provider identity is unresolved."
    )
    if report["canonical_asset_identity_status"] != "VERIFIED":
        report["asset_identity_status"] = "INDETERMINATE"
        report["report_status"] = "PARTIAL"
        report["data_quality"]["status"] = "INCOMPLETE_OR_UNVERIFIED"
        report["data_quality"]["dimensions"]["canonical_asset_identity"] = "NOT_RESOLVED"
        for horizon in report["horizons"].values():
            if "CANONICAL_ASSET_ID_NOT_RESOLVED" not in horizon["reason_codes"]:
                horizon["reason_codes"].append("CANONICAL_ASSET_ID_NOT_RESOLVED")
    report["pipeline"] = {
        "schema_version": PIPELINE_SCHEMA,
        "provider_use_assessment": metadata["captured_exchange_info"]["provider_use_assessment"],
        "capture_artifact_sha256": hashlib.sha256(capture_raw).hexdigest(),
        "capture_artifact_bytes": len(capture_raw),
        "exchange_info_sha256": metadata["captured_exchange_info"]["response_sha256"],
        "klines_source": KLINES_URL,
        "market_identity_basis": "REVIEWED_CANONICAL_IDENTITY_EVIDENCE_AND_BINANCE_BASE_ASSET" if report["canonical_asset_identity_status"] == "VERIFIED" else "BINANCE_EXCHANGE_INFO_BASE_ASSET_ONLY",
        "canonical_cross_provider_asset_id": report["canonical_asset_identity"].get("stable_id") or "NOT_RESOLVED",
        "license_review_status": metadata["captured_exchange_info"]["provider_use_assessment"].get("authorization_evidence_status", "UNKNOWN"),
        "network_requests_made": True,
        "orders_submitted": False,
    }
    report["network_requests_made"] = True
    report["orders_submitted"] = False
    identity_limitation = (
        "Canonical identity is based on the supplied reviewed evidence; source authority, scope, and aliases still require human review."
        if report["canonical_asset_identity_status"] == "VERIFIED"
        else "This pipeline resolves the base ticker from Binance exchangeInfo only; it does not establish a globally unique token identity across chains, wrapped assets, or other providers."
    )
    report["limitations"] = list(report.get("limitations", [])) + [
        identity_limitation,
        "Public endpoint documentation establishes technical availability, not a blanket commercial licence. Review applicable terms before commercial persistence, display, export, or redistribution.",
        "The pipeline performs read-only GET requests only. It never submits orders or uses trading credentials.",
    ]
    return {"artifact": artifact, "raw_bytes": capture_raw}, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    market_input = parser.add_mutually_exclusive_group(required=True)
    market_input.add_argument("--symbol", help="Exact native Binance Spot symbol, e.g. BTCUSDT")
    market_input.add_argument("--asset-ticker", help="Binance baseAsset ticker; requires --quote-asset if multiple pairs match")
    parser.add_argument("--quote-asset", help="Quote ticker to disambiguate --asset-ticker candidates, e.g. USDT")
    parser.add_argument("--base-asset-ticker", help="Optional assertion that the resolved market base ticker matches this value")
    parser.add_argument("--interval", required=True)
    parser.add_argument("--start-time-ms", required=True, type=int, help="Inclusive UTC candle boundary, Unix milliseconds")
    parser.add_argument("--end-time-ms", required=True, type=int, help="Exclusive UTC candle boundary, Unix milliseconds")
    parser.add_argument("--config", required=True, type=Path, help="Explicit descriptive-analysis configuration JSON")
    parser.add_argument("--use-case", choices=sorted(SUPPORTED_USE_CASES), default="internal_analysis",
                        help="Intended data use; defaults to internal_analysis and requires explicit authorization")
    parser.add_argument("--authorization-record", type=Path, help="Reviewed provider authorization record JSON")
    parser.add_argument("--asset-id-type", choices=("symbol", "canonical_id", "contract_address", "name"), default="symbol")
    parser.add_argument("--asset-identifier", help="Identifier checked against reviewed evidence; for example Bitcoin, registry:bitcoin, or a contract address")
    parser.add_argument("--asset-chain-id", help="Required when --asset-id-type=contract_address")
    parser.add_argument("--identity-evidence", type=Path, help="Reviewed canonical identity evidence JSON")
    parser.add_argument("--capture-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    authorization_record = json.loads(args.authorization_record.read_text(encoding="utf-8")) if args.authorization_record else None
    identity_evidence = json.loads(args.identity_evidence.read_text(encoding="utf-8")) if args.identity_evidence else None
    if args.asset_id_type != "symbol" and not args.asset_identifier:
        parser.error("--asset-identifier is required when --asset-id-type is not symbol")
    if args.asset_identifier and not args.identity_evidence:
        parser.error("--asset-identifier requires --identity-evidence for verification")
    if args.asset_ticker and args.base_asset_ticker and args.asset_ticker.casefold() != args.base_asset_ticker.casefold():
        parser.error("--base-asset-ticker must match --asset-ticker when both are supplied")
    captured, report = capture_and_build_report(
        symbol=args.symbol,
        interval=args.interval,
        start_time_ms=args.start_time_ms,
        end_time_ms_exclusive=args.end_time_ms,
        config=config,
        base_asset_ticker=args.base_asset_ticker or args.asset_ticker,
        quote_asset=args.quote_asset,
        use_case=args.use_case,
        authorization_record=authorization_record,
        requested_identifier_type=args.asset_id_type,
        requested_asset_identifier=args.asset_identifier,
        requested_chain_id=args.asset_chain_id,
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
        "canonical_asset_id": report["canonical_asset_identity"].get("stable_id"),
        "horizons": {key: value["status"] for key, value in report["horizons"].items()},
        "orders_submitted": False,
    }, ensure_ascii=False, indent=2))
    return 0 if captured["artifact"]["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
