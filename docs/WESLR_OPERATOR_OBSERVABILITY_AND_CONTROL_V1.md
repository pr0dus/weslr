# WESLR Operator Observability and Control V1

## 1. Executive summary

Operator observability means visible state, approvals, blocked items, escalations, failures, and audit trails.

Operator control means the ability to approve, reject, pause, annotate, correct, roll back, deprecate, or escalate.

This is design-only. It does not create an admin dashboard or runtime behavior. Observability must grow stronger as users and tool lanes scale.

## 2. Purpose

This layer exists to:
- prevent hidden behavior
- prevent silent external action
- make tool/action status auditable
- make state/memory corrections visible
- support support/escalation records
- support safe first tool lanes
- support future scaling
- preserve owner/operator authority

## 3. Operator-visible domains

The operator should be able to see:
- user/account state
- project state
- session state
- memory state
- action/tool state
- first tool lanes
- support/escalation records
- candidate learning patterns
- blocked actions
- validation/release-gate status
- incident/audit trail

## 4. Operator control actions

The operator should be able to:
- approve
- reject
- pause
- block
- annotate
- correct
- mark stale
- invalidate
- roll back
- deprecate/archive
- escalate
- request more context
- require user confirmation
- require implementation review
- freeze a lane

## 5. Approval queue model

Approval queue items:
- proposed memory update
- project update proposal
- external action proposal
- export/publication proposal
- support/escalation record
- blocked action requiring review
- high-risk action request
- candidate system-wide pattern
- lane expansion proposal

Each queue item should show:
- owner/user/project
- requested change/action
- risk level
- scope
- evidence/source
- approval status
- last update
- operator decision
- audit note

## 6. Blocked-state visibility

Blocked states that must be visible:
- boundary blocked
- capability unavailable
- approval missing
- source/evidence insufficient
- stale/contradicted memory
- action failed
- repeated failure stopped
- export/publication blocked
- high-risk action blocked
- integration not approved

## 7. Audit trail requirements

Every operator-visible change should record:
- who/what initiated it
- timestamp or sequence marker
- affected user/project/session
- scope
- old state
- new state
- reason
- approval/denial
- rollback availability
- related artifact/report if any

## 8. First tool lanes observability

### 8.1 Draft / artifact creation
Operator sees:
- draft status
- owner/project linkage
- export status
- blocked reason if sending is requested

Operator can approve/block:
- external use/export
- project-affecting draft changes where needed

Visible failures:
- creation failed
- export blocked
- draft mistreated as sent

Audit required:
- draft created/updated/deleted/export-requested state changes

### 8.2 Project plan / checklist
Operator sees:
- project goal
- open questions
- next steps
- blocked items
- plan/execution separation

Operator can approve/block:
- execution steps
- plan freeze or revision

Visible failures:
- missing scope
- plan marked provisional
- execution attempted without approval

Audit required:
- plan creation, edits, freeze, archive, execution approval

### 8.3 Scoped memory / project update proposal
Operator sees:
- scope
- source
- status
- correction path
- contradiction/staleness

Operator can approve/block:
- user/project memory changes
- shared/system memory changes
- promotion from proposed to confirmed

Visible failures:
- memory not confirmed
- memory contradicted
- memory update blocked

Audit required:
- proposal, confirmation, stale/contradicted, invalidation, archive events

### 8.4 Safe internal report generation
Operator sees:
- source scope
- audience
- report status
- limitations
- export state

Operator can approve/block:
- export or external use
- report withdrawal/deprecation

Visible failures:
- report incomplete
- export blocked
- report marked internal-only

Audit required:
- report generation, export request, export approval/denial, withdrawal

### 8.5 Support / escalation record
Operator sees:
- escalation reason
- status
- owner
- last safe step
- blocked-state summary

Operator can approve/block:
- escalation flow
- support-handling changes
- personal-data inclusion where required

Visible failures:
- record creation failed
- escalation hidden
- support ownership unclear

Audit required:
- record creation, updates, closure, reopen, de-escalation

## 9. User-facing vs operator-facing separation

User sees:
- their own project/session state
- visible approvals needed from them
- draft/plan/report/support status where relevant
- correction and confirmation prompts
- blocked reasons that affect them

Operator sees:
- cross-user/system-wide state only as needed for governance
- approvals, blocks, failures, audits, escalations
- candidate patterns and lane status
- support and correction workflows

Must not be hidden from user when user-affecting:
- approvals needed from the user
- state changes affecting their project/session
- memory changes that affect them
- blocking reasons that change the user experience

Must not be exposed to user if internal-only/operator-only:
- internal operator notes
- multi-user governance details
- privileged audit context beyond user relevance
- hidden risk heuristics that would create false authority

Hidden state must not change user experience without trace.

## 10. Escalation model

### Triggers
- repeated tool failure
- high-risk request
- unclear authority
- user safety concern
- boundary conflict
- data/privacy concern
- support need
- operator review needed
- suspected stale/corrupt state

### Outcomes
- approved
- blocked
- needs user confirmation
- needs external/professional help
- deferred
- archived
- implementation review required

## 11. Rollback/deprecation model

Rollback is possible when the state is reversible or when a proposed change has not been externally relied upon.

Deprecation is safer than deletion when:
- the item may still be referenced by audit or continuity
- the item should not be active but should remain inspectable
- the item is a candidate pattern, lane decision, or prior note

Handling rules:
- stale/invalidated memory is marked, not silently retained as current
- failed artifacts/reports are withdrawn or marked failed/incomplete
- tool-lane decisions can be frozen or reverted through review
- every operator action is audited

## 12. Relationship to State and Continuity MVP

Operator observability depends on the state model being visible and scoped.

It must show:
- state scope/status
- stale/contradicted state
- correction paths
- pending approvals
- candidate patterns that must not become rules without approval

## 13. Relationship to Agentic Tool Use Boundary

Operator control is required for high-risk, system-wide, external, and destructive classes.

Proposal-before-action depends on visible approval state.

Tool availability is not permission.

Failed tools must be visible.

Approvals must not become permanent permission.

## 14. Relationship to First Tool Lanes Selection

The selected first lanes require operator observability before implementation.

Deferred lanes require stronger operator controls before activation.

Lane expansion requires review.

## 15. Initial rollout vs future scaling

Initial rollout can use minimal operator views.

Scaling requires stronger dashboards, filters, alerts, and audit exports.

More users increase isolation and audit needs.

More tool lanes increase approval complexity.

Third-party integrations require separate observability review.

## 16. Inclusion/exclusion

Included:
- approval queue design
- blocked-state visibility
- audit trail requirements
- support/escalation visibility
- memory/project correction controls
- lane freeze/deprecation control
- operator-visible first-lane statuses

Excluded:
- live dashboard implementation
- runtime permissions code
- automated operator replacement
- silent admin overrides
- hidden user-affecting state changes
- public product readiness
- broad third-party admin integrations

## 17. Failure modes

- operator cannot see pending approval
- operator cannot see blocked state
- user-affecting state changed silently
- approval reused too broadly
- rollback unavailable but assumed
- stale memory remains active
- support record hidden
- audit trail incomplete
- lane expansion without review
- high-risk action approved without context
- operator dashboard becomes source of hidden personalization

## 18. Validation criteria for future implementation

- every approval has owner/scope/status
- every blocked action has reason
- every user-affecting state change is traceable
- operator can pause/freeze lanes
- stale/contradicted memory is visible
- support/escalation records are inspectable
- audit trail exists for lane actions
- no silent external action
- no runtime implementation without separate review

## 19. Future lanes

- `REVIEW_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`
- `DESIGN_WESLR_MEMORY_STATE_MODEL_V1`
- `DESIGN_WESLR_PROJECT_STATE_MODEL_V1`
- `DESIGN_WESLR_FIRST_TOOL_LANES_IMPLEMENTATION_PLAN_V1`
- `DESIGN_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 20. Final judgment

`weslr_operator_observability_and_control_design_ready_for_review`
