# WESLR Temporal Memory Retrieval Plan V1

## SECTION 1 — Executive doctrine

WESLR memory retrieval must become source-scoped and time-aware.

The time-anchor resolver identifies when the owner means things like:
- yesterday
- last week
- earlier in this chat
- before the last commit
- after a lane, report, or event

But the resolver does not retrieve memory.

Temporal Memory Retrieval Plan V1 defines the safe planning layer between:
`time anchor packet` → `actual memory retrieval`.

This layer decides:
- which source category is relevant
- whether retrieval is temporal-first, semantic-first, hybrid, or event-anchor based
- whether memory read authority is needed
- what source scope is allowed
- what confidence can be expected
- whether clarification is required
- how to avoid fabricating unavailable memory

## SECTION 2 — Current capability baseline

Observed baseline:
- `weslr/time_anchor_resolver.py` exists
- it resolves temporal phrases into packets
- it does not read memory
- it does not grant memory read authority
- it does not access `.weslr`
- it does not call runtime/chat/provider/search/advisor surfaces

Missing piece:
WESLR needs a memory retrieval plan helper before actual retrieval.

## SECTION 3 — Temporal memory retrieval plan position

Planned pipeline:
1. owner utterance received
2. temporal phrase detected
3. time anchor resolved
4. retrieval plan built
5. source scope selected
6. authority checked
7. retrieval executed later by separate approved helper
8. retrieved records ranked
9. answer formed with confidence / uncertainty
10. friction captured if wrong or incomplete

This design covers steps 4–6 only.

## SECTION 4 — Future helper design

Recommended future helper:
`weslr/temporal_memory_retrieval_plan.py`

Future public APIs:
- `build_temporal_memory_retrieval_plan_v1(...)`
- `build_temporal_memory_retrieval_plan_from_anchor_v1(time_anchor_packet, semantic_query=None, available_sources=None)`
- `validate_temporal_memory_retrieval_plan_v1(plan)`
- `summarize_temporal_memory_retrieval_plan_v1(plan)`
- `to_temporal_memory_retrieval_plan_json_safe_v1(value)`
- `build_initial_temporal_memory_retrieval_plan_examples_v1()`

## SECTION 5 — Retrieval plan fields

Future plan fields:
- `retrieval_plan_id`
- `source_time_anchor_id`
- `original_phrase`
- `anchor_type`
- `resolved_start`
- `resolved_end`
- `timezone`
- `retrieval_mode`
- `semantic_query_present`
- `semantic_query_summary`
- `source_scope`
- `source_priority`
- `project_scope_hint`
- `session_scope_hint`
- `event_anchor`
- `commit_anchor`
- `candidate_source_classes`
- `excluded_source_classes`
- `authority_required`
- `memory_read_authority_granted`
- `source_access_granted`
- `raw_log_access_allowed`
- `private_data_access_allowed`
- `expected_confidence`
- `needs_clarification`
- `clarification_question`
- `ranking_strategy`
- `result_constraints`
- `answer_boundary`
- `failure_modes`
- `safe_metadata`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `iss_internal_reference_allowed`
- `learning_claimed`

## SECTION 6 — Retrieval modes

Future retrieval modes:
- `temporal_first`
- `semantic_first`
- `hybrid_temporal_semantic`
- `event_anchor_retrieval`
- `session_order_retrieval`
- `clarification_required`
- `blocked_no_authority`
- `blocked_no_source`

Rules:
- “What did I say yesterday?” → `temporal_first`
- “What did I say yesterday about WiFi sensing?” → `hybrid_temporal_semantic`
- “Earlier in this chat…” → `session_order_retrieval`
- “Before the file manifest builder…” → `event_anchor_retrieval`
- “Recently…” → low-confidence or clarification
- unavailable source → `blocked_no_source`
- no memory authority → `blocked_no_authority`

## SECTION 7 — Source scope classes

Future source classes:
- `current_conversation`
- `prior_conversation_summary`
- `project_memory`
- `repo_commit_metadata`
- `lane_report_metadata`
- `uploaded_file_reference`
- `approved_memory_index`
- `runtime_session_log`
- `.weslr_state`
- `unknown_source`

Boundary:
This plan may mention source classes but must not read them.

`.weslr_state`, runtime logs, raw private memory, and raw conversation logs require separate explicit authority.

## SECTION 8 — Source priority doctrine

For “earlier in this chat”:
1. `current_conversation`
2. current session summary if available
3. ask clarification if inaccessible

For “yesterday”:
1. approved memory index scoped by resolved day
2. prior conversation summaries within resolved window
3. project memory if project scope is present
4. ask clarification if unavailable

For “before last commit”:
1. repo commit metadata
2. lane report metadata
3. project memory
4. ask clarification if commit metadata is unavailable

For “what did we decide about X last week”:
1. time window
2. semantic filter X
3. project memory / lane reports
4. answer with uncertainty if partial

## SECTION 9 — Authority doctrine

Temporal retrieval planning does not grant access.

Plan should preserve:
- `memory_read_authority_granted`: false by default
- `source_access_granted`: false by default
- `raw_log_access_allowed`: false by default
- `private_data_access_allowed`: false by default
- `runtime_authority`: false
- `writes_state`: false
- `model_provider_used`: false
- `public_claim_allowed`: false
- `learning_claimed`: false

Future retrieval executor must separately receive authority.

## SECTION 10 — Clarification doctrine

Ask clarification when:
- time anchor is unresolved
- phrase is vague and many windows fit
- source scope is unknown
- requested source is unavailable
- query could refer to multiple projects
- retrieval would require unauthorized private/raw source

Do not ask clarification when:
- “yesterday” resolves to an exact local calendar window
- “earlier in this chat” clearly points to current conversation
- project-relative event is known from supplied metadata

## SECTION 11 — Confidence doctrine

Future confidence levels:
- `high`: exact time window + source available + clear query
- `medium`: window resolved but source partial or semantic ambiguity
- `low`: vague phrase or incomplete source
- `unresolved`: no valid anchor/source
- `blocked`: authority/source unavailable

WESLR must not fabricate memory content.
If retrieval is unavailable, the future answer must say so.

## SECTION 12 — Ranking strategy

Future ranking strategies:
- `time_window_exact`
- `time_window_then_semantic`
- `semantic_then_time_boost`
- `session_order_nearest`
- `event_anchor_before_after`
- `commit_order_before_after`
- `manual_owner_clarification`

## SECTION 13 — Result constraints

Future retrieval results should return:
- safe summary
- source date / window
- confidence
- whether the result is partial
- source class
- no raw private dump by default
- no hidden prompt
- no full transcript unless explicitly authorized
- no cross-user retrieval

## SECTION 14 — Relationship to WESLR project workflow

Temporal retrieval plan supports:
- “What did we do yesterday?”
- “What was the last lane?”
- “What came before file manifest builder?”
- “What did OCC report last time?”
- “When did we decide not to route chat?”
- “What did I say about ISS earlier?”
- “What was the current HEAD before this commit?”

Project memory needs event / commit / lane anchors, not only calendar time.

## SECTION 15 — Relationship to artifact/code engine

Temporal memory retrieval matters for artifact work because WESLR must remember:
- previous project brief
- previous architecture choice
- previous stack decision
- last file manifest
- last validation failure
- last owner approval
- last rollback decision
- last public-claim boundary

This prevents repeating mistakes and supports friction learning.

## SECTION 16 — Safety and privacy boundaries

Forbid:
- raw private log dumping
- hidden prompt exposure
- cross-user retrieval
- unauthorized `.weslr` reads
- unauthorized runtime session log reads
- automatic memory read authority
- private data persistence
- public ISS wording
- AGI / consciousness / sentience / Turing / certification claims
- runtime authority
- file writes
- model / provider / search calls

## SECTION 17 — Example cases

1. “What did I say yesterday?”
- input anchor: yesterday
- retrieval mode: `temporal_first`
- source classes: approved memory index / prior summaries
- authority: required, not granted
- confidence: high only if source available

2. “What did I say yesterday about WiFi sensing?”
- anchor: yesterday
- semantic query: WiFi sensing
- mode: `hybrid_temporal_semantic`

3. “Earlier in this chat I said ISS.”
- anchor: session-relative
- source: current_conversation
- mode: `session_order_retrieval`

4. “Before file manifest builder, what came next?”
- anchor: project-relative
- mode: `event_anchor_retrieval`
- source: lane reports / commit metadata

5. “Recently I mentioned something about watermarking.”
- anchor: vague temporal
- mode: `clarification_required` or low-confidence hybrid

6. “What did we decide last week about public wording?”
- anchor: last week
- semantic query: public wording
- source: project memory / lane reports

## SECTION 18 — Future implementation sequence

Recommended sequence:
1. `IMPLEMENT_WESLR_TEMPORAL_MEMORY_RETRIEVAL_PLAN_V1`
2. `DESIGN_WESLR_MEMORY_SOURCE_SCOPE_REGISTRY_V1`
3. `IMPLEMENT_WESLR_MEMORY_SOURCE_SCOPE_REGISTRY_V1`
4. `DESIGN_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
5. `IMPLEMENT_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
6. integrate into future owner-chat route only after guarded review

## SECTION 19 — Relationship to artifact provenance issue

Owner-observed external issue:
AI watermarking / detection can be attacked or bypassed.

Do not implement anything related to watermark removal or detector bypass.

Relevant WESLR lesson:
Memory and artifact trust should rely on provenance chains, source scopes, timestamps, hashes, lane / commit references, validation reports, and owner approvals — not a single watermark / detector signal.

Recommended separate future design lane:
`DESIGN_WESLR_ARTIFACT_PROVENANCE_AND_TAMPER_EVIDENCE_BOUNDARY_V1`

## SECTION 20 — Boundaries

Confirmed:
- design only
- no implementation
- no memory read
- no `.weslr` access
- no log read
- no raw transcript dump
- no runtime/chat route changes
- no model/provider/search/advisor calls
- no file writes except this design doc
- protected files untouched

## SECTION 21 — Final judgment

`temporal_memory_retrieval_plan_design_ready_for_implementation`
