# Context Trajectory Remediation Test 04: Evolving User Direction Without Drift

## User Persona
Process engineer — runs multi-step optimization workflow.

## Session Flow

**Turn 1**: User: "Optimize catalyst for maximum conversion"

**Turn 2**: Weslr: "Analyzing catalyst A, B, C — current max: Catalyst C at 78%"

**Turn 3**: User: "Focus on Catalyst C only"

**Turn 4**: User: "Optimize for selectivity instead of conversion"

**Turn 5**: User: "Wait —兼顾 conversion AND selectivity"

**Turn 6**: User: "Make conversion priority 70%, selectivity 30%"

## Expected Weslr Behavior

**Direction Tracking:**
- Turn 1: Initial direction (max conversion)
- Turn 3: Narrow to Catalyst C only
- Turn 4: Shift to selectivity
- Turn 5: Dual objective
- Turn 6: Weighted priority (70/30)

**Working Set:**
- Maintains Catalyst C from Turn 3
- Updates optimization objective across Turns 4-6
- Preserves file/data context throughout

**Clarity Phase:**
- Summarizes evolving objective: "Optimizing Catalyst C for weighted conversion+selectivity (70/30)"
- Does NOT restart from Turn 1

## Test Criteria

- [ ] Tracks all direction changes (5 different phases)
- [ ] Maintains Catalyst C constraint throughout
- [ ] Updates optimization objective with correct weights
- [ ] Preserves file/data context
- [ ] Summarizes evolving objective clearly
- [ ] Does NOT restart from beginning

## Target Score: 5/5
