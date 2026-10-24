"""Small FastAPI + SQLite PoC for immutable evaluation history and idempotent requests.

Non-production only. SQLite is used to make the API behavior reproducible without
requiring a local database service; it does not replace the PostgreSQL PoC.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

Horizon = Literal["short", "medium", "long"]
RequestStatus = Literal["queued", "running", "completed", "failed", "indeterminate"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class EvaluationRequest(BaseModel):
    horizons: list[Horizon] = Field(min_length=1)
    methodology_version: str = Field(default="poc-0.1", min_length=1, max_length=100)


def create_app(database_path: str | Path | None = None) -> FastAPI:
    db_path = str(database_path or os.environ.get("STACK_POC_DB", "stack-poc.sqlite3"))
    app = FastAPI(title="Crypto Intelligence Research API PoC", version="0.1.0")

    def connect() -> sqlite3.Connection:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize() -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(connect()) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    canonical_symbol TEXT NOT NULL,
                    display_name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evaluation_requests (
                    request_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
                    idempotency_key TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN
                      ('queued','running','completed','failed','indeterminate')),
                    created_at TEXT NOT NULL,
                    UNIQUE(asset_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE REFERENCES evaluation_requests(request_id),
                    asset_id TEXT NOT NULL REFERENCES assets(asset_id),
                    horizon TEXT NOT NULL CHECK(horizon IN ('short','medium','long')),
                    methodology_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('complete','partial','indeterminate')),
                    conclusion TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL
                );
            """)
            conn.commit()

    @app.on_event("startup")
    def startup() -> None:
        initialize()

    # Ensure tables exist for ASGI test clients and direct invocation too.
    initialize()

    @app.get("/v1/assets")
    def search_assets(query: str = Query(min_length=1, max_length=100),
                      limit: int = Query(default=20, ge=1, le=100)):
        with closing(connect()) as conn:
            rows = conn.execute(
                """SELECT asset_id, canonical_symbol, display_name FROM assets
                   WHERE canonical_symbol LIKE ? OR display_name LIKE ?
                   ORDER BY canonical_symbol LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        return {"items": [dict(row) for row in rows]}

    @app.get("/v1/assets/{asset_id}/evaluations")
    def list_evaluations(asset_id: str, horizon: Horizon | None = None,
                         limit: int = Query(default=20, ge=1, le=100)):
        with closing(connect()) as conn:
            if not conn.execute("SELECT 1 FROM assets WHERE asset_id=?", (asset_id,)).fetchone():
                raise HTTPException(status_code=404, detail="asset not found")
            sql = """SELECT evaluation_id, asset_id, created_at, horizon,
                     methodology_version, status, conclusion,
                     evidence_refs_json, limitations_json
                     FROM evaluations WHERE asset_id=?"""
            args: list[object] = [asset_id]
            if horizon:
                sql += " AND horizon=?"
                args.append(horizon)
            sql += " ORDER BY created_at DESC, evaluation_id DESC LIMIT ?"
            args.append(limit)
            rows = conn.execute(sql, args).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["evidence_refs"] = json.loads(item.pop("evidence_refs_json"))
            item["limitations"] = json.loads(item.pop("limitations_json"))
            items.append(item)
        return {"items": items}

    @app.post("/v1/assets/{asset_id}/evaluations", status_code=202)
    def request_evaluation(asset_id: str, body: EvaluationRequest,
                           idempotency_key: str = Header(alias="Idempotency-Key", min_length=16, max_length=200)):
        # Keep semantic identity stable regardless of JSON object key ordering.
        request_json = json.dumps(body.model_dump(), sort_keys=True, separators=(",", ":"))
        with closing(connect()) as conn:
            if not conn.execute("SELECT 1 FROM assets WHERE asset_id=?", (asset_id,)).fetchone():
                raise HTTPException(status_code=404, detail="asset not found")
            existing = conn.execute(
                "SELECT request_id, status, request_json FROM evaluation_requests WHERE asset_id=? AND idempotency_key=?",
                (asset_id, idempotency_key),
            ).fetchone()
            if existing:
                if existing["request_json"] != request_json:
                    raise HTTPException(status_code=409, detail="idempotency key reused with different payload")
                return {"request_id": existing["request_id"], "status": existing["status"]}
            request_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO evaluation_requests
                   (request_id, asset_id, idempotency_key, request_json, status, created_at)
                   VALUES (?, ?, ?, ?, 'queued', ?)""",
                (request_id, asset_id, idempotency_key, request_json, utc_now()),
            )
            conn.commit()
        return {"request_id": request_id, "status": "queued"}

    @app.get("/v1/evaluation-requests/{request_id}")
    def get_evaluation_request(request_id: str):
        with closing(connect()) as conn:
            row = conn.execute(
                "SELECT request_id, status FROM evaluation_requests WHERE request_id=?", (request_id,)
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="request not found")
            evaluation = conn.execute(
                """SELECT evaluation_id, asset_id, created_at, horizon, methodology_version,
                          status, conclusion, evidence_refs_json, limitations_json
                   FROM evaluations WHERE request_id=?""", (request_id,)
            ).fetchone()
        result = {"request_id": row["request_id"], "status": row["status"], "evaluation": None, "error": None}
        if evaluation:
            item = dict(evaluation)
            item["evidence_refs"] = json.loads(item.pop("evidence_refs_json"))
            item["limitations"] = json.loads(item.pop("limitations_json"))
            result["evaluation"] = item
        return result

    # Explicit seed helper used by PoC tests only; not exposed as a public route.
    app.state.poc_connect = connect
    return app
