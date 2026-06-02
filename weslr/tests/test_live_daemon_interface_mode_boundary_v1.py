from __future__ import annotations

import ast
import inspect
import json
import sys
from copy import deepcopy

import pytest

import weslr.live_daemon_interface_mode_boundary as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
    "weslr.voice_gateway",
    "weslr.voice_layer.ambient_loop",
    "weslr.voice_layer.run_ambient",
    "weslr.proactive_daemon",
    "weslr.frontier_daemon",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_live_daemon_interface_examples_v1()
        if item["daemon_verdict_packet_id"] == example_id
    )


def _imported_module_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "live_daemon_interface_mode_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert "weslr.voice_gateway" not in sys.modules
    assert "weslr.voice_layer.ambient_loop" not in sys.modules
    assert "weslr.voice_layer.run_ambient" not in sys.modules
    assert "weslr.proactive_daemon" not in sys.modules
    assert "weslr.frontier_daemon" not in sys.modules

    imported = _imported_module_names(inspect.getsource(mod))
    for hint in PROTECTED_MODULE_HINTS:
        assert hint not in imported



def test_builds_deterministic_daemon_verdict_packet() -> None:
    packet_a = mod.build_live_daemon_verdict_packet_v1(
        daemon_verdict_packet_id="packet_v1",
        request_id="req_v1",
        surface="chat",
        memory_tier="identity_core",
        trust_level="conversational",
        memory_tier_context_allowed=True,
        trust_level_required="conversational",
        current_trust_level="conversational",
        listen_allowed=False,
        speak_allowed=False,
        render_allowed=True,
        reply_allowed=True,
        interrupt_allowed=False,
        autonomous_speaking_allowed=False,
        route="render_text",
        readiness_status="ready",
        grounding_status="grounded",
        source_access_status="access_allowed",
        poison_status="clean",
        privacy_status="low_sensitivity",
        action_authority_status="no_action_authority",
        public_claim_status="not_public_claim",
        risk_status="low",
        next_gate="render text",
        reason_summary="deterministic packet",
    )
    packet_b = mod.build_live_daemon_verdict_packet_v1(
        daemon_verdict_packet_id="packet_v1",
        request_id="req_v1",
        surface="chat",
        memory_tier="identity_core",
        trust_level="conversational",
        memory_tier_context_allowed=True,
        trust_level_required="conversational",
        current_trust_level="conversational",
        listen_allowed=False,
        speak_allowed=False,
        render_allowed=True,
        reply_allowed=True,
        interrupt_allowed=False,
        autonomous_speaking_allowed=False,
        route="render_text",
        readiness_status="ready",
        grounding_status="grounded",
        source_access_status="access_allowed",
        poison_status="clean",
        privacy_status="low_sensitivity",
        action_authority_status="no_action_authority",
        public_claim_status="not_public_claim",
        risk_status="low",
        next_gate="render text",
        reason_summary="deterministic packet",
    )
    assert packet_a == packet_b
    assert packet_a["raw_payload_allowed"] is False
    assert packet_a["runtime_authority"] is False



def test_validates_normal_packet() -> None:
    assert mod.validate_live_daemon_verdict_packet_v1(_example("chat_render_ready_grounded")) is True



def test_summarizes_packet() -> None:
    packet = _example("chat_render_ready_grounded")
    summary = mod.summarize_live_daemon_verdict_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["daemon_verdict_packet_id"] == packet["daemon_verdict_packet_id"]
    assert summary["surface"] == "chat"
    assert summary["route"] == "render_text"
    assert summary["readiness_status"] == "ready"



def test_json_safe_export_works() -> None:
    packet = _example("voice_speak_ready_with_caveat")
    safe = mod.to_live_daemon_verdict_json_safe_v1(packet)
    json.dumps(safe)
    assert safe["daemon_verdict_packet_id"] == packet["daemon_verdict_packet_id"]



def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_live_daemon_interface_examples_v1()
    ids = {item["daemon_verdict_packet_id"] for item in examples}
    assert len(examples) == 10
    assert ids == {
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    }


@pytest.mark.parametrize(
    "example_id,expect",
    [
        ("chat_render_ready_grounded", {"render_allowed": True, "runtime_authority": False, "route": "render_text"}),
        ("voice_speak_ready_with_caveat", {"speak_allowed": True, "readiness_status": "ready_with_caveat"}),
        ("voice_blocked_unsupported_claim", {"speak_allowed": False, "grounding_status": "unsupported"}),
        ("ambient_defer_missing_evidence", {"route": "defer_response", "readiness_status": "not_ready_missing_evidence"}),
        ("proactive_operator_review_required", {"route": "operator_review_required", "action_authority_status": "operator_required"}),
        ("frontier_silent_store_none", {"route": "silent_store_none", "render_allowed": False}),
        ("rag_access_blocked_verdict", {"route": "block_response", "source_access_status": "access_restricted"}),
        ("poison_blocked_verdict", {"route": "block_response", "poison_status": "poison_blocked"}),
        ("naie_contradiction_render_with_caveat", {"render_allowed": True, "grounding_status": "contradicted"}),
        ("autonomous_speaking_blocked_high_risk", {"autonomous_speaking_allowed": False, "risk_status": "high"}),
    ],
)
def test_initial_examples_carry_expected_behavior(example_id: str, expect: dict[str, object]) -> None:
    packet = _example(example_id)
    for key, value in expect.items():
        assert packet[key] == value
    assert packet["raw_payload_allowed"] is False
    assert packet["runtime_authority"] is False
    assert packet["writes_state"] is False
    assert packet["model_provider_used"] is False
    assert packet["public_claim_allowed"] is False
    assert packet["proof_claim_allowed"] is False
    assert packet["learning_claimed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_allows_raw_payload(example_id: str) -> None:
    assert _example(example_id)["raw_payload_allowed"] is False


def test_no_initial_example_grants_action_authority() -> None:
    examples = mod.build_initial_live_daemon_interface_examples_v1()
    allowed = {"no_action_authority", "proposal_only", "operator_required", "blocked"}
    assert all(packet["action_authority_status"] in allowed for packet in examples)
    assert all(packet["action_authority_status"] != "owner_required" for packet in examples)


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_has_runtime_authority(example_id: str) -> None:
    assert _example(example_id)["runtime_authority"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_writes_state(example_id: str) -> None:
    assert _example(example_id)["writes_state"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_calls_model_provider(example_id: str) -> None:
    assert _example(example_id)["model_provider_used"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_allows_public_claim(example_id: str) -> None:
    assert _example(example_id)["public_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_allows_proof_claim(example_id: str) -> None:
    assert _example(example_id)["proof_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "chat_render_ready_grounded",
        "voice_speak_ready_with_caveat",
        "voice_blocked_unsupported_claim",
        "ambient_defer_missing_evidence",
        "proactive_operator_review_required",
        "frontier_silent_store_none",
        "rag_access_blocked_verdict",
        "poison_blocked_verdict",
        "naie_contradiction_render_with_caveat",
        "autonomous_speaking_blocked_high_risk",
    ],
)
def test_no_initial_example_claims_learning(example_id: str) -> None:
    assert _example(example_id)["learning_claimed"] is False


@pytest.mark.parametrize("surface", ["not_a_surface", "chat_surface"])
def test_validation_fails_unknown_surface(surface: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["surface"] = surface
    with pytest.raises(mod.ValidationError, match="unknown_surface"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize("route", ["render_prompt", "voice_route"])
def test_validation_fails_unknown_route(route: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["route"] = route
    with pytest.raises(mod.ValidationError, match="unknown_route"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize("status", ["maybe_ready", "almost_ready"])
def test_validation_fails_unknown_readiness_status(status: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["readiness_status"] = status
    with pytest.raises(mod.ValidationError, match="unknown_readiness_status"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize("status", ["dangerous", "critical_hazard"])
def test_validation_fails_unknown_risk_status(status: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["risk_status"] = status
    with pytest.raises(mod.ValidationError, match="unknown_risk_status"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize("status", ["yes_action", "grant_action"])
def test_validation_fails_unknown_action_authority_status(status: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["action_authority_status"] = status
    with pytest.raises(mod.ValidationError, match="unknown_action_authority_status"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("grounding_status", "mystery_grounding", "unknown_grounding_status"),
        ("source_access_status", "mystery_access", "unknown_source_access_status"),
        ("poison_status", "mystery_poison", "unknown_poison_status"),
        ("privacy_status", "mystery_privacy", "unknown_privacy_status"),
        ("public_claim_status", "mystery_public_claim", "unknown_public_claim_status"),
    ],
)
def test_validation_fails_unknown_grounding_access_poison_privacy_public_claim_statuses(
    field: str,
    value: str,
    expected: str,
) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet[field] = value
    with pytest.raises(mod.ValidationError, match=expected):
        mod.validate_live_daemon_verdict_packet_v1(packet)


def test_validation_fails_memory_tier_used_as_trust_level() -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["memory_tier"] = "conversational"
    with pytest.raises(mod.ValidationError, match="memory_tier_confused_with_trust_level|unknown_memory_tier"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


def test_validation_fails_trust_level_used_as_memory_tier() -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["trust_level"] = "identity_core"
    with pytest.raises(mod.ValidationError, match="trust_level_confused_with_memory_tier|unknown_trust_level"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize(
    "field",
    [
        "raw_payload_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ],
)
def test_validation_fails_boolean_authority_flags_when_true(field: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet[field] = True
    with pytest.raises(mod.ValidationError):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("safe_metadata", {"hidden_prompt": "secret"}),
        ("safe_metadata", {"raw_private": "dump"}),
        ("safe_metadata", {"secret": "token"}),
        ("safe_metadata", {"token": "abc"}),
        ("safe_metadata", {"key": "abc"}),
    ],
)
def test_validation_fails_hidden_prompt_raw_private_secret_fields(field: str, value: object) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet[field] = value
    with pytest.raises(mod.ValidationError, match="hidden_prompt_or_raw_private_field"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize(
    "value",
    [
        "AGI",
        "consciousness",
        "sentience",
        "Turing",
        "certification",
        "public readiness",
        "truth certainty",
    ],
)
def test_validation_fails_agi_consciousness_turing_certification_marker(value: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["reason_summary"] = value
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize(
    "value",
    [
        "proof certainty",
        "truth certainty",
        "proof claim",
        "truth claim",
    ],
)
def test_validation_fails_proof_truth_certainty_claim(value: str) -> None:
    packet = deepcopy(_example("chat_render_ready_grounded"))
    packet["next_gate"] = value
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_live_daemon_verdict_packet_v1(packet)


@pytest.mark.parametrize("hint", PROTECTED_MODULE_HINTS)
def test_module_does_not_import_or_call_protected_runtime_files(hint: str) -> None:
    source = inspect.getsource(mod)
    assert hint not in source
    assert hint not in _imported_module_names(source)
