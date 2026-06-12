from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_cross_domain_science_direction_candidate as cross
from weslr.mlcf_cross_domain_science_direction_candidate import (
    allowed_mlcf_cross_domain_candidate_types_v1,
    allowed_mlcf_cross_domain_next_steps_v1,
    allowed_mlcf_cross_domain_relation_types_v1,
    build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1,
    build_mlcf_cross_domain_science_direction_candidate_v1,
    summarize_mlcf_cross_domain_science_direction_candidate_v1,
    to_mlcf_cross_domain_science_direction_candidate_json_safe_v1,
    validate_mlcf_cross_domain_science_direction_candidate_v1,
)
from weslr.theoretical_calibration_axes import allowed_theoretical_calibration_next_steps_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

CANONICAL_IDS = {
    "rf_material_floorplan_sparse_change_map_candidate",
    "weak_analogy_blocked_candidate",
    "cross_domain_probe_needed_candidate",
}


def _examples():
    return deepcopy(build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1())


def _example(candidate_id: str):
    for item in _examples():
        if item["candidate_id"] == candidate_id:
            return item
    raise AssertionError(f"missing example {candidate_id}")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_cross_domain_candidate_types_v1",
        "allowed_mlcf_cross_domain_relation_types_v1",
        "allowed_mlcf_cross_domain_next_steps_v1",
        "build_mlcf_cross_domain_science_direction_candidate_v1",
        "validate_mlcf_cross_domain_science_direction_candidate_v1",
        "summarize_mlcf_cross_domain_science_direction_candidate_v1",
        "to_mlcf_cross_domain_science_direction_candidate_json_safe_v1",
        "build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1",
    ]
    for name in names:
        assert hasattr(cross, name)
        assert callable(getattr(cross, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_mlcf_cross_domain_candidate_types_v1() == (
        "cross_domain_method_candidate",
        "cross_domain_experiment_candidate",
        "cross_domain_representation_candidate",
        "cross_domain_probe_candidate",
        "cross_domain_architecture_candidate",
        "blocked_cross_domain_candidate",
        "needs_repair_candidate",
    )
    assert allowed_mlcf_cross_domain_relation_types_v1() == (
        "shared_wave_behavior",
        "shared_topology",
        "shared_constraint_model",
        "shared_signal_noise_problem",
        "shared_material_response",
        "shared_spatial_inference",
        "shared_causal_uncertainty",
        "shared_measurement_limitation",
        "weak_or_fake_analogy",
        "unknown_relation",
    )
    assert allowed_mlcf_cross_domain_next_steps_v1() == allowed_theoretical_calibration_next_steps_v1()


def test_canonical_examples_build():
    examples = _examples()
    assert {item["candidate_id"] for item in examples} == CANONICAL_IDS

    method = _example("rf_material_floorplan_sparse_change_map_candidate")
    assert method["candidate_type"] == "cross_domain_method_candidate"
    assert method["recommended_ledger_id"] == "architecture_direction_ledger"
    assert method["next_safe_step"] == "pressure_test"
    assert method["candidate_method_summary"] == (
        "Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions."
    )

    blocked = _example("weak_analogy_blocked_candidate")
    assert blocked["candidate_type"] == "blocked_cross_domain_candidate"
    assert blocked["recommended_ledger_id"] == "failed_idea_ledger"
    assert blocked["next_safe_step"] == "archive"
    assert "weak_or_fake_analogy" in blocked["domain_relation_types"]

    probe = _example("cross_domain_probe_needed_candidate")
    assert probe["candidate_type"] == "cross_domain_probe_candidate"
    assert probe["recommended_ledger_id"] == "idea_candidate_ledger"
    assert probe["next_safe_step"] == "probe"


def test_canonical_examples_validate_and_summarize():
    for example in _examples():
        validation = validate_mlcf_cross_domain_science_direction_candidate_v1(example)
        summary = summarize_mlcf_cross_domain_science_direction_candidate_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert validation["validation_posture"] == "valid"
        assert summary["candidate_id"] == example["candidate_id"]
        assert summary["recommended_ledger_id"] == example["recommended_ledger_id"]
        assert summary["source_signal_family"] == example["source_signal_family"]
        assert summary["next_safe_step"] == example["next_safe_step"]
        assert summary["validation_posture"] == "valid"


def test_canonical_examples_are_metadata_only_and_json_safe():
    for example in _examples():
        safe = to_mlcf_cross_domain_science_direction_candidate_json_safe_v1(example)
        assert json.dumps(safe, sort_keys=True)
        assert example["authority_status"]["all_authority_flags_false"] is True
        assert example["authority_status"]["status"] == "metadata_only"
        assert example["safe_metadata"]["metadata_only"] is True
        assert example["safe_metadata"]["no_public_claim_authority"] is True
        assert example["why_this_is_not_a_discovery"]


def test_richer_method_summary_for_rf_material_floorplan_candidate():
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    assert "Sparse RF spatial change map constrained by floor-plan topology" in packet["candidate_method_summary"]
    assert packet["shared_structure_map"]["bridge_focus"]
    assert packet["pressure_test_questions"]
    assert packet["probe_design_suggestions"]
    assert packet["why_this_is_nontrivial"]


def test_blocked_analogy_candidate_archives_or_blocks():
    packet = _example("weak_analogy_blocked_candidate")
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert validation["valid"] is True
    assert packet["candidate_type"] == "blocked_cross_domain_candidate"
    assert packet["next_safe_step"] == "archive"
    assert "weak_or_fake_analogy" in packet["domain_relation_types"]
    assert packet["disconfirming_signals"]
    assert packet["promotion_blockers"]


def test_probe_needed_candidate_recommends_probe():
    packet = _example("cross_domain_probe_needed_candidate")
    assert packet["candidate_type"] == "cross_domain_probe_candidate"
    assert packet["next_safe_step"] == "probe"
    assert packet["missing_evidence"]
    assert packet["probe_design_suggestions"]


@pytest.mark.parametrize("domain_inputs", [[], ["only one"]])
def test_fewer_than_two_domains_fails_closed(domain_inputs):
    packet = build_mlcf_cross_domain_science_direction_candidate_v1(
        candidate_id="bad_domain_count",
        domain_inputs=domain_inputs,
        candidate_type="cross_domain_method_candidate",
        candidate_title="Bad",
        candidate_method_summary="Bad",
        cross_domain_bridge="Bad",
        why_this_is_nontrivial="Bad",
        why_this_is_not_a_discovery="This is a metadata-only candidate direction, not a discovery.",
        pressure_test_questions=["q"],
        probe_design_suggestions=["p"],
        missing_evidence=["m"],
        disconfirming_signals=["d"],
        overclaim_risks=["o"],
        underexploration_risks=["u"],
        promotion_blockers=["b"],
        forbidden_interpretations=["this is proven"],
        authority_status={"all_authority_flags_false": True, "status": "metadata_only", "boundary_notes": "x"},
        safe_metadata={"safe": True, "metadata_only": True, "json_safe": True, "non_public": True,
                       "no_runtime_wiring": True, "no_model_provider_calls": True, "no_tool_execution": True,
                       "no_retrieval": True, "no_web_calls": True, "no_source_ingestion": True,
                       "no_raw_content_retention": True, "no_weslr_io": True, "no_weslr_read": True,
                       "no_weslr_write": True, "no_weslr_persistence": True, "no_database_writes": True,
                       "no_memory_mutation": True, "no_project_mutation": True, "no_behavior_pack_promotion": True,
                       "no_public_claim_authority": True, "no_final_answer_authority": True, "no_discovery_claims": True,
                       "no_proof_claims": True, "no_benchmark_claims": True, "no_agi_claims": True,
                       "no_public_science_claims": True, "no_hidden_private_protected_markers": True},
    )
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("too_few_domain_inputs", "invalid_domain_inputs"))


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("candidate_type", "not_real", "invalid_candidate_type"),
        ("domain_relation_types", ["not_real"], "invalid_domain_relation_types"),
        ("next_safe_step", "not_real", "invalid_next_safe_step"),
        ("recommended_ledger_id", "not_real", "invalid_recommended_ledger_id"),
        ("calibration_axes_used", ["not_real"], "invalid_calibration_axes_used"),
        ("why_this_is_not_a_discovery", "This is a discovery.", "missing_not_a_discovery_explanation"),
        ("pressure_test_questions", [], "missing_pressure_test_questions"),
        ("disconfirming_signals", [], "missing_disconfirming_signals"),
        ("promotion_blockers", [], "missing_promotion_blockers"),
    ],
)
def test_invalid_core_fields_fail_closed(field, value, expected_label):
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    packet[field] = value
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "authority_field",
    [
        "runtime_authorized",
        "source_ingestion_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "provider_authority",
        "model_authority",
        "tool_execution_authority",
        "retrieval_tool_authority",
        "web_authority",
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
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("unsafe_authority_flag:") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("candidate_method_summary", "this authorizes .weslr access", "unsafe_authority_text"),
        ("candidate_method_summary", "memory mutation", "unsafe_authority_text"),
        ("candidate_title", "protected file", "forbidden_hidden_private_protected_marker"),
        ("shared_structure_map", {"secret": "value"}, "forbidden_hidden_private_protected_marker"),
    ],
)
def test_marker_checks_fail_closed(field, value, expected_label):
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    packet[field] = value
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_non_json_safe_output_is_redacted_or_blocked():
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    packet["shared_structure_map"]["bad"] = object()
    validation = validate_mlcf_cross_domain_science_direction_candidate_v1(packet)
    safe = to_mlcf_cross_domain_science_direction_candidate_json_safe_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]
    assert isinstance(safe["shared_structure_map"]["bad"], str)
    assert safe["shared_structure_map"]["bad"].startswith("[redacted:")


def test_summary_is_bounded_and_json_safe():
    packet = _example("rf_material_floorplan_sparse_change_map_candidate")
    summary = summarize_mlcf_cross_domain_science_direction_candidate_v1(packet)
    assert json.dumps(summary, sort_keys=True)
    assert summary["candidate_id"] == packet["candidate_id"]
    assert summary["recommended_ledger_id"] == packet["recommended_ledger_id"]
    assert summary["summary_text"]
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
