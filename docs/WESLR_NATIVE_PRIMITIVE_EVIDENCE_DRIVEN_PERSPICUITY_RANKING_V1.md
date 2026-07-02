# WESLR Native Primitive Evidence-Driven Perspicuity Ranking (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `UPGRADE_WESLR_NATIVE_PRIMITIVE_GENERATOR_WITH_EVIDENCE_DRIVEN_PERSPICUITY_V1`
**Start HEAD**: `5455610e`
**End HEAD**: `cd82b9af`
**Date**: 2026-07-02

---

## 1. Preflight

| Check | Result |
|-------|--------|
| `pwd` | `/data/data/com.termux/files/home/weslr-pr47-clean` ✅ |
| `git status` | one modified file (`weslr/tests/continuity/governance_scorecards.json` — auto-generated timestamp drift, pre-existing) ✅ |
| `git branch --show-current` | `occ-discovery-doctrine-implementation-20260613` ✅ |
| `git rev-parse --short HEAD` | `5455610e` ✅ matches expected |

**Actual preflight HEAD**: `5455610e`
**Metadata mismatch noted**: no — receipt HEAD matches actual.

---

## 2. Current Perspicuity Limitations (Audited)

### Existing 7-dimensional static scoring

| Dimension | What it measures | Limitation |
|-----------|-----------------|------------|
| clarity | Internal validity (typed, hashable) | Always 1.0 — no discriminative power |
| minimality | Expression length | Only measures brevity, not semantic simplicity |
| non_duplication | Content hash uniqueness | Only detects exact duplicates, not semantic near-duplicates |
| compositional_depth | Expression structure depth | Heuristic only, not evidence-based |
| testability | Deterministic + typed | Always 1.0 — no discriminative power |
| expected_usefulness | Family-based heuristic | Static, doesn't use probe or run evidence |
| shortcut_risk | Hardcoded 0.3 (or 0.8 for identity/noop) | No per-candidate analysis |

### Missing features identified

| Feature | Why it matters |
|---------|---------------|
| Semantic probe evidence | Whether candidate appears in T120_101–T120_110 and has a proven composable chain |
| Promotion cost | Oracle/solver implementation complexity estimate |
| Oracle implementability | How hard is the oracle reference to write |
| Solver implementability | How hard is the solver target to write |
| Task-space expansion value | How much new task variety this primitive enables |
| Duplicate-with-existing risk | Semantic similarity to BH80/promoted primitives (not just hash equality) |
| BH80 regression risk | Risk of breaking BH80 or 120 scored results |
| 120 usefulness | Whether candidate has a probe task in the 120 suite |
| Candidate-probe diagnostic value | Whether the probe chain exercises the candidate meaningfully |
| Expected denominator gain | How many new scored tasks promotion would add |

---

## 3. Upgraded Ranking Model

### Evidence-driven scoring weights

| Component | Weight | Source |
|-----------|--------|--------|
| Static perspicuity | 25% | Existing 7-dimensional score |
| Probe availability | 10% | Does candidate appear in T120_101–T120_110? |
| Promotion ease | 20% | Inverse of promotion difficulty (oracle + solver complexity) |
| Task-space value | 20% | New family bonus + probe bonus + composability |
| Non-duplicate | 10% | Inverse of semantic similarity to existing primitives |
| Non-regression | 10% | Inverse of regression risk (dimension changes, connectivity changes) |
| Non-shortcut | 5% | Inverse of shortcut risk |

### Evidence features per candidate

Each candidate receives an `EvidenceFeatures` dataclass with:
- `static_perspicuity`: float (from existing scoring)
- `has_probe_task`: bool (candidate appears in 120 probe tasks)
- `probe_task_id`: Optional[str] (which T120 task)
- `probe_chain`: Optional[str] (what 3-step chain)
- `oracle_complexity`: float 0.0-1.0 (implementation complexity estimate)
- `solver_complexity`: float 0.0-1.0
- `promotion_difficulty`: float 0.0-1.0 (combined + testing overhead)
- `task_space_value`: float 0.0-1.0
- `new_family`: bool (introduces a genuinely new transform family)
- `expected_denominator_gain`: int (new scored tasks if promoted)
- `duplicate_risk`: float 0.0-1.0 (semantic similarity to existing primitives)
- `regression_risk`: float 0.0-1.0
- `shortcut_risk`: float 0.0-1.0
- `is_promoted`: bool
- `recommendation`: "promote_now" | "defer" | "discard" | "already_promoted"
- `reason_codes`: List[str] (explainable reasons)

### Recommendation logic

- **promote_now**: score ≥ 0.65, promotion difficulty < 0.5
- **defer**: score ≥ 0.55 but high difficulty/risk or no probe task
- **discard**: score < 0.55 with high shortcut/duplicate risk or low task-space value
- **already_promoted**: color_invert (excluded from ranking)

---

## 4. Duplicate Risk Assessment

Semantic similarity map defines the closeness of each candidate to existing BH80/promoted primitives:

| Candidate | Similar to | Similarity | Risk level |
|-----------|-----------|-----------|------------|
| geom_translate_center | normalize_position | 0.7 | High |
| mask_border_only | extract_boundary | 0.6 | Medium-high |
| geom_flip_vertical | transform | 0.6 | Medium-high |
| pat_row_alternate | pattern_output | 0.6 | Medium-high |
| color_swap_1_2 | recolor | 0.5 | Medium |
| sel_leftmost | extract | 0.5 | Medium |
| color_dominant | recolor | 0.5 | Medium |
| cond_if_multi_count | count_or_pattern | 0.5 | Medium |
| constr_extend_pattern | pattern_output | 0.5 | Medium |
| topo_fill_holes | fill_region | 0.4 | Low-medium |
| constr_draw_rect_around | extract_boundary | 0.4 | Low-medium |
| mask_complement | recolor | 0.3 | Low |
| sel_leftmost/topmost/smallest | extract | 0.4-0.5 | Low-medium |

---

## 5. Top Candidate Ranking

### Summary

| Category | Count |
|----------|-------|
| Total candidates | 32 |
| Already promoted | 1 (color_invert) |
| Promote now | 13 |
| Defer | 18 |
| Discard | 0 |

### Top 10 recommendations

| Rank | Primitive ID | Score | Recommendation | Key reasons |
|------|-------------|-------|----------------|-------------|
| 1 | mask_complement | 0.8045 | promote_now | probe task, new family, low difficulty (0.35), low dup risk (0.30), simple oracle |
| 2 | constr_draw_rect_around | 0.7938 | promote_now | probe task, new family, low difficulty (0.35), low dup risk (0.40) |
| 3 | sel_leftmost | 0.7755 | promote_now | probe task, new family, low difficulty (0.35), medium dup risk (0.50) |
| 4 | topo_fill_holes | 0.7650 | promote_now | probe task, new family, low dup risk (0.40), moderate difficulty (0.45) |
| 5 | mask_border_only | 0.7580 | promote_now | probe task, new family, simple oracle, medium-high dup risk (0.60) |
| 6 | color_swap_1_2 | 0.7336 | promote_now | probe task, very simple oracle (0.10), low difficulty (0.25) |
| 7 | rel_swap_positions | 0.7311 | defer | probe task, new family, but high promotion difficulty (0.65) |
| 8 | geom_flip_vertical | 0.7213 | promote_now | probe task, very simple oracle (0.10), but medium-high dup risk (0.60) |
| 9 | pat_row_alternate | 0.7005 | promote_now | probe task, simple oracle (0.20), medium-high dup risk (0.60) |
| 10 | cond_if_holes_fill | 0.6920 | defer | probe task, new family, but high shortcut risk (0.80), moderate difficulty (0.55) |

---

## 6. Batch 2 Reassessment

### Original Batch 2

| Candidate | Rank | Score | Recommendation |
|-----------|------|-------|----------------|
| constr_draw_rect_around | #2 | 0.7938 | promote_now ✅ |
| topo_fill_holes | #4 | 0.7650 | promote_now ✅ |
| mask_border_only | #5 | 0.7580 | promote_now ✅ |
| geom_flip_vertical | #8 | 0.7213 | promote_now ✅ |

### Revised Batch 2 (evidence-driven)

| Candidate | Rank | Score | Key advantage over original |
|-----------|------|-------|---------------------------|
| mask_complement | #1 | 0.8045 | Highest score; lowest duplicate risk (0.30); lowest regression risk (0.15); simple oracle |
| constr_draw_rect_around | #2 | 0.7938 | Retained — new family, simple oracle, low risk |
| sel_leftmost | #3 | 0.7755 | Replaces geom_flip_vertical — new family (object_selector), lower dup risk (0.50 vs 0.60) |
| topo_fill_holes | #4 | 0.7650 | Retained — new family (topology), low dup risk (0.40) |

### Reassessment verdict

**Revision needed: yes.**

The original Batch 2 is replaced by:
- `mask_complement` replaces `geom_flip_vertical` (higher score, lower risk, new family)
- `sel_leftmost` replaces `mask_border_only` (higher score, lower duplicate risk, new family)

`constr_draw_rect_around` and `topo_fill_holes` are retained from the original batch.

The dropped candidates (`geom_flip_vertical` and `mask_border_only`) remain `promote_now` but rank lower due to higher duplicate risk (0.60 each vs 0.30 and 0.50 for the replacements).

---

## 7. Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `weslr/native_arc_perspicuity.py` | Evidence-driven perspicuity ranking module | ~680 |
| `weslr/tests/test_native_arc_perspicuity_ranking.py` | 30 focused tests | ~310 |

### Files not modified

- Candidate generator (`native_arc_candidate_generator.py`) — unchanged ✅
- Native arc language schema — unchanged ✅
- Native arc oracle/solver — unchanged ✅
- Native arc promotion pilot — unchanged ✅
- 120 generator — unchanged ✅
- 120 pilot runner — unchanged ✅
- BH80 components — unchanged ✅
- Protected files — unchanged ✅

---

## 8. Tests Added

| Test class | Tests | Purpose |
|------------|-------|---------|
| TestDeterminism | 3 | Ranking is deterministic and stable |
| TestTopNRecommendation | 6 | Top-N is stable, excludes promoted, has reason codes and risk flags |
| TestPromotedRecognition | 2 | color_invert recognized as already promoted |
| TestUnpromotedBlocked | 2 | Unpromoted candidates not counted as solved |
| TestDuplicateRiskPenalty | 3 | High-duplicate candidates penalized; geom_translate_center flagged |
| TestDeferBehavior | 2 | High-complexity candidates deferred; rel_swap_positions deferred |
| TestBatch2Reassessment | 5 | Batch 2 is explainable, has 4 recommendations, covers original 4 |
| TestEvidenceFeatures | 4 | All candidates have evidence; probes detected; new family flag correct |
| TestBH80Unchanged | 3 | BH80 not modified; 110 scored maintained; 120 pilot still 110/110 |
| **Total** | **30** | All PASS ✅ |

---

## 9. BH80 Unchanged Confirmation

| Check | Result |
|-------|--------|
| BH80 task count | 80 ✅ |
| 120 scored_total | 110 ✅ |
| 120 candidate_probe_total | 10 ✅ |
| 120 semantic pilot scored_exact | 110/110 ✅ |
| 120 semantic pilot BH80 subset | 80/80 ✅ |
| No BH80 files modified | ✅ |
| No promotion of new primitives | ✅ |
| No oracle/solver implementations added | ✅ |

---

## 10. Validation

| Check | Result |
|-------|--------|
| `py_compile` perspicuity module | PASS ✅ |
| Focused pytest (30 tests) | 30/30 PASS ✅ |
| Related suites (185 tests) | 185/185 PASS ✅ |
| `git diff --check` | clean ✅ |
| `python weslr/tests/release_gate_v1.py` | `WESLR_RELEASE_GATE_V1_OK` ✅ |
| `./scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK` ✅ |
| `./scripts/chat_weslr_de_health_check.sh --mode source-repo` | PASS=6 FAIL=0 WARN=3 ✅ |

---

## 11. Receipt

| Field | Value |
|-------|-------|
| Start HEAD | `5455610e` |
| End HEAD | `cd82b9af` |
| Commit | yes (`cd82b9af`) |
| Actual preflight HEAD | `5455610e` |
| Metadata mismatch noted | no |
| Current perspicuity limitations audited | yes ✅ (7 dimensions, 10 missing features identified) |
| Evidence-driven ranking implemented | yes ✅ (7-component weighted scoring with 14 evidence features) |
| Promotion cost included | yes ✅ (oracle + solver complexity + testing overhead) |
| Task-space value included | yes ✅ (new family bonus + probe bonus + composability) |
| Duplicate risk included | yes ✅ (semantic similarity map for all 32 candidates) |
| Regression risk included | yes ✅ (duplicate risk + dimension change + connectivity change) |
| Top-N recommendation produced | yes ✅ (top 10 with reason codes, risk flags, difficulty) |
| Batch 2 reassessed | yes ✅ (revision needed: mask_complement and sel_leftmost replace geom_flip_vertical and mask_border_only) |
| Unpromoted candidates still blocked | yes ✅ |
| BH80 unchanged | yes ✅ (80/80, 110/110 maintained) |
| Validation | PASS ✅ |
| Push avoided | yes ✅ |
| Recommended next lane | `DESIGN_ARC_NATIVE_PROMOTION_BATCH_2_V1` |

---

## 12. Next Lane Recommendation

**Recommended next lane**: `DESIGN_ARC_NATIVE_PROMOTION_BATCH_2_V1`

This lane should design the promotion pipeline for the revised Batch 2:
1. `mask_complement` — mask algebra, oracle ~15 lines, solver ~15 lines
2. `constr_draw_rect_around` — construction, oracle ~20 lines, solver ~20 lines
3. `sel_leftmost` — object selector, oracle ~15 lines, solver ~20 lines
4. `topo_fill_holes` — topology, oracle ~25 lines, solver ~30 lines

Each must go through the full 9-stage promotion pipeline:
```
generated → typed → executable → oracle_defined → solver_targeted →
tested → anti_cheat_validated → regression_safe → promoted
```

After promotion, the 120 suite should be rerun with:
- These 4 candidates moved from `candidate_probe` to `scored`
- Scored denominator increases from 110 to 114 (or more with new task generation)
- BH80 must remain 80/80
- Anti-cheat controls must remain all-pass