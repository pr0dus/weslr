from __future__ import annotations

import builtins
import json
import subprocess
from pathlib import Path

import pytest

import weslr.cross_domain_open_problem_discovery_scout as helper


def _valid_broad_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_a",
        "domain_families": ["physics", "rf_signal", "materials", "cognitive_science"],
        "input_references": [
            "docs/example_cross_domain_owner_summary_a.md",
            "docs/example_cross_domain_domain_summary_a.md",
        ],
        "search_governance_mode": "metadata_only_owner_review",
        "operator_review_need": "owner review required before later cross-domain routing",
        "input_signal_items": [
            {
                "title_or_descriptor": "RF sensing mechanism remains not fully understood",
                "summary": "Future work notes an unresolved mechanism, an unexpected anomaly, and a measurement limitation.",
                "domain_family": "rf_signal",
                "source_ref": "owner_summary_rf_001",
                "source_class_label": "owner_supplied_observation",
                "authority_guess": "owner_context",
                "evidence_role_guess": "domain_context",
            },
            {
                "title_or_descriptor": "Materials scattering shows an open problem and replication gap",
                "summary": "The report says further research is required, a contradiction remains unresolved, and replication remains weak.",
                "domain_family": "materials",
                "source_ref": "owner_summary_materials_001",
                "source_class_label": "owner_supplied_observation",
                "authority_guess": "owner_context",
                "evidence_role_guess": "constraint_source",
            },
            {
                "title_or_descriptor": "Cognitive science analogy candidate with shared constraint",
                "summary": "A cross-domain analogy may transfer but needs explicit limits.",
                "domain_family": "cognitive_science",
                "source_ref": "owner_summary_cog_001",
                "source_class_label": "internal_project_artifact",
                "authority_guess": "internal_context",
                "evidence_role_guess": "candidate_signal",
            },
        ],
    }


def _rf_material_floorplan_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_b",
        "domain_families": ["rf_signal", "materials", "floor_plan"],
        "input_references": ["docs/example_rf_material_floorplan_metadata_b.md"],
        "search_governance_mode": "metadata_only_owner_review",
        "operator_review_need": "owner review required before later source selection",
        "input_signal_items": [
            {
                "title_or_descriptor": "Sparse floor-plan map with missing measurement and limited calibration",
                "summary": "The map is limited by sparse measurements and an incomplete benchmark picture.",
                "domain_family": "floor_plan",
                "source_ref": "locator_floorplan_001",
                "source_class_label": "public_lab_or_university_artifact",
                "authority_guess": "public_secondary",
                "evidence_role_guess": "measurement_data",
            },
            {
                "title_or_descriptor": "RF material scattering remains unresolved",
                "summary": "Future work is needed and the dataset is underexplored.",
                "domain_family": "rf_signal",
                "source_ref": "locator_rf_001",
                "source_class_label": "public_research_paper",
                "authority_guess": "public_primary",
                "evidence_role_guess": "prior_art",
            },
        ],
    }


def _low_value_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_d",
        "domain_families": ["materials", "architecture"],
        "input_references": ["docs/example_low_value_vague_analogy_d.md"],
        "search_governance_mode": "metadata_only_archive",
        "operator_review_need": "archive or repair the low-value analogy",
        "input_signal_items": [
            {
                "title_or_descriptor": "Maybe related",
                "summary": "This seems weak and underspecified.",
                "domain_family": "architecture",
                "source_ref": "weak_ref_001",
                "source_class_label": "community_discussion",
                "authority_guess": "community_signal",
                "evidence_role_guess": "candidate_signal",
            }
        ],
    }


def _blocked_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_c",
        "domain_families": ["physics"],
        "input_references": ["docs/example_blocked_raw_content_c.md"],
        "search_governance_mode": "metadata_only_owner_review",
        "operator_review_need": "owner review required",
        "input_signal_items": [
            {
                "title_or_descriptor": "Unsafe public claim text",
                "summary": "This is a discovery and proof claim and includes raw HTML <div>payload</div>.",
                "domain_family": "physics",
                "source_ref": "unsafe_ref_001",
                "source_class_label": "unknown_source",
                "authority_guess": "unknown_authority",
                "evidence_role_guess": "candidate_signal",
                "raw_html": "<html>raw</html>",
            }
        ],
    }


def test_required_apis_exist():
    names = [
        "allowed_cross_domain_open_problem_signal_types_v1",
        "allowed_cross_domain_open_problem_scout_next_steps_v1",
        "build_cross_domain_open_problem_discovery_scout_packet_v1",
        "validate_cross_domain_open_problem_discovery_scout_request_v1",
        "validate_cross_domain_open_problem_discovery_scout_packet_v1",
        "summarize_cross_domain_open_problem_discovery_scout_packet_v1",
        "to_cross_domain_open_problem_discovery_scout_json_safe_v1",
        "build_initial_cross_domain_open_problem_discovery_scout_examples_v1",
    ]
    for name in names:
        assert hasattr(helper, name)
        assert callable(getattr(helper, name))


def test_allowed_signal_types_and_next_steps_are_stable():
    assert "open_problem_signal" in helper.allowed_cross_domain_open_problem_signal_types_v1()
    assert "cross_domain_transfer_signal" in helper.allowed_cross_domain_open_problem_signal_types_v1()
    assert helper.allowed_cross_domain_open_problem_scout_next_steps_v1() == (
        "operator_review",
        "prepare_source_selection_evidence_plan",
        "prepare_mlcf_cross_domain_candidate",
        "prepare_metadata_only_source_locator_route",
        "prepare_cognitive_research_run_packet",
        "needs_repair",
        "blocked_by_safety",
        "archive_low_value_signal",
    )


def test_valid_broad_cross_domain_sample_validates_and_routes():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    validation = helper.validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    summary = helper.summarize_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    assert validation["valid"] is True
    assert summary["validation_posture"] == "valid"
    assert summary["signal_candidate_count"] >= 3
    assert packet["recommended_mlcf_route"] in helper.allowed_cross_domain_open_problem_scout_next_steps_v1()
    assert packet["recommended_mlcf_route"] in {"prepare_cognitive_research_run_packet", "prepare_mlcf_cross_domain_candidate"}
    assert packet["safe_metadata_summary"]["metadata_only"] is True


def test_rf_material_floor_plan_sample_produces_unresolved_or_missing_evidence_signals():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rf_material_floorplan_payload())
    assert packet["validation_status"]["valid"] is True
    assert packet["recommended_mlcf_route"] in {"prepare_source_selection_evidence_plan", "prepare_mlcf_cross_domain_candidate", "prepare_cognitive_research_run_packet"}
    assert packet["missing_evidence_map"] or packet["disconfirming_evidence_map"]
    assert packet["source_classes_needed"]


def test_open_problem_markers_are_detected():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    assert packet["open_problem_signal_candidates"]
    assert any(cand["signal_type"] in {"open_problem_signal", "unsolved_theory_signal", "unresolved_mechanism_signal", "not_fully_understood_signal", "unknown_mechanism_signal", "requires_further_research_signal"} for cand in packet["unresolved_work_signal_candidates"])


def test_future_work_markers_are_detected():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    assert packet["limitation_future_work_candidates"]
    assert any(cand["signal_type"] in {"future_work_signal", "limitation_signal"} for cand in packet["limitation_future_work_candidates"])


def test_contradiction_and_anomaly_markers_are_detected():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    assert packet["anomaly_signal_candidates"]
    assert packet["contradiction_candidates"]
    assert any(cand["signal_type"] in {"unexplained_anomaly_signal", "failed_model_signal"} for cand in packet["anomaly_signal_candidates"])
    assert any(cand["signal_type"] == "contradiction_signal" for cand in packet["contradiction_candidates"])


def test_missing_measurement_dataset_gap_and_transfer_markers_are_detected():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rf_material_floorplan_payload())
    all_candidates = (
        packet["open_problem_signal_candidates"]
        + packet["unresolved_work_signal_candidates"]
        + packet["anomaly_signal_candidates"]
        + packet["limitation_future_work_candidates"]
        + packet["contradiction_candidates"]
    )
    assert any(c["signal_type"] in {"missing_measurement_signal", "underexplored_dataset_signal", "replication_gap_signal", "incomplete_benchmark_signal", "survey_gap_signal", "calibration_gap_signal"} for c in all_candidates)
    assert packet["recommended_mlcf_route"] in {"prepare_source_selection_evidence_plan", "prepare_mlcf_cross_domain_candidate", "prepare_cognitive_research_run_packet"}


def test_candidate_ids_are_stable_and_deterministic():
    packet1 = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    packet2 = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    ids1 = [cand["signal_id"] for cand in packet1["open_problem_signal_candidates"] + packet1["unresolved_work_signal_candidates"] + packet1["anomaly_signal_candidates"] + packet1["limitation_future_work_candidates"] + packet1["contradiction_candidates"]]
    ids2 = [cand["signal_id"] for cand in packet2["open_problem_signal_candidates"] + packet2["unresolved_work_signal_candidates"] + packet2["anomaly_signal_candidates"] + packet2["limitation_future_work_candidates"] + packet2["contradiction_candidates"]]
    assert ids1 == ids2


def test_json_safe_conversion_works():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    packet["safe_metadata_summary"]["extra_set"] = {"b", "a"}
    packet["candidate_cross_domain_bridges"].append({"extra_tuple": (1, 2)})
    safe = helper.to_cross_domain_open_problem_discovery_scout_json_safe_v1(packet)
    assert safe["safe_metadata_summary"]["extra_set"] in (["a", "b"], ["b", "a"])
    assert safe["candidate_cross_domain_bridges"][-1]["extra_tuple"] == [1, 2]
    assert json.dumps(safe)


def test_denied_authority_flags_remain_false():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    denied = packet["denied_authority_flags"]
    assert denied["all_authority_flags_false"] is True
    assert all(value is False for key, value in denied.items() if key not in {"all_authority_flags_false", "metadata_only", "evidence_status", "boundary_notes"})


def test_raw_content_field_fails_closed():
    payload = _valid_broad_payload()
    payload["input_signal_items"][0]["raw_paper_text"] = "raw paper text"
    validation = helper.validate_cross_domain_open_problem_discovery_scout_request_v1(payload)
    assert validation["blocked"] is True
    assert "forbidden_content_key_present" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field_name",
    ["raw_html", "full_text", "source_excerpt"],
)
def test_raw_html_full_text_and_source_excerpt_fail_closed(field_name):
    payload = _valid_broad_payload()
    payload["input_signal_items"][0][field_name] = "unsafe content"
    validation = helper.validate_cross_domain_open_problem_discovery_scout_request_v1(payload)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("forbidden_content_key_present", "forbidden_claim_language_present"))


def test_public_discovery_proof_solution_claim_fails_closed():
    payload = _valid_broad_payload()
    payload["input_signal_items"][1]["summary"] = "This is a discovery and proof claim about a solved solution."
    validation = helper.validate_cross_domain_open_problem_discovery_scout_request_v1(payload)
    assert validation["blocked"] is True
    assert "forbidden_claim_language_present" in validation["blocked_labels"]


def test_authority_flag_true_fails_closed():
    payload = _valid_broad_payload()
    payload["authority_flags"] = {flag: False for flag in helper._AUTHORITY_FALSE_FLAGS_V1}
    payload["authority_flags"]["source_fetching_authority"] = True
    validation = helper.validate_cross_domain_open_problem_discovery_scout_request_v1(payload)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag_true" in validation["blocked_labels"]


def test_unsafe_private_hidden_protected_marker_fails_closed():
    payload = _valid_broad_payload()
    payload["input_signal_items"][0]["summary"] = "This includes a hidden prompt and protected file marker."
    validation = helper.validate_cross_domain_open_problem_discovery_scout_request_v1(payload)
    assert validation["blocked"] is True
    assert "unsafe_private_hidden_protected_marker" in validation["blocked_labels"]


def test_low_value_vague_analogy_is_not_a_discovery_candidate():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_low_value_payload())
    all_candidates = (
        packet["open_problem_signal_candidates"]
        + packet["unresolved_work_signal_candidates"]
        + packet["anomaly_signal_candidates"]
        + packet["limitation_future_work_candidates"]
        + packet["contradiction_candidates"]
    )
    assert packet["recommended_mlcf_route"] in {"archive_low_value_signal", "needs_repair"}
    assert all(cand["signal_type"] in {"weak_signal", "unknown_signal", "adjacent_science_analogy_signal"} for cand in all_candidates)


def test_output_never_creates_evidence_truth_or_accepted_evidence():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
    text = json.dumps(packet).lower()
    assert "accepted evidence" not in text
    assert "trusted evidence" not in text
    assert "truth" not in text or "no_truth" in text
    assert "evidence accepted" not in text


def test_no_network_no_filesystem_no_provider_model_no_runtime_chat_no_weslr_io():
    source = Path(helper.__file__).read_text(encoding="utf-8").lower()
    forbidden_tokens = [
        "requests",
        "urllib",
        "socket",
        "openai",
        "anthropic",
        "chat_responder",
        "dialogue.py",
        "chat_ui.py",
        "main.py",
        ".weslr",
    ]
    for token in forbidden_tokens:
        assert token not in source

    original_open = builtins.open
    original_run = subprocess.run
    try:
        builtins.open = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("open() must not be called"))
        subprocess.run = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess.run must not be called"))
        packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_valid_broad_payload())
        validation = helper.validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
        assert validation["valid"] is True
    finally:
        builtins.open = original_open
        subprocess.run = original_run
