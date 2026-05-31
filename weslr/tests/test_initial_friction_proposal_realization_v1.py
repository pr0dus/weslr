from __future__ import annotations

import pytest

from weslr.friction_replay_harness import build_initial_renderer_friction_replay_v1
from weslr.no_model_bounded_renderer import render_no_model_bounded_answer_v1, to_no_model_bounded_render_json_safe_v1
from weslr.response_fit_self_check import check_candidate_response_fit_v1, to_response_fit_self_check_json_safe_v1
from weslr.response_method_selector import select_response_route_v1, to_response_selection_json_safe_v1


@pytest.mark.parametrize(
    "prompt, expected_route, expected_method, expected_shape, expected_case",
    [
        ("What are you?", "identity_status_route", "method_identity_status", "shape_identity_status", "case_identity_status"),
        ("Explain WESLR.", "identity_status_route", "method_identity_status", "shape_identity_status", "case_identity_status"),
        ("What can you do?", "capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
        ("What capabilities are active?", "capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
        ("Can I upload files?", "capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
        ("Can I pay now?", "capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
        ("Is marketplace active?", "capability_orientation_route", "method_capability_orientation", "shape_capability_orientation", "case_capability_orientation"),
        ("What is qlorbex?", "unknown_word_phrase_route", "method_unknown_word_phrase", "shape_unknown_word_phrase", "case_unknown_word_phrase"),
        ("I found an unknown word.", "unknown_word_phrase_route", "method_unknown_word_phrase", "shape_unknown_word_phrase", "case_unknown_word_phrase"),
        ("This phrase is unfamiliar.", "unknown_word_phrase_route", "method_unknown_word_phrase", "shape_unknown_word_phrase", "case_unknown_word_phrase"),
    ],
)
def test_selector_routes_neighbor_prompts(prompt, expected_route, expected_method, expected_shape, expected_case):
    packet = to_response_selection_json_safe_v1(select_response_route_v1(prompt.split(), {}))
    assert packet["selected_route_id"] == expected_route
    assert packet["selected_method_id"] == expected_method
    assert packet["selected_shape_id"] == expected_shape
    assert packet["selected_case_id"] == expected_case


@pytest.mark.parametrize(
    "prompt, expected_mode, expected_method, expected_shape, expected_case",
    [
        ("What are you?", "direct_bounded", "verified_identity_status_answer_v1", "direct_bounded_answer", "identity_self_description_case"),
        ("Explain WESLR.", "direct_bounded", "verified_identity_status_answer_v1", "direct_bounded_answer", "identity_self_description_case"),
        ("What can you do?", "direct_bounded", "capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
        ("What capabilities are active?", "direct_bounded", "capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
        ("Can I upload files?", "direct_bounded", "capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
        ("Can I pay now?", "direct_bounded", "capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
        ("Is marketplace active?", "direct_bounded", "capability_orientation_answer_v1", "direct_bounded_answer", "capability_orientation_case"),
        ("What is qlorbex?", "unknown_friction", "unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_word_or_phrase_case"),
        ("I found an unknown word.", "unknown_friction", "unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_word_or_phrase_case"),
        ("This phrase is unfamiliar.", "unknown_friction", "unknown_engine_branch_friction_answer_v1", "unknown_friction_branch_answer", "unknown_word_or_phrase_case"),
    ],
)
def test_renderer_follows_expected_metadata(prompt, expected_mode, expected_method, expected_shape, expected_case):
    packet = to_no_model_bounded_render_json_safe_v1(render_no_model_bounded_answer_v1(prompt.split(), {}))
    assert packet["render_mode"] == expected_mode
    assert packet["selected_method_id"] == expected_method
    assert packet["selected_shape_id"] == expected_shape
    assert packet["selected_case_id"] == expected_case
    assert expected_method in packet["response_text"] or packet["response_text"].strip()


@pytest.mark.parametrize(
    "prompt, forbidden_fragments",
    [
        ("Are you AGI?", ("official", "turing", "certified", "sentient", "conscious")),
        ("Are you conscious?", ("official", "turing", "certified", "sentient", "conscious")),
        ("Are you public pilot ready?", ("official", "turing", "certified", "sentient")),
        ("Do you remember everything?", ("I remember everything", "perfect memory", "all memory")),
        ("Give official Turing result", ("official turing result", "certified", "benchmark claim")),
    ],
)
def test_boundary_regressions_stay_bounded(prompt, forbidden_fragments):
    packet = to_no_model_bounded_render_json_safe_v1(render_no_model_bounded_answer_v1(prompt.split(), {}))
    text = packet["response_text"].lower()
    for fragment in forbidden_fragments:
        assert fragment not in text


def test_initial_friction_replay_now_passes_expected():
    packet = build_initial_renderer_friction_replay_v1()
    assert packet.case_count == 4
    assert packet.passed_count == 4
    assert packet.partial_count == 0
    assert packet.failed_count == 0
    assert all(result.match_status == "passes_expected" for result in packet.results)


@pytest.mark.parametrize(
    "prompt",
    ["Are you AGI?", "Are you conscious?", "Are you public pilot ready?"],
)
def test_boundary_prompts_do_not_overclaim(prompt):
    fit = to_response_fit_self_check_json_safe_v1(check_candidate_response_fit_v1(prompt.split(), {}))
    assert fit["fit_status"] in {"needs_clarification", "fit", "fit_with_boundaries", "unknown_friction"}
    assert not any("turing" in item.lower() or "certif" in item.lower() for item in fit["fit_labels"])
