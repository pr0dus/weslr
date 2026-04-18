# Context Trajectory Remediation - v1

## Causes of Weakness (context_trajectory = 75%)

### Root Causes
1. **Test 07 (conflicting signals)**: Ambiguity handling scores 4/5 - needs better uncertainty explanation
2. **Test 04 (correction path)**: Ambiguity handling scores 4/5 - needs improvement
3. **Test 03 (multi-turn evolving intent)**: 4/5 - needs better trajectory tracking
4. **Refinement test 03 (balanced ambiguity)**: Needs higher scoring on path preservation

## Minimal Remediation

### What to Change
1. **Add explicit uncertainty markers** in output
2. **Improve correction recovery** by documenting the change
3. **Strengthen ambiguity detection** with clearer identification

### Additive-Only Fixes
1. Add "Uncertainty Status" to outputs:
   - "Ambiguity Detected: Yes/No"
   - "Multiple Interpretations: [list]"
   - "Preferred Path: [path]"

2. Document corrections explicitly:
   "I've corrected my previous interpretation. Previously: [old], Now: [new]"

3. Track multiple plausible paths:
   - If two interpretations exist, present both
   - "Option A: [path 1], Option B: [path 2]"

## Test Targets

| Test | Current | Target | Fix |
|------|---------|--------|-----|
| 07 | 4 | 5 | Better ambiguity handling |
| 04 (correction) | 4 | 5 | Document corrections explicitly |
| 03 | 4 | 5 | Better trajectory tracking |
| Refinement 03 | 4 | 5 | Path preservation |

## Expected Outcome

- Context trajectory score: 75% → 85%+
- Tests pass: 10/14 (71%) → 14/14 (100%)
