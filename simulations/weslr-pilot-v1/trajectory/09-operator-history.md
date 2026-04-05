# Trajectory Test 09: Operator History Affecting Next Intent

## User Persona
Quality control operator — maintains continuity across batches.

## History
- Operator has reviewed 5 batches this week: 2026-035 through 2026-039
- Previous decision: "Batch-2026-038 failed out-of-spec on parameter X; root cause: vendor C contaminant"
- Operator input: "run the same checks on batch 2026-041 and alert me if we see the same pattern"

## Expected Weslr Behavior
- Recognizes "same checks" and "same pattern" from previous analysis
- Re-uses analysis pipeline from Batch-2026-038 (parameter X, vendor C contaminant check)
- Applies to new batch and alerts if pattern matches
- Links to previous incident for comparison

## Test Criteria
- [ ] Identifies "same checks" from previous batch analysis
- [ ] Re-uses analysis pipeline without reconfiguration
- [ ] Compares against previous incident pattern
- [ ] Alerts with matching threshold
