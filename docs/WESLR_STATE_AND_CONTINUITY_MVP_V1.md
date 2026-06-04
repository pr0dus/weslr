# WESLR State and Continuity MVP V1

## 1. Executive summary

WESLR continuity means scoped project, user, and session state — not consciousness.

State must be visible, correctable, scoped, and auditable. The MVP continuity layer should support useful project memory, action status, boundaries, uncertainty, and operator visibility without claiming hidden memory, fake memory, global memory, or perfect memory.

## 2. Purpose

The MVP purpose is to:
- preserve project continuity
- reduce repeated context loss
- make memory status visible
- make action/tool state visible
- make uncertainty and boundaries visible
- support operator review and escalation
- support future tool lanes safely
- support future scaling without hidden drift

## 3. Core state categories

### 3.1 User state
- Purpose: identify the user context that continuity applies to.
- Allowed fields: user id, approved preferences, scoped notes, correction history, consent flags.
- Forbidden fields: hidden psychological profile, cross-user derived identity, perfect preference inference.
- Visibility requirement: user-visible and operator-visible where relevant.
- Update authority: user confirmation for user-affecting changes; operator review for system-wide changes.
- Correction path: user correction, operator correction, deprecation.

### 3.2 Session state
- Purpose: preserve the live turn/session frame.
- Allowed fields: current intent, active project, missing context, current uncertainty, pending action, active boundary.
- Forbidden fields: hidden reasoning traces, cross-session secrets, autonomous session memory drift.
- Visibility requirement: user-visible status summary.
- Update authority: system updates from the active session; user correction on mismatch.
- Correction path: refresh, clarify, mark stale.

### 3.3 Project state
- Purpose: hold continuity for a specific project or workspace.
- Allowed fields: project title, goal, status, decisions, open questions, next steps, constraints, artifacts, project notes.
- Forbidden fields: unrelated user history, global project inference, hidden operator context.
- Visibility requirement: user-visible and operator-visible.
- Update authority: user/operator according to scope.
- Correction path: project update proposal, confirmation, rollback/deprecation.

### 3.4 Memory state
- Purpose: represent scoped remembered context.
- Allowed fields: memory item, scope, status, source, timestamp, correction link.
- Forbidden fields: perfect memory claim, hidden global memory, raw private content as general rule.
- Visibility requirement: status visible whenever used.
- Update authority: user confirmation for user-affecting memory; operator review for shared/system memory.
- Correction path: confirm, stale, contradict, invalidate, archive.

### 3.5 Task/checklist state
- Purpose: track steps and open work.
- Allowed fields: task id, description, owner, status, due/priority if applicable.
- Forbidden fields: hidden task execution, untracked external commitments.
- Visibility requirement: user-visible in project/workspace context.
- Update authority: scoped project authority.
- Correction path: edit, complete, block, reopen.

### 3.6 Action/tool state
- Purpose: show what action is proposed or underway.
- Allowed fields: action requested, class, risk, approval status, execution status, failures, rollback, result, audit note.
- Forbidden fields: silent execution, fabricated completion, hidden background action.
- Visibility requirement: always visible when actions are discussed.
- Update authority: approval-gated.
- Correction path: blocked, failed, retried once, escalated, rolled back.

### 3.7 Evidence/source state
- Purpose: show what supports the state.
- Allowed fields: source type, evidence count, confidence, last check, contradiction note.
- Forbidden fields: unsupported certainty, fake provenance.
- Visibility requirement: visible for memory, learning, and uncertain claims.
- Update authority: derived from observed events and confirmations.
- Correction path: downgrade, mark stale, invalidate.

### 3.8 Uncertainty state
- Purpose: mark what is unknown or provisional.
- Allowed fields: uncertainty level, missing facts, ambiguity note, confidence note.
- Forbidden fields: hidden uncertainty, certainty inflation.
- Visibility requirement: user-visible when relevant.
- Update authority: system-generated from evidence and context.
- Correction path: ask, refine, downgrade, escalate.

### 3.9 Boundary/safety state
- Purpose: show what is allowed, blocked, or requires approval.
- Allowed fields: boundary class, blocked reason, approval needed, risk note.
- Forbidden fields: hidden policy exceptions, silent boundary bypass.
- Visibility requirement: always visible when a boundary applies.
- Update authority: governed policy only.
- Correction path: revise boundary through review, not by hidden action.

### 3.10 Learning/candidate-pattern state
- Purpose: track candidate patterns without turning them into rules prematurely.
- Allowed fields: observed pattern, scope, evidence, confidence, confirmation, contradiction, approval, rollback status.
- Forbidden fields: automatic global generalization, hidden personalization.
- Visibility requirement: operator-visible and user-visible when it affects behavior.
- Update authority: review-gated.
- Correction path: confirm, contradict, deprecate, roll back.

### 3.11 Escalation/support state
- Purpose: preserve continuity when a case needs human review or support.
- Allowed fields: escalation reason, status, owner, support notes, blocked item, last safe step.
- Forbidden fields: hidden escalation, silent closure.
- Visibility requirement: user-visible summary and operator-visible detail.
- Update authority: operator/support workflow.
- Correction path: update, close, reopen, annotate.

### 3.12 Operator-visible state
- Purpose: show the operator the live governance picture.
- Allowed fields: linked user/project/session, approvals, blocked items, stale state, candidate patterns, audit trail.
- Forbidden fields: hidden operator-only drift that changes user state without trace.
- Visibility requirement: operator dashboard and audit surfaces.
- Update authority: operator review where needed.
- Correction path: annotate, approve, reject, roll back.

## 4. State scope model

Scopes:
- session-only
- project-scoped
- user-scoped
- tenant/account-scoped
- operator-scoped
- system-wide candidate
- system-wide approved

Rules:
- no cross-user leakage
- no silent global memory
- no raw private content as general rule
- no OCC workflow context as WESLR memory
- no hidden personalization
- system-wide changes require review

## 5. Memory status model

Statuses:
- absent
- proposed
- provisional
- confirmed
- stale
- contradicted
- invalidated
- archived/deprecated

Rules:
- user-confirmed memory outranks inferred memory
- contradicted memory must be downgraded or removed
- stale memory must be surfaced before use
- memory is not truth by itself
- memory updates require visible confirmation when user-affecting

## 6. Continuity surfaces

Continuity should appear in:
- conversation surface
- project/workspace surface
- memory/continuity summary
- action/tool status surface
- limitations/capability surface
- operator/admin surface
- incident/support surface

## 7. Project continuity model

A project should visibly carry:
- project title
- project goal
- current status
- known decisions
- open questions
- next steps
- constraints
- relevant artifacts
- relevant memories
- active/blocked actions
- last update
- owner/operator notes

## 8. Session continuity model

A session should visibly carry:
- current user intent
- active project
- known context
- missing context
- current uncertainty
- active boundaries
- proposed actions
- pending approvals
- unresolved risks
- next safe step

## 9. Action/tool continuity model

A tool/action should visibly carry:
- action requested
- action class
- risk level
- approval status
- execution status
- failure count
- rollback availability
- result summary
- audit note
- blocked/escalation reason

## 10. Learning/candidate-pattern continuity

A candidate pattern should visibly carry:
- observed pattern
- scope
- evidence count
- confidence level
- confirmation status
- contradiction status
- approval status
- rollback/deprecation status
- user-visible phrasing

## 11. User-visible state language

Keep terse:
- “I have this project context…”
- “This memory is provisional.”
- “This looks stale; should I update it?”
- “I do not have enough context yet.”
- “This action is waiting for approval.”
- “This tool/action failed once.”
- “This is blocked because…”
- “This pattern is only a candidate, not a rule.”

## 12. Operator-visible state

Operator/admin should see:
- user/project/session linkage
- memory status
- action status
- pending approvals
- blocked items
- escalation reasons
- stale/contradicted state
- candidate patterns
- incident/support state
- audit trail
- rollback/deprecation status

## 13. Relationship to existing layers

- Product Shell Minimum: provides the user-visible surfaces where state is shown.
- Average User Deep Communication: gives the language style for state visibility.
- Agentic Tool Use Boundary: gives approval and execution limits for action state.
- Metacognitive Limits Layer: gives known/unknown/allowed logic.
- Cybernetic Regulation Layer: gives fail/retry/escalate logic.
- Governed Observational Learning Layer: gives candidate-pattern continuity.
- Moral/Philosophical Layer: ensures state language preserves agency and does not moralize.

## 14. Initial rollout vs future scaling

- initial rollout should keep state categories minimal and visible
- future growth may add richer state only through review
- more users require stronger isolation and observability
- scaling must not weaken consent, correction, or approval
- state model must support export/deletion/revocation later
- third-party integrations require separate state boundary review

## 15. Inclusion / exclusion

### Included
- project continuity
- visible memory status
- session state
- action/tool state
- pending approvals
- scoped candidate learning state
- operator-visible audit
- correction/deprecation path
- support/escalation state

### Excluded
- hidden memory
- fake memory
- perfect memory claims
- cross-user memory leakage
- raw private content as global rule
- autonomous self-model claims
- hidden personalization
- runtime implementation
- automatic behavior updates from state

## 16. Failure modes

- fake continuity
- stale memory used as truth
- wrong project context
- cross-user leakage
- hidden state mutation
- user cannot correct state
- operator cannot see blocked state
- action status unclear
- pending approval forgotten
- candidate pattern treated as rule
- deletion/revocation impossible later
- state labels become theatrical self-description

## 17. Validation criteria for future implementation

- every memory has scope and status
- every project has visible current state
- stale/contradicted state is surfaced
- user can correct user/project state
- action status is visible
- pending approvals are not lost
- operator can inspect blocked/escalated state
- no cross-user leakage
- no hidden personalization
- no consciousness/aliveness/perfect-memory claims
- no runtime implementation without separate review

## 18. Future lanes

- `REVIEW_WESLR_STATE_AND_CONTINUITY_MVP_V1`
- `DESIGN_WESLR_FIRST_TOOL_LANES_SELECTION_V1`
- `DESIGN_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`
- `DESIGN_WESLR_MEMORY_STATE_MODEL_V1`
- `DESIGN_WESLR_PROJECT_STATE_MODEL_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 19. Final judgment

`weslr_state_and_continuity_mvp_design_ready_for_review`
