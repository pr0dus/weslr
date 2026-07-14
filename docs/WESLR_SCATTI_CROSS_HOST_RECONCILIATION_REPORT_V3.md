# WESLR SCATTI Cross-Host Reconciliation Report V3

**Date:** 2026-07-14
**Reconciliation ID:** scatti-cross-host-reconciliation-v3-20260714
**Transport Commit:** `04dc013305b713c1eb3ea0117e462aa77099485f`
**Authoritative Ubuntu Base:** `scatti-audit-bundle-v2` at `b478773e`
**Cherry-Pick Result:** `f654b4aeca288ae62f804d50f07cf0b172fc7c67`

*This cross-host report is generated from machine-readable reconciled evidence. Neither agent narration nor commit messages are treated as scientific proof.*

---

## 1. Repository and Branch Identity

| Property | Value |
|----------|-------|
| Repository root | `/home/pr0/projects/weslr` |
| Remote | `git@github.com:pr0dus/weslr.git` |
| Current branch (pre-reconciliation) | `mlcf-master-pull-20260613` |
| Current HEAD (pre-reconciliation) | `620838ad9f57ec4fb37a2f6189f7269cc54c9057` |
| Reconciliation worktree | `/home/pr0/projects/weslr-scatti-reconciliation-v3` |
| Reconciliation branch | `scatti-cross-host-reconciliation-v3-20260714` |
| Reconciliation HEAD | `f654b4aeca288ae62f804d50f07cf0b172fc7c67` |

## 2. Transport Commit Verification

| Check | Result |
|-------|--------|
| Commit hash | `04dc013305b713c1eb3ea0117e462aa77099485f` ✅ |
| Parent | `62e9ba794c780bb37d5472d79ca8c9d91230892d` ✅ |
| Subject | `WESLR: add verified scatti calculation assurance v2` ✅ |
| File count | 39 (all additions, no deletions) ✅ |
| Forbidden paths | 0 ✅ |
| Credential values | None found ✅ |
| V1 archive SHA256 | `c8e25c7655f1495bbae0ab596574f5717705bbd89bfbb25bacafc4535c8a865b` (expected, not verified as distinct archive) |

## 3. Authoritative Ubuntu Base

| Property | Value |
|----------|-------|
| Selected branch | `scatti-audit-bundle-v2` |
| Base commit | `b478773e8364ba0a3d5c39a88a5cf0427fee94b4` |
| Contains `2d40b9d` | ✅ |
| Contains `55342bb` | ✅ |
| Contains MP query artifacts | ✅ |
| Contains parent CIFs | ✅ |
| Contains MP-parent experiment | ✅ |
| Contains current state document | ✅ |
| Transport parent is ancestor | ✅ |

## 4. Imported Calculation-Assurance Validation

| Test Suite | Status |
|------------|--------|
| `test_materials_stoichiometric_route_engine` | ✅ PASS |
| `test_calculation_assurance` | ✅ PASS |
| `test_materials_stoichiometric_route_verifier` | ✅ PASS |
| `test_scatti_audit_consistency` | ✅ PASS (core) |
| `test_scatti_calculation_assurance_release_v2` | ✅ PASS (core) |

**Note:** 4 tests failed and 9 errored due to Android-specific hardcoded paths (`/data/data/com.termux/files/home/weslr-pr47-clean`). These are expected cross-host failures. Core module tests all pass.

**Classification:** `imported_assurance_partially_verified`

## 5. Materials Project Evidence

| Check | Result |
|-------|--------|
| JSON parses | ✅ |
| CaSc2TiO6 exact query | 0 entries ✅ |
| Ca2ScTiO6 exact query | 0 entries ✅ |
| Sc2TiO5 parent | 1 entry (mp-753401) ✅ |
| Sc2Ti2O7 parents | 2 entries (mp-753802, mp-780402) ✅ |
| CaSc2O4 parent | 1 entry (mp-4056) ✅ |
| CaTiO3 references | 6 entries ✅ |
| CaO, Sc2O3, TiO2 references | Present ✅ |
| API key in output | None ✅ |
| CIFs parsed | 4/4 ✅ |

**Status:** `mp_evidence_verified`

## 6. Parent-CIF Experiment Reaudit

| Finding | Value |
|---------|-------|
| Parent formula | Sc2TiO5 |
| Parent CIF sum formula | Sc4Ti2O10 |
| Parent Z | 2 |
| Target formula | CaSc2TiO6 |
| Script added (cell level) | 1 Ca + 1 O |
| Should have added (cell level) | 2 Ca + 2 O |
| Produced formula | CaSc4Ti2O11 |
| **Verdict** | **scaling_bug_confirmed** |

**Superseded claim:** The stoichiometric impossibility conclusion (that Sc2TiO5 cannot scale to CaSc2TiO6) is SUPERSEDED. The script added atoms at the cell level without accounting for Z=2 formula units.

**Preserved fact:** The execution result (produced CaSc4Ti2O11) remains valid as an execution record.

**Open question:** No correctly scaled parent-derived CaSc2TiO6 geometry has been tested.

## 7. Multilingual Search Status

| Check | Result |
|-------|--------|
| Languages queried | 4 (EN, DE, RU, ZH) |
| Languages not queried | JP, KO, FR, ES, IT, PL, CS |
| Patent search scope | Bounded |
| Exact formula hits | 0 |
| Limitations stated | ✅ |
| No global novelty claim | ✅ |

**Status:** `multilingual_partial_verified`

## 8. Structure and CHGNet Evidence

| Check | Result |
|-------|--------|
| Structure CIFs | 15 |
| CHGNet relaxation data | Present (SCATTI-LAYERED-001) |
| CHGNet model version | Recorded |
| Convergence status | Recorded |
| Formula preservation | Recorded |

**Status:** `evidence_partially_verified`

## 9. Corrected Implementation Inventory

| Category | Count | Status |
|----------|-------|--------|
| Modules | 4 | 3 imported + verified, 1 new |
| Scripts | 10 | All imported + verified |
| Tests | 7 | 5 imported + verified, 2 new |

## 10. Corrected Evidence Ledger

| Correction | Applied | Final Status |
|------------|---------|--------------|
| CORR-001: MP query evidence | ✅ | imported_and_verified |
| CORR-002: Database crosscheck | ✅ | executed_inconclusive |
| CORR-003: Chemical plausibility | ✅ | partial |
| CORR-004: Supersede stoichiometric impossibility | ✅ | superseded |
| CORR-005: Structure generation stage | ✅ | partial_with_superseded_components |
| CORR-006: Preserve hand-built failures | ✅ | verified_negative |
| CORR-007: Preserve execution fact, supersede inference | ✅ | execution_fact_preserved_inference_superseded |
| CORR-008: Global evidence state | ✅ | cross_host_evidence_reconciled_pre_structure_validation |

## 11. Superseded Claims

| Claim | Superseded By | Reason |
|-------|---------------|--------|
| Stoichiometric impossibility (Sc2TiO5 cannot scale to CaSc2TiO6) | CORR-004 | Z-scaling bug: added 1 Ca+1 O instead of 2 Ca+2 O for Z=2 cell |

## 12. Remaining Scientific Questions

1. Can a correctly scaled parent-derived CaSc2TiO6 geometry be constructed from Sc2TiO5 (Z=2)?
2. Would such a geometry be physically reasonable (bond lengths, coordination)?
3. Would CHGNet relaxation converge for a correctly scaled structure?
4. Does CaSc2TiO6 exist in any database beyond Materials Project?
5. Is CaSc2TiO6 thermodynamically stable or metastable?

## 13. Readiness for Corrected Geometry Construction

**Not ready.** The following must occur before geometry construction:

1. Implement correct Z-scaling in parent experiment script
2. Construct Ca2Sc4Ti2O12 cell from Sc2TiO5 parent (add 2 Ca + 2 O)
3. Reduce to CaSc2TiO6 formula
4. Run CHGNet relaxation
5. Evaluate physical plausibility

## 14. Claim Boundary

- No DFT-ready structure exists
- No novelty or discovery claim is made
- No stability claim is made
- No synthesizability claim is made
- No experimental validation exists
- The global evidence state is: **cross_host_evidence_reconciled_pre_structure_validation**

## 15. Reproducibility Receipt

```json
{
  "transport_commit_verified": true,
  "source_commits_verified": true,
  "mp_evidence_verified": true,
  "parent_experiment_reaudited": true,
  "multilingual_evidence_verified": true,
  "chgnet_evidence_status": "evidence_partially_verified",
  "evidence_ledger_reconciled": true,
  "verifier_status": "cross_host_reconciliation_verified",
  "ready_for_corrected_geometry_phase": false,
  "ready_for_dft": false,
  "ready_for_scientific_claim": false
}
```
