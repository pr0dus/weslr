# COGNITIVE_ADEQUACY_TEST_HARNESS_PLAN_v1

**Scope:** Doctrine-first harness design for Cognitive Adequacy Detection. No implementation. Targets measurable validation of inadequacy detection before runtime code.

## SECTION 1 — HARNESS TARGET
Simulate and verify detection for:
- Repetitive shallow proposals.
- Repeated rejects/ignores.
- Repeated low-confidence streaks.
- Same-fix loops.
- No improvement after multiple cycles.
- Evidence-to-action failure.

## SECTION 2 — INPUT SHAPE (MINIMAL SYNTHETIC FIXTURES)
- Proposal lineage records (proposal_id, source_loop_id, workspace_id/user_id, trigger_reason, originating_evidence_signal, timestamp, confidence, status history, audit trail, linked_checkpoint).
- Confidence traces (per proposal and per loop iteration; trend windows).
- Status/audit histories (reject/ignore/approve actions, view counts).
- Loop families (loop_id/task class tagging, iteration order, checkpoints).
- Trend windows (N-cycle windows for improvement/no-improvement checks).
- Operator-requested repetition flags (to suppress false positives).
- Exploratory budget markers (to allow early low confidence without triggering).

## SECTION 3 — EXPECTED OUTPUTS (PER SCENARIO)
- Adequacy score trend (should drop on inadequacy; stay neutral when guard conditions apply).
- Inadequacy reason (scenario-specific text/category).
- Evidence references (lineage IDs, confidence traces, audit/status refs, checkpoints).
- Cognitive-improvement proposal emission: required for inadequacy scenarios; suppressed when guard conditions apply.
- Non-emission cases: when guards/thresholds indicate no inadequacy (e.g., explicit operator repetition, low sample, improving exploration).

## SECTION 4 — FALSE POSITIVE TESTS
- Operator-requested repetition (explicit flag) → no inadequacy trigger.
- Low sample count (below minimum cycles/window) → no inadequacy trigger.
- Temporary exploratory low confidence with improving trend and within exploratory budget → no inadequacy trigger.

## SECTION 5 — NEXT STEP
- Map these scenarios into concrete test cases/fixtures and thresholds, then seek approval before implementation.
