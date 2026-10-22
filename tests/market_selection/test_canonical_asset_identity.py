"""Tests for fail-closed canonical crypto-asset identity contract."""
import unittest

from scripts.market_selection.canonical_asset_identity import (
    SCHEMA_VERSION,
    assess_canonical_asset_identity,
)

BASE = {
    "schema_version": SCHEMA_VERSION,
    "ticker": "eth",
    "chain_namespace": "eip155",
    "chain_reference": "1",
    "asset_namespace": "slip44",
    "asset_reference": "60",
    "provider": "controlled-fixture",
    "source_url": "https://example.org/asset-record.json",
    "evidence_sha256": "a" * 64,
    "captured_at": "2026-10-22T12:00:00Z",
    "observed_at": "2026-10-22T11:59:00Z",
}


class CanonicalAssetIdentityTests(unittest.TestCase):
    def test_explicit_chain_and_asset_coordinates_resolve_identity(self):
        result = assess_canonical_asset_identity(BASE)
        self.assertEqual(result["identity_status"], "RESOLVED")
        self.assertEqual(result["canonical_asset_id"], "eip155:1/slip44:60")
        self.assertEqual(result["ticker"], "ETH")
        self.assertFalse(result["ticker_used_as_identity"])
        self.assertEqual(result["evidence_status"], "PRESENT")

    def test_ticker_only_never_resolves_identity(self):
        result = assess_canonical_asset_identity({
            "schema_version": SCHEMA_VERSION,
            "ticker": "BTC",
        })
        self.assertEqual(result["identity_status"], "NOT_RESOLVED")
        self.assertIsNone(result["canonical_asset_id"])
        self.assertIn("CANONICAL_ID_COMPONENTS_MISSING", result["reason_codes"])

    def test_missing_provider_evidence_is_rejected(self):
        record = dict(BASE)
        record.pop("provider")
        with self.assertRaisesRegex(ValueError, "provider"):
            assess_canonical_asset_identity(record)

    def test_http_source_is_rejected(self):
        record = dict(BASE, source_url="http://example.org/asset")
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            assess_canonical_asset_identity(record)

    def test_hash_must_be_sha256_hex(self):
        record = dict(BASE, evidence_sha256="not-a-hash")
        with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
            assess_canonical_asset_identity(record)

    def test_timestamps_require_timezone(self):
        record = dict(BASE, captured_at="2026-10-22T12:00:00")
        with self.assertRaisesRegex(ValueError, "timezone"):
            assess_canonical_asset_identity(record)

    def test_whitespace_in_references_is_rejected(self):
        record = dict(BASE, asset_reference="token address")
        with self.assertRaisesRegex(ValueError, "whitespace"):
            assess_canonical_asset_identity(record)

    def test_wrong_schema_is_rejected(self):
        record = dict(BASE, schema_version="unknown")
        with self.assertRaisesRegex(ValueError, "schema_version"):
            assess_canonical_asset_identity(record)


if __name__ == "__main__":
    unittest.main()
