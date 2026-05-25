# WESLR Existing Implementations Multi-User Boundary Audit V1

## Status

- Audit label: `AUDIT_EXISTING_IMPLEMENTATIONS_MULTI_USER_BOUNDARY_V1`
- Document path: `docs/WESLR_EXISTING_IMPLEMENTATIONS_MULTI_USER_BOUNDARY_AUDIT_V1.md`
- Lane status: audit-only / inventory-review
- Scope: existing tracked WESLR implementations checked against `DESIGN_MULTI_USER_SESSION_TENANT_ISOLATION_BOUNDARY_V1`
- Runtime status: no runtime wiring
- Chat status: no chat/user-facing behavior changes
- Implementation status: no behavior implementation, no helper implementation, no source/runtime/test changes except narrow release-gate exact-file allowance if needed
- Persistence status: no `.weslr` runtime-state reads/writes performed by this audit
- Provider/search/advisor status: no provider/model/search/advisor calls
- Forbidden path check: `weslr/chat_responder.py` must remain untouched
- Audit judgment: `existing_implementations_need_multi_user_retrofit_before_public_browser_runtime`

This report audits existing tracked implementation files and design/helper documents against the multi-user/session/tenant isolation boundary. It does not change runtime behavior, does not authorize public/browser use, does not implement guards, and does not grant response-facing authority.

## 1. Inventory Table

| Path | Purpose | Stores/reads memory/context/artifacts/uploads/logs/caches? | Explicit tenant/user/session/conversation scope? | Runtime-facing or helper-only? | Current risk label |
|---|---|---:|---|---|---|
| `weslr/cognitive_gym_exploratory_case.py` | Shared exploratory case metadata helpers | No runtime storage; blocks `.weslr`/raw/provider/runtime markers | No owner namespace because pure metadata input | helper-only, import-safe, in-memory | `safe_metadata_only_not_runtime_wired` |
| `weslr/calibration_ledger_exploratory_helpers.py` | CALIBRATION_LEDGER metadata adapter into Cognitive Gym case shape | No runtime storage; blocks `.weslr`/raw/provider/runtime markers | No owner namespace because pure metadata input | helper-only, in-memory | `safe_metadata_only_not_runtime_wired` |
| `docs/WESLR_REASONING_SUBSTRATE_MAP_V1.md` | Design map for reasoning substrate layers | No storage; design-only | Namespaces are conceptual only | design-only | `safe_metadata_only_not_runtime_wired` |
| `docs/WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1.md` | Design for source/trust/evidence separation | No storage; design-only | Conceptual source/provenance boundaries, not implementation | design-only | `safe_metadata_only_not_runtime_wired` |
| `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md` | Design for candidate-response metadata before final answer assembly | No storage; design-only | Conceptual; requires context/memory boundary upstream | design-only | `safe_metadata_only_not_runtime_wired` |
| `weslr/answer_formation.py` | Deterministic answer-formation artifact metadata helpers | No runtime persistence by design; rejects final answer/runtime/provider markers | No owner namespace required while kept synthetic/metadata-only | helper-only | `safe_if_kept_helper_only` |
| `weslr/ranked_state_grounded_response_shadow.py` | Ranked response shadow artifact inspection helpers | No persistence; raw/final/runtime/provider flags rejected | No owner namespace required while synthetic/shadow-only | helper-only / shadow-only | `safe_if_kept_helper_only` |
| `weslr/tenant_context.py` | Thread-local tenant context and tenant path resolver | Resolves persistent paths and creates tenant dirs | Has optional `tenant_id`; falls back to legacy global workspace `.weslr` | utility used by runtime-adjacent stores | `needs_namespace_guard_before_runtime_use` |
| `weslr/document_ingestor.py` | Document ingestion and fact-store path resolution | Reads documents; writes document/fact JSONL stores when invoked | Uses `resolve_path`, but explicit path overrides can bypass tenant root | runtime-adjacent store helper | `needs_authorization_guard_before_read` |
| `weslr/fact_extractor.py` | Fact extraction and fact JSONL persistence helpers | Reads/writes `.weslr/fact_assertions.jsonl`; caches domain patterns | Optional `tenant_id`; default resolves through current/legacy tenant | runtime-adjacent store helper | `needs_namespace_guard_before_runtime_use` |
| `weslr/modules/frontier_store.py` | JSONL frontier proposal store | Reads/writes `.weslr/frontier_proposals.jsonl`; has write lock | Uses `tenant_id` or current tenant or `default`; no account/session/workspace auth | runtime-adjacent store | `needs_authorization_guard_before_read` |
| `weslr/search_adapters/evidence_packet_store.py` | External evidence packet JSONL store | Reads/writes `.weslr/external_evidence_packets.jsonl` | Tenant-aware path in inspected baseline, but no central read authorization proven | runtime-adjacent evidence store | `needs_authorization_guard_before_read` |
| `weslr/artifact_store.py` | Persistent artifacts and active artifact registry | Writes/reads `continuity/artifacts/`; active registry JSON | Artifact records lack required owner tuple; active pointer keyed only by `session_id` | runtime-adjacent artifact store | `needs_upload_or_artifact_owner_scope` |
| `weslr/cross_session_artifact_eval.py` | Cross-session artifact continuity evaluation | Creates/uses artifact eval records and active artifact pointers | Uses synthetic `user_id`/`session_id`, but proves session/user-key risk surface | eval/runtime-adjacent | `needs_upload_or_artifact_owner_scope` |
| `weslr/chat_hints.py` | Process-global hints keyed by `(workspace_id, user_id)` | In-memory cache | `user_id` required for add/set, but `workspace_id` can be `None`; no tenant/session/conversation | runtime-adjacent process cache | `needs_cache_or_log_scoping` |
| `weslr/bootstrap.py` | Bootstrap/timeline identity foundation | Process-global `_BOOTSTRAP_RECORDS`, `_BOOTSTRAP_BY_TIMELINE`; writes communicator state in some paths | Uses `user_id` and `timeline_id`, not tenant/account/session namespace; in-memory stub | runtime-adjacent identity foundation | `needs_authorization_guard_before_read` |
| `weslr/channel_identity.py` | Channel/profile binding evidence model | Reads global profile/binding JSON under default home | Has `bound_user_id` and `session_id` evidence, but default path is one global home | runtime-adjacent identity helper | `needs_authorization_guard_before_read` |
| `weslr/user_profile.py` | User profile and membership claims | Reads/writes profile JSON under default global home | Has `user_id`, language prefs, membership claims; no tenant/account/session auth | runtime-adjacent profile helper | `needs_authorization_guard_before_read` |
| `weslr/entity_memory.py` | Entity-scoped memory records | Reads/writes memory records under default global home | Entity/user/access metadata exists; no central read enforcement found | runtime-adjacent memory store | `needs_authorization_guard_before_read` |
| `weslr/memory_capture.py` | Conservative memory-capture candidates | Avoids raw logging; emits candidate metadata | Has identity-state metadata but not a central authorization guard | helper/runtime-adjacent | `safe_if_kept_helper_only` |
| `weslr/context.py` | Context/injection validation structures | Builds context metadata; no inspected public storage | Has `session_id` requirement in local validation, not full namespace tuple | runtime-adjacent context helper | `needs_namespace_guard_before_runtime_use` |
| `weslr/continuity.py` | Session continuity snapshots | Writes/reads continuity snapshots when invoked | Uses `session_id`, not tenant/account/conversation/workspace namespace | runtime-adjacent continuity store | `needs_namespace_guard_before_runtime_use` |
| `weslr/unified_continuity.py` | Unified continuity helpers | Context/continuity helper surface | Needs owner-scope verification before public runtime | runtime-adjacent continuity helper | `inconclusive_needs_followup` |
| `weslr/user_timeline_memory.py` | User timeline memory structures | Timeline/memory-oriented | User-scoped naming exists, but no complete auth boundary proven | runtime-adjacent memory helper | `needs_authorization_guard_before_read` |
| `weslr/entity_timeline_memory.py` | Entity timeline memory structures | Timeline/memory-oriented | Entity scope exists; owner/tenant/session authorization not proven | runtime-adjacent memory helper | `needs_authorization_guard_before_read` |
| `weslr/voice_gateway.py` | Browser voice WebSocket gateway and timeline logging | Calls `/chat`; writes `.weslr/timelines/<timeline_id>/events.jsonl` transcripts/responses | Query-string `user_id` routing; fallback `tl_default`; no account/session auth | runtime-facing | `blocked_for_public_browser_runtime` |
| `weslr/omnichat/ephemeral_context.py` | In-memory one-turn follow-up context | Process memory only | Per instance only; explicitly thread-unsafe single-session design | runtime-adjacent chat helper | `needs_cache_or_log_scoping` |
| `weslr/advisor_review_queue_persistence.py` | Explicit-path review queue JSONL persistence schema/helpers | Reads/writes only explicit queue paths if called | Path policy includes local/default `.weslr` path; no tenant/account read guard by itself | persistence helper | `safe_if_kept_helper_only` |
| `weslr/commands/documents.py` | CLI document/fact listing | Reads `.weslr/documents.jsonl` and `.weslr/fact_assertions.jsonl` | Uses module-level repo `.weslr` path; no tenant/account/session auth | CLI/runtime-adjacent | `needs_authorization_guard_before_read` |
| `weslr/commands/evidence.py` | CLI evidence packet/fact handling | Reads/writes `.weslr` paths | No public namespace boundary found in command default paths | CLI/runtime-adjacent | `needs_authorization_guard_before_read` |
| `weslr/commands/frontier_commands.py` | Frontier proposal command handlers | Reads/writes tenant frontier stores, novelty caches | Defaults `tenant_id="default"`; no account/session/workspace auth | command/runtime-adjacent | `needs_namespace_guard_before_runtime_use` |
| `weslr/commands/advanced_commands.py` | Advanced reasoning command caches | Process-global `_TENANT_*` stores | Tenant-keyed, but no account/session/conversation namespace or universal locks | command/runtime-adjacent | `needs_cache_or_log_scoping` |
| `weslr/commands/causality_commands.py` | Causality command sessions | Process-global `_USER_SESSIONS` | User-keyed, not tenant/account/session authorized | command/runtime-adjacent | `needs_cache_or_log_scoping` |
| `weslr/commands/quantum_commands.py` | Per-user/session quantum command state | Process-global `_USER_STATES` | User/session convenience key, not full namespace/auth | command/runtime-adjacent | `needs_cache_or_log_scoping` |
| `weslr/security.py` | Token/session in-process security helpers | Process-global token stores | Session-token keyed; not audited as complete browser account boundary | runtime-adjacent | `inconclusive_needs_followup` |
| `weslr/project_registry.py` / `weslr/project_query_handler.py` | Project registry/fact query stores | `.weslr/project_registry.jsonl`, `.weslr/fact_assertions.jsonl`; active project store | Project IDs exist but tenant/account/session authorization not universal | runtime-adjacent project context | `needs_authorization_guard_before_read` |
| `weslr/arbiter_context_builder.py` / `weslr/continuity_note_chat_bridge.py` | Timeline-derived context builders | Reads `.weslr/timelines` defaults | Defaults such as `user_id="arthur"`; no public auth boundary | runtime-adjacent context reader | `blocked_for_public_browser_runtime` |
| `weslr/consolidation_loop.py` / `weslr/consolidation_config.py` / `weslr/consolidation_promotion.py` | Memory consolidation config/loop/audit | Reads/writes home `.weslr` consolidation state | Operator/local root defaults; no tenant/account/session guard | background/runtime-adjacent | `blocked_for_public_browser_runtime` |
| `weslr/proactive_daemon.py` / `weslr/frontier_daemon.py` | Background daemon state/dedupe | Process-global cache and `.weslr` daemon state | No public request namespace in default daemon state | background/runtime-adjacent | `needs_cache_or_log_scoping` |
| `weslr/evals/run_conversation_eval.py` | Conversation eval outputs | Writes `.weslr/eval_results/conversation` | Eval-only, but not owner-scoped for public runtime | eval helper | `safe_if_kept_helper_only` |

## 2. Prior Implementation Impact

### Shared Cognitive Gym exploratory case helpers

Status: safe now as metadata-only, helper-only, deterministic, in-memory infrastructure. The helper explicitly blocks raw private content, hidden prompts, provider/model/search/advisor output, runtime output, `.weslr` IO indicators, final answer text, scoring/judging, and authority claims. It does not need tenant/user/session namespace while it remains pure metadata transformation over caller-supplied bounded records.

Impact if later wired: any runtime caller must wrap records with the multi-user namespace tuple before using private observations, uploads, memory, conversation history, or evidence as input. Otherwise the helper could safely preserve an already-leaked or wrongly-scoped input record.

Risk label: `safe_metadata_only_not_runtime_wired` now; `needs_namespace_guard_before_runtime_use` if connected to real user material.

### CALIBRATION_LEDGER exploratory helpers

Status: safe now as metadata-only adapter from bounded calibration labels into the reviewed Cognitive Gym shape. It is not a score, judge, official evaluator, or response generator.

Impact if later wired: calibration records must be scoped by tenant/account/session/conversation/problem context before any persistence or cross-run learning. Public/browser use must prevent one user's outcomes, mismatch labels, or lessons from affecting another user's response unless an explicit aggregate/anonymized policy exists.

Risk label: `safe_metadata_only_not_runtime_wired` now; `needs_namespace_guard_before_runtime_use` if persisted or connected to user-specific calibration.

### Reasoning substrate map

Status: design-only and safe. It correctly says context/memory trust and evidence boundaries must precede real-text conversation testing and response formation.

Impact: the map now needs to carry the multi-user namespace requirement as a prerequisite for any context/memory/evidence layer in public/browser mode.

Risk label: `safe_metadata_only_not_runtime_wired`.

### Context/memory trust and evidence boundary

Status: design-only and safe. It separates current user turn, conversation history, uploads, explicit memory, inferred memory, repo context, external evidence, and model assumptions.

Impact: it must now be interpreted as owner-scoped. Source category labels are insufficient unless each source is also authorized for the current tenant/account/session/conversation/workspace.

Risk label: `safe_metadata_only_not_runtime_wired`.

### Candidate response formation substrate

Status: design-only and safe. It does not generate final answers or sendable text.

Impact: candidate formation must not consume memory/context/evidence without explicit owner/session/tenant scope. Candidate records should include namespace summary and authorization status before ranking or rejection.

Risk label: `safe_metadata_only_not_runtime_wired`.

### Tenant/memory/timeline/profile artifacts found

Status: partial foundations exist but are not public-browser safe. Tenant utilities, profiles, channel identity, entity memory, document/fact/frontier stores, artifact registry, timeline readers, and voice logging all contain useful pieces; however, defaults and read paths remain local/operator/global in multiple modules.

Impact: before any public/browser runtime, these must be retrofitted with mandatory namespace construction, central authorization-before-read, owner-scoped artifact/upload registries, scoped caches/logs, async-safe request context, and deletion/export/retention enforcement.

Risk label: mixed, dominated by `needs_authorization_guard_before_read`, `needs_namespace_guard_before_runtime_use`, `needs_upload_or_artifact_owner_scope`, and `blocked_for_public_browser_runtime` for voice/timeline/default-reader paths.

## 3. Multi-User Retrofit Requirements

Before public/browser use, WESLR needs the following exact requirements implemented and reviewed in separate lanes:

1. Namespace schema helper: a canonical `namespace_v1` object with `tenant_id`, `account_id`, `user_id`, `guest_id`, `session_id`, `conversation_id`, `workspace_id`, `project_id`, `artifact_id`, `upload_id`, `memory_scope_id`, `locale`, and `language`, plus deny-by-default nullable-field rules.
2. Central read authorization helper: one guard that authorizes reads before any memory/context/artifact/upload/log/cache/evidence/project/profile/timeline access, not only before writes.
3. Scoped memory/context read adapter: all entity memory, profile, timeline, conversation, continuity, fact, document, and evidence reads must pass through owner-scoped adapters.
4. Scoped artifact/upload registry: artifact and upload retrieval must require owner metadata and authorization; `artifact_id` or `session_id` alone must never retrieve private material.
5. Cache/log/trace scoping: every cache, hint store, daemon state, queue, log, trace, transcript, and eval output must include namespace keys or be explicitly local/operator-only.
6. Leakage negative tests: tenant A cannot read tenant B memories, facts, documents, proposals, artifacts, queues, logs, hints, transcripts, uploads, or traces; user A cannot resolve user B's “this”.
7. Guest/session boundary: guests need explicit guest IDs, isolated tenant/session/conversation scopes, expiry, deletion, no memory promotion without consent/account creation, and no authenticated-user inheritance.
8. Account/auth boundary: query-string `user_id`, display names, profile claims, channel IDs, and session IDs must not authorize reads without authenticated account/session binding.
9. Deletion/export/retention controls: user/profile/memory/upload/artifact/log/fact/evidence stores need export/delete/tombstone/expiry paths and retention policy enforcement.
10. Async-safe request context: thread-local tenant state is insufficient for async public runtime; use explicit request context or `contextvars` with cleanup and write-lock discipline.
11. Public runtime defaults: no global `.weslr`, no `tl_default`, no global default profile home, no operator repo context, no private docs, no unscoped daemon state, no public memory writes by default.
12. Locale/language scoping: language and locale preferences must be account/session/conversation-scoped and cannot leak into other users' responses.

## 4. Safe Status

Safe now because design-only or metadata-only:

- `docs/WESLR_REASONING_SUBSTRATE_MAP_V1.md`
- `docs/WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1.md`
- `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`
- `weslr/cognitive_gym_exploratory_case.py`
- `weslr/calibration_ledger_exploratory_helpers.py`
- `weslr/answer_formation.py`, `weslr/ranked_state_grounded_response_shadow.py`, and similar response-shadow helpers only while they remain synthetic/helper-only and not runtime-wired

Unsafe if connected to public/browser runtime without guards:

- Global `.weslr` profile/channel/entity/fact/project/evidence/document/timeline defaults.
- `tl_default` voice timeline fallback.
- Query-string `user_id` as identity.
- Session-only active artifact registry.
- Global artifact files under `continuity/artifacts/` without owner metadata.
- Process-global mutable stores such as bootstrap records, hints, command sessions/states, tenant reasoner caches, daemon dedupe state, provider/config caches, and default in-memory stores.
- Timeline/context readers with default users or default timeline roots.
- Logs/traces/transcripts/responses written without owner namespace, redaction, retention, export, and deletion controls.

Must not be wired yet:

- Public/browser final response assembly using memory/context/evidence.
- Candidate response formation using real user memory or uploaded material.
- Voice/browser `/chat` use for arbitrary public users.
- Artifact/upload reference resolution for “this”, “previous”, or active artifact pointers.
- Cross-user calibration, learning, consolidation, daemon, queue, or cache behavior.
- Any path that reads operator repo/private `.weslr` state for public users.

## 5. Direction Check

Direction check: `C — design multi-user retrofit plan before response-facing authority checkpoint`

Rationale: many existing runtime-adjacent modules lack mandatory namespace/read guards, especially profile/channel/entity memory defaults, artifact/session registry, timeline/voice logging, document/fact/evidence stores, command caches, daemons, and context readers. The response-facing authority/claim checkpoint should carry this audit forward, but a multi-user retrofit plan should come first if public/browser runtime remains the goal.

Recommended next lane:

`DESIGN_MULTI_USER_RETROFIT_PLAN_BEFORE_RESPONSE_FACING_AUTHORITY_CHECKPOINT_V1`

## 6. Safety Check

This audit did not implement behavior, did not edit runtime/chat/voice/UI behavior files, did not edit implementation source files other than a narrow release-gate exact-file allowance if needed, did not inspect or modify live `.weslr` runtime state, did not call providers/models/search/advisors, did not wire runtime, did not create tests, did not change `weslr/chat_responder.py`, and did not change chat/user-facing behavior.
