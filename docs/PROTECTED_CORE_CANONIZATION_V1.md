# PROTECTED_CORE_CANONIZATION_V1

## PURPOSE
- Establish a protected core for WESLR with explicit contracts to remove ambiguity and role leakage.
- Anchor the system around the main-door conversational decision runtime, with clear provider/runtime boundaries, stateless continuity stance, a single improvement/gov lane, and bounded observability.

## CANONICAL CONTRACTS

### Contract #1 — Main-door Chat Contract
- Truth: Chat uses a dedicated runtime entry (generate_chat), not inner-thought; user-facing response is distinct from internal payloads; neutral chat-safe fallback; bounded rescue in controller.
- Owners: ingress_adapter.py (request normalization), weslr/chat_responder.py (chat controller), llm_runtime.py (generate_chat).
- Forbidden: inner-thought JSON/role/wake/prompt/schema leakage; inner-thought fallback text; chain-of-thought; hidden meta.
- Unresolved: Actionability gaps on some prompts; metadata surface for operator not yet wired.

### Contract #2 — Provider / Runtime Contract
- Truth: Role-scoped runtime entries (generate_chat vs generate_inner_thought); provider routing shared but normalization split into _normalize_chat/_normalize_inner; chat_mode honored across providers (ollama/openai/embedded).
- Owners: llm_runtime.py.
- Forbidden: chat using inner-thought fallback/fields; mixed normalization; provider plumbing doing presentation; chain-of-thought exposure.
- Unresolved: Separate prompt builder per role; evidence routing/classification is inner-only; provider live/status not enforced in chat beyond fallback.

### Contract #3 — Continuity / Context Contract
- Truth: Main-door chat is stateless for now. Valid context: request fields + explicit chat_context; hints are helper-only, not continuity/memory.
- Owners: ingress_adapter.py (declares stateless stance), weslr/chat_responder.py (notes hints are non-continuity helpers).
- Forbidden: silent use of continuity.py/sim.py/concept_graph/request_intelligence/world.db as continuity; implying persistence where none exists.
- Unresolved: Choosing and wiring a canonical continuity source (if desired) with an explicit truth-order.

### Contract #4 — Improvement / Governance Contract
- Truth: Single sanctioned lane = adequacy → CDI proposal (with lineage/evidence) → operator approve/deny/refine → execution eligibility only after approval. Proposal-only; operator-gated.
- Owners: weslr/cognitive_dialogue_integration.py (declares lane); adequacy/lineage referenced; operator decision central.
- Forbidden: self_mod* as core; autonomous approval/execution; lineage-free proposals as canonical.
- Unresolved: Wiring adequacy/CDI into flows; approval persistence/audit; apply path; mandatory lineage enforcement.

### Contract #5 — Observability Contract
- Truth: Bounded operator-safe metadata defined (path, provider, fallback_used, rescue_used, continuity_stance=stateless, governance_lane=CDI_proposal_only, lineage_attached flag). User content stays clean.
- Owners: weslr/chat_responder.py (metadata shape), llm_runtime.status/health as source for provider info.
- Forbidden: chain-of-thought/internal payloads/prompts/evidence dumps; transcripts as operator truth.
- Unresolved: Actual operator surface to consume metadata; lineage_attached integration when CDI proposals flow; richer observability not yet wired.

## PROTECTED CORE MODULES
- llm_runtime.py (runtime/provider boundary, role separation)
- weslr/chat_responder.py (chat contract, rescue, operator-safe metadata)
- weslr/ingress_adapter.py (stateless normalization)
- weslr/cognitive_dialogue_integration.py (canonical improvement lane declaration)
- weslr/main_door_test_runner.py (runner tool; not core logic but kept with contract set)

## DEMOTED / LEGACY / EXPERIMENTAL MODULES
- self_mod_applier.py (legacy/experimental; not canonical improvement lane)
- self_modifier.py (legacy/experimental; not canonical improvement lane)
- continuity.py, sim.py, concept_graph, request_intelligence, world.db continuity usage (experimental/dormant for continuity)
- Transcript/test runner artifacts (debug-only, non-canonical observability)

## FORBIDDEN DRIFT ZONES
- Do not reintroduce inner-thought fallback/text into chat path.
- Do not imply continuity/memory without explicit canonical source.
- Do not treat self_mod* as protected-core improvement.
- Do not expose chain-of-thought/prompts/evidence dumps in observability.
- Do not add parallel proposal lanes or autonomous approval.

## REMAINING OPEN ITEMS
- Actionability gaps on some chat prompts (neutral fallback still appears).
- Separate prompt builder per role; enforce provider live/status for chat.
- Select and wire a canonical continuity source (if desired) with truth-order.
- Wire adequacy/CDI/lineage into flows; approval persistence/audit; apply path.
- Implement operator-facing observability surface to consume bounded metadata; integrate lineage_attached when CDI proposals flow.

## NEXT SAFE ARCHITECTURAL STEP
- Wire the bounded operator-safe metadata to an operator surface (not user chat), and enforce provider live/status for chat—while keeping continuity stateless and governance lane unchanged.
