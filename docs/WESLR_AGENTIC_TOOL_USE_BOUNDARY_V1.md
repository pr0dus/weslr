# WESLR Agentic Tool Use Boundary V1

## 1. Executive summary

WESLR may be action-capable only through bounded, visible, approved tool lanes.

Agentic behavior here means proposal, validation, approval, status, execution boundary, recovery, and auditability. It does not mean unrestricted autonomy, silent action, self-directed external action, or autonomous agent claims. The boundary is future-scalable and not limited to the initial rollout.

## 2. Purpose

This boundary exists to protect:
- user trust
- safe external action
- proposal-before-action
- validation-before-execution
- approval where needed
- operator visibility
- failure recovery
- no hidden autonomy
- future scaling without weakening boundaries

## 3. Agentic capability classes

### 3.1 Information-only help
- Description: explain, analyze, recommend, summarize.
- Allowed status: always allowed.
- Approval requirement: none.
- Operator visibility: normal logging only.
- Examples: explain a workflow, compare options, identify risk.
- Risks: mistaken as action.
- Scaling note: safe baseline.

### 3.2 Planning / proposal
- Description: create a plan, suggest steps, prepare an action proposal.
- Allowed status: allowed.
- Approval requirement: none for draft planning.
- Operator visibility: visible when tied to a project.
- Examples: task plan, rollout plan, email draft plan.
- Risks: plan treated as execution.
- Scaling note: should remain common.

### 3.3 Draft creation
- Description: create drafts for documents, messages, checklists, reports.
- Allowed status: allowed.
- Approval requirement: required before external use.
- Operator visibility: visible if project-linked.
- Examples: email draft, support reply draft, checklist.
- Risks: draft mistaken for sent action.
- Scaling note: safe first tool lane.

### 3.4 Local / internal artifact creation
- Description: create internal files, notes, summaries, or workspace artifacts that stay inside the controlled workspace.
- Allowed status: allowed when scoped.
- Approval requirement: user or operator approval depending on scope.
- Operator visibility: required for project-affecting artifacts.
- Examples: project note, internal report, issue summary.
- Risks: accidental external sharing.
- Scaling note: useful and low-risk if contained.

### 3.5 Reversible workspace action
- Description: a non-destructive action inside the controlled workspace that can be undone or replaced.
- Allowed status: allowed with review.
- Approval requirement: user confirmation for user-owned changes; operator approval for system-wide effects.
- Operator visibility: required.
- Examples: update a scoped memory note, mark a task done, revise a draft.
- Risks: mistaken scope or silent mutation.
- Scaling note: can expand cautiously with rollback.

### 3.6 External communication action
- Description: send or prepare to send a message to another person/system.
- Allowed status: blocked until approved.
- Approval requirement: explicit user approval; operator approval for sensitive cases.
- Operator visibility: required for anything beyond trivial low-risk use.
- Examples: send email, message a customer, post a reply.
- Risks: unauthorized communication, reputational harm.
- Scaling note: grow slowly and only with clear audit.

### 3.7 External account / system action
- Description: change or operate an external account or system.
- Allowed status: restricted.
- Approval requirement: explicit approval plus operator visibility.
- Operator visibility: required.
- Examples: change account settings, trigger third-party workflow.
- Risks: security, data loss, unauthorized side effects.
- Scaling note: separate boundary review required for each integration.

### 3.8 Destructive action
- Description: delete, revoke, overwrite, pay, publish, or otherwise cause irreversible or hard-to-reverse effects.
- Allowed status: usually blocked in early rollout.
- Approval requirement: explicit approval and operator review where applicable.
- Operator visibility: required.
- Examples: delete records, send payment, publish externally, revoke access.
- Risks: irreversible harm.
- Scaling note: only after strong controls and review.

### 3.9 High-risk action
- Description: action affecting safety, rights, finances, legality, identity, or major operational outcomes.
- Allowed status: restricted or blocked.
- Approval requirement: operator approval and/or external professional referral.
- Operator visibility: required.
- Examples: legal filing, medical-adjacent action, financial transfer.
- Risks: harm, liability, trust loss.
- Scaling note: never scaled by default.

### 3.10 Blocked action
- Description: action not allowed in current state.
- Allowed status: blocked.
- Approval requirement: not applicable until boundary changes.
- Operator visibility: required if requested repeatedly or if policy-sensitive.
- Examples: action outside scope, missing authority, unsafe request.
- Risks: confusion if boundary is unclear.
- Scaling note: should be explicit and stable.

## 4. Initial controlled-rollout tool lanes

### 4.1 Draft / artifact creation lane
- Why useful: produces immediate value without external side effects.
- Why bounded: output stays in draft or internal artifact form.
- Required approval: user approval before external use.
- Failure handling: if generation fails, return a draft-status explanation.
- Validation criteria: draft vs send must be visible.
- What must not happen: silent sending or external publishing.
- How it could later scale: add more artifact types, not more autonomy.

### 4.2 Project plan / checklist lane
- Why useful: helps the user structure work.
- Why bounded: planning is not execution.
- Required approval: none for planning, approval for execution steps.
- Failure handling: if unclear, ask for missing scope.
- Validation criteria: user can see that it is a plan.
- What must not happen: hidden task creation outside scope.
- How it could later scale: richer workflows, same boundary.

### 4.3 Scoped memory / project update proposal lane
- Why useful: preserves continuity.
- Why bounded: memory changes are scoped and reviewable.
- Required approval: user confirmation or operator approval depending on scope.
- Failure handling: mark as provisional if uncertain.
- Validation criteria: memory status visible and reversible.
- What must not happen: silent global memory changes.
- How it could later scale: more scoped memory classes, not global drift.

### 4.4 Support / escalation record lane
- Why useful: creates visible incident/support continuity.
- Why bounded: record creation is internal and audit-focused.
- Required approval: user approval when personal data is included.
- Failure handling: if the record cannot be made, explain why and stop.
- Validation criteria: operator can see the record and status.
- What must not happen: hidden incident creation or hidden escalation.
- How it could later scale: more structured support categories.

### 4.5 Safe internal report generation lane
- Why useful: produces reviewable summaries for operators or projects.
- Why bounded: report stays internal unless approved for export.
- Required approval: user or operator approval for export.
- Failure handling: report failure must be explicit.
- Validation criteria: scope, source, and audience are visible.
- What must not happen: public posting by default.
- How it could later scale: richer internal analytics with review gates.

## 5. Proposal-before-action model

Stages:
1. user request
2. intent classification
3. action class detection
4. risk check
5. capability check
6. proposal
7. user approval or operator approval
8. execution only if allowed
9. status update
10. result summary
11. audit record
12. rollback/fallback if possible

## 6. Approval model

### No approval needed
- information-only help
- safe drafting that stays internal until explicitly sent
- planning/proposal
- low-risk local summaries

### User confirmation required
- external communication draft to be sent
- scoped memory update affecting the user’s project
- reversible workspace action that changes user-owned state

### Operator approval required
- system-wide changes
- sensitive support/escalation actions
- anything with policy, security, or multi-user impact
- destructive/high-risk actions

### External/professional referral required
- medical/legal/financial actions where WESLR should not act as authority
- cases that exceed the system’s safe role

### Blocked
- unauthorized external action
- destructive action without explicit approval
- hidden background operations
- anything outside capability or policy

## 7. Tool/action status labels

- `action_requested`
- `intent_unclear`
- `action_classified`
- `capability_available`
- `capability_unavailable`
- `risk_low`
- `risk_medium`
- `risk_high`
- `approval_not_required`
- `user_approval_required`
- `operator_approval_required`
- `action_proposed`
- `action_approved`
- `action_running`
- `action_completed`
- `action_failed`
- `action_blocked`
- `rollback_available`
- `rollback_unavailable`
- `escalation_needed`

## 8. User-visible language

Keep terse:
- “I can propose this action.”
- “This needs your approval before I do anything.”
- “This affects another person/system, so I need confirmation.”
- “I can draft it, but I will not send it.”
- “This action is blocked because…”
- “The action failed once; I will not retry blindly.”
- “Here is the safe alternative.”
- “This requires operator review.”

## 9. Operator-visible action state

Operator/admin should see:
- user/project
- requested action
- action class
- risk level
- approval status
- capability status
- tool status
- failure count
- blocked reason
- escalation reason
- rollback availability
- final outcome
- audit note

## 10. Tool failure and recovery

- retry once with bounded rule
- no infinite retry loops
- fallback path
- user-visible failure explanation
- operator-visible failure record
- escalation when repeated failure
- no silent success claim

## 11. External action boundaries

Strict rules:
- no external communication sent without approval
- no account/system changes without approval
- no destructive action without explicit approval and operator visibility
- no legal/financial/medical authority actions
- no action affecting others without extra caution
- no hidden background external action

## 12. Destructive/high-risk action boundary

Include as high risk:
- deletion
- payment
- contract/legal filing
- medical/legal/financial advice action
- identity/account change
- public posting
- data export/sharing
- contacting third parties
- irreversible tool calls

Most of these should be blocked or operator-approved during early rollout.

## 13. Relationship to average-user deep communication

- tool-use language must stay clear and non-theatrical
- action approval reinforces user agency
- practical next steps may include proposals, not silent execution
- deep communication means better action judgment, not more autonomy

## 14. Relationship to metacognitive / cybernetic / learning layers

- metacognition identifies capability, boundary, and action status
- cybernetic regulation handles failure, retry, and escalation
- observational learning may notice repeated tool failure patterns
- learning must not silently change tool behavior
- candidate patterns require review

## 15. Controlled rollout vs future scaling

- initial rollout should use few tool lanes
- future growth may add tool lanes only through review
- more users do not reduce approval requirements
- scaling requires stronger observability, not weaker boundaries
- system-wide tool behavior changes require explicit review
- third-party integrations require separate boundary review

## 16. Inclusion / exclusion

### Included
- proposal-before-action
- visible action status
- limited approved tool lanes
- draft/internal artifact creation
- operator-visible escalation
- bounded retry/fallback
- blocked-action explanations
- auditability
- scalable approval model

### Excluded
- unrestricted autonomous agents
- silent external action
- destructive actions without explicit approval
- hidden background operations
- public marketplace/tool ecosystem without separate review
- broad third-party integrations without separate review
- self-directed tool discovery
- automatic behavior updates from tool outcomes

## 17. Failure modes

- action confusion
- silent action
- over-automation
- user thinks draft was sent
- tool failure hidden
- unauthorized retry loop
- destructive side effect
- third-party harm
- operator invisibility
- rollback missing
- capability inflation
- treating tool availability as permission
- using approval once as permanent permission
- scaling tool access before observability

## 18. Validation criteria for future implementation

- every action has a class
- approval required for external/destructive/high-risk actions
- draft vs send distinction visible
- failed action does not claim success
- repeated failure stops
- operator-visible audit exists
- blocked action explains reason
- no silent external action
- no unrestricted autonomy
- no AGI/superintelligence/aliveness/certification claims
- no runtime implementation without separate review

## 19. Future lanes

- `REVIEW_WESLR_AGENTIC_TOOL_USE_BOUNDARY_V1`
- `DESIGN_WESLR_STATE_AND_CONTINUITY_MVP_V1`
- `DESIGN_WESLR_FIRST_TOOL_LANES_SELECTION_V1`
- `DESIGN_WESLR_OPERATOR_OBSERVABILITY_AND_CONTROL_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 20. Final judgment

`weslr_agentic_tool_use_boundary_design_ready_for_review`
