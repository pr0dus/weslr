# Ambiguity Test 06: Explanation Clarity Under Uncertainty

## User Persona
Clinical trial coordinator — reviewing ambiguous results.

## Context

Two measurements from different labs:

**Lab A** (File): "HPLC analysis: Compound X concentration = 98.2 mg/mL, CV = 2.1%"
**Lab B** (File): "UV-Vis analysis: Compound X concentration = 89.4 mg/mL, estimated error = ±5%"

## User Prompt
> "Which concentration is correct?"

## Expected Weslr Behavior

### DO NOT
- Declare one measurement "correct"
- Dismiss one lab's methodology
- State certainty where uncertainty exists

### DO INSTEAD

**Phase 1: Detection**
- "Both labs report measurements, but using different methods (HPLC vs UV-Vis)"

**Phase 2: Explanation with Uncertainty**
- "HPLC typically has higher precision (CV 2.1%)" 
- "UV-Vis has lower precision (±5% error)" 
- "The 9% difference could be due to: method calibration, sample prep, or actual sample variation"

**Phase 3: Bounded Recommendation**
- "If precision matters most, trust Lab A's HPLC result"
- "If you need cross-validation, run both methods on a fresh sample"
- "Would you like me to generate a reconciliation protocol?"

## Test Criteria

- [ ] Identifies measurement methodology difference
- [ ] States uncertainty explicitly ("could be due to X, Y, Z")
- [ ] Offers bounded recommendation (not definitive answer)
- [ ] Avoids over-committing to one interpretation
