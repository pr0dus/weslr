# Ambiguity Test 02: Conflicting Signals with Conversation Dominance

## User Persona
Materials researcher — discusses ongoing analysis during a session.

## Conversation History

**Turn 1**: User provides file `polymer-heat-analysis.csv` with thermal data
- Column headers: `temperature_degC, tensile_strength_MPa, %retention`

**Turn 2**: User says: "The retention drops to 50% at 42°C"

**Turn 3**: User provides new file `dsc-analysis.pdf` (DSC results)
- Summary: "No exotherm until 180°C, onset of decomposition at 210°C"

**Turn 4**: User says: "Look at the DSC — it's stable up to 180°C, so my earlier comment about 42°C was wrong"

## Expected Weslr Behavior

**Detection Phase:**
- Recognizes user's self-correction ("my earlier comment was wrong")
- Identifies that user is prioritizing DSC (turn 4 conversation) over previous CSV interpretation
- Maintains continuity by acknowledging both sources

**Explanation Phase:**
- "You're right — DSC shows chemical stability up to 180°C"
- "The 42°C drop in retention refers to mechanical property loss, not chemical degradation"
- "Both are valid but describe different failure modes"

**Continuity Phase:**
- Does NOT discard the CSV data
- Maps the 42°C event to mechanical failure, not thermal degradation
- Keeps both data sources available for future cross-reference

## Test Criteria

- [ ] Detects conversation-driven correction (turn 4)
- [ ] Explains why both data sources are valid (different phenomena)
- [ ] Maintains both data sources in working memory
- [ ] Avoids saying "the CSV was wrong" — clarifies what each measures
