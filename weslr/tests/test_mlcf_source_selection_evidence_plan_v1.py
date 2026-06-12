from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_source_selection_evidence_plan as source_plan
from weslr.mlcf_source_selection_evidence_plan import (
    allowed_mlcf_evidence_roles_v1,
    allowed_mlcf_source_authority_levels_v1,
    allowed_mlcf_source_classes_v1,
    allowed_mlcf_source_selection_next_steps_v1,
    build_initial_mlcf_source_selection_evidence_plan_examples_v1,
    build_mlcf_source_selection_evidence_plan_v1,
    summarize_mlcf_source_selection_evidence_plan_v1,
    to_mlcf_source_selection_evidence_plan_json_safe_v1,
    validate_mlcf_source_selection_evidence_plan_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

CANONICAL_IDS = {
    "rf_material_floorplan_source_plan",
    "github_only_source_plan_blocked_as_insufficient",
    "private_hidden_source_plan_blocked",
}


def _examples():
    return deepcopy(build_initial_mlcf_source_selection_evidence_plan_examples_v1())


def _example(plan_id: str):
    for item in _examples():
        if item["plan_id"] == plan_id:
            return item
    raise AssertionError(f"missing example {plan_id}")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_source_classes_v1",
        "allowed_mlcf_source_authority_levels_v1",
        "allowed_mlcf_evidence_roles_v1",
        "allowed_mlcf_source_selection_next_steps_v1",
        "build_mlcf_source_selection_evidence_plan_v1",
        "validate_mlcf_source_selection_evidence_plan_v1",
        "summarize_mlcf_source_selection_evidence_plan_v1",
        "to_mlcf_source_selection_evidence_plan_json_safe_v1",
        "build_initial_mlcf_source_selection_evidence_plan_examples_v1",
    ]
    for name in names:
        assert hasattr(source_plan, name)
        assert callable(getattr(source_plan, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_mlcf_source_classes_v1() == (
        "official_standard",
        "official_government_or_agency_data",
        "official_vendor_documentation",
        "official_api_documentation",
        "public_research_paper",
        "public_dataset",
        "public_patent",
        "github_repository",
        "software_release_or_changelog",
        "public_lab_or_university_artifact",
        "public_benchmark_or_test_suite",
        "owner_supplied_observation",
        "internal_project_artifact",
        "community_discussion",
        "unknown_source",
        "blocked_private_or_hidden_source",
    )
    assert allowed_mlcf_source_authority_levels_v1() == (
        "official_primary",
        "public_primary",
        "public_secondary",
        "implementation_evidence",
        "community_signal",
        "owner_context",
        "internal_context",
        "unknown_authority",
        "blocked",
    )
    assert allowed_mlcf_evidence_roles_v1() == (
        "definition_or_standard",
        "measurement_data",
        "implementation_reference",
        "prior_art",
        "candidate_signal",
        "counterexample_source",
        "replication_target",
        "constraint_source",
        "domain_context",
        "safety_boundary_context",
        "not_authoritative_context",
    )
    assert allowed_mlcf_source_selection_next_steps_v1() == (
        "build_source_plan_only",
        "operator_review",
        "prepare_authorized_ingestion_boundary",
        "prepare_metadata_only_source_summary",
        "blocked_by_safety",
        "needs_repair",
    )


def test_canonical_examples_build():
    examples = _examples()
    assert {item["plan_id"] for item in examples} == CANONICAL_IDS

    rf = _example("rf_material_floorplan_source_plan")
    assert rf["recommended_source_classes"]
    assert "official_standard" in rf["recommended_source_classes"]
    assert "github_repository" in rf["recommended_source_classes"]
    assert rf["next_safe_step"] == "prepare_authorized_ingestion_boundary"

    github = _example("github_only_source_plan_blocked_as_insufficient")
    assert "github_repository" in github["recommended_source_classes"]
    assert "official_standard" in github["recommended_source_classes"]
    assert github["next_safe_step"] == "needs_repair"
    assert "official" in github["why_official_sources_are_needed"].lower()

    blocked = _example("private_hidden_source_plan_blocked")
    assert "blocked_private_or_hidden_source" in blocked["blocked_source_classes"]
    assert blocked["next_safe_step"] == "blocked_by_safety"


def test_canonical_examples_validate_and_summarize():
    for example in _examples():
        validation = validate_mlcf_source_selection_evidence_plan_v1(example)
        summary = summarize_mlcf_source_selection_evidence_plan_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert validation["validation_posture"] == "valid"
        assert summary["plan_id"] == example["plan_id"]
        assert summary["recommended_ledger_id"] == example["recommended_ledger_id"]
        assert summary["next_safe_step"] == example["next_safe_step"]
        assert summary["validation_posture"] == "valid"


def test_rf_material_floorplan_plan_includes_expected_source_classes_and_roles():
    packet = _example("rf_material_floorplan_source_plan")
    expected_classes = {
        "official_standard",
        "official_government_or_agency_data",
        "public_research_paper",
        "public_dataset",
        "github_repository",
        "public_lab_or_university_artifact",
        "official_vendor_documentation",
    }
    assert expected_classes.issubset(set(packet["recommended_source_classes"]))
    assert packet["source_authority_map"]["official_standard"]["authority_level"] == "official_primary"
    assert "definition_or_standard" in packet["evidence_role_map"]["official_standard"]
    assert packet["why_official_sources_are_needed"]
    assert packet["why_community_sources_are_limited"]
    assert packet["missing_evidence"]
    assert packet["disconfirming_evidence_to_seek"]


def test_github_heavy_plan_marks_github_insufficient_and_requires_repair():
    packet = _example("github_only_source_plan_blocked_as_insufficient")
    assert "GitHub is useful as implementation evidence" in packet["why_github_is_or_is_not_useful"]
    assert "not enough" in packet["why_github_is_or_is_not_useful"].lower()
    assert packet["next_safe_step"] == "needs_repair"
    assert any("official" in item.lower() for item in packet["missing_evidence"])


def test_blocked_closed_access_plan_has_blocked_source_class_and_blocked_next_step():
    packet = _example("private_hidden_source_plan_blocked")
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["valid"] is True
    assert packet["blocked_source_classes"] == ["blocked_private_or_hidden_source"]
    assert packet["next_safe_step"] == "blocked_by_safety"
    assert packet["operator_review_need"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("science_direction_summary", "", "missing_science_direction_summary"),
        ("recommended_source_classes", [], "missing_recommended_source_classes"),
        ("source_priority_order", [], "missing_source_priority_order"),
        ("next_safe_step", "not_real", "invalid_next_safe_step"),
        ("recommended_ledger_id", "not_real", "invalid_recommended_ledger_id"),
    ],
)
def test_empty_and_invalid_core_fields_fail_closed(field, value, expected_label):
    packet = _example("rf_material_floorplan_source_plan")
    packet[field] = value
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("recommended_source_classes", ["not_real"], "invalid_source_class"),
        ("source_priority_order", ["not_real"], "invalid_source_class"),
        ("source_authority_map", {"not_real": {"authority_level": "official_primary", "evidence_roles": ["definition_or_standard"]}}, "invalid_source_class"),
        ("source_authority_map", {"github_repository": {"authority_level": "not_real", "evidence_roles": ["implementation_reference"]}}, "invalid_source_authority_level"),
        ("evidence_role_map", {"github_repository": ["not_real"]}, "invalid_evidence_role"),
        ("calibration_axes_to_apply", ["not_real"], "invalid_calibration_axis"),
    ],
)
def test_invalid_enums_fail_closed(field, value, expected_label):
    packet = _example("rf_material_floorplan_source_plan")
    packet[field] = value
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_official_claim_without_official_source_class_fails_closed():
    packet = _example("github_only_source_plan_blocked_as_insufficient")
    packet["source_selection_goal"] = "Need official evidence but only GitHub is listed."
    packet["recommended_source_classes"] = ["github_repository"]
    packet["source_priority_order"] = ["github_repository"]
    packet["source_authority_map"] = {
        "github_repository": {"authority_level": "implementation_evidence", "evidence_roles": ["implementation_reference"]}
    }
    packet["evidence_role_map"] = {"github_repository": ["implementation_reference"]}
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("official_claim_without_official_source_class", "github_only_official_evidence_claim"))


def test_source_ingestion_and_authority_flags_fail_closed():
    packet = _example("rf_material_floorplan_source_plan")
    packet["authority_status"]["source_ingestion_authorized"] = True
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag:source_ingestion_authorized" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "authority_field",
    [
        "runtime_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "provider_authority",
        "model_authority",
        "tool_execution_authority",
        "retrieval_tool_authority",
        "web_authority",
        "github_call_authority",
        "weslr_io_authorized",
        "weslr_read_authorized",
        "weslr_write_authorized",
        "weslr_persistence_authorized",
        "database_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_pack_promotion_authorized",
        "public_science_claim_authorized",
        "proof_claim_authorized",
        "benchmark_claim_authorized",
        "agi_claim_authorized",
        "automatic_discovery_authorized",
        "cross_user_leakage_authorized",
        "hidden_private_protected_authorized",
    ],
)
def test_unsafe_authority_flags_fail_closed(authority_field):
    packet = _example("rf_material_floorplan_source_plan")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("unsafe_authority_flag:") for label in validation["blocked_labels"])


def test_hidden_private_protected_markers_fail_closed():
    packet = _example("rf_material_floorplan_source_plan")
    packet["why_community_sources_are_limited"] = "This text includes a protected marker."
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    assert validation["blocked"] is True
    assert "forbidden_hidden_private_protected_marker" in validation["blocked_labels"]


def test_non_json_safe_output_is_redacted_or_blocked():
    packet = _example("rf_material_floorplan_source_plan")
    packet["source_authority_map"]["github_repository"]["extra"] = object()
    validation = validate_mlcf_source_selection_evidence_plan_v1(packet)
    safe = to_mlcf_source_selection_evidence_plan_json_safe_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]
    assert isinstance(safe["source_authority_map"]["github_repository"]["extra"], str)
    assert safe["source_authority_map"]["github_repository"]["extra"].startswith("[redacted:")


def test_summary_is_bounded_and_json_safe():
    packet = _example("rf_material_floorplan_source_plan")
    summary = summarize_mlcf_source_selection_evidence_plan_v1(packet)
    assert json.dumps(summary, sort_keys=True)
    assert summary["plan_id"] == packet["plan_id"]
    assert summary["recommended_ledger_id"] == packet["recommended_ledger_id"]
    assert summary["validation_posture"] == "valid"


def test_protected_files_unchanged():
    result = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "diff",
            "--name-only",
            "--",
            *sorted(PROTECTED_FILES),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
