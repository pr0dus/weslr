# EVALUATION_ARC_SYNTHETIC_3_STEP_REAL_PRIMITIVE_DISPATCH_RESULTS_V1

**Repo:** `weslr-pr47-clean`  
**Branch:** `occ-discovery-doctrine-implementation-20260613`  
**Start HEAD:** `581d7b6e` (commit `IMPLEMENT_ARC_SYNTHETIC_3_STEP_REAL_PRIMITIVE_DISPATCH_V1`)  
**End HEAD:** `581d7b6e` (no further commits)  

---

## Current result summary
| Metric | Count |
|--------|-------|
| **Exact** | 0 |
| **Partial** | 0 |
| **Unsupported** | 20 |
| **Failed** | 0 |
| **Exact rate** | 0 % |

The goal of **17/20 exact (85 %)** is not yet reached.

---

## 1. Exact tasks
*None* – no task produced an exact result because every run stopped on the first unsupported primitive.

---

## 2. Unsupported tasks & first‑unsupported primitive
| Task ID | Family | First unsupported primitive (adapter primitive) | Failure step |
|--------|--------|-----------------------------------------------|-------------|
| F001_1 | F001 | `extract_largest_object` (mapped from `extract`) – missing component | 1 |
| F001_2 | F001 | `extract_largest_object` | 1 |
| F001_3 | F001 | `extract_largest_object` | 1 |
| F002_1 | F002 | `extract_largest_object` (from `extract`) | 1 |
| F002_2 | F002 | `extract_largest_object` | 1 |
| F002_3 | F002 | `extract_largest_object` | 1 |
| F003_1 | F003 | `count_objects` (no adapter mapping) | 2 |
| F003_2 | F003 | `count_objects` | 2 |
| F003_3 | F003 | `count_objects` | 2 |
| F004_1 | F004 | `crop_object` (no adapter mapping) | 1 |
| F004_2 | F004 | `crop_object` | 1 |
| F004_3 | F004 | `crop_object` | 1 |
| F005_1 | F005 | `extract_boundary` (no adapter mapping) | 1 |
| F005_2 | F005 | `extract_boundary` | 1 |
| F006_1 | F006 | `isolate_largest` (no adapter mapping) | 1 |
| F006_2 | F006 | `isolate_largest` | 1 |
| F007_1 | F007 | `mirror_object` (no adapter mapping) | 1 |
| F007_2 | F007 | `mirror_object` | 1 |
| F008_1 | F008 | `crop` (no adapter mapping) | 1 |
| F008_2 | F008 | `crop` | 1 |

---

## 3. Frequency of missing primitives (first blocker)
| Primitive (adapter) | Blocked tasks | Task IDs |
|----------------------|--------------|----------|
| `extract_largest_object` | 6 | F001_1, F001_2, F001_3, F002_1, F002_2, F002_3 |
| `count_objects` | 3 | F003_1, F003_2, F003_3 |
| `crop_object` | 3 | F004_1, F004_2, F004_3 |
| `extract_boundary` | 2 | F005_1, F005_2 |
| `isolate_largest` | 2 | F006_1, F006_2 |
| `mirror_object` | 2 | F007_1, F007_2 |
| `crop` | 2 | F008_1, F008_2 |

The **most common blocker** is `extract_largest_object` (6 tasks).

---

## 4. Impact analysis – which single primitive would unlock the most tasks?
| Primitive (adapter) | Additional tasks unlocked if implemented |
|----------------------|-------------------------------------------|
| `extract_largest_object` | 6 (all F001/F002 variants) |
| `count_objects` | 3 (F003 family) |
| `crop_object` | 3 (F004 family) |
| `extract_boundary` | 2 (F005 family) |
| `isolate_largest` | 2 (F006 family) |
| `mirror_object` | 2 (F007 family) |
| `crop` | 2 (F008 family) |

Implementing **`extract_largest_object`** yields the biggest immediate gain.

---

## 5. Multi‑primitive blocks
Only **F003** tasks are blocked at step 2 after a successful step 1 (`fill_region`). All other families stop at step 1, so they are blocked by a single missing primitive.

---

## 6. Leakage flags & diagnostic metadata
* All tasks report every leakage flag as **false** – verified.
* The field `diagnostic_expected_failure_categories` is retained unchanged and **separated** from solver scoring (`result`).

---

## 7. Baselines
* The 2‑step and single‑step solver scaffolds remain untouched in the repository – no changes detected.

---

## 8. Priority table for primitive implementation
| Primitive (adapter) | # blocked tasks | Task IDs | Required input type | Required output type | Likely local helper source | Risk level | Recommended order |
|----------------------|----------------|----------|---------------------|----------------------|---------------------------|------------|-------------------|
| `extract_largest_object` | 6 | F001_1‑F002_3 | Grid + background value | Grid with largest component extracted | `arc_style_grid_adapter_phase2` already contains implementation (primitive id `extract_largest_object`) – needs mapping in `NAME_TO_ADAPTER_ID` and proper scene/spec generation | Low (already present) | 1 |
| `count_objects` | 3 | F003_1‑F003_3 | Grid | Count summary | No direct primitive in Phase‑2; closest is `object_count_to_pattern` which counts objects – could be repurposed or new helper added. | Medium | 2 |
| `crop_object` | 3 | F004_1‑F004_3 | Grid + crop box | Cropped object grid | No existing primitive; would require a new helper that extracts a sub‑grid. | Medium‑High | 3 |
| `extract_boundary` | 2 | F005_1‑F005_2 | Grid | Boundary representation (list of cells) | No existing primitive; may be derived from `extract_largest_object` + geometry utilities. | Medium | 4 |
| `isolate_largest` | 2 | F006_1‑F006_2 | Grid | Grid containing only the largest component | Could reuse `extract_largest_object` logic; requires thin wrapper. | Low | 5 |
| `mirror_object` | 2 | F007_1‑F007_2 | Grid + axis | Mirrored object grid | No direct primitive; could be built on top of `reflect_object_horizontal_or_vertical`. | Medium | 6 |
| `crop` | 2 | F008_1‑F008_2 | Grid + crop box | Cropped grid | No direct primitive; similar to `crop_to_non_background_bbox` but with explicit box. | Medium | 7 |

**Risk level** reflects development effort and integration testing complexity. All listed primitives are *safe* – they do not touch protected files, external calls, or leakage flags.

---

## 9. Recommended next lane
Given the clear benefit‑to‑effort ratio, the smallest safe next implementation lane is:

**`IMPLEMENT_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_1_V1`**

*Scope:* add the missing mapping for `extract_largest_object` (already implemented in the Phase‑2 adapter) and any thin wrappers needed for `isolate_largest` (which can reuse the same implementation). This will immediately turn the 6 F001/F002 tasks from *unsupported* to *exact*, raising the exact count to **6/20 (30 %)** – a solid foothold for the next batch of primitives.

---

### Validation checklist (post‑creation)
- `git diff --check` – clean
- `python weslr/tests/release_gate_v1.py` – PASS
- `./scripts/weslr_release_check.sh` – PASS
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` – PASS

No push is performed.
