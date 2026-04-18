# Remediation Test Updates - v1

## New Tests to Add

### 1. Weak Prompt + Later Clarification Recovery
File: `remediation-test-01-weak-prompt-recovery.md`

**Scenario**: User asks vague question, later provides specific context
**Test**: Does Weslr integrate the clarification without restarting?
**Target**: Pass rate 100%

### 2. Continuity After Interruption / Resume
File: `remediation-test-02-continuity-resume.md`

**Scenario**: User leaves and returns, asks "where were we?"
**Test**: Does Weslr recall working context and direction?
**Target**: Pass rate 100%

### 3. Indirect Reference Recovery Across Turns
File: `remediation-test-03-indirect-reference.md`

**Scenario**: User says "that" / "it" / "before" - does Weslr track correctly?
**Test**: Reference tracking across 5+ turns
**Target**: Pass rate 100%

### 4. Evolving User Direction Without Drift
File: `remediation-test-04-evolving-direction.md`

**Scenario**: User changes direction 3x in same session
**Test**: Does Weslr track all directions without losing any?
**Target**: Pass rate 100%

### 5. Continuity Explanation Clarity
File: `remediation-test-05-continuity-explanation.md`

**Scenario**: User asks "how do you know that?" about previous context
**Test**: Does Weslr explain continuity clearly?
**Target**: Pass rate 100%

### 6. Trajectory Confidence Under Ambiguity
File: `remediation-test-06-confidence-under-ambiguity.md`

**Scenario**: Two plausible paths, user wants confidence assessment
**Test**: Does Weslr assess confidence without over-committing?
**Target**: Pass rate 100%

## Updated Old Tests

### Old Test 07 (Conflicting Signals)
**Update**: Add "Ambiguity Status" to expected behavior
**New Target**: 5/5 on all metrics

### Old Test 04 (Correction Path)
**Update**: Add explicit correction documentation to expected behavior
**New Target**: 5/5 on all metrics

### Old Test 01 (Weak Ask + Strong Context)
**Update**: Add explicit context markers to expected behavior
**New Target**: 5/5 on Continuity

### Refinement Test 03 (Balanced Ambiguity)
**Update**: Add path preservation requirement
**New Target**: 5/5 on Path Preservation

## Expected Test Results After Remediation

| Test ID | Name | Target Score |
|---------|------|--------------|
| 01 | weak-ask-strong-context | 5/5 |
| 02 | strong-file-weak-wording | 5/5 |
| 03 | multi-turn-evolving-intent | 5/5 |
| 04 | partial-direction-change | 5/5 |
| 05 | continuity-resumption | 5/5 |
| 06 | indirect-asks | 5/5 |
| 07 | conflicting-signals (updated) | 5/5 |
| 08 | file-conversation-merged | 5/5 |
| 09 | operator-history | 5/5 |
| 10 | long-horizon | 5/5 |
| R01 | file-dominance | 5/5 |
| R02 | conversation-dominance | 5/5 |
| R03 | balanced-ambiguity (updated) | 5/5 |
| R04 | correction-path | 5/5 |
| R05 | multi-turn-recovery | 5/5 |
| R06 | explanation-clarity | 5/5 |
| **New** | weak-prompt-recovery | 5/5 |
| **New** | continuity-resume | 5/5 |
| **New** | indirect-reference | 5/5 |
| **New** | evolving-direction | 5/5 |
| **New** | continuity-explanation | 5/5 |
| **New** | confidence-under-ambiguity | 5/5 |
