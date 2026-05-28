import inspect
import json

import pytest

from weslr.internal_evaluation_dataset_registry import (
    ALLOWED_USE_LABELS_V1,
    ANSWER_KEY_POLICY_LABELS_V1,
    BLOCKED_USE_LABELS_V1,
    CONTAMINATION_RISK_LABELS_V1,
    EXPECTED_OUTPUT_POLICY_LABELS_V1,
    EXPOSURE_LEVEL_LABELS_V1,
    LICENSE_STATUS_LABELS_V1,
    SAFE_RECOMMENDED_NEXT_LANES_V1,
    SOURCE_TYPE_LABELS_V1,
    SOURCE_REVIEW_STATUS_LABELS_V1,
    TEST_FAMILY_LABELS_V1,
    UNKNOWN_ENGINE_ALLOWED_ROLES_V1,
    UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1,
    build_internal_evaluation_dataset_registry_record_v1,
    build_internal_evaluation_dataset_registry_review_packet_v1,
    classify_internal_evaluation_dataset_source_v1,
    derive_internal_evaluation_allowed_use_labels_v1,
    summarize_internal_evaluation_dataset_registry_v1,
    to_internal_evaluation_dataset_registry_json_safe_v1,
    validate_internal_evaluation_dataset_registry_batch_v1,
    validate_internal_evaluation_dataset_registry_record_v1,
)


BASE_SAFE_FIELDS = dict(
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


PUBLIC_OPEN_REVIEWED = dict(
    BASE_SAFE_FIELDS,
    dataset_id="ds-public",
    source_family="public",
    source_type="public_open",
    exposure_level="public_open",
    license_status="open",
    source_review_status="source_review_passed",
    answer_key_policy="public_open_reviewed",
    expected_output_policy="development_only",
    contamination_risk="low",
)

PUBLIC_OPEN_UNREVIEWED = dict(
    BASE_SAFE_FIELDS,
    dataset_id="ds-public-unreviewed",
    source_family="public",
    source_type="public_open",
    exposure_level="public_open",
    license_status="open",
    source_review_status="unreviewed",
    answer_key_policy="public_open_reviewed",
    expected_output_policy="development_only",
    contamination_risk="low",
)


def make_record(**overrides):
    payload = dict(BASE_SAFE_FIELDS)
    payload.update(overrides)
    return build_internal_evaluation_dataset_registry_record_v1(**payload)


@pytest.mark.parametrize(
    "record_kwargs, expected_blocked, expected_valid",
    [
        (PUBLIC_OPEN_UNREVIEWED, True, False),
        (PUBLIC_OPEN_REVIEWED, False, True),
        (dict(BASE_SAFE_FIELDS), False, True),
    ],
)
def test_public_open_review_rules(record_kwargs, expected_blocked, expected_valid):
    record = build_internal_evaluation_dataset_registry_record_v1(**record_kwargs)
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["blocked"] is expected_blocked
    assert result["valid"] is expected_valid
    if expected_blocked:
        assert result["status_label"] == "review_required"
        assert "source_review_required" in result["blocked_labels"]
    else:
        assert result["status_label"] == "approved_for_development"
        assert result["official_claim_allowed"] is False
        assert result["public_claim_allowed"] is False


def test_synthetic_allowed_for_repeated_development_metadata():
    record = make_record(
        source_type="synthetic_weslr_created",
        source_family="synthetic",
        exposure_level="synthetic",
        license_status="approved",
        source_review_status="approved_for_development",
        answer_key_policy="synthetic_generated",
        expected_output_policy="synthetic_generated",
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is True
    assert result["normalized_record"]["development_allowed"] is True
    assert result["normalized_record"]["sealed_internal_eval_allowed"] is True
    assert result["normalized_record"]["synthetic_mutation_allowed"] is True


@pytest.mark.parametrize(
    "source_type, exposure_level, license_status, source_review_status",
    [
        ("semi_private", "semi_private", "restricted", "unreviewed"),
        ("private", "private", "restricted", "unreviewed"),
        ("hidden_blocked", "hidden", "blocked", "unreviewed"),
        ("unknown_license_blocked_until_reviewed", "unknown", "unknown", "unreviewed"),
        ("raw_private_user_data_blocked", "private", "blocked", "blocked_by_private_data"),
    ],
)
def test_blocked_source_classes_fail_closed(source_type, exposure_level, license_status, source_review_status):
    record = make_record(
        dataset_id=f"{source_type}-ds",
        source_family="blocked",
        source_type=source_type,
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        answer_key_policy="blocked",
        expected_output_policy="blocked",
        unknown_engine_role=[],
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert result["blocked"] is True
    assert "blocked_by_source_class" in result["blocked_labels"] or "source_review_required" in result["blocked_labels"]


def test_generated_mutation_from_allowed_source_preserves_lineage():
    record = build_internal_evaluation_dataset_registry_record_v1(
        **dict(
            BASE_SAFE_FIELDS,
            dataset_id="mut-allowed",
            source_type="generated_mutation_from_allowed_source",
            source_family="generated_mutation",
            exposure_level="synthetic",
            license_status="approved",
            source_review_status="approved_for_synthetic_mutation_only",
            lineage_source_type="public_open",
            lineage_preserved=True,
            contamination_risk="low",
            answer_key_policy="synthetic_generated",
            expected_output_policy="synthetic_generated",
        )
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is True
    assert result["normalized_record"]["source_type"] == "generated_mutation_from_allowed_source"
    assert result["normalized_record"]["synthetic_mutation_allowed"] is True


def test_generated_mutation_from_blocked_source_blocks():
    record = build_internal_evaluation_dataset_registry_record_v1(
        **dict(
            BASE_SAFE_FIELDS,
            dataset_id="mut-blocked",
            source_type="generated_mutation_from_blocked_source_blocked",
            source_family="generated_mutation",
            exposure_level="hidden",
            license_status="blocked",
            source_review_status="unreviewed",
            contamination_risk="extreme",
            answer_key_policy="blocked",
            expected_output_policy="blocked",
        )
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_source_class" in result["blocked_labels"]


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("official_claim_allowed", True),
        ("public_claim_allowed", True),
        ("hidden_material_allowed", True),
        ("raw_private_data_allowed", True),
    ],
)
def test_authority_booleans_fail_closed(field_name, value):
    record = make_record(**{field_name: value})
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert result[field_name] is False
    assert any("blocked_by_" in label for label in result["blocked_labels"])


def test_blocked_answer_key_policy_fails_closed():
    record = make_record(
        source_type="semi_private",
        exposure_level="semi_private",
        license_status="restricted",
        source_review_status="unreviewed",
        answer_key_policy="public_open_reviewed",
        expected_output_policy="development_only",
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_answer_key_policy" in result["blocked_labels"]


def test_unknown_engine_allowed_role_passes_when_safe():
    record = make_record(unknown_engine_role=["compress_repeated_failure_patterns"])
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is True
    assert result["unknown_engine_authority_allowed"] is False
    assert result["normalized_record"]["unknown_engine_role"] == ["compress_repeated_failure_patterns"]


@pytest.mark.parametrize(
    "role",
    sorted(UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1),
)
def test_forbidden_unknown_engine_authority_roles_fail_closed(role):
    record = make_record(unknown_engine_role=[role])
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_unknown_engine_authority" in result["blocked_labels"]


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
def test_direct_to_live_runtime_public_voice_next_lanes_fail_closed(lane):
    record = make_record(recommended_next_lane=lane)
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_forbidden_next_lane" in result["blocked_labels"]


def test_safe_next_lane_passes():
    record = make_record(
        recommended_next_lane="REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1"
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is True
    assert result["normalized_record"]["recommended_next_lane"] == "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1"


def test_metadata_only_record_does_not_store_raw_fields():
    record = make_record()
    manual_record = dict(record)
    manual_record.update(
        {
            "raw_task_content": "secret task",
            "raw_private_user_data": "private",
            "final_answer_text": "answer",
        }
    )
    result = validate_internal_evaluation_dataset_registry_record_v1(manual_record)
    assert result["valid"] is True
    assert "raw_task_content" not in result["normalized_record"]
    assert "raw_private_user_data" not in result["normalized_record"]
    assert "final_answer_text" not in result["normalized_record"]


def test_batch_validation_preserves_per_record_results_and_aggregate_blocked_labels():
    records = [
        make_record(dataset_id="ok-1"),
        make_record(
            dataset_id="bad-1",
            source_type="private",
            exposure_level="private",
            license_status="restricted",
            source_review_status="unreviewed",
        ),
    ]
    batch = validate_internal_evaluation_dataset_registry_batch_v1(records)
    assert batch["total_records"] == 2
    assert batch["valid_records"] == 1
    assert batch["blocked_records"] == 1
    assert batch["valid"] is False
    assert len(batch["records"]) == 2
    assert "blocked_by_source_class" in batch["aggregate_blocked_labels"]


def test_summary_counts_blocked_allowed_and_contamination_labels_correctly():
    records = [
        make_record(dataset_id="sum-1"),
        make_record(
            dataset_id="sum-2",
            source_type="public_open",
            source_family="public",
            exposure_level="public_open",
            license_status="open",
            source_review_status="source_review_passed",
            answer_key_policy="public_open_reviewed",
            expected_output_policy="development_only",
        ),
        make_record(
            dataset_id="sum-3",
            source_type="private",
            exposure_level="private",
            license_status="restricted",
            source_review_status="unreviewed",
            contamination_risk="high",
        ),
    ]
    summary = summarize_internal_evaluation_dataset_registry_v1(records)
    assert summary["total_records"] == 3
    assert summary["blocked_count"] == 1
    assert summary["allowed_development_count"] >= 2
    assert summary["allowed_sealed_internal_eval_count"] >= 2
    assert summary["synthetic_mutation_allowed_count"] >= 1
    assert summary["official_claim_allowed_count"] == 0
    assert summary["public_claim_allowed_count"] == 0
    assert summary["unknown_engine_authority_allowed_count"] == 0
    assert summary["source_type_counts"]["public_open"] == 1
    assert summary["source_type_counts"]["private"] == 1
    assert summary["contamination_risk_counts"]["high"] >= 1


def test_json_safe_conversion_is_deterministic_and_serializable():
    record = make_record()
    safe_one = to_internal_evaluation_dataset_registry_json_safe_v1(record)
    safe_two = to_internal_evaluation_dataset_registry_json_safe_v1(record)
    assert safe_one == safe_two
    encoded = json.dumps(safe_one, sort_keys=True)
    assert isinstance(encoded, str)


def test_review_packet_excludes_raw_content():
    packet = build_internal_evaluation_dataset_registry_review_packet_v1(
        registry_status={"count": 1},
        validation_summary={"valid": True},
        blocked_labels=["blocked"],
        contamination_summary={"risk": "low"},
        source_governance_summary={"source": "safe"},
        answer_key_policy_summary={"policy": "blocked"},
        unknown_engine_boundary_summary={"role": "bounded"},
        recommended_next_lane="REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1",
    )
    assert "raw_task_content" not in packet
    assert packet["recommended_next_lane"] == "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1"
    assert packet["blocked_labels"] == ["blocked"]


def test_validation_result_contains_denied_authority_booleans():
    result = validate_internal_evaluation_dataset_registry_record_v1(make_record())
    assert result["official_claim_allowed"] is False
    assert result["public_claim_allowed"] is False
    assert result["runtime_authority_allowed"] is False
    assert result["unknown_engine_authority_allowed"] is False


@pytest.mark.parametrize(
    "missing_field",
    ["dataset_id", "dataset_name", "source_type", "license_status"],
)
def test_missing_required_fields_fail_closed(missing_field):
    record = make_record()
    record.pop(missing_field, None)
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "missing_required_fields" in result["blocked_labels"]


def test_unknown_source_type_fails_closed():
    record = make_record(source_type="mystery_source")
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_unknown_source_type" in result["blocked_labels"]


def test_unknown_license_status_fails_closed():
    record = make_record(license_status="mystery_license")
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_unknown_license_status" in result["blocked_labels"]


@pytest.mark.parametrize(
    "family",
    sorted(TEST_FAMILY_LABELS_V1),
)
def test_mapped_test_families_accept_known_families(family):
    record = make_record(mapped_test_families=[family])
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is True
    assert result["normalized_record"]["mapped_test_families"] == [family]


def test_mapped_test_families_reject_unknown_family_labels():
    record = make_record(mapped_test_families=["not_a_known_family"])
    result = validate_internal_evaluation_dataset_registry_record_v1(record)
    assert result["valid"] is False
    assert "blocked_by_unknown_test_family" in result["blocked_labels"]


def test_classification_and_label_constants_are_explicit():
    assert "public_open" in SOURCE_TYPE_LABELS_V1
    assert "synthetic_weslr_created" in SOURCE_TYPE_LABELS_V1
    assert "open" in LICENSE_STATUS_LABELS_V1
    assert "source_review_passed" in SOURCE_REVIEW_STATUS_LABELS_V1
    assert "development_allowed" in ALLOWED_USE_LABELS_V1
    assert "blocked" in BLOCKED_USE_LABELS_V1
    assert "low" in CONTAMINATION_RISK_LABELS_V1
    assert "synthetic_generated" in ANSWER_KEY_POLICY_LABELS_V1
    assert "metadata_only" in EXPECTED_OUTPUT_POLICY_LABELS_V1
    assert "abstraction_rule_induction" in TEST_FAMILY_LABELS_V1
    assert "compress_repeated_failure_patterns" in UNKNOWN_ENGINE_ALLOWED_ROLES_V1
    assert "authority" in UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1
    assert "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1" in SAFE_RECOMMENDED_NEXT_LANES_V1


def test_classify_public_open_reviewed_metadata():
    classification = classify_internal_evaluation_dataset_source_v1(
        source_type="public_open",
        exposure_level="public_open",
        license_status="open",
        source_review_status="source_review_passed",
    )
    assert classification["source_type"] == "public_open"
    assert classification["development_allowed"] is True
    assert classification["sealed_internal_eval_allowed"] is True
    assert classification["official_claim_allowed"] is False
    assert classification["public_claim_allowed"] is False


def test_classify_generated_mutation_from_allowed_source_metadata():
    classification = classify_internal_evaluation_dataset_source_v1(
        source_type="generated_mutation",
        exposure_level="synthetic",
        license_status="approved",
        source_review_status="approved_for_synthetic_mutation_only",
        source_family="generated_mutation",
        lineage_source_type="public_open",
        lineage_preserved=True,
    )
    assert classification["source_type"] == "generated_mutation_from_allowed_source"
    assert classification["synthetic_mutation_allowed"] is True


def test_derive_labels_are_metadata_only_and_label_bound():
    labels = derive_internal_evaluation_allowed_use_labels_v1(
        source_type="synthetic_weslr_created",
        exposure_level="synthetic",
        license_status="approved",
        source_review_status="approved_for_development",
        answer_key_policy="synthetic_generated",
        contamination_risk="low",
    )
    assert labels["development_allowed"] is True
    assert labels["sealed_internal_eval_allowed"] is True
    assert labels["synthetic_mutation_allowed"] is True
    assert all(label in ALLOWED_USE_LABELS_V1 for label in labels["allowed_use_labels"])


def test_no_file_network_subprocess_provider_behavior_is_present():
    import weslr.internal_evaluation_dataset_registry as module

    source = inspect.getsource(module)
    assert "import subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "socket" not in source
    assert "open(" not in source
    assert "http://" not in source
    assert "https://" not in source
