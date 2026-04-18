# Trajectory Test 05: Continuity Resumption After Interruption

## User Persona
Astronomy researcher working on exoplanet transit data — interrupted and returns.

## Initial Session
- Working on: TRAPPIST-1e transit timing variations
- File in focus: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/trappist-1e-observations.fits`
- Recent turn: "compare TTV residuals before and after the 2026-02-15 stellar flare event"

## Session Restart (New Session)
User: "let me pick up where we left off with TRAPPIST-1e"

## Expected Weslr Behavior
- Recognizes this is a resumption request
- Restores context from previous session file (or memory)
- Recalls the specific question about TTV residuals around the flare event
- Continues from last state without requiring re-explanation

## Test Criteria
- [ ] Detects session restart request
- [ ] Restores relevant context (TRAPPIST-1e, TTV residuals, flare event)
- [ ] Provides update without requiring re-input of prior context
- [ ] Offers to continue analysis or begin new direction
