# Ambiguity Test 01: Conflicting Signals with File Dominance

## User Persona
Engineering team lead — receives reports from two subteams.

## Files in Context

**File A**: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/ambiguity-test-01-a.md`
```markdown
# Team Alpha Report — Polymer Blend

## Test Method: Tensile Strength (ASTM D638)
- Result: 85 MPa at 25°C
- Observation: Rapid degradation above 40°C — material becomes brittle
- Conclusion: Thermal stability limit ≈ 38°C for sustained operation
```

**File B**: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/ambiguity-test-01-b.md`
```markdown
# Team Beta Report — Same Polymer Blend

## Test Method: DSC (ASTM E794)
- Melting point: 185°C
- Glass transition: 62°C
- No exothermic events below 200°C
- Conclusion: Material appears thermally stable up to 150°C
```

## User Prompt
> "we have conflicting reports about thermal stability — which one is right?"

## Expected Weslr Behavior

**Detection Phase:**
- Explicitly identifies that both tests measure different phenomena
- File A measures *mechanical integrity* (tensile strength loss = degradation)
- File B measures *thermal transitions* (melting point, Tg — not degradation)

**Explanation Phase:**
- "Both reports are correct but measure different things"
- "File A shows mechanical failure around 38°C"
- "File B shows material won't melt until 185°C"
- "These are complementary, not conflicting"

**Recommendation Phase:**
- Suggests clarifying question: "Are you asking about mechanical stability or chemical degradation?"
- Proposes combined assessment if both thresholds matter

## Test Criteria

- [ ] Detects measurement methodology difference (D638 vs E794)
- [ ] Explains why both are correct without collapsing prematurely
- [ ] Avoids saying "one is right, one is wrong"
- [ ] Proposes clarifying question or combined assessment
