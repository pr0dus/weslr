# WESLR SCATTI Calculation Assurance Report V1

This report contains no manually entered calculated totals.
Numerical totals, classifications and certificates were rendered from machine-readable evidence.

**Generated at:** 2026-07-14T15:47:20Z
**Git HEAD:** 62e9ba794c780bb37d5472d79ca8c9d91230892d
**Git branch:** scatti-calculation-assurance-recovery-20260714

---

## SECTION 1 — Recovery Branch

- Branch: `scatti-calculation-assurance-recovery-20260714`
- HEAD: `62e9ba794c780bb37d5472d79ca8c9d91230892d`
- Tracked modifications: None
- Untracked files: 5 in calculation_assurance/

---

## SECTION 2 — Non-Self-Trusting Architecture

| Component | Module | Role |
|-----------|--------|------|
| Proposer | `materials_stoichiometric_route_engine.py` | Computes reaction balance |
| Independent verifier | `materials_stoichiometric_route_verifier.py` | Recomputes through different implementation |
| Invariants | `calculation_assurance.py` | Elemental residual, target multiple checks |
| Acceptance rule | All three must agree | verified only if proposer=verifier AND residual=0 |
| Abstention rule | Any disagreement | abstain_due_to_verification_disagreement |

---

## SECTION 3 — Stoichiometric Certificates

| Proposition | Proposer | Verifier | Residual Zero | Final Status |
|-------------|----------|----------|---------------|--------------|
| CaO, Sc2TiO5 → CaSc2TiO6 | balanced | balanced | ✅ | verified |
| CaO, Sc4Ti2O10 → CaSc2TiO6 | balanced | balanced | ✅ | verified |
| CaSc2O4, TiO2 → CaSc2TiO6 | balanced | balanced | ✅ | verified |
| CaTiO3, Sc2O3 → CaSc2TiO6 | balanced | balanced | ✅ | verified |
| CaO, Sc4Ti2O10 → CaSc4Ti2O11 | balanced | balanced | ✅ | verified |
| CaSc4Ti2O11 → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |
| Sc2TiO5 → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |
| CaO → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |
| CaO, Sc2O3 → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |
| NaCl → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |
| Al2O3, MgO → CaSc2TiO6 | unbalanced | unbalanced | ❌ | rejected_by_invariant |

---

## SECTION 4 — Audit Inconsistencies Found

- **category_sum_mismatch**: Reported implemented count 24 != actual 16
- **category_sum_mismatch**: Reported executed count 12 != actual 0
- **supersession_count_mismatch**: Inventory reports 0 superseded but evidence ledger has 2 entries with supersedes
- **external_evidence_not_imported**: Commit 2d40b9d not reachable in this snapshot
- **external_evidence_not_imported**: Commit 55342bb not reachable in this snapshot

---

## SECTION 5 — Corrected Counts

All counts are read from generated JSON.

- Total artifacts: 24

### Artifact Type Counts

- dataset: 10
- documentation: 2
- report: 9
- runtime_module: 1
- script: 1
- test: 1

### Implementation Status Counts

- executed: 8
- implemented: 16

### Evidence Class Counts

- claim_boundary: 1
- derived_analysis: 8
- external_source: 4
- governance: 5
- metadata_only: 2
- primary_computation: 4

---

## SECTION 6 — Evidence-Scope Reconciliation

- Locally verified: 3 entries
- Known external but not imported: Materials Project query results on Ubuntu host (commits 2d40b9d, 55342bb)
- Unresolved: 2 entries
- Superseded: 2 entries with supersedes

### Proposed Reconciliation Corrections

- **CORR-001**: Materials Project exact-formula querying was reportedly executed on Ubuntu but its evidence is not imported here. Local status must reflect that the evidence exists externally but is not locally verifiable.
- **CORR-002**: Same as CORR-001. The local snapshot cannot certify database crosscheck status without imported evidence.
- **CORR-003**: Chemical plausibility is supported by stoichiometric analysis but does not establish geometric feasibility, stability, or synthesis. 'passed_gate' overstates the available evidence for a full chemical plausibility gate.
- **CORR-004**: The parent-derived negative conclusion is superseded due to formula-unit scaling bug. This should be explicitly recorded.
- **CORR-005**: The structure_generation stage contains valid earlier negative results (hand-built coordinates failed) AND the scaling-bug result (which is superseded). The stage status should reflect that the negative result is partially superseded by the corrected stoichiometric analysis.
- **CORR-006**: E006 (hand-built structure candidates) remains valid as executed_negative. The hand-built coordinates genuinely failed geometric validation. This is not superseded by the stoichiometric correction.
- **CORR-007**: E007 (parent-motif construction) was based on the scaling-bug result. The parent-motif construction attempt itself failed geometrically, but the stoichiometric premise was invalid. This entry should be marked superseded.
- **CORR-008**: The global SCATTI state cannot be certified until cross-host evidence (commits 2d40b9d, 55342bb, MP-parent experiment artifacts) is reconciled. This snapshot is a partial view.

---

## SECTION 7 — Test Results

See validation receipt for exact values.

---

## SECTION 8 — Determinism

- Certificate hashes: 11 certificates with SHA256
- Repeated execution produces identical JSON (tested)
- Disagreement tests: proposer/verifier disagreement forces abstention

---

## SECTION 9 — Handoff Bundle

See artifacts/scatti_calculation_assurance_handoff_v1*

---

## SECTION 10 — Files Created or Modified

- `weslr/modules/calculation_assurance.py` (9428 bytes)
- `weslr/modules/materials_stoichiometric_route_verifier.py` (13556 bytes)
- `scripts/generate_stoichiometric_certificates.py` (11796 bytes)
- `scripts/scatti_audit_consistency_check.py` (15576 bytes)
- `scripts/render_scatti_calculation_assurance_report.py` (9032 bytes)
- `data/scatti_candidates/calculation_assurance/pre_modification_manifest_v1.json` (3152 bytes)
- `data/scatti_candidates/calculation_assurance/stoichiometric_certificates_v1.json` (27174 bytes)
- `data/scatti_candidates/calculation_assurance/audit_consistency_v1.json` (2352 bytes)
- `data/scatti_candidates/calculation_assurance/audit_consistency_v1.md` (1577 bytes)
- `data/scatti_candidates/calculation_assurance/evidence_ledger_reconciliation_proposal_v1.json` (4772 bytes)

---

## SECTION 11 — Git Status

```
?? cache/
?? checkpoints/arc_agi2_v1/
?? data/scatti_candidates/calculation_assurance/
?? data/scatti_candidates/scatti_evidence_ledger_v1.json
?? data/scatti_candidates/scatti_implementation_inventory_v1.json
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.json
?? data/scatti_candidates/scatti_parent_route_stoichiometry_repair_v1.md
?? docs/WESLR_SCATTI_CALCULATION_ASSURANCE_REPORT_V1.md
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
?? scripts/generate_stoichiometric_certificates.py
?? scripts/render_scatti_calculation_assurance_report.py
?? scripts/scatti_audit_consistency_check.py
?? weslr/modules/calculation_assurance.py
?? weslr/modules/materials_stoichiometric_route_engine.py
?? weslr/modules/materials_stoichiometric_route_verifier.py
?? weslr/tests/test_arc_agi2_synthesis_core_integration_audit_v1.py
?? weslr/tests/test_calculation_assurance.py
?? weslr/tests/test_materials_stoichiometric_route_engine.py
?? weslr/tests/test_materials_stoichiometric_route_verifier.py
?? weslr/tests/test_scatti_audit_consistency.py
```

---

## SECTION 12 — Next Recommended Action

**B. Transfer bundle to Ubuntu and reconcile before commit.**

The authoritative Ubuntu evidence (commits 2d40b9d, 55342bb, MP-parent experiment artifacts) has not been imported into this snapshot. The calculation assurance work should be bundled and transferred to the Ubuntu/Nova host for reconciliation before any commit.
