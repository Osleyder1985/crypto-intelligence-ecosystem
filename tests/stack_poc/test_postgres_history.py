"""PostgreSQL integration PoC: historical ordering and immutable evaluations."""
import os
import unittest
import uuid
from pathlib import Path

import psycopg

DATABASE_URL = os.environ.get("STACK_POC_POSTGRES_DSN")
SCHEMA = Path("scripts/stack_poc/postgres_schema.sql")


@unittest.skipUnless(DATABASE_URL, "requires STACK_POC_POSTGRES_DSN PostgreSQL service")
class PostgreSQLHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(DATABASE_URL, autocommit=True)
        cls.conn.execute(SCHEMA.read_text(encoding="utf-8"), prepare=False)
        cls.conn.execute("DELETE FROM stack_poc_evaluations")
        cls.conn.execute("DELETE FROM stack_poc_assets")
        cls.conn.execute(
            "INSERT INTO stack_poc_assets(asset_id, canonical_symbol, display_name) VALUES (%s, %s, %s)",
            ("asset-btc", "BTC", "Bitcoin"),
        )

    @classmethod
    def tearDownClass(cls):
        cls.conn.execute("DELETE FROM stack_poc_evaluations")
        cls.conn.execute("DELETE FROM stack_poc_assets")
        cls.conn.close()

    def test_history_is_append_only_and_ordered(self):
        older_id, newer_id = uuid.uuid4(), uuid.uuid4()
        self.conn.execute(
            """INSERT INTO stack_poc_evaluations
               (evaluation_id, asset_id, horizon, methodology_version, created_at,
                status, conclusion, evidence_refs, limitations)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)""",
            (older_id, "asset-btc", "short", "poc-0.1", "2026-10-23T10:00:00Z",
             "partial", "fixture result", '["fixture:btc"]', '["synthetic data"]'),
        )
        self.conn.execute(
            """INSERT INTO stack_poc_evaluations
               (evaluation_id, asset_id, horizon, methodology_version, created_at,
                status, conclusion, evidence_refs, limitations)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)""",
            (newer_id, "asset-btc", "long", "poc-0.2", "2026-10-23T11:00:00Z",
             "indeterminate", "insufficient evidence", '["fixture:btc-v2"]', '["synthetic data"]'),
        )
        rows = self.conn.execute(
            """SELECT evaluation_id, horizon, methodology_version
               FROM stack_poc_evaluations WHERE asset_id=%s
               ORDER BY created_at DESC, evaluation_id DESC""",
            ("asset-btc",),
        ).fetchall()
        self.assertEqual([row[0] for row in rows], [newer_id, older_id])
        self.assertEqual([row[1] for row in rows], ["long", "short"])
        with self.assertRaises(psycopg.errors.RaiseException):
            self.conn.execute(
                "UPDATE stack_poc_evaluations SET conclusion='overwritten' WHERE evaluation_id=%s",
                (older_id,),
            )
        with self.assertRaises(psycopg.errors.RaiseException):
            self.conn.execute(
                "DELETE FROM stack_poc_evaluations WHERE evaluation_id=%s", (older_id,)
            )


if __name__ == "__main__":
    unittest.main()
