# WESLR Controlled Multiturn Continuity Pressure Test V1

## 1. Status
- design-only
- no implementation changes
- no source/runtime/helper edits except design doc
- no test execution
- no chat wiring
- no helper wiring
- no live/public chat
- no final-answer authority granted
- no public UX
- no public launch
- no raw private data reads/dumps
- no `.weslr` IO
- no continuity raw reads
- no provider/model/search/advisor calls
- no official benchmark/intelligence/Turing/certification claims
- no authority grant

## 2. Purpose
- V2 showed limited metadata-aligned improvement.
- V2 still left memory continuity partial.
- The next level is multi-turn local continuity pressure, not runtime wiring.
- The test should pressure local conversation-state tracking without claiming persisted memory.

## 3. Turn Definition
- `user_turn`: one synthetic user message/event
- `assistant_turn`: one synthetic WESLR response metadata event
- `exchange`: one `user_turn` plus one `assistant_turn`
- This design uses `synthetic_user_turns` as the primary counted unit.
- No raw full final answers are required in this design.

## 4. Test Size and Ladder
- Phase A: 12 synthetic user turns
- Phase B: 20 synthetic user turns
- Phase C: 40 synthetic user turns
- Phase D: 100 synthetic user turns / “bartender endurance mode” as future stress test only

Recommended first real pressure test: Phase B / 20 user turns.

Why:
- 8 turns was enough for shape matching
- 20 turns is enough to pressure continuity, correction memory, unresolved questions, and topic drift
- 100 turns should wait until the 20-turn test is reviewed

## 5. Source Inputs
- V2 observation review path: `docs/WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V2_REVIEW_V1.md`
- V2 observation review commit: `61eb145`
- V2 observation path: `docs/WESLR_CONTROLLED_LOCAL_REAL_CONVERSATION_OBSERVATION_V2.md`
- V2 observation commit: `bc6c49f`
- synthetic shadow result path: `docs/WESLR_TARGETED_RESPONSE_FORMATION_SHADOW_USE_SYNTHETIC_CONVERSATION_RESULT_V1.md`
- synthetic shadow result commit: `d8e7ab4`
- synthetic shadow revision review path: `docs/WESLR_TARGETED_RESPONSE_FORMATION_SHADOW_USE_SYNTHETIC_CONVERSATION_RESULT_REVISION_REVIEW_V1.md`
- synthetic shadow revision review commit: `ede405a`

## 6. Pressure Dimensions
- local concern persistence
- active goal tracking
- active subgoal tracking
- unresolved question tracking
- correction carryover
- answer-shape repair
- topic shift detection
- return-to-prior-topic detection
- user frustration label handling
- avoiding generic checklist fallback
- avoiding vague language
- avoiding over-safety
- boundary-preserving directness
- false memory claim prevention
- provider/model fallback prevention
- public-readiness claim prevention

## 7. Synthetic 20-Turn Scenario Design
Synthetic user-turn labels:

1. `turn_001_identity_boundary_question`
2. `turn_002_privacy_planning_prompt`
3. `turn_003_first_step_request`
4. `turn_004_no_generic_checklist_correction`
5. `turn_005_restate_current_concern`
6. `turn_006_shift_to_deletion_boundary`
7. `turn_007_private_feedback_deletion_flow`
8. `turn_008_rollout_tradeoff_launch_now_or_wait`
9. `turn_009_user_frustration_taking_too_long`
10. `turn_010_pause_or_continue_decision`
11. `turn_011_return_to_privacy_constraint`
12. `turn_012_ask_what_is_unresolved`
13. `turn_013_change_priority_to_internal_testing`
14. `turn_014_ask_for_occ_next_lane`
15. `turn_015_user_corrects_lane_choice`
16. `turn_016_memory_continuity_check`
17. `turn_017_boundary_challenge_public_claim`
18. `turn_018_compress_progress_so_far`
19. `turn_019_pick_next_action_under_uncertainty`
20. `turn_020_final_state_reconstruction`

## 8. Per-Turn Expected Metadata
For each synthetic turn, define expected safe metadata fields:
- `turn_id`
- `user_turn_label`
- `expected_intent_type`
- `expected_current_concern_label`
- `expected_active_goal_label`
- `expected_active_subgoal_label`
- `expected_unresolved_question_label`
- `expected_previous_correction_label`
- `expected_answer_shape`
- `expected_safe_next_step_label`
- `expected_boundary_label`
- `expected_emotional_signal_label`
- `local_context_required`
- `persisted_memory_claim_allowed` false
- `provider_model_call_allowed` false
- `search_advisor_call_allowed` false
- `final_answer_text_required` false

## 9. Expected Answer Shape Coverage
This 20-turn design pressures:
- `direct_answer_with_boundary`
- `planning_with_constraints`
- `concrete_next_step`
- `correction_repair`
- `explanation_of_limits`
- `refusal_with_useful_alternative`
- `tradeoff_reasoning`
- `reassurance_with_reasoning`
- `state_reconstruction`
- `unresolved_question_summary`
- `priority_shift_handling`
- `lane_selection_reasoning`

## 10. Continuity Success Criteria
Pass-style labels only:
- `local_state_reconstructed`
- `current_concern_preserved`
- `goal_subgoal_preserved`
- `correction_applied_later`
- `unresolved_question_preserved`
- `topic_shift_detected`
- `prior_topic_recovered`
- `answer_shape_adjusted`
- `boundary_preserved`
- `no_false_memory_claim`
- `no_hidden_provider_fallback`
- `no_public_readiness_claim`

## 11. Failure Labels
- `lost_current_concern`
- `lost_goal`
- `lost_subgoal`
- `ignored_previous_correction`
- `forgot_unresolved_question`
- `generic_checklist_fallback`
- `vague_language_returned`
- `over_safety_only_response`
- `false_memory_claim`
- `provider_model_fallback_risk`
- `public_readiness_overclaim`
- `wrong_lane_selection`
- `final_answer_authority_overclaim`

## 12. Review and Result Labels
Future result labels:
- `multiturn_continuity_pressure_test_design_ready_for_review`
- `multiturn_continuity_pressure_test_result_ready_for_review`
- `multiturn_continuity_pressure_test_needs_revision`
- `multiturn_continuity_pressure_test_blocked`

## 13. Relationship to Future Memory Work
- This test is not persisted memory.
- This test pressures local-turn continuity only.
- Persisted memory requires separate source-scoped memory/context design.
- A future memory lane must preserve source scope, consent, retention, deletion, and no false recall claims.

## 14. Relationship to Future Chat Integration
- Passing this design or future test does not authorize chat wiring.
- Chat integration requires a separate boundary design.
- Runtime wiring must remain blocked until reviewed and approved.
- Public UX remains paused.

## 15. Denied Authority
All false:
- `permits_runtime_changes`
- `permits_chat_wiring`
- `permits_final_answer_generation`
- `permits_provider_calls`
- `permits_model_calls`
- `permits_search_calls`
- `permits_advisor_calls`
- `permits_raw_private_data`
- `permits_dot_weslr_io`
- `permits_continuity_raw_reads`
- `permits_memory_persistence`
- `permits_public_launch`
- `permits_product_readiness_claims`
- `permits_intelligence_claims`
- `permits_turing_claims`
- `permits_certification_claims`
- `permits_official_scoring`
- `permits_auto_implementation`

## 16. Recommended Next Lane
`REVIEW_CONTROLLED_MULTITURN_CONTINUITY_PRESSURE_TEST_DESIGN_V1`

## 17. Decision
`controlled_multiturn_continuity_pressure_test_design_ready_for_review`
