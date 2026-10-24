-- PostgreSQL candidate schema for Issue #9 PoC; not a production migration.
CREATE TABLE IF NOT EXISTS stack_poc_assets (
    asset_id TEXT PRIMARY KEY,
    canonical_symbol TEXT NOT NULL,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stack_poc_evaluations (
    evaluation_id UUID PRIMARY KEY,
    asset_id TEXT NOT NULL REFERENCES stack_poc_assets(asset_id),
    horizon TEXT NOT NULL CHECK (horizon IN ('short', 'medium', 'long')),
    methodology_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('complete', 'partial', 'indeterminate')),
    conclusion TEXT NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS stack_poc_evaluations_asset_time_idx
    ON stack_poc_evaluations (asset_id, created_at DESC, evaluation_id DESC);

CREATE OR REPLACE FUNCTION stack_poc_reject_evaluation_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'historical evaluations are append-only';
END;
$$;

DROP TRIGGER IF EXISTS stack_poc_evaluations_no_update ON stack_poc_evaluations;
CREATE TRIGGER stack_poc_evaluations_no_update
BEFORE UPDATE OR DELETE ON stack_poc_evaluations
FOR EACH ROW EXECUTE FUNCTION stack_poc_reject_evaluation_mutation();
