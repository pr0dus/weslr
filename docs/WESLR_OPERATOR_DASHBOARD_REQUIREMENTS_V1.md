# WESLR Operator Dashboard Requirements V1

## 1. Executive summary

The operator dashboard is an observability and control surface, not an autonomous controller.
It should make WESLR state visible: approvals, blocked items, first-tool-lane contract status, memory/project state, support/escalation records, audits, failures, rollback/deprecation, and validation status.
It must not create hidden admin overrides or silent user-affecting state changes.
It should support an initial controlled rollout and later scaling.

## 2. Purpose

The dashboard exists to:
- make pending approvals visible
- make blocked actions visible
- make project and memory state inspectable
- make first tool lanes auditable
- make support/escalation visible
- make failures and retries visible
- make rollback/deprecation visible
- make validation/release status visible
- reduce hidden behavior and hidden personalization risk
- support operator decisions without replacing operator judgment

## 3. Non-goals

This requirements lane explicitly excludes:
- dashboard implementation
- live backend/API design
- runtime permission system
- autonomous operator replacement
- hidden admin override
- silent user-affecting state changes
- broad third-party integrations
- public product readiness
- cross-user browsing without governance
- raw private data dumping
- production incident response automation

## 4. Operator dashboard domains

The dashboard requirements cover these sections:
- overview/home
- approvals queue
- blocked actions
- user/account scope
- project state
- memory state
- first tool lanes/contracts
- support/escalation
- audit trail
- validation/release status
- rollback/deprecation
- incidents/risk flags
- lane expansion candidates

## 5. Overview/home requirements

The overview should show:
- active projects count
- pending approvals count
- blocked actions count
- stale or contradicted memory/project count
- failed action/contract count
- support/escalation count
- validation/release-gate status
- latest high-risk flags
- no raw private data by default

## 6. Approval queue requirements

Each approval item should show:
- approval_id
- owner/user/project scope
- lane_id/action_class
- requested action
- risk level
- required approval type
- approval status
- source/provenance
- user-visible summary
- operator note
- blocked reason if blocked
- rollback/deprecation status
- created/updated markers

Controls allowed in requirements only:
- approve
- reject
- request user confirmation
- request more evidence
- block
- escalate
- mark stale
- archive/deprecate

## 7. Blocked actions requirements

Each blocked item should show:
- blocked reason
- boundary triggered
- lane/action class
- affected project/memory/support record
- user-visible blocked phrase
- operator-only note
- retry count
- last safe step
- required next approval/review
- rollback/deprecation option

## 8. Project state dashboard requirements

Each project view should show:
- project_id
- owner/user scope
- project status
- project phase
- current summary
- open questions
- constraints
- decisions
- active tasks/checklists
- pending approvals
- blocked actions
- linked artifacts/reports
- linked memory references and memory status
- support/escalation references
- last updated/used markers
- stale/contradicted flags
- correction path

Controls allowed in requirements only:
- correct
- mark stale
- mark contradicted
- invalidate item
- freeze lane/action
- archive/deprecate
- request user confirmation

## 9. Memory state dashboard requirements

Each memory item should show:
- memory_id
- scope
- status
- type
- source/provenance
- confidence/evidence level
- linked project/session
- last updated/used markers
- stale/contradicted/invalidated flags
- correction path
- export/deletion/revocation relevance

Controls allowed in requirements only:
- approve
- reject
- confirm
- mark provisional
- mark stale
- mark contradicted
- invalidate
- archive/deprecate
- require source/evidence
- block promotion

## 10. First tool lanes/contracts requirements

Each lane contract should show:
- lane_id
- action_class
- approval status
- execution status
- risk level
- blocked reason
- denied-authority flags
- external/destructive/third-party/runtime/public-export request flags
- operator visibility flag
- user-visible status phrase
- failure count
- rollback/deprecation status
- audit note

The dashboard must distinguish:
- draft vs sent/exported
- plan vs executed
- proposal vs confirmed memory/project update
- internal report vs export/public report
- support record vs external contact

## 11. Support/escalation requirements

Each support/escalation item should show:
- support/escalation id
- reason
- owner/user/project scope
- status
- last safe step
- personal-data inclusion flag
- user approval status if personal data is included
- operator owner
- blocked state summary
- closure/reopen/de-escalation history
- audit trail link

## 12. Audit trail requirements

Audit entries should show:
- who or what initiated it
- timestamp/sequence marker
- affected user/project/session
- scope
- old state
- new state
- reason
- approval/denial
- rollback availability
- related artifact/report/contract
- operator note

Requirements:
- no hidden user-affecting state changes
- no silent approval reuse
- no audit deletion in this requirements lane
- audit export/delete policies require separate boundary review

## 13. Rollback/deprecation dashboard requirements

The rollback/deprecation area should show:
- rollback availability
- rollback target
- deprecation status
- archived/deprecated items
- failed/incomplete artifacts/reports
- invalidated memory/project entries
- lane freeze/revert status
- last safe state

Controls allowed in requirements only:
- mark rollback requested
- mark deprecated
- freeze lane/action
- archive item
- require implementation review

## 14. Validation/release status requirements

The validation/release area should show:
- latest validation status
- release-gate status
- release-check status
- protected-file status
- allowed file scope
- exact-file allowlist notes
- test count/summary
- static/no-side-effect check result
- unresolved validation gaps

## 15. Incident/risk flag requirements

The dashboard should flag:
- approval bypass attempt
- external action request
- destructive action request
- runtime activation request
- hidden memory/project mutation request
- cross-user leakage risk
- stale/contradicted active state
- repeated failure
- missing audit record
- release-gate broad allowance
- public-readiness claim drift
- autonomy/consciousness claim drift

## 16. User-facing vs operator-facing separation

Requirements for separation:
- define what the user may see
- define what the operator may see
- ensure user-affecting state is not hidden from the user
- keep sensitive operational notes operator-only when appropriate
- avoid secret personalization
- avoid leaking cross-user/admin data

## 17. Permissions and access requirements

Requirements only:
- a role/scoped access model will be needed later
- operator access must be logged
- cross-user views must be governed
- raw private data should not be shown by default
- least-privilege access is required
- separation between owner/operator/support roles may be needed later
- no access implementation in this lane

## 18. Initial rollout requirements

For initial controlled rollout:
- the dashboard can be report-like and internal only
- show pending approvals, blocked actions, project/memory state, first-lane contracts, support/escalation, and validation status
- no live control required at first
- no broad multi-user search at first
- no raw private-data views by default
- manual operator review is acceptable

## 19. Future scaling requirements

Later scaling may add:
- filtering and search
- alerts
- audit exports
- user/project isolation
- role-based access
- dashboard pagination
- incident/risk grouping
- approval batching only with strict scope
- integration status panels
- export/deletion/revocation surfaces after separate boundaries

## 20. Relationship to prior designs

This requirements document builds on:
- Operator Observability and Control
- First Tool Lanes Contracts Metadata Only
- First Tool Lanes Implementation Plan
- Project State Model
- Memory State Model
- Agentic Tool Use Boundary
- State and Continuity MVP
- Product Shell Minimum

## 21. Inclusion/exclusion

Included:
- dashboard requirements only
- operator-visible fields
- user/operator separation
- approval and blocked-state visibility
- project/memory/contract/support/audit/validation requirements
- initial rollout and scaling requirements

Excluded:
- UI implementation
- backend/API implementation
- storage/database implementation
- runtime permission implementation
- live dashboard
- raw private-data dumping
- silent admin override
- autonomous operator replacement
- public product readiness

## 22. Failure modes

The requirements should prevent or surface these failure modes:
- dashboard hides pending approval
- blocked action not visible
- stale or contradicted state shown as active
- raw private data overexposed
- cross-user leakage
- hidden admin override
- approval reused too broadly
- audit incomplete
- rollback unavailable but assumed
- first-lane contract shows allowed when blocked
- public-readiness claim drift
- operator dashboard becomes a hidden personalization engine

## 23. Validation criteria for future implementation

Future implementation should satisfy:
- every dashboard item has owner, scope, status, and source
- every approval has status and required approver
- every blocked action has a reason
- every first-lane contract shows denied-authority status
- every user-affecting state change is auditable
- protected-file and release status are visible
- stale and contradicted memory/project states are visible
- no raw private data by default
- no cross-user leakage
- no hidden admin override
- no live implementation without separate review

## 24. Future lanes

Future lanes to carry forward:
- `REVIEW_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`
- `DESIGN_WESLR_MEMORY_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_EXPORT_DELETION_REVOCATION_BOUNDARY_V1`
- `IMPLEMENT_WESLR_OPERATOR_DASHBOARD_METADATA_REPORT_V1`
- `DESIGN_WESLR_ROLE_SCOPED_OPERATOR_ACCESS_BOUNDARY_V1`

Carry forward:
- `REVIEW_WESLR_PRODUCT_SHELL_MINIMUM_V1`
- `REVIEW_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`

## 25. Validation results

- `git diff --check`: passed
- `git status --short`: showed the new requirements doc staged and the exact-file release-gate edit staged; remaining untracked docs/tests are pre-existing workspace artifacts
- `git diff --stat`: 1 file changed in the staged diff at validation time for the release-gate edit
- `python3 weslr/tests/release_gate_v1.py`: passed after the exact-file allowlist update
- `bash scripts/weslr_release_check.sh`: passed after the exact-file allowlist update

## 26. Protected-file status

Unchanged:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## 27. Safety/boundary confirmation

- requirements-only document
- no UI implementation
- no backend implementation
- no runtime wiring
- no storage/database implementation
- no project-state migration
- no memory migration
- no `.weslr` reads or writes
- no hidden project state claim
- no hidden/perfect memory claim
- no perfect continuity claim
- no consciousness/self-awareness/aliveness claim
- no autonomous self-modification
- no hidden behavior tuning
- no behavior-pack promotion
- no OCC context alignment

## 28. Release-gate allowance note, if any

An exact-file release-gate allowance was required for `docs/WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1.md` because the requirements doc was outside the default allowed path scope.

## 29. Artifact-fidelity final pass result

Pass after final verification.

## 30. Commit hash

`c12c2da00e77455f3913a3b7181e929f6ee25b23`

## 31. Final judgment

`weslr_operator_dashboard_requirements_design_ready_for_review`

## 32. Recommended next lane

`REVIEW_WESLR_OPERATOR_DASHBOARD_REQUIREMENTS_V1`
