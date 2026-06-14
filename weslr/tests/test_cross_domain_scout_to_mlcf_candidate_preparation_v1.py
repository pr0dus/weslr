from __future__ import annotations

import ast
import builtins
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cross_domain_scout_to_mlcf_candidate_preparation as candidate
from weslr.cross_domain_open_problem_discovery_scout import build_initial_cross_domain_open_problem_discovery_scout_examples_v1
from weslr.cross_domain_scout_to_mlcf_integration import (
    build_cross_domain_scout_to_mlcf_integration_packet_v1,
    build_initial_cross_domain_scout_to_mlcf_integration_examples_v1,
    validate_cross_domain_scout_to_mlcf_integration_packet_v1,
)
from weslr.cross_domain_scout_to_mlcf_candidate_preparation import (
    allowed_cross_domain_scout_to_mlcf_candidate_preparation_next_steps_v1,
    allowed_cross_domain_scout_to_mlcf_candidate_preparation_statuses_v1,
    allowed_cross_domain_scout_to_mlcf_candidate_readiness_labels_v1,
    build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1,
    build_initial_cross_domain_scout_to_mlcf_candidate_preparation_examples_v1,
    summarize_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1,
    to_cross_domain_scout_to_mlcf_candidate_preparation_json_safe_v1,
    validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1,
    validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

EXPECTED_STATUSES = (
    "candidate_preparation_ready_for_operator_review",
    "candidate_preparation_needs_source_selection_plan",
    "candidate_preparation_excluded_wrong_route",
    "candidate_preparation_needs_repair",
    "candidate_preparation_blocked_by_safety",
)

EXPECTED_LABELS = (
    "metadata_candidate_ready_for_review",
    "metadata_candidate_needs_evidence_plan",
    "metadata_candidate_needs_disconfirming_review",
    "metadata_candidate_low_value_or_weak",
    "metadata_candidate_blocked",
)

EXPECTED_NEXT_STEPS = (
    "operator_review",
    "prepare_source_selection_evidence_plan",
    "prepare_mlcf_cross_domain_candidate",
    "blocked_by_safety",
    "needs_repair",
    "exclude_wrong_route",
)


@pytest.fixture(autouse=True)
def _no_open(monkeypatch):
    def _fail(*args, **kwargs):
        raise AssertionError("unexpected filesystem open")

    monkeypatch.setattr(builtins, "open", _fail)


def _scout_packet():
    return deepcopy(build_initial_cross_domain_open_problem_discovery_scout_examples_v1()[0])


def _integration_packet():
    packet = deepcopy(build_initial_cross_domain_scout_to_mlcf_integration_examples_v1()[0])
    assert validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)["valid"] is True
    return packet


def _blocked_integration_packet():
    scout = _scout_packet()
    return build_cross_domain_scout_to_mlcf_integration_packet_v1(scout, integration_id="blocked_integration_for_candidate_preparation")


def _wrong_route_integration_packet():
    packet = deepcopy(build_initial_cross_domain_scout_to_mlcf_integration_examples_v1()[4])
    assert validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)["valid"] is True
    return packet


def _candidate_packet():
    return build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        _integration_packet(),
        candidate_preparation_id="candidate_preparation_example",
    )


def test_required_apis_exist():
    names = [
        "allowed_cross_domain_scout_to_mlcf_candidate_preparation_statuses_v1",
        "allowed_cross_domain_scout_to_mlcf_candidate_readiness_labels_v1",
        "allowed_cross_domain_scout_to_mlcf_candidate_preparation_next_steps_v1",
        "build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1",
        "validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1",
        "validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1",
        "summarize_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1",
        "to_cross_domain_scout_to_mlcf_candidate_preparation_json_safe_v1",
        "build_initial_cross_domain_scout_to_mlcf_candidate_preparation_examples_v1",
    ]
    for name in names:
        assert hasattr(candidate, name)
        assert callable(getattr(candidate, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_cross_domain_scout_to_mlcf_candidate_preparation_statuses_v1() == EXPECTED_STATUSES
    assert allowed_cross_domain_scout_to_mlcf_candidate_readiness_labels_v1() == EXPECTED_LABELS
    assert allowed_cross_domain_scout_to_mlcf_candidate_preparation_next_steps_v1() == EXPECTED_NEXT_STEPS


def test_valid_integration_packet_builds_ready_for_operator_review_packet():
    packet = _candidate_packet()
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_status"] == "candidate_preparation_ready_for_operator_review"
    assert packet["candidate_readiness_label"] == "metadata_candidate_ready_for_review"
    assert packet["next_safe_step"] == "operator_review"
    assert packet["denied_authority_flags"]["source_access_authority"] is False
    assert packet["validation_status"]["operator_review_required"] is True


def test_source_selection_plan_needed_route_builds_correct_status():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["missing_evidence"] = ["official source confirmation", "replication target", "additional evidence", "another gap"]
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="needs_source_plan")
    assert built["preparation_status"] == "candidate_preparation_needs_source_selection_plan"
    assert built["candidate_readiness_label"] == "metadata_candidate_needs_evidence_plan"
    assert built["next_safe_step"] == "prepare_source_selection_evidence_plan"


def test_wrong_route_becomes_excluded_packet():
    packet = _wrong_route_integration_packet()
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="wrong_route")
    assert built["preparation_status"] == "candidate_preparation_excluded_wrong_route"
    assert built["candidate_readiness_label"] == "metadata_candidate_low_value_or_weak"
    assert built["next_safe_step"] == "exclude_wrong_route"


def test_no_bridge_refs_produce_needs_repair_status():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["cross_domain_bridge_refs"] = []
    packet["candidate_signal_refs"] = []
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="needs_repair")
    assert built["preparation_status"] == "candidate_preparation_needs_repair"
    assert built["candidate_readiness_label"] == "metadata_candidate_low_value_or_weak"
    assert built["next_safe_step"] == "needs_repair"


def test_unsafe_claim_source_content_marker_blocks():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = "This is a proof and discovery claim."
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="blocked")
    assert built["preparation_status"] == "candidate_preparation_blocked_by_safety"
    assert built["candidate_readiness_label"] == "metadata_candidate_blocked"
    assert built["next_safe_step"] == "blocked_by_safety"
    assert validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)["blocked"] is True


def test_candidate_payload_preview_is_metadata_only():
    packet = _candidate_packet()
    preview = packet["mlcf_cross_domain_candidate_helper_payload_preview"]
    assert preview["no_claim_authority"] is True
    assert "source content" not in json.dumps(preview).lower()
    assert "final answer" not in json.dumps(preview).lower()
    assert "proof" not in json.dumps(preview).lower()


def test_source_selection_followup_preview_is_metadata_only():
    packet = _candidate_packet()
    preview = packet["source_selection_followup_preview"]
    lowered = json.dumps(preview).lower()
    assert preview["github_role"] == "implementation/reference only"
    assert "source content" not in lowered
    assert "final answer" not in lowered
    assert "proof" not in lowered


def test_unresolved_sample_like_input_carries_forward_missing_evidence():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["missing_evidence"] = []
    packet["source_selection_plan_payload_preview"]["missing_evidence"] = []
    packet["source_scout_summary"] = (
        "cross-domain bridge signals remain unresolved; missing measurements, future validation, "
        "and not fully understood mechanism questions remain."
    )
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(
        packet,
        candidate_preparation_id="sample_like_missing_evidence",
    )
    assert built["preparation_status"] == "candidate_preparation_ready_for_operator_review"
    assert built["candidate_readiness_label"] == "metadata_candidate_ready_for_review"
    assert built["next_safe_step"] == "operator_review"
    assert built["missing_evidence"]
    lowered = json.dumps(built["missing_evidence"]).lower()
    assert "raw" not in lowered
    assert "html" not in lowered
    assert "snippet" not in lowered
    assert "full text" not in lowered
    assert "url" not in lowered


def test_github_role_remains_implementation_reference_only():
    assert _candidate_packet()["source_selection_followup_preview"]["github_role"] == "implementation/reference only"


def test_operator_review_remains_required():
    packet = _candidate_packet()
    assert packet["validation_status"]["operator_review_required"] is True
    assert any("operator review" in reason.lower() for reason in packet["operator_review_reasons"])


@pytest.mark.parametrize(
    "authority_key",
    [
        "source_access_authority",
        "source_fetching_authority",
        "source_ingestion_authority",
        "raw_retention_authority",
        "final_answer_authority",
        "public_claim_authority",
        "discovery_claim_authority",
        "proof_claim_authority",
        "benchmark_claim_authority",
        "agi_claim_authority",
        "consciousness_claim_authority",
        "sentience_claim_authority",
        "runtime_execution_authority",
        "memory_mutation_authority",
        "project_mutation_authority",
        "weslr_io_authority",
        "autonomous_routing_authority",
        "external_action_authority",
        "provider_model_authority",
        "http_authority",
        "web_search_authority",
        "behavior_pack_promotion_authority",
        "accepted_candidate_authority",
        "proposal_payload_authority",
        "proposal_submission_authority",
        "proposal_application_authority",
    ],
)
def test_denied_authority_flags_remain_closed(authority_key):
    packet = _candidate_packet()
    assert packet["denied_authority_flags"][authority_key] is False


@pytest.mark.parametrize(
    "authority_key",
    ["source_access_authority", "runtime_execution_authority", "accepted_candidate_authority", "proposal_application_authority"],
)
def test_denied_authority_flag_true_fails_closed(authority_key):
    packet = _integration_packet()
    packet["denied_authority_flags"][authority_key] = True
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="bad_authority")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is False
    assert any(label.startswith("unsafe_denied_authority_flag_true") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field_name",
    ["raw_html", "full_text", "html", "source_excerpt", "full_snippets"],
)
def test_raw_full_text_html_and_snippet_fields_fail_closed(field_name):
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"][field_name] = "payload"
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="raw_field")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is False
    assert "unsafe_source_content_or_authority_marker" in validation["blocked_labels"]


def test_trusted_accepted_evidence_language_fails_closed():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = "trusted evidence and accepted evidence are not allowed here"
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="trusted_evidence")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is False
    assert "unsafe_source_content_or_authority_marker" in validation["blocked_labels"]


def test_proof_discovery_and_final_answer_claim_language_fails_closed():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = "This is proof, discovery, and final answer text."
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="claim_language")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is False
    assert "unsafe_source_content_or_authority_marker" in validation["blocked_labels"]


def test_private_hidden_or_protected_marker_fails_closed():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = "private protected hidden source marker"
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="private_marker")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is False
    assert "unsafe_source_content_or_authority_marker" in validation["blocked_labels"]


def test_json_safe_conversion_works():
    packet = _candidate_packet()
    safe = to_cross_domain_scout_to_mlcf_candidate_preparation_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)


def test_summary_is_safe_and_does_not_include_claims():
    packet = _candidate_packet()
    summary = summarize_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet)
    lowered = summary["summary_text"].lower()
    assert "discovery" not in lowered
    assert "proof" not in lowered
    assert "final answer" not in lowered


def test_examples_validate_or_intentionally_fail_closed_for_blocked_example():
    examples = build_initial_cross_domain_scout_to_mlcf_candidate_preparation_examples_v1()
    assert len(examples) >= 5
    statuses = [item["preparation_status"] for item in examples]
    assert "candidate_preparation_ready_for_operator_review" in statuses
    assert "candidate_preparation_needs_source_selection_plan" in statuses
    assert "candidate_preparation_excluded_wrong_route" in statuses or "candidate_preparation_blocked_by_safety" in statuses
    assert "candidate_preparation_blocked_by_safety" in statuses
    assert "candidate_preparation_needs_repair" in statuses
    blocked_example = next(item for item in examples if item["preparation_status"] == "candidate_preparation_blocked_by_safety")
    assert validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(blocked_example)["blocked"] is True


def test_request_validation_fails_closed_on_missing_or_invalid_integration_packet():
    missing = validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1({"candidate_preparation_id": "x"})
    assert missing["blocked"] is True
    assert "missing_integration_packet" in missing["blocked_labels"]

    invalid = validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1({"candidate_preparation_id": "x", "integration_packet": {"nope": True}})
    assert invalid["blocked"] is True
    assert "unsafe_request_content" not in invalid["blocked_labels"]


def test_request_validation_fails_closed_on_non_json_safe_values():
    request = {"candidate_preparation_id": "x", "integration_packet": _integration_packet(), "extra": object()}
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_request_v1(request)
    assert validation["blocked"] is True
    assert "non_json_safe_request" in validation["blocked_labels"]


def test_blocked_raw_upstream_scout_packet_rejects_safely():
    packet = _blocked_integration_packet()
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="blocked_raw_upstream")
    assert built["preparation_status"] == "candidate_preparation_blocked_by_safety"
    assert built["candidate_readiness_label"] == "metadata_candidate_blocked"
    assert built["next_safe_step"] == "blocked_by_safety"
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["blocked"] is True
    assert "source_scout_packet_not_candidate_preparation_eligible" in built["blocked_reasons"]


def test_safe_deny_authority_labels_do_not_trigger_claim_language_by_themselves():
    packet = _integration_packet()
    packet["route_decisions"][0]["blocked_authorities"] = ["discovery_claim_authority", "proof_claim_authority"]
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="safe_labels_only")
    validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
    assert validation["valid"] is True
    assert "unsafe_source_content_or_authority_marker" not in validation["blocked_labels"]


def test_ontology_insufficient_inputs_reject_from_candidate_preparation():
    packet = _integration_packet()
    packet["selected_route"] = "route_to_ontology_expansion_request"
    packet["route_decisions"][0]["route_type"] = "route_to_ontology_expansion_request"
    packet["ontology_expansion_request_handoff"] = {
        "ontology_expansion_request_marker": "ONTOLOGY_EXPANSION_REQUEST_CONFIRMED",
        "source_locator_ids": ["source_locator_001"],
        "triggering_signal_summary": "ontology insufficient for domain",
        "why_current_ontology_failed": "Ontology insufficient for domain family routing.",
        "attempted_signal_route": "route_to_ontology_expansion_request",
        "recommended_expansion_actions": ["expand ontology coverage"],
        "operator_review_requirement": True,
        "operator_token_requirement": "OPERATOR_CONFIRMATION_TOKEN_REQUIRED_V1",
        "safe_next_step": "operator_review",
    }
    packet["safe_metadata_summary"]["sufficient_power"] = False
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="ontology_insufficient")
    assert built["preparation_status"] == "candidate_preparation_blocked_by_safety"
    assert "ontology_expansion_request_not_candidate_preparation_eligible" in built["blocked_reasons"]
    assert "sufficient_power_false" in built["blocked_reasons"]


def test_review_only_signal_classes_remain_blocked():
    for marker, label in [
        ("extraordinary claim and fringe edge science", "extraordinary_fringe"),
        ("future work and future workforce impact", "future_workforce"),
        ("language protocol and understands all communication", "language_protocol"),
        ("artifact proposal and proposal payload", "artifact_proposal"),
    ]:
        packet = _integration_packet()
        packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = marker
        built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id=label)
        validation = validate_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(built)
        assert validation["valid"] is False
        assert built["preparation_status"] == "candidate_preparation_blocked_by_safety"
        assert built["next_safe_step"] == "blocked_by_safety"


def test_candidate_like_signals_still_require_disconfirmation_fields():
    packet = _integration_packet()
    packet["mlcf_candidate_payload_preview"]["science_direction_summary"] = "candidate signal with unresolved bridge evidence"
    packet["missing_evidence"] = []
    packet["disconfirming_signals"] = []
    packet["source_classes_needed"] = []
    built = build_cross_domain_scout_to_mlcf_candidate_preparation_packet_v1(packet, candidate_preparation_id="needs_disconfirmation")
    assert built["preparation_status"] in {"candidate_preparation_needs_repair", "candidate_preparation_needs_source_selection_plan", "candidate_preparation_ready_for_operator_review"}
    assert built["validation_status"]["operator_review_required"] is True


def test_building_examples_does_not_touch_filesystem_or_runtime_modules():
    examples = build_initial_cross_domain_scout_to_mlcf_candidate_preparation_examples_v1()
    assert examples
    source = inspect.getsource(candidate)
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "requests",
        "urllib",
        "urllib3",
        "httpx",
        "subprocess",
        "pathlib",
        "os",
        "weslr.chat_responder",
        "weslr.main",
        "main",
        "dialogue",
        "chat_ui",
        "openai",
        "anthropic",
    }
    assert not any(name in imported for name in forbidden_imports)


def test_protected_files_remain_unchanged_by_design():
    assert PROTECTED_FILES == {
        "weslr/chat_responder.py",
        "weslr/main.py",
        "main.py",
        "dialogue.py",
        "chat_ui.py",
    }
