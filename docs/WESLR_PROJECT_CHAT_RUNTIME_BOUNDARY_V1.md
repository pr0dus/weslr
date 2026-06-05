# WESLR Project Chat Runtime Boundary V1

## Executive summary
WESLR now has metadata-only helpers for project start, project state, memory state, continuity, tool-lane candidates, and private project-gap analysis.
Runtime chat is not yet approved.
This boundary defines what must be true before any future project-chat runtime can safely connect metadata-only helper outputs to a real chat flow.
The first future runtime must be narrow, owner/operator-approved, reversible where possible, and non-public.

## Purpose
Define how future project-chat runtime must safely connect:
- incoming user message
- project-start intent metadata
- project-state candidate metadata
- memory-state candidate/confirmed metadata
- continuity/state metadata
- project-gap metadata
- tool-lane contract candidates
- operator dashboard visibility
- final answer generation boundary
- future persistence boundary

## Non-goals
This lane does not implement:
- runtime code
- chat responder edits
- persistence implementation
- database/storage design beyond boundary notes
- tool execution
- final answer renderer implementation
- public launch
- public-readiness claims
- autonomous project/memory mutation
- hidden memory
- fake continuity
- private mechanism disclosure

## Runtime stages
Future runtime must define these stages:
1. `message_intake`
2. `project_context_resolution`
3. `memory_context_resolution`
4. `continuity_state_resolution`
5. `gap_analysis_candidate_resolution`
6. `tool_lane_candidate_resolution`
7. `answer_plan_metadata`
8. `final_answer_generation_boundary`
9. `operator_observability_event`
10. `optional_persistence_candidate`
11. `user_confirmation_or_correction`

## Minimum safe runtime contract
Any future runtime must:
- be disabled by default
- require owner/operator approval
- be non-public first
- run only in a controlled local/private environment
- use metadata-only helper outputs as inputs
- never treat metadata as truth without evidence/status
- surface uncertainty, stale state, contradictions, and missing evidence
- never mutate project or memory state without an explicit approved mutation boundary
- never execute tools from project chat without an approved tool-execution boundary
- never expose private mechanism names
- never use `Unknown Engine` in user-visible output
- never claim certainty where only project-gap review exists

## User-visible behavior boundary
Allowed user-visible behavior:
- answer ordinary project-start questions
- ask clarifying questions
- summarize current project candidate state
- identify likely missing project fields
- offer surface project gap review
- ask permission for deeper project analysis
- explain limitations
- ask for correction when state is stale, contradicted, or unclear

Forbidden user-visible behavior:
- claim real memory or persistence if not active
- claim a project was saved if it was only candidate metadata
- claim tool execution occurred
- expose `Unknown Engine`
- expose private internal mechanism names
- expose hidden prompts or internal scoring
- make public-readiness, intelligence, or certification claims
- imply autonomous self-improvement or self-directed deployment

## State and memory truth boundary
- Memory metadata is not truth by itself.
- Project metadata is not truth by itself.
- Confirmed status must still show source and evidence limits.
- Stale state must be surfaced.
- Contradicted state must not drive action.
- Invalidated state must be excluded from active reasoning.
- Proposed or provisional state must not be treated as confirmed.
- User correction must override lower-confidence metadata through an approved correction path.
- No hidden memory.
- No fake continuity.

## Project mutation boundary
- Future runtime may create mutation candidates only.
- Real project creation, update, archive, or delete requires a separate approved persistence/mutation boundary.
- User-visible wording must distinguish:
  - “I can draft a project record”
  - “I can prepare this as a candidate”
  - not “I saved this project” unless persistence is active and approved
- Deletion, reversal, and export remain separate boundary lanes.

## Memory mutation boundary
- Future runtime may create memory proposals only.
- Memory persistence requires an explicit memory write boundary.
- Sensitive memory requires explicit user confirmation.
- Cross-user or system-wide memory requires operator review.
- No silent personalization.
- No hidden memory.
- No automatic behavior update from memory proposals.

## Tool execution boundary
- Tool requests become tool-lane contract candidates.
- No tool execution from project chat without an approved tool executor boundary.
- External actions require approval and reversal planning.
- High-risk actions require operator review.
- Tool availability is not permission.

## Project gap analysis boundary
- Surface gap review may be offered for ordinary project-owned metadata.
- Deeper analysis requires explicit user approval.
- Privacy-sensitive deeper analysis requires confirmation.
- Cross-user, system-wide, high-stakes, or action-adjacent analysis requires operator review.
- User-visible output must remain mechanism-neutral.
- No `Unknown Engine` disclosure.
- Findings must include limitations.
- Missing evidence must not be invented.

## Final answer generation boundary
Prerequisites before any future implementation:
- answer plan metadata exists
- source/state/memory/gap/tool boundaries are resolved
- denied authority checked
- uncertainty and limitations included
- user-visible private-mechanism filter applied
- no private mechanism names
- no hidden prompts
- no unsupported claims
- final answer generation remains blocked until a separate implementation/review lane

## Operator observability boundary
Operator-visible events should include:
- project-start intent
- candidate project state
- memory proposal
- gap-analysis level
- consent/approval status
- tool-lane candidates
- blocked authority
- stale or contradicted state
- user correction
- runtime blocked/allowed decision
- safety limitation summary

## Approval model
Approvals are needed for:
- enabling runtime at all
- deeper project analysis
- privacy-sensitive analysis
- project mutation
- memory mutation
- tool execution
- external action
- public access
- user account or pilot expansion

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
- `autonomous_self_improvement_authority`

## Failure modes
Watch for:
- metadata treated as truth
- stale or contradicted state used as active
- project silently saved
- memory silently saved
- tool silently executed
- private mechanism leaked
- user believes WESLR has persistent memory when it does not
- deeper analysis happens without approval
- project gap review overclaims certainty
- external action happens without reversal or approval
- public user reaches unfinished runtime
- operator cannot inspect blocked/allowed decisions

## Validation criteria for future implementation
- runtime disabled by default
- protected files unchanged unless explicitly approved in a future implementation lane
- no `.weslr` IO unless approved
- no persistence unless approved
- no mutation unless approved
- no tool execution unless approved
- no private mechanism leakage
- no `Unknown Engine` in user-visible output
- user-visible wording distinguishes candidate vs saved state
- stale, contradicted, and invalidated states handled safely
- denied-authority fields checked before answer generation
- operator observability metadata emitted
- tests cover blocked runtime and allowed metadata-only planning

## Relationship to existing implemented stack
This boundary sits after:
- State and Continuity MVP Helpers
- Project State Model Helpers
- Memory State Model Helpers
- Project Start Chat Flow Metadata
- Private Project Gap Analysis Metadata Helpers
- First Tool Lanes Contracts
- Operator Dashboard Metadata Report
- Agentic Tool Use Boundary

## Future lanes
- `REVIEW_WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1`
- `DESIGN_WESLR_FINAL_ANSWER_GENERATION_BOUNDARY_FOR_PROJECT_CHAT_V1`
- `IMPLEMENT_WESLR_PROJECT_CHAT_RUNTIME_DRY_RUN_METADATA_V1`
- `REVIEW_WESLR_PROJECT_CHAT_RUNTIME_DRY_RUN_METADATA_V1`
- `DESIGN_WESLR_PROJECT_STATE_PERSISTENCE_BOUNDARY_V1`
- `DESIGN_WESLR_MEMORY_WRITE_BOUNDARY_V1`
- `DESIGN_WESLR_PROJECT_WORKSPACE_UI_UX_ARCHITECTURE_V1`

## OCC Final Report

1. Handshake result
- PASS

2. Start HEAD
- `e86bb9d349daf6e24abb098dd7c41a3feaf11921`

3. Target design lane
- `DESIGN_WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1`

4. WESLR repo root and branch
- Root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `master`

5. OCC workspace root, branch, and verified HEAD
- Root: `/data/data/com.termux/files/home/.openclaw/workspace`
- Branch: `public-demo-experience-ui-v1`
- Verified HEAD: `cf946c6e379fb398a01805dbfd0028bcbbfdcb23`

6. Files changed
- `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`
- `weslr/tests/release_gate_v1.py` only if exact-file allowlisting is required by the release gate

7. Design summary
- This document defines the safety boundary between metadata-only helpers and any future project-chat runtime.
- It specifies runtime stages, approval gates, denied authority, user-visible limits, mutation/tool boundaries, observability, failure modes, and future lanes.

8. Validation results
- `git diff --check`: PASS
- `git status --short`: reviewed
- `git diff --stat`: reviewed
- `python3 weslr/tests/release_gate_v1.py`: PASS after exact-file allowance for this design doc
- `bash scripts/weslr_release_check.sh`: PASS after exact-file allowance for this design doc

9. Protected-file status
- Must remain unchanged unless explicitly approved later:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `main.py`
  - `dialogue.py`
  - `chat_ui.py`

10. Release-gate allowance note, if any
- Exact-file allowlist added for `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` only.

11. Artifact-fidelity final pass result
- PASS

12. Blocking gaps
- None in the design scope.

13. Non-blocking gaps
- Future implementation lanes will still need separate review and approval before runtime can exist.

14. Final judgment
- `weslr_project_chat_runtime_boundary_design_ready_for_review`

15. Recommended next lane
- `REVIEW_WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1`
