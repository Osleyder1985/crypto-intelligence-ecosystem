"""Fail-closed gate for provider data use.

A validated record is a software-policy check, not proof of legal rights or authenticity.
"""
from __future__ import annotations
from datetime import datetime
import hashlib
import json
import re
from urllib.parse import urlsplit

SCHEMA_VERSION = "crypto-provider-authorization-v1"
POLICY_VERSION = "1.2.0"
ASSESSMENT_SCHEMA_VERSION = "crypto-provider-use-assessment-v1"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
SUPPORTED_USE_CASES = {
    "live_technical_test", "internal_analysis", "public_display",
    "persistent_storage", "export_redistribution",
}
BASELINE_POLICY = {
    "binance_spot_market_data": {u: ("ALLOW_TECHNICAL_TEST_ONLY" if u == "live_technical_test" else "REQUIRES_APPROVAL") for u in SUPPORTED_USE_CASES},
    "binance_us_market_data": {u: ("ALLOW_TECHNICAL_TEST_ONLY" if u == "live_technical_test" else "REQUIRES_APPROVAL") for u in SUPPORTED_USE_CASES},
    "pionex_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "defillama_api": {u: "BLOCK_PENDING_WRITTEN_AUTHORIZATION" for u in SUPPORTED_USE_CASES},
    "coingecko_api": {u: "REQUIRES_PLAN_AND_SCOPE_APPROVAL" for u in SUPPORTED_USE_CASES},
    # Private account data is a separate authorization domain from public market data.
    "binance_spot_account_data": {u: "REQUIRES_ACCOUNT_OWNER_AND_PROVIDER_SCOPE_APPROVAL" for u in SUPPORTED_USE_CASES},
    "pionex_spot_account_data": {u: "REQUIRES_ACCOUNT_OWNER_AND_PROVIDER_SCOPE_APPROVAL" for u in SUPPORTED_USE_CASES},
    # Multi-exchange public snapshots are persisted as evidence; each venue requires explicit scope approval.
    "okx_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "bybit_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "mexc_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "gate_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "bitget_spot_market_data": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    # SEC press-release RSS is a candidate source; the machine-readable source registry keeps it disabled until terms are reviewed.
    "sec_press_releases": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    # Official regulatory feeds remain blocked until their source registry and use authorization are approved.
    "cftc_general_press_releases": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "federal_reserve_press_releases": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    # Historical archive pages are distinct source scopes; do not inherit approval from RSS automatically.
    "sec_press_release_archive": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "cftc_press_release_archive": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
    "federal_reserve_press_release_archive": {u: "REQUIRES_APPROVAL" for u in SUPPORTED_USE_CASES},
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
        return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK","reason_codes":["PROVIDER_NOT_REVIEWED"],
                "authorization_evidence_status":"NOT_PROVIDED"}
    baseline_status = baseline[use_case]
    if provider_id in {"binance_spot_market_data", "binance_us_market_data"} and use_case == "live_technical_test" and authorization_record is None:
        return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
                "use_case":use_case,"decision":"ALLOW","reason_codes":["TECHNICAL_TEST_ONLY"],
                "authorization_evidence_status":"NOT_A_COMMERCIAL_LICENSE"}
    if not isinstance(authorization_record, dict):
        return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK",
                "reason_codes":[baseline_status,"AUTHORIZATION_RECORD_MISSING"],
                "authorization_evidence_status":"NOT_PROVIDED"}
    record = authorization_record
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"authorization_record.schema_version must be {SCHEMA_VERSION}")
    if _text(record.get("provider_id"), "authorization_record.provider_id").lower() != provider_id:
        raise ValueError("authorization_record.provider_id does not match requested provider")
    if record.get("status") != "APPROVED":
        return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
                "use_case":use_case,"decision":"BLOCK","reason_codes":["AUTHORIZATION_NOT_APPROVED"],
                "authorization_evidence_status":"PRESENT_BUT_NOT_APPROVED"}
    allowed = record.get("authorized_use_cases")
    if not isinstance(allowed, list) or use_case not in allowed:
        return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
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
    if provider_id in {"binance_spot_account_data", "pionex_spot_account_data"}:
        consent_ref = _text(record.get("account_owner_consent_ref"), "authorization_record.account_owner_consent_ref")
        consent_hash = _text(record.get("account_owner_consent_sha256"), "authorization_record.account_owner_consent_sha256")
        if not _SHA256.fullmatch(consent_hash):
            raise ValueError("authorization_record.account_owner_consent_sha256 must be 64 hexadecimal characters")
        if record.get("credential_scope_verified") is not True:
            raise ValueError("authorization_record.credential_scope_verified must be true for private account data")
    if provider_id == "coingecko_api":
        plan = _text(record.get("plan_name"), "authorization_record.plan_name").lower()
        if plan in {"demo", "free", "keyless"}:
            return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
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
            return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
                    "use_case":use_case,"decision":"BLOCK",
                    "reason_codes":["CUSTOM_REDISTRIBUTION_RIGHTS_REQUIRED"],
                    "authorization_evidence_status":"STANDARD_LICENSE_INSUFFICIENT"}
    try:
        authorization_record_sha256 = hashlib.sha256(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError) as exc:
        raise ValueError("authorization_record must be canonical JSON without non-finite values") from exc
    authorization_evidence = {
        "terms_url": terms_url,
        "terms_sha256": terms_sha256.lower(),
        "reviewed_at": reviewed_at,
        "reviewed_by": reviewer,
        "authorized_use_cases": sorted(allowed),
        "authorization_record_sha256": authorization_record_sha256,
    }
    if provider_id == "defillama_api":
        authorization_evidence["written_authorization_url"] = written_url
        authorization_evidence["written_authorization_sha256"] = written_hash.lower()
    if provider_id in {"binance_spot_account_data", "pionex_spot_account_data"}:
        authorization_evidence["account_owner_consent_ref"] = consent_ref
        authorization_evidence["account_owner_consent_sha256"] = consent_hash.lower()
        authorization_evidence["credential_scope_verified"] = True
    return {"schema_version":ASSESSMENT_SCHEMA_VERSION,"policy_version":POLICY_VERSION,"provider_id":provider_id,
            "use_case":use_case,"decision":"ALLOW",
            "reason_codes":["EXPLICIT_AUTHORIZATION_RECORD_VALIDATED"],
            "authorization_evidence_status":"RECORD_VALIDATED_NOT_LEGAL_ADVICE",
            "authorization":authorization_evidence}


def _collect_provider_assessments(value: object, output: list[dict]) -> None:
    """Collect capture assessments while ignoring failed rows that were not consumed."""
    if isinstance(value, dict):
        assessment = value.get("provider_use_assessment")
        if isinstance(assessment, dict):
            capture_status = value.get("capture_status")
            if capture_status not in {"FAIL", "BLOCKED", "NOT_AVAILABLE"}:
                output.append(assessment)
        elif value.get("capture_status") == "PASS" and any(key in value for key in ("provider", "exchange", "provider_id")):
            output.append({"schema_version": ASSESSMENT_SCHEMA_VERSION, "policy_version": None,
                           "provider_id": str(value.get("provider_id") or value.get("provider") or value.get("exchange") or ""),
                           "decision": "BLOCK", "reason_codes": ["PROVIDER_USE_ASSESSMENT_MISSING"]})
        elif value.get("schema_version") == ASSESSMENT_SCHEMA_VERSION:
            output.append(value)
        for key, child in value.items():
            if key != "provider_use_assessment":
                _collect_provider_assessments(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_provider_assessments(child, output)


def evaluate_artifact_use(artifact: object, use_case: str) -> dict:
    """Check that supplied capture evidence includes explicit authorization for a downstream use.

    This validates recorded policy evidence, not legal rights or document authenticity.
    """
    if use_case not in SUPPORTED_USE_CASES:
        raise ValueError(f"unsupported use_case: {use_case}")
    assessments: list[dict] = []
    _collect_provider_assessments(artifact, assessments)
    # Check every consumed assessment. Never deduplicate away a conflicting or tampered row.
    reasons: list[str] = []
    provider_ids: list[str] = []
    if not assessments:
        reasons.append("PROVIDER_USE_ASSESSMENT_MISSING")
    for assessment in assessments:
        provider_id = str(assessment.get("provider_id", "")).lower()
        if provider_id and provider_id not in provider_ids:
            provider_ids.append(provider_id)
        if provider_id not in BASELINE_POLICY:
            reasons.append("PROVIDER_NOT_REVIEWED")
            continue
        if assessment.get("policy_version") != POLICY_VERSION:
            reasons.append("PROVIDER_POLICY_VERSION_MISMATCH")
        if assessment.get("decision") != "ALLOW":
            reasons.extend(assessment.get("reason_codes") or ["CAPTURE_PROVIDER_USE_NOT_ALLOWED"])
            continue
        authorization = assessment.get("authorization")
        if not isinstance(authorization, dict):
            reasons.append("AUTHORIZATION_EVIDENCE_MISSING_FOR_DOWNSTREAM_USE")
            continue
        scopes = authorization.get("authorized_use_cases")
        if not isinstance(scopes, list) or use_case not in scopes:
            reasons.append("DOWNSTREAM_USE_CASE_NOT_EXPLICITLY_AUTHORIZED")
        record_hash = authorization.get("authorization_record_sha256")
        if not isinstance(record_hash, str) or not _SHA256.fullmatch(record_hash):
            reasons.append("AUTHORIZATION_RECORD_HASH_MISSING_OR_INVALID")
    return {
        "schema_version": ASSESSMENT_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "use_case": use_case,
        "decision": "ALLOW" if assessments and not reasons else "BLOCK",
        "provider_ids": sorted(provider_ids),
        "reason_codes": sorted(set(reasons)),
        "assessments_checked": len(assessments),
    }

