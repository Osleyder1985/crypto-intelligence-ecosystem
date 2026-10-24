# Issue 9 dependency and licence review — Python PoC environment

**Review date:** 2026-10-24  
**Workflow evidence:** [Issue 9 PoC dependency security and licence inventory, run 40058494463](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058494463)  
**Artifact:** [issue-9-python-license-inventory.zip](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40058494463/artifacts/12546825286)  
**Scope:** pinned Python stack PoC dependencies and the transitive environment used by the audit job; not the eventual complete product SBOM.

## Automated results

- `pip check`: PASS; no inconsistent installed dependency requirements.
- `pip-audit==2.9.0` against `requirements-stack-poc.txt`: PASS; output said “No known vulnerabilities found” for the advisory data available to that run.
- `pip-licenses==5.0.0`: generated JSON and Markdown inventory for direct and transitive installed packages; the JSON inventory was uploaded as a CI artifact (30-day retention).
- The licence inventory tool reported `UNKNOWN` for some package metadata. This means the installed distribution metadata was not sufficient for an automated label; it does **not** mean the package is unlicensed. Those rows were manually cross-checked against the corresponding PyPI project pages linked below.

## Package licence metadata manually cross-checked

| Distribution / version from audit | Declared licence expression | Official PyPI project page |
|---|---|---|
| CacheControl 0.14.4 | Apache-2.0 | https://pypi.org/project/CacheControl/ |
| Pygments 2.21.0 | BSD-2-Clause | https://pypi.org/project/Pygments/ |
| annotated-doc 0.0.5 | MIT | https://pypi.org/project/annotated-doc/ |
| anyio 4.15.1 | MIT | https://pypi.org/project/anyio/ |
| fastapi 0.158.1 | MIT | https://pypi.org/project/fastapi/ |
| idna 3.20 | BSD-3-Clause | https://pypi.org/project/idna/ |
| msgpack 1.2.3 | Apache-2.0 | https://pypi.org/project/msgpack/ |
| opentelemetry-api 1.45.1 | Apache-2.0 | https://pypi.org/project/opentelemetry-api/ |
| packaging 26.3 | Apache-2.0 OR BSD-2-Clause | https://pypi.org/project/packaging/ |
| pydantic 2.14.1 | MIT | https://pypi.org/project/pydantic/ |
| pydantic_core 2.50.1 | MIT | https://pypi.org/project/pydantic_core/2.50.1/ |
| pyparsing 3.3.3 | MIT | https://pypi.org/project/pyparsing/ |
| starlette 1.9.0 | BSD-3-Clause | https://pypi.org/project/starlette/ |
| typing-inspection 0.4.4 | MIT | https://pypi.org/project/typing-inspection/0.4.4/ |
| typing_extensions 4.16.0 | PSF-2.0 | https://pypi.org/project/typing-extensions/ |
| urllib3 2.8.0 | MIT | https://pypi.org/project/urllib3/ |

The versions above are the versions reported by the run's installed environment. Re-run this review whenever the pinned requirements or resolved transitive versions change. For package pages where the current page now shows a newer release, use the version-specific page or the exact wheel/source distribution metadata for the pinned version before changing this record.

## Direct dependency considerations

- FastAPI, HTTPX and PyYAML are permissive open-source components under their published licences.
- Psycopg 3 is published under LGPL-3.0-only. The pinned extra `psycopg[binary]` also brings a binary distribution with bundled native components; review the exact wheel contents, included notices and obligations for the intended deployment and packaging model before distributing it. Do not assume that all dependencies share one licence.
- This PoC licence review is not legal advice and does not replace review of notices, bundled binaries, fonts, mobile SDKs, chart libraries, or eventual production dependencies.
- The Python licence inventory does not cover Flutter/Dart, Android Gradle plugins, Kotlin, React/Node dependencies, browser assets, Xcode or Apple platform SDK terms.

## Security interpretation

A clean pip-audit run is evidence only for the Python requirements and advisory sources available at the recorded run. It is not a penetration test, proof of exploitability absence, source-code security audit, or guarantee against undisclosed/new vulnerabilities. The audit must be repeated at release and whenever dependency pins change.

## Remaining actions

- [x] Automated Python dependency consistency and known-advisory check for this PoC requirements file.
- [x] Preserve machine-readable Python licence inventory as CI artifact.
- [x] Resolve the `UNKNOWN` labels listed in the emitted inventory against PyPI project licence expressions.
- [ ] Produce a full product SBOM after candidate stacks and their exact dependency locks are selected.
- [ ] Review the complete Flutter/Dart/Android and any selected React/Node dependency graphs before stack ratification.
- [ ] Confirm licence obligations against the intended distribution/deployment model and preserve required notices.
