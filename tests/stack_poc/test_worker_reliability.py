"""Concurrency and transaction-recovery tests for the SQLite worker PoC.

These tests exercise local SQLite transaction semantics only; they are not a
production multi-host queue or process-kill chaos test.
"""
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.stack_poc.research_api import create_app
from scripts.stack_poc.research_worker import process_next_request


class WorkerReliabilityPocTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "worker.sqlite3"
        self.app = create_app(self.db, bearer_token="test-token")
        self.client = TestClient(
            self.app, headers={"Authorization": "Bearer test-token"}
        )
        with self.app.state.poc_connect() as conn:
            conn.execute(
                "INSERT INTO assets(asset_id, canonical_symbol, display_name) VALUES (?, ?, ?)",
                ("asset-btc", "BTC", "Bitcoin"),
            )
            conn.commit()

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def _enqueue(self, index):
        response = self.client.post(
            "/v1/assets/asset-btc/evaluations",
            json={"horizons": ["short", "long"], "methodology_version": "poc-0.1"},
            headers={"Idempotency-Key": f"worker-concurrency-key-{index:04d}"},
        )
        self.assertEqual(response.status_code, 202)
        return response.json()["request_id"]

    def test_concurrent_workers_claim_each_request_once(self):
        request_ids = {self._enqueue(i) for i in range(12)}
        with ThreadPoolExecutor(max_workers=8) as pool:
            processed = list(pool.map(lambda _: process_next_request(self.db), range(16)))

        processed_ids = [request_id for request_id in processed if request_id is not None]
        self.assertEqual(len(processed_ids), 12)
        self.assertEqual(set(processed_ids), request_ids)
        self.assertEqual(len(set(processed_ids)), len(processed_ids))

        with self.app.state.poc_connect() as conn:
            statuses = conn.execute(
                "SELECT status, COUNT(*) AS count FROM evaluation_requests GROUP BY status"
            ).fetchall()
            evaluations = conn.execute(
                "SELECT request_id, horizon, COUNT(*) AS count FROM evaluations GROUP BY request_id, horizon"
            ).fetchall()
        self.assertEqual({row["status"]: row["count"] for row in statuses}, {"indeterminate": 12})
        self.assertEqual(len(evaluations), 24)
        self.assertTrue(all(row["count"] == 1 for row in evaluations))

    def test_rolled_back_claim_remains_eligible_for_recovery(self):
        request_id = self._enqueue(99)
        # Model an interrupted transaction: claim is changed but not committed.
        with self.app.state.poc_connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE evaluation_requests SET status='running' WHERE request_id=?",
                (request_id,),
            )
            conn.rollback()

        with self.app.state.poc_connect() as conn:
            status = conn.execute(
                "SELECT status FROM evaluation_requests WHERE request_id=?", (request_id,)
            ).fetchone()["status"]
        self.assertEqual(status, "queued")
        self.assertEqual(process_next_request(self.db), request_id)
        self.assertIsNone(process_next_request(self.db))

        with self.app.state.poc_connect() as conn:
            status = conn.execute(
                "SELECT status FROM evaluation_requests WHERE request_id=?", (request_id,)
            ).fetchone()["status"]
            count = conn.execute(
                "SELECT COUNT(*) AS count FROM evaluations WHERE request_id=?", (request_id,)
            ).fetchone()["count"]
        self.assertEqual(status, "indeterminate")
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
