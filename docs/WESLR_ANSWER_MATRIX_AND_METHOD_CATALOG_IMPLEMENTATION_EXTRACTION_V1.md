# WESLR Answer Matrix and Method Catalog Implementation Extraction V1

**Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`  
**Branch:** `master`  
**Scope:** discovery/extraction only; no runtime wiring, no model/provider calls, no `.weslr` writes

## 1. Executive truth

### What concrete answer/matrix/catalog designs exist

Found concrete helper/code surfaces for:
- ranked state-grounded response formation
- candidate response formation substrate
- unified response formation canon
- response fit engine
- real-answer quality observation
- evaluation matrix case registry
- controlled real-answer sample run / approval helpers
- unknown engine metadata-only boundary
- targeted response formation improvement helpers
- ordinary reasoning guidance
- reasoning task / trace / arbitrator
- behavior evaluation / Turing-style readiness (design-only)

### What is only doctrine

These are design/canon documents without dedicated runtime implementation here:
- `docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md`
- `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`
- `docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md`
- `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`
- `docs/WESLR_REAL_ANSWER_QUALITY_OBSERVATION_BOUNDARY_V1.md`
- `docs/WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1.md`
- `docs/WESLR_BENCHMARK_REASONING_ENGINE_V1.md`
- `docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md`
- `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`
- `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`
- `docs/RESPONSE_GENERATION.md`
- `docs/REUSABLE_RESPONSE.md`
- `docs/LIVE_BEHAVIOUR.md`
- `docs/ORDINARY_TASK_CONTEXT.md`
- `THOUGHT-DYNAMICS.md`
- `WORLD-MODEL.md`
- `grammar.md`
- `vocabulary.md`

### What is already helper-coded

Implemented helper/file surfaces exist for:
- `weslr/native_reasoning_frame.py`
- `weslr/native_response_draft.py`
- `weslr/native_response_self_check.py`
- `weslr/native_response_assembly.py`
- `weslr/native_response_dry_slice.py`
- `weslr/meaning_response.py`
- `weslr/response_obligation.py`
- `weslr/linguistic_meaning.py`
- `weslr/ordinary_reasoning_guidance.py`
- `weslr/response_fit_engine_helpers.py`
- `weslr/real_answer_quality_observation_helpers.py`
- `weslr/evaluation_matrix_case_registry_helpers.py`
- `weslr/run_controlled_real_answer_sample_run_approval_helpers.py`
- `weslr/controlled_real_answer_sample_run.py`
- `weslr/controlled_unknown_engine_metadata_shadow_runner.py`
- `weslr/ranked_state_grounded_response_shadow.py`
- `weslr/ranked_response_shadow_evaluation_report.py`
- `weslr/ranked_response_shadow_evaluation_scenarios.py`
- `weslr/frontier_intelligence_preview_surface.py`
- `weslr/targeted_response_formation_improvement.py`
- `weslr/reasoning_task.py`
- `weslr/reasoning_task_builder.py`
- `weslr/reasoning_trace.py`
- `weslr/reasoning_arbitrator.py`

### What should be coded first

Not a generic live adapter. First should be the method/catalog layer that turns designed answering families into structured, selectable records.

### What should wait

Wait on:
- live chat runtime adapter
- provider/model/search/advisor wiring
- external tester exposure
- any path that treats helper metadata as final answer authority
- any direct patch to `chat_responder.py`, `main.py`, `dialogue.py`, or `chat_ui.py`

### Missing docs

Could not find:
- `docs/WESLR_SCIENTIFIC_CAPABILITY_DISCOVERY.md`
- `docs/WESLR_SCIENTIFIC_DISCOVERY_IMPLEMENTATION.md`

## 2. Matrix inventory

| Matrix-like design | File / docs | Purpose | Cases / categories | Measures or selects | Code exists | Tests exist | Runtime / eval / both |
|---|---|---|---|---|---|---|---|
| Answer matrix | no dedicated file found; implied by `WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md`, `WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`, `WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md` | choose answer form from state/context/evidence | direct answer, clarification, partial, refusal, plan, boundary, memory-honest, evidence-needed | selects answer shape and candidate family | partial helpers only | partial via response/helper tests | both, but mostly runtime selection later |
| Response matrix / chat matrix | no dedicated file found; implied by `RESPONSE_GENERATION.md`, `REUSABLE_RESPONSE.md`, `LIVE_BEHAVIOUR.md`, `ORDINARY_TASK_CONTEXT.md`, `WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md` | map user turn to response form and delivery | identity, capability, memory, continuity, ordinary task, evidence, explanation, refusal | selects response family and delivery shape | partial | partial | both |
| Cognition matrix | no dedicated file found; implied by ranked response canon and cognition docs | unify cognition/state into response planning | intent, context, evidence, memory, continuity, capability, safety, uncertainty | selects canonical response-planning route | partial | partial | both |
| Evaluation matrix | `docs/WESLR_ADVERSARIAL_FAIRNESS_ENTERPRISE_COGNITION_EVALUATION_MATRIX_V1.md`; `weslr/evaluation_matrix_case_registry_helpers.py` | coverage gate before broader real-answer testing | A-J families: fairness, stereotypes, injection, jailbreak, privacy, IDOR, groundedness, theory of mind, compression, continuity stress | measures coverage and blocks bad sources | yes | yes (`44 passed` noted in review) | evaluation |
| Behavior matrix | `docs/WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1.md` | behavior/readiness observation | ordinary task, non-cannedness, alignment, memory honesty, self-boundaries, evidence/source boundaries, guardrails, continuity, live-slice behavior | measures behavior readiness qualitatively | no dedicated helper surface found | design docs only | evaluation |
| Response-fit matrix | `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`; `weslr/response_fit_engine_helpers.py` | match truth kernel to human situation frame and answer shape | too_generic, too_verbose, too_technical, too_simple, wrong_urgency, wrong_risk_posture, fake_empathy, missed_emotional_pressure, ignored_correction, lost_continuity, evidence_depth_mismatch, jargon_mismatch, actionability_mismatch, answer_shape_mismatch, industry_context_mismatch, human_perceived_ai_tone | selects mismatch labels and recommended revision type | yes | yes (`13 passed` noted in review) | both |
| Real-answer sample matrix | `docs/WESLR_CONTROLLED_REAL_ANSWER_SAMPLE_RUN_V1.md`; `docs/WESLR_REAL_ANSWER_QUALITY_OBSERVATION_BOUNDARY_V1.md`; `weslr/controlled_real_answer_sample_run.py`; `weslr/real_answer_quality_observation_helpers.py`; `weslr/run_controlled_real_answer_sample_run_approval_helpers.py` | controlled sample observation of real WESLR answers | source-approved public_open/synthetic cases, redacted answer descriptors, quality dimensions, blocked labels | measures answer quality fit/partial/mismatch and blocked reasons | yes | yes (reviews note strong coverage) | both, but observation/eval first |
| Controlled safe non-model observation matrix | `docs/WESLR_DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_MATRIX_V1.md`; `docs/WESLR_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_MATRIX_REPORT_V1.md` | tiny shadow retry matrix for safe non-model path | ordinary_task_behavior, non_canned_cognition, conduct_alignment | tracks routing/validator safety and shadow call interception | report exists; no core helper module named as matrix | yes (report records release gates) | evaluation |
| Product mode matrix | `docs/WESLR_PRODUCT_MODE_MATRIX_V1.md` | UI/runtime contract by deployment mode | public_demo_readonly, hosted_trial, hosted_paid_individual, hosted_team, private_institution, self_hosted_admin, operator_dev, staging | selects visible capabilities and allowed UX | doctrine only | no dedicated helper surface found | runtime contract |

## 3. Answering method catalog

### 3.1 Identity / status family

1. **Verified identity / status answer**  
   - Source: `weslr/meaning_response.py`, `weslr/chat_responder.py`, `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`  
   - Purpose: answer “who/what are you?” safely and boundedly.  
   - Trigger: identity/status/self-description questions.  
   - Input: verified identity state, relationship state, available memory scope, capability boundary.  
   - Output shape: short identity/status paragraph or bounded self-description.  
   - Type: deterministic + evidence-based + memory-aware.  
   - Implemented: yes, partially.  
   - Target file: `weslr/meaning_response.py` / `weslr/chat_responder.py` (later via catalog).  
   - Diff vs generic LLM: avoids persona switching and unsupported self-claims.

2. **Memory report answer**  
   - Source: `weslr/meaning_response.py`, `docs/WESLR_CONTEXT_MEMORY_TRUST_AND_EVIDENCE_BOUNDARY_V1.md`, `docs/WESLR_REAL_ANSWER_QUALITY_OBSERVATION_BOUNDARY_V1.md`  
   - Purpose: say what memory is available and what is not.  
   - Trigger: memory/continuity questions, “do you remember…” requests.  
   - Input: memory availability, source labels, freshness, scope, trust.  
   - Output shape: bounded memory summary + uncertainty.  
   - Type: memory-based + governed.  
   - Implemented: yes, partially.  
   - Target file: `weslr/meaning_response.py` + catalog layer.  
   - Diff: distinguishes known, unknown, and claimed memory.

3. **Capability orientation answer**  
   - Source: `weslr/meaning_response.py`, `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`  
   - Purpose: explain what WESLR can do.  
   - Trigger: capability queries, “can you help with X?”  
   - Input: capability boundary, domain context, current mode.  
   - Output shape: capability-guidance posture + next safe step.  
   - Type: governed + evidence-based.  
   - Implemented: yes, partially.  
   - Target file: `weslr/meaning_response.py` / future selector.  
   - Diff: capability guidance, not false authority.

4. **New contact / orientation answer**  
   - Source: `weslr/meaning_response.py`  
   - Purpose: greet/establish a bounded working relationship.  
   - Trigger: first-contact or onboarding turns.  
   - Input: verified identity, role, context.  
   - Output shape: short welcome/orientation.  
   - Type: deterministic + relationship-aware.  
   - Implemented: yes, partially.  
   - Target file: `weslr/meaning_response.py`.  
   - Diff: avoids generic canned welcome.

### 3.2 Boundary / uncertainty family

5. **Clarifying question answer**  
   - Source: `weslr/meaning_response.py`, `weslr/native_reasoning_frame.py`, `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`  
   - Purpose: ask the smallest useful question when input is insufficient.  
   - Trigger: missing context, ambiguous intent, insufficient authorization.  
   - Input: missing context slots, uncertainty labels, response obligation.  
   - Output shape: one focused question.  
   - Type: deterministic + governed + evidence-aware.  
   - Implemented: yes, partially.  
   - Target file: `weslr/native_reasoning_frame.py` + selector.  
   - Diff: asks only when needed.

6. **Bounded uncertainty answer**  
   - Source: `weslr/meaning_response.py`, `weslr/native_reasoning_frame.py`, `weslr/request_intelligence/uncertainty.py`  
   - Purpose: preserve uncertainty instead of inventing certainty.  
   - Trigger: low confidence, missing evidence, unclear memory.  
   - Input: uncertainty labels, confidence, evidence sufficiency.  
   - Output shape: answer with explicit uncertainty.  
   - Type: evidence-based + calibrated.  
   - Implemented: yes, partially.  
   - Target file: `weslr/native_reasoning_frame.py`.  
   - Diff: honest uncertainty over confident bluffing.

7. **Refusal / boundary answer**  
   - Source: `weslr/native_response_self_check.py`, `weslr/answer_authority_boundary.py`, `weslr/answer_formation.py`, `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`  
   - Purpose: refuse unsupported, unsafe, or unauthorized requests.  
   - Trigger: privacy, authority, official-claim, runtime, provider/model, protected-content requests.  
   - Input: denied authority flags, blocked labels, safety boundary.  
   - Output shape: refusal with useful alternative or boundary note.  
   - Type: governed + rule-based.  
   - Implemented: yes, partially.  
   - Target file: `weslr/native_response_self_check.py` + boundary modules.  
   - Diff: refusal is bounded and helpful, not just negative.

8. **Evidence-needed answer**  
   - Source: `weslr/native_reasoning_frame.py`, `weslr/evidence_needed_detector.py`, `weslr/evidence_answer_builder.py`  
   - Purpose: say evidence is needed before stronger claims.  
   - Trigger: current/latest/source/lookup/open-knowledge questions.  
   - Input: evidence need, source scope, claim burden.  
   - Output shape: request for evidence or evidence-collection next step.  
   - Type: evidence-based + governed.  
   - Implemented: yes, partially.  
   - Target file: `weslr/native_reasoning_frame.py` + evidence modules.  
   - Diff: does not fake current facts.

9. **Partial answer / supported portion answer**  
   - Source: `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`, `weslr/native_response_assembly.py`  
   - Purpose: answer what can be safely answered and label the rest.  
   - Trigger: mixed-support requests.  
   - Input: supported facts, unsupported remainder, evidence gaps.  
   - Output shape: split answer with explicit gaps.  
   - Type: ranked + evidence-based.  
   - Implemented: partial helper support.  
   - Target file: `weslr/native_response_assembly.py`.  
   - Diff: avoids all-or-nothing overrefusal.

10. **Direct bounded answer**  
   - Source: `weslr/native_response_draft.py`, `weslr/native_response_assembly.py`, `docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md`  
   - Purpose: answer directly when state/evidence is sufficient.  
   - Trigger: clear intent + sufficient grounding.  
   - Input: frame, obligations, known context, evidence sufficiency.  
   - Output shape: direct answer with boundaries.  
   - Type: ranked + governed.  
   - Implemented: yes, partially.  
   - Target file: `weslr/native_response_draft.py` / selector.  
   - Diff: directness without hidden authority.

### 3.3 Task / workflow family

11. **Ordinary task planning answer**  
   - Source: `weslr/ordinary_reasoning_guidance.py`, `weslr/native_reasoning_frame.py`, `docs/ORDINARY_TASK_CONTEXT.md`, `docs/RESPONSE_GENERATION.md`  
   - Purpose: provide safe step planning for ordinary tasks.  
   - Trigger: planning/debug/migration/deployment/checklist turns.  
   - Input: task markers, constraints, missing context, evidence/tool need.  
   - Output shape: numbered steps or bounded next actions.  
   - Type: heuristic + governed + context-aware.  
   - Implemented: yes, partially.  
   - Target file: `weslr/ordinary_reasoning_guidance.py`.
   - Diff: task-aware planning, not generic FAQ.

12. **Implementation planning answer**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`, `weslr/targeted_response_formation_improvement.py`  
   - Purpose: turn a design gap into a constrained implementation plan.  
   - Trigger: “what should we code first?”, “what lane next?”.  
   - Input: target gaps, answer-shape policy, authority calibration.  
   - Output shape: plan with first safe step.  
   - Type: matrix-ranked + governed.  
   - Implemented: yes, partially.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: proposes the next safe build step, not runtime authority.

13. **Artifact / workspace planning answer**  
   - Source: `weslr/ordinary_reasoning_guidance.py`, `docs/ORDINARY_TASK_CONTEXT.md`  
   - Purpose: plan docs/tests/files/workspace steps.  
   - Trigger: repo/workspace change requests.  
   - Input: file targets, constraints, safety.  
   - Output shape: staged file/work plan.  
   - Type: heuristic + governed.  
   - Implemented: partial.  
   - Target file: `weslr/ordinary_reasoning_guidance.py`.  
   - Diff: keeps work bounded and explicit.

14. **Workflow / next-lane answer**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`, `docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md`  
   - Purpose: say what lane should happen next.  
   - Trigger: design/review/implementation sequencing.  
   - Input: gap labels, readiness, blocked flags.  
   - Output shape: next-lane recommendation.  
   - Type: metadata-guided + ranked.  
   - Implemented: partial.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: sequence recommendation, not blind roadmapping.

15. **Governance escalation proposal**  
   - Source: `weslr/native_reasoning_frame.py`, `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`  
   - Purpose: propose operator review when authority is missing.  
   - Trigger: approval-needed or policy-blocked cases.  
   - Input: approval requirement, denied authority fields.  
   - Output shape: proposal / escalation note.  
   - Type: governed.  
   - Implemented: partial.  
   - Target file: `weslr/native_reasoning_frame.py` + governance modules.  
   - Diff: asks for review instead of pretending authorization.

### 3.4 Teaching / explanation / discovery family

16. **Teaching / explanation answer**  
   - Source: `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`, `docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md` (search hit), `grammar.md`, `vocabulary.md`  
   - Purpose: explain concepts in human-teachable form.  
   - Trigger: “explain X”, educational asks, onboarding.  
   - Input: audience level, vocabulary, domain context, evidence needs.  
   - Output shape: staged explanation / human-readable explanation.  
   - Type: evidence-based + adaptive-delivery.  
   - Implemented: doctrine + partial helpers.  
   - Target file: `weslr/meaning_response.py` / future answer catalog.  
   - Diff: explanation shaped to person/context, not template prose.

17. **Language / grammar / vocabulary discovery answer**  
   - Source: `grammar.md`, `vocabulary.md`, `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_INTELLIGENCE_ENRICHMENT_DOCTRINE_V1.md` (search hits)  
   - Purpose: translate internal form into human-understandable language and support discovery/teaching ideas.  
   - Trigger: grammar/vocabulary asks, language discovery/teaching prompts, explanation of internal state.  
   - Input: internal state signals, preferred vocabulary, target audience.  
   - Output shape: human-readable explanation or teaching-oriented language.  
   - Type: doctrine-only / heuristic.  
   - Implemented: docs only; no dedicated method module found.  
   - Target file: future `weslr/answer_method_catalog.py` + `weslr/answer_shape_catalog.py`.  
   - Diff: translates internal forms without pretending to know an unknown language.

18. **Scientific discovery / capability guidance answer**  
   - Source: `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`, `docs/WESLR_BENCHMARK_REASONING_ENGINE_V1.md`  
   - Purpose: guide research/discovery with staged workflow.  
   - Trigger: materials/science/research capability questions.  
   - Input: candidate generation constraints, novelty, structural sanity, evidence gates.  
   - Output shape: stepwise research plan + boundary notes.  
   - Type: evidence-based + workflow-guided.  
   - Implemented: doctrine only / partial helper overlap.  
   - Target file: future `weslr/answer_method_catalog.py` + `weslr/answer_matrix.py`.  
   - Diff: does not claim discovery; it guides discovery.

19. **Benchmark / evaluation answer**  
   - Source: `weslr/reasoning_task.py`, `weslr/reasoning_trace.py`, `weslr/reasoning_arbitrator.py`, `docs/WESLR_BENCHMARK_REASONING_ENGINE_V1.md`, `docs/WESLR_INTELLIGENCE_AND_TURING_TEST_EVALUATION_TRACK_DESIGN_V1.md`  
   - Purpose: explain evaluation, not assert official results.  
   - Trigger: evaluation-track, benchmark, Turing-style questions.  
   - Input: task schema, trace, conflicts, legibility, anti-gaming.  
   - Output shape: evaluation summary / readiness label / caveat.  
   - Type: governed + metadata-only.  
   - Implemented: helper structures exist; doctrine only for official-eval claims.  
   - Target file: `weslr/cognition_case_registry.py` + `weslr/answer_method_catalog.py`.  
   - Diff: evaluation support without official score authority.

20. **Unknown-engine branch / friction answer**  
   - Source: `weslr/controlled_unknown_engine_metadata_shadow_runner.py`, `docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md`, `docs/WESLR_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ASSIMILATION_V1.md`, `docs/WESLR_UNKNOWN_ENGINE_GRADED_FRICTION_RESPONSE_LEVELS_V1.md`  
   - Purpose: represent uncertainty, branches, friction, and bounded hypotheses.  
   - Trigger: unknowns, future branches, friction assimilation, repeated failure patterns.  
   - Input: knowns/unknowns, missing evidence, branch assumptions, risk boundaries.  
   - Output shape: metadata-only uncertainty record or graded proposal.  
   - Type: metadata-only + governed.  
   - Implemented: yes, partially.  
   - Target file: `weslr/controlled_unknown_engine_metadata_shadow_runner.py`.  
   - Diff: not a prediction oracle; a bounded uncertainty boundary.

### 3.5 Relationship / correction / continuity family

21. **Correction repair answer**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`, `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`  
   - Purpose: repair after a user correction.  
   - Trigger: user says previous answer was wrong/too generic.  
   - Input: correction history, continuity state, answer-shape gap.  
   - Output shape: revised answer that changes shape.  
   - Type: ranked + adaptive.  
   - Implemented: partial.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: correction changes the answer, not just the wording.

22. **Continuity / thread answer**  
   - Source: `weslr/meaning_state_context.py`, `weslr/entity_timeline_memory.py`, `weslr/user_timeline_memory.py`, `docs/ORDINARY_TASK_CONTEXT.md`  
   - Purpose: preserve the current thread and prior decisions.  
   - Trigger: “what were we doing?”, follow-ups, multi-turn continuity.  
   - Input: continuity state, recent turns, timeline anchors.  
   - Output shape: thread-aware response or recap.  
   - Type: memory-aware + context-grounded.  
   - Implemented: partial.  
   - Target file: `weslr/meaning_state_context.py` / selector.  
   - Diff: continuity without fake long-term memory.

23. **Relationship / feedback answer**  
   - Source: `weslr/relationship_observation_capture.py`, `weslr/meaning_response.py`, `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`  
   - Purpose: acknowledge user signals, trust state, and feedback.  
   - Trigger: correction, frustration, trust or preference signals.  
   - Input: relationship context, trust state, emotional pressure.  
   - Output shape: bounded acknowledgment + useful next step.  
   - Type: adaptive + governed.  
   - Implemented: partial.  
   - Target file: `weslr/meaning_response.py`.  
   - Diff: concern-aware without fake empathy.

24. **Conflict / contradiction handling answer**  
   - Source: `weslr/reasoning_trace.py`, `weslr/reasoning_arbitrator.py`, `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`  
   - Purpose: preserve contradictions instead of erasing them.  
   - Trigger: conflicting evidence, conflicting goals, or constraint clashes.  
   - Input: conflict records, evidence conflicts, missing assumptions.  
   - Output shape: conflict-aware explanation or clarification.  
   - Type: governed + metadata-only.  
   - Implemented: helper structures only.  
   - Target file: `weslr/reasoning_trace.py` / future selector.  
   - Diff: contradiction is visible, not smoothed away.

### 3.6 Response-shape / quality family

25. **Answer-shape planning**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`, `weslr/targeted_response_formation_improvement.py`  
   - Purpose: choose the right shape before composing text.  
   - Trigger: any answer that could be direct, explanatory, plan-based, refusal-based, or clarification-based.  
   - Input: task frame, concern slot, recency, directness pressure, boundary calibration.  
   - Output shape: shape label + plan.  
   - Type: matrix-ranked + heuristic.  
   - Implemented: yes, partially.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: shape first, prose second.

26. **Non-cannedness pressure**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`, `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`  
   - Purpose: suppress repeated template feel.  
   - Trigger: repeated skeletons, checklist drift, generic fallback.  
   - Input: repetition markers, current-turn specificity, user concern.  
   - Output shape: pressure label and selected structure.  
   - Type: heuristic + quality control.  
   - Implemented: partial.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: content-specific, not boilerplate.

27. **Directness / concern integration / self-check family**  
   - Source: `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`  
   - Purpose: tune directness, empathy concern handling, and pre-final self-check.  
   - Trigger: frictiony or emotionally loaded conversations.  
   - Input: concern slot, frustration signal, directness pressure, boundary calibration.  
   - Output shape: revised answer plan or rejection.  
   - Type: heuristic + governed.  
   - Implemented: partial.  
   - Target file: `weslr/targeted_response_formation_improvement.py`.  
   - Diff: useful and human-fit without fake warmth.

## 4. Catalog implementation design

### 4.1 `weslr/answer_method_catalog.py`

**Purpose**
- canonical registry of answer methods/families
- method metadata, trigger labels, inputs, outputs, implementation status

**Data structures**
- `AnswerMethodSpec`
- `AnswerMethodFamilySpec`
- `AnswerMethodCatalog`
- `AnswerMethodCatalogPacket`

**Public functions**
- `build_answer_method_catalog_v1(...)`
- `validate_answer_method_catalog_v1(...)`
- `summarize_answer_method_catalog_v1(...)`
- `to_answer_method_catalog_json_safe_v1(...)`
- `select_methods_for_turn_v1(...)`

**Based on**
- `docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md`
- `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md`
- `docs/WESLR_UNIFIED_RESPONSE_FORMATION_CANON_V1.md`
- `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`
- `weslr/meaning_response.py`
- `weslr/ordinary_reasoning_guidance.py`
- `weslr/targeted_response_formation_improvement.py`
- `weslr/response_fit_engine_helpers.py`

**Tests needed**
- method registration completeness
- method/family validation
- missing-doc / missing-method fail-closed behavior
- JSON-safe output

**Risks**
- collapsing into a generic FAQ table
- allowing runtime authority to leak into method metadata
- overfitting to current helper names instead of stable intent labels

### 4.2 `weslr/answer_shape_catalog.py`

**Purpose**
- catalog answer shapes separately from methods
- keep shape choice visible before prose generation

**Data structures**
- `AnswerShapeSpec`
- `AnswerShapeCompatibility`
- `AnswerShapeCatalog`

**Public functions**
- `build_answer_shape_catalog_v1(...)`
- `validate_answer_shape_catalog_v1(...)`
- `select_answer_shape_v1(...)`
- `summarize_answer_shape_catalog_v1(...)`
- `to_answer_shape_catalog_json_safe_v1(...)`

**Based on**
- `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md`
- `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md`
- `weslr/targeted_response_formation_improvement.py`
- `weslr/native_response_draft.py`

**Tests needed**
- direct/partial/refusal/clarification/plan shape selection
- blocked shape rejection
- cross-check against method family compatibility

**Risks**
- shape catalog becoming just a style guide
- shape selection ignoring evidence or authority constraints

### 4.3 `weslr/answer_matrix.py`

**Purpose**
- bind method catalog + shape catalog + case context into a selectable matrix
- express which method is appropriate for which answer situation

**Data structures**
- `AnswerMatrixCase`
- `AnswerMatrixRow`
- `AnswerMatrixPacket`

**Public functions**
- `build_answer_matrix_case_v1(...)`
- `validate_answer_matrix_case_v1(...)`
- `build_answer_matrix_v1(...)`
- `summarize_answer_matrix_v1(...)`
- `to_answer_matrix_json_safe_v1(...)`

**Based on**
- ranked state-grounded response canon
- candidate substrate
- response fit engine
- ordinary task context docs

**Tests needed**
- case-to-method mapping
- shape compatibility mapping
- blocked/unknown case fail-closed behavior

**Risks**
- becoming a deterministic response table
- mixing evaluation labels with runtime authority
- duplicating `chat_responder.py`

### 4.4 `weslr/response_method_selector.py`

**Purpose**
- choose the best answer method for a turn
- separate selection from rendering

**Data structures**
- `ResponseMethodSelection`
- `ResponseMethodSelectionTrace`

**Public functions**
- `select_response_method_v1(...)`
- `rank_candidate_methods_v1(...)`
- `validate_response_method_selection_v1(...)`
- `summarize_response_method_selection_v1(...)`

**Based on**
- `weslr/native_reasoning_frame.py`
- `weslr/meaning_response.py`
- `weslr/response_fit_engine_helpers.py`
- `weslr/ordinary_reasoning_guidance.py`

**Tests needed**
- identity/status vs plan vs boundary vs evidence routing
- correction handling
- uncertainty routing
- no direct runtime/provider call leakage

**Risks**
- hidden runtime branching reappearing here
- selector becoming a policy engine without review gates

### 4.5 `weslr/cognition_case_registry.py`

**Purpose**
- registry of cognition/evaluation/observation cases across answer families
- unify answer matrix, evaluation matrix, and observation matrix cases

**Data structures**
- `CognitionCaseSpec`
- `CognitionCaseRegistry`
- `CognitionCasePacket`

**Public functions**
- `build_cognition_case_registry_v1(...)`
- `validate_cognition_case_registry_v1(...)`
- `summarize_cognition_case_registry_v1(...)`
- `to_cognition_case_registry_json_safe_v1(...)`

**Based on**
- evaluation matrix helpers
- real-answer observation helpers
- controlled real-answer sample run helpers
- behavior evaluation docs
- benchmark reasoning engine docs

**Tests needed**
- source-class gating
- family coverage gating
- blocked label propagation
- operator-provided synthetic case handling

**Risks**
- registry drifting into an evaluation authority surface
- raw transcript persistence creeping in
- merging runtime and observation concerns too early

## 5. What to code before live runtime

Recommended order, confirmed by repo evidence:

1. **Answer method catalog**
2. **Answer shape catalog**
3. **Cognition / case registry**
4. **Response method selector**
5. **Candidate formation from method catalog**
6. **Response-fit integration**
7. **Real-answer sample evaluation harness**
8. **Only then** a live runtime adapter

### Why this order
- the repo already has helper substrates for frame, draft, self-check, fit, and observations
- the missing layer is a method/shape registry that makes selection explicit
- runtime wiring before cataloging would preserve the current deterministic surface instead of the designed intelligence surface

## 6. Language discovery / teaching capability

### Docs found
- `grammar.md`
- `vocabulary.md`
- `THOUGHT-DYNAMICS.md`
- `WORLD-MODEL.md`
- `docs/WESLR_STABLE_IDENTITY_AND_ADAPTIVE_DELIVERY_DOCTRINE_V1.md`
- search hits in:
  - `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`
  - `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`
  - `docs/WESLR_INTELLIGENCE_ENRICHMENT_DOCTRINE_V1.md`
  - `docs/WESLR_TEACHING_EXPLANATION_DESIGN_V1.md`
  - `docs/WESLR_FORMAL_LOGIC_PARSER_V1.md`
  - `docs/WESLR_LOGIC_TEACHING_SPINE_V1.md`

### Implementation status
- grammar/vocabulary/thought/world-model docs exist as doctrine and language scaffolding
- no dedicated language-discovery answer method module found
- explanation/teaching is partly supported by meaning response, stable identity doctrine, and ordinary reasoning guidance
- the “discover unknown human language” idea is present in positioning/public-UX doctrine, but not yet a dedicated answer family

### Influence on answer methods
- the answer catalog should include a **teaching/explanation** family
- the catalog should also include a **language discovery / translation** family if later evidence supports it
- internal forms must be translated to human-understandable explanation before any public-facing surface
- grammar/vocabulary should inform answer shape and delivery, not become hidden authority

### What should be coded later
- a language/discovery subclass inside `answer_method_catalog.py`
- a shape policy that can render internal form as human-teachable explanation
- tests that prove it does not become fake-translation or discovery theater

## 7. What must NOT happen

- do not reduce WESLR to a deterministic FAQ
- do not skip method/catalog implementation
- do not wire a generic adapter before the catalog exists
- do not patch the old Ollama-style chat path as a shortcut
- do not treat helper metadata as final answer authority
- do not use the model provider as identity
- do not expose this lane to external testers early
- do not overclaim intelligence, emergence, readiness, or discovery

## 8. First coding lane proposal

### Recommended first lane
`IMPLEMENT_WESLR_ANSWER_METHOD_CATALOG_V1`

### Exact files to add
- `weslr/answer_method_catalog.py`
- `weslr/tests/test_answer_method_catalog_v1.py`

### No runtime wiring
- no `chat_responder.py` edits
- no `main.py` edits
- no `dialogue.py` edits
- no `chat_ui.py` edits
- no provider/model/search/advisor calls
- no `.weslr` IO

### Success criteria
- methods/families are enumerated explicitly
- each method has trigger, input, output shape, implementation status, target file, and diff-vs-generic-LLM notes
- method catalog validates fail-closed on unknown/missing families
- JSON-safe summary is produced
- tests pass

### How it moves WESLR forward
- it turns designed answering behavior into a governed inventory
- it makes later selection and shape choice explicit
- it prevents the runtime adapter from becoming the first place where WESLR’s intelligence is defined

## 9. Second and third coding lanes

### Second lane
`IMPLEMENT_WESLR_ANSWER_SHAPE_CATALOG_V1`

- files:
  - `weslr/answer_shape_catalog.py`
  - `weslr/tests/test_answer_shape_catalog_v1.py`
- focus:
  - shape selection rules
  - directness / refusal / clarification / plan / partial-answer shapes
  - compatibility with method families

### Third lane
`IMPLEMENT_WESLR_COGNITION_CASE_REGISTRY_AND_SELECTOR_V1`

- files:
  - `weslr/cognition_case_registry.py`
  - `weslr/response_method_selector.py`
  - `weslr/tests/test_cognition_case_registry_v1.py`
  - `weslr/tests/test_response_method_selector_v1.py`
- focus:
  - case registry
  - matrix selection
  - method ranking
  - fail-closed source/family gating

### After that
- integrate response-fit helpers
- then real-answer sample observation harness
- then, only after review, a narrow live adapter

## 10. Final recommendation

### Implement now
- answer method catalog
- answer shape catalog
- cognition case registry
- method selector

### Implement next
- response-fit integration
- real-answer observation harness
- review gating for controlled samples

### Postpone
- live runtime adapter
- generic chat rewrite
- external tester exposure
- provider/model-driven identity

### Return to live chat runtime when
- the method catalog exists
- the shape catalog exists
- the registry is in place
- selection is explicit and tested
- response-fit and observation gates pass review

### Final judgment
This repo has enough doctrine and helper scaffolding to begin catalog/case-registry work now, but not enough reason to jump straight to a generic live runtime plan.
