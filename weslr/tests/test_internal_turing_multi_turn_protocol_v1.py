from __future__ import annotations

from copy import deepcopy
import inspect

import pytest

from weslr import internal_turing_multi_turn_protocol as protocol
from weslr import internal_turing_scenario_corpus as corpus_mod


def _episodes():
    return protocol.build_internal_turing_multi_turn_episode_set_v1()


def _episode():
    return _episodes()[0]


def _approved_ids():
    return {record["scenario_id"] for record in corpus_mod.build_internal_turing_scenario_corpus_v1()}


def _invalid_with(**updates):
    episode = deepcopy(_episode())
    episode.update(updates)
    return episode


def _set_with_episode(episode):
    episodes = _episodes()
    episodes[0] = episode
    return episodes


def test_module_imports_without_side_effects():
    assert protocol.SCHEMA_VERSION_V1 == "internal_turing_multi_turn_protocol_v1"


def test_constants_include_15_episode_groups():
    assert len(protocol.INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1) == 15


def test_constants_include_required_multi_turn_dimensions():
    dims = set(protocol.INTERNAL_TURING_MULTI_TURN_DIMENSIONS_V1)
    assert "turn-to-turn context preservation" in dims
    assert "OCC/OpenClaw identity separation" in dims
    assert len(dims) >= 15


def test_episode_set_builder_returns_15_episodes():
    assert len(_episodes()) == 15


def test_episode_set_contains_all_required_groups():
    assert {e["episode_group"] for e in _episodes()} == set(protocol.INTERNAL_TURING_MULTI_TURN_EPISODE_GROUPS_V1)


def test_episode_ids_are_unique():
    ids = [e["episode_id"] for e in _episodes()]
    assert len(ids) == len(set(ids))


def test_episode_builder_creates_required_fields():
    episode = _episode()
    for field in protocol._REQUIRED_FIELDS:
        assert field in episode


@pytest.mark.parametrize("field", protocol._FALSE_SAFETY_FIELDS)
def test_episode_builder_sets_required_false_booleans(field):
    assert _episode()[field] is False


@pytest.mark.parametrize("episode", _episodes())
def test_each_episode_has_turn_count_at_least_two(episode):
    assert episode["turn_count"] >= 2


@pytest.mark.parametrize("episode", _episodes())
def test_each_episode_has_turn_summary_count_matching_turn_count(episode):
    assert len(episode["turn_summaries"]) == episode["turn_count"]


@pytest.mark.parametrize("episode", _episodes())
def test_each_episode_has_dimension_targets(episode):
    assert episode["dimension_targets"]


@pytest.mark.parametrize("episode", _episodes())
def test_each_episode_has_expected_response_properties(episode):
    assert episode["expected_response_properties"]


@pytest.mark.parametrize("episode", _episodes())
def test_each_episode_has_failure_modes(episode):
    assert episode["failure_modes"]


@pytest.mark.parametrize("episode", _episodes())
def test_episode_references_approved_scenario_ids(episode):
    assert set(episode["scenario_ids"]).issubset(_approved_ids())


def test_episode_validator_accepts_safe_episode():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_episode())
    assert result["valid"] is True
    assert result["blocked"] is False


def test_episode_set_validator_accepts_full_episode_set():
    result = protocol.validate_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert result["valid"] is True
    assert result["all_groups_present"] is True


def test_validator_rejects_unknown_episode_group():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(episode_group="unknown_group"))
    assert "unknown_episode_group" in result["errors"]


def test_validator_rejects_unknown_scenario_id():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(scenario_ids=["unknown_scenario_id"]))
    assert "unknown_scenario_id" in result["errors"]


@pytest.mark.parametrize("field", protocol._REQUIRED_FIELDS)
def test_validator_rejects_missing_required_field(field):
    episode = deepcopy(_episode())
    episode.pop(field)
    result = protocol.validate_internal_turing_multi_turn_episode_v1(episode)
    assert any(error == f"missing_required_field:{field}" for error in result["errors"])


def test_validator_rejects_duplicate_episode_ids():
    episodes = _episodes()
    episodes[1]["episode_id"] = episodes[0]["episode_id"]
    result = protocol.validate_internal_turing_multi_turn_episode_set_v1(episodes)
    assert result["duplicate_episode_ids"]


def test_validator_rejects_turn_count_less_than_two():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(turn_count=1, turn_summaries=["one"]))
    assert "turn_count_lt_2" in result["errors"]


def test_validator_rejects_mismatched_turn_summary_count():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(turn_count=3))
    assert "turn_summaries_count_mismatch" in result["errors"]


def test_validator_rejects_empty_turn_summary():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(turn_summaries=["", "safe"]))
    assert "empty_turn_summary" in result["errors"]


@pytest.mark.parametrize(
    "field",
    [
        "raw_content_allowed",
        "prompt_execution_allowed",
        "final_answer_required",
        "runtime_execution_allowed",
        "official_score_allowed",
    ],
)
def test_validator_rejects_primary_unsafe_booleans_true(field):
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(**{field: True}))
    assert f"unsafe_boolean_true_or_missing:{field}" in result["errors"]


@pytest.mark.parametrize(
    ("update", "expected"),
    [
        ({"raw_prompt_text": "metadata-only"}, "raw_content_detected"),
        ({"raw_response_text": "metadata-only"}, "raw_content_detected"),
        ({"final_answer_text": "metadata-only"}, "final_answer_detected"),
        ({"notes": ["private content: redacted"]}, "private_content_detected"),
        ({"notes": ["hidden prompt: redacted"]}, "hidden_prompt_detected"),
        ({"answer_key": "redacted"}, "answer_key_detected"),
        ({"provider_output": "redacted"}, "provider_or_model_output_detected"),
        ({"official_score": "redacted"}, "official_score_or_claim_detected"),
        ({"notes": ["official Turing pass"]}, "official_score_or_claim_detected"),
        ({"notes": ["IQ certification"]}, "official_score_or_claim_detected"),
        ({"notes": ["certified product-ready"]}, "official_score_or_claim_detected"),
        ({"notes": ["WESLR is conscious"]}, "consciousness_or_sentience_claim_detected"),
        ({"notes": ["WESLR is sentient"]}, "consciousness_or_sentience_claim_detected"),
        ({"notes": ["OCC is WESLR"]}, "identity_confusion_detected"),
        ({"notes": ["execute prompt"]}, "prompt_execution_detected"),
        ({"notes": ["model_call_made=true"]}, "provider_or_model_output_detected"),
        ({"notes": ["search_call_made=true"]}, "provider_or_model_output_detected"),
        ({"notes": ["advisor_call_made=true"]}, "provider_or_model_output_detected"),
        ({"notes": [".weslr write"]}, "dot_weslr_write_detected"),
        ({"notes": ["feature_flag_enabled=true"]}, "feature_flag_detected"),
    ],
)
def test_validator_rejects_unsafe_keys_and_markers(update, expected):
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(**update))
    assert expected in result["errors"]


def test_validator_rejects_runtime_outputs_treated_as_authority():
    result = protocol.validate_internal_turing_multi_turn_episode_v1(_invalid_with(runtime_output_text="metadata-only"))
    assert "runtime_authority_detected" in result["errors"]


def test_episode_set_validator_reports_unknown_scenario_ids():
    result = protocol.validate_internal_turing_multi_turn_episode_set_v1(_set_with_episode(_invalid_with(scenario_ids=["unknown"])))
    assert result["unknown_scenario_ids"] == ["unknown"]


def test_episode_set_validator_requires_all_groups():
    result = protocol.validate_internal_turing_multi_turn_episode_set_v1(_episodes()[:-1])
    assert result["all_groups_present"] is False
    assert result["missing_groups"]


def test_summary_includes_episode_and_group_counts():
    summary = protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())
    assert summary["episode_count"] == 15
    assert summary["group_count"] == 15


def test_summary_includes_scenario_reference_count():
    assert protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["scenario_reference_count"] == 15


def test_summary_includes_dimension_coverage():
    assert protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["dimension_coverage"]


def test_summary_includes_failure_mode_coverage():
    assert protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["failure_mode_coverage"]


def test_summary_includes_governance_expected_count():
    assert protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["governance_expected_count"] >= 1


def test_summary_includes_minor_followups():
    assert set(protocol.INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1).issubset(
        protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["minor_followups"]
    )


def test_summary_includes_risks_carried_forward():
    assert set(protocol.INTERNAL_TURING_MULTI_TURN_RISKS_V1).issubset(
        protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())["risks_carried_forward"]
    )


def test_summary_excludes_raw_final_private_provider_content():
    summary_text = repr(protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())).lower()
    for forbidden in ("raw prompt:", "final answer:", "private content:", "provider output:"):
        assert forbidden not in summary_text


def test_renderer_includes_episode_set_status():
    assert "Episode Set Status" in protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_renderer_includes_validation_status():
    assert "Validation Status" in protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_renderer_includes_group_coverage():
    assert "Group Coverage" in protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_renderer_includes_scenario_reference_coverage():
    assert "Scenario Reference Coverage" in protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_renderer_includes_minor_followups():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "renderer_next_lane_wording_drift" in rendered


def test_renderer_includes_carried_risks():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "Turing-name overclaim risk" in rendered


def test_renderer_includes_safety_confirmation():
    assert "Safety Confirmation" in protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())


def test_renderer_blocks_invalid_episode_set_without_leaking_offending_content():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(
        _set_with_episode(_invalid_with(notes=["private content: SHOULD_NOT_RENDER"]))
    )
    assert "blocked_reason_labels" in rendered
    assert "SHOULD_NOT_RENDER" not in rendered


def test_renderer_omits_raw_final_private_provider_content():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    for forbidden in ("raw prompt:", "raw response:", "final answer:", "private content:", "provider output:"):
        assert forbidden not in rendered


def test_json_safe_copy_returns_safe_copy_for_valid_episode_set():
    episodes = _episodes()
    copy = protocol.to_internal_turing_multi_turn_episode_set_json_safe_v1(episodes)
    assert copy == episodes
    assert copy is not episodes


def test_json_safe_copy_returns_invalid_wrapper_for_unsafe_episode_set():
    wrapper = protocol.to_internal_turing_multi_turn_episode_set_json_safe_v1(
        _set_with_episode(_invalid_with(raw_prompt_text="metadata-only"))
    )
    assert wrapper["valid"] is False
    assert wrapper["blocked"] is True
    assert wrapper["raw_content_returned"] is False


def test_helpers_are_deterministic_for_same_episode_set():
    assert _episodes() == _episodes()
    assert protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes()) == protocol.summarize_internal_turing_multi_turn_episode_set_v1(_episodes())


def test_helpers_use_approved_scenario_corpus_references_only():
    refs = {sid for episode in _episodes() for sid in episode["scenario_ids"]}
    assert refs.issubset(_approved_ids())


def test_helpers_do_not_mutate_scenario_corpus_helpers():
    before = corpus_mod.build_internal_turing_scenario_corpus_v1()
    protocol.build_internal_turing_multi_turn_episode_set_v1()
    after = corpus_mod.build_internal_turing_scenario_corpus_v1()
    assert before == after


def test_no_helper_writes_files():
    source = inspect.getsource(protocol)
    forbidden = ("open(", "write_text", "Path(", "mkdir", "unlink(")
    assert not any(token in source for token in forbidden)


def test_no_helper_calls_network_subprocess_model_search_advisor():
    source = inspect.getsource(protocol)
    forbidden = ("subprocess", "requests", "urllib", "socket", "model_provider", "search_provider", "advisor_provider")
    assert not any(token in source for token in forbidden)


def test_no_chatresponder_respond_chat_generate_chat_calls():
    source = inspect.getsource(protocol)
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


def test_no_official_claims_are_made():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    for forbidden in ("official turing pass", "passed the turing test", "iq certification", "certified product-ready"):
        assert forbidden not in rendered


def test_no_runtime_ready_declaration_is_rendered():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    assert "runtime ready" not in rendered
    assert "runtime integration not authorized" in rendered


def test_no_prompts_are_executable():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes()).lower()
    assert "execute prompt" not in rendered
    assert "prompt execution not authorized" in rendered


def test_no_final_answers_are_generated():
    episodes = _episodes()
    assert all(e["final_answer_generated"] is False for e in episodes)
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(episodes).lower()
    assert "final answer:" not in rendered


def test_no_dot_weslr_writes_occur():
    assert all(e["dot_weslr_write_performed"] is False for e in _episodes())


def test_minor_followups_remain_visible():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    for followup in protocol.INTERNAL_TURING_MULTI_TURN_MINOR_FOLLOWUPS_V1:
        assert followup in rendered


def test_risks_remain_visible():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    for risk in protocol.INTERNAL_TURING_MULTI_TURN_RISKS_V1:
        assert risk in rendered


def test_observation_labels_are_qualitative_only():
    assert all(isinstance(label, str) and not any(char.isdigit() for char in label) for label in protocol.INTERNAL_TURING_MULTI_TURN_OBSERVATION_LABELS_V1)


def test_failure_taxonomy_is_preserved():
    assert set(protocol.INTERNAL_TURING_MULTI_TURN_FAILURE_TAXONOMY_V1) == {
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


def test_next_lane_recommendation_avoids_runtime_wiring():
    rendered = protocol.render_internal_turing_multi_turn_episode_set_markdown_v1(_episodes())
    assert "REVIEW_INTERNAL_TURING_MULTI_TURN_PROTOCOL_HELPERS_IMPLEMENTATION_V1" in rendered
    assert "IMPLEMENT_RUNTIME" not in rendered
