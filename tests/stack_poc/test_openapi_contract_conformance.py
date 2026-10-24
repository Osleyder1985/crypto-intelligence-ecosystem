"""Contract conformance checks between the checked-in OpenAPI and the running API PoC."""
import tempfile
import unittest
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from scripts.stack_poc.research_api import create_app

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs" / "architecture" / "stack-poc-openapi.yaml"


class OpenAPIClientServerContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "contract.sqlite3"
        self.token = "contract-test-secret"
        self.app = create_app(self.db, bearer_token=self.token)
        self.client = TestClient(
            self.app, headers={"Authorization": f"Bearer {self.token}"}
        )
        with self.app.state.poc_connect() as conn:
            conn.execute(
                "INSERT INTO assets(asset_id, canonical_symbol, display_name) VALUES (?, ?, ?)",
                ("asset-btc", "BTC", "Bitcoin"),
            )
            conn.commit()
        self.contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.server_contract = self.app.openapi()

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def test_contract_paths_and_methods_exist_on_server(self):
        server_paths = self.server_contract["paths"]
        for path, operations in self.contract["paths"].items():
            self.assertIn(path, server_paths, f"Server missing contract path: {path}")
            for method in operations:
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    self.assertIn(
                        method.lower(), server_paths[path],
                        f"Server missing {method.upper()} {path}",
                    )

    def test_contract_success_statuses_are_declared_by_server(self):
        server_paths = self.server_contract["paths"]
        for path, operations in self.contract["paths"].items():
            for method, operation in operations.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                declared = set(server_paths[path][method.lower()]["responses"])
                for status in operation.get("responses", {}):
                    if str(status).startswith("2"):
                        self.assertIn(str(status), declared, f"{method.upper()} {path}")

    def test_search_response_matches_contract_asset_envelope(self):
        response = self.client.get("/v1/assets", params={"query": "BTC"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        schema = self.contract["paths"]["/v1/assets"]["get"]["responses"]["200"][
            "content"
        ]["application/json"]["schema"]
        self.assertTrue(set(schema["required"]).issubset(payload))
        asset_schema = schema["properties"]["items"]["items"]
        for asset in payload["items"]:
            self.assertTrue(set(asset_schema["required"]).issubset(asset))

    def test_request_and_status_payloads_match_contract(self):
        response = self.client.post(
            "/v1/assets/asset-btc/evaluations",
            headers={"Idempotency-Key": "contract-test-idempotency-001"},
            json={"horizons": ["short", "long"], "methodology_version": "contract-0.1"},
        )
        self.assertEqual(response.status_code, 202)
        request_payload = response.json()
        request_schema = self.contract["paths"]["/v1/assets/{asset_id}/evaluations"][
            "post"
        ]["responses"]["202"]["content"]["application/json"]["schema"]
        self.assertTrue(set(request_schema["required"]).issubset(request_payload))

        status_response = self.client.get(
            f"/v1/evaluation-requests/{request_payload['request_id']}"
        )
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        status_schema = self.contract["paths"]["/v1/evaluation-requests/{request_id}"][
            "get"
        ]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertTrue(set(status_schema["required"]).issubset(status_payload))
        self.assertEqual(status_payload["request_id"], request_payload["request_id"])
        self.assertEqual(status_payload["evaluations"], [])


if __name__ == "__main__":
    unittest.main()
