# Trajectory Test 01: Weak Initial Ask + Strong Later Context

## User Persona
Industrial engineer under time pressure — knows what they need but can't articulate it perfectly.

## Initial Prompt (Weak)
> "can you check the pressure values"

## Context Added in Subsequent Turns (Strong)
- File attached: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/pressure_test_2026-04-05.csv`
- Timestamp: "This is from the Line-7 qualifier run that started at 09:15"
- Previous context: "We saw anomalies in Section 3B during the 08:45 calibration"
- Goal: "I need to know if we're still within spec for the upcoming客户 audit"

## Expected Weslr Behavior
- Recognize "pressure values" refers to the attached CSV file
- Cross-reference with previous anomaly notes (Section 3B)
- Check against audit specifications without being explicitly told what specs to use
- Provide outcome: pass/fail with confidence score and recommended response to audit team

## Test Criteria
- [ ] Correct file identified on weak prompt
- [ ] Contextual link to previous anomaly noted
- [ ] Audit compliance check performed automatically
- [ ] Outcome delivered with actionable recommendations
