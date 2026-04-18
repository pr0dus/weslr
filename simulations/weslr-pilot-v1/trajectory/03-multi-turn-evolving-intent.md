# Trajectory Test 03: Multi-Turn Evolving Intent

## User Persona
Materials researcher comparing candidate compounds — investigation evolves over time.

## Turn 1 (Initial)
User: "show me high-temperature superconductors under 50K"

## Turn 2 (Refinement)
User: "actually, I need ones that are also stable in air — not just cryogenic stability"

## Turn 3 (Direction Change)
User: "wait, make that room-temperature operation — and focus on thin-film variants"

## Turn 4 (Continuation)
User: "can you compare the thin-film performance with the bulk properties for the top three candidates"

## Expected Weslr Behavior
- Track evolution of requirements: temperature → air stability → thin-film → comparison
- Maintain previous candidates from earlier turns to avoid re-scanning
- Compare thin-film vs bulk performance using existing knowledge base
- Present side-by-side comparison with synthesis difficulty and commercial availability

## Test Criteria
- [ ] Maintains continuity across all four turns
- [ ] Requirements tracked and applied incrementally
- [ ] Previous candidates reused (not re-fetched from scratch)
- [ ] Final output includes direct comparison of thin-film vs bulk
