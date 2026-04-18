# COGNITIVE_ADEQUACY_DETECTION_PLAN_v1

**Scope:** Doctrine-first detection/assessment plan. No implementation. Uses proposal lineage + observability signals to detect inadequate reasoning/proposal generation and emit governed improvement proposals.

## SECTION 1 — EVIDENCE SOURCES
- Proposal lineage:
  - proposal_id, source_loop_id, workspace_id/user_id
  - trigger_reason, originating_evidence_signal, timestamp, confidence
  - status history, audit trail (views/overrides), checkpoint linkage
- Observability (background analysis surface):
  - loop state, budgets, proposals_recent, proposal_lineage references
  - checkpoints and status for loops
- Background loops:
  - loop ids, recurrence, proposal families emitted, checkpoint history
  - budget usage vs outcomes
- Confidence traces:
  - confidence scores per proposal (from lineage) and per loop iteration
  - trends (declining confidence, flat/unimproved over cycles)
- Ignored/overridden proposals:
  - operator actions (reject/ignore) captured via status history/audit
  - repeated overrides for the same task class or trigger_reason

## SECTION 2 — DETECTION LOGIC
Detect inadequacy when one or more of:
- Repetitive proposal families: same trigger_reason/source_loop with minor deltas across N cycles.
- Shallow depth: proposals lack actionable steps or domain-specific evidence; confidence remains low.
- Low usefulness: high ignore/reject rate by operators for a task class.
- Low confidence streak: repeated low confidence across M consecutive proposals in a loop/task class.
- Same-fix loop: proposals keep suggesting the same fix without observed acceptance or improvement.
- No improvement after cycles: confidence and acceptance do not improve after multiple iterations for the same task class.

## SECTION 3 — ASSESSMENT OUTPUT
Emit a governed assessment bundle:
- adequacy_score (qualitative/ordinal)
- inadequacy_reason (text + category)
- evidence_references (proposal ids, lineage refs, observability checkpoints)
- affected_task_class (loop/task/tag)
- suggested_better_pattern (reasoning/process pattern proposal, no code)
- risk (low/med/high) and why
- approval_needed (yes; route through governance)

## SECTION 4 — GOVERNANCE PATH
- Package assessment as a governed proposal (cognitive-improvement class).
- Route through Governed Activation & Permission Framework; operator/owner approval required.
- Record lineage of the adequacy proposal itself (proposal lineage view) for audit.
- No activation or reasoning changes without approval.

## SECTION 5 — NEXT STEP
- Draft test/validation scenarios for detection logic (doctrine-first), then seek approval before any implementation.
