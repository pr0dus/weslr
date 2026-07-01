# WESLR_ARC_SYNTHETIC_3_STEP_LADDER_DESIGN_V1

**Lane**: `DESIGN_ARC_SYNTHETIC_3_STEP_LADDER_V1`
**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `5d0ccc75`

---

## 1. Why a 3‑step ladder matters
The ARC‑style 2‑step ladder has demonstrated that WESLR can preserve state across a single transition and correctly reproduce a synthetic result. Adding a **third step** stresses additional capabilities that are not exercised in a 2‑step pipeline:

| New capability | Why it matters |
|----------------|----------------|
| **Longer state carry‑over** | The system must keep objects, parameters and intermediate representations alive for two consecutive transitions before a final output.
| **Intermediate object identity preservation** | An object created in step 1 must be recognisable and addressable in step 2 and step 3, testing reference stability.
| **Parameter memory across multiple transitions** | Parameters (e.g., colours, offsets) set in step 1 may be transformed or reused in step 2 and step 3, checking correct propagation.
| **Error propagation & early‑stop detection** | Failures in early steps must be reported accurately and prevent spurious later processing.
| **Step‑order sensitivity** | Reordering the three primitives should change the outcome, confirming that the pipeline respects the defined sequence.
| **Branch rejection & role preservation** | When a branch of reasoning is invalid at step 2, the system must discard it while preserving the role of remaining branches.
| **No‑op detection** | A step that makes no effective change (e.g., rotate 0°) should be recognised and not corrupt the state.
| **Dynamic vs stable parameter separation** | Distinguish parameters that are allowed to evolve (e.g., colour) from invariants that must stay constant (e.g., object ID).

These stress‑tests advance the **state‑carrying** and **error‑handling** stack without leaving the static‑local boundary.

---

## 2. What a 3‑step ladder does **NOT** prove
* It is **not** evidence of human‑level reasoning or understanding.
* It does **not** demonstrate the ability to ingest live, external evidence.
* It does **not** confer any **public benchmark** or **AGI** claim authority.
* It does **not** prove autonomous discovery or the capability to generate novel scientific hypotheses.
* It does **not** validate scalability to unbounded or real‑world datasets.

---

## 3. Proposed 3‑step task families (12 families)
| # | Primitive sequence | Cognitive capability tested | Required carry‑over fields | Expected failure modes | Difficulty |
|---|-------------------|----------------------------|----------------------------|------------------------|------------|
| 1 | `extract → rotate → recolor` | Object extraction + geometric transform + colour mapping | `object_id`, `grid`, `rotation_angle` | Rotation out of bounds, missing object | Medium |
| 2 | `remove_noise → extract_object → recolor` | Noise filtering then attribute change | `noise_map`, `object_id` | Over‑filtering removes object | Easy |
| 3 | `complete_line → reflect → recolor` | Line completion + symmetry + colour | `line_points`, `axis` | Incomplete line detection | Medium |
| 4 | `fill_region → count_objects → pattern_output` | Region filling then quantitative reasoning | `region_mask`, `object_counts` | Mis‑count due to overlapping fills | Hard |
| 5 | `crop_object → transform → place_back` | Cropping and re‑integration with transformation | `crop_box`, `transform_params` | Mis‑alignment on placement | Medium |
| 6 | `extract_boundary → recolor_boundary → count` | Boundary detection plus counting | `boundary_coords` | Boundary fragmentation | Easy |
| 7 | `isolate_largest → normalize_position → recolor` | Selection of dominant object, normalization | `largest_id`, `position_vector` | Wrong selection when tie | Medium |
| 8 | `remove_background_noise → complete_shape → recolor` | Denoising then shape completion | `bg_mask`, `shape_template` | Partial shape remnants | Hard |
| 9 | `mirror_object → extract_changed_region → recolor` | Symmetry plus delta detection | `mirror_axis`, `changed_region` | False positives on change detection | Medium |
|10| `crop → rotate → count_or_pattern` | Simple geometric pipeline ending in quantitative output | `crop_box`, `angle` | Loss of data after crop | Easy |
|11| `scale → extract_features → recolor_by_feature` | Scaling then feature extraction and colour mapping | `scale_factor`, `feature_vector` | Feature extraction mismatch | Hard |
|12| `blur → edge_detect → recolor_edges` | Filtering then edge detection | `blur_radius`, `edge_map` | Edge loss after blur | Medium |

**First pilot selection** – include families **1, 2, 4, 5, 7, 9, 10, 12** (8 tasks) as the core set; the remaining families can be added later for stress testing.

---

## 4. First pilot size
The default recommendation is **20 tasks** to provide statistically meaningful coverage while remaining manageable for manual review. The 8 core families can each be instantiated with 2–3 parameter variations, reaching the target of 20.

---

## 5. Success metrics
| Metric | Definition |
|--------|------------|
| **Exact** | All three steps produce the expected output with no deviation.
| **Partial** | One or two steps match; remaining step deviates within a defined tolerance.
| **Unsupported** | The task uses a primitive not allowed in the static‑local ladder.
| **Failed** | Crash, exception, or violation of boundary rules.
| **Represented candidates** | Number of distinct parameter combinations generated.
| **Carry‑over success** | Percentage of parameters correctly propagated across steps.
| **Dropped parameters** | Count of parameters lost or overwritten unintentionally.
| **Intermediate mismatch category** | Classification of where the deviation occurred (step 1, step 2, step 3).
| **Step‑wise exactness** | `step_1_exact`, `step_2_exact`, `step_3_exact` flags.
| **Composition failure category** | E.g., *identity loss*, *parameter drift*, *order violation*.

---

## 6. Trace requirements (per task)
A full 3‑step trace must record:
* `step_1_exports` – exported grid/objects after step 1.
* `step_2_imports` – inputs consumed by step 2.
* `step_2_exports` – outputs of step 2.
* `step_3_imports` – inputs to step 3.
* `carried_parameters_by_edge` – mapping of each parameter from one step to the next.
* `dropped_parameters_by_edge` – parameters that were intentionally or unintentionally removed.
* `parameter_origin_by_step` – origin source (initial, derived, transformed).
* `intermediate_grid_1_summary` / `intermediate_grid_2_summary` – concise descriptions (size, object count, colour histogram).
* `failure_step` – if any, the step number where failure occurred.
* `failure_reason` – human‑readable explanation.
* `sequence_visibility_reason` – why the sequence is observable (e.g., visual change, count change).

All trace fields must be **static‑local** – no external file reads/writes beyond the repository.

---

## 7. Strict leakage boundaries
The 3‑step ladder **must** forbid the following:
* Any attempt to query live services or external APIs during candidate generation.
* Shortcut identifiers that bypass full task specification (e.g., `task-id = 123`).
* Generator‑note shortcuts that embed expected outputs.
* Public benchmark claims or statements of “ARC‑AGI‑1” participation.
* Any wiring that routes candidate output to a final‑answer surface.
* Creation or modification of `.weslr` files.
* External tool invocations (e.g., shell commands, model calls).
* Disclosure of internal metrics to external parties.

---

## 8. Relation to the 2‑step 80 baseline
* The 3‑step ladder **preserves** the existing 2‑step 80 results (`77 exact / 3 partial / 0 unsupported / 0 failed`).
* All 2‑step tasks must remain **valid** as sub‑tasks within the 3‑step pipeline (e.g., step 1 + step 2 of a 3‑step task may exactly reproduce a known 2‑step case).
* The baseline metrics for the original 40‑task and single‑step canonical ladders must **not degrade**; they continue to serve as reference points.
* The two static‑local real‑evidence replay milestones remain unchanged and continue to be cited as successful static‑local evidence.

---

## 9. First implementation lane after design
The smallest safe next lane is:
```
DESIGN_ARC_SYNTHETIC_3_STEP_PILOT_V1
```
*Create a formal specification document (JSON schema) for a 3‑step task, together with a diagnostic‑only packet generator that produces a handful of pilot tasks (e.g., 5) with trace placeholders. No runner execution is required at this stage.

---

**Conclusion** – The design defines a clear, bounded, and static‑local 3‑step synthetic capability ladder that extends the current state‑carrying tests without over‑promising.
