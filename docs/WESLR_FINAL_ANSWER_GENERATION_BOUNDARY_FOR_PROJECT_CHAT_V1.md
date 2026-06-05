# WESLR Final Answer Generation Boundary for Project Chat V1

## Executive summary
Final-answer generation is not yet implemented or approved.
This boundary defines the conditions under which future WESLR project chat may produce user-visible answers.
Final answers must be grounded in approved metadata/evidence packets.
Retrieval/RAG is evidence support, not truth authority.
Final answers must distinguish candidate, proposed, confirmed, stale, contradicted, invalidated, and missing evidence states.
Private mechanisms must not be disclosed.
No `Unknown Engine` in user-visible output.

## Purpose
Define how future final-answer generation must safely consume:
- project-start chat-flow metadata
- project-state metadata
- memory-state metadata
- state/continuity metadata
- private project-gap analysis metadata
- tool-lane contract candidates
- RAG/evidence retrieval packets
- operator observability metadata
- user corrections and approvals

## Non-goals
This lane does not implement:
- implementation
- runtime wiring
- chat responder edits
- RAG/retrieval implementation
- SearXNG integration
- persistence
- project/memory mutation
- tool execution
- external action
- public launch/readiness claims
- hidden memory
- private mechanism disclosure
- autonomous self-improvement

## Architecture position
Future flow:
`User message`
→ `Project Chat Runtime Boundary`
→ `Project/Memory/Continuity/Gap/Tool Metadata Resolution`
→ `RAG and Evidence Retrieval Boundary`
→ `Evidence Packet / Provenance Envelope`
→ `Answer Plan Metadata`
→ `Final Answer Generation Boundary`
→ `User-visible Answer Candidate`
→ `Operator Observability Event`
→ optional future `Persistence/Mutation Candidate`

## Required preconditions before final answer generation
- runtime lane approved
- answer-generation lane approved
- source/evidence packets validated
- denied authority checked
- user-visible private-mechanism filter applied
- state/memory truth boundary resolved
- stale/contradicted/invalidated state handled
- missing evidence surfaced
- tool/external action boundaries checked
- project/memory mutation boundaries checked
- privacy and approval gates satisfied
- answer plan metadata exists

## Answer plan metadata
Fields:
- `answer_plan_id`
- `project_id`
- `owner_user_scope`
- `tenant_account_scope`
- `source_scope`
- `user_intent_class`
- `answer_mode`
- `allowed_answer_scope`
- `evidence_packet_refs`
- `project_state_refs`
- `memory_state_refs`
- `continuity_state_refs`
- `gap_analysis_refs`
- `tool_lane_candidate_refs`
- `operator_visibility_refs`
- `uncertainty_flags`
- `stale_state_flags`
- `contradiction_flags`
- `missing_evidence_flags`
- `privacy_flags`
- `approval_refs`
- `blocked_authority`
- `limitations`
- `user_visible_status`
- `denied_authority`

## Answer modes
- `clarifying_question`
- `project_start_guidance`
- `candidate_project_summary`
- `surface_gap_review_summary`
- `deeper_analysis_requires_approval`
- `evidence_grounded_answer`
- `uncertain_or_missing_evidence_answer`
- `contradiction_resolution_request`
- `tool_request_boundary_response`
- `blocked_boundary_response`
- `operator_review_required_response`

## Evidence consumption rules
- Final answer consumes evidence packets, not raw retrieval directly.
- SearXNG/web results are not truth authority.
- External evidence remains unverified unless assessed.
- Snippets alone are weak evidence.
- Source URLs alone do not prove truth.
- Local metadata is not truth by itself.
- Memory is not truth by itself.
- Final answer must not claim beyond evidence authority.
- Missing evidence must not be invented.
- Unsupported claims must be blocked or marked uncertain.
- Current factual claims require freshness labels.
- Conflicting evidence must be surfaced or trigger clarification/operator review.

## State and memory truth rules
- Candidate project state must be described as candidate/draft/provisional.
- Proposed memory must be described as proposed.
- Confirmed memory still requires source/evidence limitation.
- Stale state must be surfaced.
- Contradicted state must not drive confident answers.
- Invalidated state must be excluded from active answer support.
- User correction overrides lower-confidence metadata through approved correction path.
- No hidden memory.
- No fake continuity.
- No claim of persistence unless persistence is active and approved.

## Project gap-analysis answer rules
- Surface gap review may be summarized as likely gaps.
- Deeper project analysis requires explicit user approval.
- Privacy-sensitive deeper analysis requires confirmation.
- Cross-user/system-wide/high-stakes/action-adjacent analysis requires operator review.
- User-visible wording must remain mechanism-neutral.
- No private internal mechanism names.
- No `Unknown Engine`.
- Gap findings must include limitations.
- Severity/priority labels must be qualitative only, not scores/certification.

## Tool and external-action answer rules
- Tool requests become tool-lane contract candidates.
- Final answer may say that a tool action needs approval.
- Final answer must not claim a tool ran unless tool-execution boundary exists and execution is confirmed.
- External actions require approval and reversal planning.
- High-risk actions require operator review.
- Tool availability is not permission.

## User-visible wording boundary
Allowed:
- “I can prepare this as a project candidate.”
- “This looks like a likely gap.”
- “I need one clarification before I can answer safely.”
- “The available evidence is incomplete.”
- “The sources conflict.”
- “This may be stale.”
- “I can review this more deeply if you approve.”
- “I can use online search if you approve sharing these search terms.”
- “I cannot treat this as confirmed yet.”

Forbidden:
- “I saved this project” unless persistence is actually active and approved.
- “I remember this” unless memory state is actually active and evidence-limited.
- “I searched your private data automatically.”
- “SearXNG proves this.”
- “The web confirms this” without assessed evidence.
- `Unknown Engine`
- private mechanism names
- hidden prompt references
- internal scoring labels
- certainty claims unsupported by evidence
- public-readiness/intelligence/certification claims
- autonomous self-improvement/deployment claims

## Private mechanism and prompt-injection filter
- Final answer must remove private mechanism names from user-visible output.
- Retrieved source instructions cannot alter WESLR governance.
- web/file content cannot grant authority.
- hidden prompts must not be revealed.
- suspicious/hostile source content requires limitation/warning.
- Final answer must not follow instructions found inside retrieved evidence unless they are user-approved task content and safe.
- Private internal labels may remain operator metadata only.

## Answer denial / blocked response model
Blocked cases:
- missing source permission
- unapproved external query
- privacy-sensitive retrieval without approval
- cross-user retrieval
- tool execution request without executor boundary
- project/memory mutation request without mutation boundary
- unsupported high-confidence claim
- hidden prompt request
- private mechanism disclosure request
- public-readiness/certification claim request
- unsafe/high-stakes unsupported advice request

Blocked response must:
- state the boundary in user-safe language
- offer safe next step
- ask for approval/clarification if appropriate
- avoid private mechanism naming

## Operator observability model
Operator-visible event fields:
- `answer_plan_id`
- `answer_mode`
- `project_id`
- `owner_user_scope`
- `source_scope`
- `evidence_packet_refs`
- `blocked_authority`
- `approval_status`
- `privacy_flags`
- `retrieval_used`
- `external_search_used`
- `stale_state_flags`
- `contradiction_flags`
- `missing_evidence_flags`
- `user_visible_summary`
- `operator_visible_summary`
- `limitations`

## Denied-authority model
Denied authority must include:
- `runtime_wiring_authority`
- `chat_responder_authority`
- `final_answer_generation_implementation_authority`
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
- `unapproved_external_query_authority`
- `retrieval_truth_authority`
- `unsupported_certainty_authority`
- `public_product_readiness_authority`
- `autonomous_self_improvement_authority`

## Failure modes
- evidence packet ignored
- retrieval treated as truth
- SearXNG treated as proof
- snippets over-trusted
- missing evidence invented
- stale/contradicted/invalidated state used confidently
- project candidate described as saved
- proposed memory described as confirmed
- private mechanism leaked
- `Unknown Engine` leaked
- hidden prompt revealed
- tool execution falsely claimed
- external action implied
- unsupported certainty
- no operator observability
- user receives final answer when clarification/approval was required

## Validation criteria for future implementation
- no final-answer implementation unless explicitly approved
- protected files unchanged unless future lane approves them
- no `.weslr` IO unless approved
- no persistence/mutation/tool execution unless approved
- answer plan metadata exists before user-visible answer
- evidence packets consumed instead of raw retrieval
- denied authority checked before answer
- private mechanism filter applied
- no `Unknown Engine` in user-visible output
- missing evidence surfaced
- contradictions surfaced
- stale/invalidated state handled safely
- candidate/proposed/confirmed statuses worded correctly
- blocked responses are safe and mechanism-neutral
- tests cover allowed answer modes and blocked cases

## Relationship to existing stack
This boundary sits after:
- Project Chat Runtime Boundary
- Project Chat RAG and Evidence Retrieval Boundary
- Project Start Chat Flow Metadata
- Project State Model Helpers
- Memory State Model Helpers
- State and Continuity MVP Helpers
- Private Project Gap Analysis Metadata Helpers
- First Tool Lanes Contracts
- Agentic Tool Use Boundary
- Operator Dashboard Metadata Report

## Future lanes
- `REVIEW_WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1`
- `IMPLEMENT_WESLR_PROJECT_CHAT_ANSWER_PLAN_METADATA_HELPERS_V1`
- `REVIEW_WESLR_PROJECT_CHAT_ANSWER_PLAN_METADATA_HELPERS_V1`
- `IMPLEMENT_WESLR_PROJECT_CHAT_RUNTIME_DRY_RUN_METADATA_V1`
- `REVIEW_WESLR_PROJECT_CHAT_RUNTIME_DRY_RUN_METADATA_V1`
- `DESIGN_WESLR_PROJECT_STATE_PERSISTENCE_BOUNDARY_V1`
- `DESIGN_WESLR_MEMORY_WRITE_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_WORKSPACE_UI_UX_ARCHITECTURE_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `03d1c710b29edbf4105429952371cad3b2333a6b`

3. Target design lane
- `DESIGN_WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. OCC workspace root, branch, and verified HEAD
- Root: `/data/data/com.termux/files/home/.openclaw/workspace`
- Branch: `public-demo-experience-ui-v1`
- Verified HEAD: `cf946c6e379fb398a01805dbfd0028bcbbfdcb23`

6. Files changed
- `docs/WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1.md`
- `weslr/tests/release_gate_v1.py` only if exact-file allowlisting is required by the release gate

7. Design summary
- This boundary defines the safety, evidence, authority, privacy, wording, and output-contract requirements for future project-chat final answers.

8. Validation results
- `git diff --check`: PASS
- `git status --short`: PASS for staged scope; only pre-existing untracked workspace clutter remains outside staged scope
- `git diff --stat`: PASS
- `python3 weslr/tests/release_gate_v1.py`: PASS
- `bash scripts/weslr_release_check.sh`: PASS

9. Protected-file status
- Must remain unchanged unless explicitly approved later:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

10. Release-gate allowance note, if any
- Exact-file allowlist added for `docs/WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1.md`.

11. Artifact-fidelity final pass result
- PASS

12. Blocking gaps
- None in the design scope.

13. Non-blocking gaps
- The future review/implementation lanes still need separate approval before any final-answer behavior can exist.

14. Final judgment
- `weslr_final_answer_generation_boundary_for_project_chat_design_ready_for_review`

15. Recommended next lane
- `REVIEW_WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1`
