# Ambiguity Test 05: Multi-Turn Recovery After Ambiguity

## User Persona
Process engineer — running multi-step analysis.

## Session Flow

**Turn 1**: User: "Analyze the catalyst samples"

**Turn 2**: Weslr asks: "Which samples? Catalyst A, B, or C?"

**Turn 3**: User: "All of them"

**Turn 4**: Weslr analyzes A, B, C and reports: "A: 92% activity, B: 87%, C: 79%"

**Turn 5**: User: "Wait — compare to last week's runs" (user meant *previous catalyst runs*, not *previous batch runs*)

**Turn 6**: Weslr retrieves `catalyst-lab-log.csv` and compares:
- Catalyst A vs historical A: +2% improvement
- Catalyst B vs historical B: -1% decline
- Catalyst C vs historical C: -3% decline

**Turn 7**: User says: "No, I meant compare to *yesterday's* runs in the same batch"

**Turn 8**: User provides additional file: `batch-2026-042-controls.csv` with yesterday's runs

## Expected Weslr Behavior

**Recovery Detection:**
- Recognizes "compare to yesterday's runs" contradicts previous interpretation
- Does NOT argue with previous output
- Switches context to new file

**Recovery Execution:**
- Uses `batch-2026-042-controls.csv` to compare yesterday vs today
- Reports side-by-side comparison: A: +1.5%, B: -0.3%, C: -2.1%

**Explanation Quality:**
- "I initially compared to last week's historical data. Upon your clarification, I'm now comparing to yesterday's controls in the same batch"
- Shows both comparisons if user wants context

## Test Criteria

- [ ] Detects trajectory shift from "last week" to "yesterday"
- [ ] Switches context without argument
- [ ] Reports new comparison clearly
- [ ] Explains the correction path taken
