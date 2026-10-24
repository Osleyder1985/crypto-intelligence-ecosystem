# Issue 9 PoC dependency audit log

**Scope:** Python dependencies used only by the Issue #9 API/PostgreSQL PoCs, not the complete repository or a production deployment.

## First reproducible scan

GitHub Actions run [40057862828](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40057862828) installed the pinned PoC requirements and `pip-audit==2.9.0`. The vulnerability gate failed on 2026-10-24 and identified seven advisories affecting the resolved transitive dependency `starlette==0.46.2` (`PYSEC-2026-161`, `PYSEC-2026-249`, `PYSEC-2026-248`, `PYSEC-2026-1942`, `PYSEC-2026-1941`, `PYSEC-2026-2281`, `PYSEC-2026-2280`). The tool reported fixed versions beginning at 1.0.1/1.1.0/1.3.0/1.3.1 or 0.47.2/0.49.1, depending on advisory.

This is an automated advisory match, not evidence that the PoC was exploited. The result is not suppressed: it is retained as the initial failing baseline.

## Remediation attempt

The direct pin was updated from `fastapi==0.115.12` to `fastapi==0.158.1`, which is a current release line with support for modern Starlette. The follow-up audit is running in [run 40058018130](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058018130). Do not mark the vulnerability gate as passed until this run finishes successfully. API contract, idempotency and worker tests must also pass against the updated dependency graph.

## Licence inventory

The workflow emits a direct/transitive Markdown licence inventory using `pip-licenses==5.0.0` after the vulnerability step, including when that step fails. The output is CI log evidence; it is not legal approval. This scan does not resolve the repository's root licensing decision, rights for external market data, or licences for future client/chart dependencies.

## Remaining scope

- Repeat scan on every requirements change and before release.
- Preserve the final scan output and timestamp; disposition any new advisories explicitly.
- Review GitHub Actions pins separately.
- Complete licence review for the whole repository and future Flutter/React Native/React chart stacks.
- Do not claim a full-repository SBOM, legal clearance, ISO certification, or production security review from this narrow PoC scan.
