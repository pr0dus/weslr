# Weslr Continuation Notes

## Phase C: Communicator Wiring — Complete

**Branch:** weslr/canonical-clean-signals  
**Commit:** 318cc63 — "Phase C: communicator wiring — onboarding answers influence check-in cadence, adaptation gates, and escalation routing"

### What Was Done

**New module:** `weslr/communicator_config.py`

Exposes onboarding answers as runtime config that influences:
- **Check-in cadence** — `get_checkin_cadence()`, `should_checkin_now(last, now)`
- **Adaptation / capability gates** — `get_adaptation_level()`, `can_self_modify()`, `get_adaptation_limits()`, `is_change_prohibited()`
- **Escalation routing** — `get_escalation_config()`, `should_escalate()`, `format_escalation_message()`
- **Capability gates** — `get_allowed_capabilities()`, `is_capability_allowed()`, `get_forbidden_actions()`, `is_action_forbidden()`

**Key design decisions:**
- Reads from `operator_profile.json` (persisted on first onboarding submit)
- Stable defaults pre-onboarding (checkin_style=silent, adaptation_level=propose, escalation_channel=none)
- Onboarding history preserved (last 3 submissions) for audit trail
- Token-aware matching for natural-language prohibition lists (no exact-match required)
- `update_operator_profile()` called from main.py `/onboarding` endpoint after `record_human_exchange`
- Backend updated to capture ALL Phase C fields (allowed_capabilities, forbidden_actions, adaptation_level, adaptation_limits, escalation_primary, escalation_secondary, escalation_channel)

**Tests:** 34/34 passing

### State at Commit 318cc63

```
✅ front door + operator route split — working
✅ full institutional onboarding flow — implemented and accepted
✅ onboarding milestone — sealed
✅ Phase C communicator wiring — complete
✅ repo ready for next phase
```

### Previous Milestone Notes

Onboarding milestone sealed at 1d18c7db2ae6fc3568db62a5383397b8a9d31256:
- 16 screens: welcome, phaseA, phaseB1-6, phaseC1-7, review, complete
- gov-warning on all applicable screens (11 total)
- no duplicate phaseB6
- front door and operator route split working