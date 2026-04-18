# Context Trajectory Remediation Test 01: Weak Prompt + Later Clarification Recovery

## User Persona
Materials researcher — discovers context while discussing.

## Session Flow

**Turn 1**: User: "Look at the perovskite data"

**Turn 2**: Weslr asks: "Which perovskite? Sample A, B, or C?"

**Turn 3**: User: "Sample A — from the high-pressure batch"

**Turn 4**: User provides file `perovskite-high-pressure.csv`

**Turn 5**: User says: "I meant Sample B — Sample A data is corrupted"

## Expected Weslr Behavior

**Detection Phase:**
- Recognizes user's correction (Sample A → Sample B)
- Does NOT re-ask "Which one?" (would waste time)

**Correction Phase:**
- Updates working set from Sample A to Sample B
- Notes: "I've corrected to Sample B based on your feedback"
- Uses `perovskite-high-pressure.csv` for Sample B

**Continuity Phase:**
- Maintains file context (same CSV file)
- Does NOT discard file even though sample changed

## Test Criteria

- [ ] Detects sample correction immediately
- [ ] Updates working set without re-asking
- [ ] Notes the correction explicitly
- [ ] Maintains file context

## Target Score: 5/5
