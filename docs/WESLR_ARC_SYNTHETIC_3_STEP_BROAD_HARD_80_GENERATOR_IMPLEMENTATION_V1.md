# ARC Synthetic 3‑Step – Broad Hard‑80 Generator Implementation Report (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `IMPLEMENT_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_V1`
**Start HEAD**: `cb9339e3`

---

## 1. Implementation Summary

### Generator function
- Added `generate_broad_hard_80_tasks()` to `weslr/arc_synthetic_3_step_task_schema.py`
- Emits exactly 80 deterministic task packets (`BH80_001`–`BH80_080`)
- No randomness; all task specs are defined as a static list `_BROAD_HARD_80_SPECS`
- Each task includes: `task_id`, `family_id`, `difficulty`, `primitive_sequence`, `hardness_axes`, `shortcut_defeated`, `scene_spec`, `leakage_flags` (all false), `forbidden_shortcuts`, `expected_trace_requirements`

### Primitive boundary
- 13 core primitives: `extract`, `extract_largest_object`, `isolate_largest`, `extract_boundary`, `crop`, `mirror_object`, `rotate`, `recolor`, `normalize_position`, `place_back`, `count_objects`, `pattern_output`, `transform`
- 8 approved aliases: `remove_noise`, `extract_object`, `crop_object`, `recolor_boundary`, `count`, `count_or_pattern`, `extract_changed_region`, `fill_region`
- Generator validates each primitive at construction time against the allowed set

### Files changed
| File | Change |
|------|--------|
| `weslr/arc_synthetic_3_step_task_schema.py` | Added `_BROAD_HARD_80_SPECS`, `generate_broad_hard_80_tasks()`, boundary constants |
| `weslr/tests/test_broad_hard_80_generator.py` | New test file — 21 focused tests |

### Tests
21 tests covering:
1. Exactly 80 tasks
2. IDs `BH80_001`–`BH80_080` present, no duplicates, in order
3. Every task has exactly 3 primitives
4. All primitives from allowed boundary or approved aliases
5. Allocation: 18 known anchors, 20 hybrid, 20 mutation, 22 unknown‑family
6. Difficulty distribution: 0 easy, 16 medium, 48 hard, 16 adversarial
7. Hardness‑axis difficulty derivation consistent (medium=2–3, hard=4–6, adversarial≥7+axis6)
8. 15 family IDs (F001–F008 + BH‑A through BH‑G)
9. Every task has `hardness_axes`, `shortcut_defeated`, `scene_spec`
10. Leakage flags all false
11. No expected‑output leakage
12. Deterministic output across repeated calls

**Test result: 21 passed in 0.60s**

---

## 2. Validation

| Check | Result |
|-------|--------|
| `py_compile` on `arc_synthetic_3_step_task_schema.py` | PASS ✅ |
| `py_compile` on `test_broad_hard_80_generator.py` | PASS ✅ |
| Focused pytest (`test_broad_hard_80_generator.py`) | 21/21 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 WARN=3 ✅ |

---

## 3. Forbidden Claims

- No public ARC data used ✅
- No hidden/private ARC data used ✅
- No ARC‑AGI benchmark claims ✅
- No external provider API or model calls ✅
- No runtime/chat/UI/provider path changes ✅
- No `.weslr` IO ✅
- No solver or dispatch behavior changes ✅
- No push performed ✅

---

## Receipt

| Field | Value |
|-------|-------|
| **Start HEAD** | `cb9339e3` |
| **End HEAD** | `329ab7ac` |
| **Commit** | yes (`329ab7ac`) |
| **Actual HEAD preflight** | `cb9339e3` ✅ |
| **Metadata consistency verified** | yes ✅ |
| **Generator implemented** | yes ✅ |
| **Exactly 80 tasks generated** | yes ✅ |
| **All IDs BH80_001–BH80_080 present** | yes ✅ |
| **All tasks exactly 3 primitives** | yes ✅ |
| **Primitive boundary valid** | yes ✅ |
| **Aliases approved** | yes ✅ |
| **Allocation verified** | yes (18/20/20/22) ✅ |
| **Difficulty distribution verified** | yes (0/16/48/16) ✅ |
| **Hardness‑axis derivation verified** | yes ✅ |
| **Leakage flags all false** | yes ✅ |
| **Deterministic output** | yes ✅ |
| **Validation** | PASS ✅ |
| **Push avoided** | yes ✅ |
| **Recommended next lane** | `REVIEW_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_V1` |