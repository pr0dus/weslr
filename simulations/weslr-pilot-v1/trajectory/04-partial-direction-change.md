# Trajectory Test 04: Partial User Direction Changes

## User Persona
Enterprise operator managing ongoing analysis pipeline — direction shifts mid-workflow.

## Initial State
- User has a running analysis pipeline for "Batch-2026-039"
- Previous output: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/batch-2026-039-analysis.csv`
- Task: "validate quality control metrics"

## Mid-Workflow Direction Change
User: "actually, shift focus to the supplier variance analysis — look at the last three batches and see if we can isolate which vendor introduced the outliers"

## Expected Weslr Behavior
- Recognize the workflow shift from QC validation to supplier variance analysis
- Pull in data from last three batches (2026-036, 2026-037, 2026-038)
- Cross-reference supplier IDs with batch metadata
- Identify outliers and trace back to specific vendors with confidence

## Test Criteria
- [ ] Detects direction change without requiring restart
- [ ] Retrieves relevant batch history
- [ ] Correlates supplier IDs with outlier patterns
- [ ] Identifies responsible vendor(s) with supporting evidence
