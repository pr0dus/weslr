from __future__ import annotations

import builtins
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_routing_from_live_searxng_metadata_result as helper

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _valid_packet() -> dict[str, object]:
    return {
        "packet_id": "synthetic_controlled_live_searxng_metadata_only_result_packet_v1",
        "evidence_status": "metadata_only_locator_candidates",
        "authority_verdict": "external_evidence_unverified",
        "raw_content_retained": False,
        "snippets_retained": False,
        "automatic_truth_write": False,
        "query": "wifi sensing floorplan metadata only",
        "results": [
            {
                "query": "wifi sensing floorplan metadata only",
                "title": "GitHub WiFi sensing implementation reference",
                "url": "https://github.example.invalid/wifi-sensing/repo",
                "domain": "github.example.invalid",
                "source_engine": "searxng",
                "engines": ["searxng"],
                "rank": 1,
                "score": 98.1,
                "published_date": "2026-06-13",
                "source_class_hint": "github_repository",
                "authority_guess": "community_signal",
                "evidence_role_guess": "implementation_reference",
                "relevance_reason": "GitHub implementation reference only; metadata-only community signal.",
                "freshness_status_guess": "current",
                "access_license_status_guess": "open",
                "privacy_status_guess": "low",
                "blocked_status": "kept",
                "locator_id": "github_wifi_sensing_locator",
            },
            {
                "query": "wifi sensing floorplan metadata only",
                "title": "Public lab artifact",
                "url": "https://lab.example.invalid/wifi/artifact",
                "domain": "lab.example.invalid",
                "source_engine": "searxng",
                "engines": ["searxng"],
                "rank": 2,
                "score": 96.2,
                "published_date": "2026-05-01",
                "source_class_hint": "public_lab_or_university_artifact",
                "authority_guess": "public_secondary",
                "evidence_role_guess": "prior_art",
                "relevance_reason": "Public lab artifact metadata only; operator review required.",
                "freshness_status_guess": "recent",
                "access_license_status_guess": "open",
                "privacy_status_guess": "low",
                "blocked_status": "kept",
                "locator_id": "public_lab_artifact_locator",
            },
            {
                "query": "wifi sensing floorplan metadata only",
                "title": "Unknown authority locator",
                "url": "https://unknown.example.invalid/loc",
                "domain": "unknown.example.invalid",
                "source_engine": "searxng",
                "engines": ["searxng"],
                "rank": 3,
                "score": 90.0,
                "published_date": "2026-04-11",
                "source_class_hint": "unknown_authority",
                "authority_guess": "unknown_authority",
                "evidence_role_guess": "candidate_signal",
                "relevance_reason": "Unknown authority remains operator review only.",
                "freshness_status_guess": "unknown",
                "access_license_status_guess": "unknown",
                "privacy_status_guess": "unknown",
                "blocked_status": "kept",
                "locator_id": "unknown_authority_locator",
            },
            {
                "query": "wifi sensing floorplan metadata only",
                "title": "Candidate signal locator",
                "url": "https://candidate.example.invalid/loc",
                "domain": "candidate.example.invalid",
                "source_engine": "searxng",
                "engines": ["searxng"],
                "rank": 4,
                "score": 88.4,
                "published_date": "2026-03-22",
                "source_class_hint": "candidate_signal",
                "authority_guess": "owner_context",
                "evidence_role_guess": "candidate_signal",
                "relevance_reason": "Candidate signal remains posture only.",
                "freshness_status_guess": "stale",
                "access_license_status_guess": "open",
                "privacy_status_guess": "low",
                "blocked_status": "kept",
                "locator_id": "candidate_signal_locator",
            },
            {
                "query": "wifi sensing floorplan metadata only",
                "title": "Official standard locator",
                "url": "https://standard.example.invalid/spec",
                "domain": "standard.example.invalid",
                "source_engine": "searxng",
                "engines": ["searxng"],
                "rank": 5,
                "score": 87.1,
                "published_date": "2026-02-10",
                "source_class_hint": "official_standard",
                "authority_guess": "official_primary",
                "evidence_role_guess": "definition_or_standard",
                "relevance_reason": "Metadata-only standard locator ready for operator review.",
                "freshness_status_guess": "recent",
                "access_license_status_guess": "open",
                "privacy_status_guess": "low",
                "blocked_status": "kept",
                "locator_id": "official_standard_locator",
            },
        ],
        "blocked": [
            {
                "locator_id": f"overflow_{index:02d}",
                "blocked_status": "result_cap_exceeded",
                "title": f"Overflow locator {index:02d}",
                "url": f"https://overflow.example.invalid/{index:02d}",
                "domain": "overflow.example.invalid",
            }
            for index in range(1, 36)
        ],
        "source_result_packet_reference": "synthetic_in_memory_example_only",
        "authority_flags": {flag: False for flag in helper._AUTHORITY_FALSE_FLAGS_V1},
    }


def _private_packet() -> dict[str, object]:
    packet = _valid_packet()
    packet = deepcopy(packet)
    packet["results"] = [
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Private loopback locator",
            "url": "http://127.0.0.1/private",
            "domain": "127.0.0.1",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 1,
            "score": 1.0,
            "published_date": "2026-06-13",
            "source_class_hint": "blocked_private_or_hidden_source",
            "authority_guess": "blocked",
            "evidence_role_guess": "not_authoritative_context",
            "relevance_reason": "Private loopback locator should be blocked.",
            "freshness_status_guess": "unknown",
            "access_license_status_guess": "blocked",
            "privacy_status_guess": "high",
            "blocked_status": "blocked_from_routing",
            "locator_id": "private_loopback_locator",
        }
    ]
    packet["blocked"] = []
    return packet


def _route_for_first_result(*, source_class_hint: str | None = None, authority_guess: str | None = None, evidence_role_guess: str | None = None, relevance_reason: str | None = None, title: str | None = None) -> dict[str, object]:
    packet = deepcopy(_valid_packet())
    entry = packet["results"][0]
    if source_class_hint is not None:
        entry["source_class_hint"] = source_class_hint
    if authority_guess is not None:
        entry["authority_guess"] = authority_guess
    if evidence_role_guess is not None:
        entry["evidence_role_guess"] = evidence_role_guess
    if relevance_reason is not None:
        entry["relevance_reason"] = relevance_reason
    if title is not None:
        entry["title"] = title
    return helper.build_mlcf_route_from_live_searxng_metadata_result_v1(packet, operator_role="owner")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_live_searxng_metadata_route_actions_v1",
        "allowed_mlcf_live_searxng_metadata_route_statuses_v1",
        "allowed_mlcf_live_searxng_metadata_route_next_steps_v1",
        "build_mlcf_route_from_live_searxng_metadata_result_v1",
        "validate_mlcf_route_from_live_searxng_metadata_result_request_v1",
        "validate_mlcf_route_from_live_searxng_metadata_result_v1",
        "summarize_mlcf_route_from_live_searxng_metadata_result_v1",
        "to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1",
        "build_initial_mlcf_route_from_live_searxng_metadata_result_examples_v1",
    ]
    for name in names:
        assert hasattr(helper, name)
        assert callable(getattr(helper, name))


def test_allowed_enums_are_exact_and_stable():
    assert helper.allowed_mlcf_live_searxng_metadata_route_actions_v1() == (
        "route_to_source_selection_plan",
        "route_to_cross_domain_scout",
        "route_to_operator_review",
        "route_to_disconfirming_review",
        "route_to_extraordinary_claim_quarantine",
        "route_to_archive_low_value_signal",
        "route_to_blocked_by_safety",
        "route_to_time_revisit_review",
        "route_to_domain_convergence_review",
        "route_to_future_workforce_impact_review",
        "route_to_language_protocol_review",
        "route_to_artifact_proposal_plan",
        "route_to_ontology_expansion_request",
        "route_to_locator_metadata_candidate",
        "hold_for_operator_review",
        "block_from_routing",
    )
    assert helper.allowed_mlcf_live_searxng_metadata_route_statuses_v1() == (
        "ready_for_operator_review",
        "blocked",
    )
    assert helper.allowed_mlcf_live_searxng_metadata_route_next_steps_v1() == (
        "operator_review",
        "blocked_by_safety",
        "no_next_step",
    )


def test_build_initial_examples_are_synthetic_and_cover_valid_and_blocked_paths():
    examples = helper.build_initial_mlcf_route_from_live_searxng_metadata_result_examples_v1()
    assert len(examples) == 2
    assert examples[0]["validation_status"]["valid"] is True
    assert examples[0]["kept_locator_route_entries"]
    assert examples[0]["blocked_overflow_summary"]["count"] == 35
    assert examples[1]["validation_status"]["valid"] is True
    assert examples[1]["route_status"] == "blocked"
    assert examples[1]["kept_locator_route_entries"] == []


def test_valid_packet_with_five_kept_and_thirty_five_blocked_overflow_rows():
    packet = _valid_packet()
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(packet, operator_role="owner")
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_v1(route)
    assert validation["valid"] is True
    assert route["route_status"] == "ready_for_operator_review"
    assert len(route["kept_locator_route_entries"]) == 5
    assert route["blocked_overflow_summary"]["count"] == 35
    assert route["blocked_overflow_summary"]["result_cap_exceeded_count"] == 35
    assert route["safe_metadata_summary"]["metadata_only"] is True


def test_github_result_maps_to_community_implementation_signal_only():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    entry = route["kept_locator_route_entries"][0]
    assert entry["locator_id"] == "github_wifi_sensing_locator"
    assert entry["route_action"] == "route_to_locator_metadata_candidate"
    assert entry["source_class_posture"] == "community_signal"
    assert entry["authority_posture"] == "community_signal"
    assert entry["evidence_role_posture"] == "implementation_reference"
    assert entry["operator_review_required"] is True


def test_public_lab_artifact_maps_to_secondary_public_metadata_only():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    entry = route["kept_locator_route_entries"][1]
    assert entry["locator_id"] == "public_lab_artifact_locator"
    assert entry["route_action"] == "hold_for_operator_review"
    assert entry["source_class_posture"] == "secondary_public_metadata"
    assert entry["authority_posture"] == "public_secondary"
    assert entry["operator_review_required"] is True


def test_unknown_authority_holds_for_operator_review():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    entry = route["kept_locator_route_entries"][2]
    assert entry["locator_id"] == "unknown_authority_locator"
    assert entry["route_action"] == "hold_for_operator_review"
    assert entry["source_class_posture"] == "operator_review"
    assert entry["authority_posture"] == "unknown_authority"


def test_shared_registry_source_classes_are_accepted_where_safe():
    cases = [
        ("public_research_paper", "public_primary", "prior_art", "route_to_locator_metadata_candidate"),
        ("survey_paper", "public_primary", "prior_art", "route_to_locator_metadata_candidate"),
        ("review_paper", "public_primary", "prior_art", "route_to_locator_metadata_candidate"),
        ("benchmark_paper", "public_primary", "benchmark_gap_signal", "route_to_locator_metadata_candidate"),
        ("dataset_record", "public_secondary", "measurement_gap_signal", "route_to_locator_metadata_candidate"),
        ("official_standard", "official_primary", "official_constraint_signal", "route_to_locator_metadata_candidate"),
        ("government_agency_report", "official_primary", "official_constraint_signal", "route_to_locator_metadata_candidate"),
        ("patent", "public_primary", "prior_art", "route_to_locator_metadata_candidate"),
        ("thesis_dissertation", "public_secondary", "prior_art", "route_to_locator_metadata_candidate"),
        ("lab_university_artifact", "public_secondary", "source_selection_needed", "route_to_source_selection_plan"),
        ("conference_workshop_artifact", "public_secondary", "candidate_signal", "route_to_locator_metadata_candidate"),
        ("negative_result_paper", "public_primary", "disconfirming_signal", "route_to_disconfirming_review"),
        ("replication_study", "public_primary", "replication_gap_signal", "route_to_locator_metadata_candidate"),
        ("historical_archive", "public_secondary", "prior_art", "route_to_archive_low_value_signal"),
        ("technical_report", "public_primary", "unfinished_work_signal", "route_to_locator_metadata_candidate"),
        ("preprint", "public_primary", "dormant_direction_signal", "route_to_archive_low_value_signal"),
        ("vendor_technical_documentation", "official_primary", "implementation_reference_only", "route_to_locator_metadata_candidate"),
        ("code_repository_as_implementation_reference", "community_signal", "implementation_reference_only", "route_to_locator_metadata_candidate"),
        ("forum_blog_as_weak_signal", "community_signal", "candidate_signal", "hold_for_operator_review"),
        ("unknown_authority", "unknown_authority", "candidate_signal", "hold_for_operator_review"),
    ]
    for source_class_hint, authority_guess, evidence_role_guess, expected_route_action in cases:
        route = _route_for_first_result(
            source_class_hint=source_class_hint,
            authority_guess=authority_guess,
            evidence_role_guess=evidence_role_guess,
            relevance_reason=f"{source_class_hint} safe metadata-only test",
        )
        entry = route["kept_locator_route_entries"][0]
        assert route["validation_status"]["valid"] is True
        assert entry["route_action"] == expected_route_action
        assert entry["source_class_hint"] == source_class_hint
        assert entry["evidence_role_guess"] == evidence_role_guess
        assert entry["route_action"] != "route_to_candidate_preparation"
        assert entry["blocked_status"] != "result_cap_exceeded"


def test_shared_registry_evidence_roles_are_accepted_where_safe():
    cases = [
        ("candidate_signal", "public_research_paper", "public_primary", "route_to_locator_metadata_candidate"),
        ("unfinished_work_signal", "technical_report", "public_primary", "route_to_locator_metadata_candidate"),
        ("dormant_direction_signal", "preprint", "public_primary", "route_to_archive_low_value_signal"),
        ("cross_domain_transfer_signal", "review_paper", "public_primary", "route_to_cross_domain_scout"),
        ("technology_blocked_signal", "vendor_technical_documentation", "official_primary", "route_to_blocked_by_safety"),
        ("anomaly_signal", "dataset_record", "public_secondary", "route_to_locator_metadata_candidate"),
        ("contradiction_signal", "negative_result_paper", "public_primary", "route_to_disconfirming_review"),
        ("replication_gap_signal", "replication_study", "public_primary", "route_to_locator_metadata_candidate"),
        ("benchmark_gap_signal", "benchmark_paper", "public_primary", "route_to_locator_metadata_candidate"),
        ("measurement_gap_signal", "dataset_record", "public_secondary", "route_to_locator_metadata_candidate"),
        ("extraordinary_claim_signal", "public_research_paper", "public_primary", "route_to_extraordinary_claim_quarantine"),
        ("implementation_reference_only", "code_repository_as_implementation_reference", "community_signal", "route_to_locator_metadata_candidate"),
        ("disconfirming_signal", "negative_result_paper", "public_primary", "route_to_disconfirming_review"),
        ("official_constraint_signal", "official_standard", "official_primary", "route_to_locator_metadata_candidate"),
        ("source_selection_needed", "survey_paper", "public_primary", "route_to_source_selection_plan"),
        ("prior_art", "patent", "public_primary", "route_to_locator_metadata_candidate"),
    ]
    for evidence_role_guess, source_class_hint, authority_guess, expected_route_action in cases:
        route = _route_for_first_result(
            source_class_hint=source_class_hint,
            authority_guess=authority_guess,
            evidence_role_guess=evidence_role_guess,
            relevance_reason=f"{evidence_role_guess} safe metadata-only test",
        )
        entry = route["kept_locator_route_entries"][0]
        assert route["validation_status"]["valid"] is True
        assert entry["route_action"] == expected_route_action
        assert entry["evidence_role_guess"] == evidence_role_guess
        assert entry["route_action"] != "route_to_candidate_preparation"
        assert route["blocked_overflow_summary"]["count_only"] is True


def test_ontology_insufficient_signal_routes_to_expansion_request_and_not_candidate_preparation():
    route = _route_for_first_result(
        source_class_hint="public_research_paper",
        authority_guess="public_primary",
        evidence_role_guess="ontology_insufficient_signal",
        relevance_reason="ontology_insufficient_for_domain; metadata-only operator review required",
    )
    entry = route["kept_locator_route_entries"][0]
    assert route["validation_status"]["valid"] is True
    assert entry["route_action"] == "route_to_ontology_expansion_request"
    assert entry["allowed_next_MLCF_stage"] == "operator_review"
    assert entry["source_class_posture"] == "operator_review"
    assert entry["authority_posture"] == "unknown_authority"
    assert entry["evidence_role_posture"] == "ontology_insufficient_signal"
    assert entry["route_action"] != "route_to_candidate_preparation"
    assert all(item["route_action"] != "route_to_candidate_preparation" for item in route["kept_locator_route_entries"])


def test_overflow_rows_stay_blocked_and_count_only():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    overflow = route["blocked_overflow_summary"]
    assert overflow["count_only"] is True
    assert overflow["routed_into_kept"] is False
    assert overflow["future_larger_cap_requires_owner_authorization"] is True
    assert all(entry["blocked_status"] != "result_cap_exceeded" for entry in route["kept_locator_route_entries"])


@pytest.mark.parametrize(
    "mutator, expected_label",
    [
        (lambda p: p.__setitem__("raw_content_retained", True), "raw_content_retained_must_be_false"),
        (lambda p: p.__setitem__("snippets_retained", True), "snippets_retained_must_be_false"),
        (lambda p: p.__setitem__("automatic_truth_write", True), "automatic_truth_write_must_be_false"),
    ],
)
def test_boolean_posture_flags_fail_closed(mutator, expected_label):
    packet = _valid_packet()
    mutator(packet)
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_any_authority_flag_true_fails_validation():
    packet = _valid_packet()
    packet["authority_flags"]["source_ingestion_authorized"] = True
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_or_claim_flag" in validation["blocked_labels"]


def test_trusted_evidence_verdict_fails_validation():
    packet = _valid_packet()
    packet["trusted_evidence_verdict"] = "supported"
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("forbidden_content_key_present", "forbidden_content_text_present"))


def test_source_summary_or_content_field_fails_validation():
    packet = _valid_packet()
    packet["source_summaries"] = ["summary text"]
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert "forbidden_content_key_present" in validation["blocked_labels"]


def test_json_safe_serialization_converts_sets_and_tuples():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    route["safe_metadata_summary"]["extra_set"] = {"b", "a"}
    route["safe_metadata_summary"]["extra_tuple"] = (1, 2)
    safe = helper.to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1(route)
    assert safe["safe_metadata_summary"]["extra_set"] in (["a", "b"], ["b", "a"])
    assert safe["safe_metadata_summary"]["extra_tuple"] == [1, 2]
    assert json.dumps(safe)


def test_non_finite_rank_or_score_fails_validation():
    packet = _valid_packet()
    packet["results"][0]["rank"] = float("nan")
    packet["results"][1]["score"] = float("inf")
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_rank" in validation["blocked_labels"]
    assert "invalid_score" in validation["blocked_labels"]


def test_denied_authority_flags_remain_false():
    route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
    denied = route["denied_authority_flags"]
    assert denied["all_authority_flags_false"] is True
    assert all(value is False for key, value in denied.items() if key not in {"all_authority_flags_false", "status", "boundary_notes"})


def test_no_weslr_io_no_http_no_provider_model_import():
    source = Path(helper.__file__).read_text(encoding="utf-8").lower()
    forbidden = [
        ".weslr",
        "requests",
        "urllib",
        "socket",
        "subprocess.run",
        "openai",
        "anthropic",
        "chat_responder",
        "chat_ui",
        "dialogue.py",
        "main.py",
        "import provider",
        "import model",
    ]
    for token in forbidden:
        assert token not in source

    original_open = builtins.open
    original_run = subprocess.run
    try:
        builtins.open = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("open() must not be called"))
        subprocess.run = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess.run must not be called"))
        route = helper.build_mlcf_route_from_live_searxng_metadata_result_v1(_valid_packet(), operator_role="owner")
        validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_v1(route)
        assert validation["valid"] is True
    finally:
        builtins.open = original_open
        subprocess.run = original_run


def test_unsafe_private_loopback_url_fails_closed():
    packet = _private_packet()
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("unsafe_url", "unsafe_url_scheme", "unsafe_domain_or_url"))


def test_missing_query_fails_closed():
    packet = _valid_packet()
    packet["query"] = ""
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert "missing_query" in validation["blocked_labels"]


def test_missing_locator_id_fails_closed():
    packet = _valid_packet()
    packet["results"][0]["locator_id"] = ""
    validation = helper.validate_mlcf_route_from_live_searxng_metadata_result_request_v1(packet)
    assert validation["blocked"] is True
    assert "missing_locator_id" in validation["blocked_labels"]


def test_protected_files_unchanged():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
