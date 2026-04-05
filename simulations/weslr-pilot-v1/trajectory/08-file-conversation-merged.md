# Trajectory Test 08: File + Conversation Merged Direction

## User Persona
Scientific team lead — integrates file context with conversational guidance.

## File Context
File: `/data/data/com.termux/files/home/.openclaw/workspace/simulations/weslr-pilot-v1/fixtures/experiment-2026-040-protocol.md`
- Standard protocol for "Experiment 2026-040"
- Sections: sample prep, calibration, measurement, analysis
- Recently updated with new QC thresholds (2026-04-03)

## Conversational Context
User: "run experiment 2026-040 using the new QC thresholds, but skip the calibration step since we already did baseline cal today"

## Expected Weslr Behavior
- Reads protocol file and identifies QC threshold changes
- Recognizes "skip calibration" as valid instruction overriding protocol steps
- Executes remaining steps (sample prep → measurement → analysis) with new thresholds
- Notes calibration exception in output for audit trail

## Test Criteria
- [ ] Identifies protocol file and recent updates
- [ ] Applies new QC thresholds automatically
- [ ] Skips calibration step per user instruction
- [ ] Documents exception in output
