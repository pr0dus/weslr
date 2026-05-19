from __future__ import annotations

from copy import deepcopy
import inspect
import json

import pytest

from weslr import internal_turing_multi_turn_protocol as protocol_mod
from weslr.internal_turing_scenario_corpus import build_internal_turing_scenario_corpus_v1


def _episodes():
    return protocol_mod.build_internal_turing_multi_turn_episode_set_v1()


def _safe_episode():
    return protocol_mod.build_internal_turing_multi_turn_episode_v1(
        episode_id="safe_episode_v1",
        episode_group="ordinary_multi_turn_request",
        scenario_ids=["itsc_v1_01_simple_ordinary_request"],
        turn_summaries=["Initial metadata summary only.", "Follow-up metadata summary only."],
        dimension_targets=["turn-to-turn context preservation"],
        context_constraints=["metadata-only"],
        continuity_requirements=["carry relevant constraints only"],
        correction_points=[],
        ambiguity_points=[],
        evidence_requirements=["preserve evidence boundary labels"],
        memory_boundaries=["summary-only"],
        expected_response_properties=["bounded helpfulness label"],
        failure_modes=["turn_context_drift"],
        safety_boundaries=["internal-only"],
    )


def _invalid_episode(**updates):
    episode = _safe_episode()
    episode.update(updates)
    return episode


def _approved_scenario_ids():
    return {record["scenario_id"] for record in build_internal_turing_scenario_corpus_v1()}


def test_01_module_imports_without_side_effects():
    assert protocol_mod.SCHEMA_VERSION_V1 == "internal_turing_multi_turn_protocol_v1"


def test_02_constants_include_15_episode_groups():
    assert len(protocol_mod.INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1) == 15


def test_03_constants_include_required_multi_turn_dimensions():
    required = {
        "turn-to-turn context preservation",
        "user-intent tracking across turns",
        "ambiguity handling across turns",
        "correction acceptance",
        "continuity without memory overclaim",
        "evidence/provenance honesty",
        "uncertainty preservation",
        "non-canned response formation",
        "emotional/social appropriateness",
        "domain adaptation",
        "governance escalation when needed",
        "final-answer authority boundary",
        "runtime authority boundary",
        "OCC/OpenClaw identity separation",
        "no official overclaiming",
    }
    assert required <= set(protocol_mod.INTERNAL_TURING_MULTI_TURN_DIMENSIONS_V1)


def test_04_episode_set_builder_returns_15_episodes():
    assert len(_episodes()) == 15


def test_05_episode_set_contains_all_required_groups():
    assert {episode["episode_group"] for episode in _episodes()} == set(
        protocol_mod.INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1
    )


def test_06_episode_ids_are_unique():
    ids = [episode["episode_id"] for episode in _episodes()]
    assert len(ids) == len(set(ids))


def test_07_episode_builder_creates_required_fields():
    episode = _safe_episode()
    for field in (
        "episode_id",
        "episode_group",
        "scenario_ids",
        "turn_count",
        "turn_summaries",
        "dimension_targets",
        "context_constraints",
        "continuity_requirements",
        "correction_points",
        "ambiguity_points",
        "evidence_requirements",
        "memory_boundaries",
        "governance_expected",
        "expected_response_properties",
        "failure_modes",
        "safety_boundaries",
        "schema_version",
        "metadata_only",
        "internal_only",
    ):
        assert field in episode


@pytest.mark.parametrize(
    "field",
    [
        "raw_content_allowed",
        "prompt_execution_allowed",
        "final_answer_required",
        "runtime_execution_allowed",
        "official_score_allowed",
        "official_evaluation_claimed",
        "prompt_execution_authorized",
        "final_answer_generated",
        "runtime_wired",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "dot_weslr_write_performed",
        "feature_flag_enabled",
    ],
)
def test_08_episode_builder_sets_required_false_booleans(field):
    assert _safe_episode()[field] is False


@pytest.mark.parametrize("episode", _episodes())
def test_09_each_episode_has_turn_count_at_least_2(episode):
    assert episode["turn_count"] >= 2


@pytest.mark.parametrize("episode", _episodes())
def test_10_each_episode_turn_summaries_count_matches_turn_count(episode):
    assert len(episode["turn_summaries"]) == episode["turn_count"]


@pytest.mark.parametrize("episode", _episodes())
def test_11_each_episode_has_dimension_targets(episode):
    assert episode["dimension_targets"]


@pytest.mark.parametrize("episode", _episodes())
def test_12_each_episode_has_expected_response_properties(episode):
    assert episode["expected_response_properties"]


@pytest.mark.parametrize("episode", _episodes())
def test_13_each_episode_has_failure_modes(episode):
    assert episode["failure_modes"]


@pytest.mark.parametrize("episode", _episodes())
def test_14_episode_references_approved_scenario_ids(episode):
    assert set(episode["scenario_ids"]) <= _approved_scenario_ids()


def test_15_episode_validator_accepts_safe_episode():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_safe_episode())
    assert result["valid"] is True
    assert result["blocked"] is False


def test_16_episode_set_validator_accepts_full_episode_set():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert result["valid"] is True
    assert result["all_groups_present"] is True


def test_17_validator_rejects_unknown_episode_group():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(episode_group="unknown"))
    assert not result["valid"]
    assert "unknown_episode_group" in result["errors"]


def test_18_validator_rejects_unknown_scenario_id():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(scenario_ids=["unknown_scenario"]))
    assert not result["valid"]
    assert "unknown_scenario_id:unknown_scenario" in result["errors"]


def test_19_validator_rejects_missing_required_field():
    episode = _safe_episode()
    del episode["episode_id"]
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(episode)
    assert not result["valid"]
    assert "missing_required_field:episode_id" in result["errors"]


def test_20_validator_rejects_duplicate_episode_ids():
    episodes = _episodes()
    episodes[1]["episode_id"] = episodes[0]["episode_id"]
    result = protocol_mod.validate_internal_turing_multi_turn_episode_set_v1(episodes)
    assert not result["valid"]
    assert result["duplicate_episode_ids"]


def test_21_validator_rejects_turn_count_less_than_2():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(
        _invalid_episode(turn_count=1, turn_summaries=["single metadata summary"])
    )
    assert not result["valid"]
    assert "turn_count_less_than_2" in result["errors"]


def test_22_validator_rejects_mismatched_turn_summaries_count():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(
        _invalid_episode(turn_count=3, turn_summaries=["one", "two"])
    )
    assert not result["valid"]
    assert "turn_summaries_count_mismatch" in result["errors"]


def test_23_validator_rejects_empty_turn_summary():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(
        _invalid_episode(turn_summaries=["metadata", ""])
    )
    assert not result["valid"]
    assert "empty_turn_summary" in result["errors"]


@pytest.mark.parametrize(
    "field,error",
    [
        ("raw_content_allowed", "unsafe_boolean_true:raw_content_allowed"),
        ("prompt_execution_allowed", "unsafe_boolean_true:prompt_execution_allowed"),
        ("final_answer_required", "unsafe_boolean_true:final_answer_required"),
        ("runtime_execution_allowed", "unsafe_boolean_true:runtime_execution_allowed"),
        ("official_score_allowed", "unsafe_boolean_true:official_score_allowed"),
    ],
)
def test_24_to_28_validator_rejects_required_false_booleans_true(field, error):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(**{field: True}))
    assert not result["valid"]
    assert result["safety_booleans_valid"] is False
    assert error in result["errors"]


@pytest.mark.parametrize(
    "field,value,flag",
    [
        ("raw_prompt", "raw prompt: unsafe", "raw_content_detected"),
        ("raw_response", "raw response: unsafe", "raw_content_detected"),
        ("final_answer_text", "final answer: unsafe", "final_answer_detected"),
        ("private_content", "private content: unsafe", "raw_content_detected"),
        ("hidden_prompt", "hidden prompt: unsafe", "raw_content_detected"),
        ("answer_key", "answer key: unsafe", "raw_content_detected"),
        ("provider_output", "provider output: unsafe", "raw_content_detected"),
        ("official_score", "official score: 100", "official_claim_detected"),
    ],
)
def test_29_to_36_validator_rejects_unsafe_keys_and_text(field, value, flag):
    episode = _safe_episode()
    episode[field] = value
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(episode)
    assert not result["valid"]
    assert result[flag] is True


@pytest.mark.parametrize(
    "text",
    [
        "official Turing pass",
        "passed the Turing test",
        "IQ certification",
        "certification granted",
        "certified product-ready",
        "official benchmark",
        "product-readiness certified",
    ],
)
def test_37_validator_rejects_official_claims(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert result["official_claim_detected"] is True


@pytest.mark.parametrize("text", ["WESLR is conscious", "WESLR is sentient", "sentience proven"])
def test_38_validator_rejects_consciousness_or_sentience_claim(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert "consciousness_or_sentience_claim_detected" in result["errors"]


@pytest.mark.parametrize("text", ["OCC is WESLR", "OpenClaw is WESLR", "OCC/OpenClaw as WESLR"])
def test_39_validator_rejects_occ_openclaw_as_weslr_framing(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert "occ_openclaw_as_weslr_detected" in result["errors"]


@pytest.mark.parametrize("text", ["execute prompt", "prompt execution", "run this prompt"])
def test_40_validator_rejects_prompt_execution_marker(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert result["prompt_execution_detected"] is True


@pytest.mark.parametrize("text", ["model_call_made=true", "search_call_made=true", "advisor_call_made=true"])
def test_41_validator_rejects_model_search_advisor_call_markers(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert "provider_call_marker_detected" in result["errors"]


@pytest.mark.parametrize("text", [".weslr write", "write .weslr", "dot_weslr_write_performed=true"])
def test_42_validator_rejects_dot_weslr_write_marker(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert "dot_weslr_write_marker_detected" in result["errors"]


@pytest.mark.parametrize("text", ["feature_flag_enabled=true", "enable feature flag"])
def test_43_validator_rejects_feature_flag_marker(text):
    result = protocol_mod.validate_internal_turing_multi_turn_episode_v1(_invalid_episode(turn_summaries=[text, "metadata"]))
    assert not result["valid"]
    assert "feature_flag_marker_detected" in result["errors"]


def test_44_summary_includes_episode_and_group_counts():
    summary = protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert summary["episode_count"] == 15
    assert summary["group_count"] == 15


def test_45_summary_includes_scenario_reference_count():
    summary = protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert summary["scenario_reference_count"] >= 15


def test_46_summary_includes_dimension_coverage():
    assert protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["dimension_coverage"]


def test_47_summary_includes_failure_mode_coverage():
    assert protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["failure_mode_coverage"]


def test_48_summary_includes_governance_expected_count():
    assert protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["governance_expected_count"] >= 1


def test_49_summary_includes_minor_followups():
    assert set(protocol_mod.INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1) <= set(
        protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["minor_followups"]
    )


def test_50_summary_includes_risks_carried_forward():
    assert set(protocol_mod.INTERNAL_TURING_MULTI_TURN_RISKS_V1) <= set(
        protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["risks_carried_forward"]
    )


def test_51_summary_excludes_raw_prompts_final_answers_private_provider_content():
    text = json.dumps(protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())).lower()
    for forbidden in ["raw prompt:", "raw response:", "final answer:", "private content:", "provider output:"]:
        assert forbidden not in text


def test_52_renderer_includes_episode_set_status():
    assert "Episode Set Status" in protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_53_renderer_includes_validation_status():
    assert "Validation status: valid" in protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_54_renderer_includes_group_coverage():
    assert "Group coverage: 15/15" in protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_55_renderer_includes_scenario_reference_coverage():
    assert "Scenario reference coverage:" in protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_56_renderer_includes_minor_followups():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "renderer_next_lane_wording_drift" in rendered
    assert "validator_phrase_key_limitation" in rendered


def test_57_renderer_includes_carried_risks():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "Turing-name overclaim risk" in rendered
    assert "future label non-scoring discipline" in rendered


def test_58_renderer_includes_safety_confirmation():
    assert "Safety confirmation:" in protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_59_renderer_blocks_invalid_episode_set_without_leaking_offending_content():
    episodes = _episodes()
    episodes[0]["turn_summaries"] = ["raw prompt: SECRET", "metadata"]
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(episodes)
    assert "Status: blocked" in rendered
    assert "SECRET" not in rendered
    assert "raw prompt:" not in rendered.lower()


def test_60_renderer_omits_raw_final_private_provider_content():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    for forbidden in ["raw prompt:", "raw response:", "final answer:", "private content:", "provider output:"]:
        assert forbidden not in rendered


def test_61_json_safe_copy_returns_safe_copy_for_valid_episode_set():
    episodes = _episodes()
    safe = protocol_mod.to_internal_turing_multi_turn_episode_set_json_safe_v1(episodes)
    assert safe == episodes
    assert safe is not episodes


def test_62_json_safe_copy_returns_invalid_wrapper_for_unsafe_episode_set():
    episodes = _episodes()
    episodes[0]["raw_prompt"] = "raw prompt: unsafe"
    wrapped = protocol_mod.to_internal_turing_multi_turn_episode_set_json_safe_v1(episodes)
    assert wrapped["valid"] is False
    assert wrapped["blocked"] is True
    assert "raw prompt: unsafe" not in json.dumps(wrapped).lower()


def test_63_helpers_are_deterministic_for_same_episode_set():
    assert _episodes() == _episodes()
    assert protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes()) == protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())


def test_64_helpers_use_approved_scenario_corpus_references_only():
    result = protocol_mod.validate_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert result["all_scenario_refs_approved"] is True


def test_65_helpers_do_not_mutate_scenario_corpus_helpers():
    before = build_internal_turing_scenario_corpus_v1()
    protocol_mod.build_internal_turing_multi_turn_episode_set_v1()
    after = build_internal_turing_scenario_corpus_v1()
    assert before == after


def test_66_no_helper_writes_files(monkeypatch):
    def fail_open(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError("file write attempted")

    monkeypatch.setattr("builtins.open", fail_open)
    protocol_mod.build_internal_turing_multi_turn_episode_set_v1()
    protocol_mod.validate_internal_turing_multi_turn_episode_set_v1(_episodes())
    protocol_mod.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())
    protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    protocol_mod.to_internal_turing_multi_turn_episode_set_json_safe_v1(_episodes())


def test_67_no_helper_calls_network_subprocess_model_search_advisor():
    source = inspect.getsource(protocol_mod)
    forbidden_calls = ["requests.", "urllib.", "socket.", "subprocess.", "os.system", "model_call(", "search_call(", "advisor_call("]
    for forbidden in forbidden_calls:
        assert forbidden not in source


def test_68_no_chatresponder_respond_chat_generate_chat_calls():
    source = inspect.getsource(protocol_mod)
    for forbidden in ["ChatResponder", "respond_chat(", "generate_chat("]:
        assert forbidden not in source


def test_69_no_official_claims_are_made():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    for forbidden in ["passed the turing", "iq certification", "certified product-ready", "product-readiness certified"]:
        assert forbidden not in rendered


def test_70_no_runtime_ready_declaration_is_rendered():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    assert "runtime ready" not in rendered
    assert "ready for runtime" not in rendered


def test_71_no_prompts_are_executable():
    for episode in _episodes():
        assert episode["prompt_execution_allowed"] is False
        assert episode["prompt_execution_authorized"] is False


def test_72_no_final_answers_are_generated():
    for episode in _episodes():
        assert episode["final_answer_required"] is False
        assert episode["final_answer_generated"] is False


def test_73_no_dot_weslr_writes_occur():
    for episode in _episodes():
        assert episode["dot_weslr_write_performed"] is False


def test_74_minor_followups_remain_visible():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    for followup in protocol_mod.INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1:
        assert followup in rendered


def test_75_risks_remain_visible():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    for risk in protocol_mod.INTERNAL_TURING_MULTI_TURN_RISKS_V1:
        assert risk in rendered


def test_76_observation_labels_are_qualitative_only():
    for label in protocol_mod.INTERNAL_TURING_MULTI_TURN_OBSERVATION_LABELS_V1:
        assert isinstance(label, str)
        assert label
        assert not label.isdigit()
    assert "score" not in " ".join(protocol_mod.INTERNAL_TURING_MULTI_TURN_OBSERVATION_LABELS_V1).lower()


def test_77_failure_taxonomy_is_preserved():
    assert set(protocol_mod.INTERNAL_TURING_MULTI_TURN_FAILURE_TAXONOMY_V1) >= {
        "turn_context_drift",
        "obsolete_intent_persistence",
        "missed_clarification",
        "correction_rejected",
        "memory_overclaim",
        "evidence_overclaim",
        "uncertainty_lost",
        "canned_multi_turn_behavior",
        "emotional_mismatch",
        "domain_constraint_missed",
        "governance_missed",
        "final_answer_authority_overreach",
        "runtime_authority_overreach",
        "official_claim_overreach",
        "identity_confusion",
        "raw_private_content_leakage",
    }


def test_78_next_lane_recommendation_avoids_runtime_wiring():
    rendered = protocol_mod.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "REVIEW_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_IMPLEMENTATION_V1" in rendered
    assert "wire runtime" not in rendered.lower()
    assert "runtime wiring" not in rendered.lower()
