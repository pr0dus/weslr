# WESLR ARC Discovery 140 — Frontier Saturation and Dynamic Probe Budget (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `ANALYZE_ARC_DISCOVERY_140_FRONTIER_SATURATION_AND_DYNAMIC_PROBE_BUDGET_V1`
**Start HEAD**: `0592a426`
**Date**: 2026-07-02

---

## 1. Current frontier

- Total tasks: 140
- Scored: 130
- Candidate probes: 10
- Scored exact: 130/130
- BH80: 80/80
- Previous 117 base: 117/117
- New 13 scored: 13/13
- Candidate probes counted as solved: 0
- Anti-cheat: 18/18 pass

## 2. Why the frontier is 10

The current 10-probe frontier is **design-driven**, not statistically derived.

It is the sum of:
- **3 old high-dup-risk controls** retained as unscored guardrails
- **7 new low-dup-risk probes** selected from the remaining candidate pool

So the number 10 is **evidence-informed but conventional**:
- old probes preserve known duplicate-risk checks
- new probes broaden discovery into under-tested families and CC risk
- the frontier size matches the available risk surface, not a fixed universal optimum

## 3. Old vs new probes

### Old high-duplicate-risk controls
- `T120_101` `mask_border_only` — border-vs-boundary distinction
- `T120_102` `geom_flip_vertical` — geometry reflection distinction
- `T120_107` `pat_row_alternate` — pattern-generation distinction

**Signal:** keep known ambiguous / high-overlap candidates unscored so they remain duplicate-risk sentinels.

### New low-duplicate-risk probes
- `T140_134` `geom_scale_2x` — dimension-change / scale stress
- `T140_135` `topo_merge_objects` — connected-components / merge stress
- `T140_136` `constr_connect_line` — connectivity-creation stress
- `T140_137` `constr_copy_to_pos` — multi-object construction / copy stress
- `T140_138` `pat_color_cycle` — pattern-cycle stress
- `T140_139` `cond_if_edge_clip` — edge-clip conditional stress
- `T140_140` `topo_split_at_gap` — gap-finding / split stress

**Signal:** each probes a different frontier gap with low duplicate risk and clearer semantic separation.

## 4. Saturation analysis

### Scored coverage
The 130 scored tasks are not just more volume; they add:
- 13 new composed scored scenes
- all 8 promoted native primitives appearing at least twice in the new scored set
- CC / relation sentinels (`rel_swap_positions`, `sel_leftmost`, `mask_complement`) under stress
- native-to-native and native-to-BH80 composition evidence

### Frontier usefulness
The 10 probes still provide real signal:
- 3 are permanent duplicate-risk controls
- 7 are low-dup discovery candidates
- candidate probes remain uncounted as solved (`0`), so they still separate discovery from scoring

### Is clean 130/130 becoming too easy?
**Not yet.** It is clean, but not trivial:
- the expansion added real composition stress
- CC-sensitive scenes were included
- order sensitivity remained tested
- probe separation still holds

That said, the clean score is now **maturing**: future value will come less from more of the same and more from new frontier classes.

## 5. Is 10 evidence-based or arbitrary?

**Answer:** partly evidence-based, partly convention.

Evidence-based because:
- it preserves 3 known high-dup controls
- it adds 7 low-dup candidates with distinct coverage goals
- it matches the current frontier of known risk classes

Convention because:
- there is no numeric proof that 10 is globally optimal
- the boundary was chosen to balance coverage, noise, and review cost

## 6. Healthy scored/probe ratio

Current ratio:
- `130 / 10 = 13:1`

That is healthy for this stage.

Suggested healthy band:
- **8:1 to 16:1** scored/probe
- with a soft target near **12:1 to 14:1**

Interpretation:
- too low: probes dominate and scoring stops learning
- too high: frontier may be under-probed and the clean score may hide blind spots

## 7. Dynamic probe budget policy

### Recommended policy
- **Minimum probes:** 6
- **Target probes:** `ceil(scored_total / 13)`
- **Maximum probes:** 16

At 130 scored, that target is 10 probes, which matches the current frontier.

### Add probes when
- a new primitive family appears
- a new CC / graph / relation risk appears
- duplicate-risk candidates exist but have no probe evidence
- current probes stop differentiating new compositions

### Promote probes when
- duplicate risk falls below threshold
- a probe is exact in at least 2 independent scored contexts
- it remains distinct from adjacent primitives under CC stress and order reversal
- it no longer behaves like a duplicate-risk sentinel

### Retire probes when
- they are promoted
- they are clearly dominated by a stronger, lower-risk probe
- they stop adding new information and remain permanently ambiguous

### Freeze instead of expand when
- scored tasks are clean
- probes are clean but no new gaps remain
- added tasks would mostly repeat existing compositions
- frontier value is flattening and repair work is more useful than more breadth

## 8. What evidence would change the plan?

### Promote probes if
- solver/oracle agreement becomes stable in repeated scored contexts
- duplicate-risk drops and semantics stay distinct
- the probe fills a real family gap

### Generate more probes if
- a family or structural class is still untested
- new frontier behavior appears (e.g. CC, boundary, topology, edge, copy, split)
- the candidate pool has distinct low-dup items left

### Expand scored tasks if
- promoted primitives have enough evidence to be compositional
- the frontier still has under-tested combinations
- the clean score is stable but coverage is still narrow

### Repair primitives if
- any scored task fails due to oracle/solver mismatch
- a probe reveals a semantic gap in a promoted primitive
- CC divergence or tie-break behavior causes disagreement

### Stop expanding if
- new tasks are repetitive
- no new risk classes are exposed
- probes stop yielding useful differentiation
- maintenance/freeze would preserve more value than another breadth increment

## 9. 120→140 marginal value, and 140→160 estimate

### 120→140 value
High. It added:
- 13 new scored compositions
- 7 new low-dup probes
- explicit CC stress coverage
- broader promoted-native composition evidence

### 140→160 value
Likely **conditional / diminishing**.

It becomes worth doing only if one of these is true:
- new low-dup candidates exist
- a new family gap appears
- CC or graph behavior remains under-tested
- probe saturation is still low relative to scored breadth

If the next 20 tasks would mostly remix the same primitives, value drops fast.

## 10. Dynamic budget conclusion

**Recommendation:** keep the frontier **dynamic**, not fixed.

- Current 10-probe frontier is justified for 140
- It is not arbitrary, but it is also not a permanent optimum
- Maintain a ratio around **12:1–14:1 scored/probe**
- Recompute probe budget whenever scored breadth increases materially

## 11. Validation

To stay within the requested lane, the following gates should hold:
- `git diff --check`
- `python weslr/tests/release_gate_v1.py`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## 12. Receipt

- Start HEAD: `0592a426`
- End HEAD: `0592a426` (analysis-only lane)
- Commit: no
- actual preflight HEAD: `0592a426`
- probe frontier explanation produced: yes
- old vs new probes classified: yes
- dynamic probe budget proposed: yes
- scored/probe ratio analyzed: yes
- 140 saturation analyzed: yes
- 160 expansion value estimated: yes
- recommended next lane: `FREEZE_ARC_SYNTHETIC_DISCOVERY_140_SEMANTIC_GATE_V1` or hold if a dynamic budget lane is preferred
- validation: PASS
- push avoided: yes
