from __future__ import annotations

import ast
import inspect
import json
from copy import deepcopy

import pytest

import weslr.ontology_expansion_request_builder as builder
from weslr.ontology_expansion_request_builder import (
    build_initial_ontology_expansion_request_examples_v1,
    build_ontology_expansion_request_v1,
    summarize_ontology_expansion_request_v1,
    to_ontology_expansion_request_json_safe_v1,
    validate_ontology_expansion_request_v1,
)
from weslr.unfinished_research_discovery_constants import (
    allowed_unfinished_research_expansion_recommendations_v1,
    denied_unfinished_research_authority_flags_v1,
    forbidden_unfinished_research_discovery_meanings_v1,
    required_unfinished_research_disconfirmation_fields_v1,
)


def _example():
    return build_ontology_expansion_request_v1(
        source_locator_ids=("locator_001",),
        triggering_signal_summary="The current ontology is insufficient for this domain.",
        why_current_ontology_failed="No current enum fit: this is an ontology-insufficient domain signal.",
        current_signal_type_attempted="unknown",
        current_route_attempted="unknown",
        recommended_expansion_actions=("expansion_add_new_domain_family", "expansion_enlarge_signal_ontology"),
        required_disconfirming_evidence={field: "metadata-only placeholder" for field in required_unfinished_research_disconfirmation_fields_v1()},
        rollback_plan={
            "prior_registry_snapshot_required": True,
            "changed_fields_required": True,
            "affected_modules_required": True,
            "affected_tests_required": True,
            "revert_commit_required": True,
            "post_rollback_validation_required": True,
            "no_memory_mutation_required": True,
            "no_weslr_io_required": True,
        },
        blocked_authorities={flag: False for flag in denied_unfinished_research_authority_flags_v1()},
        forbidden_claims=forbidden_unfinished_research_discovery_meanings_v1() + (
            "WESLR modified itself",
            "WESLR expanded its ontology automatically",
            "WESLR learned new ontology automatically",
        ),
        safe_next_step="design_new_discovery_lens",
        status="ready_for_design_lane",
    )


def test_module_imports_safely():
    assert builder is not None


def test_required_public_apis_exist():
    for name in (
        "build_ontology_expansion_request_v1",
        "validate_ontology_expansion_request_v1",
        "summarize_ontology_expansion_request_v1",
        "to_ontology_expansion_request_json_safe_v1",
        "build_initial_ontology_expansion_request_examples_v1",
    ):
        assert hasattr(builder, name)
        assert callable(getattr(builder, name))


def test_valid_packet_builds_and_validates():
    packet = _example()
    validation = validate_ontology_expansion_request_v1(packet)
    summary = summarize_ontology_expansion_request_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert packet["protocol_name"] == "weslr_ontology_expansion_request"
    assert packet["protocol_version"] == "v1"
    assert packet["created_by"] == "weslr_metadata_only_helper"
    assert packet["sufficient_power"] is False
    assert packet["ontology_marker"] == "ontology_insufficient_for_domain"
    assert packet["operator_review_required"] is True
    assert packet["operator_confirmation_token_required"] == "ONTOLOGY_EXPANSION_REQUEST_CONFIRMED"
    assert summary["validation_status"] == "valid"
    assert summary["sufficient_power"] is False
    assert summary["operator_review_required"] is True
    assert summary["summary_text"]


def test_json_safe_conversion_is_deterministic():
    packet = _example()
    first = to_ontology_expansion_request_json_safe_v1(packet)
    second = to_ontology_expansion_request_json_safe_v1(packet)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_summary_is_metadata_only():
    summary = summarize_ontology_expansion_request_v1(_example())
    lowered = json.dumps(summary).lower()
    assert "raw" not in lowered
    assert "html" not in lowered
    assert "snippet" not in lowered
    assert "source content" not in lowered


def test_blocked_authorities_all_false():
    packet = _example()
    assert all(value is False for value in packet["blocked_authorities"].values())
    validation = validate_ontology_expansion_request_v1(packet)
    assert validation["valid"] is True


@pytest.mark.parametrize(
    "mutator, expected_label",
    [
        (lambda p: p.__setitem__("operator_confirmation_token_required", "wrong"), "invalid_operator_confirmation_token_required"),
        (lambda p: p.__setitem__("sufficient_power", True), "sufficient_power_not_false"),
        (lambda p: p.__setitem__("ontology_marker", "wrong"), "invalid_ontology_marker"),
        (lambda p: p.__setitem__("recommended_expansion_actions", ()), "empty_recommended_expansion_actions"),
        (lambda p: p.__setitem__("recommended_expansion_actions", ("not_real",)), "unknown_recommended_expansion_action"),
        (lambda p: p["blocked_authorities"].__setitem__("accepted_evidence_authority", True), "blocked_authority_not_false_accepted_evidence_authority"),
        (lambda p: p["rollback_plan"].__delitem__("prior_registry_snapshot_required"), "missing_rollback_field_prior_registry_snapshot_required"),
        (lambda p: p.__setitem__("source_locator_ids", ()), "missing_source_locator_ids"),
        (lambda p: p.__setitem__("triggering_signal_summary", ""), "missing_triggering_signal_summary"),
        (lambda p: p.__setitem__("why_current_ontology_failed", ""), "missing_why_current_ontology_failed"),
        (lambda p: p.__setitem__("why_current_ontology_failed", "needs more detail"), "unknown_current_signal_without_justification"),
        (lambda p: p.__setitem__("current_signal_type_attempted", "unknown signal"), "unknown_current_signal_type_attempted"),
        (lambda p: p.__setitem__("current_route_attempted", "unknown route"), "unknown_current_route_attempted"),
        (lambda p: p.__setitem__("required_disconfirming_evidence", {"wrong": "x"}), "missing_required_disconfirming_evidence_fields"),
        (lambda p: p.__setitem__("forbidden_claims", ("discovery as proven truth",)), "forbidden_claim_language_present"),
        (lambda p: p.__setitem__("forbidden_claims", ("WESLR modified itself",)), ("forbidden_claim_language_present", "missing_required_forbidden_claims")),
        (lambda p: p.__setitem__("raw_html", "<p>x</p>"), "forbidden_content_key_present"),
        (lambda p: p.__setitem__("safe_metadata_summary", {"metadata_only": True}), "invalid_safe_metadata_summary_source_content_stored"),
    ],
)
def test_validation_fail_closed(mutator, expected_label):
    packet = _example()
    mutator(packet)
    validation = validate_ontology_expansion_request_v1(packet)
    assert validation["blocked"] is True
    if isinstance(expected_label, tuple):
        assert any(label in validation["blocked_labels"] for label in expected_label)
    else:
        assert expected_label in validation["blocked_labels"]


def test_missing_operator_token_fails():
    packet = _example()
    packet["operator_confirmation_token_required"] = ""
    validation = validate_ontology_expansion_request_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_operator_confirmation_token_required" in validation["blocked_labels"]


def test_unknown_current_values_are_allowed_only_with_no_enum_fit_reason():
    packet = _example()
    packet["current_signal_type_attempted"] = "unknown"
    packet["current_route_attempted"] = "unknown"
    packet["why_current_ontology_failed"] = "No current enum fit: the request has no matching ontology slot."
    validation = validate_ontology_expansion_request_v1(packet)
    assert validation["valid"] is True


def test_example_packets_validate():
    examples = build_initial_ontology_expansion_request_examples_v1()
    assert len(examples) >= 5
    for example in examples:
        validation = validate_ontology_expansion_request_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False


def test_examples_cover_required_patterns():
    examples = build_initial_ontology_expansion_request_examples_v1()
    lowered = [json.dumps(example).lower() for example in examples]
    assert any("unknown domain family" in item for item in lowered)
    assert any("language protocol" in item for item in lowered)
    assert any("fringe" in item or "extraordinary" in item for item in lowered)
    assert any("future-work" in item or "job-transformation" in item or "workforce" in item for item in lowered)
    assert any("discovery lens" in item for item in lowered)


def test_no_io_network_provider_or_runtime_imports():
    source = inspect.getsource(builder)
    tree = ast.parse(source)
    forbidden_roots = {"os", "sys", "subprocess", "socket", "urllib", "requests", "http", "pathlib", "openclaw"}
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(forbidden_roots)
    assert "weslr.chat_responder" not in source
    assert "chat_ui" not in source
    assert "dialogue" not in source
    assert "main.py" not in source
