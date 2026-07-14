# WESLR SCATTI Cross-Host Reconciliation Report R4C

**Date:** 2026-07-14
**R4C Commit:** `d9113dba8d92acdb77ed6df36d32886387b719a3`
**Parent (R4B):** `754da5256edd75598aeefddaad870a3bef91a32d`

*This report is generated from machine-readable evidence. Agent narration is not accepted as a source of calculated values.*

---

## 1. R4B Invalidation

R4B was invalidated by raw/summary disagreement:

| Source | Total | Passed | Failed | Errors |
|--------|-------|--------|--------|--------|
| `test_summary.json` (claimed) | 159 | 159 | 0 | 0 |
| `test_output.txt` (raw evidence) | 159 | 155 | 4 | 0 |

**Root cause:** `test_summary.json` was manually written with hardcoded totals instead of being generated from JUnit XML or raw pytest output.

**Verdict:** `r4b_release_invalid_raw_summary_disagreement`

## 2. Circular Dependency Removal

Stage A (test execution) and Stage B (release verification) are now fully separated:

- **Stage A** runs pytest in a fresh subprocess, generates JUnit XML, and writes a receipt parsed from JUnit
- **Stage B** independently parses JUnit XML, raw stdout/stderr, return code, and receipt — rejecting any disagreement
- No Stage A test invokes the live repository verifier
- Verifier tests use isolated temporary fixtures

## 3. Authoritative Test Pipeline

The authoritative runner (`scripts/run_scatti_release_validation_r4c.py`):
1. Records pre-run Git HEAD and status
2. Runs pytest with `--junitxml` in a fresh subprocess
3. Writes command receipt, raw stdout/stderr, JUnit XML
4. Parses JUnit XML to generate test receipt
5. Verifies return code, JUnit totals, stdout/JUnit agreement, source unchanged

## 4. Stage A — Test Execution

| Metric | Value |
|--------|-------|
| Return code | 0 |
| JUnit tests | 174 |
| Passed | 174 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Source unchanged | True |
| Validation status | accepted |

## 5. Stage B — Release Verification

| Metric | Value |
|--------|-------|
| Verifier | `verify_scatti_cross_host_reconciliation_r4c.py` |
| Checks passed | 26 |
| Checks failed | 0 |
| Checks abstained | 0 |
| Overall | `cross_host_reconciliation_r4c_release_verified` |

## 6. R4C Commit

| Property | Value |
|----------|-------|
| Hash | `d9113dba8d92acdb77ed6df36d32886387b719a3` |
| Parent | `754da5256edd75598aeefddaad870a3bef91a32d` |
| Subject | `WESLR: repair scatti raw-evidence release verification r4c` |
| Files | 13 changed, 919 insertions, 33 deletions |

## 7. Push

| Property | Value |
|----------|-------|
| Branch | `scatti-cross-host-reconciliation-v3-20260714` |
| Local hash | `d9113dba8d92acdb77ed6df36d32886387b719a3` |
| Remote hash | `d9113dba8d92acdb77ed6df36d32886387b719a3` |
| Agreement | ✅ |
| Force push | No |

## 8. Readiness

- **ready_for_corrected_geometry_phase = true**
- **next_recommended_phase = corrected_parent_derived_geometry_construction**

## 9. Claim Boundary

- No DFT-ready structure exists
- No novelty or discovery claim is made
- No stability claim is made
- No synthesizability claim is made
- No experimental validation exists
- R4B was invalidated and corrected by R4C
- R4C establishes raw-evidence-authoritative release verification
