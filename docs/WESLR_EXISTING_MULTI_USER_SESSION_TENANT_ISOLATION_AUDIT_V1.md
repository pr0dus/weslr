# WESLR Existing Multi-User Session Tenant Isolation Audit V1

## Status

- Audit label: `AUDIT_EXISTING_MULTI_USER_SESSION_TENANT_ISOLATION_IMPLEMENTATION_V1`
- Lane status: audit-only / inventory-review
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no behavior implementation, no helper implementation, no runtime edits, no source/test changes except narrow release-gate exact-file allowance if needed
- Persistence status: no `.weslr` reads/writes performed by this audit
- Provider/search/advisor status: no provider/model/search/advisor calls
- Scope: existing tracked WESLR implementation, docs, tests, and known structure relevant to multi-user/browser/session/tenant isolation

## Section 1 — Review Target

- Repo path: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Expected start HEAD: `055f284`
- Report path: `docs/WESLR_EXISTING_MULTI_USER_SESSION_TENANT_ISOLATION_AUDIT_V1.md`
- Forbidden runtime path checked by validation: `weslr/chat_responder.py` unchanged
- Forbidden state path: `.weslr` not inspected as runtime state and not modified

## Section 2 — Inspection Method

Tracked files were inspected with targeted searches for:

- `user_id`
- `session_id`
- `tenant_id`
- `conversation_id`
- `account`
- `auth`
- `browser`
- `websocket`
- `request`
- `context`
- `memory`
- `timeline`
- `profile`
- `locale`
- `language`
- `privacy`
- `retention`
- `isolation`
- `namespace`
- `per-user`
- `multi-user`
- `multi-tenant`
- `concurrency`
- `async`
- `lock`
- `queue`
- `cache`
- `global`
- `singleton`
- `.weslr`

The audit intentionally did not inspect or mutate live `.weslr` runtime state and did not touch `weslr/chat_responder.py`.

## Section 3 — Existing Implementation Inventory

### 3.1 Tenant context implementation

File: `weslr/tenant_context.py`

Relevant implemented functions/classes/modules:

- `set_current_tenant(tenant_id)`
- `get_current_tenant()`
- `is_default_tenant()`
- `get_tenant_root()`
- `get_tenant_dir(tenant_id)`
- `get_tenant_config_path(tenant_id)`
- `resolve_path(relative_path, tenant_id)`
- `list_tenants()`
- `has_tenant(tenant_id)`

What appears implemented:

- Thread-local tenant context via `threading.local()`.
- Optional `WESLR_TENANT_ID` / `WESLR_TENANT_DIR` environment concepts.
- Tenant-specific path resolution when a tenant is explicitly set.
- Legacy single-tenant fallback to workspace `.weslr` paths when no tenant is set.
- Tenant config discovery by `tenant_config.json`.

What appears partial:

- Tenant routing exists as a utility, not as a universal request/account enforcement layer.
- Many call sites still default to `tenant_id=None`, `tenant_id="default"`, or hard-coded default tenant/user values.
- Thread-local context helps threaded isolation only if all entry points set and clear it correctly.
- There is no audited request middleware proving tenant context is established per browser/API request.

What appears missing:

- No global account/session/tenant authorization boundary around all stateful reads/writes.
- No mandatory tenant key requirement for all memory/context/cache/log access.
- No request lifecycle cleanup guarantee for async/browser workloads.

### 3.2 Bootstrap and timeline identity foundation

File: `weslr/bootstrap.py`

Relevant implemented functions/classes/modules:

- `new_timeline_id(user_id)`
- `new_pending_bootstrap(...)`
- `complete_bootstrap(...)`
- `register_completed_bootstrap(...)`
- `get_bootstrap_record(user_id)`
- `get_bootstrap_by_timeline(timeline_id)`
- `is_verified_timeline(timeline_id)`
- in-process stores `_BOOTSTRAP_RECORDS` and `_BOOTSTRAP_BY_TIMELINE`

What appears implemented:

- Bootstrap records include `user_id`, `email`, `display_name`, `institution_id`, status, activation token fields, secret words hash, trusted device ID, and `timeline_id`.
- Completed bootstrap records can be indexed by `user_id` and by `timeline_id`.
- Activation token is invalidated on completion.
- `timeline_id` is intended as a persistent identity record rather than a transient session.

What appears partial or risky:

- `_BOOTSTRAP_RECORDS` and `_BOOTSTRAP_BY_TIMELINE` are process-local mutable dictionaries.
- The comments explicitly call the in-process store a stub to replace with DB/Redis in production.
- `hash_secret_words()` returns a string containing both the SHA-256 hash and the normalized words after a colon. That is not suitable for real production secret storage.
- `complete_bootstrap()` attempts to persist bootstrap status into `communicator_self.json`, which appears single-record/global rather than clearly tenant/user namespaced.

What appears missing:

- Production account store.
- Production-safe secret hashing with per-record salt and no plaintext suffix.
- Cross-process/session persistence model for pending/completed bootstrap records.
- Role/account permission checks for browser/public use.

### 3.3 Channel identity and profile implementation

Files:

- `weslr/channel_identity.py`
- `weslr/user_profile.py`
- `weslr/commands/channel_identity_commands.py`

Relevant implemented functions/classes/modules:

- `ChannelIdentityEvidence`
- `ChannelBinding`
- `default_channel_binding(...)`
- `finalize_binding(...)`
- `validate_binding(...)`
- `build_channel_identity_evidence(...)`
- `UserProfile`
- `MembershipClaim`
- `load_user_profile(...)`
- `save_user_profile(...)`
- `validate_user_profile(...)`

What appears implemented:

- Explicit separation between profile claims and channel/device/session verification.
- Text self-claims are treated as claims, not verification.
- Binding confidence distinguishes strong/medium/weak evidence.
- User profile stores language and communication preferences.
- Membership claims are marked unverified by default.

What appears partial or risky:

- Defaults point to one global `DEFAULT_WESLR_HOME = /data/data/com.termux/files/home/.weslr`.
- Profile and channel-binding files default to single paths: `user_profile.json` and `channel_identity.json`.
- CLI binding uses `OPENCLAW_SESSION_ID` evidence but is not a full account/session auth boundary.
- `build_channel_identity_evidence()` can produce useful metadata, but this audit did not find universal enforcement that every memory/context read depends on verified identity.

What appears missing:

- Browser login/account model.
- Per-account profile directory or tenant-scoped user profile store as the default.
- Guest/anonymous session contract.
- User-data export/delete controls bound to profile/account identity.

### 3.4 Entity memory and memory capture implementation

Files:

- `weslr/entity_memory.py`
- `weslr/memory_capture.py`
- `weslr/commands/entity_memory_commands.py`

Relevant implemented functions/classes/modules:

- `EntityType`
- `AccessLevel`
- `RelationshipType`
- `RoleType`
- `MemoryRecord`
- `entity_memory_path(...)`
- `append_entity_memory(...)`
- `load_entity_memories(...)`
- `summarize_memory_records(...)`
- `MemoryCaptureCandidate`
- `classify_memory_capture_candidates(...)`
- `safe_turn_fingerprint(...)`
- `contains_sensitive_content(...)`
- `has_explicit_consent(...)`

What appears implemented:

- Entity-scoped memory namespaces for persons, families, companies, institutions, teams, departments, projects, systems, and unknown entities.
- Access-level labels: private, shared, representative, public, operator_only, role_restricted.
- Memory capture avoids raw message logging and uses bounded summaries/fingerprints.
- Sensitive-pattern and consent-pattern checks exist.
- Memory records include provenance, access level, verified flag, confidence, related entities, project IDs, and retention policy field.

What appears partial or risky:

- Default base path again points to one global `DEFAULT_WESLR_HOME` unless `base_path` is explicitly provided.
- Access levels are stored as metadata, but this audit did not find a complete enforcement layer proving access checks happen before every read/summarization.
- Retention policy is a field value, not a complete deletion/export/expiry system.
- Entity memory can be correctly scoped if callers choose the right `entity_type`, `entity_id`, and base path; it is not yet sufficient as a public multi-user isolation boundary by itself.

What appears missing:

- Mandatory account/tenant/session namespace for every memory read/write.
- Central authorization gate that maps verified account/session to allowed entity memory scopes.
- Data subject export/delete implementation.
- International privacy policy enforcement beyond local metadata fields.

### 3.5 Session/artifact continuity implementation

Files/docs:

- `weslr/artifact_store.py`
- `docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md`

Relevant implemented functions/classes/modules:

- `save_artifact(...)`
- `get_artifact(...)`
- `list_artifacts(...)`
- `search_artifacts(...)`
- `set_active_artifact(session_id, artifact_id)`
- `get_active_artifact(session_id)`
- `clear_active_artifact(session_id)`

What appears implemented:

- Persistent artifact files under `continuity/artifacts/`.
- Active artifact registry keyed by `session_id`.
- Artifact lineage fields exist for new artifacts: `parent_artifact_ids`, `root_artifact_id`, `generation`.

What appears partial or risky:

- Artifact storage itself is global under repository `continuity/artifacts/`, not tenant/user namespaced.
- Active artifact registry is only keyed by `session_id`, not by `(tenant_id, user_id, session_id)`.
- Existing continuity design docs already identify that session-keyed reference resolution does not match user-scope continuity and can fail across sessions.
- Session ID alone is not an authorization boundary.

What appears missing:

- Tenant/user/workspace ownership metadata on artifacts as a required field.
- Authorization check before artifact retrieval.
- Upload/material namespace per account/session/tenant.
- Cross-user contamination prevention for references like “this”.

### 3.6 Chat hints and process-global state

File: `weslr/chat_hints.py`

Relevant implemented functions/classes/modules:

- `_HINTS: Dict[Tuple[Optional[str], Optional[str]], List[str]]`
- `get_hints(workspace_id, user_id)`
- `add_hint(workspace_id, user_id, hint)`
- `set_hints(workspace_id, user_id, hints)`
- `clear_hints(workspace_id, user_id)`

What appears implemented:

- Hints are keyed by `(workspace_id, user_id)`.
- Hints are allowlisted and small.

What appears partial or risky:

- The key accepts `None` values, which can collapse hints into shared `(None, user_id)` or `(workspace_id, None)` patterns if callers are loose.
- The store is process-local mutable state.
- No concurrency lock is present.

What appears missing:

- Mandatory non-null namespace keys for public/browser use.
- Request-bound cleanup or durable tenant-scoped storage contract.

### 3.7 Voice/browser gateway implementation

File: `weslr/voice_gateway.py`

Relevant implemented functions/classes/modules:

- `weslr_chat(text, timeline_id="tl_default")`
- `log_voice_event(..., timeline_id)`
- `voice_connection(ws, path=None)`

What appears implemented:

- WebSocket voice connection handling exists.
- Voice path supports `?user_id=<normalized_user>` and maps to `tl_user_<normalized>`.
- Without `user_id`, it falls back to `tl_default` for backward compatibility.
- Voice events are logged to `.weslr/timelines/<timeline_id>/events.jsonl`.

What appears partial or risky:

- `user_id` appears to come from query string routing, not authenticated account binding.
- Fallback to `tl_default` creates a known shared timeline risk for browser/public use.
- Logged voice event data includes transcript and response text, which may be private if used publicly.
- Voice event uses fixed `client_id: browser`, `source: operator`, and `trust_level: operator_verified`, which is unsafe for arbitrary users unless separately authenticated.

What appears missing:

- Browser session auth.
- Guest isolation.
- Locale/language metadata beyond default English in logging.
- Public-safe transcript retention policy.
- Per-request account/session/tenant authorization.

### 3.8 Tenant-aware domain/research stores

Files observed through search:

- `weslr/document_ingestor.py`
- `weslr/fact_extractor.py`
- `weslr/modules/frontier_store.py`
- `weslr/modules/frontier_proposer.py`
- `weslr/search_adapters/evidence_packet_store.py`
- `weslr/combinatorial_materials.py`
- `weslr/combinatorial_chemistry.py`
- `weslr/commands/propose.py`
- `weslr/commands/frontier_commands.py`

What appears implemented:

- Some document/fact/frontier/evidence paths route through `tenant_context.resolve_path(...)`.
- Several command/domain functions accept `tenant_id` parameters.
- Some frontend/domain commands use default tenant strings for legacy behavior.

What appears partial or risky:

- Tenant support is uneven: some modules are tenant-aware, while many default to `tenant_id=None` or ``tenant_id="default"`.
- A utility-level tenant path resolver does not prove end-to-end tenant isolation.
- Default tenant behavior is suitable for legacy/local use but unsafe as a public multi-tenant default.

What appears missing:

- A complete map of all persistent stores and whether each is tenant-scoped.
- A mandatory tenant context precondition for public/browser request entry points.
- Negative tests proving tenant A cannot read tenant B facts, documents, proposals, artifacts, queues, logs, or traces.

### 3.9 Existing docs and designs

Relevant docs found:

- `docs/WESLR_ACCOUNT_TENANT_AND_DATA_OWNERSHIP_V1.md`
- `docs/PUBLIC_SURFACE_INVENTORY_V1.md`
- `docs/REPO_HYGIENE_STANDARD_V1.md`
- `docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md`
- `docs/TEST_LANE_AUDIT_V1.md`
- `docs/PUBLIC_LEARNING_BOUNDARY_V1.md`
- `docs/CONTEXT_AND_BOUNDARY_SIGNALS_V1.md`
- `docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md`

What appears implemented by documentation:

- Clear conceptual distinction among person identity, account access, workspace membership, tenant ownership, memory scope, role authority, data ownership, and operator authority.
- Public-surface inventory already identifies public demo hardening requirements: operator panel hidden, file upload disabled/hidden, memory writes unavailable, execution unavailable, limitations visible, backend errors sanitized.
- Repo hygiene standard defines `.weslr` as runtime state by default.
- Timeline continuity design explicitly says session is not the correct durable continuity granularity.

What appears only designed/documented:

- Full account/tenant/data ownership contract.
- Public browser readiness boundary.
- Data export/delete/user departure policy.
- Cross-session/user continuity resolution model.
- Public-demo read-only mode enforcement.

What appears missing:

- A single enforced implementation contract tying all of these docs to runtime entry points.
- Complete browser/public/international request boundary.

## Section 4 — Multi-User / Session / Tenant Isolation Assessment

### Users

Status: partial.

Evidence:

- `UserProfile` and `ChannelIdentityEvidence` exist and correctly avoid overclaiming verification.
- Entity memory can store person-scoped records.
- Bootstrap can create user-linked timelines.

Gap:

- Defaults still point to global profile/memory locations.
- User identity is not shown as a mandatory authorization input to every state read/write.

### Sessions

Status: partial and not sufficient.

Evidence:

- Artifact active registry is keyed by `session_id`.
- Channel identity carries `session_id` metadata.
- Voice gateway creates a per-connection `connection_id` and passes a timeline.

Gap:

- Session ID is used as a convenience key, not as an authenticated session boundary.
- Active artifact registry is not keyed by tenant/user.
- No complete session lifecycle/expiry/guest cleanup model was found.

### Conversations

Status: mostly missing as an isolation boundary.

Evidence:

- Searches found `conversation_id` references in limited/adjacent contexts, but no complete conversation-scoped storage boundary was identified in the inspected target set.

Gap:

- No clear per-conversation context store with owner/tenant/session keys.
- No proof that conversation context cannot bleed across users.

### Tenants / workspaces

Status: partial.

Evidence:

- `tenant_context.py` provides thread-local tenant context and path resolution.
- Some fact/document/frontier/evidence stores use `resolve_path()`.
- Account/tenant ownership is well documented.

Gap:

- Tenant context is optional/legacy-compatible rather than mandatory.
- Many paths still use default tenant or global `.weslr` conventions.
- Workspace/tenant membership and authorization are documented but not universally enforced.

### Memory / context

Status: partial with meaningful leakage risks.

Evidence:

- Entity memory namespaces and access-level labels exist.
- Memory capture is conservative and avoids raw chat logging.
- Context labeling/validation exists in `weslr/context.py` for injection defense.

Gap:

- Memory path defaults are global unless callers override base path.
- Labels and access levels are metadata, not proof of read-time enforcement.
- Process-global hints and bootstrap stores can share state inside one process.

### Uploaded files / material

Status: missing or not proven.

Evidence:

- Public surface docs mention file upload should be disabled/hidden in public demo mode.
- Document ingestion has tenant-aware path resolution in some places.

Gap:

- No complete upload material boundary was found proving files are keyed by account/session/tenant and inaccessible cross-user.

### Repo/project context

Status: local/single-operator oriented.

Evidence:

- Repo hygiene separates tracked source from `.weslr` runtime state.
- Many docs and helpers assume local repository context.

Gap:

- Public/browser users must not inherit operator repo state, private docs, or local runtime state unless explicitly exposed through a public-safe layer.

### Browser/runtime requests

Status: missing for public multi-user use.

Evidence:

- Voice WebSocket gateway exists and has query-parameter user routing.
- `weslr-ui` public-surface docs identify future `/api/chat` and public-demo hardening needs.

Gap:

- Query-string `user_id` is not authentication.
- `tl_default` fallback is unsafe for public use.
- No universal browser request middleware/account/session boundary was found.

### Caches / global state

Status: risky for public multi-user use.

Evidence:

- `_BOOTSTRAP_RECORDS`, `_BOOTSTRAP_BY_TIMELINE`, `_HINTS`, `_USER_SESSIONS`, `_USER_STATES`, `_TENANT_REASONERS`, `_TENANT_META_ANALYSES`, `_TENANT_ANALOGY_ENGINES`, `_SIM_HISTORY`, and other module-level mutable stores were found.

Gap:

- Some globals are keyed, but keys are optional or defaulted in several cases.
- No universal tenant/user/session namespace requirement.
- No concurrency lock strategy for all mutable globals.

### Logs / traces

Status: partial and unsafe for public defaults.

Evidence:

- Voice timeline event logging writes transcript and response text to `.weslr/timelines/<timeline_id>/events.jsonl`.
- Repo hygiene treats timeline logs as runtime state not to commit.

Gap:

- No public logging privacy policy enforcement found.
- No redaction/export/delete controls proven for logs/traces.
- `tl_default` can aggregate unrelated voice sessions.

### Async / concurrent calls

Status: partial.

Evidence:

- `tenant_context.py` uses `threading.local()`.
- Voice gateway uses `async` WebSocket handling.

Gap:

- Thread-local tenant context does not automatically isolate async tasks unless request entry points bind context correctly and avoid task reuse leaks.
- No async contextvars-based tenant/request boundary was found.
- No complete concurrent write locking strategy was found for JSON/JSONL runtime stores.

## Section 5 — Memory / Context Leakage Risks

Cross-user memory/context leakage risk exists. Direction check must therefore recommend C.

Risks found:

1. Global default `.weslr` paths: `user_profile.py`, `channel_identity.py`, and `entity_memory.py` default to one home directory unless explicitly overridden.
2. Legacy tenant fallback: `tenant_context.resolve_path()` falls back to workspace-global paths when no tenant is set.
3. Shared timeline fallback: `voice_gateway.py` uses `tl_default` when no `user_id` query parameter is supplied.
4. Query-string identity: voice routing accepts `user_id` from WebSocket path rather than a verified account/session boundary.
5. Session-only artifact registry: `artifact_store.py` keys active artifact by `session_id` without tenant/user namespace.
6. Global artifact store: artifact files are stored under repository `continuity/artifacts/` without required owner/tenant namespace.
7. Process-global mutable stores: bootstrap records, chat hints, command/session caches, simulation history, and other globals can share process memory across requests.
8. Optional namespace keys: chat hints permit `None` workspace/user keys, increasing collision risk if callers are incomplete.
9. Access metadata without universal enforcement: entity memory has access labels, but this audit did not find a central enforced authorization gate for every read.
10. Logs/traces may contain private text: voice timeline events store transcripts/responses and need tenant/user/session privacy boundaries before public use.
11. Docs identify future requirements but do not enforce them: account/tenant/data ownership and public demo contracts exist mostly as design/governance docs.
12. Concurrency model incomplete: thread-local tenant context and JSON/JSONL stores need request-bound async-safe isolation and write locking before many-user browser use.

## Section 6 — Browser / Public / International Readiness

| Area | Result | Notes |
|---|---|---|
| Per-user memory separation | Partial | Entity namespaces exist, but global defaults and read enforcement gaps remain. |
| Per-session context separation | Partial | Session IDs exist, but are not sufficient authorization boundaries. |
| Authentication/account boundary | Missing / design-only | Bootstrap/profile/binding exist, but no full browser account boundary found. |
| Guest/session handling | Missing | No robust guest isolation/expiry/deletion model found. |
| Locale/language handling | Partial | User profile stores language preferences; voice logging defaults to `en`; no public i18n boundary found. |
| Data retention/privacy boundary | Partial / design-only | Retention fields/docs exist; deletion/export/enforcement not proven. |
| Request concurrency | Partial / risky | Thread-local tenant context is not enough for async browser/public workloads. |
| Rate/load boundary | Missing | No public request quota/load boundary found in inspected scope. |
| Audit logging without private leakage | Partial / risky | Logs exist; redaction/private leakage controls are not complete. |
| Deletion/export/user-data controls | Design-only / missing | Account/data ownership doc defines need; implementation not found. |
| International public users | Not ready | Requires auth, tenant, language, privacy, retention, deletion/export, concurrency, and abuse/load boundaries. |

## Section 7 — Existing Implementation Inventory Summary

Existing implementation found:

- Tenant path utility: `weslr/tenant_context.py`.
- Bootstrap timeline identity foundation: `weslr/bootstrap.py`.
- Channel/profile evidence model: `weslr/channel_identity.py`, `weslr/user_profile.py`.
- Entity-scoped memory and safe capture: `weslr/entity_memory.py`, `weslr/memory_capture.py`.
- Session-keyed artifact active registry: `weslr/artifact_store.py`.
- Voice WebSocket/user timeline routing: `weslr/voice_gateway.py`.
- Some tenant-aware fact/document/frontier/evidence stores.
- Governance/docs for account/tenant/data ownership, public surface readiness, repo hygiene, timeline continuity.

Implemented but insufficient alone:

- Tenant path resolution.
- Access-level memory metadata.
- Channel identity evidence.
- Session ID registries.
- Timeline IDs.

Only designed/documented:

- Full account/tenant/data ownership boundary.
- Public/browser demo hardening.
- Data deletion/export controls.
- User departure and hosted tenant policy.
- Cross-session continuity resolution model.

Missing or not proven:

- Mandatory authenticated browser account/session boundary.
- Mandatory tenant/user/session keys for all stateful stores.
- Central authorization gate for memory/context/artifact/log reads.
- Guest isolation.
- Public upload/material isolation.
- Async-safe request scoping.
- Public privacy/retention/export/delete enforcement.
- Complete load/rate boundary.
- Negative tests proving no tenant/user/session leakage.

## Section 8 — Judgment

Judgment:

`existing_multi_user_isolation_partial_needs_boundary_design_before_public_runtime`

Rationale:

WESLR has meaningful foundations: tenant path resolution, entity memory namespaces, user/profile/channel evidence, bootstrap timeline identity, and strong governance docs. However, these are partial foundations with legacy/global defaults and no single enforced public/browser boundary. The implementation is likely acceptable only for current local/nonpublic/single-operator or carefully controlled internal use. It is not sufficient for public browser or international multi-user runtime.

Because cross-user memory/context leakage risks exist, the required direction is C.

## Section 9 — Direction Check

Direction check:

`C — design MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1 before response-facing authority or public/browser runtime`

Recommended next lane:

`DESIGN_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1`

The next design should define, before any public/browser runtime work:

1. Account/session/tenant/workspace identity model.
2. Required request context object.
3. Mandatory namespace tuple for every state read/write: `(tenant_id, workspace_id, user_id/account_id, session_id, conversation_id)` with explicit nullable rules.
4. Guest/anonymous handling.
5. Artifact/upload/material ownership.
6. Memory/context read authorization.
7. Log/trace redaction and retention.
8. Export/delete/user-data controls.
9. Async-safe context propagation, preferably `contextvars` or explicit request context passing.
10. Negative test matrix for tenant/user/session isolation.
11. Public browser defaults: no global `.weslr`, no `tl_default`, no unauthenticated user_id query routing, no operator panel, no memory writes unless explicitly authorized.

## Section 10 — Safety Check

This audit did not implement behavior, did not edit `weslr/chat_responder.py`, did not inspect or modify live `.weslr` runtime state, did not call providers/models/search/advisors, did not wire runtime, did not add helpers, did not create tests, and did not change chat/user-facing behavior.

