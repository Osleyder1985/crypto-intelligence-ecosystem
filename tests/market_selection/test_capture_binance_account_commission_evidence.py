import hashlib
import hmac
import json
import unittest
from urllib.parse import parse_qs, urlparse

from scripts.market_selection.capture_binance_account_commission_evidence import (
    build_signed_url,
    capture_commission_evidence,
    validate_commission_response,
)


def valid_payload(symbol="BTCUSDT"):
    return {
        "symbol": symbol,
        "standardCommission": {"maker": "0.00100000", "taker": "0.00100000", "buyer": "0", "seller": "0"},
        "taxCommission": {"maker": "0", "taker": "0", "buyer": "0", "seller": "0"},
        "specialCommission": {"maker": "0", "taker": "0", "buyer": "0", "seller": "0"},
        "discount": {"enabledForAccount": True, "enabledForSymbol": True, "discountAsset": "BNB", "discount": "0.25"},
    }


class FakeResponse:
    def __init__(self, payload, status=200):
        self.raw = json.dumps(payload).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.raw


AUTHORIZATION_RECORD = {
    "schema_version": "crypto-provider-authorization-v1",
    "provider_id": "binance_spot_account_data",
    "status": "APPROVED",
    "authorized_use_cases": ["internal_analysis"],
    "terms_url": "https://www.binance.com/en/terms",
    "terms_sha256": "a" * 64,
    "reviewed_at": "2026-10-22T00:00:00Z",
    "reviewed_by": "offline-test-fixture",
    "account_owner_consent_ref": "offline-consent-fixture",
    "account_owner_consent_sha256": "b" * 64,
    "credential_scope_verified": True,
}


class CommissionEvidenceTests(unittest.TestCase):
    def test_signed_url_signs_exact_query_and_contains_no_secret(self):
        url = build_signed_url("BTCUSDT", "not-for-output", 123456789)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        expected = hmac.new(b"not-for-output", b"symbol=BTCUSDT&timestamp=123456789", hashlib.sha256).hexdigest()
        self.assertEqual(query["signature"], [expected])
        self.assertEqual(query["symbol"], ["BTCUSDT"])
        self.assertNotIn("not-for-output", url)

    def test_valid_account_specific_response_passes_and_does_not_emit_credentials(self):
        response = FakeResponse(valid_payload())
        def opener(request, timeout):
            self.assertEqual(request.get_header("X-mbx-apikey"), "public-key-test")
            self.assertEqual(timeout, 12)
            return response
        result = capture_commission_evidence("BTCUSDT", "public-key-test", "secret-test", timestamp_ms=123, opener=opener, authorization_record=AUTHORIZATION_RECORD)
        self.assertEqual(result["commission_evidence_status"], "PASS")
        self.assertEqual(result["response_sha256"], hashlib.sha256(response.raw).hexdigest())
        self.assertFalse(result["orders_submitted"])
        rendered = json.dumps(result)
        self.assertNotIn("public-key-test", rendered)
        self.assertNotIn("secret-test", rendered)

    def test_wrong_symbol_is_indeterminate(self):
        valid, reason = validate_commission_response(valid_payload("ETHUSDT"), "BTCUSDT")
        self.assertFalse(valid)
        self.assertIn("does not match", reason)

    def test_missing_commission_group_is_indeterminate(self):
        payload = valid_payload()
        del payload["taxCommission"]
        valid, reason = validate_commission_response(payload, "BTCUSDT")
        self.assertFalse(valid)
        self.assertIn("taxCommission", reason)

    def test_negative_or_nonfinite_rate_is_rejected(self):
        for value in ("-0.01", "NaN", "Infinity", "not-a-rate"):
            payload = valid_payload()
            payload["standardCommission"]["maker"] = value
            valid, _reason = validate_commission_response(payload, "BTCUSDT")
            self.assertFalse(valid, value)

    def test_missing_discount_metadata_is_rejected(self):
        payload = valid_payload()
        payload.pop("discount")
        valid, reason = validate_commission_response(payload, "BTCUSDT")
        self.assertFalse(valid)
        self.assertIn("discount", reason)

    def test_non_json_http_200_does_not_pass(self):
        class BadResponse(FakeResponse):
            def __init__(self):
                self.raw = b"not-json"
                self.status = 200
        result = capture_commission_evidence(
            "BTCUSDT", "key", "secret", timestamp_ms=1, opener=lambda *_args, **_kwargs: BadResponse(),
            authorization_record=AUTHORIZATION_RECORD,
        )
        self.assertEqual(result["commission_evidence_status"], "INDETERMINATE")
        self.assertEqual(result["response_sha256"], hashlib.sha256(b"not-json").hexdigest())
        self.assertIsNone(result["response"])

    def test_http_error_does_not_persist_error_body_or_secrets(self):
        from urllib.error import HTTPError
        def fail(*_args, **_kwargs):
            raise HTTPError("https://api.binance.com", 451, "restricted", {}, None)
        result = capture_commission_evidence("BTCUSDT", "key", "secret", timestamp_ms=1, opener=fail, authorization_record=AUTHORIZATION_RECORD)
        self.assertEqual(result["http_status"], 451)
        self.assertEqual(result["commission_evidence_status"], "INDETERMINATE")
        self.assertNotIn("signature", json.dumps(result))
        self.assertFalse(result["orders_submitted"])


if __name__ == "__main__":
    unittest.main()
