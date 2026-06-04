# WESLR Implemented Architecture Component Map V1

This map is intentionally compact and status-driven. It names the most important architecture groups, what they do, and how mature they are.

## Legend

- `implemented_runtime` — actively wired into the current runnable shell
- `implemented_helper_boundary` — real code exists, but the main role is gating, metadata, or helper behavior
- `implemented_metadata_only` — review/design artifact or metadata packet, no runtime authority
- `design_only` — architecture exists in docs/spec only
- `review_only` — implementation exists only as a reviewed artifact or review lane result
- `context_only` — carried in memory/context files or session provenance, not an integrated feature
- `not_integrated` — present as a concept or file family, but not yet coherently tied into product flow
- `experimental_or_historical` — useful evidence, but not canonical runtime shape

## Component map

| Component group | Key files / document families | Status | Role / purpose | User-facing? | Integrated? | Dependencies / adjacent systems | Risks / limitations / next questions |
|---|---|---:|---|---|---|---|---|
| Core runtime / shell | `main.py`, `weslr/chat_responder.py`, `chat_ui.py`, `dialogue.py`, `weslr/README.md` | `implemented_runtime` | Live shell, chat entry, UI/dialogue path, command runtime | Yes | Partly integrated | config, llm runtime, routing, guards | Runtime still broader than unified cognition; shell can outrun deeper architecture |
| Memory / continuity / time | `weslr/continuity.py`, `weslr/context.py`, `weslr/context_continuity.py`, `weslr/entity_memory.py`, `weslr/entity_timeline_memory.py`, `weslr/decision_memory.py`, `weslr/memory_capture.py`, `weslr/architecture_memory.py` | mixed: `implemented_helper_boundary` + `implemented_metadata_only` | Scoped continuity, state capture, timeline memory, memory honesty | Mostly internal | Partly integrated | provenance, source scope, session context | Not yet a single unified memory engine; persistent identity remains bounded |
| Retrieval / RAG / provenance | `weslr/rag_query_routing_boundary.py`, `weslr/safe_memory_retrieval_executor.py`, `weslr/evidence_*`, `weslr/artifact_provenance_boundary.py`, `weslr/document_access_pii_boundary.py`, `docs/WESLR_RAG_QUERY_ROUTING_AND_RETRIEVAL_BOUNDARY_V1.md` | `implemented_helper_boundary` | Routes evidence before answer use; protects access and provenance | Mostly internal | Partly integrated | memory, source registries, poison shield | Routing exists, but retrieval/grounding remains boundary-heavy |
| Safety / poison shield / authority | `weslr/poison_shield.py`, `weslr/action_authority_boundary.py`, `weslr/answer_authority_boundary.py`, `docs/WESLR_POISON_SHIELD_ADVERSARIAL_CONTENT_QUARANTINE_AND_AUTHORITY_FIREWALL_V1.md` | `implemented_helper_boundary` | Quarantine adversarial content; keep evidence distinct from authority | Mostly internal | Partly integrated | routing, memory, final-answer boundaries | Strong doctrine; needs continued enforcement as system grows |
| Controlled answer formation / composition | `weslr/controlled_answer_formation_execution.py`, `weslr/controlled_answer_composition.py`, `weslr/controlled_final_answer_generation.py`, `weslr/controlled_reply_text.py`, `weslr/controlled_reply_preview.py`, `docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_BOUNDARY_V1.md` | mostly `implemented_helper_boundary` | Separates internal composition metadata from user-facing answers | Limited/indirect | Partly integrated | runtime shell, validation, authority gates | Good separation, but not yet a single end-user answer pipeline |
| Tool use / execution / validation | `weslr/controlled_local_runtime_adapter.py`, `weslr/controlled_local_runtime_guards.py`, `weslr/autonomous_debugging_dry_run_boundary.py`, `weslr/friction_*`, `weslr/behavior_evaluation_report.py`, `weslr/ai_audit_*`, test harnesses | mixed: `implemented_runtime` + `implemented_helper_boundary` | Propose, validate, rehearse, gate, and record execution | Internal mostly | Partly integrated | tests, release gate, runtime shell | Fragmentation across dry-run / rehearsal / execution still visible |
| Release-gate / governance | `weslr/tests/release_gate_v1.py`, `weslr/tests/public_readiness_tests.py`, `weslr/launch_*`, `weslr/governance_*`, `docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_V1.md` | `implemented_runtime` + `implemented_helper_boundary` | Prevent drift, preserve exact-file control, keep approvals narrow | Internal | Yes/partly | repository state, protected-file scans | Needs continued exact-file discipline; broad allowlists are a known hazard |
| Evidence / claims / source truth | `weslr/evidence_*`, `weslr/fact_extractor.py`, `weslr/fact_query_bridge.py`, `weslr/evidence_policy.py`, `weslr/evidence_sufficiency_gate.py` | `implemented_helper_boundary` | Ground claims in source evidence and policy | Mostly internal | Partly integrated | RAG routing, provenance, public claim policy | Evidence graph exists, but truth-to-answer path is still disciplined and segmented |
| Voice / speech / signal quality | `weslr/mfcc_feature_quality_metadata.py`, `weslr/reaction_time_latency_budget_helper.py`, `weslr/speech_quality_packet.py`, `weslr/ambient_voice_*`, related tests/reviews | `implemented_helper_boundary` | Signal-quality metadata, not voice authority | Mostly internal | Partly integrated | review docs, test harness, boundary docs | Good metadata discipline; not a runtime speech intelligence engine |
| Product shell / pilot readiness | `weslr/PILOT_COHORT.md`, `weslr/PILOT_DAY0_REPORT.md`, `weslr/PILOT_LAUNCH_RUNBOOK.md`, `weslr/PUBLIC_TEST_DEPLOYMENT.md` | `implemented_runtime` + `experimental_or_historical` | Public-test and pilot framing, controlled deployment prep | Yes/mostly | Partly integrated | profiles, logging, operator workflow | Pilot readiness exists, but it is still constrained and not a broad 50-user operating model |
| Internal canon / identity / context | `SOUL.md`, `IDENTITY.md`, `MEMORY.md`, `AGENTS.md`, `docs/*review*`, `docs/*design*` | `context_only` + `review_only` | Narrative continuity, operator memory, long-term doctrine | No | Indirect | session context, memory files | Rich context, but easy to confuse with runtime capability if not classified carefully |
| Broad topic / concept ontology | `weslr/broad_topic_ontology.py`, `weslr/broad_topic_domain_intake.py`, `docs/WESLR_BROAD_TOPIC_ONTOLOGY_LAYER_V1.md` | `implemented_helper_boundary` | Domain routing and intake concept mapping | Mostly internal | Partly integrated | cognitive routing, domain intake | Good scaffolding; not yet a universal answer planner |
| Adaptive / self-improvement / governance review | `weslr/adaptive_guidance.py`, `weslr/auto_refinement.py`, `weslr/change_proposals.py`, `weslr/governance_surface.py`, `weslr/self_improvement_*` | mixed: `implemented_runtime` + `implemented_helper_boundary` + `experimental_or_historical` | Controlled change proposals, approval flow, self-improvement discipline | Internal | Partly integrated | operator workflow, tests, proposals | Must remain gated; no silent self-modification authority |
| Evaluation / rehearsal / synthetic corpora | `weslr/cognitive_gym_*`, `weslr/friction_*`, `weslr/internal_evaluation_*`, `weslr/tests/*rehearsal*`, `weslr/tests/*synthetic*` | `implemented_helper_boundary` | Rehearse failures, mine gaps, compare controlled cases | Internal | Partly integrated | validation, review lanes, registry docs | Strong learning substrate, but still mostly internal and synthetic |

## Component notes by status

### `implemented_runtime`
These are already part of the runnable system. They matter most for immediate user experience and operational reliability.

### `implemented_helper_boundary`
These are real and important, but they mainly protect boundaries, encode metadata, or support controlled reasoning rather than freely acting as product intelligence.

### `implemented_metadata_only`
These are valid architecture artifacts, but their role is to describe or validate behavior, not perform it.

### `design_only` / `review_only`
These help the project remember where it wants to go. They are architectural evidence, not current runtime capability.

### `context_only`
These preserve continuity of the project and operator memory. They matter, but they are not the same as production feature wiring.

### `experimental_or_historical`
These are useful, but they should not be mistaken for canonical product shape unless later lanes explicitly promote them.

## Biggest component questions still open

1. Which helper boundaries should become first-class runtime services versus stay internal?
2. How much of continuity should be read-only metadata versus lived state?
3. What is the smallest coherent product shell that still feels like one intelligence?
4. How should tool use be surfaced so it feels checked rather than theatrical?
5. What identity signals are safe to preserve across sessions without authority drift?
6. Which pilot/public surfaces should be considered product shell, and which remain operator scaffolding?
7. How should 50-user readiness be defined without jumping too early into complex proto-cognitive layers?
