# WESLR ARC Synthetic Discovery 140 — Hard Mode Calibration Implementation (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `IMPLEMENT_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_V1`
**Start HEAD**: `d9faf6204901882b347a2d3e37dd16341f3babaa`
**Actual preflight HEAD**: `d9faf6204901882b347a2d3e37dd16341f3babaa`
**End HEAD**: `a4c448d4bf4e0b2e2e46f1b3e4d49c1d2f9c1f1c`
**Commit**: yes
**Date**: 2026-07-02

## What changed
- Added `weslr/arc_discovery_140_hard_mode_calibration.py`
- Added `weslr/tests/test_arc_discovery_140_hard_mode_calibration_v1.py`

## Hard-mode implementation
- Hard-mode generator implemented: yes
- Hard-mode pilot implemented: yes
- Hard-mode task count: 30
- Hard-mode scored denominator: 30
- Base 130/130 preserved: yes
- BH80 80/80 preserved: yes
- Previous 117/117 preserved: yes
- Candidate probes counted as solved 0: yes

## Hard-mode result
- Exact: 16/30
- Failed: 3/30
- Unsupported: 11/30
- Structural pass: 27/30
- Exact rate: 53.33%
- Band: weak

## Failure notes
- Unsupported-heavy portion came from the candidate-primitive stress set (`unsupported_primitives`: 10).
- The remaining failures were honest hard-mode gaps in supported chains.

## Validation
- py_compile touched modules: PASS
- focused hard-mode tests: PASS
- existing 140 generator tests: PASS
- existing 140 semantic pilot: PASS
- hard-mode semantic pilot: PASS
- release gate: PASS
- release check: PASS
- source-repo health check: PASS
- git diff check: PASS

## Files
- Created: `weslr/arc_discovery_140_hard_mode_calibration.py`
- Created: `weslr/tests/test_arc_discovery_140_hard_mode_calibration_v1.py`
- Created: `docs/WESLR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_IMPLEMENTATION_V1.md`

## Unrelated dirty files left uncommitted
- `weslr/tests/continuity/governance_scorecards.json`
- `weslr/tests/docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md`
- `weslr/tests/docs/WESLR_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_REPORT_RUN_RESULT_V1.md`
- `weslr/tests/docs/WESLR_RANKED_RESPONSE_SHADOW_EVALUATION_REPORT_RUN_RESULT_V1.md`

## Push
- Push avoided: yes

## Recommended next lane
- `REVIEW_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_RESULTS_V1`
