# COGNITIVE_ADEQUACY_FIXTURES_HARNESS_v1

**Scope:** Doctrine-first fixture and harness case design for Cognitive Adequacy Detection. No runtime code. Prepares implementation-ready inputs and expected outputs.

## SECTION 1 — FIXTURE PLAN (REUSABLE FAMILIES)
- Proposal lineage fixtures: minimal records with proposal_id, source_loop_id, workspace_id/user_id, trigger_reason, originating_evidence_signal, timestamp, confidence, status_history, audit_log, linked_checkpoint.
- Observability/loop fixtures: loop_id, workspace_id/user_id, proposals_recent with lineage refs, checkpoints, budget_used/cap.
- Confidence trace fixtures: per-proposal confidence values over iterations; trend windows.
- Status/audit fixtures: reject/ignore/approve actions, view counts per proposal/task class.
- Operator-requested repetition fixtures: flag on proposals/loops indicating intentional repetition.
- Exploratory-budget fixtures: markers for early exploratory passes and improving confidence trend.

## SECTION 2 — HARNESS CASES
- Repetitive shallow proposals: lineage+loop fixtures showing ≥3 similar proposals in one task class; expect inadequacy.
- Repeated rejects/ignores: status/audit fixtures with ≥60% rejects/ignores over 5 proposals; expect inadequacy.
- Low-confidence streaks: confidence trace with <0.4 across 3 consecutive proposals; expect inadequacy.
- Same-fix loops: same fix/category emitted 3 times without acceptance; expect inadequacy.
- No improvement across cycles: two windows (size 4) with no confidence/acceptance lift; expect inadequacy.
- Evidence-to-action failure: 2+ proposals in window of 4 that cite evidence but have no actionable steps; expect inadequacy.
- False-positive guards: 
  - operator-requested repetition → no trigger;
  - low sample (<3 proposals) → no trigger;
  - exploratory window (first 3) with improving confidence (+0.05/step) → no trigger.

## SECTION 3 — EXPECTED OUTPUT BUNDLES (PER CASE)
- Adequacy score: decrease on inadequacy cases; stay neutral on guarded cases.
- Inadequacy reason: scenario-specific label (repetition, low usefulness, low confidence, same-fix, no improvement, evidence-to-action failure).
- Evidence references: proposal_ids, lineage refs, confidence traces, status/audit refs, checkpoints as applicable.
- Cognitive-improvement proposal: emit for inadequacy cases; suppress when guard applies.

## SECTION 4 — NEXT STEP
- Build detailed fixture instances per case and approval for implementation; then proceed to code the harness using these fixtures.
