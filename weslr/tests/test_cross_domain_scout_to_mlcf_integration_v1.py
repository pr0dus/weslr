from __future__ import annotations

import ast
import builtins
import inspect
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cross_domain_scout_to_mlcf_integration as integration
from weslr.cross_domain_open_problem_discovery_scout import (
    build_initial_cross_domain_open_problem_discovery_scout_examples_v1,
    validate_cross_domain_open_problem_discovery_scout_packet_v1,
)
from weslr.cross_domain_scout_to_mlcf_integration import (
    allowed_cross_domain_scout_to_mlcf_next_steps_v1,
    allowed_cross_domain_scout_to_mlcf_route_types_v1,
    build_cross_domain_scout_to_mlcf_integration_packet_v1,
    build_initial_cross_domain_scout_to_mlcf_integration_examples_v1,
    summarize_cross_domain_scout_to_mlcf_integration_packet_v1,
    to_cross_domain_scout_to_mlcf_integration_json_safe_v1,
    validate_cross_domain_scout_to_mlcf_integration_packet_v1,
    validate_cross_domain_scout_to_mlcf_integration_request_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

EXPECTED_ROUTE_TYPES = (
    "scout_to_source_selection_evidence_plan",
    "scout_to_mlcf_cross_domain_candidate",
    "scout_to_metadata_only_source_locator_route",
    "scout_to_cognitive_research_run_packet",
    "scout_to_operator_review",
    "scout_to_archive_low_value_signal",
    "scout_blocked_by_safety",
)

EXPECTED_NEXT_STEPS = (
    "operator_review",
    "prepare_source_selection_evidence_plan",
    "prepare_mlcf_cross_domain_candidate",
    "prepare_metadata_only_source_locator_route",
    "prepare_cognitive_research_run_packet",
    "archive_low_value_signal",
    "blocked_by_safety",
    "needs_repair",
)


def _examples():
    return deepcopy(build_initial_cross_domain_scout_to_mlcf_integration_examples_v1())


def _example(integration_id: str):
    for item in _examples():
        if item["integration_id"] == integration_id:
            return item
    raise AssertionError(f"missing example {integration_id}")


def _source_examples():
    return deepcopy(build_initial_cross_domain_open_problem_discovery_scout_examples_v1())


def _safe_scout_packet() -> dict[str, object]:
    return deepcopy(_source_examples()[0])


def _custom_locator_scout_packet() -> dict[str, object]:
    packet = deepcopy(_source_examples()[1])
    packet["scout_id"] = "cross_domain_open_problem_scout_locator_example"
    packet["candidate_cross_domain_bridges"] = []
    packet["missing_evidence_map"] = {"source_class_gap": ["metadata-only locator needed"]}
    packet["disconfirming_evidence_map"] = {"blocked_private_or_hidden_source": ["no raw content", "no claim authority"]}
    packet["recommended_mlcf_route"] = "prepare_metadata_only_source_locator_route"
    packet["next_safe_step"] = "prepare_metadata_only_source_locator_route"
    return packet


def _custom_weak_scout_packet() -> dict[str, object]:
    packet = deepcopy(_source_examples()[3])
    packet["scout_id"] = "cross_domain_open_problem_scout_weak_example"
    packet["candidate_cross_domain_bridges"] = []
    packet["open_problem_signal_candidates"] = []
    packet["unresolved_work_signal_candidates"] = []
    packet["anomaly_signal_candidates"] = []
    packet["limitation_future_work_candidates"] = []
    packet["contradiction_candidates"] = []
    packet["missing_evidence_map"] = {}
    packet["disconfirming_evidence_map"] = {}
    packet["source_classes_needed"] = []
    packet["pressure_test_questions"] = ["Is this only a vague analogy?"]
    packet["probe_suggestions"] = ["Archive unless a stronger signal appears."]
    packet["recommended_mlcf_route"] = "archive_low_value_signal"
    packet["next_safe_step"] = "archive_low_value_signal"
    return packet


@pytest.fixture(autouse=True)
def _no_open(monkeypatch):
    def _fail(*args, **kwargs):
        raise AssertionError("unexpected filesystem open")

    monkeypatch.setattr(builtins, "open", _fail)


def test_required_apis_exist():
    names = [
        "allowed_cross_domain_scout_to_mlcf_route_types_v1",
        "allowed_cross_domain_scout_to_mlcf_next_steps_v1",
        "build_cross_domain_scout_to_mlcf_integration_packet_v1",
        "validate_cross_domain_scout_to_mlcf_integration_request_v1",
        "validate_cross_domain_scout_to_mlcf_integration_packet_v1",
        "summarize_cross_domain_scout_to_mlcf_integration_packet_v1",
        "to_cross_domain_scout_to_mlcf_integration_json_safe_v1",
        "build_initial_cross_domain_scout_to_mlcf_integration_examples_v1",
    ]
    for name in names:
        assert hasattr(integration, name)
        assert callable(getattr(integration, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_cross_domain_scout_to_mlcf_route_types_v1() == EXPECTED_ROUTE_TYPES
    assert allowed_cross_domain_scout_to_mlcf_next_steps_v1() == EXPECTED_NEXT_STEPS


def test_initial_examples_cover_the_requested_routes():
    examples = _examples()
    assert {item["selected_route"] for item in examples} == {
        "scout_to_mlcf_cross_domain_candidate",
        "scout_to_source_selection_evidence_plan",
        "scout_to_metadata_only_source_locator_route",
        "scout_blocked_by_safety",
        "scout_to_archive_low_value_signal",
        "scout_to_cognitive_research_run_packet",
    }
    assert {item["next_safe_step"] for item in examples} == {
        "prepare_mlcf_cross_domain_candidate",
        "prepare_source_selection_evidence_plan",
        "prepare_metadata_only_source_locator_route",
        "blocked_by_safety",
        "needs_repair",
        "prepare_cognitive_research_run_packet",
    }


@pytest.mark.parametrize("integration_id", [
    "cross_domain_scout_to_mlcf_candidate_example_a",
    "cross_domain_scout_to_mlcf_source_selection_example_b",
    "cross_domain_scout_to_mlcf_locator_example_c",
    "cross_domain_scout_to_mlcf_weak_example_e",
    "cross_domain_scout_to_mlcf_cognitive_example_f",
])
def test_examples_validate(integration_id):
    packet = _example(integration_id)
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    summary = summarize_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"
    assert summary["integration_id"] == packet["integration_id"]
    assert summary["selected_route"] == packet["selected_route"]
    assert summary["next_safe_step"] == packet["next_safe_step"]


def test_valid_scout_packet_routes_to_cross_domain_candidate():
    packet = build_cross_domain_scout_to_mlcf_integration_packet_v1(_safe_scout_packet(), integration_id="candidate_route")
    assert packet["selected_route"] == "scout_to_mlcf_cross_domain_candidate"
    assert packet["next_safe_step"] == "prepare_mlcf_cross_domain_candidate"
    assert packet["route_decisions"]
    assert any(item["route_type"] == "scout_to_mlcf_cross_domain_candidate" for item in packet["route_decisions"])


def test_valid_scout_packet_routes_to_source_selection_when_missing_evidence_dominates():
    packet = build_cross_domain_scout_to_mlcf_integration_packet_v1(deepcopy(_source_examples()[1]), integration_id="source_selection_route")
    assert packet["selected_route"] == "scout_to_source_selection_evidence_plan"
    assert packet["next_safe_step"] == "prepare_source_selection_evidence_plan"


def test_valid_scout_packet_routes_to_locator_when_source_classes_are_needed():
    packet = build_cross_domain_scout_to_mlcf_integration_packet_v1(_custom_locator_scout_packet(), integration_id="locator_route")
    assert packet["selected_route"] == "scout_to_metadata_only_source_locator_route"
    assert packet["next_safe_step"] == "prepare_metadata_only_source_locator_route"


def test_cognitive_research_route_is_supported():
    packet = build_cross_domain_scout_to_mlcf_integration_packet_v1(deepcopy(_source_examples()[0]), integration_id="cognitive_route", candidate_cross_domain_bridges=[], missing_evidence_map={}, disconfirming_evidence_map={}, source_classes_needed=[], anomaly_signal_candidates=[], contradiction_candidates=[], recommended_mlcf_route="prepare_cognitive_research_run_packet", next_safe_step="prepare_cognitive_research_run_packet")
    assert packet["selected_route"] == "scout_to_cognitive_research_run_packet"
    assert packet["next_safe_step"] == "prepare_cognitive_research_run_packet"


def test_weak_packet_archives_or_repair_posture():
    packet = build_cross_domain_scout_to_mlcf_integration_packet_v1(_custom_weak_scout_packet(), integration_id="weak_route")
    assert packet["selected_route"] == "scout_to_archive_low_value_signal"
    assert packet["next_safe_step"] == "needs_repair"


def test_blocked_and_claim_unsafe_inputs_fail_closed():
    packet = deepcopy(_source_examples()[2])
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="blocked_route")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert validation["blocked"] is True
    assert "invalid_source_scout_packet" in validation["blocked_labels"]

    claim_packet = deepcopy(_safe_scout_packet())
    claim_packet["input_signal_items"][0]["summary"] = "This is a discovery and proof claim."
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(claim_packet, integration_id="claim_route")
    claim_validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert claim_validation["blocked"] is True
    assert "unsafe_claim_language_present" in claim_validation["blocked_labels"]


def test_trusted_accepted_evidence_language_fails_closed():
    packet = _safe_scout_packet()
    packet["input_signal_items"][0]["summary"] = "Trusted evidence and accepted evidence are not allowed here."
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="trusted_evidence")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert validation["blocked"] is True
    assert "unsafe_claim_language_present" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "authority_key",
    [
        "source_access_authority",
        "runtime_execution_authority",
        "public_claim_authority",
        "discovery_claim_authority",
        "proof_claim_authority",
        "benchmark_claim_authority",
        "agi_claim_authority",
        "consciousness_claim_authority",
        "sentience_claim_authority",
        "memory_mutation_authority",
        "project_mutation_authority",
        "weslr_io_authority",
        "autonomous_routing_authority",
        "external_action_authority",
        "provider_model_authority",
        "http_authority",
        "web_search_authority",
        "behavior_pack_promotion_authority",
    ],
)
def test_denied_authority_flag_true_fails_closed(authority_key):
    packet = _safe_scout_packet()
    packet["denied_authority_flags"][authority_key] = True
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="authority_flag")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert validation["blocked"] is True
    assert any(label.startswith("unsafe_denied_authority_flag_true") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field_name",
    ["raw_html", "full_text", "full_snippets", "source_excerpts"],
)
def test_raw_full_text_html_and_snippet_fields_fail_closed(field_name):
    packet = _safe_scout_packet()
    packet["input_signal_items"][0][field_name] = "payload"
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="raw_field")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert validation["blocked"] is True
    assert "unsafe_source_content_field" in validation["blocked_labels"]


def test_private_hidden_or_protected_marker_fails_closed():
    packet = _safe_scout_packet()
    packet["input_signal_items"][0]["summary"] = "This mentions a private protected source."
    built = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="private_marker")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(built)
    assert validation["blocked"] is True
    assert "unsafe_private_hidden_protected_marker" in validation["blocked_labels"]


def test_route_decisions_include_safe_payload_previews_and_blocked_authorities():
    packet = _example("cross_domain_scout_to_mlcf_candidate_example_a")
    decision = packet["route_decisions"][0]
    assert "safe_payload_preview" in decision
    assert isinstance(decision["safe_payload_preview"], dict)
    assert decision["blocked_authorities"]


def test_selected_route_is_deterministic_and_integration_ids_are_controlled():
    packet = _safe_scout_packet()
    first = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    second = build_cross_domain_scout_to_mlcf_integration_packet_v1(deepcopy(packet))
    assert first["selected_route"] == second["selected_route"]
    assert first["integration_id"] == second["integration_id"]
    overridden = build_cross_domain_scout_to_mlcf_integration_packet_v1(packet, integration_id="custom_integration_id")
    assert overridden["integration_id"] == "custom_integration_id"


def test_json_safe_conversion_works():
    packet = _example("cross_domain_scout_to_mlcf_candidate_example_a")
    safe = to_cross_domain_scout_to_mlcf_integration_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)


def test_summary_is_safe_and_does_not_include_claim_language():
    packet = _example("cross_domain_scout_to_mlcf_candidate_example_a")
    summary = summarize_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    lowered = summary["summary_text"].lower()
    assert "discovery" not in lowered
    assert "proof" not in lowered
    assert "official benchmark" not in lowered
    assert "final answer" not in lowered


def test_request_validation_fails_closed_on_missing_or_invalid_scout_packet():
    missing = validate_cross_domain_scout_to_mlcf_integration_request_v1({"integration_id": "x"})
    assert missing["blocked"] is True
    assert "missing_source_scout_packet" in missing["blocked_labels"]

    invalid = validate_cross_domain_scout_to_mlcf_integration_request_v1({"integration_id": "x", "scout_packet": {"nope": True}})
    assert invalid["blocked"] is True
    assert "invalid_source_scout_packet" in invalid["blocked_labels"]


def test_request_validation_fails_closed_on_non_json_safe_values():
    request = {"integration_id": "x", "scout_packet": _safe_scout_packet(), "extra": object()}
    validation = validate_cross_domain_scout_to_mlcf_integration_request_v1(request)
    assert validation["blocked"] is True
    assert "non_json_safe_request" in validation["blocked_labels"]


def test_building_examples_does_not_touch_filesystem_or_runtime_modules():
    examples = build_initial_cross_domain_scout_to_mlcf_integration_examples_v1()
    assert examples
    source = inspect.getsource(integration)
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


@pytest.mark.parametrize("bad_packet", [None, 123, "not a packet"])
def test_packet_validation_fails_closed_on_bad_types(bad_packet):
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(bad_packet)
    assert validation["blocked"] is True
    assert validation["valid"] is False


def test_scout_packets_still_validate_on_their_own():
    assert validate_cross_domain_open_problem_discovery_scout_packet_v1(_safe_scout_packet())["valid"] is True


def test_validator_handles_missing_source_scout_packet_and_route_fields():
    packet = _example("cross_domain_scout_to_mlcf_candidate_example_a")
    packet.pop("source_scout_packet")
    validation = validate_cross_domain_scout_to_mlcf_integration_packet_v1(packet)
    assert validation["blocked"] is True
    assert "missing_source_scout_packet" in validation["blocked_labels"]


def test_protected_files_remain_unchanged_by_design():
    assert PROTECTED_FILES == {
        "weslr/chat_responder.py",
        "weslr/main.py",
        "main.py",
        "dialogue.py",
        "chat_ui.py",
    }
