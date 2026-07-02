# WESLR ARC Synthetic Discovery 140 — Hard Mode Supported-Chain Gaps Repair Review (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_REPAIR_V1`
**Start HEAD**: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
**Actual preflight HEAD**: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
**End HEAD**: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
**Commit**: no
**Date**: 2026-07-02

## 1) Repair provenance

- Repair commit verified: yes
- Repair commit: `17307b9f` (`Repair hard-mode supported-chain gaps`)
- Files changed in repair commit:
  - `weslr/arc_discovery_140_hard_mode_calibration.py`
  - `docs/WESLR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_REPAIR_V1.md`

## 2) Repair validity by task

### T140H_002
- Repair valid: yes
- Verified result: `semantic_exact`
- Cause of the earlier failure: accidental adjacency between the distractor object and the main hollow object.
- Why the repair is valid: the distractor was moved away so the intended object remains the largest component without changing the primitive chain or introducing any scorer/oracle shortcut.

### T140H_005
- Repair valid: yes
- Verified result: `semantic_exact`
- Cause of the earlier failure: accidental adjacency between the secondary object and the filled donut changed the boundary bbox.
- Why the repair is valid: the secondary object was moved away so the boundary/extract composition sees the intended bbox consistently.

### T140H_015
- Repair valid: yes
- Verified result: `semantic_exact`
- Cause of the earlier failure: the extra 2x2 object created an oracle/solver content mismatch during noise removal.
- Why the repair is valid: the extra object was removed, leaving the same donut + noise pressure without altering primitive semantics.

## 3) Shortcut / weakening check

- No scorer shortcut introduced: yes
- No oracle/solver separation weakened: yes
- No promoted-primitive semantics changed broadly: yes
- No candidate primitives promoted: yes
- No unsupported hard-mode tasks repaired accidentally: yes

Evidence:
- The only code diff is three scene-spec edits.
- No primitive implementations changed.
- No scorer logic changed.
- No oracle/solver dispatch changed.

## 4) Base and denominator preservation

- Base 130/130 preserved: yes
- BH80 80/80 preserved: yes
- Previous 117/117 preserved: yes
- Candidate probes counted as solved 0 preserved: yes
- Hard-mode denominator remains separate: yes

## 5) Hard-mode result check

- Before repair: `16/30 exact, 3 failed, 11 unsupported`
- After repair: `19/30 exact, 0 failed, 11 unsupported`
- Hard-mode 19/30 exact verified: yes
- Failed count 0 verified: yes
- Unsupported count 11 verified: yes

## 6) Unsupported-task status

The 11 unsupported tasks remain unsupported and were not promoted.

## 7) Validation

- `git diff --check`: PASS
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## 8) Recommended next lane

Recommended next lane:
- `DESIGN_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_UNSUPPORTED_CANDIDATE_PROMOTION_V1`

Reason:
- The supported-chain repair is now clean and verified.
- The remaining signal is entirely in the 11 unsupported tasks, so the next useful step is to design candidate promotion work from that unsupported set rather than freeze or expand yet.

## 9) Receipt

- Start HEAD: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
- End HEAD: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
- Commit: no
- actual preflight HEAD: `17307b9f65a0c69fbc83c5a09029cf3470f0ac15`
- repair commit verified: yes
- T140H_002 repair valid: yes
- T140H_005 repair valid: yes
- T140H_015 repair valid: yes
- hard-mode 19/30 exact verified: yes
- failed count 0 verified: yes
- unsupported count 11 verified: yes
- base 130/130 preserved: yes
- BH80 80/80 preserved: yes
- previous 117/117 preserved: yes
- candidate probes counted as solved 0: yes
- no shortcut/weakening found: yes
- recommended next lane: `DESIGN_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_UNSUPPORTED_CANDIDATE_PROMOTION_V1`
- validation: PASS
- push avoided: yes
