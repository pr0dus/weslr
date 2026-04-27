# WESLR Bottleneck Discovery V1

---

## Batch 1 — dialogue.py, interpretation.py, weslr/chat_responder.py

Files Read

- dialogue.py
- interpretation.py
- weslr/chat_responder.py

Current Subsystems Observed

- Dialogue handling: message classification, reference phrase detection, artifact resolution cascade, context selection signals, boundary hints
- Interpretation: human turn classification, topic inference, intent mapping, stance detection, reply shape routing
- Chat responding: conversational formatting, greeting/help/status rendering, adaptive explanation sessions, decision rendering

Observed Breakpoints

- file/section: dialogue.py — `_resolve_active_artifact` — Resolution Cascade
  - symptom: Cascade lists "Level 1: timeline_resolution: active thread artifact for user" but timeline_resolution module is not imported or called at that point in the actual code; resolution falls through to registry fallback without trying thread-aware resolution
  - when it matters: When a user references an artifact across a session boundary via "improve this" or "explain this"

- file/section: dialogue.py — `_resolve_active_artifact` — user_id Resolution
  - symptom: `_resolve_user_id()` is defined and used to extract user identity, but the timeline_resolution module it should call (`resolve_active_artifact_for_user`) is never imported or invoked in `_resolve_active_artifact`; the user_id is extracted but not used for thread-aware resolution
  - when it matters: When the same user has multiple sessions and expects continuity via thread registry

- file/section: interpretation.py — `infer_human_topics` — Interest Keyword Map
  - symptom: Keyword map is hardcoded (e.g., "memory" → "memory continuity", "circleforge" → "Weslr"); adding a new interest requires code edit; no mechanism exists to register interests dynamically or read them from a config file
  - when it matters: When users create new interests that are not in the hardcoded keyword map

- file/section: interpretation.py — `classify_human_turn` — Completion Notify Patterns
  - symptom: `COMPLETION_NOTIFY_PATTERNS` list includes phrases like "tell me when done" but these are matched via `any(pattern in lowered)` which catches substrings; "don't tell me when done" would incorrectly match
  - when it matters: When user says something like "I don't need you to tell me when done"

- file/section: weslr/chat_responder.py — `format_status_summary` — Evidence Gaps Formatting
  - symptom: `format_evidence_uncertainty()` returns lines for gaps and confidence; `format_delta_block()` has an ev/evidence_gaps_change key; no evidence_gaps_change key is ever written by any code in these three files
  - when it matters: When delta tracking is active and operator wants to see evidence gap changes

Repetitive Failure Patterns

- `_resolve_active_artifact` in dialogue.py is the canonical resolution function but it never calls timeline_resolution; it only falls through to registry fallback
- user_id extraction happens in `_resolve_user_id()` but the extracted user_id is only used for session-keyed registry fallback, never passed to timeline_resolution
- The docstring for `_resolve_active_artifact` describes a three-level cascade but only level 2 (registry fallback) is implemented

Fragmentation Points

- `interpretation.py` maintains its own hardcoded keyword map for interests, completely separate from any interest tracker or interest registry; no shared schema between topic classification and interest persistence
- `weslr/chat_responder.py` formats status output but has no access to the actual decision layer; it receives a `decision` dict as argument but the decision dict shape is never validated or defined in these files
- No file among the three defines what a "reply shape" is supposed to be — `reply_shape` values like "answer_directly", "repair_then_answer", "clarify" are produced by interpretation but never consumed by dialogue.py or chat_responder.py

Unused or Orphaned Elements

- `_compute_boundary_hints` in dialogue.py produces a list of boundary type keywords but the output is never stored, returned, or used by any caller of `_compute_context_selection`
- `_attach_context_selection` in dialogue.py calls `_classify_context` which does not exist in the file; the function is dead code
- `generate_from_self_state` in dialogue.py references `sim.py` and `communicator_state` but these modules are not present in the files read
- `synthesize_concept_or_self_reply` in dialogue.py has an internal allowlist for concept topics but the allowlist cannot be extended without code changes

Hard Limitations

- All three files are pure Python with no schema enforcement; any dict shape can be passed through and will fail silently at runtime
- `handle_request` in chat_responder.py calls `DecisionLayer` via a try/except but the DecisionLayer class is never imported or defined in these files
- No file among the three has any test coverage or validation of the interface contracts between them

Batch Conclusion

Batch 1 reviewed dialogue.py, interpretation.py, and chat_responder.py. Key factual gaps: the thread-aware resolution cascade described in dialogue.py is not implemented (only registry fallback runs), user_id extraction is disconnected from timeline resolution, the interest keyword map is hardcoded and not shared with any interest registry, and no reply_shape values produced by interpretation are consumed by downstream code. Boundary hints are computed but never attached or used.

---

## Batch 2 — weslr/timeline_resolution.py, weslr/artifact_store.py, weslr/lineage_inspector.py, chat_ui.py

Files Read

- weslr/timeline_resolution.py
- weslr/artifact_store.py
- weslr/lineage_inspector.py
- chat_ui.py

Current Subsystems Observed

- Timeline resolution: active thread registry, thread-aware artifact resolution, user-scoped continuity, contamination checking
- Artifact store: artifact persistence, active artifact registry, lineage fields (parent_artifact_ids, root_artifact_id, generation)
- Lineage inspector: artifact lineage classification (root, derived, incomplete, legacy_unknown), thread context tracking
- Chat UI: HTTP server, artifact inspection UI, chat history, state polling

Observed Breakpoints

- file/section: weslr/timeline_resolution.py — `resolve_active_artifact_for_user` — Thread Registry Path
  - symptom: Function calls `get_active_thread(user_id)` and if found, calls `_get_latest_artifact_in_thread(thread_id)`, but `_get_latest_artifact_in_thread` imports and calls `weslr.thread_tracker.get_thread`; if `thread_tracker` module is absent or its `get_thread` returns None, the function falls through to registry fallback without raising an error
  - when it matters: When a user has an active thread set but the thread tracker is unavailable

- file/section: weslr/artifact_store.py — `save_artifact` — Lineage Field Handling
  - symptom: `root_artifact_id` is set to `artifact_id` when not provided (self-referential fallback), but `parent_artifact_ids` is set to an empty list `[]` when not provided; if a derived artifact is saved without explicit parent ids, it will appear as root with generation=0 despite claiming to be derived
  - when it matters: When artifact lineage is reconstructed from storage and generation/root fields are used for trust scoring

- file/section: weslr/artifact_store.py — Active Artifact Registry
  - symptom: Registry is keyed by `session_id` not `user_id`; dialogue.py passes `session_id` as the key when calling `set_active_artifact` and `get_active_artifact`; but `timeline_resolution.py` keys its active thread registry by `user_id`; there is no coordination between session-keyed and user-keyed active artifact tracking
  - when it matters: When the same user_id has multiple sessions with different active artifacts

- file/section: weslr/lineage_inspector.py — `inspect_artifact_lineage` — Legacy Detection
  - symptom: Legacy detection relies solely on presence/absence of the `generation` field; artifacts written before lineage fields was added will classify as `legacy_unknown`, but artifacts written with `generation = None` (explicit null) will also classify as `legacy_unknown` even though they are not legacy
  - when it matters: When querying lineage across artifacts with explicit null generation vs. truly legacy artifacts

- file/section: chat_ui.py — `Handler.do_GET /api/state` — State Payload
  - symptom: `/api/state` calls `state_payload()` which calls `weslr_speak_with_timing()` to get a reply, but `weslr_speak_with_timing()` calls `weslr_main.py speak` which runs a subprocess that imports the full Python path; if any dependency is missing, the whole state call fails
  - when it matters: When the chat UI polls for state and the subprocess call fails, the entire state payload errors out

Repetitive Failure Patterns

- artifact_store.py stores lineage fields but provides no query interface to filter by parent, root, or generation range
- timeline_resolution.py and artifact_store.py both maintain separate registries (active thread registry vs. active artifact registry) with no synchronization between them
- lineage_inspector.py classifies lineage status but chat_ui.py does not call lineage_inspector for the `/api/state` endpoint, only for the artifact inspection endpoint

Fragmentation Points

- Active thread registry (timeline_resolution.py) is stored in `continuity/active_thread_registry.json`; active artifact registry (artifact_store.py) is stored in `continuity/active_artifact_registry.json`; no coordination file or schema links them
- Lineage inspector reads thread_ids from the artifact dict itself (`artifact.get("thread_ids")`), but thread_ids are never written by artifact_store.py at save time — they are only attached by thread_tracker when artifacts are explicitly linked to threads
- chat_ui.py embeds full HTML/CSS/JS inline and calls subprocesses for weslr commands; there is no shared HTTP client or API layer between chat_ui.py and the rest of the codebase

Unused or Orphaned Elements

- `contamination_check` in timeline_resolution.py returns a boolean but the result is included in the resolution dict; no caller of `resolve_active_artifact_for_user` reads or acts on `contamination_check` in the files reviewed
- `link_artifact_to_active_thread` in timeline_resolution.py is defined but never called by any file in these batches
- `has_continuity` in timeline_resolution.py is defined for CLI use; no runtime code calls it
- `get_continuity_status` in timeline_resolution.py is defined for CLI use; no runtime code calls it

Hard Limitations

- No file provides a query interface to retrieve artifacts by lineage (e.g., "all descendants of artifact X", "all roots", "all artifacts at generation > 0")
- artifact_store.py has no cleanup or archival mechanism; artifacts accumulate indefinitely in `continuity/artifacts/`
- chat_ui.py runs a ThreadingHTTPServer on port 8081 with no authentication, no rate limiting, and no TLS

Batch Conclusion

Batch 2 reviewed timeline_resolution.py, artifact_store.py, lineage_inspector.py, and chat_ui.py. Key factual gaps: active thread registry and active artifact registry are separate and unsynchronized; artifact lineage fields are written but no query interface exists for lineage traversal; contamination_check result is computed but never consumed; thread_ids are read from artifacts but never written at artifact save time; and chat_ui.py subprocess calls can fail the entire state endpoint. No archival or cleanup mechanism for accumulated artifacts.

---

## Batch 3 — weslr/cross_session_artifact_eval.py, weslr/relevance_eval_analysis.py

Files Read

- weslr/cross_session_artifact_eval.py
- weslr/relevance_eval_analysis.py

Current Subsystems Observed

- Cross-session artifact evaluation: scenario catalog (csc-001, csc-006, csc-008), session simulation, continuity assessment, contamination advisory generation
- Relevance evaluation analysis: pattern detection over eval artifacts, contamination advisory analysis, context/boundary signal tracking, chain scenario analysis

Observed Breakpoints

- file/section: weslr/cross_session_artifact_eval.py — SCENARIOS — csc-001 user_id Sharing
  - symptom: Scenario csc-001 sets user_id="csc001-user" and uses it for both session_a and session_b; this is intentional for cross-session continuity, but session_a saves an artifact with its own session_id as context and then session_b tries to resolve with a different session_id; the active thread registry is keyed by user_id so thread persistence works, but the active artifact registry is keyed by session_id — session_b will not find session_a's artifact in the registry because the key differs
  - when it matters: When session_b in csc-001 tries to resolve the artifact from session_a using registry fallback path

- file/section: weslr/cross_session_artifact_eval.py — `_execute_session_a` — Thread Creation
  - symptom: Thread creation is attempted via `weslr.thread_tracker.create_thread` but if thread_tracker module is absent or create_thread returns None, `thread_id` remains None and the function silently continues without failing; no assertion or error is raised
  - when it matters: When running csc scenarios in an environment where thread_tracker module is not importable

- file/section: weslr/relevance_eval_analysis.py — `analyze_patterns` — Phase 1A vs Chain Scenario Handling
  - symptom: Function has two separate code paths: one for chain scenarios (when "chain_results" key is present in artifact) and one for single-turn Phase 1A scenarios; but single-turn artifacts from Phase 1A are also produced by the relevance eval harness and they do NOT have a "chain_results" key; the single-turn path tries to access `artifact.get("relevant_interests_snapshot", [])` and `artifact.get("resolved_artifact_interests", [])` — but these fields are only populated when the relevance eval harness runs; if the harness writes artifacts without these fields, the single-turn code path will silently treat them as empty
  - when it matters: When eval artifacts exist with partial field coverage

- file/section: weslr/relevance_eval_analysis.py — `print_analysis_report` — Undefined Variable
  - symptom: `print_analysis_report` references `boundary_hint_counts` directly at the bottom of the function when building `top_boundary`, but `boundary_hint_counts` is a local variable inside `analyze_patterns`, not passed into `print_analysis_report`; the function will raise NameError at runtime when called
  - when it matters: When running the full analysis and printing the report

Repetitive Failure Patterns

- cross_session_artifact_eval.py simulates sessions but the simulation cannot verify that the actual runtime resolution paths work — it can only verify the data that flows through the simulated calls
- relevance_eval_analysis.py runs entirely in-memory from already-written eval artifacts; if the eval harness fails to write artifacts, the analysis produces no results without any error signal
- Both modules are evaluation/inspection tools that read from and write to the same `continuity/artifacts/eval/` directory; there is no locking or atomic write mechanism, so concurrent runs could corrupt the index

Fragmentation Points

- cross_session_artifact_eval.py defines scenario metadata (SCENARIOS dict) but the scenario definitions are not shared with any other module; if the scenario catalog needs to be extended, it requires a code change in that file
- relevance_eval_analysis.py embeds domain keyword sets (`_DOMAIN_KEYWORD_SETS`) for contamination detection but these are not shared with interpretation.py which has its own hardcoded keyword map
- Both eval modules write artifacts to `continuity/artifacts/eval/` but no other module reads from that directory; the eval output is isolated from runtime decision-making

Unused or Orphaned Elements

- `run_all_csc_scenarios` in cross_session_artifact_eval.py runs scenarios sequentially; no parallel execution, no result aggregation, no summary output format defined
- `run_full_analysis` in relevance_eval_analysis.py loads all eval artifacts and prints a report but returns the raw result dict; no caller uses the returned dict
- `_extract_domain_keywords` in cross_session_artifact_eval.py is defined but never called by any code path in the module

Hard Limitations

- No mechanism exists to automatically run these eval scenarios on a schedule; they must be triggered manually
- eval artifacts accumulate in `continuity/artifacts/eval/` with no retention policy; no cleanup of old eval artifacts
- Neither module has any test coverage; they cannot be unit-tested without a full filesystem with continuity/artifacts/ directory pre-populated

Batch Conclusion

Batch 3 reviewed cross_session_artifact_eval.py and relevance_eval_analysis.py. Key factual gaps: session_id vs user_id key mismatch between registries causes cross-session fallback to fail silently; thread creation failure is silent; eval analysis print function references an out-of-scope variable causing NameError; domain keyword sets are duplicated across modules; eval output is isolated with no automated scheduling or cleanup. No test coverage for either module.

---

## Batch 4 — Canon and architecture docs

Files Read

- ARCHITECTURE_DOCTRINE_ADDENDUM.md
- docs/ARTIFACT_TYPES_AND_LIFECYCLE_V1.md
- docs/ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md
- docs/CONTEXT_AND_BOUNDARY_SIGNALS_V1.md
- docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md
- docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md
- docs/WESLR_FUNCTIONAL_TREE_MAP_V1.md

Current Subsystems Observed

- Artifact lifecycle management (creation, validation, versioning, retirement)
- Artifact lineage and graph model (nodes, edges, provenance)
- Context and boundary signals (external input, session context, artifact boundaries)
- Continuity contamination control (timeline isolation, session handoffs)
- Timeline-native continuity resolution (permanent records, targeted retrieval)
- Functional tree map (Weslr system organization)

Observed Breakpoints

- doc/section: ARTIFACT_TYPES_AND_LIFECYCLE_V1.md — Artifact Retirement
  - symptom: No explicit retirement criteria defined for artifacts; "retired" status mentioned but not enumerated
  - when it matters: When artifacts accumulate over time and need lifecycle pruning

- doc/section: ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md — Provenance Fields
  - symptom: Provenance fields listed (author, timestamp, tool, method, version, source_id) but source_id field purpose is ambiguous when artifacts can have multiple contributing sources
  - when it matters: When tracing lineage across merged or federated artifacts

- doc/section: CONTEXT_AND_BOUNDARY_SIGNALS_V1.md — Signal Categories
  - symptom: "Artifact metadata" listed as a signal category but no schema or field list provided for what metadata fields constitute a valid signal
  - when it matters: When evaluating whether a given artifact's metadata is sufficient to reconstruct context

- doc/section: TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md — Permanent Record Criteria
  - symptom: "Permanent record" is defined by disposition rather than by schema; no explicit set of required fields that make a record permanent vs. ephemeral
  - when it matters: When deciding whether a new artifact should be committed to permanent storage

Repetitive Failure Patterns

- Documents reference "schema" for artifact types but no schema definitions exist as separate artifacts
- "Provenance" is used as both a field name and a concept, with no clear distinction between the two uses
- Continuity strategy references "timeline IDs" without specifying the format or scope of those IDs

Fragmentation Points

- ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md treats artifacts as nodes in a graph, but the functional tree map organizes Weslr as a hierarchical system — no mapping between the two models
- Context signals are described as external inputs in CONTEXT_AND_BOUNDARY_SIGNALS_V1.md but continuity resolution in TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md does not reference which signal types trigger permanent record creation
- No document defines how "timeline-native" differs architecturally from the graph model used for artifact lineage

Unused or Orphaned Elements

- ARCHITECTURE_DOCTRINE_ADDENDUM.md references "OCC Agent" and "governance_surface" but no other document references governance or agent roles
- "Session boundary" is mentioned in CONTEXT_AND_BOUNDARY_SIGNALS_V1.md but no session concept appears in the functional tree map
- ARTIFACT_TYPES_AND_LIFECYCLE_V1.md lists "configuration" as an artifact type but no configuration artifact examples are provided in any other document

Hard Limitations

- All seven documents exist as markdown files only; no machine-readable schema, validation, or enforcement mechanism defined in this batch
- No definition of which document or component is authoritative when documents conflict
- No timeline or version specified for when any document was last validated or updated

Batch Conclusion

Batch 4 reviewed all seven canon/architecture documents. Key factual gaps: artifact retirement criteria are undefined, provenance field semantics are ambiguous, artifact metadata schema is not specified, and permanent record criteria lack a field-based definition. The graph model and functional tree map have no explicit mapping. All documents are markdown-only with no cross-document conflict resolution mechanism defined.
