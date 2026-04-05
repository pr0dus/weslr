# Continuity Remediation - v1

## Causes of Weakness (continuity = 80%)

### Root Causes
1. **Test 01 (weak ask + strong context)**: Context continuity from previous anomaly notes not fully utilized
2. **Test 04 (partial direction change)**: Continuity alignment breaks when user direction shifts mid-workflow
3. **Test 05 (continuity resumption)**: Cross-session state preservation is weak (scores 3/5 on Robustness)
4. **Test 09 (operator history)**: Operator workflow continuity could be more explicit

## Minimal Remediation

### What to Change
1. **Add explicit context continuity markers** to file outputs
2. **Improve cross-session recovery** by persisting working set state
3. **Strengthen continuity explanation** when direction shifts occur

### Additive-Only Fixes
1. Add "Working Context" section to output files showing:
   - Current target
   - Previous state
   - Continuity markers

2. Implement continuity header in files:
   ```
   # Context: [current_target]
   # Continuity: [previous_state]
   # Working Set: [items_in_context]
   ```

3. Explicitly state continuity when resuming:
   "I'm continuing from our previous discussion about [topic]"

## Test Targets

| Test | Current | Target | Fix |
|------|---------|--------|-----|
| 01 | 4 | 5 | Add explicit context markers |
| 04 | 4 | 5 | Strengthen direction shift handling |
| 05 | 3 | 5 | Improve cross-session recovery |
| 09 | 4 | 5 | Better operator history tracking |

## Expected Outcome

- Continuity category score: 80% → 90%+
- Tests pass: 12/15 (80%) → 15/15 (100%)
