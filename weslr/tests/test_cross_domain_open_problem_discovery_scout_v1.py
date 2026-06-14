from __future__ import annotations

import json

import pytest

import weslr.cross_domain_open_problem_discovery_scout as helper


_DEF_DOMAIN_FAMILIES = [
    "rf_sensing",
    "energy_systems",
    "materials",
    "biology_medicine",
    "mathematics",
    "physics_quantum",
    "ai_cognition",
    "language_communication",
    "economics_labor",
    "standards_specification",
]


def _rich_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_rich",
        "domain_families": list(_DEF_DOMAIN_FAMILIES),
        "input_references": [
            "docs/example_cross_domain_owner_summary_a.md",
            "docs/example_cross_domain_domain_summary_a.md",
        ],
        "search_governance_mode": "metadata_only_owner_review",
        "operator_review_need": "owner review required before later routing",
        "input_signal_items": [
            {
                "title_or_descriptor": "unfinished work and technology blocked",
                "summary": "unfinished work is technology blocked and dormant direction with time revisit.",
                "domain_family": "rf_sensing",
                "source_ref": "owner_summary_rf_001",
                "source_class_label": "owner_supplied_observation",
                "authority_guess": "owner_context",
                "evidence_role_guess": "domain_context",
            },
            {
                "title_or_descriptor": "cross domain transfer and anomaly",
                "summary": "cross-domain transfer with anomaly and measurement gap and open problem.",
                "domain_family": "materials",
                "source_ref": "owner_summary_materials_001",
                "source_class_label": "public_research_paper",
                "authority_guess": "public_primary",
                "evidence_role_guess": "constraint_source",
            },
            {
                "title_or_descriptor": "extraordinary claim fringe edge science",
                "summary": "extraordinary claim and fringe edge science need disconfirmation required.",
                "domain_family": "physics_quantum",
                "source_ref": "owner_summary_phy_001",
                "source_class_label": "public_research_paper",
                "authority_guess": "public_primary",
                "evidence_role_guess": "candidate_signal",
            },
            {
                "title_or_descriptor": "language protocol artifact generation",
                "summary": "language protocol candidate and artifact generation candidate.",
                "domain_family": "language_communication",
                "source_ref": "owner_summary_lang_001",
                "source_class_label": "official_standard",
                "authority_guess": "official_source",
                "evidence_role_guess": "candidate_signal",
            },
            {
                "title_or_descriptor": "future workforce impact and ontology insufficient",
                "summary": "future workforce impact and ontology insufficient.",
                "domain_family": "economics_labor",
                "source_ref": "owner_summary_econ_001",
                "source_class_label": "government_agency_report",
                "authority_guess": "official_source",
                "evidence_role_guess": "policy_context",
            },
            {
                "title_or_descriptor": "formal open question and theorem gap",
                "summary": "formal open question with theorem gap and not settled details.",
                "domain_family": "mathematics",
                "source_ref": "owner_summary_math_001",
                "source_class_label": "public_research_paper",
                "authority_guess": "public_primary",
                "evidence_role_guess": "candidate_signal",
            },
            {
                "title_or_descriptor": "domain convergence and shared constraint",
                "summary": "domain convergence and shared constraint across adjacent lines of work.",
                "domain_family": "ai_cognition",
                "source_ref": "owner_summary_ai_001",
                "source_class_label": "github_repository",
                "authority_guess": "public_secondary",
                "evidence_role_guess": "candidate_signal",
            },
        ],
    }


def _unknown_payload() -> dict[str, object]:
    return {
        "scout_id": "cross_domain_open_problem_scout_example_unknown",
        "domain_families": ["materials"],
        "input_references": ["docs/example_unknown_signal.md"],
        "search_governance_mode": "metadata_only_owner_review",
        "operator_review_need": "owner review required before later routing",
        "input_signal_items": [
            {
                "title_or_descriptor": "miscellaneous metadata blob",
                "summary": "no clear signal family is visible here.",
                "domain_family": "materials",
                "source_ref": "unknown_summary_001",
                "source_class_label": "community_discussion",
                "authority_guess": "unknown_authority",
                "evidence_role_guess": "candidate_signal",
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


def test_allowed_signal_types_cover_registry_and_safe_aliases():
    allowed = helper.allowed_cross_domain_open_problem_signal_types_v1()
    expected = {
        "unfinished_work_signal",
        "technology_blocked_signal",
        "dormant_direction_signal",
        "anomaly_signal",
        "measurement_benchmark_gap_signal",
        "formal_unsolved_problem_signal",
        "extraordinary_claim_signal",
        "fringe_edge_science_signal",
        "time_revisit_signal",
        "domain_convergence_signal",
        "future_workforce_impact_signal",
        "language_protocol_discovery_signal",
        "artifact_generation_candidate",
        "disconfirmation_required",
        "ontology_insufficient_signal",
        "theory_gap_signal",
        "formal_open_question_signal",
        "language_protocol_candidate",
    }
    assert expected.issubset(set(allowed))
    assert helper.allowed_cross_domain_open_problem_scout_next_steps_v1()


def test_rich_sample_validates_and_stays_metadata_only():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    validation = helper.validate_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    summary = helper.summarize_cross_domain_open_problem_discovery_scout_packet_v1(packet)
    assert validation["valid"] is True
    assert summary["validation_posture"] == "valid"
    assert packet["safe_metadata_summary"]["metadata_only"] is True
    assert packet["safe_metadata_summary"]["json_safe"] is True
    assert packet["recommended_mlcf_route"] in helper.allowed_cross_domain_open_problem_scout_next_steps_v1()
    assert packet["denied_authority_flags"]["all_authority_flags_false"] is True
    assert all(value is False for key, value in packet["denied_authority_flags"].items() if key not in {"all_authority_flags_false", "metadata_only", "evidence_status", "boundary_notes"})


def test_domain_family_coverage_is_preserved():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    assert packet["safe_metadata_summary"]["domain_family_count"] == 10
    assert packet["domain_families"] == _DEF_DOMAIN_FAMILIES


@pytest.mark.parametrize(
    "field_name, expected_type",
    [
        ("unfinished_work_candidates", "unfinished_work_signal"),
        ("technology_blocked_candidates", "technology_blocked_signal"),
        ("dormant_direction_candidates", "dormant_direction_signal"),
        ("time_revisit_candidates", "time_revisit_signal"),
        ("domain_convergence_candidates", "domain_convergence_signal"),
        ("future_workforce_impact_candidates", "future_workforce_impact_signal"),
        ("language_protocol_candidates", "language_protocol_candidate"),
        ("artifact_generation_candidates", "artifact_generation_candidate"),
        ("disconfirmation_required_candidates", "disconfirmation_required"),
        ("ontology_insufficient_candidates", "ontology_insufficient_signal"),
        ("extraordinary_claim_candidates", "extraordinary_claim_signal"),
        ("fringe_edge_science_candidates", "fringe_edge_science_signal"),
    ],
)
def test_registry_family_candidates_are_represented_safely(field_name, expected_type):
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    assert packet[field_name]
    assert packet[field_name][0]["signal_type"] == expected_type
    assert packet[field_name][0]["operator_review_required"] is True
    assert packet[field_name][0]["denied_authority_flags"]["all_authority_flags_false"] is True


def test_cross_domain_transfer_and_measurement_gap_are_detected():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    assert packet["open_problem_signal_candidates"]
    assert packet["unresolved_work_signal_candidates"]
    assert packet["anomaly_signal_candidates"]
    assert packet["limitation_future_work_candidates"]
    assert any(cand["signal_type"] in {"open_problem_signal", "theory_gap_signal", "unresolved_mechanism_signal", "missing_measurement_signal"} for cand in packet["unresolved_work_signal_candidates"])
    assert any(cand["signal_type"] in {"unexplained_anomaly_signal", "failed_model_signal"} for cand in packet["anomaly_signal_candidates"])


def test_extraordinary_and_fringe_signals_quarantine_for_review():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    assert packet["recommended_mlcf_route"] == "route_to_extraordinary_claim_quarantine"
    assert packet["disconfirming_evidence_map"]
    text = json.dumps(packet).lower()
    for banned in ("accepted evidence", "trusted evidence", "final answer", "public science", "proof"):
        assert banned not in text


def test_language_protocol_and_artifact_candidates_stay_structure_only():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    lang = packet["language_protocol_candidates"][0]
    art = packet["artifact_generation_candidates"][0]
    assert lang["signal_type"] == "language_protocol_candidate"
    assert art["signal_type"] == "artifact_generation_candidate"
    assert "universal" not in json.dumps(lang).lower()
    assert "generated artifact" not in json.dumps(art).lower()
    assert lang["recommended_next_step"] == "route_to_language_protocol_review"
    assert art["recommended_next_step"] == "route_to_artifact_proposal_plan"


def test_future_workforce_impact_signals_are_hypotheses_only():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    future = packet["future_workforce_impact_candidates"][0]
    assert future["signal_type"] == "future_workforce_impact_signal"
    assert future["recommended_next_step"] == "route_to_future_workforce_impact_review"
    text = json.dumps(future).lower()
    for banned in ("product readiness", "job replacement", "certainty", "hype"):
        assert banned not in text


def test_disconfirmation_first_and_ontology_insufficient_handling():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    dis = packet["disconfirmation_required_candidates"][0]
    ont = packet["ontology_insufficient_candidates"][0]
    assert dis["required_disconfirmation_fields"]
    assert ont["recommended_next_step"] == "route_to_ontology_expansion_request"
    assert "prepare_" not in ont["recommended_next_step"]
    assert any(field in dis["required_disconfirmation_fields"] for field in ("falsification_criterion", "missing_evidence_summary", "required_source_classes"))


def test_unknown_metadata_fails_closed_or_routes_to_safe_review():
    packet = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_unknown_payload())
    assert packet["validation_status"]["valid"] is True
    assert packet["recommended_mlcf_route"] in {"route_to_archive_low_value_signal", "route_to_operator_review"}
    assert packet["safe_metadata_summary"]["metadata_only"] is True


def test_json_safe_conversion_is_deterministic_and_content_free():
    packet1 = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    packet2 = helper.build_cross_domain_open_problem_discovery_scout_packet_v1(_rich_payload())
    safe1 = helper.to_cross_domain_open_problem_discovery_scout_json_safe_v1(packet1)
    safe2 = helper.to_cross_domain_open_problem_discovery_scout_json_safe_v1(packet2)
    assert json.dumps(safe1, sort_keys=True) == json.dumps(safe2, sort_keys=True)
    text = json.dumps(safe1).lower()
    for banned in ("raw_html", "full_text", "source_excerpt", "paper_text", "article_text", "accepted evidence", "trusted evidence"):
        assert banned not in text
