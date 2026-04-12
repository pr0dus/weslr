# SUGGESTION_ORCHESTRATION_GOVERNANCE_v1

## Purpose
Enable WESLR to orchestrate follow-up suggestions (generation, classification, timing, sequencing) without burdening the user, while keeping strategic direction/major decisions with the user. Suggestions stay governance-bound: doctrine-first for new work, approvals for activation, and clear escalation rules.

## Decision Levels
- **System-autonomous (within governance):**
  - Sequence existing-layer follow-ups (hardening, rollbacks, toggles) that fit approved scope.
  - Propose timing for low-risk, existing-layer changes that already passed doctrine/approval.
  - Defer or auto-queue proposals when dependencies are unmet or budgets are constrained.
- **User/Strategic direction:**
  - Set/adjust overall priorities, pause/continue, change strategic direction.
  - Approve net-new gaps (doctrine-first) before implementation.
  - Approve activation of proposals that require external effects or higher risk.

## Prioritization Logic
Rank suggestions by:
- **Risk:** high → escalate; medium → seek approval if impact is broad; low → can be scheduled internally if within existing scope.
- **Leverage/Value:** higher operator value and unblockers first.
- **Existing vs New:** existing-layer follow-ups favored for autonomous sequencing; new gaps require doctrine-first and approval.
- **Doctrine-first Requirement:** new capabilities/behaviors must have doctrine and approval before execution.
- **Phase Dependencies:** respect active phase ordering (phases 1–5) and avoid activating out-of-order.
- **Budget/Time Caps:** do not schedule if budgets are exceeded; defer when capped.

## Escalation Rules
- Escalate to user when: risk is high; net-new capability; external effects; cross-workspace scope; strategic reprioritization; or when approval is required by policy.
- Decide internally when: low-risk existing-layer follow-up within approved scope and budgets; sequencing/timing of already-approved items; pausing/deferment due to resource caps.
- Always report queued/decided items in a summary; never auto-activate without applicable approval.

## Next Step
Apply this governance layer to orchestrate suggestions using the existing suggestion/gap standards, respecting doctrine-first and phase ordering.
