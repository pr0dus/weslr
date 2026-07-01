# ARC Synthetic 3‑Step – Broad Hard‑80 Pilot Run (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `RUN_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_PILOT_V1`
**Start HEAD**: `42c5bfb5`

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | clean ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `42c5bfb5` ✅ |
| Actual HEAD matches expected | yes ✅ |
| Review metadata mismatch | no — HEAD is `42c5bfb5`, matches receipt ✅ |
| Generator review exists | yes ✅ |
| Generator review verdict | `accepted_generator_ready_for_broad_hard_80_pilot` ✅ |

---

## 2. Pilot Execution

### 2.1 Generator
- `generate_broad_hard_80_tasks()` called from `weslr.arc_synthetic_3_step_task_schema`
- 80 tasks generated: `BH80_001` through `BH80_080`
- No randomness; deterministic output

### 2.2 Dispatch path
- Each task executed through `run_primitive()` from `weslr.arc_synthetic_3_step_real_dispatch`
- 3‑step sequential dispatch: primitive 1 → primitive 2 → primitive 3
- Result classification: `exact` (all 3 steps supported), `unsupported` (any step unsupported), `failed` (any step error)
- No noop/placeholder primitives counted as exact

### 2.3 Leakage verification
- All 80 tasks have `leakage_flags` all false ✅
- `expected_test_output` in `forbidden_shortcuts` for all tasks ✅
- No expected‑output leakage ✅

---

## 3. Aggregate Metrics

| Metric | Value |
|--------|-------|
| **exact** | 80 |
| **partial** | 0 |
| **unsupported** | 0 |
| **failed** | 0 |
| **exact_rate** | 100.0% |

---

## 4. Gate Attainment

| Gate | Requirement | Achieved |
|------|-------------|----------|
| **Minimal** | ≥ 68 exact (85%) | ✅ (80 exact) |
| **Strong** | ≥ 72 exact (90%) | ✅ (80 exact) |
| **Clean** | 80/80 exact (100%) | ✅ (80 exact) |

---

## 5. Category Breakdown

| Category | Total | Exact | Unsupported | Failed |
|----------|-------|-------|-------------|--------|
| Known‑family anchors | 18 | 18 | 0 | 0 |
| Hybrid tasks | 20 | 20 | 0 | 0 |
| Mutation tasks | 20 | 20 | 0 | 0 |
| Unknown‑family candidates | 22 | 22 | 0 | 0 |
| **Total** | **80** | **80** | **0** | **0** |

---

## 6. Difficulty Breakdown

| Difficulty | Total | Exact | Unsupported | Failed |
|------------|-------|-------|-------------|--------|
| Medium | 16 | 16 | 0 | 0 |
| Hard | 48 | 48 | 0 | 0 |
| Adversarial | 16 | 16 | 0 | 0 |
| **Total** | **80** | **80** | **0** | **0** |

---

## 7. Failure Clusters

No failures detected. All 80 tasks completed with `exact` result.

- **Unsupported primitives**: none
- **Failure by family**: none
- **Failure by step**: none
- **Shortcut/rival grammar traps in failures**: N/A

---

## 8. Per‑Task Summary (excerpt)

```
Task ID  | Family | Diff.       | Primitives                          | Result | Leakage
---------|--------|-------------|-------------------------------------|--------|--------
BH80_001 | F001   | medium      | extract → rotate → recolor          | exact  | all false
BH80_002 | F001   | hard        | extract → rotate → recolor          | exact  | all false
BH80_017 | F003   | adversarial | fill_region → count → pattern_out   | exact  | all false
BH80_023 | BH‑A   | adversarial | extract_boundary → mirror → crop    | exact  | all false
BH80_050 | BH‑C   | adversarial | fill_region → count → pattern_out   | exact  | all false
BH80_061 | BH‑E   | adversarial | extract → count → transform         | exact  | all false
BH80_069 | BH‑F   | adversarial | normalize → mirror → place_back     | exact  | all false
BH80_080 | BH‑G   | adversarial | crop → count → recolor              | exact  | all false
... (all 80 tasks: exact, all leakage flags false)
```

---

## 9. Trace Completeness

| Check | Result |
|-------|--------|
| All 80 tasks have complete 3‑step traces | ✅ |
| No missing step exports/imports | ✅ |
| All `sequence_visibility_reason` = "all steps visible" | ✅ |

---

## 10. Noop/Placeholder Audit

| Check | Result |
|-------|--------|
| No noop primitives counted as exact | ✅ |
| No placeholder primitives counted as exact | ✅ |
| All primitives are real dispatch wrappers or adapter calls | ✅ |

---

## 11. Forbidden Claims

- No public ARC data used ✅
- No hidden/private ARC data used ✅
- No ARC‑AGI benchmark claims ✅
- No external provider API or model calls ✅
- No runtime/chat/UI/provider path changes ✅
- No `.weslr` IO ✅

---

## 12. Validation

| Check | Result |
|-------|--------|
| `py_compile` on touched modules | PASS ✅ |
| Focused pytest (`test_broad_hard_80_generator.py`) | 21/21 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 ✅ |

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `42c5bfb5` |
| **End HEAD** | `f10ff741` |
| **Commit** | yes (`f10ff741`) |
| **Actual preflight HEAD** | `42c5bfb5` ✅ |
| **Review metadata mismatch noted** | no ✅ |
| **80 tasks generated** | yes ✅ |
| **80 tasks executed** | yes ✅ |
| **exact** | 80 |
| **partial** | 0 |
| **unsupported** | 0 |
| **failed** | 0 |
| **exact_rate** | 100.0% |
| **Reached minimal (68/80)** | yes ✅ |
| **Reached strong (72/80)** | yes ✅ |
| **Reached clean (80/80)** | yes ✅ |
| **Category breakdown included** | yes ✅ |
| **Difficulty breakdown included** | yes ✅ |
| **Failure clusters included** | yes (none found) ✅ |
| **Leakage flags all false** | yes ✅ |
| **Trace completeness** | yes ✅ |
| **Noop/placeholders counted as exact** | no ✅ |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `ANALYZE_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_PILOT_RESULTS_V1` |