"""Executable contract/history/idempotency tests for the stack-selection API PoC."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.stack_poc.research_api import create_app


class ResearchApiPocTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "research.sqlite3"
        self.app = create_app(self.db)
        self.client = TestClient(self.app)
        with self.app.state.poc_connect() as conn:
            conn.execute(
                "INSERT INTO assets(asset_id, canonical_symbol, display_name) VALUES (?, ?, ?)",
                ("asset-btc", "BTC", "Bitcoin"),
            )
            conn.commit()

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def test_search_asset_and_empty_result_shape(self):
        response = self.client.get("/v1/assets", params={"query": "BTC"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["asset_id"], "asset-btc")
        self.assertEqual(self.client.get("/v1/assets", params={"query": "no-match"}).json(), {"items": []})

    def test_evaluation_request_is_idempotent_and_conflicts_on_changed_payload(self):
        headers = {"Idempotency-Key": "issue9-test-key-0001"}
        payload = {"horizons": ["short", "long"], "methodology_version": "poc-0.1"}
        first = self.client.post("/v1/assets/asset-btc/evaluations", json=payload, headers=headers)
        second = self.client.post("/v1/assets/asset-btc/evaluations", json=payload, headers=headers)
        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json(), second.json())
        changed = self.client.post(
            "/v1/assets/asset-btc/evaluations",
            json={"horizons": ["medium"], "methodology_version": "poc-0.1"},
            headers=headers,
        )
        self.assertEqual(changed.status_code, 409)

    def test_unknown_asset_and_request_return_404(self):
        self.assertEqual(
            self.client.post(
                "/v1/assets/no-such-asset/evaluations",
                json={"horizons": ["short"]},
                headers={"Idempotency-Key": "issue9-test-key-0002"},
            ).status_code,
            404,
        )
        self.assertEqual(self.client.get("/v1/evaluation-requests/not-a-uuid").status_code, 404)

    def test_historical_evaluations_are_append_only_and_filterable(self):
        request = self.client.post(
            "/v1/assets/asset-btc/evaluations",
            json={"horizons": ["short"], "methodology_version": "poc-0.1"},
            headers={"Idempotency-Key": "issue9-test-key-0003"},
        ).json()
        with self.app.state.poc_connect() as conn:
            conn.execute(
                """INSERT INTO evaluations
                   (evaluation_id, request_id, asset_id, horizon, methodology_version,
                    created_at, status, conclusion, evidence_refs_json, limitations_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("eval-1", request["request_id"], "asset-btc", "short", "poc-0.1",
                 "2026-10-23T10:00:00Z", "partial", "insufficient fixture evidence",
                 '["fixture:btc"]', '["synthetic test data"]'),
            )
            conn.execute("UPDATE evaluation_requests SET status='completed' WHERE request_id=?",
                         (request["request_id"],))
            conn.commit()
            # A second evaluation is stored separately; no UPDATE overwrites eval-1.
            conn.execute(
                """INSERT INTO evaluations
                   (evaluation_id, request_id, asset_id, horizon, methodology_version,
                    created_at, status, conclusion, evidence_refs_json, limitations_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("eval-2", request["request_id"] + "-second", "asset-btc", "long", "poc-0.2",
                 "2026-10-23T11:00:00Z", "indeterminate", "not enough evidence",
                 '["fixture:btc-v2"]', '["synthetic test data"]'),
            )
            # The second row needs a valid parent request, so insert its parent first if needed.
            conn.rollback()
            # Instead, keep the request table relationally valid and create a distinct request.
            conn.execute(
                """INSERT INTO evaluation_requests
                   (request_id, asset_id, idempotency_key, request_json, status, created_at)
                   VALUES (?, ?, ?, ?, 'completed', ?)""",
                (request["request_id"] + "-second", "asset-btc", "issue9-history-second",
                 '{"horizons":["long"],"methodology_version":"poc-0.2"}', "2026-10-23T10:59:00Z"),
            )
            conn.execute(
                """INSERT INTO evaluations
                   (evaluation_id, request_id, asset_id, horizon, methodology_version,
                    created_at, status, conclusion, evidence_refs_json, limitations_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("eval-2", request["request_id"] + "-second", "asset-btc", "long", "poc-0.2",
                 "2026-10-23T11:00:00Z", "indeterminate", "not enough evidence",
                 '["fixture:btc-v2"]', '["synthetic test data"]'),
            )
            conn.commit()
        response = self.client.get("/v1/assets/asset-btc/evaluations")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual([item["evaluation_id"] for item in items], ["eval-2", "eval-1"])
        self.assertEqual(self.client.get(
            "/v1/assets/asset-btc/evaluations", params={"horizon": "short"}
        ).json()["items"][0]["evaluation_id"], "eval-1")


if __name__ == "__main__":
    unittest.main()
