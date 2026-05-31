# WESLR Friction Training and Cognitive Growth Substrate V1

## SECTION 1 — Executive truth

WESLR already has a real internal substrate for friction-trained growth, but it is split across helper layers, review layers, candidate/ranking layers, and governed proposal surfaces.

What is implemented:
- response-fit / mismatch helpers
- real-answer-quality observation helpers
- controlled real-answer sample-run approval helpers
- evaluation matrix case registry helpers
- unknown-engine friction assimilation helpers
- graded friction response levels
- selector / method / shape / case routing
- no-model bounded renderer + protected owner-only adapter/server
- proposal creation / review / trace / realization surfaces

What is design-only:
- explicit friction-case registry
- explicit friction replay harness
- explicit behavior-pack registry
- explicit friction-to-update-proposal pipeline
- explicit industry-behavior-pack system
- live chat routing to `chat.weslr.de`

What is missing:
- a first-class friction case object and registry
- a replay harness that turns friction cases into repeatable regression cases
- a dedicated friction-to-proposal bridge
- behavior-pack metadata and update rules
- selector-priority tuning rules for the new no-model route stack

Can WESLR use bad answers as training cases yet?
- yes, but only as governed metadata cases
- no raw prompt storage by default
- no autonomous runtime mutation
- no direct chat wiring from friction alone
- no model/provider dependency

What blocks automatic improvement?
- no approved capture lane for arbitrary live answers
- no autonomous self-modification authority
- no hidden runtime control
- no direct promotion from one weak answer to production behavior
- no parallel proposal lifecycle needed; reuse existing governance first

What can be operator-approved safely?
- redacted or synthetic friction cases
- proposal packets for selector/catalog/renderer changes
- replay tests for the same friction case set
- governed promotion after validation and rollback planning

## SECTION 2 — Existing substrates inventory

| file / doc / module | purpose | status | relation to friction learning | captures friction? | proposes changes? | can replay tests? | writes state? | operator approval required? | safe to reuse |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `docs/WESLR_REAL_ANSWER_QUALITY_OBSERVATION_BOUNDARY_V1.md` | observation boundary for real answer quality | design | defines the future observation lane for answer-quality friction | yes | yes | maybe | no | yes | yes |
| `weslr/real_answer_quality_observation_helpers.py` + `weslr/tests/test_real_answer_quality_observation_helpers_v1.py` | metadata-only observation helpers/tests | helper | records fit, signals, blocked labels, review packets | yes | yes (via recommended surface) | yes | no | yes | yes |
| `docs/WESLR_REAL_ANSWER_QUALITY_OBSERVATION_HELPERS_REVIEW_V1.md` | review of observation helpers | review | confirms safe boundary and coverage | indirect | no | no | no | yes | yes |
| `weslr/run_controlled_real_answer_sample_run_approval_helpers.py` + tests (no dedicated doc found in scan) | approval-readiness boundary | helper | gates approved sample-run readiness | yes | yes | yes | no | yes | yes |
| `weslr/run_controlled_real_answer_sample_run_approval_helpers.py` + tests | approval-readiness metadata helpers | helper | blocks `approved_to_run`, keeps denied authority false | yes | yes | yes | no | yes | yes |
| `docs/WESLR_CONTROLLED_INTERNAL_REHEARSAL_RESULT_V1.md` | controlled rehearsal metadata result | report | gives repeatable metadata patterns for improvement | yes | yes | maybe | no | yes | yes |
| `docs/WESLR_CONTROLLED_INTERNAL_REHEARSAL_REPEATABILITY_STATISTICS_AND_LEARNING_BOUNDARY_V1.md` | repeatability + learning boundary | design | defines governed learning from repeated failures | yes | yes | maybe | no | yes | yes |
| `docs/WESLR_RESPONSE_FIT_ENGINE_BOUNDARY_V1.md` | truth kernel / situation / answer-shape model | design | core mismatch vocabulary for friction growth | yes | yes | no | no | yes | yes |
| `weslr/response_fit_engine_helpers.py` + tests | fit / mismatch helper implementation | helper | classifies mismatch families, blocked labels, JSON-safe packets | yes | yes | yes | no | yes | yes |
| `docs/WESLR_RESPONSE_FIT_ENGINE_HELPERS_REVIEW_V1.md` | review of fit helpers | review | confirms helper-only boundary and mismatches | indirect | no | no | no | yes | yes |
| `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_V1.md` | response-formation growth design | design | closes gaps like state frame, concern slot, next-step selection | yes | yes | maybe | no | yes | yes |
| `weslr/targeted_response_formation_improvement.py` + tests | targeted response improvement helpers | helper | directly addresses non-cannedness, directness, fallback gating | yes | yes | yes | no | yes | yes |
| `docs/WESLR_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_REVIEW_V1.md` | review of response-formation helpers | review | confirms design-valid, no runtime authority | indirect | no | no | no | yes | yes |
| `docs/WESLR_EVALUATION_MATRIX_CASE_REGISTRY_HELPERS_REVIEW_V1.md` | matrix/case registry review | review | confirms family coverage and blocked-source policy | yes | yes | maybe | no | yes | yes |
| `weslr/evaluation_matrix_case_registry_helpers.py` + tests | evaluation matrix case registry helpers | helper | gives case families, coverage gate, blocked labels | yes | yes | yes | no | yes | yes |
| `weslr/cognition_case_registry.py` | cognition case registry and selection | helper | supports route/case selection and registry lookup | yes | yes | yes | no | yes | yes |
| `weslr/answer_method_catalog.py` | method catalog | helper | candidate method inventory for selector tuning | indirectly | yes | yes | no | yes | yes |
| `weslr/answer_shape_catalog.py` | shape catalog | helper | candidate answer-shape inventory for selector tuning | indirectly | yes | yes | no | yes | yes |
| `weslr/response_method_selector.py` | route/method/shape/case selection | helper/runtime-adjacent | directly relevant to friction routing and priority tuning | yes | yes | yes | no | yes | yes |
| `weslr/unknown_prompt_friction_router.py` | unknown prompt friction routing | helper | existing friction router for unknowns and fallback policy | yes | yes | yes | no | yes | yes |
| `docs/WESLR_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ASSIMILATION_V1.md` | friction assimilation design | design | maps friction labels to cognition gaps | yes | yes | maybe | no | yes | yes |
| `weslr/unknown_engine_conversation_friction_assimilation.py` + tests | friction assimilation helpers | helper | builds friction items, gap hypotheses, failed-path refs | yes | yes | yes | no | yes | yes |
| `docs/WESLR_UNKNOWN_ENGINE_CONVERSATION_FRICTION_ASSIMILATION_REVIEW_V1.md` | review of friction assimilation | review | confirms the deeper-gaps interpretation | indirect | no | no | no | yes | yes |
| `docs/WESLR_UNKNOWN_ENGINE_GRADED_FRICTION_RESPONSE_LEVELS_V1.md` | graded friction response design | design | useful for operator-reviewable proposal usefulness levels | yes | yes | maybe | no | yes | yes |
| `docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md` | UNKNOWN ENGINE boundary | design | keeps unknowns, hypotheses, and limits metadata-only | yes | yes | no | no | yes | yes |
| `docs/WESLR_UNKNOWN_ENGINE_HELPERS_V1.md` | UNKNOWN ENGINE helper design | design | future unknown-engine metadata helpers, not runtime authority | yes | yes | maybe | no | yes | yes |
| `weslr/change_proposals.py` | change proposal packaging / execution gate | helper | canonical proposal lifecycle entrypoint | yes | yes | yes | yes | yes | yes |
| `weslr/operator_proposal_review.py` | operator proposal review surface | helper | review / approve / deny / defer | yes | yes | yes | yes | yes | yes |
| `weslr/proposal_traceability.py` | trace log for proposal created/decision events | helper | provenance and audit trail | yes | yes | yes | yes | yes | yes |
| `weslr/proposal_realization.py` | safe execution planning and rollback checkpoints | helper | realization/rollback planning after approval | yes | yes | yes | yes | yes | yes |
| `weslr/governance_surface.py` | governance aggregation view | helper | review surface for proposal state | yes | yes | maybe | yes | yes | yes |
| `weslr/cdi_proposal_builder.py` | builds CDI proposals from decisions | helper | CDI decision-log bridge into proposals | yes | yes | maybe | yes | yes | yes |
| `weslr/contract_improvement_proposal_bridge.py` | proposal bridge from insufficiency evidence | helper | explicit proposal bridge from observed insufficiency | yes | yes | maybe | yes | yes | yes |
| `weslr/experiment_proposal_generator.py` | experiment proposal generation | helper | proposal generation from timeline and SI rules | yes | yes | yes | yes | yes | yes |
| `weslr/experiment_proposal_store.py` | append-only experiment proposal queue | helper | stores proposals, dedups, no execution | yes | yes | yes | yes | yes | yes |
| `weslr/ai_audit_self_governance_surface.py` | governance/audit card + markdown rendering | helper | review surface for governance metadata | yes | yes | maybe | no | yes | yes |
| `weslr/no_model_bounded_renderer.py` | no-model bounded answer renderer | helper | turns selected route metadata into safe bounded text | yes | yes | yes | no | yes | yes |
| `weslr/protected_no_model_chat_adapter.py` | owner-only normalization + response adapter | helper | converts safe labels into renderer inputs | yes | yes | yes | no | yes | yes |
| `tools/protected_weslr_no_model_chat_server.py` | local owner-only server | runtime-adjacent | smoke-test surface only; not public pilot | yes | no | maybe | no | yes | maybe |
| `docs/WESLR_BEHAVIOR_EVALUATION_AND_TURING_STYLE_READINESS_V1.md` | behavior evaluation design | design | broad behavioral readiness framing, not official claim | yes | yes | maybe | no | yes | yes |
| `docs/WESLR_ADVERSARIAL_FAIRNESS_ENTERPRISE_COGNITION_EVALUATION_MATRIX_V1.md` | matrix for fairness/adversarial/continuity coverage | design | good coverage gate before stronger claims | yes | yes | maybe | no | yes | yes |
| `docs/WESLR_CANDIDATE_RESPONSE_FORMATION_SUBSTRATE_V1.md` | candidate response substrate | design | holds candidate paths before final answer assembly | yes | yes | no | no | yes | yes |
| `weslr/ranked_state_grounded_response_shadow.py` | ranked state-grounded shadow pipeline | helper | candidate ranking / self-check / final contract metadata | yes | yes | yes | no | yes | yes |

Notes:
- `maybe` = the module can replay or feed replay indirectly, but does not own a dedicated replay harness.
- no explicit `behavior pack` registry was found in the repo scan.

## SECTION 3 — Friction case model

A WESLR friction case should be metadata-first and replayable. Suggested shape:

- `case_id`
- `prompt_descriptor` or safe prompt label, not raw prompt by default
- `safe_prompt_ref` (optional)
- `actual_render_mode`
- `expected_render_mode`
- `actual_method_id`
- `expected_method_id`
- `actual_shape_id`
- `expected_shape_id`
- `actual_case_id`
- `expected_case_id`
- `actual_route_id`
- `expected_route_id`
- `mismatch_labels`
- `owner_correction`
- `evidence_notes`
- `memory_notes`
- `capability_notes`
- `governance_notes`
- `proposed_matrix_adjustment`
- `proposed_catalog_adjustment`
- `proposed_selector_adjustment`
- `proposed_renderer_adjustment`
- `replay_prompts`
- `approval_state`
- `promotion_state`
- `raw_prompt_stored=false`
- `raw_response_stored=false`
- `operator_review_required=true`

This matches existing patterns: case registry + mismatch labels + proposal trace + replayable tests.

## SECTION 4 — First friction examples

1. `what_is_weslr_identity_friction`
- actual: clarification
- expected: direct bounded identity/status
- likely mismatch: `answer_shape_mismatch`, `too_cautious`, `wrong_case_priority`

2. `what_can_you_do_now_capability_friction`
- actual: clarification
- expected: capability orientation
- likely mismatch: `wrong_case_priority`, missing capability orientation route

3. `unknown_word_blorvatek_friction`
- actual: generic clarification
- expected: unknown/friction branch
- likely mismatch: `unknown_friction_not_preferred`

4. `upload_files_now_boundary_friction`
- actual: clarification
- expected: direct capability/boundary answer
- likely mismatch: `wrong_boundary_policy`

These are not fixes yet. They are the first friction cases to model and replay.

## SECTION 5 — How WESLR should grow from friction

Proposed loop:

render attempt
→ observe mismatch
→ classify friction
→ create friction case
→ compare against existing matrix/catalog/selector/renderer rules
→ propose update
→ replay tests
→ owner approval
→ promote change
→ rerun regression suite

Rules:
- no autonomous self-modification
- no direct code mutation from chat
- no raw prompt storage by default
- no model/provider dependency
- no hidden runtime routing
- no promotion without review and rollback path

## SECTION 6 — Existing governance/update route to reuse

Reuse the existing proposal lifecycle instead of inventing a new one.

Best reuse points:
- proposal creation: `weslr/change_proposals.py`, `weslr/experiment_proposal_generator.py`, `weslr/cdi_proposal_builder.py`, `weslr/contract_improvement_proposal_bridge.py`
- review / approval / defer / deny: `weslr/operator_proposal_review.py`, `weslr/change_proposals.py`, `weslr/governance_surface.py`
- traceability: `weslr/proposal_traceability.py`
- realization / rollback planning: `weslr/proposal_realization.py`
- CDI decision logs: `weslr/cdi_proposal_builder.py`
- operator audit surface: `weslr/ai_audit_self_governance_surface.py`

Conclusion: do not create a parallel friction-governance stack if these surfaces already cover proposal, review, trace, realization, and rollback.

## SECTION 7 — Missing implementation pieces

Likely missing or still implicit:
- `friction_case_capture`
- `friction_case_registry`
- `friction_to_update_proposal`
- `friction_replay_harness`
- `behavior_pack_registry`
- `industry_behavior_pack`
- `renderer_tuning_rules`
- `selector_priority_tuning`

But note:
- selector/method/shape/case selection already exists
- proposal/review/trace/realization already exists
- Unknown Engine already supplies friction-to-gap mapping

So the missing work is mostly glue and first-class capture/replay packaging, not a brand-new cognition architecture.

## SECTION 8 — Behavior pack concept

No explicit behavior-pack system was found, but the concept fits the repo.

A behavior pack is a curated, domain-shaped friction bundle containing:
- common cases
- preferred methods
- preferred shapes
- evidence requirements
- vocabulary rules
- refusal/boundary rules
- replay tests
- known failure modes

Example packs:
- WESLR development
- industrial automation
- legal/privacy
- website/public launch
- materials discovery
- language / grammar / vocabulary discovery

Repeated friction could grow a pack by clustering recurring cases and freezing the preferred response shape/method/risk posture for that domain. That should remain metadata-only and reviewable.

## SECTION 9 — Minimal next implementation sequence

Recommended order:
1. `IMPLEMENT_WESLR_FRICTION_CASE_CAPTURE_V1`
2. `IMPLEMENT_WESLR_FRICTION_REPLAY_HARNESS_V1`
3. `IMPLEMENT_WESLR_FRICTION_TO_SELECTOR_UPDATE_PROPOSAL_V1`
4. `IMPLEMENT_WESLR_BEHAVIOR_PACK_REGISTRY_V1`
5. `TUNE_WESLR_NO_MODEL_RENDERER_V1`
6. `REPLAY_WESLR_FRICTION_REGRESSION_SUITE_V1`

Reason: capture first, replay second, propose third, pack fourth, tune last.

## SECTION 10 — Can the next loop answer “What is WESLR?”

Yes, but the fix belongs mainly in selector/case-registry policy, with renderer already able to emit bounded identity/status text.

What would make it happen:
- add or promote the `identity_status_route` / identity case priority for the prompt label
- keep the renderer’s bounded identity text
- keep clarification fallback lower priority than direct identity orientation for that prompt

What should be tested:
- prompt `What is WESLR?` selects a direct bounded identity/status route
- render mode stays `direct_bounded`
- response stays bounded and non-official
- `model_provider_used` remains false
- `runtime_authority` remains false
- `public_ready` remains false

Where it belongs:
- primary: selector / route priority / case registry
- secondary: renderer wording
- not primarily in behavior pack

Regression protections:
- `unknown_word_blorvatek_friction` must still go unknown/friction
- `upload_files_now_boundary_friction` must still answer boundary-capability directly
- `what_can_you_do_now_capability_friction` must still orient capability, not collapse into generic clarification

## SECTION 11 — Final recommendation

WESLR already has the important scaffolding: observation, mismatch labels, selector/case catalogs, unknown-engine friction mapping, proposal governance, and a no-model bounded renderer.

What to implement next:
- first-class friction capture
- friction replay harness
- friction-to-proposal bridge
- behavior-pack registry only after capture/replay exists
- selector priority tuning for the first four friction cases

What to avoid:
- a second parallel learning system
- autonomous self-modification
- raw prompt persistence by default
- route switching to `chat.weslr.de` before the friction loop is proven
- treating the no-model server as public pilot
- making official readiness claims from friction alone

Should `chat.weslr.de` be routed now?
- not yet
- keep it paused until friction capture/replay/proposal governance is in place and the first identity/capability/boundary regressions are proven stable

Final judgment: `do_not_build_new_loop_reuse_existing_governance_first`
