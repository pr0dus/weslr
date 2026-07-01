# ARC Synthetic 3‑Step – 40‑Task Expansion Design (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_SYNTHETIC_3_STEP_40_EXPANSION_V1`
**Start HEAD**: `d4b4adc8`

**Design‑only declaration**: This document specifies the design of a controlled 40‑task synthetic 3‑step pilot. No code is changed, no tasks are executed, and no solver behavior is altered. The design will be consumed by a later generator lane.

---

## Reference Baseline
The 20‑task baseline is canonized in:
`docs/WESLR_ARC_SYNTHETIC_3_STEP_BASELINE_AND_SCALING_LADDER_V1.md`

---

## 40‑Task Gate Summary
| Gate | Exact | Exact % |
|------|-------|--------|
| **Minimal** | 34 | 85 % |
| **Strong**  | 36 | 90 % |
| **Clean**   | 40 | 100 % |

---

## Task Set Structure
The 40‑task set consists of:
1. **20 preserved baseline tasks** – the original tasks from the 20‑task pilot (IDs T01‑T20). These remain unchanged.
2. **20 newly designed tasks** – IDs **T21‑T40**. Each new task declares exactly three primitive steps.

### Preserved Tasks (T01‑T20)
The baseline tasks are retained verbatim. Their IDs are assumed to be `T01` … `T20` as used in the baseline report. No modifications are made to their definitions.

### New Tasks (T21‑T40)
All new tasks are synthetic, public‑safe, and internally generated. Each task follows the 3‑step primitive pattern:
```
extract_boundary → mirror_object → crop
```
or a permutation thereof, with variations to stress specific primitives.

Below is the specification table (excerpt, full list follows the same schema):
| Task ID | Primitive Sequence (order) | Family | Difficulty | Edge‑case focus |
|---------|---------------------------|--------|------------|-----------------|
| T21 | extract_boundary → mirror_object → crop | A | easy | centered single object, simple shape |
| T22 | extract_boundary → crop → mirror_object | A | easy | centered object, square bbox |
| T23 | mirror_object → extract_boundary → crop | B | medium | asymmetric shape requiring correct mirroring |
| T24 | mirror_object → crop → extract_boundary | B | medium | multi‑object scene, mirror creates overlap |
| T25 | crop → extract_boundary → mirror_object | A | medium | object near image edge, bbox clipping |
| T26 | crop → mirror_object → extract_boundary | A | medium | object touching multiple edges |
| T27 | extract_boundary → mirror_object → crop | B | hard | non‑centered object, off‑center bbox |
| T28 | extract_boundary → crop → mirror_object | B | hard | multi‑object with overlapping bboxes |
| T29 | mirror_object → extract_boundary → crop | A | hard | asymmetric shape with distractor colors |
| T30 | mirror_object → crop → extract_boundary | A | hard | scene with distractor colors and background noise |
| T31 | crop → extract_boundary → mirror_object | B | easy | simple L‑shaped object, clear bbox |
| T32 | crop → mirror_object → extract_boundary | B | easy | single vertical rectangle, mirror test |
| T33 | extract_boundary → mirror_object → crop | A | medium | object with hole (donut) – bbox must ignore hole |
| T34 | extract_boundary → crop → mirror_object | A | medium | object rotated 45°, bbox must be tight |
| T35 | mirror_object → extract_boundary → crop | B | medium | two objects, one mirrored, one not
| T36 | mirror_object → crop → extract_boundary | B | medium | overlapping objects, mirror changes ordering |
| T37 | crop → extract_boundary → mirror_object | A | hard | object spanning whole canvas, crop must keep size |
| T38 | crop → mirror_object → extract_boundary | A | hard | very small object, precision of bbox critical |
| T39 | extract_boundary → mirror_object → crop | B | hard | asymmetric multi‑color object, mirror must preserve colors |
| T40 | extract_boundary → crop → mirror_object | B | hard | object partially outside canvas, bbox must be clipped correctly |

*All tasks use public‑safe synthetic grids; no real‑world images or ARC data are involved.*

---

## Family Distribution
- **Family A**: 10 new tasks (T21, T22, T25, T26, T31, T32, T33, T34, T37, T38)
- **Family B**: 10 new tasks (T23, T24, T27, T28, T29, T30, T35, T36, T39, T40)

This mirrors the baseline family split and ensures balanced evaluation.

---

## Difficulty Distribution
- **Easy**: 6 tasks (T21, T22, T31, T32, T33, T34)
- **Medium**: 8 tasks (T23, T24, T25, T26, T35, T36, T37, T38)
- **Hard**: 6 tasks (T27, T28, T29, T30, T39, T40)

The distribution provides a progressive challenge for the solver while keeping the overall exact‑rate target feasible.

---

## New Edge Cases Introduced
- **Non‑centered objects** (T27, T28) to test bbox calculation offsets.
- **Multi‑object scenes** (T24, T35, T36) to verify that primitives correctly isolate the largest component.
- **Asymmetric shapes** (T23, T29, T39) to stress `mirror_object` correctness.
- **Objects near or crossing canvas edges** (T25, T26, T40) to test clipping logic in `crop`.
- **Distractor colors/background noise** (T30, T39) to ensure primitives ignore irrelevant pixels.
- **Objects with holes** (T33) to confirm `extract_boundary` ignores interior voids.
- **Rotated objects** (T34) to verify bbox tightness.

---

## Leakage‑Prevention Rules
- No task includes any real‑world ARC data; all grids are generated synthetically.
- No hidden or private data is referenced.
- All primitives must produce deterministic outputs; stochastic behavior is prohibited.
- No expected‑output leakage: the ground‑truth for each primitive is derived from the synthetic generator and is not exposed to the solver.
- No tuning on the assessment set; the 40‑task set itself is the evaluation set.

---

## Trace Requirements
- Every task must produce a full trace of the three primitive calls, including input grid, intermediate outputs, and final grid.
- Traces must be recorded in the standard Weslr trace format (JSON lines) for later analysis.
- Leak‑prevention flags (`leakage`, `blocked_reason`) must be false for all tasks.

---

## Scoring Policy (to be applied in the later pilot)
- **Exact**: primitive output matches the deterministic reference exactly.
- **Partial**: output matches reference modulo inconsequential differences (e.g., colour ordering when irrelevant).
- **Unsupported**: primitive not applicable to the task (should never occur with the designed tasks).
- **Failed**: runtime error or incorrect output.
- No noop/placeholders are permitted; each primitive must have real semantics.

---

## Implementation Constraints for Generator Lane
- The generator must emit tasks conforming to the table above.
- Primitive sequences must be recorded in the `primitives` field in order.
- Family and difficulty metadata must be attached to each task.
- Edge‑case flags (`non_centered`, `multi_object`, `asymmetric`, `edge_crossing`, `distractor_colors`, `hole`, `rotated`) should be encoded for later analysis.
- All files must be placed under `weslr/arc_synthetic_3_step_tasks/` respecting the Weslr directory layout.

---

## Validation Plan (for the later 40‑task pilot)
1. **Structural validation** – ensure 40 task definitions exist, each with exactly three primitives.
2. **Trace completeness** – each task produces a full three‑step trace.
3. **Leakage flags** – verify no task has `leakage:true`.
4. **Scoring run** – execute the pilot, compute exact/partial/unsupported/failed counts.
5. **Gate checks** – confirm the chosen gate (minimal/strong/clean) is met.
6. **Release‑gate** – run `weslr_release_check.sh` and `chat_weslr_de_health_check.sh --mode source-repo` on the new files.

---

## Forbidden Claims
The design deliberately avoids any of the following:
- Public ARC‑AGI score or benchmark claims.
- Use of public or hidden ARC datasets beyond the synthetic generator.
- Assertions of autonomous discovery or real‑world evidence intake.
- References to external provider APIs or model calls.

---

## Next Lane Recommendation
`IMPLEMENT_ARC_SYNTHETIC_3_STEP_40_EXPANSION_TASK_PACKET_GENERATOR_V1` – implement the task‑packet generator that emits the 40‑task set defined above.
