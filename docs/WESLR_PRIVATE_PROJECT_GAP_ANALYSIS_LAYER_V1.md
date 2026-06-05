# WESLR Private Project Gap Analysis Layer V1

## Executive summary
WESLR needs a private, governed project-gap analysis layer that can review a project’s missing pieces, risks, contradictions, and weak evidence without exposing internal mechanisms to users.

This layer supports:
- surface project review for ordinary “what is missing?” questions
- deeper project analysis only after explicit user approval
- operator review for privacy-sensitive or cross-user/system-wide cases

User-visible output must stay mechanism-neutral. It must not expose private engine names, hidden prompts, internal scoring labels, or claims of certainty. No runtime implementation is included in this lane.

## Purpose
The layer is for controlled gap analysis that can identify:
- missing project fields
- contradictions
- risks
- blocked assumptions
- weak evidence
- missing decisions
- missing next steps
- missing constraints
- tool/action approval needs
- privacy-sensitive areas

The goal is to improve project quality without pretending certainty.

## Non-goals
This lane explicitly does not include:
- implementation
- runtime wiring
- hidden engine exposure
- final answer generation
- automatic project mutation
- automatic memory mutation
- external action
- tool execution
- scoring/certification claims
- public explanation of private mechanisms
- autonomous self-improvement

## User-visible language boundary
Allowed phrases:
- “surface project review”
- “project gap review”
- “missing-parts review”
- “project risk review”
- “deeper project analysis”
- “I can review this more deeply if you approve”
- “I found these likely gaps”
- “I’m not treating this as certainty”

Forbidden user-visible phrases:
- `Unknown Engine`
- private engine names
- hidden internal mechanism names
- hidden prompt references
- internal scoring labels
- private friction mechanism names
- claims that WESLR used secret reasoning
- claims of certainty where only gap analysis exists

## Analysis levels
### surface_gap_review
- default for ordinary “what is missing?” questions
- uses available project metadata only
- no deep inspection
- no private details exposed
- outputs likely gaps, risks, missing fields, and clarification questions

### deeper_gap_analysis
- requires explicit user approval
- may inspect more project structure and linked metadata
- still no private mechanism disclosure
- outputs a structured project gap report, risks, missing decisions, missing constraints, and suggested next safe steps

### operator_review_required
- used for privacy-sensitive, cross-user, system-wide, legal/high-stakes, or external-action-adjacent cases
- no automatic analysis expansion

## Consent and approval model
- surface review is allowed for ordinary project-owned metadata
- deeper analysis requires user confirmation
- privacy-sensitive analysis requires explicit confirmation
- cross-user/system-wide analysis requires operator review
- external action/tool execution remains blocked or separate lane
- consent is scoped and not permanent
- users can decline deeper analysis
- declined deeper analysis still allows a limited surface summary

## Inputs
### Allowed input metadata
- current project-state packet
- project-start chat-flow packet
- memory-state proposals/confirmed items
- state/continuity packet
- first-tool-lane contract candidates
- operator dashboard metadata report
- user-provided current project description
- user-approved linked artifact metadata

### Blocked inputs
- raw private data by default
- cross-user data
- hidden prompts
- protected answer keys
- private engine internals
- unapproved external data
- `.weslr` runtime/private state
- live account data
- unapproved files

## Output model
### Surface output should include
- likely missing fields
- unclear assumptions
- risks
- contradictions
- weak evidence
- blocked items
- suggested questions
- next safe step
- whether deeper analysis is available

### Deeper output should include
- structured gap report
- severity/priority labels as qualitative labels only
- evidence/source references when available
- missing decisions
- missing constraints
- missing approvals
- suggested next safe steps
- limitations
- no certainty overclaim

## Internal metadata model
Candidate fields:
- `analysis_id`
- `analysis_level`
- `project_id`
- `owner_user_scope`
- `tenant_account_scope`
- `source_scope`
- `consent_status`
- `approval_status`
- `privacy_sensitivity`
- `input_metadata_refs`
- `gap_categories`
- `risk_flags`
- `missing_fields`
- `contradictions`
- `weak_evidence_items`
- `blocked_items`
- `suggested_questions`
- `safe_next_steps`
- `operator_visible_summary`
- `user_visible_summary`
- `limitations`
- `denied_authority`

## Gap categories
- `missing_goal`
- `unclear_scope`
- `missing_constraints`
- `missing_success_criteria`
- `missing_inputs`
- `missing_output_definition`
- `missing_deadline_or_priority`
- `missing_owner_decision`
- `missing_evidence`
- `weak_assumption`
- `contradiction`
- `stale_context`
- `privacy_sensitive_gap`
- `missing_approval`
- `tool_action_boundary`
- `external_action_boundary`
- `project_state_gap`
- `memory_state_gap`
- `support_escalation_gap`
- `rollout_gap`

## Denied-authority model
Denied authority must include:
- `runtime_wiring_authority`
- `chat_responder_authority`
- `final_answer_generation_authority`
- `storage_database_authority`
- `weslr_io_authority`
- `project_state_mutation_authority`
- `memory_mutation_authority`
- `tool_execution_authority`
- `external_action_authority`
- `hidden_memory_authority`
- `hidden_project_state_authority`
- `private_mechanism_disclosure_authority`
- `cross_user_leakage_authority`
- `public_product_readiness_authority`

## Behavior rules
- Surface review may identify likely gaps from provided metadata.
- Surface review must not pretend certainty.
- Surface review must not mutate project or memory state.
- Deeper analysis requires explicit user approval.
- Deeper analysis must remain bounded to the approved project scope.
- Privacy-sensitive deeper analysis requires confirmation.
- Cross-user/system analysis requires operator review.
- Tool/external action suggestions become approval-gated candidates only.
- User-visible output must not expose private mechanism names.
- Internal metadata may preserve audit/reasoning boundary labels.
- Findings must include limitations.
- Missing evidence must be marked as missing evidence, not invented.
- Contradictions must be surfaced as contradictions.
- Stale project/memory state must be surfaced.
- No hidden memory.
- No fake continuity.
- No automatic behavior update.

## Relationship to existing helpers
- **Project Start Chat Flow Metadata**: upstream intake and intent classification; this layer consumes its candidate metadata and approvals.
- **Project State Model Helpers**: source for project-state candidate structure, missing fields, and state boundaries.
- **Memory State Model Helpers**: source for memory proposals/confirmed items and memory-boundary checks.
- **State and Continuity MVP Helpers**: source for continuity/staleness/contradiction metadata.
- **First Tool Lanes Contracts**: source for approval-gated tool-lane candidates, never executed actions.
- **Operator Dashboard Metadata Report**: source for operator-facing visibility, escalation cues, and review context.
- **Agentic Tool Use Boundary**: source for execution boundaries and blocked tool/action behavior.

## Failure modes
- private mechanism leaked to user
- surface review pretends deep analysis
- deeper analysis happens without approval
- project state is silently mutated
- memory is silently updated
- tool action is executed
- stale or contradicted state treated as active
- missing evidence invented
- privacy-sensitive context analyzed without consent
- cross-user leakage
- qualitative risk label treated as score/certification
- user believes WESLR is certain when it is only surfacing gaps

## Validation criteria for future implementation
- no private mechanism names in user-visible output
- no `Unknown Engine` in user-visible output
- surface/deeper distinction enforced
- deeper analysis requires approval metadata
- privacy-sensitive deeper analysis requires confirmation
- no runtime/persistence/tool execution
- no project/memory mutation
- blocked/cross-user states fail closed
- findings include limitations
- missing evidence not invented
- qualitative labels only
- denied-authority fields remain false/blocked

## Future lanes
- `REVIEW_WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_LAYER_V1`
- `IMPLEMENT_WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_METADATA_HELPERS_V1`
- `REVIEW_WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_METADATA_HELPERS_V1`
- `DESIGN_WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_WORKSPACE_UI_UX_ARCHITECTURE_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `a3a7a3e9e5517345c774a5ca6441e4142e0cdfa9`

3. Target design lane
- `DESIGN_WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_LAYER_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. OCC workspace root, branch, and verified HEAD
- Root: `/data/data/com.termux/files/home/.openclaw/workspace`
- Branch: `public-demo-experience-ui-v1`
- Verified HEAD: `53949e6f95a14d1e402c6d576a4005b9dcfa6501`

6. Files changed
- `docs/WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_LAYER_V1.md`
- `weslr/tests/release_gate_v1.py`

7. Design summary
- Private, governed gap-analysis layer.
- Surface review first, deeper analysis only with explicit approval.
- Mechanism-neutral user-visible language.
- Strict no-runtime, no-mutation, no-execution boundary.

8. Validation results
- `git diff --check`: PASS
- `git status --short`: reviewed for staged scope
- `git diff --stat`: reviewed for staged scope
- `python3 weslr/tests/release_gate_v1.py`: PASS
- `bash scripts/weslr_release_check.sh`: PASS

9. Protected-file status
- Verified unchanged: `weslr/chat_responder.py`, `weslr/main.py`, `main.py`, `dialogue.py`, `chat_ui.py`

10. Release-gate allowance note
- Exact-file allowlist entry added for `docs/WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_LAYER_V1.md`.

11. Artifact-fidelity final pass result
- PASS

12. Blocking gaps
- None

13. Non-blocking gaps
- None

14. Final judgment
- `weslr_private_project_gap_analysis_layer_design_ready_for_review`

15. Recommended next lane
- `REVIEW_WESLR_PRIVATE_PROJECT_GAP_ANALYSIS_LAYER_V1`
