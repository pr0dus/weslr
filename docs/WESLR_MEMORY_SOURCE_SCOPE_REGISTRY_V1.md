# WESLR Memory Source Scope Registry V1

## SECTION 1 — Executive doctrine

WESLR memory retrieval must be source-scoped before it is content-scoped.

A temporal retrieval plan may say: “Search yesterday’s memory.”

But WESLR must first know:
- which memory source is allowed
- whether that source exists
- whether the source contains summaries or raw logs
- whether access requires owner authority
- whether retrieval would cross project, session, or user boundaries
- whether only metadata may be used
- whether retrieval must be blocked

The Memory Source Scope Registry is the authority map before retrieval.

## SECTION 2 — Current capability baseline

Observed baseline:
- `weslr/time_anchor_resolver.py` resolves time phrases into anchor packets.
- `weslr/temporal_memory_retrieval_plan.py` creates retrieval plans.
- Neither helper reads memory or grants access.
- The next layer must decide source availability and authority.

## SECTION 3 — Registry position in pipeline

Planned pipeline:
1. owner utterance
2. time anchor resolver
3. temporal memory retrieval plan
4. memory source scope registry
5. source authorization decision
6. future safe memory retrieval executor
7. result ranking
8. answer formation
9. friction capture

This design covers only:
- source registry
- source scope policy
- authority matrix
- blocked/allowed source decisions

## SECTION 4 — Future helper design

Recommended future helper:
`weslr/memory_source_scope_registry.py`

Future public APIs:
- `build_memory_source_scope_record_v1(...)`
- `build_memory_source_scope_registry_v1(...)`
- `resolve_memory_source_scope_v1(retrieval_plan, registry=None, owner_authority=None)`
- `validate_memory_source_scope_record_v1(record)`
- `validate_memory_source_scope_registry_v1(registry)`
- `summarize_memory_source_scope_registry_v1(registry)`
- `to_memory_source_scope_json_safe_v1(value)`
- `build_initial_memory_source_scope_examples_v1()`

## SECTION 5 — Source classes

Source classes from the temporal retrieval plan:
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

Optional future classes:
- `artifact_manifest_metadata`
- `artifact_validation_report`
- `behavior_pack_registry`
- `friction_case_registry`
- `owner_approved_summary`
- `external_connector_reference`

## SECTION 6 — Source scope record fields

Future record fields:
- `source_scope_id`
- `source_class`
- `source_label`
- `description`
- `content_level`
- `authority_required`
- `default_access_decision`
- `raw_access_allowed`
- `summary_access_allowed`
- `metadata_access_allowed`
- `private_data_possible`
- `cross_user_allowed`
- `cross_project_allowed`
- `cross_session_allowed`
- `temporal_filter_supported`
- `semantic_filter_supported`
- `event_anchor_supported`
- `commit_anchor_supported`
- `owner_authority_required`
- `operator_authority_required`
- `runtime_authority_required`
- `retention_sensitivity`
- `privacy_risk`
- `public_claim_risk`
- `safe_result_format`
- `blocked_reason`
- `required_redactions`
- `safe_metadata`

## SECTION 7 — Allowed content levels

Define:
- `metadata_only`
- `summary_only`
- `redacted_summary`
- `owner_visible_content`
- `raw_log`
- `private_state`
- `unknown_content`

Rules:
- `metadata_only` is safest.
- `summary_only` may be used for memory continuity.
- `redacted_summary` is preferred when private content may exist.
- `raw_log` requires explicit authority.
- `private_state` requires stronger explicit authority.
- `unknown_content` defaults blocked or clarification-required.

## SECTION 8 — Default access decisions

Define:
- `allow_metadata_only`
- `allow_summary_only`
- `allow_redacted_summary`
- `requires_owner_authority`
- `requires_operator_authority`
- `blocked_by_default`
- `clarification_required`
- `unknown_blocked`

## SECTION 9 — Source class policies

### 9.1 `current_conversation`
- content level: owner-visible content / summary
- default: allow summary/metadata within current session
- raw full transcript: authority-required if persisted/exported
- cross-user: false
- temporal filter: yes
- session filter: yes

### 9.2 `prior_conversation_summary`
- content level: summary
- default: allow summary only if available and scoped to owner/project
- raw transcript: not allowed by default
- cross-user: false

### 9.3 `project_memory`
- content level: summary/metadata
- default: allow scoped project summary if owner/project scope matches
- cross-project: false by default unless owner asks

### 9.4 `repo_commit_metadata`
- content level: metadata
- default: allow metadata only
- no raw private memory
- supports commit/event anchors

### 9.5 `lane_report_metadata`
- content level: metadata/summary
- default: allow summary/metadata
- useful for “what came before/after lane X?”

### 9.6 `uploaded_file_reference`
- content level: reference/metadata unless user uploaded or authorized
- default: requires scope check
- raw file reading requires explicit file-source authority

### 9.7 `approved_memory_index`
- content level: summary/index metadata
- default: allow scoped summary/index only
- raw source requires separate authority

### 9.8 `runtime_session_log`
- content level: raw log/private possible
- default: blocked or requires owner/operator authority
- no raw dump by default

### 9.9 `.weslr_state`
- content level: private state
- default: blocked by default
- access requires explicit design and owner/operator authority
- never silently read

### 9.10 `unknown_source`
- default: `unknown_blocked` or `clarification_required`

## SECTION 10 — Authority matrix

Authority levels:
- `no_authority`
- `metadata_authority`
- `summary_authority`
- `redacted_summary_authority`
- `owner_content_authority`
- `raw_log_authority`
- `private_state_authority`
- `operator_runtime_authority`

Rules:
- Registry may recommend required authority.
- Registry does not grant authority.
- Authority must come from a separate approved caller/policy.
- Private state and raw logs are never default.

## SECTION 11 — Source resolution decision packet

Future packet fields:
- `source_resolution_id`
- `retrieval_plan_id`
- `candidate_sources`
- `allowed_sources`
- `blocked_sources`
- `requires_authority_sources`
- `selected_source_priority`
- `effective_access_decision`
- `authority_required`
- `authority_missing`
- `clarification_required`
- `clarification_question`
- `safe_result_format`
- `redaction_required`
- `raw_access_allowed`
- `summary_access_allowed`
- `metadata_access_allowed`
- `private_data_access_allowed`
- `memory_read_authority_granted`
- `source_access_granted`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## SECTION 12 — Retrieval plan mapping rules

Map retrieval modes to source behavior:

- `temporal_first`
  - prefer time-filterable summaries/index/project memory
  - avoid raw logs unless explicitly authorized

- `hybrid_temporal_semantic`
  - same as temporal-first plus semantic filtering
  - safe summary preferred

- `session_order_retrieval`
  - current conversation if current session
  - prior session summary if previous session
  - raw logs blocked by default

- `event_anchor_retrieval`
  - lane report metadata, repo commit metadata, project memory
  - no private state needed by default

- `blocked_no_source`
  - no source resolution attempted except blocked result

- `blocked_no_authority`
  - return authority-required decision only

## SECTION 13 — Scope boundaries

Required scopes:
- owner/user scope
- project scope
- session scope
- workspace scope
- source class scope
- time window scope
- event/commit scope

Rules:
- no cross-user retrieval
- no cross-project retrieval unless owner explicitly asks and authority permits
- no raw private dump
- no hidden prompt exposure
- no unrelated workspace retrieval
- no source class escalation
- no `.weslr` access by implication

## SECTION 14 — Redaction and safe result formats

Safe formats:
- `metadata_summary`
- `redacted_summary`
- `owner_visible_excerpt`
- `source_reference_only`
- `blocked_authority_required`
- `clarification_needed`

Default:
- metadata or summary first
- raw excerpts only with explicit authority and safe context

## SECTION 15 — Example decisions

1. “What did I say yesterday?”
- plan: `temporal_first`
- sources: `approved_memory_index`, `prior_conversation_summary`, `project_memory`
- decision: requires memory/source authority; summary preferred

2. “Earlier in this chat I said ISS.”
- plan: `session_order_retrieval`
- source: `current_conversation`
- decision: current session summary/visible context allowed if available

3. “Before file manifest builder, what came next?”
- plan: `event_anchor_retrieval`
- sources: `lane_report_metadata`, `repo_commit_metadata`, `project_memory`
- decision: metadata/summary allowed

4. “Read the raw runtime log from yesterday.”
- source: `runtime_session_log`
- decision: blocked/requires explicit owner/operator authority

5. “Check `.weslr` state from last week.”
- source: `.weslr_state`
- decision: blocked by default; private-state authority required

6. “Find uploaded file from yesterday.”
- source: `uploaded_file_reference`
- decision: file-source authority required before raw file read

## SECTION 16 — Relationship to artifact/code engine

Source registry should later apply to:
- artifact manifests
- validation reports
- generated scaffolds
- patch reports
- behavior packs
- friction cases

WESLR should retrieve project context safely before generating new artifacts.

## SECTION 17 — Relationship to provenance/tamper evidence

Artifact trust should not rely on watermarking alone.

Future source registry should support provenance source classes:
- artifact hash metadata
- validation reports
- commit/lane references
- owner approvals

Recommended future lane:
`DESIGN_WESLR_ARTIFACT_PROVENANCE_AND_TAMPER_EVIDENCE_BOUNDARY_V1`

## SECTION 18 — Safety boundaries

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

## SECTION 19 — Future implementation sequence

Recommend:
1. `IMPLEMENT_WESLR_MEMORY_SOURCE_SCOPE_REGISTRY_V1`
2. `DESIGN_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
3. `IMPLEMENT_WESLR_SAFE_MEMORY_RETRIEVAL_EXECUTOR_V1`
4. `DESIGN_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
5. `IMPLEMENT_WESLR_MEMORY_RETRIEVAL_RESULT_RANKER_V1`
6. integrate into future owner-chat route only after guarded review

## SECTION 20 — Boundaries

Confirm:
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

`memory_source_scope_registry_design_ready_for_implementation`
