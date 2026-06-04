# WESLR Memory State Model V1

## 1. Executive summary

Memory is scoped continuity state, not truth by itself.

Memory must have scope, status, source, timestamp or sequence marker, correction path, and auditability. Memory must be visible when used. No hidden memory, fake memory, perfect memory, cross-user leakage, or silent global personalization.

## 2. Purpose

This memory model exists to:
- reduce repeated context loss
- support project continuity
- support user-approved preferences
- distinguish proposed/provisional/confirmed/stale/contradicted memory
- make memory correction possible
- make memory use visible
- support operator review
- prevent hidden personalization and memory drift

## 3. Memory item shape

Every memory item should be able to carry:
- memory_id
- owner/user scope
- project/session scope
- tenant/account scope if applicable
- memory type
- memory content summary
- source type
- source reference or safe provenance
- status
- confidence/evidence level
- created marker
- last updated marker
- last used marker
- correction/deprecation link
- operator audit note
- visibility flag
- export/deletion/revocation relevance

## 4. Memory scopes

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
- no OCC workflow context as WESLR memory
- no raw private content as global memory
- no hidden personalization
- system-wide memory requires review

## 5. Memory statuses

### 5.1 Absent
- Meaning: no memory item exists for the scope.
- Allowed use: none.
- User-visible phrase: “I do not have confirmed memory for that.”
- Operator-visible meaning: no stored item.
- Transition rules: can move to proposed.
- Correction path: create proposed memory if appropriate.

### 5.2 Proposed
- Meaning: candidate memory has been identified but not yet accepted.
- Allowed use: not as confirmed fact.
- User-visible phrase: “Should I save this to the project memory?”
- Operator-visible meaning: awaiting review or confirmation.
- Transition rules: can move to provisional, or be rejected.
- Correction path: confirm, reject, or revise.

### 5.3 Provisional
- Meaning: likely useful, but not fully confirmed.
- Allowed use: as tentative context only.
- User-visible phrase: “This memory is provisional.”
- Operator-visible meaning: usable with caution.
- Transition rules: can move to confirmed, stale, or contradicted.
- Correction path: refresh, confirm, or downgrade.

### 5.4 Confirmed
- Meaning: accepted scoped memory.
- Allowed use: as active scoped memory.
- User-visible phrase: “I remember this as project context…”
- Operator-visible meaning: approved memory in scope.
- Transition rules: can move to stale, contradicted, or archived/deprecated.
- Correction path: update, stale, contradict, or invalidate.

### 5.5 Stale
- Meaning: memory may be outdated or no longer fully reliable.
- Allowed use: only with warning or refresh.
- User-visible phrase: “This may be stale.”
- Operator-visible meaning: needs revalidation.
- Transition rules: can move to confirmed after refresh, or to contradicted.
- Correction path: refresh or replace.

### 5.6 Contradicted
- Meaning: memory conflicts with newer evidence or correction.
- Allowed use: not as active fact.
- User-visible phrase: “You corrected this earlier.”
- Operator-visible meaning: should not drive active behavior.
- Transition rules: can move to invalidated or archived/deprecated.
- Correction path: invalidate or replace with confirmed memory.

### 5.7 Invalidated
- Meaning: memory is no longer usable as active memory.
- Allowed use: audit only.
- User-visible phrase: “I do not have confirmed memory for that.”
- Operator-visible meaning: removed from active use.
- Transition rules: can move to archived/deprecated.
- Correction path: archive or replace if a new memory exists.

### 5.8 Archived/deprecated
- Meaning: inactive but retained for audit/continuity.
- Allowed use: inspection or audit only.
- User-visible phrase: “This pattern is only a candidate, not a rule.”
- Operator-visible meaning: inactive history, not active memory.
- Transition rules: normally not active again without explicit review.
- Correction path: new memory item instead of revival.

## 6. Memory type categories

### 6.1 User preference
- Allowed: scoped preferences that the user approved.
- Blocked: hidden preference inference, psychological profiling.
- Confirmation requirement: user confirmation.
- Visibility requirement: user-visible and operator-visible where relevant.
- Stale/contradiction handling: downgrade or ask for confirmation.

### 6.2 Project fact
- Allowed: project-specific facts.
- Blocked: unrelated user history, cross-user inference.
- Confirmation requirement: usually project/user confirmation.
- Visibility requirement: visible in project continuity surfaces.
- Stale/contradiction handling: refresh or replace.

### 6.3 Project decision
- Allowed: explicit decisions made for a project.
- Blocked: hidden decision drift.
- Confirmation requirement: user or operator review depending on scope.
- Visibility requirement: visible in continuity and audit.
- Stale/contradiction handling: revise or invalidate.

### 6.4 Task/checklist continuity
- Allowed: task continuity, open steps, blockages.
- Blocked: hidden task execution, untracked external commitments.
- Confirmation requirement: project authority as applicable.
- Visibility requirement: project-visible.
- Stale/contradiction handling: update or close.

### 6.5 Tool/action outcome
- Allowed: success/failure/blocked/rollback outcomes.
- Blocked: fabricated completion, hidden background action.
- Confirmation requirement: derived from actual outcomes.
- Visibility requirement: user-visible when it affects current work; operator-visible for audit.
- Stale/contradiction handling: supersede with latest outcome.

### 6.6 Support/escalation note
- Allowed: continuity for support and escalation.
- Blocked: hidden escalation, unapproved data sharing.
- Confirmation requirement: user approval when personal data is included.
- Visibility requirement: user summary and operator detail.
- Stale/contradiction handling: update or close.

### 6.7 Correction event
- Allowed: record that a prior memory was corrected.
- Blocked: burying corrections.
- Confirmation requirement: evidence of correction.
- Visibility requirement: audit-visible.
- Stale/contradiction handling: correction is the handling.

### 6.8 Candidate pattern
- Allowed: repeated pattern with evidence.
- Blocked: automatic global behavior update.
- Confirmation requirement: review/approval.
- Visibility requirement: operator-visible and user-visible when behavior-affecting.
- Stale/contradiction handling: downgrade or remove.

### 6.9 Boundary/safety-relevant note
- Allowed: scoped safety constraints, boundaries, approvals.
- Blocked: hidden policy exceptions.
- Confirmation requirement: governed review.
- Visibility requirement: visible when material to action.
- Stale/contradiction handling: revise through review.

### 6.10 Source/provenance note
- Allowed: source and provenance metadata.
- Blocked: unsupported provenance or hidden reasoning.
- Confirmation requirement: source must be known and acceptable.
- Visibility requirement: visible for memory and learning.
- Stale/contradiction handling: mark insufficient or invalid.

## 7. Memory source/provenance model

Allowed source types:
- direct user confirmation
- user correction
- project artifact
- session summary
- tool/action outcome
- operator note
- support/escalation record
- approved synthetic/rehearsal case
- candidate observational pattern

Blocked sources:
- hidden reasoning
- unscoped raw private data
- cross-user inference
- OCC/OpenClaw workflow context
- external source without verification
- unsupported psychological inference

## 8. Memory transition model

Allowed transitions:
- absent → proposed
- proposed → provisional
- proposed/provisional → confirmed
- confirmed → stale
- confirmed/provisional → contradicted
- contradicted → invalidated
- stale → confirmed after refresh
- any non-active state → archived/deprecated
- candidate pattern → approved only through review

Blocked transitions:
- proposed → system-wide approved without review
- stale → confirmed without refresh
- contradicted → confirmed without correction
- candidate pattern → active rule without approval
- session-only → global memory silently

## 9. Memory use rules

- memory is not truth by itself
- memory must be surfaced when material to answer/action
- stale memory requires warning or refresh
- contradicted memory cannot be used as active fact
- inferred/provisional memory must not be stated as confirmed
- user-confirmed memory outranks inferred memory
- operator-reviewed system memory outranks unreviewed candidate patterns
- memory cannot override policy/boundary/safety rules

## 10. User-visible memory language

Keep terse:
- “I remember this as project context…”
- “This memory is provisional.”
- “This may be stale.”
- “You corrected this earlier.”
- “I do not have confirmed memory for that.”
- “Should I save this to the project memory?”
- “Should I update or invalidate the old memory?”
- “This pattern is only a candidate, not a rule.”

## 11. Operator-visible memory controls

Controls:
- approve
- reject
- confirm
- mark provisional
- mark stale
- mark contradicted
- invalidate
- archive/deprecate
- roll back
- annotate
- require user confirmation
- require source/evidence
- block promotion

## 12. Memory correction and contradiction handling

- user correction path
- operator correction path
- contradiction detection
- downgrade behavior
- invalidation behavior
- audit trail
- user-visible correction summary
- rollback/deprecation behavior

## 13. Export/deletion/revocation readiness

Design only:
- memory should be traceable by owner/scope
- memory should be exportable later by scope
- memory should be deletable/revocable later subject to audit/legal boundaries
- archived/deprecated memory should not be active
- deletion implementation requires separate review

## 14. Relationship to State and Continuity MVP

- memory state is a subset of continuity state
- project/session state may reference memory
- memory status must be visible in continuity surfaces
- stale/contradicted memory affects session uncertainty
- pending memory approvals must not disappear

## 15. Relationship to Operator Observability and Control

- operator sees memory status, scope, source, contradiction, stale state, and approval queue
- operator can approve/reject/correct/invalidate/archive
- system-wide memory and candidate patterns require operator review
- memory changes must be auditable

## 16. Relationship to Governed Observational Learning

- observed patterns become candidate memory only
- candidate patterns do not become rules silently
- evidence count/confidence must be tracked
- learning cannot silently change behavior
- behavior-pack promotion is separate and review-gated

## 17. Initial rollout vs future scaling

- initial rollout should support minimal project/user memory statuses
- future scaling requires stronger isolation, audit, export/delete support
- more users increase leakage risk
- shared/system memory requires stricter review
- third-party memory sources require separate boundary review

## 18. Inclusion/exclusion

Included:
- scoped memory items
- status model
- source/provenance model
- correction and contradiction handling
- operator controls
- user-visible memory language
- export/deletion/revocation readiness

Excluded:
- storage/database implementation
- hidden memory
- perfect memory
- raw private content as global memory
- cross-user memory inference
- automatic behavior updates
- consciousness/self-model claims
- runtime memory wiring

## 19. Failure modes

- stale memory treated as truth
- provisional memory stated as confirmed
- cross-user leakage
- hidden personalization
- user cannot correct memory
- operator cannot inspect memory status
- candidate pattern becomes rule
- memory overrides policy
- memory source/provenance missing
- deletion/revocation impossible later
- fake memory claimed

## 20. Validation criteria for future implementation

- every memory has owner/scope/status/source
- memory use is visible when material
- stale/contradicted memory is surfaced
- user can correct user/project memory
- operator can inspect/approve/invalidate memory
- candidate patterns cannot become rules silently
- no cross-user leakage
- no hidden personalization
- no perfect-memory claims
- no runtime implementation without separate review

## 21. Future lanes

- `REVIEW_WESLR_MEMORY_STATE_MODEL_V1`
- `DESIGN_WESLR_PROJECT_STATE_MODEL_V1`
- `DESIGN_WESLR_FIRST_TOOL_LANES_IMPLEMENTATION_PLAN_V1`
- `DESIGN_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`
- `DESIGN_WESLR_MEMORY_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 22. Final judgment

`weslr_memory_state_model_design_ready_for_review`
