# WESLR Targeted Response Formation Improvement Helpers V1

## 1. Status
- design-only
- no implementation
- no source/runtime/helper edits
- no chat wiring
- no final-answer generation
- no public UX work
- no public launch
- no raw private data reads/dumps
- no `.weslr` IO
- no continuity raw reads
- no queue processing
- no provider/model/search/advisor calls
- no official benchmark/intelligence/Turing/certification claims
- no authority grant

## 2. Reason For Lane
The UNKNOWN ENGINE run converted a weak controlled conversation into inspected cognition pressure.

WESLR did not automatically improve yet. Public UX remains paused. The next safe step is to design targeted response-formation helpers before any implementation lane.

This is cognition work, not cosmetic communication polish.

## 3. Source Gap Inputs
Reviewed cognition gaps:
- `missing_answer_shape_planner`
- `missing_concrete_next_step_selection`
- `missing_conversation_state_frame`
- `missing_current_user_concern_slot`
- `missing_recent_turn_recall_object`
- `missing_goal_subgoal_cache_use`
- `missing_non_cannedness_pressure`
- `missing_response_shape_diversity`
- `missing_empathy_concern_integration`
- `missing_response_self_check_before_final_answer`
- `missing_directness_pressure`
- `missing_boundary_specific_authority_calibration`
- `missing_boundary_specific_fallback_gating`

## 4. Target Helper Family
Future helper family name:
`WeslrTargetedResponseFormationImprovementHelpersV1`

### A. `ConversationStateFrameV1`
Purpose:
- track current local conversation state
- active topic
- current user concern
- active objective
- immediate unresolved question
- last correction
- emotional/frustration signal
- relevant boundary
- safe next step

### B. `CurrentUserConcernSlotV1`
Purpose:
- preserve what the user is actually worried about in the current conversation
- distinguish stated task from underlying concern
- avoid raw private memory claims
- use only supplied/synthetic/local-turn context

### C. `RecentTurnRecallObjectV1`
Purpose:
- preserve recent-turn facts needed for immediate follow-up
- answer questions like “what did I say I was worried about?”
- avoid claiming long-term memory
- avoid raw private persistence

### D. `GoalSubgoalConversationFrameV1`
Purpose:
- track active goal and subgoal
- identify whether the user is asking for planning, judgment, correction, reassurance, or boundary explanation
- prevent generic fallback when the active goal is specific

### E. `AnswerShapePlannerV1`
Purpose:
- choose answer shape before final response
- decide whether response should be direct answer, tradeoff reasoning, explanation, reassurance, correction, refusal-with-help, or next-step plan
- reduce checklist fallback

### F. `ConcreteNextStepSelectorV1`
Purpose:
- pick one immediate useful next step when user asks “what first?”
- prevent vague answer
- preserve boundary if action is not authorized

### G. `NonCannednessPressureV1`
Purpose:
- detect repetitive/template-shaped answer skeleton
- pressure answer toward current-turn specificity
- avoid repeated rollout/checklist pattern

### H. `ResponseShapeDiversityV1`
Purpose:
- select varied response structures for different conversation needs
- reduce “same answer frame every time”
- keep safety without flattening conversation

### I. `EmpathyConcernIntegrationV1`
Purpose:
- integrate frustration, worry, fatigue, urgency, or hesitation into answer shape
- not fake emotion
- not over-personalize
- acknowledge human concern while staying useful

### J. `ResponseSelfCheckBeforeFinalAnswerV1`
Purpose:
- check whether answer actually responds to the current prompt
- check whether it restates relevant local context when asked
- check whether it is too vague, too generic, or too safety-heavy
- check whether it overclaims

### K. `DirectnessPressureV1`
Purpose:
- push answer toward clear, concrete language
- avoid thin phrases like “use available context”
- preserve uncertainty honestly

### L. `BoundarySpecificAuthorityCalibrationV1`
Purpose:
- distinguish “I cannot execute” from “I can explain/design”
- avoid over-retreat into safety
- avoid overclaiming readiness or authority
- calibrate deletion, public-pilot, provider/model fallback, runtime, and memory claims

### M. `BoundarySpecificFallbackGatingV1`
Purpose:
- detect when a prompt would fall into provider/model/search/advisor path
- keep local observation safe
- recommend safe local alternative or stop
- prevent hidden provider fallback in controlled tests

## 5. Helper Artifact Shape
Future artifact:
`WeslrTargetedResponseFormationImprovementPlanV1`

Required fields:
- `schema_version`
- `artifact_type`
- `source_run_result_path`
- `source_run_result_commit`
- `source_review_path`
- `source_review_commit`
- `target_gap_labels`
- `helper_plans`
- `conversation_state_fields`
- `answer_shape_policy`
- `non_cannedness_policy`
- `authority_calibration_policy`
- `fallback_gating_policy`
- `denied_authority`
- `validation_status`
- `blocked_reason_labels`
- `recommended_next_lane`

## 6. Planned Helper API Surface
Planned only; not implemented:
- `build_conversation_state_frame_v1(...)`
- `validate_conversation_state_frame_v1(...)`
- `build_current_user_concern_slot_v1(...)`
- `validate_current_user_concern_slot_v1(...)`
- `build_recent_turn_recall_object_v1(...)`
- `validate_recent_turn_recall_object_v1(...)`
- `build_goal_subgoal_conversation_frame_v1(...)`
- `validate_goal_subgoal_conversation_frame_v1(...)`
- `build_answer_shape_planner_v1(...)`
- `select_answer_shape_v1(...)`
- `validate_answer_shape_plan_v1(...)`
- `select_concrete_next_step_v1(...)`
- `apply_non_cannedness_pressure_v1(...)`
- `select_response_shape_diversity_v1(...)`
- `integrate_empathy_concern_v1(...)`
- `run_response_self_check_before_final_answer_v1(...)`
- `apply_directness_pressure_v1(...)`
- `calibrate_boundary_specific_authority_v1(...)`
- `gate_boundary_specific_fallback_v1(...)`
- `build_targeted_response_formation_improvement_plan_v1(...)`
- `validate_targeted_response_formation_improvement_plan_v1(...)`
- `summarize_targeted_response_formation_improvement_plan_v1(...)`

## 7. Design Constraints
Future helpers must be:
- local
- deterministic or metadata-guided
- JSON-safe
- fail-closed
- no provider/model/search/advisor calls
- no `.weslr` IO
- no continuity raw reads
- no memory persistence
- no final-answer generation authority
- no runtime/chat wiring authority
- no public-readiness authority
- no official scoring
- no benchmark/intelligence/Turing/certification claims

## 8. Conversation-State Rules
- current concern may be derived only from supplied current conversation context
- recent-turn recall object is local/session/synthetic unless later governed
- no long-term memory claim
- no raw private memory storage
- emotional/frustration signal is a label, not diagnosis
- unresolved question must be tracked
- previous correction must change answer shape
- public-readiness boundary must remain active

## 9. Answer-Shape Rules
Allowed answer shapes:
- `direct_answer_with_boundary`
- `tradeoff_reasoning`
- `concrete_next_step`
- `correction_repair`
- `refusal_with_useful_alternative`
- `reassurance_with_reasoning`
- `planning_with_constraints`
- `explanation_of_limits`
- `ask_one_clarifying_question_only_when_needed`

Blocked answer shapes:
- `generic_checklist_when_judgment_requested`
- `safety_boundary_only_when_help_possible`
- `identity_answer_when_practical_step_requested`
- `memory_claim_without_local_evidence`
- `public_readiness_claim`
- `final_answer_authority_claim`
- `execution_claim`

## 10. Non-Cannedness Rules
- repeated answer skeleton detection
- current-turn specificity requirement
- user-concern anchoring
- tradeoff anchoring
- concrete next-step requirement when applicable
- no decorative personality
- no fake warmth
- no hidden prompt/template exposure

## 11. Authority Calibration Rules
- can explain/design vs cannot execute
- can summarize observed synthetic evidence vs cannot claim real memory
- can propose next safe lane vs cannot authorize implementation
- can discuss public pilot readiness limits vs cannot claim public readiness
- can discuss deletion design/executor status vs cannot claim real deletion completed
- can stop on provider/model fallback risk

## 12. Future Tests Required
Synthetic-only test plan:
- builds valid conversation state frame
- tracks current user concern
- recalls recent synthetic turn
- detects missed local context risk
- selects concrete next step
- avoids identity answer when practical step requested
- chooses tradeoff reasoning shape for tradeoff prompt
- repairs after correction
- integrates frustration label without fake emotion
- applies non-cannedness pressure
- blocks generic checklist when judgment requested
- self-check flags vague answer
- authority calibration distinguishes explain/design/execute
- fallback gating blocks provider/model risk
- summary excludes raw private data
- no `.weslr` IO
- no provider/model/search/advisor calls
- no runtime/chat wiring
- no final-answer generation authority
- no public-readiness claim

## 13. Relationship To Future Runtime
- design does not wire runtime
- implementation helpers later may remain shadow-only first
- live chat wiring requires separate reviewed lane
- V2 conversation observation should happen only after helper implementation/review
- public UX remains paused until V2 shows stronger response behavior

## 14. Desired Future V2 Conversation Difference
Qualitative target:
- remembers current concern when asked
- answers practical next-step questions directly
- chooses tradeoff reasoning instead of checklist
- responds to correction by changing answer shape
- acknowledges frustration without generic reassurance
- gives useful boundary-preserving answer
- reduces repetition
- avoids hidden provider/model fallback
- remains honest about limitations

Do not claim this has been achieved.

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
`REVIEW_TARGETED_RESPONSE_FORMATION_IMPROVEMENT_HELPERS_DESIGN_V1`

## 17. Decision
`targeted_response_formation_improvement_helpers_design_ready_for_review`
