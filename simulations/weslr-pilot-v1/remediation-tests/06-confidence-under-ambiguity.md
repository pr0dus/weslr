# Context Trajectory Remediation Test 06: Trajectory Confidence Under Ambiguity

## User Persona
Clinical trial coordinator — needs confidence assessment for ambiguous data.

## Context

Two measurements from different labs:

**Lab A**: "HPLC: Compound X = 98.2 mg/mL, CV = 2.1%"
**Lab B**: "UV-Vis: Compound X = 89.4 mg/mL, estimated error = ±5%"

## User Prompt
> "What's your confidence in the value?"

## Expected Weslr Behavior

**Confidence Assessment:**
- "Confidence in exact value: Low (89.4-98.2 range suggests method differences)"
- "Confidence in relative comparison: High (both methods agree on magnitude)"

**Ambiguity Transparency:**
- "I have two plausible interpretations:"
  - Interpretation 1: Lab A's HPLC is more precise (CV 2.1% vs ±5% error)
  - Interpretation 2: Lab B's UV-Vis may be measuring a different form of Compound X
- "My preferred interpretation: Lab A's HPLC (higher precision)"

**Recommendation with Confidence:**
- "I'm 75% confident the value is closer to 98 mg/mL based on HPLC precision"
- "I'm 25% confident there's a measurement difference that needs investigation"
- "Would you like me to recommend a reconciling test?"

## Test Criteria

- [ ] States confidence explicitly (not vague)
- [ ] Identifies multiple plausible interpretations
- [ ] Prefers one interpretation with justification
- [ ] Provides confidence percentage for path
- [ ] Recommends next steps when uncertain
- [ ] Does NOT over-commit to single answer

## Target Score: 5/5
