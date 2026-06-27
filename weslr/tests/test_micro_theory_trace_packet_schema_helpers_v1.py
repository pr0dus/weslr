from __future__ import annotations

import pytest

from weslr.micro_theory_trace_packet_schema_helpers import (
    CANONICAL_PRESSURES,
    ALLOWED_ALIASES,
    FORBIDDEN_ALIASES,
    is_overfit_family,
    expand_alias,
    is_allowed_alias,
    field_visibility,
    contains_evaluator_only_fields,
    alias_entry_is_safe,
    certainty_channels_are_separate,
    packet_respects_basic_boundaries,
)


def test_canonical_pressure_families_exist():
    expected = {
        "role_stability",
        "relation_stability",
        "absence",
        "exception",
        "contradiction_precedence",
        "negative_evidence",
        "non_change",
        "distractor_rejection",
        "color_appearance_bait",
        "target_location",
        "action_type",
        "output_shape",
        "rival_grammar",
        "unresolved_ambiguity",
        "counterfactual_stability",
        "concept_bloat",
        "coordinate_overfit",
    }
    assert expected.issubset(CANONICAL_PRESSURES)


def test_allowed_aliases_expand_correctly():
    assert expand_alias("absence_of_expected_change_pressure") == (
        "negative_evidence",
        "non_change",
    )
    assert expand_alias("salience_distractor_pressure") == (
        "distractor_rejection",
        "color_appearance_bait",
    )


def test_forbidden_overfit_alias_raises():
    with pytest.raises(ValueError):
        expand_alias("overfit_specificity_pressure")


def test_unknown_alias_raises():
    with pytest.raises(KeyError):
        expand_alias("unknown_alias")


def test_overfit_families_remain_separate():
    assert is_overfit_family("concept_bloat")
    assert is_overfit_family("coordinate_overfit")
    assert not is_overfit_family("non_change")


def test_field_visibility_classifies_solver_visible():
    assert field_visibility("train_inputs") == "solver_visible"
    assert field_visibility("certainty_target") == "solver_visible"


def test_field_visibility_classifies_evaluator_only():
    assert field_visibility("intended_rule") == "evaluator_only"
    assert field_visibility("expected_test_output") == "evaluator_only"


def test_contains_evaluator_only_fields_detects_leakage():
    assert contains_evaluator_only_fields(["train_inputs", "expected_test_output"])
    assert not contains_evaluator_only_fields(["train_inputs", "certainty_target"])


def test_alias_entry_is_safe_accepts_valid_absence_alias():
    entry = {
        "alias_name": "absence_of_expected_change_pressure",
        "canonical_expansion": ["negative_evidence", "non_change"],
        "sub_notes": ["expected-but-missing effect"],
        "fail_open_trigger": False,
    }
    assert alias_entry_is_safe(entry)


def test_alias_entry_is_safe_accepts_valid_salience_alias():
    entry = {
        "alias_name": "salience_distractor_pressure",
        "canonical_expansion": ["distractor_rejection", "color_appearance_bait"],
        "sub_notes": ["color bait"],
        "fail_open_trigger": False,
    }
    assert alias_entry_is_safe(entry)


def test_alias_entry_is_safe_rejects_missing_sub_notes():
    entry = {
        "alias_name": "salience_distractor_pressure",
        "canonical_expansion": ["distractor_rejection", "color_appearance_bait"],
        "sub_notes": [],
        "fail_open_trigger": False,
    }
    assert not alias_entry_is_safe(entry)


def test_alias_entry_is_safe_rejects_wrong_canonical_expansion():
    entry = {
        "alias_name": "absence_of_expected_change_pressure",
        "canonical_expansion": ["non_change", "negative_evidence"],
        "sub_notes": ["expected-but-missing effect"],
        "fail_open_trigger": False,
    }
    assert not alias_entry_is_safe(entry)


def test_alias_entry_is_safe_rejects_forbidden_overfit_alias():
    entry = {
        "alias_name": "overfit_specificity_pressure",
        "canonical_expansion": ["concept_bloat", "coordinate_overfit"],
        "sub_notes": ["forbidden"],
        "fail_open_trigger": True,
    }
    assert not alias_entry_is_safe(entry)


def test_certainty_channels_are_separate_requires_all_three_channels():
    assert not certainty_channels_are_separate({"certainty_target": 0.5, "certainty_action": 0.5})
    assert certainty_channels_are_separate(
        {
            "certainty_target": 0.5,
            "certainty_action": 0.5,
            "certainty_representation": 0.5,
        }
    )


def test_packet_respects_basic_boundaries_accepts_safe_synthetic_packet():
    packet = {
        "solver_visible_fields": ["train_inputs", "test_input", "certainty_target"],
        "alias_names": ["absence_of_expected_change_pressure"],
        "alias_entries": [
            {
                "alias_name": "absence_of_expected_change_pressure",
                "canonical_expansion": ["negative_evidence", "non_change"],
                "sub_notes": ["expected-but-missing effect"],
                "fail_open_trigger": False,
            }
        ],
        "certainty_target": 0.5,
        "certainty_action": 0.5,
        "certainty_representation": 0.5,
    }
    assert packet_respects_basic_boundaries(packet)


def test_packet_respects_basic_boundaries_rejects_solver_visible_evaluator_only_leak():
    packet = {
        "solver_visible_fields": ["train_inputs", "expected_test_output"],
        "certainty_target": 0.5,
        "certainty_action": 0.5,
        "certainty_representation": 0.5,
    }
    assert not packet_respects_basic_boundaries(packet)


def test_packet_respects_basic_boundaries_rejects_forbidden_overfit_alias():
    packet = {
        "solver_visible_fields": ["train_inputs"],
        "alias_names": ["overfit_specificity_pressure"],
        "certainty_target": 0.5,
        "certainty_action": 0.5,
        "certainty_representation": 0.5,
    }
    assert not packet_respects_basic_boundaries(packet)


def test_no_external_side_effect_config_symbols_present():
    assert "overfit_specificity_pressure" in FORBIDDEN_ALIASES
    assert is_allowed_alias("absence_of_expected_change_pressure")
    assert "absence_of_expected_change_pressure" in ALLOWED_ALIASES
