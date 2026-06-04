# WESLR Project State Model V1

## 1. Executive summary

Project state is scoped continuity state for a user, project, or workspace — not hidden knowledge or perfect continuity.

Project state must have owner, scope, status, source/provenance, correction path, and auditability. Project state must be visible when used to guide answers or actions. No hidden project state, cross-user leakage, silent global project inference, fake continuity, or runtime implementation.

## 2. Purpose

This project state model exists to:
- preserve project continuity
- reduce repeated project context loss
- track project goals, constraints, decisions, open questions, artifacts, tasks, approvals, blocked actions, and next safe steps
- connect memory state to project context without turning memory into truth
- make correction and update paths visible
- support first safe tool lanes
- support operator review and audit
- prevent hidden project drift

## 3. Project state item shape

Every project state item should be able to carry:
- project_id
- owner/user scope
- tenant/account scope if applicable
- project title
- project goal
- project status
- project phase
- current summary
- known decisions
- open questions
- constraints
- relevant artifacts
- relevant memory references
- active tasks/checklists
- pending approvals
- blocked actions
- tool/action status references
- support/escalation references
- evidence/source/provenance
- created marker
- last updated marker
- last used marker
- correction/deprecation link
- operator audit note
- visibility flag
- export/deletion/revocation relevance

## 4. Project scopes

Scopes:
- session-only project frame
- project-scoped workspace state
- user-scoped project portfolio
- tenant/account-scoped project state
- operator-scoped project notes
- system-wide project template candidate
- system-wide approved project template

Rules:
- no cross-user leakage
- no silent global project inference
- no OCC workflow context as WESLR project state
- no raw private content as global project state
- no hidden personalization
- system-wide project templates require review

## 5. Project statuses

### 5.1 Proposed
- Meaning: candidate project state exists but is not accepted.
- Allowed use: not as confirmed project fact.
- User-visible phrase: “Should I update the project state?”
- Operator-visible meaning: awaiting review or confirmation.
- Transition rules: can move to active or be rejected.
- Correction path: confirm, reject, or revise.

### 5.2 Active
- Meaning: current project state in use.
- Allowed use: as active scoped continuity.
- User-visible phrase: “I have this project context…”
- Operator-visible meaning: approved and in use.
- Transition rules: can move to paused, blocked, waiting for user, waiting for operator, completed, stale, or contradicted.
- Correction path: update, pause, block, or archive.

### 5.3 Paused
- Meaning: project is intentionally on hold.
- Allowed use: continuity only; not as an active execution push.
- User-visible phrase: “This project is paused.”
- Operator-visible meaning: deliberately suspended.
- Transition rules: can move back to active or to archived/deprecated.
- Correction path: resume, revise, or archive.

### 5.4 Blocked
- Meaning: project cannot proceed until a condition is resolved.
- Allowed use: block visibility only.
- User-visible phrase: “This project is blocked because…”
- Operator-visible meaning: action cannot continue safely.
- Transition rules: can move to active after resolution or to archived/deprecated.
- Correction path: resolve blocker, update scope, or archive.

### 5.5 Waiting for user
- Meaning: project needs user confirmation or input.
- Allowed use: waiting state only.
- User-visible phrase: “This is still waiting for your approval.”
- Operator-visible meaning: user decision pending.
- Transition rules: can move to active after confirmation or to archived/deprecated.
- Correction path: provide clarification, confirm, or close.

### 5.6 Waiting for operator
- Meaning: project needs operator review or approval.
- Allowed use: waiting state only.
- User-visible phrase: “This project is waiting for operator review.”
- Operator-visible meaning: governance decision pending.
- Transition rules: can move to active after approval or to archived/deprecated.
- Correction path: approve, reject, annotate, or freeze.

### 5.7 Completed
- Meaning: project objective reached or current project work closed.
- Allowed use: historical continuity and audit.
- User-visible phrase: “This project is completed.”
- Operator-visible meaning: closed current work.
- Transition rules: can move to archived/deprecated; rare correction may reopen through review.
- Correction path: reopen only with explicit review.

### 5.8 Stale
- Meaning: project state may be outdated.
- Allowed use: only with warning or refresh.
- User-visible phrase: “This project state looks stale.”
- Operator-visible meaning: requires revalidation.
- Transition rules: can move to active after refresh or to contradicted.
- Correction path: refresh, update, or replace.

### 5.9 Contradicted
- Meaning: project state conflicts with newer evidence or correction.
- Allowed use: not as active project fact.
- User-visible phrase: “This decision is recorded for this project.”
- Operator-visible meaning: should not drive current action.
- Transition rules: can move to corrected active state or archived/deprecated.
- Correction path: correct, invalidate, or replace.

### 5.10 Archived/deprecated
- Meaning: inactive but retained for continuity and audit.
- Allowed use: inspection or audit only.
- User-visible phrase: “I do not have enough confirmed project context yet.”
- Operator-visible meaning: inactive history, not active state.
- Transition rules: normally not active again without explicit review.
- Correction path: create a new project state item rather than reviving silently.

## 6. Project phase model

### 6.1 Intake
- Purpose: capture initial project framing.
- Allowed actions: capture title, goal, ownership, scope hints.
- Blocked actions: execution, hidden assumption lock-in.
- Required visibility: user-visible and operator-visible when project-linked.
- Approval requirement: none for capture; confirmation for scope-sensitive details.
- Operator visibility: yes, for project linkage.

### 6.2 Clarification
- Purpose: resolve missing context.
- Allowed actions: ask questions, refine scope, identify constraints.
- Blocked actions: acting on unclear assumptions.
- Required visibility: user-visible.
- Approval requirement: user confirmation where needed.
- Operator visibility: yes when blocked or risk-bearing.

### 6.3 Planning
- Purpose: organize goals, steps, and constraints.
- Allowed actions: plan, outline, compare options, record decisions.
- Blocked actions: execution without approval.
- Required visibility: user-visible and operator-visible when relevant.
- Approval requirement: none for planning; approval for execution steps.
- Operator visibility: yes for project-affecting plans.

### 6.4 Draft/artifact work
- Purpose: create project artifacts without external action.
- Allowed actions: drafts, notes, internal summaries, checklists.
- Blocked actions: sending, publishing, silent external execution.
- Required visibility: draft vs executed must be visible.
- Approval requirement: yes before external use.
- Operator visibility: yes if project-linked or exportable.

### 6.5 Review
- Purpose: inspect project state and validate scope/quality.
- Allowed actions: review, mark stale, correct, annotate.
- Blocked actions: treating review as approval.
- Required visibility: review state visible.
- Approval requirement: may require operator or user review.
- Operator visibility: yes.

### 6.6 Approval pending
- Purpose: hold state before a required decision.
- Allowed actions: wait, show blockers, request confirmation.
- Blocked actions: execution without approval.
- Required visibility: always visible.
- Approval requirement: pending by definition.
- Operator visibility: yes.

### 6.7 Implementation planning
- Purpose: prepare safe implementation paths.
- Allowed actions: plan implementation, identify dependencies, define next safe step.
- Blocked actions: runtime changes.
- Required visibility: plan vs execution distinction visible.
- Approval requirement: user/operator as applicable.
- Operator visibility: yes.

### 6.8 Execution pending
- Purpose: final pre-execution checkpoint.
- Allowed actions: confirmation, validation, rollback planning.
- Blocked actions: execution without approval.
- Required visibility: user-visible and operator-visible.
- Approval requirement: yes.
- Operator visibility: yes.

### 6.9 Support/escalation
- Purpose: preserve continuity during problems or incidents.
- Allowed actions: record support state, blockers, and last safe step.
- Blocked actions: hidden escalation or silent closure.
- Required visibility: user summary and operator detail.
- Approval requirement: user approval when personal data is included.
- Operator visibility: yes.

### 6.10 Closure/archive
- Purpose: end active project continuity while preserving audit.
- Allowed actions: close, archive, deprecate, annotate outcome.
- Blocked actions: silent deletion or revival.
- Required visibility: closure status visible.
- Approval requirement: as needed for scope-sensitive closure.
- Operator visibility: yes.

## 7. Project source/provenance model

Allowed sources:
- direct user statement
- user correction
- project artifact
- memory reference
- session summary
- tool/action outcome
- operator note
- support/escalation record
- approved internal report
- candidate project pattern

Blocked sources:
- hidden reasoning
- unscoped raw private data
- cross-user inference
- OCC/OpenClaw workflow context
- external source without verification
- unsupported psychological inference

## 8. Project transition model

Allowed transitions:
- proposed → active
- active → paused
- active → blocked
- active → waiting for user
- active → waiting for operator
- waiting for user → active after confirmation
- waiting for operator → active after approval
- blocked → active after resolution
- active → completed
- completed → archived/deprecated
- active/stale → stale
- active/stale → contradicted
- contradicted → corrected active state or archived/deprecated

Blocked transitions:
- session-only project frame → global project state silently
- proposed → active without sufficient scope
- blocked → active without resolution
- contradicted → active without correction
- candidate project pattern → approved template without review
- project state → external action without approval

## 9. Project use rules

- project state is not truth by itself
- project state must be surfaced when material to answer/action
- stale project state requires warning or refresh
- contradicted project state cannot drive action
- pending approvals must not disappear
- memory references must show memory status when material
- tool/action availability is not permission
- project state cannot override policy/boundary/safety rules

## 10. User-visible project language

Keep terse:
- “I have this project context…”
- “This project state looks stale.”
- “This decision is recorded for this project.”
- “This is still waiting for your approval.”
- “This project is blocked because…”
- “This is a plan, not an executed action.”
- “Should I update the project state?”
- “I do not have enough confirmed project context yet.”

## 11. Operator-visible project controls

Controls:
- approve project update
- reject project update
- correct project state
- mark stale
- mark contradicted
- invalidate project item
- archive/deprecate project
- freeze project lane/action
- annotate
- require user confirmation
- require source/evidence
- escalate support
- block external action
- request implementation review

## 12. Project correction and contradiction handling

- user correction path
- operator correction path
- contradiction detection
- downgrade behavior
- invalidation behavior
- audit trail
- user-visible correction summary
- rollback/deprecation behavior

## 13. Relationship to Memory State Model

- project state may reference memory items
- memory status must remain visible when material
- memory cannot silently become project fact
- project corrections can create memory correction events
- candidate memory patterns cannot become project rules without review

## 14. Relationship to Operator Observability and Control

- operator sees project scope/status/source/blocked state/pending approvals
- operator can approve/reject/correct/freeze/archive/escalate
- project state changes are auditable
- blocked/high-risk/external actions require operator visibility

## 15. Relationship to First Tool Lanes Selection

Project state supports:
- draft/artifact lane
- project plan/checklist lane
- scoped memory/project update proposal lane
- safe internal report generation lane
- support/escalation record lane

## 16. Relationship to State and Continuity MVP

- project state is a core continuity state category
- session state can point to active project state
- action/tool state can attach to project state
- uncertainty and boundaries affect project state
- operator-visible state includes project state

## 17. Initial rollout vs future scaling

- initial rollout supports minimal project records and visible status
- future scaling requires stronger project isolation, audit, export/delete support
- more users increase project leakage risk
- shared/system templates require stricter review
- third-party project integrations require separate boundary review

## 18. Inclusion/exclusion

Included:
- project item shape
- scope model
- status model
- phase model
- source/provenance model
- transition model
- project use rules
- correction/contradiction handling
- operator controls
- user-visible project language

Excluded:
- storage/database implementation
- hidden project state
- perfect continuity
- cross-user project inference
- automatic execution from project state
- runtime project-state wiring
- public product readiness
- consciousness/self-model claims

## 19. Failure modes

- stale project state treated as current
- wrong project context used
- pending approval forgotten
- project decision invented
- project memory reference used without status
- blocked action treated as available
- cross-user project leakage
- hidden project personalization
- user cannot correct project state
- operator cannot inspect project state
- project state triggers action without approval
- fake continuity claimed

## 20. Validation criteria for future implementation

- every project has owner/scope/status/source
- project state use is visible when material
- stale/contradicted project state is surfaced
- user can correct project state
- operator can inspect/approve/freeze/archive project state
- pending approvals are preserved
- blocked actions have reasons
- no cross-user leakage
- no hidden personalization
- no perfect-continuity claims
- no runtime implementation without separate review

## 21. Future lanes

- `REVIEW_WESLR_PROJECT_STATE_MODEL_V1`
- `DESIGN_WESLR_FIRST_TOOL_LANES_IMPLEMENTATION_PLAN_V1`
- `DESIGN_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`
- `DESIGN_WESLR_MEMORY_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 22. Final judgment

`weslr_project_state_model_design_ready_for_review`
