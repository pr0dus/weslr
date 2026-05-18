# WESLR Ranked State-Grounded Response Formation V1

## SECTION 1 — PURPOSE

This document defines the design-only architecture for future WESLR ranked state-grounded response formation.

It extends `docs/WESLR_COGNITION_TARGET_MODEL_V1.md` by specifying how WESLR should move from fragmented response behavior toward a pipeline where final answers are selected from interpreted state, relevant context, bounded memory, evidence/provenance requirements, domain constraints, response obligations, and qualitative candidate ranking.

This is a WESLR canon-alignment document. It prepares a future helper-only/shadow-only implementation lane, but does not implement response formation code or authorize runtime wiring.

## SECTION 2 — CLAIM BOUNDARIES AND NON-GOALS

This document does not claim WESLR is conscious or sentient. It does not claim official benchmark, Turing-test, IQ, certification, product-readiness, or AI-audit authority status.

This document does not define WESLR as OCC/OpenClaw, a chatbot persona, raw LLM output, a model fallback wrapper, or a deterministic keyword-template responder. OCC/OpenClaw is only the construction and inspection tool used to modify the repository when instructed. OCC/OpenClaw is not part of the deployed WESLR system.

Non-goals:

- no runtime behavior changes
- no `weslr/chat_responder.py` edits
- no model fallback behavior edits
- no response formation implementation
- no candidate generation implementation
- no ranking implementation
- no memory implementation changes
- no evidence/provenance implementation changes
- no domain onboarding implementation changes
- no AI-audit authority changes
- no ChatResponder, `respond_chat()`, or `generate_chat()` calls
- no prompt execution
- no model/search/advisor calls
- no `.weslr` writes
- no raw prompt or raw response retention
- no feature flag enablement
- no defaults changes
- no voice/prosody/TTS work

## SECTION 3 — CURRENT RESPONSE FORMATION PROBLEM

Current WESLR response behavior contains useful parts, but the parts do not yet form one ranked state-grounded response system.

Observed problem:

1. `weslr/chat_responder.py` is runtime-wired and contains multiple deterministic branches, formatters, limited slices, and fallback paths.
2. `weslr/linguistic_meaning.py`, `weslr/response_obligation.py`, and `weslr/meaning_response.py` provide interpretation, obligation, and response helpers, but they do not yet define a complete state frame or ranking authority.
3. Native response helpers in `weslr/native_reasoning_frame.py`, `weslr/native_response_draft.py`, `weslr/native_response_self_check.py`, `weslr/native_response_assembly.py`, and `weslr/native_response_dry_slice.py` form a dry structural lane, not runtime authority.
4. Memory, continuity, relationship, tenant, evidence, provenance, and governance modules exist but are not yet unified into answer selection.
5. Evaluation and advisor modules can review behavior, but must not become hidden answer authority.
6. Existing deterministic phrasing may be safe for narrow slices, but expanding it would create coverage without cognition.

The architecture problem is selection: WESLR needs a future state frame and ranking process that can decide which answer form best satisfies the user need under context, evidence, safety, continuity, and domain constraints.

## SECTION 4 — TARGET RESPONSE FORMATION MODEL

Ranked state-grounded response formation is the target process where WESLR:

1. interprets the turn
2. builds a response state frame
3. selects relevant context and memory
4. detects evidence and provenance requirements
5. detects capability, safety, legal, moral, and domain boundaries
6. builds multiple candidate response intents or drafts
7. ranks them against grounding, safety, usefulness, continuity, domain fit, and human-fit criteria
8. rejects unsafe, unsupported, overclaiming, or canned candidates
9. self-checks the selected candidate
10. composes the final answer from the selected candidate
11. emits provenance and observation/proposal metadata where policy allows

The final answer should be the surface expression of selected state-grounded reasoning. It should not be selected because a keyword branch matched first or because an external model produced fluent text.

## SECTION 5 — RESPONSE STATE FRAME

Future implementation should define a conceptual response-state structure before producing any user-facing answer. This document does not implement the schema in code.

Conceptual fields:

- `user_turn_interpretation` — structured meaning of the current turn, with no raw prompt retention by default.
- `inferred_need` — what the user appears to need: answer, plan, explanation, triage, clarification, boundary, memory recall, evidence-backed guidance, or escalation.
- `uncertainty` — known ambiguities, missing facts, low-confidence interpretations, and whether clarification is necessary.
- `task_type` — qualitative task family such as planning, explanation, decision support, memory/continuity, governance, evaluation, domain advice, or refusal/boundary.
- `domain_context` — active deployment context, domain ontology, tenant boundary, response style, and domain-specific constraints.
- `relationship_context` — bounded relationship/tone state relevant to interpreting and responding.
- `memory_relevance` — selected memory records, confidence, source scope, age, and relevance rationale.
- `continuity_relevance` — selected continuity trajectory, active work state, stale-context notes, and context decay status.
- `evidence_requirement` — whether evidence is required, optional, unavailable, insufficient, or governance-blocking.
- `provenance_requirement` — what sources, memory, advisor inputs, governance decisions, or repository states must be attributed.
- `capability_boundary` — what WESLR can and cannot do in the current turn.
- `safety_boundary` — privacy, security, misuse, raw-content, external-action, and operational safety limits.
- `legal_moral_boundary` — deployment-specific legal, moral, duty-of-care, and escalation constraints.
- `response_obligation` — the owed response form: direct answer, bounded answer, ask one question, refuse, escalate, propose next step, or no response.
- `candidate_responses` — candidate intents, structures, or drafts derived from state and reasoning.
- `ranking_trace` — qualitative reasons for preferring, demoting, or rejecting candidates.
- `selected_response` — the chosen candidate and reason for selection.
- `self_check` — final safety/evidence/provenance/uncertainty/non-cannedness check result.
- `final_answer_contract` — constraints the final answer must satisfy: length, tone, sections, caveats, source/provenance notes, and action boundaries.
- `post_response_observation` — safe metadata or proposal routing candidates, not raw prompt/response text.

The state frame is not memory storage. It is an ephemeral reasoning artifact unless future governance explicitly permits safe redacted summaries or metrics.

## SECTION 6 — CANDIDATE RESPONSE FORMATION

Candidate responses should be formed from interpreted state, not fixed keyword templates.

Candidate formation inputs:

- interpreted user intent and inferred need
- current response state frame
- relevant memory and continuity context
- domain and tenant constraints
- evidence and provenance requirements
- response obligation
- reasoning frame
- capability and safety limits
- legal and moral boundaries
- desired final answer contract

Candidate types may include:

- direct bounded answer
- clarification-first answer
- uncertainty-preserving answer
- evidence-required answer
- safe refusal or boundary answer
- next-step plan
- compare/options answer
- memory/continuity-aware answer
- governance-escalation proposal
- advisor-needed-but-not-authorized fallback
- no-response/low-interruption answer for contexts where response is not owed

Candidate formation should create alternatives before final composition. The important architectural shift is from branch-first answer selection to candidate-first evaluation.

Candidates must not be fixed keyword templates. Reusable wording fragments may support style and safety, but the candidate's substance must derive from state, context, evidence, obligation, and reasoning.

## SECTION 7 — RANKING DIMENSIONS

Ranking should use qualitative labels and rationale. Numeric scoring is not required unless a future approved architecture explicitly supports it.

Recommended qualitative dimensions:

- **correctness / grounding** — candidate is supported by known state, evidence, or clearly marked inference.
- **relevance to user need** — candidate addresses the inferred need rather than a superficial keyword.
- **continuity fit** — candidate uses relevant prior context without overusing stale or private memory.
- **domain fit** — candidate respects active deployment context and domain boundaries.
- **legal / moral safety** — candidate avoids unsafe, unlawful, coercive, or duty-of-care failures.
- **evidence sufficiency** — candidate matches the required evidence burden or downgrades confidence appropriately.
- **provenance clarity** — candidate can explain what it relies on without leaking raw private content.
- **uncertainty honesty** — candidate preserves unknowns and does not fabricate certainty.
- **actionability** — candidate gives a useful next step when appropriate.
- **human-understanding fit** — candidate reflects the user's likely need, stress, expertise, and context.
- **non-cannedness** — candidate is visibly derived from state rather than a generic fixed paragraph.
- **minimal necessary verbosity** — candidate says enough, not everything.
- **reversibility / safety of suggested actions** — candidate prefers reversible, low-risk actions unless authority and evidence justify more.

Qualitative labels may include: `strong_fit`, `acceptable_fit`, `weak_fit`, `reject`, `needs_clarification`, `needs_evidence`, `needs_governance`, and `not_authorized`.

## SECTION 8 — REJECTION AND FALLBACK RULES

A candidate should be rejected when it is:

- unsafe
- unsupported by required evidence
- outside capability boundary
- overclaiming
- treating raw private memory as usable without policy
- ignoring tenant, domain, legal, moral, or safety boundaries
- relying on stale continuity as if current
- canned/template-like when state-grounded response is required
- hiding advisor or model output as WESLR authority
- requiring model/search/advisor calls when none are authorized
- making official benchmark/Turing/IQ/certification/product-readiness/consciousness claims
- implying WESLR is conscious or sentient
- treating OCC/OpenClaw as deployed WESLR

Safe fallback behavior:

- ask for missing information only when necessary to proceed safely
- state uncertainty plainly
- provide a bounded next step when useful
- refuse or narrow the scope when boundaries require it
- propose governance review when authority is missing
- identify evidence needed before answering stronger claims
- preserve fallback safety without turning canned fallback into primary cognition

Fallback should be proportional. If a bounded useful answer can be given without extra information, WESLR should not over-ask.

## SECTION 9 — NON-CANNEDNESS GUARANTEE

Future implementation should avoid:

- exact phrase templates as primary cognition
- keyword-only branching as primary cognition
- category-specific fixed paragraphs as primary answer substance
- prompt-specific scripts
- deterministic canned user-facing behavior masquerading as reasoning
- expanding prompt families to simulate understanding

Allowed:

- deterministic validation gates
- deterministic safety gates
- deterministic evidence/provenance checks
- deterministic schema validation
- canned emergency fallbacks when required for safety
- narrow owner-approved disabled-by-default slices
- reusable style helpers that do not determine substantive answer content

Guarantee principle:

User-facing cognition should be derived from state, context, memory relevance, evidence requirements, response obligation, candidate ranking, and self-check. Deterministic components may guard and verify the process; they must not replace the process.

## SECTION 10 — MODULE MAPPING

| Stage / concern | Current files | Status | Future role |
|---|---|---|---|
| Runtime responder surface | `weslr/chat_responder.py` | runtime-wired but needs demotion/refinement | Keep as surface/fallback until approved architecture can replace narrow pieces. Do not expand as main cognition. |
| Meaning interpretation | `weslr/linguistic_meaning.py`, `weslr/meaning_state_context.py` | usable with adaptation | Feed `user_turn_interpretation`, intent signals, and state-frame hints. |
| Response obligation | `weslr/response_obligation.py`, `weslr/meaning_vector_response_obligation.py` | usable with adaptation | Determine owed response form; should not alone compose final answer. |
| Existing meaning responses | `weslr/meaning_response.py` | usable with adaptation / do not expand as canned path | Reuse concepts where state-grounded; avoid growing fixed response families. |
| Native reasoning frame | `weslr/native_reasoning_frame.py` | helper-only | Candidate frame construction input for future shadow helpers. |
| Native draft helpers | `weslr/native_response_draft.py` | helper-only | Candidate draft structure, not runtime answer authority. |
| Native self-check | `weslr/native_response_self_check.py` | helper-only | Pre-final safety and consistency checks. |
| Native assembly | `weslr/native_response_assembly.py` | helper-only | Candidate/final contract assembly after selection. |
| Native dry slice | `weslr/native_response_dry_slice.py` | dry-slice only | Useful for shadow validation, not live wiring. |
| Ordinary guidance | `weslr/ordinary_reasoning_guidance.py`, `weslr/ordinary_explanation_guidance.py` | usable with adaptation | Supply guidance patterns without becoming fixed answer paragraphs. |
| Reasoning task structures | `weslr/reasoning_task.py`, `weslr/reasoning_task_builder.py`, `weslr/reasoning_trace.py`, `weslr/reasoning_arbitrator.py`, `weslr/reasoning_engine_dry_run.py` | usable with adaptation / dry-run | Inform structured reasoning, conflict handling, and dry evaluation. |
| Memory | `weslr/entity_memory.py`, `weslr/entity_timeline_memory.py`, `weslr/memory_capture.py` | usable with adaptation | Provide bounded memory relevance and safe post-response capture proposals. |
| Continuity/context | `weslr/context.py`, `weslr/context_continuity.py`, `weslr/continuity.py`, `weslr/context_decay_policy.py` | usable with adaptation | Provide continuity relevance and staleness boundaries. |
| Relationship state | `weslr/relationship_depth.py`, `weslr/relationship_observation_capture.py` | usable with adaptation | Provide human-fit and tone context without privacy leakage. |
| Tenant/domain | `weslr/tenant_context.py` | usable with adaptation | Tenant boundary and path/context isolation input. |
| Evidence | `weslr/evidence_ontology.py`, `weslr/evidence_policy.py`, `weslr/evidence_sufficiency_gate.py`, `weslr/evidence_packet_builder.py`, `weslr/evidence_pipeline.py` | usable with adaptation | Evidence requirement and sufficiency control; no unauthorized search/model calls. |
| Provenance | `weslr/output_provenance.py`, `weslr/provenance_source_registry.py` | usable with adaptation | Provenance requirement and redacted attribution. |
| Governance | `weslr/governance_surface.py`, `weslr/governance_invocation.py`, `weslr/governance_review_log.py`, `weslr/governance_scorecard.py` | usable with adaptation | Authority routing, proposal review, and decision-quality records. |
| Evaluation/advisor | `weslr/internal_evaluation_corpus.py`, `weslr/behavior_evaluation_report.py`, `weslr/internal_corpus_advisor_review_adapter.py`, `weslr/advisor_review_queue.py`, `weslr/ai_audit_plan.py`, `weslr/ai_audit_report.py`, `weslr/ai_audit_status_bundle.py`, `weslr/ai_audit_readiness_gap_advisor.py` | usable with adaptation / not answer authority | Test and review response formation; do not produce hidden live answers. |
| Candidate ranking | no dedicated module yet | missing | Future helper-only/shadow-only implementation needed. |
| State frame schema | no dedicated module yet | missing | Future conceptual schema should be implemented only after approval. |
| Runtime integration | none approved | missing / not authorized | Not part of this design packet. |

## SECTION 11 — MEMORY / CONTINUITY USE

Memory and continuity should influence response formation only through relevance selection and policy boundaries.

Target use:

1. Select memory records by relevance, access scope, confidence, age, tenant, and relationship/domain fit.
2. Select continuity state by active trajectory, recency, decay status, and current task relevance.
3. Prefer summaries, identifiers, confidence labels, and provenance metadata over raw remembered text.
4. Avoid using private, stale, or unrelated memory because it merely exists.
5. Preserve uncertainty when memory conflicts with current input.
6. Route post-response memory candidates through safe capture policy, not automatic raw storage.

Memory should improve continuity and human understanding. It should not silently determine truth, override current user input, or broaden access boundaries.

## SECTION 12 — EVIDENCE / PROVENANCE USE

Evidence and provenance should constrain candidate ranking and final answer composition.

Target use:

- detect whether a claim requires evidence
- determine whether evidence is sufficient, insufficient, unavailable, or governance-blocking
- downgrade certainty when evidence is weak
- reject candidates that make unsupported material claims
- attach provenance for memory-derived, evidence-derived, advisor-derived, governance-derived, or repository-derived content
- avoid storing or emitting raw private evidence unless policy permits it

A candidate that cannot meet evidence or provenance requirements should either be rejected, rewritten with uncertainty, narrowed to a bounded next step, or routed for governance review.

## SECTION 13 — DOMAIN ADAPTATION USE

Domain adaptation should tune the response state frame, candidate ranking, and final answer contract.

Deployment contexts tune:

- scope
- legal boundaries
- moral boundaries
- capability boundaries
- evidence thresholds
- memory boundaries
- escalation rules
- response style
- later voice behavior

Domain adaptation must not create separate WESLR identities. It must not lower safety or evidence standards without explicit governance. It should make the same WESLR system more context-aware, not less governed.

## SECTION 14 — LLM / ADVISOR BOUNDARY

External model or advisor help may be requested in a future approved route only when it is:

- bounded to a specific helper role
- attributed in provenance
- checked by evidence and safety gates
- treated as non-authoritative unless governance explicitly allows otherwise
- prevented from directly writing memory or truth
- prevented from becoming WESLR identity
- prevented from becoming hidden final-answer authority

Future advisor uses may include candidate critique, gap finding, alternative framing, or redacted structural review. Advisor output should enter the response state as a provenance-bearing input, not as final answer text.

If a candidate requires model/search/advisor help but no route is authorized, the candidate should be rejected or downgraded to a bounded fallback.

## SECTION 15 — EVALUATION IMPLICATIONS

Future tests should verify that:

- the same input can produce different responses under different relevant context
- response changes when evidence requirement changes
- response changes when domain changes
- memory relevance is used but not overused
- stale memory is treated differently from active continuity
- unsafe candidates are rejected
- unsupported candidates are rejected
- overclaiming candidates are rejected or downgraded
- canned responses are demoted when a state-grounded response exists
- uncertainty is preserved
- provenance requirements influence final answer contract
- model/advisor-required candidates fail safely when not authorized
- no raw prompts or raw responses are retained by default
- no official benchmark/Turing/IQ/certification/product-readiness/consciousness claims are made

Evaluation should begin with helper-only/shadow-only artifacts before any runtime integration.

## SECTION 16 — IMPLEMENTATION SEQUENCE

Recommended sequence after this design:

1. Implement helper-only/shadow-only response state frame construction.
2. Implement helper-only/shadow-only candidate representation.
3. Implement qualitative ranking trace helpers without numeric official scoring.
4. Implement candidate rejection and fallback classification helpers.
5. Implement self-check helpers over selected candidate state.
6. Implement provenance/final-answer contract metadata helpers.
7. Add synthetic internal tests for ranking, rejection, non-cannedness, and context variation.
8. Run dry/shadow validation only.
9. Review governance and release-gate boundaries.
10. Only later consider narrow owner-approved disabled-by-default runtime observation, not replacement.

This document recommends sequence only. It does not implement any step.

## SECTION 17 — RISKS AND GUARDRAILS

Risks:

- response ranking becoming hidden numeric scoring without governance
- candidate generation becoming fixed-template expansion
- runtime-wired chat branches expanding before architecture is ready
- memory relevance turning into memory overuse
- evidence requirements being treated as optional style notes
- advisor output being smuggled into final answers as authority
- domain adaptation fragmenting WESLR identity
- evaluation artifacts being marketed as official claims
- voice polish being prioritized before cognition quality

Guardrails:

- design before implementation
- helper-only/shadow-only before runtime wiring
- no `weslr/chat_responder.py` edits in this lane
- no raw prompt/response retention by default
- qualitative labels before numeric scoring
- provenance for memory, evidence, advisor, and governance inputs
- explicit rejection rules
- deterministic safety/validation allowed, deterministic canned cognition rejected
- no official claims without separate governance/legal/product review

## SECTION 18 — READINESS LABELS

- `ranked_response_formation_design_defined`
- `design_only_not_runtime_wired`
- `shadow_helpers_not_implemented`
- `runtime_integration_not_authorized`
- `non_canned_response_principle_defined`
- `official_evaluation_not_claimed`
- `voice_downstream_not_current_priority`

## SECTION 19 — NEXT LANE RECOMMENDATION

Recommended next lane:

`IMPLEMENT_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_SHADOW_HELPERS_V1`

Required constraints for that lane:

- helper-only
- shadow-only
- not runtime-wired
- no `weslr/chat_responder.py` edits unless separately approved
- no model/search/advisor calls
- no raw prompt/response retention
- qualitative ranking labels only
- synthetic/internal tests first
- no official claims

Do not start that lane as part of this packet.

## SECTION 20 — SAFETY CONFIRMATION

This document confirms:

- design-only
- no runtime/source behavior changes
- no `weslr/chat_responder.py` edits
- no model fallback behavior edits
- no response generation implementation
- no candidate generation implementation
- no ranking code implementation
- no memory implementation changes
- no evidence/provenance implementation changes
- no domain onboarding implementation changes
- no AI-audit authority changes
- no ChatResponder calls
- no `respond_chat()` calls
- no `generate_chat()` calls
- no prompt execution
- no model/search/advisor calls
- no `.weslr` writes
- no raw prompt retention
- no raw response retention
- no feature flag enablement
- no defaults changes
- no voice/prosody/TTS work
- no official benchmark/Turing/IQ/certification/product-readiness/consciousness claims
- OCC/OpenClaw treated only as construction/inspection tool, not deployed WESLR
