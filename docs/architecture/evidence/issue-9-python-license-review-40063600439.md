# Issue 9 Python dependency security and licence triage — run 40063600439

- Workflow: https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063600439
- Commit: `05c33ddc5ad091973e9d8d82ce2abd3588385db8`
- Result: PASS for `pip check`, `pip-audit`, licence inventory generation, and the four unit tests for conservative licence triage.
- Security: `pip-audit` reported **no known vulnerabilities** in the audited `requirements-stack-poc.txt` environment at run time. This is a point-in-time advisory scan, not a full code audit or a guarantee against unknown vulnerabilities.
- Inventory: 42 installed Python distributions, including transitive dependencies. Raw inventory and triage JSON are preserved in artifact [issue-9-python-license-inventory, ID 12548740668](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/actions/runs/40063600439).

## Triage output

| Result | Count | Meaning |
|---|---:|---|
| Licence expression identified from version-bound captured licence text | 15 | The exact package/version's captured text was matched to an SPDX expression; re-review if version changes |
| Metadata and classifier aligned | 14 | Declared values agree, but legal obligations/notices still need review |
| Metadata only | 2 | Metadata exists but classifier is absent |
| Classifier only | 7 | Classifier exists but metadata is absent |
| Manual review required | 4 | Not production-cleared |
| Missing captured licence text | 3 | `license-expression 30.4.4`, `packageurl-python 0.17.6`, `pip-requirements-parser 32.0.1` |
| Missing separate NOTICE file/text | 39 | Not automatically a violation; check the licence text and intended distribution obligations |

The four manual-review items are:
1. `license-expression 30.4.4`: metadata says Apache-2.0, but the installed distribution inventory did not include licence text. The official PyPI release metadata identifies Apache-2.0: https://pypi.org/project/license-expression/30.4.4/
2. `packageurl-python 0.17.6`: metadata says MIT and the classifier says MIT License, but the installed distribution inventory did not include licence text. The official PyPI release metadata identifies MIT: https://pypi.org/project/packageurl-python/0.17.6/ . The upstream repository lists `mit.LICENSE`: https://github.com/package-url/packageurl-python
3. `pip-requirements-parser 32.0.1`: metadata says MIT, but the installed distribution inventory did not include licence text. The official PyPI release metadata identifies MIT: https://pypi.org/project/pip-requirements-parser/32.0.1/
4. `typing_extensions 4.16.0`: a licence file is present, but it contains the Python licence-history bundle and the inventory does not identify one unambiguous package-level SPDX expression. This requires manual confirmation rather than an inferred licence.

## Maintenance and distribution disposition

The workflow now preserves both raw `pip-licenses` output and a conservative JSON triage report. Four tests ensure that version-bound overrides do not silently carry forward to new versions, and that missing licence text remains unresolved. The report deliberately does not claim legal approval.

**Disposition: security scan PASS; dependency consistency PASS; licence triage PARTIAL.** Do not mark licence review complete or ratify ADR-0001 until the four manual-review items are resolved, the applicable attribution/copyright/NOTICE obligations are recorded, and the intended product distribution model is known.
