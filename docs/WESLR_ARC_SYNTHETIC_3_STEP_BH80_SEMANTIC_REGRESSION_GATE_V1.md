# WESLR ARC Synthetic 3‑Step – BH80 Semantic Regression Gate (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `FREEZE_BH80_AS_SEMANTIC_REGRESSION_GATE_V1`
**Start HEAD**: `dfe65eb7`
**Frozen at HEAD**: `dfe65eb7`
**Date**: 2026‑07‑01

---

## 1. Frozen Baseline

| Metric | Value |
|--------|-------|
| **semantic_exact** | 80/80 |
| **failed** | 0 |
| **unsupported** | 0 |
| **structural_pass** | 80/80 |
| **semantic_exact_rate** | 100.0% |

**This is the official BH80 semantic regression baseline.** All future solver changes must be verified against this baseline before merging.

---

## 2. Score Progression History

| Lane | Date | semantic_exact | Rate | Notes |
|------|------|---------------|------|-------|
| Structural pilot (pre‑oracle) | 2026‑07‑01 | 80/80 structural_pass | 100% structural | `exact` = all primitives supported, not output equality |
| Anti‑cheat audit | 2026‑07‑01 | — | — | Reclassified as `structural_pass_only_semantic_scoring_missing` |
| First semantic pilot | 2026‑07‑01 | 27/80 | 33.8% | First honest semantic measurement |
| Solver/oracle primitive alignment | 2026‑07‑01 | 50/80 | 62.5% | 5 primitives realigned (extract, extract_changed_region, normalize_position, isolate_largest, extract_boundary) |
| Remaining mismatch repair | 2026‑07‑01 | 80/80 | 100.0% | 5 more wrappers fixed (recolor, recolor_boundary, rotate, place_back, count_or_pattern), oracle pipeline passes canvas context |
| **Frozen baseline** | **2026‑07‑01** | **80/80** | **100.0%** | **This gate** |

---

## 3. Gate Thresholds

| Level | Threshold | Action |
|-------|-----------|--------|
| **Clean** | 80/80 (100%) | Current baseline — no action needed |
| **Preferred expansion** | ≥ 75/80 (93.75%) | May proceed to 120‑task expansion |
| **Strong** | ≥ 72/80 (90%) | Minimum for blocking regression |
| **Minimal** | ≥ 68/80 (85%) | Absolute floor |
| **Below minimal** | < 68/80 | Critical semantic regression — block all changes, investigate |

### Regression policy

1. **Any score below 80/80**: regression requiring written explanation
2. **Below 75/80**: preferred expansion gate lost — 120 expansion blocked
3. **Below 72/80**: strong gate lost — block all solver changes until repaired
4. **Below 68/80**: critical regression — rollback or emergency repair required

---

## 4. Anti‑Cheat Requirements (Frozen)

The following controls must pass for the gate to be valid:

| # | Control | Requirement |
|---|---------|-------------|
| 1 | No `[[1]]` scenes | No task materializes to default `[[1]]` grid |
| 2 | Oracle output diversity | ≥ 20 unique oracle outputs across 80 tasks |
| 3 | Solver output diversity | ≥ 10 unique solver outputs |
| 4 | No‑op shadow control | Replacing primitives with no‑op chain produces different oracle output |
| 5 | Primitive‑order negative control | Reversing primitive order produces different oracle output |
| 6 | Unsupported primitive sentinel | `fake_primitive` returns `unsupported` from both solver and oracle |
| 7 | Oracle avoids solver dispatch | Oracle module does not import or call solver dispatch; verified statically and dynamically |
| 8 | Semantic scorer uses grid equality | `semantic_exact` = solver grid equals oracle grid (element‑wise, dimension‑wise) |
| 9 | structural_pass separate | `structural_pass` is a separate boolean, never reported as `semantic_exact` |

---

## 5. Regression Gate Usage

### When to run the gate
- After **any** change to `weslr/arc_synthetic_3_step_real_dispatch.py`
- After **any** change to `weslr/arc_bh80_oracle.py`
- After **any** change to `weslr/arc_bh80_materializer.py`
- After **any** change to `weslr/arc_bh80_semantic_scorer.py`
- After **any** change to `weslr/arc_bh80_enriched_scenes.py`
- After **any** change to `weslr/arc_synthetic_3_step_task_schema.py`
- Before any 120‑task expansion work

### How to run the gate
```python
from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks
from weslr.arc_bh80_enriched_scenes import get_enriched_scene_spec
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_bh80_oracle import run_oracle_pipeline
from weslr.arc_bh80_solver_adapter import solver_run_with_input
from weslr.arc_bh80_semantic_scorer import grids_equal

tasks = generate_broad_hard_80_tasks()
semantic_exact = 0
for t in tasks:
    t["scene_spec"] = get_enriched_scene_spec(t["task_id"])
    ig = materialize_scene(t["scene_spec"], t["task_id"])
    _, og, _ = run_oracle_pipeline(t["primitive_sequence"], ig)
    ss, sg = solver_run_with_input(ig, t["primitive_sequence"])
    if ss and grids_equal(sg, og):
        semantic_exact += 1
print(f"BH80 semantic_exact: {semantic_exact}/80")
```

### Gate result interpretation
- **80/80**: PASS — no regression, proceed
- **72–79**: WARN — regression detected, investigate before proceeding
- **68–71**: BLOCK — strong gate lost, 120 expansion blocked
- **< 68**: CRITICAL — rollback required

---

## 6. Frozen Components

| Component | File | Role |
|-----------|------|------|
| Generator | `weslr/arc_synthetic_3_step_task_schema.py` | 80 deterministic task packets |
| Materializer | `weslr/arc_bh80_materializer.py` | Scene_spec → concrete grid |
| Oracle | `weslr/arc_bh80_oracle.py` | Independent reference primitives |
| Solver adapter | `weslr/arc_bh80_solver_adapter.py` | Passes materialized grid to dispatch |
| Semantic scorer | `weslr/arc_bh80_semantic_scorer.py` | Grid equality comparison |
| Enriched scenes | `weslr/arc_bh80_enriched_scenes.py` | 80 deterministic scene specs |
| Solver dispatch | `weslr/arc_synthetic_3_step_real_dispatch.py` | Primitive wrappers (aligned to oracle) |

---

## 7. Allowed Future Uses

- Running the gate to verify solver changes
- Adding new anti‑cheat controls (without weakening existing ones)
- Expanding to 120 tasks (after this freeze)
- Adding `semantic_partial` scoring (without removing `semantic_exact`)
- Adding perturbation suite tests

## 8. Forbidden Claims

- No public ARC‑AGI benchmark scores or claims
- No use of public or hidden ARC datasets
- No assertions of autonomous discovery or real‑world evidence intake
- No external provider API or model calls
- No public product readiness claims
- No `.weslr` IO
- No runtime/chat/UI/provider path changes

The BH80 semantic regression gate is an **internal quality tool**. It does not certify external benchmark performance.

---

## 9. 120‑Task Expansion Status

**120 expansion is now ALLOWED.**

All entry conditions are met:

| Condition | Status |
|-----------|--------|
| BH80 oracle exists | ✅ |
| BH80 semantic scoring exists | ✅ |
| No‑op controls fail as expected | ✅ |
| Primitive‑order negative controls fail as expected | ✅ |
| scene_spec is actually read | ✅ |
| Output diversity is nontrivial (≥ 20) | ✅ (27 oracle, 56 solver) |
| At least one semantic BH80 run recorded | ✅ (80/80) |
| BH80 frozen as semantic regression gate | ✅ (this document) |

---

## 10. Validation

| Check | Result |
|-------|--------|
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 ✅ |

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `dfe65eb7` |
| **End HEAD** | `2d919a70` |
| **Commit** | yes (`2d919a70`) |
| **Actual preflight HEAD** | `dfe65eb7` ✅ |
| **Metadata mismatch noted** | no ✅ |
| **BH80 semantic baseline frozen** | yes ✅ |
| **semantic_exact baseline recorded** | yes (80/80) ✅ |
| **failed/unsupported recorded** | yes (0/0) ✅ |
| **Score progression recorded** | yes ✅ |
| **Regression thresholds defined** | yes ✅ |
| **Anti‑cheat requirements frozen** | yes (9 controls) ✅ |
| **120 allowed after freeze** | yes ✅ |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `DESIGN_ARC_SYNTHETIC_3_STEP_SEMANTIC_120_V1` |