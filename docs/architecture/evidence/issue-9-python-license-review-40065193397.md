# Updated Python dependency security and licence triage — run 40065193397

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40065193397
- Commit: `a95146f8b78a4d82ccb4faf88b2a0b9de270bb7b`
- Result: PASS for dependency consistency, `pip-audit`, inventory generation and unit tests.
- Security: no known vulnerabilities reported by `pip-audit` for the audited Python environment at scan time.
- Inventory: 42 installed distributions; raw inventory and triage report in artifact [12548732148](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40065193397).

## Updated triage counts

| Result | Count |
|---|---:|
| Expression identified from version-bound captured licence text | 15 |
| Expression identified from version-pinned upstream source metadata | 1 |
| Metadata and classifier aligned, obligations still need review | 14 |
| Metadata only | 2 |
| Classifier only | 7 |
| Manual review required | 3 |
| Missing captured licence text | 3 |
| No separate NOTICE file/text | 39 |

The version-tagged upstream `pyproject.toml` for [typing_extensions 4.16.0](https://github.com/python/typing_extensions/blob/4.16.0/pyproject.toml) declares `license = "PSF-2.0"`. The triage now records this source URL and reduces the manual-review count from four to three.

The three unresolved packages remain:
- `license-expression 30.4.4` — metadata declares Apache-2.0, but the installed distribution inventory has no captured licence text/file.
- `packageurl-python 0.17.6` — metadata/classifier declare MIT, but the installed distribution inventory has no captured licence text/file.
- `pip-requirements-parser 32.0.1` — metadata declares MIT, but the installed distribution inventory has no captured licence text/file.

No separate NOTICE file/text for 39 packages is not automatically a violation; review each licence's obligations against the intended distribution model. This remains a partial legal review, not formal legal approval. Resolve the three missing upstream texts and record attribution/NOTICE obligations before production ratification.
