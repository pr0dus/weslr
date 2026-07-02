"""Tests for the ARC Synthetic Task Difficulty Ladder schema helpers."""

from __future__ import annotations

import pytest

from weslr.arc_discovery_140_generator import generate_discovery_140_tasks, get_scoring_summary
from weslr.arc_discovery_140_hard_mode_calibration import generate_hard_mode_calibration_tasks, get_hard_mode_summary
from weslr.arc_task_difficulty_ladder import (
    LEVEL_IDS_V1,
    SCHEMA_VERSION_V1,
    allowed_task_difficulty_levels_v1,
    classify_task_contract_to_level_v1,
    export_solver_visible_task_contract_v1,
    get_task_difficulty_level_definition_v1,
    get_task_difficulty_level_definitions_v1,
    list_under_covered_task_difficulty_levels_v1,
    task_difficulty_contract_issues_v1,
    task_difficulty_ladder_coverage_snapshot_v1,
    task_difficulty_level_definition_issues_v1,
    task_language_fields_for_level_v1,
    task_language_issues_v1,
    validate_task_difficulty_contract_v1,
    validate_task_difficulty_level_definition_v1,
    validate_task_language_v1,
)


@pytest.fixture(scope="module")
def level_defs():
    return get_task_difficulty_level_definitions_v1()


@pytest.fixture(scope="module")
def valid_contracts():
    return {
        "T1": {
            "level_id": "T1",
            "purpose": "Primitive isolation for one rule.",
            "task_signature": "single latent operation with minimal ambiguity",
            "rule_type": "selection",
            "primary_object_scope": "single object",
            "expected_transform": "recolor",
            "ambiguity_axes": [],
            "confidence_policy": "exact",
            "anti_cheat_controls": [
                "no_task_id_shortcut",
                "no_primitive_name_leakage",
                "no_sequence_leakage",
                "no_noop_task",
                "no_single_template_repetition",
                "no_metadata_only_solving",
            ],
            "scoring_layer_compatibility": ["scored", "regression"],
        },
        "T2": {
            "level_id": "T2",
            "purpose": "Short composition for 2–3 ordered operations.",
            "task_signature": "deterministic chain with preserved intermediate state",
            "primitive_chain_length": 3,
            "ordered_operations": ["select", "recolor", "place"],
            "intermediate_state_required": True,
            "confidence_policy": "exact",
            "anti_cheat_controls": [
                "no_sequence_leakage",
                "no_output_template_leakage",
                "no_duplicate_surface_reuse",
            ],
            "scoring_layer_compatibility": ["scored", "hard_mode"],
        },
        "T3": {
            "level_id": "T3",
            "purpose": "Rival-grammar ambiguity resolved by separating evidence.",
            "task_signature": "multiple grammars fit visible examples",
            "confidence_policy": "resolve_or_flag",
            "anti_cheat_controls": [
                "require_separating_examples",
                "no_tie_breaker_leakage",
                "no_easy_clue_metadata",
                "no_overfriendly_distractors",
            ],
            "scoring_layer_compatibility": ["hard_mode", "scored"],
            "internal_task_language": {
                "latent_rule": "select the leftmost object unless a border-touching rival grammar fits",
                "rival_grammars": ["leftmost", "border_touching"],
                "separating_examples": ["train_1", "train_2"],
                "ambiguity_axes": ["position", "boundary_contact"],
                "confidence_state": "confident",
            },
        },
        "T4": {
            "level_id": "T4",
            "purpose": "Unseen composition with known primitives.",
            "task_signature": "known primitives in a novel order and scene form",
            "confidence_policy": "exact_if_generalized",
            "anti_cheat_controls": [
                "no_exact_training_chain_repetition",
                "variants_must_change_shapes_distractors_or_geometry",
                "no_surface_copy_paste",
            ],
            "scoring_layer_compatibility": ["hard_mode", "scored"],
            "internal_task_language": {
                "latent_rule": "compose the known steps through a new scene graph",
                "composition_graph": {"nodes": 3, "edges": 2},
                "novelty_marker": "novel_scene_form",
                "confidence_state": "confident",
            },
        },
        "T5": {
            "level_id": "T5",
            "purpose": "Primitive insufficiency frontier.",
            "task_signature": "nearest known primitives fail in a separable way",
            "confidence_policy": "insufficient_language",
            "anti_cheat_controls": [
                "candidate_probes_never_count_as_solved",
                "no_nearest_neighbor_shortcut",
                "no_primitive_name_leakage",
                "no_claim_of_regression_win",
            ],
            "scoring_layer_compatibility": ["candidate_probe", "hard_mode_unsupported"],
            "can_be_counted_as_solved": False,
            "internal_task_language": {
                "latent_rule": "existing primitives cannot cleanly explain the frontier behavior",
                "nearest_existing_primitive_set": ["select", "recolor"],
                "insufficiency_reason": "boundary fusion requires a primitive not yet represented",
                "confidence_state": "insufficient_evidence",
            },
        },
        "T6": {
            "level_id": "T6",
            "purpose": "Transfer family across changed surfaces.",
            "task_signature": "same latent rule across surface variants",
            "confidence_policy": "exact_across_variants",
            "anti_cheat_controls": [
                "minimum_three_surface_variants",
                "no_single_template_repetition",
                "no_same_task_new_color_only_padding",
            ],
            "scoring_layer_compatibility": ["scored", "hard_mode"],
            "internal_task_language": {
                "latent_rule": "apply the same rule across shifted surfaces",
                "transfer_family_anchor": "family_a",
                "surface_variant_axes": ["color", "size", "distractor_density"],
                "confidence_state": "confident",
            },
        },
        "T7": {
            "level_id": "T7",
            "purpose": "Self-calibrating underdetermined task.",
            "task_signature": "evidence may be insufficient by design",
            "confidence_policy": "abstain_or_flag",
            "anti_cheat_controls": [
                "unresolved_must_be_valid",
                "no_forced_binary_labeling",
                "no_metadata_only_solve_by_inspection",
            ],
            "scoring_layer_compatibility": ["diagnostic", "hard_mode"],
            "internal_task_language": {
                "latent_rule": "the evidence is not sufficient to force a unique solve",
                "confidence_state": "unresolved",
                "unresolved_abstain_policy": "abstain_when_insufficient",
                "more_examples_needed": True,
            },
        },
    }


class TestDefinitions:
    def test_all_levels_defined(self, level_defs):
        assert allowed_task_difficulty_levels_v1() == LEVEL_IDS_V1
        assert [item["level_id"] for item in level_defs] == list(LEVEL_IDS_V1)
        assert len(level_defs) == 7

    def test_level_definitions_validate(self, level_defs):
        for definition in level_defs:
            assert task_difficulty_level_definition_issues_v1(definition) == []
            assert validate_task_difficulty_level_definition_v1(definition) == definition

    def test_definition_lookup(self):
        assert get_task_difficulty_level_definition_v1("T7")["confidence_policy"] == "abstain_or_flag"
        with pytest.raises(KeyError):
            get_task_difficulty_level_definition_v1("T8")


class TestTaskLanguage:
    @pytest.mark.parametrize("level_id", ["T3", "T4", "T5", "T6", "T7"])
    def test_required_task_language_fields_are_declared(self, level_id):
        fields = task_language_fields_for_level_v1(level_id)
        assert fields
        if level_id == "T3":
            assert fields == ("latent_rule", "rival_grammars", "separating_examples", "ambiguity_axes", "confidence_state")
        if level_id == "T4":
            assert fields == ("latent_rule", "composition_graph", "novelty_marker", "confidence_state")
        if level_id == "T5":
            assert fields == ("latent_rule", "nearest_existing_primitive_set", "insufficiency_reason", "confidence_state")
        if level_id == "T6":
            assert fields == ("latent_rule", "transfer_family_anchor", "surface_variant_axes", "confidence_state")
        if level_id == "T7":
            assert fields == ("latent_rule", "confidence_state", "unresolved_abstain_policy")

    def test_valid_task_language_packets_pass(self):
        packets = {
            "T3": {
                "latent_rule": "select leftmost unless border-touching rival grammar wins",
                "rival_grammars": ["leftmost", "border_touching"],
                "separating_examples": ["train_1", "train_2"],
                "ambiguity_axes": ["position", "boundary_contact"],
                "confidence_state": "confident",
            },
            "T4": {
                "latent_rule": "compose the known steps through a new scene graph",
                "composition_graph": {"nodes": 3, "edges": 2},
                "novelty_marker": "novel_scene_form",
                "confidence_state": "confident",
            },
            "T5": {
                "latent_rule": "existing primitives cannot cleanly explain the frontier behavior",
                "nearest_existing_primitive_set": ["select", "recolor"],
                "insufficiency_reason": "boundary fusion requires a primitive not yet represented",
                "confidence_state": "insufficient_evidence",
            },
            "T6": {
                "latent_rule": "apply the same rule across shifted surfaces",
                "transfer_family_anchor": "family_a",
                "surface_variant_axes": ["color", "size", "distractor_density"],
                "confidence_state": "confident",
            },
            "T7": {
                "latent_rule": "the evidence is not sufficient to force a unique solve",
                "confidence_state": "unresolved",
                "unresolved_abstain_policy": "abstain_when_insufficient",
            },
        }
        for level_id, packet in packets.items():
            assert task_language_issues_v1(level_id, packet) == []
            assert validate_task_language_v1(level_id, packet) == packet

    def test_missing_task_language_fields_are_rejected(self):
        with pytest.raises(ValueError):
            validate_task_language_v1("T3", {"latent_rule": "x", "confidence_state": "confident"})
        with pytest.raises(ValueError):
            validate_task_language_v1("T4", {"latent_rule": "x", "confidence_state": "confident"})
        with pytest.raises(ValueError):
            validate_task_language_v1("T5", {"latent_rule": "x", "confidence_state": "insufficient_evidence"})
        with pytest.raises(ValueError):
            validate_task_language_v1("T6", {"latent_rule": "x", "confidence_state": "confident", "surface_variant_axes": ["c", "s"]})
        with pytest.raises(ValueError):
            validate_task_language_v1("T7", {"latent_rule": "x", "confidence_state": "unresolved"})


class TestContracts:
    @pytest.mark.parametrize("level_id", list(LEVEL_IDS_V1))
    def test_valid_example_contracts_pass(self, valid_contracts, level_id):
        contract = valid_contracts[level_id]
        assert classify_task_contract_to_level_v1(contract) == level_id
        assert task_difficulty_contract_issues_v1(contract) == []
        validated = validate_task_difficulty_contract_v1(contract)
        assert validated["level_id"] == level_id

    def test_invalid_contracts_are_rejected(self, valid_contracts):
        bad_t2 = dict(valid_contracts["T2"])
        bad_t2.pop("ordered_operations")
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t2)

        bad_t3 = dict(valid_contracts["T3"])
        bad_t3["internal_task_language"] = dict(bad_t3["internal_task_language"])
        bad_t3["internal_task_language"].pop("rival_grammars")
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t3)

        bad_t4 = dict(valid_contracts["T4"])
        bad_t4["internal_task_language"] = dict(bad_t4["internal_task_language"])
        bad_t4["internal_task_language"].pop("composition_graph")
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t4)

        bad_t5 = dict(valid_contracts["T5"])
        bad_t5["can_be_counted_as_solved"] = True
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t5)

        bad_t6 = dict(valid_contracts["T6"])
        bad_t6["internal_task_language"] = dict(bad_t6["internal_task_language"])
        bad_t6["internal_task_language"]["surface_variant_axes"] = ["v1", "v2"]
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t6)

        bad_t7 = dict(valid_contracts["T7"])
        bad_t7["internal_task_language"] = dict(bad_t7["internal_task_language"])
        bad_t7["internal_task_language"].pop("unresolved_abstain_policy")
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(bad_t7)

    def test_t5_candidate_probe_cannot_be_counted_as_solved(self, valid_contracts):
        contract = dict(valid_contracts["T5"])
        contract["counted_as_solved"] = True
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(contract)

    def test_t7_unresolved_state_is_valid(self, valid_contracts):
        contract = dict(valid_contracts["T7"])
        assert validate_task_difficulty_contract_v1(contract)["internal_task_language"]["confidence_state"] == "unresolved"

    def test_t6_requires_three_surface_variants(self, valid_contracts):
        contract = dict(valid_contracts["T6"])
        contract["internal_task_language"] = dict(contract["internal_task_language"])
        contract["internal_task_language"]["surface_variant_axes"] = ["color", "size"]
        issues = task_difficulty_contract_issues_v1(contract)
        assert "task_language:surface_variant_axes_too_small" in issues

    def test_t3_requires_rival_grammars_and_separating_examples(self, valid_contracts):
        contract = dict(valid_contracts["T3"])
        contract["internal_task_language"] = dict(contract["internal_task_language"])
        contract["internal_task_language"].pop("rival_grammars")
        issues = task_difficulty_contract_issues_v1(contract)
        assert "task_language:missing_task_language_field:rival_grammars" in issues

    def test_task_id_and_leakage_controls(self, valid_contracts):
        task_id_shortcut = dict(valid_contracts["T1"])
        task_id_shortcut["task_id_shortcut"] = True
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(task_id_shortcut)

        primitive_leak = dict(valid_contracts["T1"])
        primitive_leak["primitive_name_leakage"] = "extract"
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(primitive_leak)

        sequence_leak = dict(valid_contracts["T2"])
        sequence_leak["sequence_leakage"] = ["select", "recolor"]
        with pytest.raises(ValueError):
            validate_task_difficulty_contract_v1(sequence_leak)

    def test_solver_visible_export_strips_internal_task_language(self, valid_contracts):
        visible = export_solver_visible_task_contract_v1(valid_contracts["T3"])
        assert "internal_task_language" not in visible
        assert "level_id" not in visible
        assert "confidence_policy" not in visible
        assert "rival_grammars" not in visible
        assert "separating_examples" not in visible
        assert "task_signature" not in visible
        assert "purpose" not in visible
        assert "scoring_layer_compatibility" not in visible


class TestCoverageAndRegressionSafety:
    def test_under_covered_levels(self):
        snapshot = {
            "coverage_by_level": {
                "T1": 30,
                "T2": 24,
                "T3": 6,
                "T4": 5,
                "T5": 12,
                "T6": 2,
                "T7": 1,
            },
            "minimum_coverage_by_level": {
                "T1": 24,
                "T2": 24,
                "T3": 12,
                "T4": 12,
                "T5": 12,
                "T6": 12,
                "T7": 12,
            },
        }
        assert list_under_covered_task_difficulty_levels_v1(snapshot) == ("T3", "T4", "T6", "T7")
        coverage = task_difficulty_ladder_coverage_snapshot_v1(snapshot)
        assert coverage["schema_version"] == SCHEMA_VERSION_V1
        assert coverage["under_covered_levels"] == ["T3", "T4", "T6", "T7"]

    def test_existing_140_base_and_hard_mode_remain_unchanged(self):
        summary = get_scoring_summary(generate_discovery_140_tasks())
        assert summary == {
            "total_tasks": 140,
            "scored_total": 130,
            "candidate_probe_total": 10,
            "bh80_count": 80,
            "previous_scored_base_total": 117,
            "new_scored_expansion_total": 13,
            "old_probe_total": 3,
            "new_probe_total": 7,
            "color_invert_task_count": 16,
            "candidate_probe_counted_as_solved": 0,
        }

        hard_mode_summary = get_hard_mode_summary(generate_hard_mode_calibration_tasks())
        assert hard_mode_summary == {
            "total_tasks": 30,
            "hard_mode_total": 30,
            "hard_mode_scored_total": 30,
            "candidate_probe_total": 0,
            "family_counts": {
                "connected_component_ambiguity": 4,
                "diagonal_adjacency_trap": 1,
                "distractor_density": 3,
                "hole_topology_trap": 3,
                "largest_object_trap": 2,
                "leftmost_topmost_trap": 1,
                "object_ambiguity": 1,
                "order_sensitivity": 1,
                "output_dimension_change": 3,
                "primitive_chain_deception": 3,
                "relation_swap_ambiguity": 1,
                "rival_grammar_ambiguity": 3,
                "same_color_multi_object_trap": 2,
                "symmetry_trap": 2,
            },
            "axis_counts": {
                "object_ambiguity": 2,
                "color_ambiguity": 2,
                "connected_component_ambiguity": 7,
                "distractor_density": 3,
                "symmetry_trap": 2,
                "largest_object_trap": 2,
                "leftmost_topmost_trap": 4,
                "same_color_multi_object_trap": 6,
                "diagonal_adjacency_trap": 3,
                "hole_topology_trap": 6,
                "relation_swap_ambiguity": 3,
                "order_sensitivity": 2,
                "primitive_chain_deception": 4,
                "output_dimension_change": 6,
                "unseen_composition": 3,
                "rival_grammar_ambiguity": 6,
            },
            "hard_mode_denominator": 30,
            "hard_mode_counted_as_solved": 0,
        }
