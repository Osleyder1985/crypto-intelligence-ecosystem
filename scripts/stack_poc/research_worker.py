"""Persisted SQLite PoC worker; abstains instead of inventing an analysis."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path


def process_next_request(database_path: str | Path) -> str | None:
    """Process one queued request atomically and persist indeterminate results.

    This deliberately does not call external providers or claim analytical output.
    Once a real evaluator is integrated, replace the abstention body and retain
    the transaction/idempotency behavior.
    """
    db_path = str(database_path)
    with closing(sqlite3.connect(db_path, timeout=5, isolation_level=None)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """SELECT request_id, asset_id, request_json FROM evaluation_requests
               WHERE status='queued' ORDER BY created_at, request_id LIMIT 1"""
        ).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return None

        request_id = row["request_id"]
        payload = json.loads(row["request_json"])
        conn.execute(
            "UPDATE evaluation_requests SET status='running' WHERE request_id=? AND status='queued'",
            (request_id,),
        )
        created_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat().replace("+00:00", "Z")
        for horizon in payload["horizons"]:
            conn.execute(
                """INSERT OR IGNORE INTO evaluations
                   (evaluation_id, request_id, asset_id, horizon, methodology_version,
                    created_at, status, conclusion, evidence_refs_json, limitations_json)
                   VALUES (?, ?, ?, ?, ?, ?, 'indeterminate', ?, '[]', ?)""",
                (
                    str(uuid.uuid4()), request_id, row["asset_id"], horizon,
                    payload["methodology_version"], created_at,
                    "No investment conclusion: analysis engine is not integrated in this PoC.",
                    json.dumps(["analysis_engine_not_integrated"]),
                ),
            )
        conn.execute(
            "UPDATE evaluation_requests SET status='indeterminate' WHERE request_id=?",
            (request_id,),
        )
        conn.execute("COMMIT")
        return request_id
