from __future__ import annotations

import importlib
import json
import sys

import pytest

from weslr.no_model_bounded_renderer import (
    NoModelBoundedRenderPacket,
    build_no_model_bounded_render_packet_v1,
    render_no_model_bounded_answer_v1,
    summarize_no_model_bounded_render_packet_v1,
    to_no_model_bounded_render_json_safe_v1,
    validate_no_model_bounded_render_packet_v1,
)


def _packet(labels, context=None):
    return build_no_model_bounded_render_packet_v1(labels, context_signals=context or {})


def _json(packet):
    return to_no_model_bounded_render_json_safe_v1(packet)


def test_module_import_is_safe_and_public_api_exists():
    module = importlib.import_module("weslr.no_model_bounded_renderer")
    for name in (
        "NoModelBoundedRenderPacket",
        "NoModelRenderedAnswer",
        "NoModelRenderTrace",
        "NoModelRenderSummary",
        "build_no_model_bounded_render_packet_v1",
        "validate_no_model_bounded_render_packet_v1",
        "summarize_no_model_bounded_render_packet_v1",
        "to_no_model_bounded_render_json_safe_v1",
        "render_no_model_bounded_answer_v1",
    ):
        assert hasattr(module, name)


@pytest.mark.parametrize("labels", [["who are you", "status"], ["identity", "status"]])
def test_renders_deterministic_packet(labels):
    assert _json(_packet(labels)) == _json(_packet(labels))


def test_validates_normal_packet():
    packet = _packet(["who are you", "status"])
    assert validate_no_model_bounded_render_packet_v1(packet) is True
    assert isinstance(packet, NoModelBoundedRenderPacket)


def test_json_safe_export_works():
    payload = _json(_packet(["memory", "remember"]))
    assert isinstance(payload, dict)
    json.dumps(payload)
    assert isinstance(payload["render_trace"], dict)


def test_summary_includes_render_mode_and_selected_candidate():
    packet = _packet(["who are you", "status"])
    summary = summarize_no_model_bounded_render_packet_v1(packet)
    payload = _json(packet)
    assert summary.render_mode == payload["render_mode"]
    assert summary.selected_candidate_id == payload["selected_candidate_id"]


def test_direct_bounded_labels_render_non_empty_bounded_text():
    packet = _packet(["who are you", "status"])
    payload = _json(packet)
    assert payload["render_mode"] == "direct_bounded"
    assert payload["response_text"].strip()
    assert "bounded" in payload["response_text"].lower()


def test_identity_status_renders_bounded_identity_text():
    packet = _packet(["identity", "status"])
    payload = _json(packet)
    assert payload["render_mode"] == "direct_bounded"
    assert "identity" in payload["response_text"].lower()


def test_memory_uncertainty_renders_memory_honesty_text():
    packet = _packet(["memory", "remember", "do you remember"])
    payload = _json(packet)
    assert payload["render_mode"] == "memory_honesty"
    assert "memory" in payload["response_text"].lower()


def test_continuity_signal_renders_continuity_recap_text():
    packet = _packet(["continuity", "follow up", "what were we doing"])
    payload = _json(packet)
    assert payload["render_mode"] == "continuity_recap"
    assert "continuity" in payload["response_text"].lower() or "we were on" in payload["response_text"].lower()


def test_missing_context_renders_one_focused_clarification_question():
    packet = _packet([])
    payload = _json(packet)
    assert payload["render_mode"] == "clarifying_question"
    assert payload["response_text"].strip().endswith("?")
    assert payload["response_text"].count("?") == 1


def test_uncertainty_renders_bounded_uncertainty_text():
    packet = _packet(["uncertain", "not sure", "maybe"])
    payload = _json(packet)
    assert payload["render_mode"] == "bounded_uncertainty"
    assert "not fully sure" in payload["response_text"].lower() or "not sure" in payload["response_text"].lower()


def test_unsafe_boundary_renders_refusal_boundary_text():
    packet = _packet(["unsafe", "privacy", "not allowed"])
    payload = _json(packet)
    assert payload["render_mode"] == "refusal_boundary"
    assert "can't help" in payload["response_text"].lower() or "safe alternative" in payload["response_text"].lower()


def test_missing_evidence_renders_evidence_needed_text():
    packet = _packet(["need evidence", "source", "current"])
    payload = _json(packet)
    assert payload["render_mode"] == "evidence_needed"
    assert "evidence" in payload["response_text"].lower() or "source" in payload["response_text"].lower()


def test_partial_supported_renders_partial_supported_text():
    packet = _packet(["partial", "supported", "split answer"])
    payload = _json(packet)
    assert payload["render_mode"] == "partial_supported"
    assert "supported part" in payload["response_text"].lower()


def test_ordinary_task_renders_stepwise_plan_text():
    packet = _packet(["task", "plan", "checklist"])
    payload = _json(packet)
    assert payload["render_mode"] == "stepwise_plan"
    assert "1." in payload["response_text"]


def test_implementation_planning_renders_implementation_plan_text():
    packet = _packet(["implementation", "build", "next lane"])
    payload = _json(packet)
    assert payload["render_mode"] == "implementation_plan"
    assert "implementation" in payload["response_text"].lower()


def test_workflow_next_lane_renders_workflow_text():
    packet = _packet(["next lane", "sequence", "what next"])
    payload = _json(packet)
    assert payload["render_mode"] == "workflow_next_lane"
    assert "next lane" in payload["response_text"].lower()


def test_governance_escalation_renders_owner_review_text():
    packet = _packet(["approval", "operator review", "blocked"])
    payload = _json(packet)
    assert payload["render_mode"] == "governance_escalation"
    assert "owner review" in payload["response_text"].lower() or "needs owner review" in payload["response_text"].lower()


def test_teaching_renders_teaching_text():
    packet = _packet(["teach", "explain", "education"])
    payload = _json(packet)
    assert payload["render_mode"] == "teaching_explanation"
    assert "teach" in payload["response_text"].lower() or "short version" in payload["response_text"].lower()


def test_language_grammar_vocabulary_renders_language_discovery_explanation_text():
    packet = _packet(["language", "grammar", "vocabulary"])
    payload = _json(packet)
    assert payload["render_mode"] == "language_discovery_explanation"
    assert "language-discovery" in payload["response_text"].lower() or "grammar" in payload["response_text"].lower()


def test_scientific_discovery_renders_bounded_research_guidance_text():
    packet = _packet(["scientific", "research", "experiment"])
    payload = _json(packet)
    assert payload["render_mode"] == "scientific_discovery_guidance"
    assert "research" in payload["response_text"].lower() or "guidance" in payload["response_text"].lower()


def test_benchmark_evaluation_renders_non_official_evaluation_summary_text():
    packet = _packet(["benchmark", "evaluation", "readiness"])
    payload = _json(packet)
    assert payload["render_mode"] == "benchmark_evaluation_summary"
    assert "certify" not in payload["response_text"].lower()


def test_unknown_word_phrase_renders_unknown_friction_text():
    packet = _packet(["unknown word", "what does this mean"])
    payload = _json(packet)
    assert payload["render_mode"] == "unknown_friction"
    assert "unknown" in payload["response_text"].lower() or "friction" in payload["response_text"].lower()


def test_unknown_intent_renders_unknown_or_clarification_text():
    packet = _packet(["unknown intent", "what do you mean"])
    payload = _json(packet)
    assert payload["render_mode"] in {"unknown_friction", "clarifying_question"}


def test_unknown_capability_renders_bounded_capability_unknown_text():
    packet = _packet(["unknown capability", "can you do this"])
    payload = _json(packet)
    assert payload["render_mode"] == "unknown_friction"
    assert "capability" in payload["response_text"].lower()


def test_repeated_friction_renders_friction_text():
    packet = _packet(["repeated failure", "stuck", "friction"])
    payload = _json(packet)
    assert payload["render_mode"] == "unknown_friction"
    assert "friction" in payload["response_text"].lower()


def test_relationship_feedback_renders_bounded_acknowledgment_plus_next_step():
    packet = _packet(["relationship", "feedback", "frustration"])
    payload = _json(packet)
    assert payload["render_mode"] == "relationship_feedback"
    assert "feedback" in payload["response_text"].lower() or "next" in payload["response_text"].lower()


def test_correction_signal_renders_correction_repair_text():
    packet = _packet(["actually", "wrong", "fix"])
    payload = _json(packet)
    assert payload["render_mode"] == "correction_repair"
    assert "correct" in payload["response_text"].lower() or "repair" in payload["response_text"].lower()


def test_contradiction_signal_renders_conflict_text():
    packet = _packet(["contradiction", "inconsistent", "clash"])
    payload = _json(packet)
    assert payload["render_mode"] == "conflict_contradiction"
    assert "contradiction" in payload["response_text"].lower() or "conflict" in payload["response_text"].lower()


def test_non_canned_pressure_avoids_generic_boilerplate():
    packet = _packet(["template", "generic", "boilerplate"])
    payload = _json(packet)
    assert payload["render_mode"] == "non_canned_specificity"
    assert "specific" in payload["response_text"].lower()
    assert "boilerplate" not in payload["response_text"].lower()


def test_directness_concern_renders_direct_bounded_text():
    packet = _packet(["directness", "too direct", "concern"])
    payload = _json(packet)
    assert payload["render_mode"] == "directness_concern"
    assert "directly" in payload["response_text"].lower()


def test_blocked_fit_renders_boundary_text_only():
    packet = _packet(["unsafe", "privacy", "not allowed"])
    payload = _json(packet)
    assert payload["blocked"] is True
    assert payload["render_mode"] == "refusal_boundary"
    assert "safe alternative" in payload["response_text"].lower() or "can't help" in payload["response_text"].lower()


def test_no_raw_prompt_text_is_echoed():
    packet = _packet(["who are you", "status"], {"raw_prompt_text": "secret prompt"})
    payload = _json(packet)
    assert "secret prompt" not in payload["response_text"]
    with pytest.raises(ValueError):
        validate_no_model_bounded_render_packet_v1(packet)


def test_no_model_provider_claim_appears():
    packet = _packet(["who are you", "status"])
    response = _json(packet)["response_text"].lower()
    assert "language model" not in response
    assert "as an ai" not in response


def test_no_consciousness_or_sentience_claim_appears():
    packet = _packet(["who are you", "status"])
    response = _json(packet)["response_text"].lower()
    assert "conscious" not in response
    assert "sentient" not in response


def test_no_official_turing_intelligence_certification_claim_appears():
    packet = _packet(["benchmark", "evaluation", "readiness"])
    response = _json(packet)["response_text"].lower()
    assert "certified" not in response
    assert "turing" not in response
    assert "official benchmark" not in response


@pytest.mark.parametrize(
    "context,field",
    [
        ({"runtime_authority": True}, "runtime_authority"),
        ({"model_provider_used": True}, "model_provider_used"),
        ({"writes_state": True}, "writes_state"),
        ({"chat_wired": True}, "chat_wired"),
        ({"public_ready": True}, "public_ready"),
    ],
)
def test_forbidden_context_flags_fail_validation(context, field):
    packet = _packet(["who are you", "status"], context)
    with pytest.raises(ValueError):
        validate_no_model_bounded_render_packet_v1(packet)


def test_raw_prompt_leakage_fails_validation():
    packet = _packet(["who are you", "status"], {"raw_prompt_text": "secret prompt"})
    with pytest.raises(ValueError):
        validate_no_model_bounded_render_packet_v1(packet)


@pytest.mark.parametrize("module_name", ["weslr.chat_responder", "weslr.main", "dialogue", "chat_ui"])
def test_renderer_does_not_import_forbidden_modules(monkeypatch, module_name):
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    importlib.reload(importlib.import_module("weslr.no_model_bounded_renderer"))
    _packet(["who are you", "status"])
    assert module_name not in sys.modules
