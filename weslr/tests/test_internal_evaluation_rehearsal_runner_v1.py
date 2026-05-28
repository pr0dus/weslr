from __future__ import annotations

import inspect
import json

import pytest

from weslr.internal_evaluation_dataset_registry import build_internal_evaluation_dataset_registry_record_v1
from weslr.internal_evaluation_rehearsal_runner import (
    FAILURE_LABELS_V1,
    MISSING_CAPABILITY_LABELS_V1,
    RESULT_LABELS_V1,
    SAFE_NEXT_LANES_V1,
    UNKNOWN_ENGINE_ALLOWED_ROLES_V1,
    UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1,
    build_internal_evaluation_gap_report_v1,
    build_internal_evaluation_rehearsal_review_packet_v1,
    build_internal_evaluation_rehearsal_run_plan_v1,
    map_internal_evaluation_rehearsal_gaps_v1,
    normalize_internal_evaluation_rehearsal_outcome_v1,
    summarize_internal_evaluation_rehearsal_runner_v1,
    to_internal_evaluation_rehearsal_runner_json_safe_v1,
    validate_internal_evaluation_rehearsal_batch_v1,
    validate_internal_evaluation_rehearsal_preflight_v1,
)

BASE_RECORD_FIELDS = dict(
    dataset_id="ds-001",
    dataset_name="Synthetic Rehearsal Set",
    dataset_description_redacted="redacted",
    source_family="synthetic",
    source_type="synthetic_weslr_created",
    exposure_level="synthetic",
    license_status="approved",
    source_review_status="approved_for_development",
    repeated_use_policy="limited_logged",
    contamination_risk="low",
    answer_key_policy="synthetic_generated",
    expected_output_policy="synthetic_generated",
    unknown_engine_role=["propose_synthetic_task_families"],
    mapped_test_families=["abstraction_rule_induction", "uncertainty_explanation"],
    required_pre_run_checks=["source_review_status_checked"],
    recommended_next_lane="REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1",
    notes_redacted="redacted",
)


def make_record(**overrides):
    payload = dict(BASE_RECORD_FIELDS)
    payload.update(overrides)
    return build_internal_evaluation_dataset_registry_record_v1(**payload)


@pytest.fixture()
def valid_records():
    return [
        make_record(dataset_id="ds-001"),
        build_internal_evaluation_dataset_registry_record_v1(
            **dict(
                BASE_RECORD_FIELDS,
                dataset_id="ds-public",
                source_family="public",
                source_type="public_open",
                exposure_level="public_open",
                license_status="open",
                source_review_status="source_review_passed",
                answer_key_policy="public_open_reviewed",
                expected_output_policy="development_only",
                contamination_risk="low",
                unknown_engine_role=["compress_repeated_failure_patterns"],
                mapped_test_families=["contextual_rule_application", "non_canned_response_formation"],
            )
        ),
    ]


def test_valid_registry_records_create_safe_run_plan(valid_records):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        valid_records,
        run_metadata={
            "run_id": "run-safe-1",
            "run_purpose": "metadata_only_internal_rehearsal",
            "run_scope": "internal_metadata_only",
            "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
            "notes_redacted": "redacted",
        },
    )
    assert plan["execution_allowed"] is False
    assert plan["status_label"] == "needs_operator_review"
    assert plan["result_label"] == "needs_operator_review"
    assert plan["planned_record_count"] == 2
    assert plan["blocked_record_count"] == 0
    assert plan["preflight"]["valid"] is True
    assert plan["source_type_summary"]["synthetic_weslr_created"] == 1
    assert plan["source_type_summary"]["public_open"] == 1
    assert plan["answer_key_policy_summary"]["synthetic_generated"] == 1
    assert plan["answer_key_policy_summary"]["public_open_reviewed"] == 1
    assert "abstraction_rule_induction" in plan["selected_test_families"]
    assert "contextual_rule_application" in plan["selected_test_families"]
    assert plan["registry_records"][0]["source_type"] == "synthetic_weslr_created"


@pytest.mark.parametrize(
    "source_type, exposure_level, license_status, source_review_status",
    [
        ("semi_private", "semi_private", "restricted", "unreviewed"),
        ("private", "private", "restricted", "unreviewed"),
        ("hidden_blocked", "hidden", "blocked", "unreviewed"),
    ],
)
def test_blocked_registry_records_fail_closed(source_type, exposure_level, license_status, source_review_status):
    record = make_record(
        dataset_id=f"blocked-{source_type}",
        source_family="blocked",
        source_type=source_type,
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        answer_key_policy="blocked",
        expected_output_policy="blocked",
        unknown_engine_role=[],
    )
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        [record],
        run_metadata={"run_id": f"run-{source_type}", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    assert plan["planned_record_count"] == 0
    assert plan["blocked_record_count"] == 1
    assert plan["preflight"]["blocked"] is True
    assert plan["result_label"] in {"blocked_by_registry", "blocked_by_source_governance", "blocked_by_contamination", "blocked_by_answer_key_policy"}


def test_unvalidated_records_fail_closed():
    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=[{"dataset_id": "raw-only"}],
        run_metadata={"run_id": "run-unvalidated", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    assert preflight["valid"] is False
    assert preflight["blocked"] is True
    assert "blocked_by_registry" in preflight["blocked_labels"]


@pytest.mark.parametrize(
    "override",
    [
        {"source_type": "mystery_source"},
        {"license_status": "mystery_license"},
        {"mapped_test_families": ["not_a_known_family"]},
    ],
)
def test_unknown_source_license_test_family_fails_closed(override):
    record = make_record(dataset_id="bad-meta", **override)
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        [record],
        run_metadata={"run_id": "run-bad-meta", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    assert plan["result_label"] == "blocked_by_registry"
    assert plan["preflight"]["blocked"] is True


@pytest.mark.parametrize(
    "source_type, exposure_level, expected_blocked_label",
    [
        ("semi_private", "semi_private", "blocked_by_source_governance"),
        ("private", "private", "blocked_by_source_governance"),
        ("hidden_blocked", "hidden", "blocked_by_source_governance"),
    ],
)
def test_semi_private_private_hidden_blocked(source_type, exposure_level, expected_blocked_label):
    record = make_record(
        dataset_id=f"{source_type}-ds",
        source_family="blocked",
        source_type=source_type,
        exposure_level=exposure_level,
        license_status="restricted",
        source_review_status="unreviewed",
        answer_key_policy="blocked",
        expected_output_policy="blocked",
    )
    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=[record],
        run_metadata={"run_id": "run-blocked-source", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    assert preflight["blocked"] is True
    assert expected_blocked_label in preflight["blocked_labels"]


@pytest.mark.parametrize(
    "flag_name",
    ["raw_private_data_allowed", "hidden_material_allowed"],
)
def test_raw_private_hidden_material_flags_fail_closed(flag_name):
    record = make_record(dataset_id="flagged", **{flag_name: True})
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        [record],
        run_metadata={"run_id": "run-flagged", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    assert plan["preflight"]["blocked"] is True
    assert plan["result_label"] in {"blocked_by_private_data", "blocked_by_hidden_material", "blocked_by_registry"}


@pytest.mark.parametrize(
    "flag_name, expected_blocked_label",
    [
        ("official_claim_allowed", "blocked_by_official_claim_boundary"),
        ("public_claim_allowed", "blocked_by_official_claim_boundary"),
        ("runtime_authority_allowed", "blocked_by_runtime_boundary"),
        ("voice_authority_allowed", "blocked_by_runtime_boundary"),
        ("answer_authority_granted", "blocked_by_runtime_boundary"),
        ("composition_authority_granted", "blocked_by_runtime_boundary"),
    ],
)
def test_official_public_runtime_voice_authority_flags_fail_closed(flag_name, expected_blocked_label):
    record = make_record()
    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=[record],
        run_metadata={
            "run_id": "run-authority",
            "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
            flag_name: True,
        },
    )
    assert preflight["blocked"] is True
    assert expected_blocked_label in preflight["blocked_labels"]


@pytest.mark.parametrize(
    "lane",
    [
        "LIVE_PUBLIC_RELEASE_V1",
        "RUNTIME_CHAT_WIRING_V1",
        "PUBLIC_UX_LAUNCH_V1",
        "VOICE_ENABLEMENT_V1",
        "DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1",
    ],
)
def test_direct_live_runtime_public_voice_next_lanes_fail_closed(lane):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        [make_record(dataset_id=f"lane-{lane}")],
        run_metadata={"run_id": f"run-{lane}", "next_lane": lane},
    )
    assert plan["preflight"]["blocked"] is True
    assert "blocked_by_forbidden_next_lane" in plan["preflight"]["blocked_labels"]
    assert plan["result_label"] == "blocked_by_forbidden_next_lane"


@pytest.mark.parametrize("role", sorted(UNKNOWN_ENGINE_ALLOWED_ROLES_V1))
def test_unknown_engine_allowed_roles_pass_as_metadata_only(role):
    record = make_record(dataset_id=f"role-{role}")
    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=[record],
        run_metadata={
            "run_id": "run-unknown-engine-allowed",
            "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
            "unknown_engine_role": [role],
        },
    )
    assert preflight["valid"] is True
    assert preflight["unknown_engine_authority_allowed"] is False


@pytest.mark.parametrize("role", sorted(UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1))
def test_unknown_engine_forbidden_roles_fail_closed(role):
    record = make_record(dataset_id=f"forbidden-{role}")
    preflight = validate_internal_evaluation_rehearsal_preflight_v1(
        registry_records=[record],
        run_metadata={
            "run_id": "run-unknown-engine-forbidden",
            "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1",
            "unknown_engine_role": [role],
        },
    )
    assert preflight["blocked"] is True
    assert "blocked_by_unknown_engine_authority" in preflight["blocked_labels"]


@pytest.mark.parametrize(
    "result_label",
    sorted(RESULT_LABELS_V1),
)
def test_outcome_normalization_accepts_qualitative_labels_only(result_label):
    outcome = normalize_internal_evaluation_rehearsal_outcome_v1(
        {
            "run_id": "run-outcome",
            "result_label": result_label,
            "failure_labels": ["abstraction_failure", "overconfidence_failure"],
            "missing_capability_labels": ["missing_abstraction_helper"],
            "predicted_failure_labels": ["abstraction_failure"],
            "observed_failure_labels": ["abstraction_failure"],
            "test_family_labels": ["abstraction_rule_induction"],
            "notes_redacted": "redacted",
        }
    )
    assert outcome["result_label"] == result_label if result_label != "pass_internal_rehearsal" else outcome["result_label"] in {"pass_internal_rehearsal", "partial_internal_rehearsal"}
    assert all(label in FAILURE_LABELS_V1 for label in outcome["failure_labels"])
    assert all(label in MISSING_CAPABILITY_LABELS_V1 for label in outcome["missing_capability_labels"])
    assert outcome["raw_answer_present"] is False


def test_outcome_normalization_rejects_raw_answers():
    outcome = normalize_internal_evaluation_rehearsal_outcome_v1(
        {
            "result_label": "pass_internal_rehearsal",
            "raw_answer_text": "secret answer",
            "notes_redacted": "redacted",
        }
    )
    assert outcome["blocked"] is True
    assert "blocked_by_runtime_boundary" in outcome["blocked_labels"]


def test_gap_mapping_maps_failures_to_missing_capabilities():
    mapping = map_internal_evaluation_rehearsal_gaps_v1(
        [
            {
                "result_label": "partial_internal_rehearsal",
                "failure_labels": ["abstraction_failure", "unknown_engine_projection_mismatch"],
                "missing_capability_labels": ["missing_gap_compression_helper"],
                "predicted_failure_labels": ["abstraction_failure"],
                "observed_failure_labels": ["abstraction_failure", "unknown_engine_projection_mismatch"],
            }
        ]
    )
    assert mapping["failure_label_counts"]["abstraction_failure"] == 1
    assert mapping["missing_capability_counts"]["missing_abstraction_helper"] == 1
    assert mapping["missing_capability_counts"]["missing_unknown_engine_projection_comparison"] == 1
    assert mapping["missing_capability_counts"]["missing_gap_compression_helper"] == 1


def test_predicted_vs_observed_labels_remain_metadata_only():
    mapping = map_internal_evaluation_rehearsal_gaps_v1(
        [
            {
                "result_label": "partial_internal_rehearsal",
                "predicted_failure_labels": ["composition_failure"],
                "observed_failure_labels": ["composition_failure", "canned_or_generic_response_failure"],
                "failure_labels": ["composition_failure", "canned_or_generic_response_failure"],
            }
        ]
    )
    assert mapping["predicted_vs_observed_labels"]
    assert "predicted_differs_from_observed" in mapping["predicted_vs_observed_labels"]
    assert "predicted_underpredicted" in mapping["predicted_vs_observed_labels"]
    assert "predicted_matches_observed" not in mapping["predicted_vs_observed_labels"]


def test_gap_report_excludes_raw_content_and_official_scores(valid_records):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        valid_records,
        run_metadata={"run_id": "run-gap", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    report = build_internal_evaluation_gap_report_v1(
        run_plan=plan,
        outcomes=[
            {
                "result_label": "partial_internal_rehearsal",
                "failure_labels": ["abstraction_failure"],
                "missing_capability_labels": ["missing_abstraction_helper"],
                "predicted_failure_labels": ["abstraction_failure"],
                "observed_failure_labels": ["abstraction_failure"],
                "raw_answer_text": "secret",
                "official_score": 99,
            }
        ],
        run_metadata={"run_id": "run-gap"},
        notes_redacted="redacted",
    )
    assert "raw_answer_text" not in report
    assert "official_score" not in report
    assert report["operator_review_required"] is True
    assert report["result_label_counts"]["blocked_by_official_claim_boundary"] == 1
    assert report["missing_capability_counts"]["missing_abstraction_helper"] == 1


def test_review_packet_has_clear_operator_sections_and_excludes_raw_content(valid_records):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        valid_records,
        run_metadata={"run_id": "run-packet", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    report = build_internal_evaluation_gap_report_v1(run_plan=plan, outcomes=[], run_metadata={"run_id": "run-packet"})
    packet = build_internal_evaluation_rehearsal_review_packet_v1(
        registry_status=plan["registry_validation_summary"],
        preflight_status=plan["preflight"],
        run_plan=plan,
        gap_report=report,
        unknown_engine_boundary_summary=report["unknown_engine_projection_summary"],
        blocked_next_lanes=report["blocked_live_or_voice_lanes"],
        recommended_next_lanes=report["recommended_gap_closure_lanes"],
        notes_redacted="redacted",
    )
    assert packet["operator_sections"] == [
        "registry_status",
        "preflight_status",
        "run_plan_summary",
        "gap_report_summary",
        "unknown_engine_boundary_summary",
        "blocked_lanes",
        "recommended_next_lanes",
    ]
    assert "raw_answer_text" not in packet
    assert "final_answer_text" not in packet
    assert packet["public_claim_allowed"] is False
    assert packet["unknown_engine_authority_allowed"] is False


def test_batch_validation_preserves_per_record_status(valid_records):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        valid_records,
        run_metadata={"run_id": "run-batch", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    batch = validate_internal_evaluation_rehearsal_batch_v1(
        [
            plan,
            {
                "result_label": "partial_internal_rehearsal",
                "failure_labels": ["abstraction_failure"],
                "missing_capability_labels": ["missing_abstraction_helper"],
            },
            {"dataset_id": "raw-only"},
        ]
    )
    assert batch["total_records"] == 3
    assert len(batch["records"]) == 3
    assert batch["records"][0]["item_type"] == "run_plan"
    assert batch["records"][1]["item_type"] == "outcome"
    assert batch["records"][2]["item_type"] == "registry_record"
    assert batch["blocked_records"] >= 1
    assert any(
        label in batch["aggregate_blocked_labels"]
        for label in ("blocked_by_registry", "blocked_by_unknown_source_type")
    )


def test_json_safe_conversion_is_deterministic():
    payload = {
        "b": 2,
        "a": {"z": 9, "x": [1, {"k": object()}]},
        "set_value": {3, 1, 2},
    }
    safe_one = to_internal_evaluation_rehearsal_runner_json_safe_v1(payload)
    safe_two = to_internal_evaluation_rehearsal_runner_json_safe_v1(payload)
    assert safe_one == safe_two
    assert json.dumps(safe_one, sort_keys=True)


def test_summarize_runner_is_safe_and_metadata_only(valid_records):
    plan = build_internal_evaluation_rehearsal_run_plan_v1(
        valid_records,
        run_metadata={"run_id": "run-summary", "next_lane": "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_IMPLEMENTATION_V1"},
    )
    summary = summarize_internal_evaluation_rehearsal_runner_v1(plan)
    assert summary["kind"] == "mapping"
    assert summary["status_label"] == "needs_operator_review"
    assert summary["operator_review_required"] is True


def test_no_file_network_subprocess_or_dot_weslr_behavior_is_present():
    source = inspect.getsource(__import__("weslr.internal_evaluation_rehearsal_runner", fromlist=["*"]))
    assert "import subprocess" not in source
    assert "http://" not in source
    assert "https://" not in source
    assert "open(" not in source
    assert ".weslr" not in source
