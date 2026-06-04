# WESLR First Tool Lanes Implementation Plan V1

## 1. Executive summary

First implementation should cover only the approved first tool lanes.

Implementation must be disabled-by-default until separate approval. It must preserve proposal-before-action, visible status, approval, operator audit, and rollback/deprecation.

No external sending, public posting, destructive action, third-party account action, or autonomous multi-step agent behavior. This plan is not runtime activation.

## 2. Scope

Selected lanes to plan:
- draft/artifact creation
- project plan/checklist
- scoped memory/project update proposal
- safe internal report generation
- support/escalation record

Explicitly out of scope:
- external sending/posting
- public publishing
- destructive actions
- payments/contracts/legal/medical/financial authority actions
- broad third-party integrations
- autonomous tool discovery
- automatic behavior updates
- runtime chat wiring
- public product readiness

## 3. Preconditions before implementation

Required before any implementation starts:
- reviewed implementation plan
- exact feature flag or disabled-by-default gate
- tests for every lane
- operator-visible audit records
- visible user-facing statuses
- no silent external action
- no hidden memory/project mutation
- no `.weslr` IO unless separately approved
- protected files untouched unless a later implementation lane explicitly approves them
- rollback plan
- release gate/check pass

## 4. Shared implementation contract

Future shared contract fields:
- lane_id
- action_class
- project_id
- memory_reference_ids
- owner/user scope
- requested action
- risk level
- approval status
- execution status
- failure count
- rollback/deprecation status
- blocked reason
- audit note
- created/updated markers
- operator visibility flag
- user-visible status phrase

## 5. Shared approval model

- approval not required for internal planning/drafting only
- user confirmation required before external use/export/user-affecting memory/project updates
- operator approval required for shared/system/cross-user/high-risk changes
- blocked for external/destructive/deferred lanes
- approval is scoped and not permanent permission

## 6. Shared state model integration

Future implementation must use:
- Project State Model
- Memory State Model
- Operator Observability and Control
- Agentic Tool Use Boundary
- State and Continuity MVP

## 7. Lane 1: Draft / artifact creation implementation plan

Future allowed operations:
- create drafts
- create internal artifacts
- create checklists
- create summaries and reports
- mark draft status explicitly

Future blocked operations:
- sending
- publishing
- externally sharing
- claiming completion when no external action occurred

Required state fields:
- draft status
- owner
- project
- last update
- export status

Required user-visible status:
- draft vs sent/exported distinction

Required operator-visible audit:
- draft created/updated/deleted/export-requested events

Failure handling:
- explain the failure
- do not claim the artifact exists if creation failed

Rollback/deprecation path:
- discard draft
- revise draft
- mark deprecated

Tests required:
- draft/send distinction
- failure does not claim success
- export gating
- operator audit presence

Validation criteria:
- user can clearly tell draft vs sent vs exported
- no silent sending
- no artifact-created claim if failure occurs

## 8. Lane 2: Project plan / checklist implementation plan

Future allowed operations:
- create plans
- create checklists
- stage next steps
- create project summaries

Future blocked operations:
- executing plan steps without approval

Required project state fields:
- project goal
- open questions
- next steps
- blocked items

User-visible plan/execution distinction:
- plan is not execution
- execution requires later approval
- missing scope becomes provisional or clarification-needed

Operator-visible audit:
- plan creation
- edits
- freeze
- archive
- execution approval

Failure handling:
- ask for missing scope
- mark the plan provisional

Rollback/deprecation path:
- revise plan
- archive plan

Tests required:
- plan/execute distinction
- missing scope handling
- approval gating
- operator audit presence

Validation criteria:
- user can clearly tell plan vs executed action
- no execution without approval

## 9. Lane 3: Scoped memory / project update proposal implementation plan

Future allowed operations:
- propose memory/project updates
- mark provisional/confirmed/stale
- summarize continuity

Future blocked operations:
- silent global memory
- cross-user memory
- hidden personalization

Required memory/project state fields:
- scope
- source
- status
- correction path

User-visible proposal/confirmed/stale distinction:
- proposed/provisional/confirmed/stale states remain visible

Operator-visible audit:
- proposal
- confirmation
- stale/contradicted
- invalidation
- archive events

Failure handling:
- keep the item proposed/provisional
- do not silently store

Rollback/deprecation path:
- contradict
- invalidate
- archive
- revert to provisional

Tests required:
- proposal/confirmed/stale distinction
- user confirmation requirement
- operator review for shared/system memory
- no silent global storage

Validation criteria:
- no silent global memory
- no cross-user memory
- no hidden personalization
- user/project updates require confirmation where user-affecting
- shared/system memory requires operator review

## 10. Lane 4: Safe internal report generation implementation plan

Future allowed operations:
- internal summaries
- status reports
- audit-friendly reports
- review packets

Future blocked operations:
- public posting/export without approval
- official benchmark/certification claims

Required report state fields:
- source scope
- audience
- report status
- limitations

User-visible internal/export distinction:
- internal only by default
- export/public use requires approval

Operator-visible audit:
- generation
- export request
- export approval/denial
- withdrawal

Failure handling:
- mark report generation failed or incomplete

Rollback/deprecation path:
- revise report
- withdraw export permission
- archive report

Tests required:
- internal/export distinction
- approval gating
- failure marking
- audit presence

Validation criteria:
- internal-only by default
- export/public use requires approval
- no benchmark/certification claims
- failed/incomplete reports are visibly marked

## 11. Lane 5: Support / escalation record implementation plan

Future allowed operations:
- internal support notes
- escalation notes
- blocked-state summaries
- incident continuity records

Future blocked operations:
- hidden escalation
- silent third-party contact
- unapproved personal data sharing

Required support/escalation state fields:
- escalation reason
- status
- owner
- last safe step

User-visible support/escalation status:
- visible support/escalation status and summary

Operator-visible audit:
- record creation
- updates
- closure
- reopen
- de-escalation

Failure handling:
- explain and stop
- do not pretend escalation exists

Rollback/deprecation path:
- close
- reopen
- annotate
- de-escalate

Tests required:
- support record visibility
- personal-data approval gating
- hidden escalation rejection
- operator audit presence

Validation criteria:
- no hidden escalation
- no silent third-party contact
- personal data inclusion requires user approval
- operator ownership is visible

## 12. Implementation phases

### Phase 0: implementation plan review
Allowed work:
- review the plan
- confirm scope and boundaries
- confirm tests and gates

Forbidden work:
- implementation
- wiring
- runtime changes

Required tests:
- plan review completeness check

Exit criteria:
- plan approved

Rollback/abort criteria:
- scope or boundary mismatch

### Phase 1: contracts and metadata-only helpers
Allowed work:
- define contracts
- define metadata-only helpers
- define state labels and audit fields

Forbidden work:
- runtime activation
- external action
- storage/database code

Required tests:
- contract shape tests
- metadata-only boundaries

Exit criteria:
- contracts verified

Rollback/abort criteria:
- hidden runtime dependency

### Phase 2: synthetic tests only
Allowed work:
- synthetic cases
- synthetic validation
- synthetic edge cases

Forbidden work:
- live user data
- runtime wiring
- external action

Required tests:
- lane classification
- approval mapping
- blocked/deferred rejection

Exit criteria:
- synthetic tests pass

Rollback/abort criteria:
- live-data dependency

### Phase 3: disabled-by-default local dry-run
Allowed work:
- local dry-run
- disabled-by-default gating
- preview of statuses and audits

Forbidden work:
- actual execution
- external sending
- production activation

Required tests:
- draft vs send distinction
- plan vs execute distinction
- proposal vs confirmed memory distinction

Exit criteria:
- dry-run passes under default-off gate

Rollback/abort criteria:
- any reachable runtime activation

### Phase 4: operator-reviewed internal preview
Allowed work:
- operator-reviewed preview
- internal visibility checks
- audit review

Forbidden work:
- public rollout
- broad user exposure

Required tests:
- operator visibility
- audit completeness
- blocked-state visibility

Exit criteria:
- operator review passes

Rollback/abort criteria:
- hidden side effects or audit gaps

### Phase 5: limited controlled rollout gate
Allowed work:
- limited rollout under feature flag
- constrained lane access
- monitored execution boundary

Forbidden work:
- broad enablement
- autonomous extension

Required tests:
- rollback readiness
- approval enforcement
- failure handling

Exit criteria:
- release gate/check pass under constraints

Rollback/abort criteria:
- approval bypass
- external action reachability

### Phase 6: review before expansion
Allowed work:
- collect feedback
- review scope
- decide whether to expand

Forbidden work:
- silent lane expansion
- automatic broadening

Required tests:
- expansion review checklist

Exit criteria:
- explicit approval for any new lane

Rollback/abort criteria:
- drift beyond approved lanes

## 13. Test plan

Required tests:
- lane classification
- approval requirement mapping
- blocked/deferred lane rejection
- draft vs send distinction
- plan vs execute distinction
- proposal vs confirmed memory distinction
- internal vs export report distinction
- support record visibility
- failure does not claim success
- retry bounded
- audit record present
- operator visibility present
- no protected-file drift
- no runtime wiring unless later approved
- no `.weslr` IO

## 14. Release-gate and protected-file plan

- no broad allowlists
- exact-file allowances only
- protected files remain untouched unless a later implementation lane explicitly approves edits
- release gate must block hidden prompt/answer key/protected-material leaks
- release gate must block broad docs/source/test exemptions
- release check must pass before commit

## 15. Rollback and abort criteria

Abort if:
- runtime wiring appears
- external action becomes reachable
- protected files change outside approved scope
- hidden memory/project mutation appears
- `.weslr` IO appears
- cross-user leakage risk appears
- approval checks can be bypassed
- audit missing
- failed action claims success
- release gate/check fails
- public-readiness or AGI/consciousness claims appear

## 16. Operator review checkpoints

- before implementation starts
- before any feature flag exists
- before any dry-run
- before any user-visible preview
- before any rollout
- before any lane expansion

## 17. User-visible language requirements

- “I can draft it, but I will not send it.”
- “This is a plan, not an executed action.”
- “Should I update this project memory?”
- “This is an internal report unless approved for export.”
- “I can record this for support/escalation visibility.”
- “This action is blocked because…”
- “This requires your approval first.”
- “This failed; I will not claim it succeeded.”

## 18. Operator-visible requirements

- lane id
- requested action
- project/memory linkage
- approval status
- blocked reason
- failure count
- audit note
- rollback/deprecation status
- export/external-use status
- support/escalation status

## 19. Relationship to prior designs

This implementation plan is downstream of and constrained by:
- First Tool Lanes Selection
- Project State Model
- Memory State Model
- Operator Observability and Control
- Agentic Tool Use Boundary
- State and Continuity MVP
- Product Shell Minimum

## 20. Inclusion/exclusion

Included:
- implementation planning only
- lane contracts
- approval/status/audit requirements
- tests and validation plan
- rollout phases
- rollback/abort criteria

Excluded:
- actual implementation
- runtime wiring
- storage/database code
- external sending/posting
- destructive actions
- third-party integrations
- public product readiness
- hidden memory/project state
- autonomous multi-step agents

## 21. Failure modes

- plan accidentally becomes implementation
- disabled-by-default not enforced
- draft treated as sent
- plan treated as executed
- memory proposal silently stored
- report exported without approval
- support record hidden
- operator audit missing
- approval reused too broadly
- lane expansion without review
- protected-file drift
- release-gate weakening
- public-readiness claim drift

## 22. Validation criteria for future implementation

- every lane has explicit contract
- every action has class/status
- every user-affecting change has approval state
- every blocked action has reason
- every lane has tests
- operator audit exists
- no silent external action
- no hidden memory/project mutation
- no `.weslr` IO without separate review
- no runtime implementation without separate approval
- no protected-file drift

## 23. Future lanes

- `REVIEW_WESLR_FIRST_TOOL_LANES_IMPLEMENTATION_PLAN_V1`
- `IMPLEMENT_WESLR_FIRST_TOOL_LANES_CONTRACTS_METADATA_ONLY_V1`
- `DESIGN_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`
- `DESIGN_WESLR_MEMORY_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 24. Final judgment

`weslr_first_tool_lanes_implementation_plan_ready_for_review`
