"""Read-only 24h Spot quote-turnover observations for the Issue #7 exchange universe."""
from __future__ import annotations
import argparse, base64, hashlib, json, math, sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TIMEOUT_SECONDS = 12
READ_CHUNK_BYTES = 64 * 1024
SCHEMA_VERSION = "multi-exchange-spot-quote-volume-v1"
MARKETS = (
    {"asset":"BTC","binance":"BTCUSDT","okx":"BTC-USDT","bybit":"BTCUSDT","mexc":"BTCUSDT","gate":"BTC_USDT","bitget":"BTCUSDT","pionex":"BTC_USDT"},
    {"asset":"ETH","binance":"ETHUSDT","okx":"ETH-USDT","bybit":"ETHUSDT","mexc":"ETHUSDT","gate":"ETH_USDT","bitget":"ETHUSDT","pionex":"ETH_USDT"},
    {"asset":"SOL","binance":"SOLUSDT","okx":"SOL-USDT","bybit":"SOLUSDT","mexc":"SOLUSDT","gate":"SOL_USDT","bitget":"SOLUSDT","pionex":"SOL_USDT"},
)

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def read_complete(response):
    chunks = []
    while True:
        chunk = response.read(READ_CHUNK_BYTES)
        if not chunk: break
        chunks.append(chunk)
    return b"".join(chunks)

def build_requests():
    requests = []
    for market in MARKETS:
        for exchange, symbol in ((k, market[k]) for k in ("binance","okx","bybit","mexc","gate","bitget","pionex")):
            if exchange == "binance": url = "https://data-api.binance.vision/api/v3/ticker/24hr?" + urlencode({"symbol":symbol})
            elif exchange == "okx": url = "https://www.okx.com/api/v5/market/ticker?" + urlencode({"instId":symbol})
            elif exchange == "bybit": url = "https://api.bybit.com/v5/market/tickers?" + urlencode({"category":"spot","symbol":symbol})
            elif exchange == "mexc": url = "https://api.mexc.com/api/v3/ticker/24hr?" + urlencode({"symbol":symbol})
            elif exchange == "gate": url = "https://api.gateio.ws/api/v4/spot/tickers?" + urlencode({"currency_pair":symbol})
            elif exchange == "bitget": url = "https://api.bitget.com/api/v3/market/tickers?" + urlencode({"category":"SPOT","symbol":symbol})
            else: url = "https://api.pionex.com/api/v1/market/tickers?" + urlencode({"symbol":symbol,"type":"SPOT"})
            requests.append({"exchange":exchange,"asset":market["asset"],"symbol":symbol,"quote_currency":"USDT","url":url})
    return requests

def extract_quote_volume(exchange, payload):
    if exchange == "gate":
        if not isinstance(payload, list) or not payload: raise ValueError("Gate response has no ticker")
        return payload[0].get("quote_volume"), payload[0].get("time"), "quote_volume: quote-currency turnover"
    if not isinstance(payload, dict): raise ValueError("top-level response must be an object")
    if exchange == "binance": return payload.get("quoteVolume"), payload.get("closeTime"), "quoteVolume: quote-asset turnover over rolling 24h"
    if exchange == "okx":
        if payload.get("code") != "0": raise ValueError("OKX response code was not 0")
        rows = payload.get("data")
        if not isinstance(rows,list) or not rows: raise ValueError("OKX response has no ticker")
        return rows[0].get("volCcy24h"), rows[0].get("ts"), "volCcy24h: quote-currency volume for Spot"
    if exchange == "bybit":
        if payload.get("retCode") != 0: raise ValueError("Bybit retCode was not 0")
        result = payload.get("result")
        rows = result.get("list") if isinstance(result,dict) else None
        if not isinstance(rows,list) or not rows: raise ValueError("Bybit response has no ticker list")
        return rows[0].get("turnover24h"), payload.get("time"), "turnover24h: quote-currency turnover for Spot"
    if exchange == "mexc": return payload.get("quoteVolume"), payload.get("closeTime"), "quoteVolume: quote-asset volume when supplied by endpoint"
    if exchange == "bitget":
        if payload.get("code") != "00000": raise ValueError("Bitget response code was not 00000")
        rows = payload.get("data")
        if not isinstance(rows,list) or not rows: raise ValueError("Bitget response has no ticker list")
        return rows[0].get("turnover24h"), rows[0].get("ts"), "turnover24h: quote-currency turnover for Spot"
    if exchange == "pionex":
        if payload.get("result") is not True: raise ValueError("Pionex response result was not true")
        data = payload.get("data")
        rows = data.get("tickers") if isinstance(data,dict) else None
        if not isinstance(rows,list) or not rows: raise ValueError("Pionex response has no tickers")
        return rows[0].get("amount"), rows[0].get("time",payload.get("timestamp")), "amount: documented 24h total trading amount; verify quote denomination from symbol"
    raise ValueError("unsupported exchange: " + str(exchange))

def capture_one(spec):
    record = {**spec,"request_started_at_utc":now_utc(),"captured_at_utc":None,"http_status":None,"response_bytes":None,"response_sha256":None,"response_base64":None,"parsed_json":None,"source_timestamp_raw":None,"quote_volume_raw":None,"quote_volume_decimal":None,"quote_volume_unit":"USDT","volume_semantics":None,"capture_status":"FAIL","quote_volume_status":"INDETERMINATE","error_type":None,"error_message":None}
    req = Request(spec["url"],headers={"Accept":"application/json","User-Agent":"crypto-intelligence-ecosystem-quote-volume-probe/1.0"})
    try:
        with urlopen(req,timeout=TIMEOUT_SECONDS) as response:
            status=getattr(response,"status",None); raw=read_complete(response)
        record.update(http_status=status,captured_at_utc=now_utc(),response_bytes=len(raw),response_sha256=hashlib.sha256(raw).hexdigest(),response_base64=base64.b64encode(raw).decode("ascii"))
        payload=json.loads(raw.decode("utf-8")); record["parsed_json"]=payload
        if status != 200: raise ValueError("expected HTTP 200, received " + str(status))
        raw_volume,source_ts,semantics=extract_quote_volume(spec["exchange"],payload)
        record.update(source_timestamp_raw=source_ts,quote_volume_raw=raw_volume,volume_semantics=semantics,capture_status="PASS")
        if raw_volume is not None:
            try:
                value=Decimal(str(raw_volume))
                if value.is_finite() and value >= 0:
                    record["quote_volume_decimal"]=str(value); record["quote_volume_status"]="VALID"
                else: record["quote_volume_status"]="INVALID"
            except (InvalidOperation,ValueError): record["quote_volume_status"]="INVALID"
    except (HTTPError,URLError,TimeoutError,OSError,ValueError,TypeError,KeyError,IndexError,json.JSONDecodeError) as exc:
        record["captured_at_utc"]=now_utc(); record["error_type"]=type(exc).__name__; record["error_message"]=str(exc)[:300]
        if isinstance(exc,HTTPError):
            record["http_status"]=exc.code
            try:
                raw=read_complete(exc); record["response_bytes"]=len(raw); record["response_sha256"]=hashlib.sha256(raw).hexdigest(); record["response_base64"]=base64.b64encode(raw).decode("ascii")
            except OSError: pass
    return record

def capture_batch():
    records=[capture_one(spec) for spec in build_requests()]
    exchanges=("binance","okx","bybit","mexc","gate","bitget","pionex")
    return {"schema_version":SCHEMA_VERSION,"created_at_utc":now_utc(),"scope":"read-only rolling 24h public Spot quote-turnover observations; no credentials; no orders","expected_record_count":21,"actual_record_count":len(records),"records":records,"exchange_status":{e:("PASS" if any(x["exchange"]==e and x["capture_status"]=="PASS" for x in records) else "FAIL") for e in exchanges},"overall_status":"PASS" if all(x["capture_status"]=="PASS" and x["quote_volume_status"]=="VALID" for x in records) else "PARTIAL","limitations":["A single rolling-24h ticker is not historical volume stability; stability requires repeated dated captures or candle history.","Provider fields have documented but non-identical semantics; raw values, source timestamps, URLs and response hashes are retained.","MEXC may return null quoteVolume; missing values remain INDETERMINATE and are never replaced by zero.","Bybit HTTP 403 from the CI runner is preserved as an access failure; no alternate domain is used to bypass it.","Snapshots are sequential and quote volume alone does not measure executable liquidity or asset risk."]}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output",default="artifacts/multi-exchange-spot-quote-volume.json"); args=parser.parse_args()
    artifact=capture_batch(); path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(artifact,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"artifact":str(path),"overall_status":artifact["overall_status"],"exchange_status":artifact["exchange_status"],"records":[{k:r.get(k) for k in ("exchange","asset","symbol","capture_status","http_status","quote_volume_raw","quote_volume_unit","quote_volume_status","source_timestamp_raw","error_type","error_message")} for r in artifact["records"]]},ensure_ascii=False,indent=2))
    return 0 if artifact["overall_status"]=="PASS" else 1

if __name__ == "__main__": sys.exit(main())
