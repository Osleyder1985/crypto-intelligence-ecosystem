# Issue 9 decision matrix — scoring and sensitivity protocol

**Status:** method control; not a final technology decision.  
**Applies to:** `docs/architecture/stack-technology-evaluation.md` and `scripts/stack_poc/sensitivity_analysis.py`.

## Scoring anchors (1–5)

Each candidate/criterion score must include a stable evidence reference (CI run + artifact/report path, a reproducible measurement, or a versioned official source). A score without evidence is invalid and must remain N/E.

| Score | Interpretation | Evidence requirement |
|---:|---|---|
| 1 | Fails a material requirement or has an evidenced blocking risk | Reproducible failure, unmet mandatory requirement, or documented blocker |
| 2 | Weak fit; material gaps or costly workarounds remain | PoC passes only with limitations that materially impair the requirement |
| 3 | Adequate baseline, with material unresolved gaps | PoC demonstrates the core path but limitations are explicitly recorded |
| 4 | Strong fit with bounded, understood gaps | Repeated/reproducible evidence covers the criterion and major failure modes |
| 5 | Best evidenced fit for the stated requirement, with low residual uncertainty | Comparable evidence covers the full criterion; no material unreviewed gap remains |

Do not award a 5 merely because a workflow passes. A CI pass proves only the tested scope.

## Evidence and N/E rules

- `N/E` is not zero and is not a neutral score. It means insufficient evidence to score.
- Do not impute a candidate's missing score from another candidate, a framework's reputation, or a hosted runner result.
- Partial scores may be used to prioritize the next experiment, but never to rank candidates when evidence coverage differs.
- All candidates must be assessed against the same criteria and weight set before a full ranking is calculated.
- If a criterion is not applicable (for example, Android-only Kotlin does not cover iOS), record the architecture-level consequence; do not silently omit that platform or renormalize its weight away.

## Weight sensitivity

The current script runs one-at-a-time ±20% perturbations for every criterion while keeping the other weights unchanged, then normalizes by the new total. This is a local robustness diagnostic, not a probability model and not a substitute for alternative stakeholder weight profiles.

Before ratification, run at least these scenarios on the complete, evidenced matrix:
1. Approved baseline weights.
2. Equal weights across all criteria.
3. Product-functionality emphasis: functional contracts and charts/series receive greater relative weight.
4. Operational-risk emphasis: security/privacy, maintenance, licences and operating cost receive greater relative weight.
5. Delivery-constraint emphasis: local resources/build and maintainability receive greater relative weight.

Publish each scenario's exact weights, score vector, rank order, rank reversals and criteria driving reversals. Do not call a ranking "stable" if any required criterion is N/E or if an alternative architecture omits a required platform.

## Current disposition

The currently documented input is intentionally incomplete. It contains evidence for selected chart, persistence and CI criteria, while several criteria and the user's actual Windows 11 build measurements remain N/E. The script must return `status=incomplete`, `ranking=[]` and `sensitivity=[]` for the full matrix until every candidate/criterion has a 1–5 score and an evidence reference. The separate three-criterion sensitivity subset is diagnostic only and cannot ratify ADR-0001.

## Ratification gate

Ratify ADR-0001 only when:
- the shared Android runtime comparison passes and its artifacts prove visible canonical fixture rendering for each candidate;
- the user's actual Windows environment has a captured report, or the owner explicitly accepts a documented N/E limitation;
- security, support lifecycle, build-tool dependencies and third-party licence obligations have documented dispositions;
- the full matrix is evidenced and the required weight scenarios are published;
- all required CI checks for the PR pass, and the owner explicitly approves the final decision.

A legal/licence inventory is evidence collection, not a legal opinion or proof of compliance. Do not claim ISO certification or conformity based solely on this protocol.
