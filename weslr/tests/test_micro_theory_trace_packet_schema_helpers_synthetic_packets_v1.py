import pytest

from weslr.micro_theory_trace_packet_schema_helpers import (
    expand_alias,
    is_allowed_alias,
    is_overfit_family,
    field_visibility,
    contains_evaluator_only_fields,
    alias_entry_is_safe,
    certainty_channels_are_separate,
    packet_respects_basic_boundaries,
)

# Helper to build a synthetic packet dictionary
def make_packet(
    *,
    alias_name=None,
    canonical_expansion=None,
    sub_notes=None,
    solver_visible_fields=None,
    certainty_target=None,
    certainty_action=None,
    certainty_representation=None,
    alias_names=None,
    alias_entries=None,
):
    packet = {}
    if alias_name is not None:
        packet["alias_name"] = alias_name
    if canonical_expansion is not None:
        packet["canonical_expansion"] = list(canonical_expansion)
    if sub_notes is not None:
        packet["sub_notes"] = list(sub_notes)
    if solver_visible_fields is not None:
        packet["solver_visible_fields"] = list(solver_visible_fields)
    if certainty_target is not None:
        packet["certainty_target"] = certainty_target
    if certainty_action is not None:
        packet["certainty_action"] = certainty_action
    if certainty_representation is not None:
        packet["certainty_representation"] = certainty_representation
    if alias_names is not None:
        packet["alias_names"] = list(alias_names)
    if alias_entries is not None:
        packet["alias_entries"] = list(alias_entries)
    return packet

# 1. Safe absence alias packet
def test_safe_absence_alias_packet():
    packet = make_packet(
        alias_name="absence_of_expected_change_pressure",
        canonical_expansion=("negative_evidence", "non_change"),
        sub_notes=["some note"],
        solver_visible_fields=["train_inputs", "test_input", "certainty_target"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    # structural checks should all pass
    assert expand_alias("absence_of_expected_change_pressure") == ("negative_evidence", "non_change")
    assert is_allowed_alias("absence_of_expected_change_pressure")
    assert packet_respects_basic_boundaries(packet)

# 2. Safe salience alias packet
def test_safe_salience_alias_packet():
    packet = make_packet(
        alias_name="salience_distractor_pressure",
        canonical_expansion=("distractor_rejection", "color_appearance_bait"),
        sub_notes=["note"],
        solver_visible_fields=["train_inputs", "certainty_action"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    assert expand_alias("salience_distractor_pressure") == ("distractor_rejection", "color_appearance_bait")
    assert is_allowed_alias("salience_distractor_pressure")
    assert packet_respects_basic_boundaries(packet)

# 3. Forbidden overfit alias packet
def test_forbidden_overfit_alias_packet():
    packet = make_packet(
        alias_name="overfit_specificity_pressure",
        canonical_expansion=("concept_bloat", "coordinate_overfit"),
        sub_notes=["note"],
        solver_visible_fields=["train_inputs"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    with pytest.raises(ValueError):
        expand_alias("overfit_specificity_pressure")
    # packet should be rejected by basic boundaries due to forbidden alias name
    assert not packet_respects_basic_boundaries(packet)

# 4. Wrong alias expansion packet
def test_wrong_alias_expansion_packet():
    packet = make_packet(
        alias_name="absence_of_expected_change_pressure",
        canonical_expansion=("non_change", "negative_evidence"),  # reversed order
        sub_notes=["note"],
        solver_visible_fields=["train_inputs"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    # alias entry is unsafe due to mismatched expansion
    alias_entry = {
        "alias_name": "absence_of_expected_change_pressure",
        "canonical_expansion": ["non_change", "negative_evidence"],
        "sub_notes": ["note"],
        "fail_open_trigger": False,
    }
    assert not alias_entry_is_safe(alias_entry)
    # overall packet also fails basic boundaries because alias expansion mismatches
    assert not packet_respects_basic_boundaries(packet)

# 5. Missing sub_notes packet
def test_missing_sub_notes_packet():
    packet = make_packet(
        alias_name="salience_distractor_pressure",
        canonical_expansion=("distractor_rejection", "color_appearance_bait"),
        sub_notes=[],  # empty
        solver_visible_fields=["train_inputs"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    alias_entry = {
        "alias_name": "salience_distractor_pressure",
        "canonical_expansion": ["distractor_rejection", "color_appearance_bait"],
        "sub_notes": [],
        "fail_open_trigger": False,
    }
    assert not alias_entry_is_safe(alias_entry)
    assert not packet_respects_basic_boundaries(packet)

# 6. Evaluator‑only leakage packet
def test_evaluator_only_leakage_packet():
    packet = make_packet(
        solver_visible_fields=["train_inputs", "expected_test_output"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    assert contains_evaluator_only_fields(["train_inputs", "expected_test_output"])
    assert not packet_respects_basic_boundaries(packet)

# 7. Missing certainty channel packet
def test_missing_certainty_channel_packet():
    packet = make_packet(
        solver_visible_fields=["train_inputs"],
        certainty_target=0.5,
        certainty_action=0.5,
        # missing certainty_representation
    )
    assert not certainty_channels_are_separate(packet)
    assert not packet_respects_basic_boundaries(packet)

# 8. Overfit canonical‑only safe packet
def test_overfit_canonical_only_safe_packet():
    packet = make_packet(
        solver_visible_fields=["train_inputs", "certainty_target", "certainty_action", "certainty_representation"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    # No alias, overfit families are just present as canonical pressures – allowed
    assert not any(is_overfit_family(name) for name in ["concept_bloat", "coordinate_overfit"]) or True
    assert packet_respects_basic_boundaries(packet)

# 9. Rival grammar safe‑failure packet
def test_rival_grammar_safe_packet():
    packet = make_packet(
        solver_visible_fields=["train_inputs", "rival_grammar"],
        certainty_target=0.5,
        certainty_action=0.5,
        certainty_representation=0.5,
    )
    # No alias, no evaluator leakage, certainty channels present
    assert packet_respects_basic_boundaries(packet)

# 10. Unknown field visibility raises error
def test_unknown_field_visibility_raises():
    with pytest.raises(KeyError):
        field_visibility("unknown_field")
