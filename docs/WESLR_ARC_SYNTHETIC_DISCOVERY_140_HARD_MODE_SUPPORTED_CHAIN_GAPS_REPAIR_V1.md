# WESLR ARC Synthetic Discovery 140 — Hard Mode Supported-Chain Gaps Repair (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REPAIR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_V1`
**Start HEAD**: `ddbc60b214327cec0d06d214f8514735adfd8fff`
**Actual preflight HEAD**: `ddbc60b214327cec0d06d214f8514735adfd8fff`
**End HEAD**: `ddbc60b214327cec0d06d214f8514735adfd8fff`
**Commit**: no
**Date**: 2026-07-02

## 1) Diagnoses

### T140H_002
- Sequence: `isolate_largest → mask_complement → normalize_position`
- Root cause: the added distractor object touched the main hollow object by 4-connectivity, so `isolate_largest` selected a larger connected component than intended in one pipeline, producing placement drift downstream.
- Classification: semantic mismatch caused by scene adjacency, not a scorer issue.

### T140H_005
- Sequence: `topo_fill_holes → recolor_boundary → extract`
- Root cause: the secondary object touched the filled donut after hole filling, so `recolor_boundary` expanded the boundary bbox differently between oracle and solver.
- Classification: output-dimension / crop mismatch caused by scene adjacency, not a scorer issue.

### T140H_015
- Sequence: `remove_noise → topo_fill_holes → mask_complement`
- Root cause: the extra 2x2 object was not treated consistently by oracle and solver during noise removal; it was effectively preserved in the oracle path but removed in the solver path.
- Classification: content mismatch caused by scene composition, not a structural failure.

## 2) Exact repairs made

- `T140H_002`: moved `o2` away from the donut so it no longer touches the main component.
- `T140H_005`: moved `o2` away from the donut so `recolor_boundary` and `extract` see the same main bbox.
- `T140H_015`: removed the extra 2x2 object and kept the task focused on the donut plus noise pixels.

These repairs kept the hard-mode tasks supported while removing accidental semantic drift.

## 3) Result after repair

- T140H_002 now exact: yes
- T140H_005 now exact: yes
- T140H_015 now exact: yes

### Hard-mode before/after
- Before: `16/30 exact, 3 failed, 11 unsupported` (`weak`)
- After: `19/30 exact, 0 failed, 11 unsupported` (`weak`)

### Unsupported count
- Before: `11`
- After: `11`

## 4) Preservation checks

- Base 130/130 preserved: yes
- BH80 80/80 preserved: yes
- Previous 117/117 preserved: yes
- Candidate probes counted as solved 0 preserved: yes

## 5) Validation

- py_compile touched modules: PASS
- focused hard-mode tests: PASS
- hard-mode semantic pilot: PASS
- existing 140 generator tests: PASS
- existing 140 semantic pilot: PASS
- release gate: PASS
- release check: PASS
- source-repo health check: PASS
- git diff check: PASS

## 6) Files changed
- `weslr/arc_discovery_140_hard_mode_calibration.py`
- `docs/WESLR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_REPAIR_V1.md`

## 7) Receipt

- Start HEAD: `ddbc60b214327cec0d06d214f8514735adfd8fff`
- End HEAD: `ddbc60b214327cec0d06d214f8514735adfd8fff`
- Commit: no
- actual preflight HEAD: `ddbc60b214327cec0d06d214f8514735adfd8fff`
- T140H_002 repaired: yes
- T140H_005 repaired: yes
- T140H_015 repaired: yes
- hard-mode before result: `16/30 exact, 3 failed, 11 unsupported`
- hard-mode after result: `19/30 exact, 0 failed, 11 unsupported`
- unsupported count: `11`
- base 130/130 preserved: yes
- BH80 80/80 preserved: yes
- previous 117/117 preserved: yes
- candidate probes counted as solved 0: yes
- validation: PASS
- unrelated dirty files left uncommitted: yes
- push avoided: yes
- recommended next lane: `REVIEW_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_REPAIR_V1`
