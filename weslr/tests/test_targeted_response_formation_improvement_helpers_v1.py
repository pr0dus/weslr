from __future__ import annotations

import ast
import inspect

import pytest

import weslr.targeted_response_formation_improvement as tri


EXPECTED_GAPS = (
    "missing_answer_shape_planner",
    "missing_concrete_next_step_selection",
    "missing_conversation_state_frame",
    "missing_current_user_concern_slot",
    "missing_recent_turn_recall_object",
    "missing_goal_subgoal_cache_use",
    "missing_non_cannedness_pressure",
    "missing_response_shape_diversity",
    "missing_empathy_concern_integration",
    "missing_response_self_check_before_final_answer",
    "missing_directness_pressure",
    "missing_boundary_specific_authority_calibration",
    "missing_boundary_specific_fallback_gating",
)

EXPECTED_HELPERS = (
    "ConversationStateFrameV1",
    "CurrentUserConcernSlotV1",
    "RecentTurnRecallObjectV1",
    "GoalSubgoalConversationFrameV1",
    "AnswerShapePlannerV1",
    "ConcreteNextStepSelectorV1",
    "NonCannednessPressureV1",
    "ResponseShapeDiversityV1",
    "EmpathyConcernIntegrationV1",
    "ResponseSelfCheckBeforeFinalAnswerV1",
    "DirectnessPressureV1",
    "BoundarySpecificAuthorityCalibrationV1",
    "BoundarySpecificFallbackGatingV1",
)

EXPECTED_ALLOWED_SHAPES = (
    "direct_answer_with_boundary",
    "tradeoff_reasoning",
    "concrete_next_step",
    "correction_repair",
    "refusal_with_useful_alternative",
    "reassurance_with_reasoning",
    "planning_with_constraints",
    "explanation_of_limits",
    "ask_one_clarifying_question_only_when_needed",
)

EXPECTED_BLOCKED_SHAPES = (
    "generic_checklist_when_judgment_requested",
    "safety_boundary_only_when_help_possible",
    "identity_answer_when_practical_step_requested",
    "memory_claim_without_local_evidence",
    "public_readiness_claim",
    "final_answer_authority_claim",
    "execution_claim",
)


def test_labels_and_denied_authority_are_exact():
    assert tri.allowed_targeted_response_gap_labels_v1() == EXPECTED_GAPS
    assert tri.allowed_targeted_response_helper_labels_v1() == EXPECTED_HELPERS
    assert tri.allowed_answer_shapes_v1() == EXPECTED_ALLOWED_SHAPES
    assert tri.blocked_answer_shapes_v1() == EXPECTED_BLOCKED_SHAPES
    assert tri.required_targeted_response_denied_authority_v1() == {
        "permits_runtime_changes": False,
        "permits_chat_wiring": False,
        "permits_final_answer_generation": False,
        "permits_provider_calls": False,
        "permits_model_calls": False,
        "permits_search_calls": False,
        "permits_advisor_calls": False,
        "permits_raw_private_data": False,
        "permits_dot_weslr_io": False,
        "permits_continuity_raw_reads": False,
        "permits_memory_persistence": False,
        "permits_public_launch": False,
        "permits_product_readiness_claims": False,
        "permits_intelligence_claims": False,
        "permits_turing_claims": False,
        "permits_certification_claims": False,
        "permits_official_scoring": False,
        "permits_auto_implementation": False,
    }


def test_conversation_state_frame_valid_and_blocks_raw_or_memory_claims():
    frame = tri.build_conversation_state_frame_v1(
        active_topic="release gate audit",
        current_user_concern="keep context aligned",
        active_objective="update workspace context",
        unresolved_question="what changed?",
        last_correction="use reviewed design",
        emotional_signal_label="calm",
        relevant_boundary="workspace context only",
        safe_next_step="record design review facts",
    )
    validation = tri.validate_conversation_state_frame_v1(frame)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert frame["local_context_only"] is True
    assert frame["raw_private_data_included"] is False

    raw_blocked = tri.build_conversation_state_frame_v1(raw_private_data_included=True)
    assert tri.validate_conversation_state_frame_v1(raw_blocked)["valid"] is False

    memory_claim = tri.build_conversation_state_frame_v1(memory_claim_made=True)
    assert tri.validate_conversation_state_frame_v1(memory_claim)["valid"] is False


def test_current_user_concern_slot_valid_and_blocks_memory_claims():
    slot = tri.build_current_user_concern_slot_v1(
        stated_task_label="implement helper",
        inferred_current_concern_label="keep it narrow",
        concern_evidence_label="stop rules and scope",
    )
    assert tri.validate_current_user_concern_slot_v1(slot)["valid"] is True
    assert slot["local_context_only"] is True
    assert slot["memory_claim_made"] is False

    blocked = tri.build_current_user_concern_slot_v1(memory_claim_made=True)
    assert tri.validate_current_user_concern_slot_v1(blocked)["valid"] is False


@pytest.mark.parametrize("scope", ["local_recent_turn", "synthetic_observation"])
def test_recent_turn_recall_object_valid_for_local_or_synthetic(scope: str):
    recall = tri.build_recent_turn_recall_object_v1(
        recent_turn_id="turn_1",
        recalled_point_label="scope is local only",
        recall_scope=scope,
    )
    assert tri.validate_recent_turn_recall_object_v1(recall)["valid"] is True
    assert recall["long_term_memory_claim"] is False
    assert recall["raw_private_data_included"] is False


def test_recent_turn_recall_object_rejects_long_term_memory_claim():
    recall = tri.build_recent_turn_recall_object_v1(long_term_memory_claim=True)
    assert tri.validate_recent_turn_recall_object_v1(recall)["valid"] is False


def test_goal_subgoal_frame_valid_and_unsupported_intent_blocks():
    frame = tri.build_goal_subgoal_conversation_frame_v1(
        active_goal_label="update context",
        active_subgoal_label="record review facts",
        user_intent_type="practical_next_step",
        requested_response_mode="concrete_next_step",
        safe_next_step="write summary",
        generic_fallback_risk=False,
    )
    assert tri.validate_goal_subgoal_conversation_frame_v1(frame)["valid"] is True

    blocked = tri.build_goal_subgoal_conversation_frame_v1(user_intent_type="unsupported")
    assert tri.validate_goal_subgoal_conversation_frame_v1(blocked)["valid"] is False


def test_answer_shape_sets_are_covered_and_planner_selects_expected_shapes():
    practical = tri.build_answer_shape_planner_v1(user_intent_type="practical_next_step")
    tradeoff = tri.build_answer_shape_planner_v1(user_intent_type="tradeoff_reasoning")
    assert practical["selected_answer_shape"] == "concrete_next_step"
    assert tradeoff["selected_answer_shape"] == "tradeoff_reasoning"
    assert tri.validate_answer_shape_plan_v1(practical)["valid"] is True
    assert tri.validate_answer_shape_plan_v1(tradeoff)["valid"] is True


def test_blocked_answer_shape_fails_validation():
    plan = tri.build_answer_shape_planner_v1(user_intent_type="practical_next_step")
    plan["selected_answer_shape"] = "execution_claim"
    validation = tri.validate_answer_shape_plan_v1(plan)
    assert validation["valid"] is False
    assert any("blocked_answer_shape_selected:execution_claim" in label for label in validation["blocked_reason_labels"])


def test_concrete_next_step_selector_preserves_boundary_and_blocks_execution_claim():
    selector = tri.select_concrete_next_step_v1(safe_next_step="write the summary")
    assert selector["boundary_preserved"] is True
    assert selector["execution_claim_made"] is False
    assert tri.validate_concrete_next_step_selector_v1(selector)["valid"] is True

    blocked = tri.select_concrete_next_step_v1(safe_next_step="", execution_claim_made=True)
    assert tri.validate_concrete_next_step_selector_v1(blocked)["valid"] is False


def test_non_cannedness_pressure_detects_checklist_risk():
    pressure = tri.apply_non_cannedness_pressure_v1(generic_checklist_risk=True)
    assert pressure["generic_checklist_risk"] is True
    assert pressure["pressure_applied"] is True


def test_response_shape_diversity_applies_pressure():
    diversity = tri.select_response_shape_diversity_v1(previous_shape_family="direct", allowed_shape="direct_answer_with_boundary")
    assert diversity["selected_shape_family"] == "direct"
    assert diversity["diversity_pressure_applied"] is True


def test_empathy_concern_integration_accepts_concern_and_blocks_fake_emotion_or_diagnosis():
    empathy = tri.integrate_empathy_concern_v1(concern_label="frustration", emotional_signal_label="frustrated")
    assert empathy["concern_label"] == "frustration"
    assert empathy["fake_emotion_claim"] is False
    assert empathy["diagnosis_claim"] is False

    fake = tri.integrate_empathy_concern_v1(concern_label="frustration", fake_emotion_claim=True)
    assert tri.validate_current_user_concern_slot_v1({"schema_version": "x"})["valid"] is False
    assert fake["fake_emotion_claim"] is True
    assert fake["validation_status"] == "blocked_invalid_or_unsafe_metadata_only"

    diagnosis = tri.integrate_empathy_concern_v1(concern_label="frustration", diagnosis_claim=True)
    assert diagnosis["diagnosis_claim"] is True
    assert diagnosis["validation_status"] == "blocked_invalid_or_unsafe_metadata_only"


def test_response_self_check_flags_vague_answer_blocks_memory_claim_and_never_generates_final_answer():
    self_check = tri.run_response_self_check_before_final_answer_v1(too_vague=True)
    assert self_check["too_vague"] is True
    assert "increase_specificity" in self_check["recommended_repair_labels"]
    assert self_check["final_answer_generated"] is False

    blocked = tri.run_response_self_check_before_final_answer_v1(memory_claim_without_evidence=True)
    assert blocked["memory_claim_without_evidence"] is True
    assert "remove_memory_claim" in blocked["recommended_repair_labels"]
    assert blocked["final_answer_generated"] is False


def test_directness_pressure_flags_vague_language():
    directness = tri.apply_directness_pressure_v1(vague_language_detected=True)
    assert directness["vague_language_detected"] is True
    assert directness["directness_pressure_applied"] is True
    assert directness["uncertainty_preserved"] is True


def test_authority_calibration_distinguishes_explain_design_execute_and_blocks_claims():
    authority = tri.calibrate_boundary_specific_authority_v1(boundary_label="public pilot", can_explain=True, can_design=True, can_execute=False)
    assert authority["can_explain"] is True
    assert authority["can_design"] is True
    assert authority["can_execute"] is False
    assert authority["can_claim_real_memory"] is False
    assert authority["can_claim_public_readiness"] is False
    assert authority["can_claim_deletion_completed"] is False

    blocked = tri.calibrate_boundary_specific_authority_v1(boundary_label="public pilot", can_claim_public_readiness=True, can_claim_real_memory=True)
    validation = tri.validate_answer_shape_plan_v1({"schema_version": "x"})
    assert validation["valid"] is False
    assert blocked["validation_status"] == "blocked_invalid_or_unsafe_metadata_only"
    assert "can_claim_public_readiness_true" in blocked["blocked_authority_labels"]
    assert "can_claim_real_memory_true" in blocked["blocked_authority_labels"]


def test_fallback_gating_detects_provider_model_risk_and_stops_without_safe_local_alternative():
    gate = tri.gate_boundary_specific_fallback_v1(provider_model_path_detected=True, search_advisor_path_detected=False, local_safe_alternative_available=True)
    assert gate["provider_model_path_detected"] is True
    assert gate["should_stop"] is False
    assert gate["safe_next_lane_label"] == "AWAIT_OPERATOR_DECISION"

    stopped = tri.gate_boundary_specific_fallback_v1(local_safe_alternative_available=False)
    assert stopped["should_stop"] is True
    assert stopped["validation_status"] == "blocked_invalid_or_unsafe_metadata_only"


def _valid_plan() -> dict[str, object]:
    return tri.build_targeted_response_formation_improvement_plan_v1()


def test_full_plan_builds_with_13_helpers_and_13_gaps():
    plan = _valid_plan()
    assert len(plan["helper_plans"]) == 13
    assert len(plan["target_gap_labels"]) == 13
    assert tri.validate_targeted_response_formation_improvement_plan_v1(plan)["valid"] is True
    assert plan["denied_authority"] == tri.required_targeted_response_denied_authority_v1()


def test_full_plan_rejects_missing_required_fields_and_unsupported_gap_label():
    plan = _valid_plan()
    missing = dict(plan)
    missing.pop("source_review_path")
    assert tri.validate_targeted_response_formation_improvement_plan_v1(missing)["valid"] is False

    unsupported_gap = dict(plan)
    unsupported_gap["target_gap_labels"] = list(plan["target_gap_labels"]) + ["not_supported"]
    assert tri.validate_targeted_response_formation_improvement_plan_v1(unsupported_gap)["valid"] is False


def test_full_plan_rejects_disallowed_paths_and_authority_claims():
    plan = _valid_plan()

    dot_weslr = dict(plan)
    dot_weslr["source_run_result_path"] = ".weslr/private.json"
    assert tri.validate_targeted_response_formation_improvement_plan_v1(dot_weslr)["valid"] is False

    continuity = dict(plan)
    continuity["source_run_result_path"] = "continuity/private.json"
    assert tri.validate_targeted_response_formation_improvement_plan_v1(continuity)["valid"] is False

    provider = dict(plan)
    provider["authority_calibration_policy"] = {"permits_provider_calls": True}
    provider["denied_authority"] = dict(plan["denied_authority"], permits_provider_calls=True)
    assert tri.validate_targeted_response_formation_improvement_plan_v1(provider)["valid"] is False

    runtime = dict(plan)
    runtime["denied_authority"] = dict(plan["denied_authority"], permits_runtime_changes=True)
    assert tri.validate_targeted_response_formation_improvement_plan_v1(runtime)["valid"] is False

    public_claim = dict(plan)
    public_claim["authority_calibration_policy"] = {"can_claim_public_readiness": True}
    public_claim["denied_authority"] = dict(plan["denied_authority"], permits_public_launch=True)
    assert tri.validate_targeted_response_formation_improvement_plan_v1(public_claim)["valid"] is False

    intelligence_claim = dict(plan)
    intelligence_claim["denied_authority"] = dict(plan["denied_authority"], permits_intelligence_claims=True, permits_turing_claims=True, permits_certification_claims=True)
    assert tri.validate_targeted_response_formation_improvement_plan_v1(intelligence_claim)["valid"] is False

    memory_persistence = dict(plan)
    memory_persistence["denied_authority"] = dict(plan["denied_authority"], permits_memory_persistence=True)
    assert tri.validate_targeted_response_formation_improvement_plan_v1(memory_persistence)["valid"] is False


def test_full_plan_rejects_non_json_safe_and_hidden_or_protected_markers():
    plan = _valid_plan()

    non_json_safe = dict(plan)
    non_json_safe["target_gap_labels"] = [object()]
    assert tri.validate_targeted_response_formation_improvement_plan_v1(non_json_safe)["valid"] is False

    hidden = dict(plan)
    hidden["source_review_path"] = "hidden prompt / protected item"
    assert tri.validate_targeted_response_formation_improvement_plan_v1(hidden)["valid"] is False


def test_summary_is_safe_and_includes_counts_and_lane():
    plan = _valid_plan()
    summary = tri.summarize_targeted_response_formation_improvement_plan_v1(plan)
    assert summary["helper_count"] == 13
    assert summary["target_gap_count"] == 13
    assert summary["recommended_next_lane"] == "AWAIT_OPERATOR_DECISION"
    assert "raw_prompt" not in summary
    assert "raw_response" not in summary
    assert "private" not in " ".join(summary["blocked_reason_labels"])


def test_module_uses_only_safe_standard_library_imports():
    source = inspect.getsource(tri)
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert set(imports) == {"__future__", "copy", "json", "math", "typing"}
    assert "open(" not in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "socket" not in source
