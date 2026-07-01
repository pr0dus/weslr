# WESLR ARC Synthetic 3‑Step Pilot Design – V1

**Lane**: `DESIGN_ARC_SYNTHETIC_3_STEP_PILOT_V1`
**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `22d95cec`

---

## 1. Pilot Size
- **Total tasks**: **20** (the default pilot size recommended in the 3‑step ladder design).

---

## 2. Pilot Task Families (Core 8 families)
| Family ID | Primitive Sequence | Variations | Difficulty | Capability Tested | Required Carry‑over Fields | Likely Failure Modes | Expected Trace Fields |
|-----------|-------------------|------------|------------|-------------------|----------------------------|----------------------|-----------------------|
| `F001` | `extract → rotate → recolor` | 3 (different rotations, colours) | Medium | Object extraction + geometric transform + colour mapping | `object_id`, `grid`, `rotation_angle`, `colour_map` | Rotation out of bounds, missing object, colour clash | `step_1_exports`, `step_2_imports`, `step_2_exports`, `step_3_imports`, `carried_parameters_by_edge`, `dropped_parameters_by_edge`, `parameter_origin_by_step`, `intermediate_grid_1_summary`, `intermediate_grid_2_summary`, `failure_step`, `failure_reason`, `sequence_visibility_reason` |
| `F002` | `remove_noise → extract_object → recolor` | 3 (noise levels, object types) | Easy | Noise filtering then attribute change | `noise_map`, `object_id` | Over‑filtering removes object | Same as above |
| `F003` | `fill_region → count_objects → pattern_output` | 3 (region shapes, counts) | Hard | Region filling then quantitative reasoning | `region_mask`, `object_counts` | Mis‑count due to overlapping fills | Same as above |
| `F004` | `crop_object → transform → place_back` | 3 (crop sizes, transforms) | Medium | Cropping and re‑integration with transformation | `crop_box`, `transform_params`, `object_id` | Mis‑alignment on placement | Same as above |
| `F005` | `extract_boundary → recolor_boundary → count` | 3 (boundary types, recolour schemes) | Easy | Boundary detection plus counting | `boundary_coords` | Boundary fragmentation | Same as above |
| `F006` | `isolate_largest → normalize_position → recolor` | 3 (size thresholds, normalisation methods) | Medium | Selection of dominant object, normalisation | `largest_id`, `position_vector` | Wrong selection when tie | Same as above |
| `F007` | `mirror_object → extract_changed_region → recolor` | 3 (mirror axes, change detection thresholds) | Medium | Symmetry plus delta detection | `mirror_axis`, `changed_region` | False positives on change detection | Same as above |
| `F008` | `crop → rotate → count_or_pattern` | 3 (crop dimensions, rotation angles) | Easy | Simple geometric pipeline ending in quantitative output | `crop_box`, `angle` | Loss of data after crop | Same as above |

*Each family will contribute **2–3** variations, yielding the required **20** pilot tasks.*

---

## 3. Task Specification Schema (JSON‑like)
```json
{
  "task_id": "string",                 // Unique identifier within the pilot
  "family_id": "string",               // One of the Family IDs above (e.g., "F001")
  "difficulty": "easy | medium | stress",
  "primitive_sequence": ["string"],    // Ordered list of primitives, e.g., ["extract","rotate","recolor"]
  "scene_spec": {
    "grid_size": "int[2]",
    "initial_objects": [
      {
        "object_id": "string",
        "type": "string",
        "attributes": { "color": "string", "position": "int[2]" }
      }
    ]
  },
  "train_pair_count": "int",          // Number of train input‑output pairs (static for pilot, typically 1)
  "test_input_count": "int",           // Number of test inputs (static, typically 1)
  "expected_trace_requirements": {
    "step_1_exports": true,
    "step_2_imports": true,
    "step_2_exports": true,
    "step_3_imports": true,
    "carried_parameters_by_edge": true,
    "dropped_parameters_by_edge": true,
    "parameter_origin_by_step": true,
    "intermediate_grid_1_summary": true,
    "intermediate_grid_2_summary": true,
    "failure_step": true,
    "failure_reason": true,
    "sequence_visibility_reason": true
  },
  "allowed_dynamic_parameters": ["rotation_angle","colour_map","transform_params","noise_level"],
  "forbidden_shortcuts": [
    "expected_test_output",
    "task_id_shortcut",
    "generator_note_shortcut"
  ],
  "leakage_flags": {
    "arc_agi_participation_claim": false,
    "leaderboard_claim": false,
    "hidden_test_use": false,
    "public_claim": false,
    "final_answer_wiring": false,
    "weslr_persistence": false,
    "external_calls": false,
    "provider_model_calls": false,
    "runtime_chat_wiring": false
  },
  "expected_failure_categories": [
    "rotation_out_of_bounds",
    "object_missing",
    "count_mismatch",
    "alignment_error",
    "parameter_drift"
  ]
}
```

---

## 4. Diagnostic Packet Generator Design (future implementation notes)
- **Input**: The JSON task specs described above (generated offline).
- **Output**: A static‑local `evidence/arc_synthetic_3_step_<family>_<variant>.json` packet containing:
  - `packet_id` = generated task id.
  - `known_science_anchor` = reference to the synthetic ARC 3‑step anchor (to be created after the pilot).
  - `evidence_items` = a single `EvidenceItem` referencing a local synthetic report file (e.g., `weslr/arc_synthetic_3_step_<family>_<variant>_report.txt`).
  - All boundary fields (`static_local_only`, `external_calls_allowed`, …) set to `true`/`false` as required.
- **Behaviour**: No execution of primitives; the generator merely packages the static description and the pre‑computed synthetic report (produced by a separate offline script, not part of this lane). The packet can later be validated with `validate_packet` and replayed safely.

---

## 5. Trace Contract (required for every pilot task)
| Trace Element | Description |
|---------------|------------|
| `step_1_exports` | Exported grid/object representation after primitive 1. |
| `step_2_imports` | Input consumed by primitive 2 (should match `step_1_exports`). |
| `step_2_exports` | Output after primitive 2. |
| `step_3_imports` | Input for primitive 3 (should match `step_2_exports`). |
| `carried_parameters_by_edge` | Mapping of each parameter from one step to the next (e.g., rotation angle carried from step 1 to step 2). |
| `dropped_parameters_by_edge` | Parameters intentionally removed (e.g., noise map after step 2). |
| `parameter_origin_by_step` | Source of each parameter (initial, derived, transformed). |
| `intermediate_grid_1_summary` | Summary of grid after step 1 (size, object count, colour histogram). |
| `intermediate_grid_2_summary` | Same for after step 2. |
| `failure_step` | If a stop condition triggered, the step number (1‑3). |
| `failure_reason` | Human‑readable explanation of the failure. |
| `sequence_visibility_reason` | Why the sequence is observable (visual change, count change, etc.). |

All fields must be recorded as **static‑local metadata** – no external calls or live data are permitted.

---

## 6. Baseline Preservation
The pilot design explicitly **preserves** the following established baselines and does **not** modify them:
- **2‑step 80**: `77 exact / 3 partial / 0 unsupported / 0 failed`
- **Original 40‑step**: `39 exact / 1 partial / 0 unsupported / 0 failed`
- **Single‑step canonical**: `114 exact / 6 partial / 0 unsupported / 0 failed`
- **Two static‑local real‑evidence replay milestones** (first and second packets).

All 3‑step tasks are built on top of these baselines; no existing metrics are altered.

---

## 7. Leakage Boundaries (hard “forbid” list)
The pilot **must not** perform or encode any of the following:
1. Expected test‑output usage during candidate generation.
2. Task‑id shortcuts that bypass full specification.
3. Generator‑note shortcuts embedding answers.
4. Access to hidden/private ARC data or any ARC‑AGI material.
5. ARC‑AGI participation or leaderboard claims.
6. Public benchmark score assertions.
7. Candidate‑output‑surface wiring (i.e., connecting generated candidates directly to a final answer).
8. Final‑answer generation within the pilot (only internal reports are allowed).
9. `.weslr` persistence writes.
10. Any external API / provider / model calls.
11. Runtime or chat‑wire wiring that would expose internal state.

These boundaries are enforced by the schema (`leakage_flags`) and by the static‑local execution model.

---

## 8. Recommended Next Implementation Lane
**`IMPLEMENT_ARC_SYNTHETIC_3_STEP_TASK_SCHEMA_AND_PACKET_GENERATOR_V1`**
- Implement the JSON task schema defined in section 3.
- Build a diagnostic‑only packet generator that produces the static‑local evidence packets for the 20 pilot tasks (without executing the primitives).
- Produce the synthetic ARC 3‑step anchor report files referenced by the packets.
- Validate the packets with `validate_packet` and ensure they meet the trace contract.

---

**Conclusion** – This design fully specifies a 20‑task ARC synthetic 3‑step pilot, provides a reusable task schema, outlines a diagnostic packet generation approach, and enforces strict leakage boundaries while preserving all existing baselines.
