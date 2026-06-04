# WESLR Product Shell Minimum V1

## 1. Executive summary

WESLR is **not yet a broad public product**. This shell is for invite-only / manually approved 50-user working version preparation. The goal is coherence, reliability, and operator visibility — not feature breadth.

The minimum shell should make WESLR understandable as one product, while preserving the architecture boundary that WESLR is still a governed system with partial runtime surfaces and many internal helper layers.

## 2. Product-shell purpose

The shell must:
- make WESLR understandable
- show what WESLR can do now
- show what WESLR cannot do yet
- provide a coherent conversation/workspace/project experience
- expose state and boundaries clearly enough for operator/tester trust

## 3. Minimum user model

The shell should assume:
- invite-only or manual approval
- bounded accounts
- no public self-registration by default
- no public paid-product claim
- tester/user role
- operator/admin role
- support/escalation path

## 4. Minimum navigation / surfaces

Required product surfaces:
- landing / entry surface
- login / access gate
- workspace/project list
- conversation surface
- project/session context surface
- memory/continuity summary surface
- tool/action status surface
- limitations / “what WESLR can do now” surface
- operator/admin visibility surface
- incident/support surface

These surfaces do not require a large feature set. They do require a coherent information architecture.

## 5. Minimum conversation shell

A conversation should visibly carry:
- conversation identity
- session boundaries
- project association
- state summary
- visible memory/carry-forward status
- tool/action status
- uncertainty/unsupported-state display
- correction/update path
- graceful failure path

The conversation shell should feel like a stateful workspace, not only a prompt box.

## 6. Minimum project/workspace shell

A project/workspace should visibly carry:
- project name
- project description
- current objective
- active context
- relevant files/artifacts if applicable
- memory/continuity summary
- open tasks
- blocked/pending items
- operator notes

This is the product’s “working room” model.

## 7. Minimal self-state / regulation baseline

The shell needs a minimal non-mystical state panel/model that supports the later proto-cognitive direction without claiming aliveness.

Visible state categories:
- session state
- project state
- memory state
- tool/action state
- boundary/safety state
- latency/background-task state
- recovery/escalation state
- operator-visible state

Clarifications:
- this is not consciousness
- this is not autonomy
- this is not a claim WESLR is alive
- this is a practical reliability layer

This panel is mainly about keeping state legible, not about simulating mind.

## 8. Minimum memory/continuity exposure

The shell should define:
- what memory is visible to user/operator
- what is only internal
- how corrections are shown
- how carry-forward context is approved
- how stale/uncertain memory is marked
- no memory-as-authority
- no fake memory claims

Visible memory should be labeled as scoped, provisional, or confirmed as needed.

## 9. Minimum tool/action exposure

Tool/action status should be visible and boringly clear:
- proposal-before-action
- validation-before-execution
- status values:
  - proposed
  - approved
  - running
  - blocked
  - failed
  - completed
- visible reason for blocked actions
- operator approval where needed

This helps WESLR feel checked, not theatrical.

## 10. Operator/admin shell

Operator/admin visibility should include:
- user list / invite status
- per-user/project status
- memory/change visibility
- blocked actions
- incidents
- deletion/export/revocation status
- support notes
- manual override boundaries

The operator shell is part of the product, not a hidden sidecar.

## 11. 50-user constraints

The shell must assume:
- low feature count
- high reliability
- manual onboarding
- operator-supervised scaling
- clear failure modes
- strict privacy/legal boundaries
- no public launch posture

This is a working version, not a public expansion.

## 12. First product-shell deliverables

Before implementation, the shell work should produce:
- shell information architecture
- page/surface map
- minimum user flows
- state object sketch
- permissions/access sketch
- operator dashboard sketch
- memory visibility sketch
- tool status sketch
- failure/escalation sketch

## 13. What must not be done yet

- no public self-registration
- no broad marketplace
- no paid product claim
- no many-tool expansion
- no advanced proto-cognitive UI claims
- no “alive” or consciousness framing
- no hidden autonomy
- no memory as authority
- no OCC workflow context in WESLR master

## 14. Relationship to next phases

This shell prepares the next phases by creating a visible place for:
- Phase 2 state and continuity MVP
- Phase 3 tool-governed execution lanes
- Phase 4 observability/operator control
- Phase 6 latency/responsiveness
- Phase 7 bounded adaptive identity

In other words, the shell is the staging area where the later state and governance work can become user-visible.

## 15. Recommended next lanes

- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `DESIGN_WESLR_STATE_AND_CONTINUITY_MVP_V1`
- `DESIGN_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1` remains pending and should be scheduled before deeper release-gate hardening

## Final judgment

`weslr_product_shell_minimum_design_ready_for_review`
