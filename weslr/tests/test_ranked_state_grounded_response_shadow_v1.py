from __future__ import annotations

import inspect
import json

import pytest

from weslr import ranked_state_grounded_response_shadow as shadow


def safe_state(**overrides):
    base = dict(
        user_turn_interpretation={"intent": "plan", "summary": "synthetic metadata only"},
        inferred_need={"need": "bounded next step"},
        uncertainty={"status": "low", "missing": []},
        task_type="planning",
        domain_context={"domain": "core", "boundary": "general"},
        relationship_context={"tone": "collaborative"},
        memory_relevance={"records": 0, "status": "not_needed"},
        continuity_relevance={"status": "active_context_only"},
        evidence_requirement={"status": "required"},
        provenance_requirement={"status": "required"},
        capability_boundary={"status": "bounded"},
        safety_boundary={"status": "safe"},
        legal_moral_boundary={"status": "clear"},
        response_obligation={"shape": "bounded_plan"},
    )
    base.update(overrides)
    return shadow.build_response_state_frame_v1(**base)


def candidate(candidate_id="safe", **overrides):
    base = dict(
        candidate_id=candidate_id,
        candidate_type="bounded_plan",
        source_basis={"basis": "state_frame"},
        intended_response_shape={"shape": "brief_plan"},
        grounding_notes=["derived from synthetic state metadata"],
        evidence_fit="sufficient",
        provenance_fit="clear",
        domain_fit="strong",
        continuity_fit="strong",
        safety_fit="safe",
        uncertainty_handling="honest",
        actionability="actionable",
        non_cannedness="state_grounded",
        requires_model_call=False,
        requires_search_call=False,
        requires_advisor_call=False,
        requires_governance=False,
        risk_labels=[],
    )
    base.update(overrides)
    return shadow.build_candidate_response_v1(**base)


def ranked_artifact():
    state = safe_state()
    candidates = [candidate("safe"), candidate("unsafe", safety_fit="unsafe", risk_labels=["unsafe"])]
    ranking = shadow.rank_candidate_responses_v1(state, candidates)
    return state, candidates, ranking


# 1
def test_state_frame_builder_returns_required_metadata_and_safety_flags():
    frame = safe_state()
    assert frame["schema_version"] == shadow.SCHEMA_VERSION_V1
    assert frame["helper_name"] == shadow.HELPER_NAME_V1
    assert frame["runtime_wired"] is False
    assert frame["shadow_only"] is True
    assert frame["final_answer_generated"] is False
    assert frame["raw_prompt_retained"] is False
    assert frame["raw_response_retained"] is False
    assert frame["model_call_made"] is False
    assert frame["search_call_made"] is False
    assert frame["advisor_call_made"] is False
    assert frame["persistence_performed"] is False


# 2
def test_state_frame_does_not_require_raw_prompt_text():
    frame = shadow.build_response_state_frame_v1(inferred_need={"need": "clarify"})
    assert frame["user_turn_interpretation"] == {}
    assert "raw_prompt" not in frame
    assert "prompt_text" not in frame


# 3
def test_candidate_builder_metadata_only_no_final_answer_text():
    item = candidate(final_answer_text="should be dropped")
    assert item["final_answer_text_present"] is False
    assert "final_answer_text" not in item
    assert item["sanitized_forbidden_input_fields"] == ["final_answer_text"]


# 4
def test_ranking_selects_strong_safe_candidate_over_weak_canned_unsafe():
    state = safe_state()
    safe = candidate("strong")
    weak = candidate("weak", evidence_fit="sufficient", provenance_fit="clear", safety_fit="safe", non_cannedness="low")
    unsafe = candidate("unsafe", safety_fit="unsafe", risk_labels=["unsafe"])
    result = shadow.rank_candidate_responses_v1(state, [weak, unsafe, safe])
    assert result["selected_candidate_id"] == "strong"
    assert result["selected_label"] == "strong_fit"
    assert "unsafe" in result["rejected_candidate_ids"]
    assert "weak" in result["rejected_candidate_ids"]


# 5
def test_ranking_rejects_unauthorized_model_call_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("model", requires_model_call=True)])
    assert result["selected_candidate_id"] is None
    assert result["ranking_trace"][0]["label"] == "not_authorized"


# 6
def test_ranking_rejects_unauthorized_search_call_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("search", requires_search_call=True)])
    assert result["selected_candidate_id"] is None
    assert result["ranking_trace"][0]["label"] == "not_authorized"


# 7
def test_ranking_rejects_unauthorized_advisor_call_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("advisor", requires_advisor_call=True)])
    assert result["selected_candidate_id"] is None
    assert result["ranking_trace"][0]["label"] == "not_authorized"


# 8
def test_ranking_rejects_unsupported_evidence_required_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("no_evidence", evidence_fit="insufficient")])
    assert result["selected_candidate_id"] is None
    assert result["ranking_trace"][0]["label"] == "needs_evidence"


# 9
def test_ranking_rejects_provenance_failing_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("no_provenance", provenance_fit="missing")])
    assert result["selected_candidate_id"] is None
    assert "no_provenance" in result["rejected_candidate_ids"]


# 10
def test_ranking_rejects_domain_legal_moral_boundary_violation():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("domain_bad", domain_fit="outside_scope", risk_labels=["legal_violation"])])
    assert result["selected_candidate_id"] is None
    trace = result["ranking_trace"][0]
    assert "domain_boundary" in trace["boundary_labels"]
    assert "legal_moral_boundary" in trace["boundary_labels"]


# 11
def test_ranking_rejects_canned_template_like_candidate():
    result = shadow.rank_candidate_responses_v1(safe_state(), [candidate("canned", non_cannedness="keyword_only template")])
    assert result["selected_candidate_id"] is None
    assert "canned" in result["rejected_candidate_ids"]


# 12
def test_rejection_classifier_returns_reason_labels():
    classification = shadow.classify_candidate_rejection_v1(candidate("bad", requires_search_call=True), safe_state())
    assert classification["rejected"] is True
    assert "unauthorized_search_call_required" in classification["reason_labels"]
    assert classification["safe_fallback_needed"] is True


# 13
def test_self_check_passes_safe_selected_candidate():
    state, candidates, ranking = ranked_artifact()
    check = shadow.self_check_selected_candidate_v1(state, candidates[0], ranking)
    assert check["passed"] is True
    assert check["issue_labels"] == []


# 14
def test_self_check_fails_artifact_with_final_answer_text_marker():
    state, candidates, ranking = ranked_artifact()
    bad = dict(candidates[0], final_answer_text_present=True)
    check = shadow.self_check_selected_candidate_v1(state, bad, ranking)
    assert check["passed"] is False
    assert "selected_candidate_final_answer_text_present" in check["issue_labels"]


# 15
def test_final_answer_contract_metadata_does_not_generate_final_answer():
    state, candidates, ranking = ranked_artifact()
    check = shadow.self_check_selected_candidate_v1(state, candidates[0], ranking)
    contract = shadow.build_final_answer_contract_metadata_v1(state, candidates[0], check)
    assert contract["final_answer_generated"] is False
    assert contract["final_answer_text_present"] is False
    assert "final_answer" not in contract


# 16
def test_validator_rejects_forbidden_raw_prompt_response_keys():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"raw_prompt": "secret", "raw_response": "answer"})
    assert validation["valid"] is False
    assert "forbidden_key:raw_prompt" in validation["reason_labels"]
    assert "forbidden_key:raw_response" in validation["reason_labels"]


# 17
def test_validator_rejects_hidden_prompt_and_answer_key_keys():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"hidden_prompt": "x", "answer_key": "a"})
    assert validation["valid"] is False
    assert "forbidden_key:hidden_prompt" in validation["reason_labels"]
    assert "forbidden_key:answer_key" in validation["reason_labels"]


# 18
def test_validator_rejects_runtime_wired_true():
    assert "runtime_wired_true" in shadow.validate_ranked_response_shadow_artifact_v1({"runtime_wired": True})["reason_labels"]


# 19
def test_validator_rejects_model_search_advisor_call_made_true():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"model_call_made": True, "search_call_made": True, "advisor_call_made": True})
    assert {"model_call_made_true", "search_call_made_true", "advisor_call_made_true"}.issubset(set(validation["reason_labels"]))


# 20
def test_validator_rejects_persistence_true():
    assert "persistence_performed_true" in shadow.validate_ranked_response_shadow_artifact_v1({"persistence_performed": True})["reason_labels"]


# 21
def test_validator_rejects_official_turing_iq_benchmark_product_claim_markers():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"claim": "passed Turing with official IQ score and official benchmark product readiness certified"})
    assert validation["valid"] is False
    assert "official_claim_marker_present" in validation["reason_labels"]


# 22
def test_validator_rejects_consciousness_sentience_markers():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"claim": "WESLR is conscious and WESLR is sentient"})
    assert "consciousness_or_sentience_claim_marker_present" in validation["reason_labels"]


# 23
def test_validator_rejects_occ_as_weslr_marker():
    validation = shadow.validate_ranked_response_shadow_artifact_v1({"claim": "OCC is WESLR"})
    assert "occ_as_weslr_claim_marker_present" in validation["reason_labels"]


# 24
def test_json_safe_helper_does_not_sanitize_invalid_artifact_silently():
    result = shadow.to_ranked_response_shadow_json_safe_v1({"raw_prompt": "secret"})
    assert result["valid"] is False
    assert result["artifact_rejected"] is True
    assert result["validation"]["valid"] is False


# 25
def test_summary_helper_returns_count_status_only():
    _, _, ranking = ranked_artifact()
    summary = shadow.summarize_ranked_response_shadow_v1(ranking)
    assert summary["number_of_candidates"] == 2
    assert summary["selected_label"] == "strong_fit"
    assert summary["rejected_count"] == 1
    assert summary["raw_content_included"] is False
    assert "raw_prompt" not in summary
    assert "response_text" not in summary


# 26
def test_markdown_renderer_does_not_include_raw_prompt_response_final_answer_text():
    _, _, ranking = ranked_artifact()
    rendered = shadow.render_ranked_response_shadow_markdown_v1(ranking)
    lowered = rendered.lower()
    assert "synthetic secret" not in lowered
    assert "response_text" not in lowered
    assert "final_answer_text" not in lowered
    assert "final_answer_generated" in lowered


# 27
def test_all_helpers_are_deterministic_for_same_metadata_input():
    state_a = safe_state()
    state_b = safe_state()
    cand_a = candidate("same")
    cand_b = candidate("same")
    assert state_a == state_b
    assert cand_a == cand_b
    assert shadow.rank_candidate_responses_v1(state_a, [cand_a]) == shadow.rank_candidate_responses_v1(state_b, [cand_b])


# 28
def test_no_helper_writes_files_by_static_source_check():
    source = inspect.getsource(shadow)
    forbidden = ["open(", ".write(", "Path(", "pathlib", "NamedTemporaryFile"]
    assert not any(token in source for token in forbidden)


# 29
def test_no_network_subprocess_model_search_advisor_calls_by_static_source_check():
    source = inspect.getsource(shadow)
    forbidden = ["import subprocess", "import requests", "import urllib", "import socket", "generate_chat(", "respond_chat(", "ChatResponder(", "web_search(", "advisor.call("]
    assert not any(token in source for token in forbidden)


# 30
def test_readiness_labels_are_present_on_artifacts():
    frame = safe_state()
    item = candidate("safe")
    ranking = shadow.rank_candidate_responses_v1(frame, [item])
    for artifact in (frame, item, ranking):
        labels = set(artifact["readiness_labels"])
        assert set(shadow.READINESS_LABELS_V1).issubset(labels)


# Extra coverage
def test_validator_accepts_safe_ranking_artifact():
    _, _, ranking = ranked_artifact()
    validation = shadow.validate_ranked_response_shadow_artifact_v1(ranking)
    assert validation["valid"] is True
    assert validation["safe_to_inspect"] is True


def test_to_json_safe_preserves_valid_artifact_with_validation_state():
    _, _, ranking = ranked_artifact()
    safe = shadow.to_ranked_response_shadow_json_safe_v1(ranking)
    assert safe["validation"]["valid"] is True
    assert safe["selected_candidate_id"] == "safe"


def test_state_builder_sanitizes_forbidden_extra_fields_without_retaining_raw_text():
    frame = shadow.build_response_state_frame_v1(raw_prompt="secret prompt", full_conversation="secret convo")
    assert sorted(frame["sanitized_forbidden_input_fields"]) == ["full_conversation", "raw_prompt"]
    dumped = json.dumps(frame)
    assert "secret prompt" not in dumped
    assert "secret convo" not in dumped


def test_candidate_builder_sanitizes_nested_forbidden_fields():
    item = candidate("nested", safe_extra={"raw_response": "secret"})
    assert "safe_extra.raw_response" in item["sanitized_forbidden_input_fields"]
    assert "secret" not in json.dumps(item)


def test_weak_but_safe_candidate_can_be_selected_when_only_non_rejected_option():
    weak = candidate("weak_safe", actionability="unknown", continuity_fit="unknown", domain_fit="unknown", non_cannedness="state_grounded")
    result = shadow.rank_candidate_responses_v1(safe_state(), [weak])
    assert result["selected_candidate_id"] == "weak_safe"
    assert result["selected_label"] in {"weak_fit", "acceptable_fit", "strong_fit"}
