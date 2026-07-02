# WESLR ARC Synthetic Discovery 140 — Hard Mode Calibration Review (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_CALIBRATION_RESULTS_V1`
**Start HEAD**: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
**Actual preflight HEAD**: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
**End HEAD**: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
**Commit**: no
**Date**: 2026-07-02

## 1) Provenance

- Implementation commit: `a4c448d4` (`Implement ARC synthetic discovery 140 hard-mode calibration`)
- Report commit: `b25803fe` (`Add hard-mode calibration implementation report`)
- Provenance verified: yes
- End HEAD mismatch explained: yes — the implementation report’s End HEAD points at the implementation commit, but the final repository head moved again when the report file itself was committed.

## 2) Base gate separation

Verified separate layers:
- Base 140 gate remains `130/130`
- BH80 remains `80/80`
- Previous 117 base remains `117/117`
- Candidate probes counted as solved remain `0`
- Hard-mode denominator is separate: `30/30`

No hard-mode failure corrupted the clean 130-base regression gate.

## 3) Non-exact hard-mode tasks

### Unsupported / unpromoted tasks (11)
These are unsupported because they use unpromoted candidate primitives already present in the hard-mode pressure layer.

| Task | Unsupported primitive/capability | Decision |
|---|---|---|
| T140H_007 | `constr_copy_to_pos` | future candidate probe |
| T140H_021 | `geom_scale_2x` | future candidate probe |
| T140H_022 | `topo_merge_objects` | future candidate probe |
| T140H_023 | `constr_connect_line` | future candidate probe |
| T140H_024 | `constr_copy_to_pos` | future candidate probe |
| T140H_025 | `pat_color_cycle` | future candidate probe |
| T140H_026 | `cond_if_edge_clip` | future candidate probe |
| T140H_027 | `topo_split_at_gap` | future candidate probe |
| T140H_028 | `geom_scale_2x` + `topo_merge_objects` | hard-mode unsupported sentinel |
| T140H_029 | `constr_connect_line` + `cond_if_edge_clip` | hard-mode unsupported sentinel |
| T140H_030 | `pat_color_cycle` + `topo_split_at_gap` | hard-mode unsupported sentinel |

Notes:
- These are not promotions.
- None are retired/duplicate by exact-match evidence.
- The single-primitive cases are best kept as future candidate probes.
- The combined cases are best kept as hard-mode unsupported sentinels.

### Supported-chain failures (3)
These are supported by the pipelines on both sides, but solver and oracle disagree.

| Task | Primitive sequence | Mismatch type | Interpretation |
|---|---|---|---|
| T140H_002 | `isolate_largest → mask_complement → normalize_position` | placement drift / semantic mismatch | weak primitive semantics after complement; normalization/background handling differs between oracle and solver |
| T140H_005 | `topo_fill_holes → recolor_boundary → extract` | output-dimension / crop mismatch | composition-sensitive `extract`/boundary semantics differ; not a scorer issue |
| T140H_015 | `remove_noise → topo_fill_holes → mask_complement` | content mismatch | composition-sensitive noise/topology handling differs; not a structural failure |

## 4) Promoted primitive risk check

Potentially implicated primitives:
- `mask_complement`
- `normalize_position`
- `topo_fill_holes`
- `remove_noise`
- `extract`

No evidence in this review that the following regressed:
- `color_invert`
- `constr_draw_rect_around`
- `sel_leftmost`
- `cond_if_holes_fill`
- `rel_swap_positions`
- `color_swap_1_2`

## 5) Connected-components divergence

- Known medium CC divergence implicated: no
- CC-adjacent pressure exists in the hard-mode design, but the three supported-chain failures do not point to the known CC divergence sentinel as the primary cause.

## 6) Best next lane

Recommended next lane:
- `REPAIR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_V1`

Reason:
- The hard-mode layer is useful as a diagnostic layer.
- The immediate value now is fixing the three supported-chain semantic gaps before using hard-mode for any broader calibration or promotion work.

## 7) Validation

- `git diff --check`: PASS
- `python weslr/tests/release_gate_v1.py`: PASS
- `./scripts/weslr_release_check.sh`: PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`: PASS

## 8) Receipt

- Start HEAD: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
- End HEAD: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
- Commit: no
- actual preflight HEAD: `b25803fe33e9d2e0b1256376f8748f4f67f6df73`
- provenance verified: yes
- end-head mismatch explained: yes
- base gate preservation verified: yes
- hard-mode separate denominator verified: yes
- all 14 non-exact tasks classified: yes
- 11 unsupported tasks classified: yes
- 3 supported-chain failures analyzed: yes
- CC divergence implicated: no
- promoted primitive risks identified: yes
- recommended next lane: `REPAIR_ARC_SYNTHETIC_DISCOVERY_140_HARD_MODE_SUPPORTED_CHAIN_GAPS_V1`
- validation: PASS
- push avoided: yes
