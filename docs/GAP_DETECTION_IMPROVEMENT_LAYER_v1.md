# GAP_DETECTION_IMPROVEMENT_LAYER_v1

## Purpose
Provide an internal, governance-bound layer that detects workflow gaps and proposes improvements for both WESLR self-improvement and user workflows—without automatic activation or redesign. It surfaces actionable proposals that stay within doctrine-first and permissioned activation.

## Modes
- **A) Self-Improvement Mode:** Detects internal failures, friction, low-confidence patterns, approval/override churn, and underused capabilities within WESLR. Outputs proposals to harden or activate existing layers; net-new ideas remain proposals only.
- **B) User Workflow Optimization Mode:** Detects user-facing bottlenecks, repeated corrections, stalled tasks, or missing capabilities that impede operator outcomes. Outputs proposals to streamline user workflows, respecting role/permission partitions.

## Gap Signals (inspect at minimum)
- Recurring failures and error clusters.
- Repeated friction points (retries, manual overrides, operator interventions).
- Low-confidence patterns and evidence gaps that stall decisions.
- User correction frequency and conversational repair events.
- Workflow bottlenecks (latency, blocked approvals, queue backlogs).
- Underused existing capabilities (low utilization where applicable).
- Potential net-new capability gaps inferred from unmet intents/outcomes.

## Output
- Outputs are **proposals/suggestions only** (titles, why-it-matters, existing vs new, risk, doctrine-first flag, activation vs net-new, approval needed), following POST_STEP_SUGGESTION_STANDARD_v1.
- **No auto-activation. No auto-redesign.**

## Governance
- All outputs route through the Governed Activation & Permission Framework: doctrine-first, role/permission checks, explicit approvals before any activation or change.
- Suggestions remain advisory until approved; activation/hardening/net-new work requires explicit consent and lane-appropriate worktrees.

## Next Step
Stage runtime detection plan and tests for this layer (doctrine-first), then seek approval before implementation.
