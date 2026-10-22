import unittest

from scripts.market_selection.canonical_asset_identity import (
    SCHEMA_VERSION,
    resolve_asset_identity,
)


def evidence(*, asset_type="NATIVE_ASSET", symbol="BTC", stable_id="registry:bitcoin", candidate_count=1, review_status="APPROVED", contract_address=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "stable_id": stable_id,
        "asset_type": asset_type,
        "symbol": symbol,
        "name": "Bitcoin" if symbol == "BTC" else "Example Token",
        "chain_id": "bitcoin" if asset_type == "NATIVE_ASSET" else "eip155:1",
        "contract_address": contract_address,
        "resolution": {
            "status": "VERIFIED_UNIQUE" if candidate_count == 1 else "AMBIGUOUS",
            "candidate_count": candidate_count,
            "review_status": review_status,
            "reviewed_by": "offline-test-fixture",
            "reviewed_at": "2026-10-22T00:00:00Z",
        },
        "source": {
            "source_type": "AUTHORITATIVE_REGISTRY",
            "url": "https://example.invalid/registry/item",
            "publisher": "Synthetic fixture only",
            "captured_at": "2026-10-22T00:00:00Z",
            "content_sha256": "a" * 64,
        },
    }


class CanonicalAssetIdentityTests(unittest.TestCase):
    def test_symbol_match_only_verifies_market_mapping_not_canonical_identity(self):
        result = resolve_asset_identity({"type": "symbol", "value": "BTC"}, {"base_asset": "BTC"})
        self.assertEqual(result["market_base_asset_mapping_status"], "VERIFIED")
        self.assertEqual(result["canonical_asset_identity_status"], "NOT_RESOLVED")
        self.assertEqual(result["asset_identity_status"], "INDETERMINATE")

    def test_reviewed_unique_native_asset_evidence_verifies_identity(self):
        result = resolve_asset_identity(
            {"type": "symbol", "value": "BTC"},
            {"base_asset": "BTC", "market_type": "SPOT"},
            evidence(),
        )
        self.assertEqual(result["canonical_asset_identity_status"], "VERIFIED")
        self.assertEqual(result["asset_identity_status"], "VERIFIED")
        self.assertEqual(result["stable_id"], "registry:bitcoin")
        self.assertRegex(result["identity_evidence"]["identity_evidence_record_sha256"], r"^[0-9a-f]{64}$")

    def test_ambiguous_or_unapproved_evidence_remains_unresolved(self):
        ambiguous = resolve_asset_identity(
            {"type": "symbol", "value": "BTC"}, {"base_asset": "BTC"}, evidence(candidate_count=2)
        )
        self.assertEqual(ambiguous["canonical_asset_identity_status"], "NOT_RESOLVED")
        pending = resolve_asset_identity(
            {"type": "symbol", "value": "BTC"}, {"base_asset": "BTC"}, evidence(review_status="PENDING")
        )
        self.assertEqual(pending["canonical_asset_identity_status"], "NOT_RESOLVED")

    def test_token_requires_chain_and_contract_and_matches_both(self):
        token = evidence(asset_type="TOKEN", symbol="EXM", stable_id="registry:example-token", contract_address="0xAbCd")
        token["chain_id"] = "eip155:1"
        result = resolve_asset_identity(
            {"type": "contract_address", "value": "0xAbCd", "chain_id": "eip155:1"},
            {"base_asset": "EXM"},
            token,
        )
        self.assertEqual(result["canonical_asset_identity_status"], "VERIFIED")
        wrong_chain = resolve_asset_identity(
            {"type": "contract_address", "value": "0xAbCd", "chain_id": "eip155:10"},
            {"base_asset": "EXM"},
            token,
        )
        self.assertEqual(wrong_chain["canonical_asset_identity_status"], "CONFLICT")

    def test_contract_address_without_chain_is_not_resolved(self):
        token = evidence(asset_type="TOKEN", symbol="EXM", stable_id="registry:example-token", contract_address="0xAbCd")
        token["chain_id"] = "eip155:1"
        result = resolve_asset_identity(
            {"type": "contract_address", "value": "0xAbCd"},
            {"base_asset": "EXM"},
            token,
        )
        self.assertEqual(result["canonical_asset_identity_status"], "NOT_RESOLVED")
        self.assertIn("CHAIN_ID_REQUIRED_FOR_CONTRACT_ADDRESS", result["reason_codes"])

    def test_market_base_conflict_blocks_identity(self):
        result = resolve_asset_identity(
            {"type": "symbol", "value": "BTC"},
            {"base_asset": "WBTC"},
            evidence(),
        )
        self.assertEqual(result["canonical_asset_identity_status"], "CONFLICT")
        self.assertEqual(result["market_base_asset_mapping_status"], "MISMATCH")

    def test_bad_source_hash_and_schema_are_rejected(self):
        invalid_hash = evidence()
        invalid_hash["source"]["content_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "64-character SHA-256"):
            resolve_asset_identity({"type": "symbol", "value": "BTC"}, {"base_asset": "BTC"}, invalid_hash)
        invalid_schema = evidence()
        invalid_schema["schema_version"] = "unknown"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            resolve_asset_identity({"type": "symbol", "value": "BTC"}, {"base_asset": "BTC"}, invalid_schema)


if __name__ == "__main__":
    unittest.main()
