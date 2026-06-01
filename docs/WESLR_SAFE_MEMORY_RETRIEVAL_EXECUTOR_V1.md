# WESLR Safe Memory Retrieval Executor V1

## 1. Executive doctrine

The safe memory retrieval executor is the first future layer that may eventually touch memory sources, but only after:
- time anchor resolution
- temporal retrieval planning
- source scope resolution
- authority check
- redaction boundary
- result constraints

Memory retrieval must not be a free search.

It must be:
- source-scoped
- time-scoped
- authority-scoped
- privacy-scoped
- project/session-scoped
- confidence-scored
- redacted by default

## 2. Current capability baseline

Implemented helpers:
- `weslr/time_anchor_resolver.py`
- `weslr/temporal_memory_retrieval_plan.py`
- `weslr/memory_source_scope_registry.py`

Boundary:
- none of these read memory
- none of these should be treated as retrieval executors
- this design preserves that boundary until implementation is separately approved

## 3. Executor position in pipeline

Future pipeline:

owner utterance
→ time anchor resolver
→ temporal retrieval plan
→ memory source scope registry
→ safe memory retrieval executor
→ retrieval result packet
→ result ranker
→ answer formation
→ friction capture

This design covers only the future executor rules and result packet shape.

## 4. Future helper design

Recommended future helper:
- `weslr/safe_memory_retrieval_executor.py`

Future public APIs:
- `build_safe_memory_retrieval_request_v1(...)`
- `execute_safe_memory_retrieval_v1(retrieval_plan, source_resolution, source_provider=None, authority_packet=None)`
- `validate_safe_memory_retrieval_request_v1(request)`
- `validate_safe_memory_retrieval_result_v1(result)`
- `summarize_safe_memory_retrieval_result_v1(result)`
- `to_safe_memory_retrieval_json_safe_v1(value)`
- `build_initial_safe_memory_retrieval_examples_v1()`

## 5. Retrieval request packet

Required fields:
- `retrieval_request_id`
- `retrieval_plan_id`
- `source_resolution_id`
- `allowed_sources`
- `blocked_sources`
- `requires_authority_sources`
- `selected_source_priority`
- `resolved_start`
- `resolved_end`
- `timezone`
- `retrieval_mode`
- `semantic_query_present`
- `semantic_query_summary`
- `authority_packet_id`
- `authority_level`
- `memory_read_authority_granted`
- `source_access_granted`
- `raw_log_access_allowed`
- `private_data_access_allowed`
- `redaction_required`
- `safe_result_format`
- `max_result_count`
- `max_excerpt_length`
- `allow_raw_transcript`
- `allow_hidden_prompt`
- `allow_cross_user`
- `allow_cross_project`
- `result_constraints`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 6. Retrieval result packet

Required fields:
- `retrieval_result_id`
- `retrieval_request_id`
- `retrieval_executed`
- `blocked`
- `blocked_reason`
- `source_results`
- `result_count`
- `partial_result`
- `expected_confidence`
- `actual_confidence`
- `source_classes_used`
- `source_classes_blocked`
- `time_window_used`
- `semantic_filter_used`
- `redaction_applied`
- `raw_content_included`
- `private_data_included`
- `hidden_prompt_included`
- `cross_user_content_included`
- `cross_project_content_included`
- `answer_safe_summary`
- `result_constraints`
- `failure_modes`
- `recommended_next_step`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 7. Source result item shape

Each source result item should include:
- `source_class`
- `source_id`
- `source_label`
- `source_timestamp`
- `source_time_window`
- `match_reason`
- `rank_hint`
- `confidence`
- `safe_summary`
- `safe_excerpt`
- `raw_content_omitted`
- `redactions`
- `source_reference`
- `authority_used`
- `private_data_possible`
- `safe_metadata`

## 8. Authority doctrine

The executor must not grant authority.

It may only execute retrieval if authority was already granted by approved policy or caller.

Default:
- no memory read authority
- no source access authority
- no raw log access
- no private data access
- no hidden prompt access
- no cross-user access
- no writes state
- no runtime mutation

If authority is missing:
- return a blocked result

## 9. Source provider boundary

The executor should not directly know how to read every source.

Possible future provider functions:
- `list_candidates(source_class, time_window, semantic_query)`
- `fetch_summary(source_reference)`
- `fetch_metadata(source_reference)`
- `fetch_redacted_excerpt(source_reference)`

Raw fetch functions require explicit authority and should be absent by default.

Provider boundary requirements:
- must support test doubles / fake providers first
- must not require direct `.weslr` reads in V1
- must keep source-specific access out of the executor core

## 10. Safe retrieval behavior by source class

1. `current_conversation`
- current visible context or supplied source provider only
- no hidden prompt
- no full transcript unless authorized

2. `prior_conversation_summary`
- summary only
- no raw transcript

3. `project_memory`
- scoped project summary / metadata only

4. `repo_commit_metadata`
- metadata only

5. `lane_report_metadata`
- summary / metadata only

6. `uploaded_file_reference`
- reference / metadata only unless file-read authority exists

7. `approved_memory_index`
- summary / index only

8. `runtime_session_log`
- blocked unless explicit raw_log / operator authority

9. `.weslr_state`
- blocked unless explicit private_state authority and separate approved design

10. `unknown_source`
- blocked

## 11. Redaction doctrine

Default result must be:
- metadata summary or redacted summary
- no raw private dump
- no hidden prompt
- no credentials / secrets
- no full transcript
- no cross-user content
- no private state

If excerpts are included:
- keep short
- owner-visible only
- include source class and confidence
- mark partial if incomplete

## 12. Temporal and semantic filtering

The executor should respect:
- `resolved_start`
- `resolved_end`
- `timezone`
- event anchor
- commit anchor
- semantic query summary

Rules:
- `temporal_first`: filter time first
- `hybrid`: filter time and semantic
- `session_order`: preserve session order
- `event_anchor`: before / after event
- blocked modes: no retrieval

## 13. Failure and blocked behavior

Blocked cases:
- no source available
- no authority
- source class blocked
- private state requested
- raw logs requested without authority
- hidden prompt requested
- source provider missing
- time anchor unresolved
- source scope ambiguous
- cross-user / cross-project boundary risk

Blocked result must be safe and explicit.

## 14. Confidence doctrine

Result confidence:
- `high`: exact time/source match and complete summary
- `medium`: time/source match but partial or semantic ambiguity
- `low`: vague or incomplete
- `blocked`: not executed
- `unresolved`: no valid anchor/source

Executor must not fabricate memory content.

## 15. Relationship to answer formation

The executor does not answer the user.

It returns a safe result packet.

Future answer formation layer decides:
- what to tell the user
- how much uncertainty to include
- whether to ask clarification
- whether to cite source class / time window
- whether to say memory unavailable

## 16. Relationship to friction learning

If retrieval fails or is wrong:
- capture friction case later
- classify failure:
  - bad time anchor
  - wrong source scope
  - missing authority
  - missing source
  - poor ranking
  - unsafe result boundary
  - incomplete answer
- feed replay / proposal loop only after approved capture policy

## 17. Example cases

1. “What did I say yesterday?”
- request: temporal-first
- allowed sources: approved memory index / prior summaries / project memory
- authority missing by default
- result: blocked until authority/source available

2. “Earlier in this chat I said ISS.”
- request: session-order
- source: current conversation if supplied by caller
- result: safe summary, no hidden prompt

3. “Before file manifest builder, what came next?”
- source: lane report metadata / repo commit metadata
- result: metadata summary only

4. “Read raw runtime logs from yesterday.”
- result: blocked, raw_log authority required

5. “Check `.weslr` state.”
- result: blocked, private_state authority required

6. “Find uploaded file from yesterday.”
- result: source reference only unless file-read authority exists

## 18. Implementation strategy

Recommended implementation sequence:
1. implement request / result packet builders
2. implement validation only
3. implement fake source provider tests
4. implement metadata-only retrieval from supplied in-memory provider
5. keep real source access blocked
6. later design source-specific connectors

## 19. Safety boundaries

Forbid:
- raw private log dumping
- hidden prompt exposure
- cross-user retrieval
- unauthorized `.weslr` reads
- unauthorized runtime log reads
- automatic memory authority
- private data persistence
- public ISS wording
- AGI / consciousness / sentience / Turing / certification claims
- runtime mutation
- file writes
- model / provider / search calls

## 20. Future implementation lane

Recommended next implementation lane:
- `IMPLEMENT_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`

Initial implementation must use in-memory fake / source-provider input only.
No real `.weslr`, runtime log, file, or conversation store access.

## 21. Future follow-up lanes

Recommended follow-up lanes:
- `IMPLEMENT_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
- `DESIGN_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
- `IMPLEMENT_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
- `DESIGN_WESLR_MEMORY_ANSWER_FORMATION_BOUNDARY_V1`
- `DESIGN_WESLR_ARTIFACT_PROVENANCE_AND_TAMPER_EVIDENCE_BOUNDARY_V1`
- resume `IMPLEMENT_WESLR_CODE_SCAFFOLD_GENERATOR_V1` when owner decides

## 22. Boundaries

Confirm:
- design only
- no implementation
- no memory read
- no `.weslr` access
- no log read
- no raw transcript dump
- no runtime / chat route changes
- no model / provider / search / advisor calls
- no file writes except this design doc
- protected files untouched

## 23. Final judgment

`safe_memory_retrieval_executor_design_ready_for_fake_provider_implementation`

Validation:
- doc only
- `git diff --check`
- release gate / check if required by repo policy
- protected files untouched:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `dialogue.py`
  - `chat_ui.py`

Recommended next lane:
- `IMPLEMENT_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
