# WESLR ARC GENERATIVE BRIDGE V5 REPLAY EMITTER DECISION RULE ADDENDUM V1

## 1. Executive verdict
`arc_generative_bridge_v5_replay_emitter_decision_rule_addendum_ready`

## 2. Purpose

Define MDL generator-health handling. High MDL-only rejection indicates generator may be overproducing weak/elegance-driven candidates.

## 3. Qualitative Diagnostic

**Metric:** `mdl_only_rejected_count`

## 4. Derived Flag

**Flag:** `generator_health_warning = True` if either:
- `mdl_only_rejected_count / candidate_generation_attempt_count >= 0.25`, OR
- `mdl_only_rejected_count / attempted_tasks >= 0.20`

## 5. Interpretation

MDL-only rejection is NOT an automatic emitter hard-stop if main safety gate passes.

**Reason:** Rejecting MDL-only candidates means the assembler is doing its job.

**But:** High MDL-only rejection means the generator may be overproducing weak candidates.

## 6. Consequence

If emitter gate passes AND `generator_health_warning == True`:
- `DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1` may proceed only as design/boundary lane
- `ANALYZE_ARC_CONTROLLED_GENERATOR_HEALTH_V1` becomes mandatory before any emitter implementation
- Do NOT proceed directly to emitter implementation
- Do NOT treat generator as healthy merely because emitter threshold passed

**Wording:** "High MDL-only rejection does not invalidate a clean emitter-boundary design decision, but it blocks emitter implementation until generator-health analysis is completed."

---

MDL generator-health warning defined: yes
Soft gate implemented: yes
Consequence defined: yes
Final judgment: arc_generative_bridge_v5_replay_emitter_decision_rule_addendum_ready