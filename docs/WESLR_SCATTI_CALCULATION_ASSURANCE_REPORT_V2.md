# WESLR SCATTI Calculation Assurance Report V2

This report is rendered from one canonical run-summary JSON.
A separate release verifier independently parses this report and checks every reported numerical value and coefficient-bearing equation.

**Generated at:** 2026-07-14T16:07:52Z
**Git HEAD:** 62e9ba794c780bb37d5472d79ca8c9d91230892d
**Branch:** scatti-calculation-assurance-recovery-20260714

---

## SECTION 1 — Repository Identity

- Branch: `scatti-calculation-assurance-recovery-20260714`
- HEAD: `62e9ba794c780bb37d5472d79ca8c9d91230892d`
- Source hashes: 4 files tracked

---

## SECTION 2 — Explicit Scope Counts

| Scope | File Count | Inclusion Rule |
|-------|-----------|----------------|
| repository_untracked_total | 40 | All git '??' paths |
| scatti_untracked_total | 23 | Paths containing 'scatti', 'calculation_assurance', 'stoichiometric' |
| calculation_assurance_untracked_total | 19 | Explicit allowlist of CA implementation and output files |

---

## SECTION 3 — Canonical Artifact Counts

- Total records: 24
- All category sums pass: True

### By Artifact Type

- dataset: 10
- documentation: 2
- report: 9
- runtime_module: 1
- script: 1
- test: 1

### By Implementation Status

- implemented: 24

### By Execution Status

- executed: 11
- not_executed: 13

### By Evidence Class

- claim_boundary: 1
- derived_analysis: 8
- external_source: 4
- governance: 5
- metadata_only: 2
- primary_computation: 4

- Tracked: 19
- Untracked: 5
- Existing: 24
- Missing: 0

---

## SECTION 4 — Coefficient-Explicit Certificates

### Reaction Balance Certificates

| Canonical Equation | Proposer | Verifier | Residual Zero | Final Status |
|--------------------|----------|----------|---------------|--------------|
| `CaO + Sc2TiO5 -> CaSc2TiO6` | balanced | balanced | ✅ | verified |
| `2 CaO + Sc4Ti2O10 -> 2 CaSc2TiO6` | balanced | balanced | ✅ | verified |
| `CaSc2O4 + TiO2 -> CaSc2TiO6` | balanced | balanced | ✅ | verified |
| `CaTiO3 + Sc2O3 -> CaSc2TiO6` | balanced | balanced | ✅ | verified |
| `CaO + Sc4Ti2O10 -> CaSc4Ti2O11` | balanced | balanced | ✅ | verified |

**Note:** Route 5 (Sc4Ti2O10 + CaO -> CaSc4Ti2O11) is elementally balanced as its own reaction but does NOT produce CaSc2TiO6. See target-multiple checks below.

### Target-Multiple Check Certificates

| Check | Candidate | Target | Exact Multiple | Required Multiplier | Final Status |
|-------|-----------|--------|----------------|---------------------|--------------|
| target_multiple | CaSc4Ti2O11 | CaSc2TiO6 | ❌ | 0 | rejected_by_invariant |
| target_multiple | Ca2Sc4Ti2O12 | CaSc2TiO6 | ✅ | 2.0 | verified |
| target_multiple | Sc4Ti2O10 | CaSc2TiO6 | ❌ | 0 | rejected_by_invariant |

---

## SECTION 5 — Target-Multiple Checks (Detail)

- CaSc4Ti2O11 is not an integer multiple of CaSc2TiO6: rejected_by_invariant
- Ca2Sc4Ti2O12 is exactly 2 × CaSc2TiO6: verified
- Sc4Ti2O10 is not an integer multiple of CaSc2TiO6: rejected_by_invariant

---

## SECTION 6 — V1 Discrepancies Resolved

| V1 Issue | Resolution in V2 |
|----------|-----------------|
| Artifact-type counts sum to 23 not 24 | V2 counts all verified: all category sums pass |
| Rendered report counts differ from conversational report | V2 uses one canonical summary JSON as single source |
| 'implemented' and 'executed' conflated | V2 separates implementation_status from execution_status |
| Scope 'untracked files' ambiguous | V2 names every scope explicitly |
| Coefficient-free equations | V2 displays all equations with coefficients |
| Target-multiple checks presented as reactions | V2 separates reaction_balance from target_multiple_check |

---

## SECTION 7 — Test Receipt

- Pytest commands: 1
- Passed: 1
- Failed: 0

---

## SECTION 8 — Release Verifier Result

See release_verification_receipt_v2.json for full result.

---

## SECTION 9 — Deterministic Bundle Rebuild

See handoff bundle section below.

---

## SECTION 10 — Bundle V2

- V1 bundle exists: True
- V1 bundle SHA256: c8e25c7655f1495bbae0ab596574f5717705bbd89bfbb25bacafc4535c8a865b
- V1 bundle size: 41633 bytes

---

## SECTION 11 — Git Status

```
?? artifacts/
?? cache/
?? checkpoints/arc_agi2_v1/
?? data/scatti_candidates/calculation_assurance/
?? data/scatti_candidates/calculation_assurance_v2/
?? data/scatti_candidates/scatti_evidence_ledger_v1.json
?? data/scatti_candidates/scatti_implementation_inventory_v1.json
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.json
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.md
?? docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V1.md
?? docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V2.md
?? docs/WESLR_SCATTI_IMPLEMENTATION_AND_EVIDENCE_AUDIT_V1.md
?? docs/b_experiment_results_v1.json
?? docs/b_experiment_results_v2.json
?? docs/b_experiment_results_v3.json
?? docs/five_task_pilot_results_v1.json
?? docs/focused_experiment_results_v1.json
?? docs/focused_experiment_results_v2.json
?? docs/isolated_package_receipts_v1.json
?? docs/pilot_experiment_results_v1.json
?? run_five_task_pilot.py
?? scripts/generate_canonical_run_summary_v2.py
?? scripts/generate_preflight_scope_counts_v2.py
?? scripts/generate_stoichiometric_certificates.py
?? scripts/generate_stoichiometric_certificates_v2.py
?? scripts/generate_validation_receipt_v2.py
?? scripts/rebuild_inventory_v2.py
?? scripts/render_scatti_calculation_assurance_report.py
?? scripts/render_scatti_calculation_assurance_report_v2.py
?? scripts/scatti_audit_consistency_check.py
?? scripts/verify_scatti_calculation_assurance_release_v2.py
?? weslr/modules/calculation_assurance.py
?? weslr/modules/materials_stoichiometric_route_engine.py
?? weslr/modules/materials_stoichiometric_route_verifier.py
?? weslr/tests/test_arc_agi2_synthesis_core_integration_audit_v1.py
?? weslr/tests/test_calculation_assurance.py
?? weslr/tests/test_materials_stoichiometric_route_engine.py
?? weslr/tests/test_materials_stoichiometric_route_verifier.py
?? weslr/tests/test_scatti_audit_consistency.py
?? weslr/tests/test_scatti_calculation_assurance_release_v2.py
```

---

## SECTION 12 — Next Action

**A. Transfer V2 bundle to Ubuntu for cross-host reconciliation.**

Prerequisites:
- Release verifier = release_verified
- Bundle rebuild hashes agree
- No unresolved count mismatch
- No ambiguous equations
- No manifest mismatch
