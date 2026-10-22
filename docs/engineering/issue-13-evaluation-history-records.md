# Evaluation history records and comparison — Issue #13 (RF-01/RF-02)

## Scope

The module `scripts/market_selection/evaluation_record.py` introduces a local proof of concept for immutable evaluation records, source-input archiving and conservative comparison. It does **not** implement a central database, authenticated multi-user persistence, retention/backup/restore, a ranking, or a prediction model; those require platform architecture and operational controls.

## Record creation

A JSON manifest provides asset/market identity, horizon, methodology ID/version and parameters, code version/Git SHA, quality, results, uncertainty/warnings, prior evaluation ID, and one or more source artifact paths with source/endpoint/window metadata.

The builder:
1. Computes SHA-256 and byte size of each source artifact and archives the exact bytes at `archive/sha256/<digest>.bin`.
2. Uses exclusive file creation for content-addressed blobs and evaluation records; it never silently overwrites an existing artifact or evaluation.
3. Computes a content-derived `evaluation_id` and a separate `record_sha256`.
4. Marks `orders_submitted=false` and records persistence mode as `LOCAL_CONTENT_ADDRESSED_ARCHIVE`.

A later evaluation may set `previous_evaluation_id`; this is a link, not a claim that a chain is complete or signed. Verification checks record digests and, when given the archive root, every referenced source blob.

## Comparison rules

The comparator separates:
- scope compatibility: asset, market and horizon;
- methodology/parameter changes;
- implementation/code changes;
- source-set changes;
- declared data-quality changes;
- source input hash changes;
- numeric metric deltas, including absolute delta and relative percentage where the old value is non-zero.

It labels results `COMPARABLE_OBSERVED_CHANGE_CANDIDATE` only when scope, methodology, implementation, source set and declared quality match while input hashes and results change. This is not causal attribution. A changed methodology, implementation, source set, quality state or scope yields a mixed/incompatible status. Changed results with identical input hashes are flagged as inconsistent.

## Limitations

- The archive is local filesystem storage, not a durable central platform. GitHub artifact retention alone is not a permanent history service.
- Source metadata and analysis outputs are supplied by the caller; this module verifies byte integrity but does not prove that the source is authoritative, that the method is valid, or that metrics are economically meaningful.
- Numeric differences are descriptive. They do not prove market causality, forecast accuracy or profitability.
- A ranking must not be built from these records until methodology comparability, freshness, uncertainty, eligibility and historical validation are specified.
- No private credentials, account data, or trading actions are required.
