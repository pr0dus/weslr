# WESLR Missing Layers Discovery V1

---

## Section 1 — Grouping of Bottlenecks

### Group A — Wiring Failures

Bottlenecks where code describes a path but the wire is not connected:

- dialogue.py: `_resolve_active_artifact` docstring describes Level 1 (timeline_resolution) but that module is never imported or called
- dialogue.py: `_resolve_user_id()` extracts user identity but the result is not passed to any thread-aware resolution function
- timeline_resolution.py: `link_artifact_to_active_thread` is defined but no caller exists anywhere in the codebase
- timeline_resolution.py: `has_continuity` and `get_continuity_status` are defined for CLI only — no runtime caller
- artifact_store.py + timeline_resolution.py: active thread registry and active artifact registry are separate files with no synchronization; a thread can be active while a different artifact is registered as active for the same user
- lineage_inspector.py: `inspect_artifact_lineage` is inspection-only — its output is never used by any runtime path
- chat_ui.py: `/api/state` endpoint subprocess call fails the entire state payload if dependencies are missing — no partial degradation
- `_compute_boundary_hints` in dialogue.py: computes a list that is never stored, returned, or consumed
- `_attach_context_selection` in dialogue.py: calls `_classify_context` which does not exist — dead code path

### Group B — Identity Mismatches

Bottlenecks where two systems have different identity keys for the same entity:

- artifact_store.py: active artifact registry keyed by `session_id`
- timeline_resolution.py: active thread registry keyed by `user_id`
- cross_session_artifact_eval.py csc-001: session_a saves with its own `session_id` key; session_b uses a different `session_id`; registry fallback lookup fails because keys differ — but this failure is silent

Bottlenecks where identity state cannot be reconstructed correctly:

- lineage_inspector.py: legacy detection uses presence/absence of `generation` field only; explicit `generation = None` and true field-absence both yield `legacy_unknown` — same classification for two different states
- artifact_store.py: `parent_artifact_ids` defaults to `[]` and `generation` defaults to `0`; an artifact saved without explicit lineage fields is indistinguishable from one intentionally saved as a root

### Group C — Unused Intelligence

Signals that are produced but never consumed:

- `contamination_check` in timeline_resolution.py: result is placed in the resolution dict; no caller reads it
- `reply_shape` values from interpretation.py (`answer_directly`, `repair_then_answer`, `clarify`, etc.): produced by `classify_human_turn` and `interpret_human_turn`; no code path reads or acts on these values
- `_compute_boundary_hints` output: computed per message, never stored or passed to any downstream function
- `_lineage_inspection` attached to `research_context` by `_attach_lineage_inspection`: observational metadata that is never read by a rendering or decision function

Duplicated hardcoded intelligence with no shared source:

- interpretation.py `infer_human_topics`: hardcoded keyword map for mapping keywords to interest names
- relevance_eval_analysis.py `_DOMAIN_KEYWORD_SETS`: hardcoded domain keyword sets for contamination detection
- Neither is read from a shared config or registry

Orphaned functions that are never called in any code path:

- `link_artifact_to_active_thread` (timeline_resolution.py)
- `has_continuity` (timeline_resolution.py)
- `get_continuity_status` (timeline_resolution.py)
- `_extract_domain_keywords` (cross_session_artifact_eval.py)
- `_attach_context_selection` (dialogue.py — calls nonexistent `_classify_context`)
- `generate_from_self_state` (dialogue.py — references absent `sim.py` and `communicator_state`)
- `synthesize_concept_or_self_reply` allowlist (dialogue.py — internal hardcoded allowlist with no extension mechanism)

### Group D — Doctrine vs Runtime Gaps

Signals specified in docs but absent from runtime:

- docs describe artifact metadata as a signal category — no schema defining which metadata fields constitute a valid signal
- docs reference "timeline IDs" — no format, scope, or validation defined anywhere in code or docs
- docs describe provenance as both a concept and a field — no distinction between the two uses
- docs define "permanent record" by disposition — no schema of required fields that makes a record permanent

Runtime produces signals that eval cannot verify:

- eval harness writes artifacts to `continuity/artifacts/eval/` but no runtime path reads from that directory — eval and runtime are completely isolated
- eval analysis (`relevance_eval_analysis.py`) runs offline from already-written artifacts; if the harness fails to write, the analysis silently produces empty results

Eval produces no usable signal back to runtime:

- `run_full_analysis` returns a dict — no caller uses the return value
- `run_all_csc_scenarios` prints a line per scenario — no aggregate signal, no pass/fail propagation

Eval artifacts and continuity artifacts accumulate with no retention mechanism:

- artifact_store.py: no cleanup, no archival, no retention policy
- cross_session_artifact_eval.py: no retention policy for `continuity/artifacts/eval/`
- relevance_eval_analysis.py: `print_analysis_report` references `boundary_hint_counts` which is a local variable in `analyze_patterns` — NameError at runtime

Docs describe behavior that code does not implement:

- CONTEXT_AND_BOUNDARY_SIGNALS_V1.md: context signals described as external inputs; TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md does not specify which signal types trigger permanent record creation
- ARTIFACT_LINEAGE_AND_GRAPH_MODEL_V1.md: artifacts as graph nodes; WESLR_FUNCTIONAL_TREE_MAP_V1.md: hierarchical system — no mapping between the two models
- No document specifies which document is authoritative when two documents conflict

---

## Section 2 — What Must Exist for This to Work

### Wiring Failures — What Must Exist

- **A wired resolution path**: The function that is described as Level 1 (thread-aware resolution) must actually be called when resolving an artifact reference. The call must exist in the code, not only in the docstring.

- **A way to verify resolution succeeded**: When `resolve_active_artifact_for_user` returns, the caller must be able to distinguish "found an artifact via thread path" from "fell through to registry fallback" from "found nothing". The current code falls through silently.

- **A way to confirm registry sync**: When an artifact is set as active, there must be a way to determine whether the thread registry and the artifact registry agree on which artifact is active for a given user. Currently they can disagree with no detection.

- **A way to validate thread creation before use**: When `create_thread` is called, the result must be checked. If thread creation fails, the calling code must not silently continue with a None thread_id.

- **A way for computed signals to reach consumers**: Boundary hints, contamination_check results, and context selection signals must be stored where downstream functions can read them. Currently `_compute_boundary_hints` computes and discards; `contamination_check` result is placed in a dict no one reads.

### Identity Mismatches — What Must Exist

- **A way to map session identity to user identity across registries**: Either the active artifact registry must key by the same identity as the active thread registry, or there must be a known lookup path from session_id to user_id that resolution can follow.

- **A way to distinguish true absence from explicit null in lineage**: The difference between "this artifact predates lineage fields" and "this artifact was saved with generation explicitly null" must be recoverable from the stored data. Currently both produce `legacy_unknown`.

- **A way to determine whether an artifact is a root because it was saved as one vs. because lineage fields were omitted**: These are different states. The artifact store must produce artifacts that are unambiguously classifiable as root or derived without requiring external context.

### Unused Intelligence — What Must Exist

- **A way to extend interest keywords without code edits**: The keyword map in `interpretation.py` must either be read from a shared config or be generated from an external interest registry. A new interest registered by a user must be discoverable by the topic inference path without a code deployment.

- **A way to extend domain keyword sets without code edits**: The contamination detection keywords in `relevance_eval_analysis.py` must be backed by a shared config or registry that is used by both eval analysis and runtime contamination detection.

- **A way to ensure produced signals are consumed**: When a new signal type is added (e.g., `boundary_hints`, `reply_shape`, `contamination_check`), there must be a way to detect whether any consumer exists. Signals with no consumer must produce a visible indicator, not silent丢弃.

- **A way to run eval on a schedule and propagate results**: Eval scenarios must be executable without manual triggering, and their results must produce a signal that runtime or monitoring can observe.

### Doctrine vs Runtime Gaps — What Must Exist

- **A way to define which metadata fields constitute a valid artifact metadata signal**: The docs say "artifact metadata" is a signal category. The actual field list that makes metadata sufficient to reconstruct context must be specified in a machine-readable form.

- **A way to define timeline ID format and scope**: "Timeline IDs" are referenced across docs and code but never defined. A timeline ID format must exist so it can be validated, compared, and used as a stable reference.

- **A way to make docs enforceable**: When a doc specifies a contract (e.g., "artifact must have these fields to be considered permanent"), runtime must be able to validate against that contract. Markdown docs cannot be enforced by code.

- **A way to resolve conflicts between documents**: When two docs give different guidance, there must be a rule for which one governs. Currently no such rule exists.

- **A way to determine when an artifact should become permanent**: The boundary between ephemeral and permanent must be definable by explicit criteria, not only by disposition.

---

## Section 3 — Minimal Completion Set

The minimum set of missing capabilities required so that signals influence behavior, continuity actually works, and eval reflects runtime reality:

### M1 — Thread-aware resolution must be called

The `resolve_active_artifact_for_user` from `timeline_resolution.py` must be invoked in `_resolve_active_artifact` when a user_id is available. The resolution path result must be captured and used, not discarded.

### M2 — Resolution outcome must be surfaced to caller

`_resolve_active_artifact` must return a structure that tells the caller which resolution path was taken (active_thread, registry_fallback, none). The calling code must be able to branch on this result.

### M3 — Session-to-user identity mapping must be defined

The relationship between `session_id` (used by artifact registry) and `user_id` (used by thread registry) must be specified and used. Cross-session continuity cannot work when the two registries use unrelated keys.

### M4 — Thread creation failure must be visible

When `create_thread` is called and returns None or raises, the calling code in `_execute_session_a` must record or report this failure rather than silently continuing.

### M5 — Lineage source-of-truth must be unambiguous

Artifacts must store a field that distinguishes "lineage fields not applicable (legacy)" from "lineage fields were applicable but provided as null." Without this, lineage classification is unreliable.

### M6 — Boundary hints must be attached to the signal output

`_compute_boundary_hints` output must be stored in a location that `build_communicator_message_payload` can include in the response dict it returns. Currently it is computed and discarded.

### M7 — Reply shape must be consumed

`reply_shape` values from `interpret_human_turn` must be read by some downstream function. If no function consumes them, they serve no purpose and constitute misleading complexity.

### M8 — Interest keyword map must be dynamic

`infer_human_topics` must read its keyword mapping from a shared, writable source. Hardcoded keyword maps cannot reflect user-registered interests without code changes.

### M9 — Eval output must be observable by runtime

Artifacts written to `continuity/artifacts/eval/` must be readable by a runtime-accessible path, or eval results must be propagated to a location runtime can query. Currently eval and runtime are isolated.

### M10 — `print_analysis_report` variable reference must be fixed

`boundary_hint_counts` must be passed from `analyze_patterns` to `print_analysis_report`, or the variable must be placed in a scope accessible to both functions.

### M11 — Eval must be schedulable

A mechanism must exist to trigger `run_all_csc_scenarios` and `run_full_analysis` without manual invocation. The results of scheduled runs must not require reading files manually.

### M12 — Artifact retention must be defined

A policy or mechanism must exist to prevent indefinite accumulation of artifacts in `continuity/artifacts/` and `continuity/artifacts/eval/`. This can be a count limit, age limit, or explicit archival step — something that prevents unbounded growth.

### M13 — Artifact metadata schema must be machine-readable

The set of fields that constitute a valid artifact metadata signal must exist as a defined schema. Docs can describe this in prose, but the schema must be expressible in a form that code can validate against.

### M14 — Permanent record criteria must be field-based

The distinction between ephemeral and permanent artifacts must be expressible as a set of field conditions, not only as a disposition label.

### M15 — Conflict resolution rule must exist

When two documents give different guidance, a rule must exist that specifies which one governs. This can be a simple ordering (e.g., "more recent wins" or "explicit override wins"), but the absence of any rule means every conflict requires manual arbitration.

---

## Section 4 — Stop

No solutions described.
No system names proposed.
No implementation directions given.

Only capabilities listed: M1 through M15.
Only groups defined: Wiring Failures, Identity Mismatches, Unused Intelligence, Doctrine vs Runtime Gaps.
Only factual gaps from bottleneck discovery used as input.
