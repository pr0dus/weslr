# WESLR Generalized Friction Improvement Existing Substrate V1

## SECTION 1 — Executive truth

WESLR already has a real friction-improvement substrate, but it is split across helper layers, replay layers, proposal/governance surfaces, and review docs.

What already resembles a generalized process:
- observe friction in metadata-only helpers/reports
- capture friction cases
- replay cases against the no-model stack
- classify mismatch labels / route-family gaps
- generate governed update proposals
- owner review / approval / denial surfaces
- owner-approved realization for the initial friction cases
- replay and proof-review documents after realization

What is implemented:
- friction case capture
- friction replay harness
- friction update proposal bridge
- response-method / shape / case selector stack
- unknown-engine friction assimilation
- no-model bounded renderer
- proposal / CDI / governance / trace / realization surfaces
- initial friction realization for the four starter cases

What is design-only:
- explicit behavior-pack registry
- explicit friction replay suite builder
- explicit friction pattern miner / generalization engine
- explicit friction-training proof report runner

What is review-only:
- the V1.01 proof review docs
- the controlled real-answer sample and readiness reviews
- the canonical update/freeze docs that say reuse existing governance rather than inventing a parallel lifecycle

What is missing:
- a dedicated pattern miner that clusters repeated friction into generalized candidates
- a first-class behavior-pack registry
- a replay-suite builder for expanding from fixed starter cases to broader regression sets
- a standardized proof-report runner for the generalized improvement cycle

Behavior-pack concept already exists?
- yes in docs
- no explicit code registry yet

Pattern-mining/generalization concept already exists?
- partially
- label→gap mapping exists
- repeated-failure aggregation exists
- true clustering/generalization engine does not yet exist

Reusable proposal/governance route already exists?
- yes
- and it should be reused

Should we reuse existing governance instead of creating a new loop?
- yes
- no parallel lifecycle should be introduced

## SECTION 2 — Existing process chain map

| chain step | existing modules/docs/tests | status | safe to reuse | gaps |
|---|---|---|---|---|
| 1. observe friction | `weslr/response_fit_self_check.py`, `weslr/real_answer_quality_observation_helpers.py`, `weslr/unknown_engine_conversation_friction_assimilation.py`, `docs/WESLR_FRICTION_TRAINING_AND_COGNITIVE_GROWTH_SUBSTRATE_V1.md` | implemented | yes | broad live observation lane still bounded |
| 2. capture friction case | `weslr/friction_case_capture.py`, `weslr/tests/test_initial_friction_proposal_realization_v1.py`, `docs/WESLR_FRICTION_TRAINING_AND_COGNITIVE_GROWTH_SUBSTRATE_V1.md` | implemented | yes | registry is still implicit rather than first-class |
| 3. replay failure | `weslr/friction_replay_harness.py`, `weslr/tests/test_friction_replay_harness_v1.py` | implemented | yes | replay suite expansion builder missing |
| 4. classify mismatch | `weslr/response_fit_self_check.py`, `weslr/unknown_prompt_friction_router.py`, `weslr/response_method_selector.py`, `weslr/unknown_engine_conversation_friction_assimilation.py` | implemented / partial | yes | no dedicated clustering stage yet |
| 5. cluster/generalize pattern | `weslr/unknown_engine_conversation_friction_assimilation.py`, `weslr/friction_case_capture.py`, docs on graded friction / growth substrate | partial | maybe | missing dedicated pattern miner / generalization engine |
| 6. generate update proposal | `weslr/friction_update_proposal_bridge.py`, `weslr/contract_improvement_proposal_bridge.py`, `weslr/cdi_proposal_builder.py`, `weslr/experiment_proposal_generator.py` | implemented / partial | yes | friction-to-proposal bridge is metadata-only and narrow |
| 7. owner review | `weslr/governance_surface.py`, `weslr/change_proposals.py`, `weslr/operator_proposal_review.py`, `weslr/cdi_decision_log.py` | implemented | yes | none blocking |
| 8. implement approved realization | `weslr/proposal_realization.py`, initial commit `7604ca8a726c7bbba78ceded9ec9bac6baf9b9d0` | implemented | yes | only starter realization chain exists so far |
| 9. replay before/after | `weslr/friction_replay_harness.py`, proof review docs | implemented | yes | no generalized suite builder yet |
| 10. anti-hardcoding proof | `weslr/tests/test_initial_friction_proposal_realization_v1.py`, `weslr/tests/test_response_method_selector_v1.py`, `weslr/tests/test_no_model_bounded_renderer_v1.py`, `weslr/tests/test_unknown_prompt_friction_router_v1.py` | implemented | yes | reusable hardening helper could reduce duplication |
| 11. proof report | `docs/WESLR_V101_FRICTION_TRAINED_IMPROVEMENT_PROOF_REVIEW_V1.md`, `docs/WESLR_FRICTION_TRAINING_AND_COGNITIVE_GROWTH_SUBSTRATE_V1.md` | implemented / review-only | yes | standardized proof-report runner missing |
| 12. promote to behavior pack or core rule | docs mention behavior packs; selector/renderer updates already happened; no registry | design-only / partial | maybe | behavior-pack registry and promotion policy missing |
| 13. monitor regression | `weslr/tests/test_initial_friction_proposal_realization_v1.py`, `weslr/tests/test_friction_replay_harness_v1.py`, selector/renderer tests | implemented | yes | broader regression suite builder missing |

## SECTION 3 — Current implemented pieces

The newest chain now shows a real governed improvement loop:
- friction case capture records safe metadata and expected/actual route mismatches
- replay harness re-runs those cases against the protected no-model stack
- update proposal bridge turns replay metadata into operator-reviewable proposal packets
- owner-approved realization in commit `7604ca8a726c7bbba78ceded9ec9bac6baf9b9d0` changed selector / routing / renderer behavior
- replay improved to 4/4 on the starter cases
- neighbor prompts passed
- protected runtime files stayed untouched

What this proves:
- WESLR can turn weak answers into governed metadata cases
- WESLR can replay those cases deterministically
- WESLR can produce proposals without model/provider calls
- WESLR can realize approved selector/renderer changes
- the improvement is not a single hardcoded answer patch

What it does not prove yet:
- general learning authority
- autonomous self-modification
- broad live-chat improvement across arbitrary domains
- a reusable pattern miner
- a behavior-pack registry
- public readiness or official claims

## SECTION 4 — Generalization and anti-hardcoding substrate

Already present:
- prompt-family routing in `weslr/response_method_selector.py`
- unknown/friction branching in `weslr/unknown_prompt_friction_router.py`
- candidate formation in `weslr/candidate_response_formation.py`
- bounded rendering in `weslr/no_model_bounded_renderer.py`
- neighbor prompt tests in `weslr/tests/test_initial_friction_proposal_realization_v1.py`
- boundary regressions in `weslr/tests/test_no_model_bounded_renderer_v1.py`
- selector compatibility validation in `weslr/tests/test_response_method_selector_v1.py`
- friction replay validation in `weslr/tests/test_friction_replay_harness_v1.py`

Reusable anti-hardcoding pattern already exists:
- normalize labels/context signals
- detect route family
- select compatible method/shape/case
- render bounded text from metadata only
- replay neighbor prompts
- fail closed on official-claim / runtime / provider drift

What should be extracted into a shared helper:
- label and context normalization
- route-family / case-family classification helpers
- route compatibility scoring / validation
- neighbor-case regression suite builder
- boundary-claim blocker shared by selector + renderer + router

## SECTION 5 — Pattern mining / clustering substrate

There is partial pattern-mining already:
- `weslr/unknown_engine_conversation_friction_assimilation.py` maps friction labels to gap labels and improvement targets
- `weslr/friction_case_capture.py` aggregates mismatch labels and proposed update areas
- `weslr/friction_update_proposal_bridge.py` aggregates proposal types, target areas, replay status, and approval status
- the docs already describe graded friction and repeated-failure growth

What is missing:
- a dedicated repeated-failure clusterer
- a generalized pattern candidate packet
- a stable “this family keeps failing” compressor

Minimal missing module:
- `friction_pattern_miner.py`

Why it is needed:
- to turn repeated cases into generalized pattern candidates without inventing a new lifecycle

What it should reuse:
- friction case capture
- friction replay harness
- unknown-engine assimilation
- selector / renderer outputs
- existing proposal/governance surfaces

What it must not do:
- call models/providers/search/advisors
- write runtime state
- create a parallel self-improvement loop
- promote itself automatically
- claim learning authority

`friction_generalization_engine.py` is optional unless you want a higher-order abstraction above the miner.

## SECTION 6 — Behavior pack substrate

Current state:
- no explicit code registry for behavior packs
- docs already describe the concept
- friction modules already contain placeholder references to `behavior_pack` / `behavior_pack_registry`

The concept is real in docs, not yet in code.

A behavior pack should be built from repeated friction and should be fed by:
- `weslr/friction_case_capture.py`
- `weslr/friction_replay_harness.py`
- `weslr/friction_update_proposal_bridge.py`
- `weslr/unknown_engine_conversation_friction_assimilation.py`
- `weslr/response_method_selector.py`
- `weslr/no_model_bounded_renderer.py`
- `weslr/evaluation_matrix_case_registry_helpers.py`
- `weslr/targeted_response_formation_improvement.py`

Example domains already named in docs:
- WESLR development
- industrial automation
- legal/privacy
- website/public launch
- materials discovery
- language / grammar / vocabulary discovery
- owner workflow

## SECTION 7 — Governance / proposal reuse

Reuse the existing governance spine rather than creating a new lifecycle.

Existing routes to reuse:
- proposal creation: `weslr/change_proposals.py`, `weslr/experiment_proposal_generator.py`, `weslr/cdi_proposal_builder.py`, `weslr/contract_improvement_proposal_bridge.py`
- review / approval / defer / deny: `weslr/operator_proposal_review.py`, `weslr/change_proposals.py`, `weslr/governance_surface.py`, `weslr/cdi_decision_log.py`
- traceability: `weslr/proposal_traceability.py`
- realization / rollback planning: `weslr/proposal_realization.py`
- governance audit surface: `weslr/ai_audit_self_governance_surface.py`
- proof / eligibility gating: `weslr/proof_gate.py`

`weslr/auto_refinement.py` exists, but it is a separate guarded weight-update path, not the generalized friction loop.

Conclusion: the generalized friction process should route through existing proposal/governance/CDI/proof surfaces.

## SECTION 8 — Generalized improvement process proposal

Safe generalized process, based only on existing substrate:

1. single bad answer
2. capture as friction case
3. replay the case
4. classify mismatch family
5. mine repeated patterns / candidate clusters
6. generate governed update proposal
7. owner review
8. implement approved realization
9. replay before/after
10. publish a proof report
11. optionally promote into behavior pack or core selector rule
12. monitor regression

Status by step:
- 1–4: implemented
- 5: partial
- 6–9: implemented for the starter chain
- 10: review docs exist, but a dedicated runner is missing
- 11: docs-only concept, no registry yet
- 12: implemented as regression tests for the starter set

## SECTION 9 — Missing minimal modules

1. `friction_pattern_miner.py`
- needed for clustering repeated failures into generalized candidates
- reuse: capture, replay, assimilation, selector outputs
- must not: become runtime authority or model-dependent
- priority: soon

2. `friction_replay_suite_builder.py`
- needed to expand from hand-written starter cases into broader regression suites
- reuse: capture, replay harness, selector, renderer
- must not: auto-apply behavior or store raw prompts
- priority: soon

3. `behavior_pack_registry.py`
- needed to store reusable domain packs once repeated patterns are stable
- reuse: miner, capture, replay, proposal/governance surfaces
- must not: become a hidden live router or public-claim surface
- priority: later

4. `behavior_pack_promotion_policy.py`
- needed to define governed promotion rules into packs/core rules
- reuse: governance, proposal trace, proof gate, rollback planning
- must not: auto-promote or bypass owner review
- priority: later

5. `friction_training_proof_report_run.py`
- needed for a standardized before/after proof-report artifact
- reuse: replay harness, proposal traceability, governance surface, proof docs
- must not: claim certification or public readiness
- priority: later

## SECTION 10 — Recommended next lane

Recommended next lane:
- `DESIGN_WESLR_GENERALIZED_FRICTION_IMPROVEMENT_PROCESS_V1`

Why this first:
- the starter proof is real, but the generalized process is not yet canonical
- pattern mining and pack promotion should be designed before more code is added
- the repo already has enough governance to avoid a new parallel lifecycle
- after the design is frozen, implement `friction_pattern_miner.py` and then `behavior_pack_registry.py`

## SECTION 11 — Boundaries

Confirmed:
- no code changes
- no runtime behavior changes
- no chat route changes
- no model/provider/search/advisor calls
- no `.weslr` writes
- no raw private data
- no official intelligence / Turing / certification claims
- no AGI / consciousness / sentience claims
- no autonomous self-modification
- no protected runtime files touched

## SECTION 12 — Final judgment

do_not_design_new_process_reuse_existing_governance_and_add_missing_helpers

## Validation
- doc only
- protected files untouched: `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py`
- no implementation changes made
