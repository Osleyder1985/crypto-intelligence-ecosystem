"""Fail-closed gate for provider data use.

A validated record is a software-policy check, not proof of legal rights or authenticity.
"""
from __future__ import annotations
from datetime import datetime
import re
from urllib.parse import urlsplit

SCHEMA_VERSION = "crypto-provider-authorization-v1"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
SUPPORTED_USE_CASES = {
    "live_technical_test", "internal_analysis", "public_display",
    "persistent_storage", "export_redistribution",
}
BASELINE_POLICY = {
    "binance_spot_market_data": {u: ("ALLOW_TECHNICAL_TEST_ONLY" if u == "live_technical_test" else "REQUIRES_APPROVAL") for u in SUPPORTED_USE_CASES},
    "pionex_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "defillama_api": {u: "BLOCK_PENDING_WRITTEN_AUTHORIZATION" for u in SUPPORTED_USE_CASES},
    "coingecko_api": {u: "REQUIRES_PLAN_AND_SCOPE_APPROVAL" for u in SUPPORTED_USE_CASES},
}

def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()

def _timestamp(value: object, field: str) -> str:
    raw = _text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return raw

def evaluate_provider_use(provider_id: str, use_case: str, authorization_record: dict | None = None) -> dict:
    provider_id = _text(provider_id, "provider_id").lower()
    if use_case not in SUPPORTED_USE_CASES:
        raise ValueError(f"unsupported use_case: {use_case}")
    baseline = BASELINE_POLICY.get(provider_id)
    if baseline is None:
        return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK","reason_codes":["PROVIDER_NOT_REVIEWED"],
                "authorization_evidence_status":"NOT_PROVIDED"}
    baseline_status = baseline[use_case]
    if provider_id == "binance_spot_market_data" and use_case == "live_technical_test":
        return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                "use_case":use_case,"decision":"ALLOW","reason_codes":["TECHNICAL_TEST_ONLY"],
                "authorization_evidence_status":"NOT_A_COMMERCIAL_LICENSE"}
    if not isinstance(authorization_record, dict):
        return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK",
                "reason_codes":[baseline_status,"AUTHORIZATION_RECORD_MISSING"],
                "authorization_evidence_status":"NOT_PROVIDED"}
    record = authorization_record
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"authorization_record.schema_version must be {SCHEMA_VERSION}")
    if _text(record.get("provider_id"), "authorization_record.provider_id").lower() != provider_id:
        raise ValueError("authorization_record.provider_id does not match requested provider")
    if record.get("status") != "APPROVED":
        return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK","reason_codes":["AUTHORIZATION_NOT_APPROVED"],
                "authorization_evidence_status":"PRESENT_BUT_NOT_APPROVED"}
    allowed = record.get("authorized_use_cases")
    if not isinstance(allowed, list) or use_case not in allowed:
        return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK","reason_codes":["USE_CASE_NOT_EXPLICITLY_AUTHORIZED"],
                "authorization_evidence_status":"SCOPE_MISMATCH"}
    terms_url = _text(record.get("terms_url"), "authorization_record.terms_url")
    parsed_url = urlsplit(terms_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("authorization_record.terms_url must be an absolute HTTPS URL")
    terms_sha256 = _text(record.get("terms_sha256"), "authorization_record.terms_sha256")
    if not _SHA256.fullmatch(terms_sha256):
        raise ValueError("authorization_record.terms_sha256 must be 64 hexadecimal characters")
    reviewed_at = _timestamp(record.get("reviewed_at"), "authorization_record.reviewed_at")
    reviewer = _text(record.get("reviewed_by"), "authorization_record.reviewed_by")
    if provider_id == "defillama_api":
        written_url = _text(record.get("written_authorization_url"), "authorization_record.written_authorization_url")
        written_hash = _text(record.get("written_authorization_sha256"), "authorization_record.written_authorization_sha256")
        if urlsplit(written_url).scheme != "https" or not urlsplit(written_url).netloc:
            raise ValueError("written_authorization_url must be an absolute HTTPS URL")
        if not _SHA256.fullmatch(written_hash):
            raise ValueError("written_authorization_sha256 must be 64 hexadecimal characters")
    if provider_id == "coingecko_api":
        plan = _text(record.get("plan_name"), "authorization_record.plan_name").lower()
        if plan in {"demo", "free", "keyless"}:
            return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                    "use_case":use_case,"decision":"BLOCK",
                    "reason_codes":["PAID_PLAN_REQUIRED_FOR_COMMERCIAL_PRODUCT"],
                    "authorization_evidence_status":"PLAN_INSUFFICIENT"}
        if use_case == "public_display":
            _text(record.get("attribution_text"), "authorization_record.attribution_text")
            _text(record.get("attribution_url"), "authorization_record.attribution_url")
        if use_case == "persistent_storage":
            refresh = record.get("cache_refresh_hours")
            if not isinstance(refresh, (int, float)) or isinstance(refresh, bool) or not 0 < refresh <= 24:
                raise ValueError("CoinGecko cache_refresh_hours must be greater than 0 and at most 24")
            if record.get("encrypted_storage") is not True or record.get("delete_on_termination") is not True:
                raise ValueError("CoinGecko persistent storage requires encryption and deletion on termination")
        if use_case == "export_redistribution" and record.get("custom_redistribution_rights") is not True:
            return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
                    "use_case":use_case,"decision":"BLOCK",
                    "reason_codes":["CUSTOM_REDISTRIBUTION_RIGHTS_REQUIRED"],
                    "authorization_evidence_status":"STANDARD_LICENSE_INSUFFICIENT"}
    return {"schema_version":"crypto-provider-use-assessment-v1","provider_id":provider_id,
            "use_case":use_case,"decision":"ALLOW",
            "reason_codes":["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization_evidence_status":"RECORD_VALIDATED_NOT_LEGAL_ADVICE",
            "authorization":{"terms_url":terms_url,"terms_sha256":terms_sha256.lower(),
                             "reviewed_at":reviewed_at,"reviewed_by":reviewer}}
