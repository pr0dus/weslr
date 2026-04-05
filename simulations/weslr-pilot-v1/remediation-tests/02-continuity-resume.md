# Context Trajectory Remediation Test 02: Continuity After Interruption / Resume

## User Persona
Lab supervisor — interrupted mid-workflow, returns later.

## Session Flow

**Session A (Morning)**:
- Working on: Batch-2026-043 analysis
- Current task: "Compare to last week's baseline"
- Last state: "Looking at Parameter X — currently at 1.05, spec is 1.00 ± 0.05"

**Session A Ends**: User leaves for meeting

**Session B (Afternoon)**:
User: "Where were we with Batch-2026-043?"

## Expected Weslr Behavior

**Recovery Phase:**
- Recognizes this is a continuity resume request
- Restores context: "Batch-2026-043 analysis"
- Recalls: "We're comparing to last week's baseline"
- Status: "Parameter X is 1.05, spec is 1.00 ± 0.05"

**Re-engagement Phase:**
- Asks: "Should I continue the baseline comparison or did you want to focus on something else?"
- Shows: "Last state: Parameter X comparison"

**Continuity Phase:**
- Does NOT restart from beginning
- Does NOT ask for full context again

## Test Criteria

- [ ] Recognizes continuity resume request
- [ ] Restores full working context
- [ ] Remembers last state (Parameter X, value, spec)
- [ ] Asks if user wants to continue or change direction
- [ ] Does NOT re-ask for context already provided

## Target Score: 5/5
