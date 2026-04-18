# Context Trajectory Remediation Test 03: Indirect Reference Recovery Across Turns

## User Persona
Research team lead — uses natural indirect references.

## Session Flow

**Turn 1**: User: "Show me the new catalyst samples"

**Turn 2**: Weslr provides: "Catalyst A, B, C — all from Batch-2026-043"

**Turn 3**: User: "What about *that* one with the 15% conversion?"

**Turn 4**: User: "And *it* — the same sample but with the higher temperature"

**Turn 5**: User: "How does *that* compare to *the one* we tested last month?"

## Expected Weslr Behavior

**Reference Tracking:**
- Turn 3: "*that*" = Catalyst with 15% conversion (Catalyst B)
- Turn 4: "*it*" = Same sample (Catalyst B) but higher temperature
- Turn 5: "*that*" = Catalyst B at high temp, "*the one*" = previous month's test

**Working Set Management:**
- Maintains working set of referenced items
- Tracks transformation chain (original → 15% conversion → higher temp)

**Clarity Phase:**
- If uncertain: "I'm tracking Catalyst B at high temp vs last month's test. Is that correct?"
- If certain: Proceeds with comparison

## Test Criteria

- [ ] Correctly identifies all indirect references (*that*, *it*, *the one*)
- [ ] Maintains working set of referenced items
- [ ] Tracks transformation chain across turns
- [ ] Clarifies if uncertain (not silently guessing)
- [ ] Compares correctly without re-identifying items

## Target Score: 5/5
