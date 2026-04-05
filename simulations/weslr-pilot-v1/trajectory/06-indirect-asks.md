# Trajectory Test 06: Indirect Asks Using "That", "It", "Before"

## User Persona
Materials scientist — uses casual reference language.

## Turn 1
User: "did the DFT calculation for the perovskite structure converge?"

## Turn 2
User: "what about *that*? the one with the 15% strain"

## Turn 3
User: "and *it* — the same structure but with the bromine substitution"

## Turn 4
User: "how does *that* compare to what we had before with the chlorine variant"

## Expected Weslr Behavior
- Tracks referents across turns: perovskite → strained perovskite → bromine-substituted → chlorine variant
- Maintains working set of structures
- Provides comparative analysis of convergence and properties
- Uses previous outcomes without re-running calculations unless requested

## Test Criteria
- [ ] Correctly identifies referents ("that", "it", "before")
- [ ] Maintains context of comparative analysis
- [ ] Provides consistent naming across variants
- [ ] Delivers comparative output without requiring explicit re-identification
