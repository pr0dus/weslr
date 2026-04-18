# Core Evaluation Model — Trajectory + Continuity

## Metrics

| Metric | Description | Score Range | Weight |
|--------|-------------|-------------|--------|
| **Trajectory Understanding** | Does Weslr correctly identify where the user is trying to go, even with weak prompts? | 0-5 | 3x |
| **Continuity Alignment** | Does Weslr maintain consistent direction across multiple turns or session restarts? | 0-5 | 3x |
| **Intent Recovery** | When prompts are vague, does Weslr recover intent from context? | 0-5 | 2x |
| **Prompt Independence** | Does Weslr require minimal perfect prompting, or can it work with indirect/ambiguous language? | 0-5 | 1x |
| **Robustness** | Does Weslr handle conflicting signals or partial information gracefully? | 0-5 | 1x |

## NEW: Ambiguity-Specific Metrics (v1 refinement)

| Metric | Description | Score Range | Weight |
|--------|-------------|-------------|--------|
| **Uncertainty Detection** | Does Weslr detect when signals conflict or are ambiguous? | 0-5 | 2x |
| **Explanation Clarity** | Does Weslr explain uncertainty clearly without over-committing? | 0-5 | 3x |
| **Correction Recovery** | Does Weslr handle user corrections and adjust direction gracefully? | 0-5 | 2x |
| **Path Preservation** | Does Weslr preserve both plausible interpretations when appropriate? | 0-5 | 2x |

## Scoring Method

- Each test is scored on the 5-point scale per metric
- Weighted scores are summed and normalized to 0-100
- **Excellent**: 85-100 (Weslr guides user, anticipates needs)
- **Good**: 70-84 (Weslr follows correctly with occasional clarification)
- **Needs Improvement**: 50-69 (Weslr requires frequent user guidance)
- **Weak**: <50 (Weslr fails to maintain direction)

## NEW: Ambiguity Score Sub-Score

- Uncertainty Detection + Explanation Clarity + Correction Recovery + Path Preservation
- Normalized to 0-25 points (added to overall 100-point score)
- Focuses specifically on handling ambiguity and conflicting signals

## Additional Notes

- Tests are designed to stress-test *intent trajectory* rather than raw knowledge
- Success means Weslr understands the *direction* even when the user can't articulate it clearly
- Over-assumption is penalized — confidence in correct direction matters more than speed
